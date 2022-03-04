import sqlalchemy
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String
import requests
from bs4 import BeautifulSoup
from time import sleep

ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
headers = {'User-Agent': ua}
Base = sqlalchemy.ext.declarative.declarative_base()
engine = create_engine('sqlite:///:memory:')


class Lancers(Base):
    __tablename__ = "data"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=False)
    body = Column(String, unique=False)
    price = Column(String, unique=False)
    url = Column(String, unique=False)

    def __init__(self, title=None, body=None, price=None, url=None):
        self.title = title
        self.body = body
        self.price = price
        self.url = url


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def get_post_urls():
    post_urls = []
    url = "https://www.lancers.jp/work/search/system?open=1&ref=header_menu&show_description=0&work_rank%5B%5D=0&work_rank%5B%5D=1&work_rank%5B%5D=2&work_rank%5B%5D=3"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')
    urls = soup.select("a", class_="c-media__title")
    i = 0
    for url in urls:
        if "/work/detail" in url.get("href"):
            post_urls.append("https://www.lancers.jp/" + url.get("href"))
        elif i == 5:
            break
        i += 1
    return post_urls


def scrap_detail():
    c = 1
    scrap_data = {"title": {}, "body": {}, "price": {}, "url": {}}
    for post_url in get_post_urls():
        response = requests.get(post_url, headers=headers)
        sleep(1)
        soup = BeautifulSoup(response.text, 'lxml')

        title_elem = soup.select("h1", class_='c-heading heading--lv1')
        title = processing(title_elem[0].get_text(strip=True))

        body_elem = soup.select("dd", class_='c-definitionList definitionList--holizonalA01')
        body = processing(body_elem[1].text)

        price_elem = soup.select("meta")
        price_pos_left = price_elem[1].get("content").find("(")
        price_pos_right = price_elem[1].get("content").find(")")
        price = processing(price_elem[1].get("content")[1 + price_pos_left:price_pos_right])

        scrap_data["title"].setdefault("title_" + str(c), title)
        scrap_data["body"].setdefault("body_" + str(c), body)
        scrap_data["price"].setdefault("price_" + str(c), price)
        scrap_data["url"].setdefault("url_" + str(c), post_url)
        c += 1
    return scrap_data


def connect_db(scrap_data):
    Session = sessionmaker(bind=engine)
    session = Session()
    for i in range(len(scrap_data["title"])):
        if "閲覧制限" in scrap_data["title"]["title_" + str(i + 1)] or "【新着】" in scrap_data["title"]["title_" + str(i + 1)]:
            continue
        title = scrap_data["title"]["title_" + str(i + 1)]
        body = scrap_data["body"]["body_" + str(i + 1)]
        price = scrap_data["price"]["price_" + str(i + 1)]
        url = scrap_data["url"]["url_" + str(i + 1)]
        data = Lancers(title=title, body=body, price=price, url=url)
        session.add(data)
        session.commit()


def processing(data):
    return data.replace("\n", "").replace("\r", "").replace(" ", "")


def line_notify(scrap_data, i):
    line_notify_token = '9svqlHYyAN65WuseSjTohZolFGwgFMAfRTKL0NqjLiL'
    line_notify_api = 'https://notify-api.line.me/api/notify'
    header = {'Authorization': f'Bearer {line_notify_token}'}
    data = {
        'message': f'message: {"依頼タイトル:" + processing(scrap_data["title"]["title_" + str(i + 1)]), "依頼内容:" + processing(scrap_data["body"]["body_" + str(i + 1)]), "予算:" + processing(scrap_data["price"]["price_" + str(i + 1)]), "URL:" + processing(scrap_data["url"]["url_" + str(i + 1)])}'}
    requests.post(line_notify_api, headers=header, data=data)


def show_db():
    Session = sessionmaker(bind=engine)
    session = Session()
    lancers_data = session.query().all()
    for row in lancers_data:
        print(row.id, row.title)

    session.close()


def delete_all_data():
    Session = sessionmaker(bind=engine)
    session = Session()
    session.query(Lancers).delete()
    session.commit()


def check_update_post(scrap_data):
    Session = sessionmaker(bind=engine)
    session = Session()
    delete_all_data()
    connect_db(scrap_detail())
    while True:
        history = session.query(Lancers).order_by(asc(Lancers.id)).all()
        for i in range(len(scrap_data["title"])):
            if "閲覧制限" not in scrap_data["title"]["title_" + str(i + 1)] or "【新着】" not in scrap_data["title"]["title_" + str(i + 1)]:
                if scrap_data["title"]["title_" + str(i + 1)] not in history[i].title:
                    sleep(1)
                    lancers_obj = session.query(Lancers).filter(Lancers.id == i + 1).first()
                    lancers_obj.title = scrap_data["title"]["title_" + str(i + 1)]
                    lancers_obj.body = scrap_data["body"]["body_" + str(i + 1)]
                    lancers_obj.price = scrap_data["price"]["price_" + str(i + 1)]
                    lancers_obj.price = scrap_data["url"]["url_" + str(i + 1)]
                    session.commit()
                    print(scrap_data["title"]["title_" + str(i + 1)], history[i].title)
                    line_notify(scrap_data, i)


if __name__ == '__main__':
    check_update_post(scrap_detail())
