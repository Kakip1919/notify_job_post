import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String
from time import sleep
import requests
from bs4 import BeautifulSoup
import os

ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
headers = {'User-Agent': ua}
database_file = os.path.join(os.path.abspath(os.getcwd()), "new.db")
Base = declarative_base()

engine = create_engine('sqlite:///' + database_file, echo=True)
Base.metadata.create_all(bind=engine)


class Lancers(Base):
    __tablename__ = "lancers"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=False)
    body = Column(String, unique=False)
    price = Column(String, unique=False)

    def __init__(self, title=None, body=None, price=None):
        self.body = body
        self.title = title
        self.price = price


def get_post_urls():
    post_urls = []
    url = "https://www.lancers.jp/work/search/system?open=1&ref=header_menu&show_description=0&work_rank%5B%5D=0&work_rank%5B%5D=1&work_rank%5B%5D=2&work_rank%5B%5D=3"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')
    urls = soup.select("a", class_="c-media__title")
    for url in urls:
        if "/work/detail" in url.get("href"):
            post_urls.append("https://www.lancers.jp/" + url.get("href"))
    return post_urls


def scrap_detail():
    c = 1
    scrap_data = {"title": {}, "body": {}, "price": {}}
    for post_url in get_post_urls():
        response = requests.get(post_url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')

        title_elem = soup.select("h1", class_='c-heading heading--lv1')
        title = title_elem[0].get_text(strip=True).replace("\n", "")

        body_elem = soup.select("dd", class_='c-definitionList definitionList--holizonalA01')
        body = body_elem[1].text.replace(" ", "")

        price_elem = soup.select("meta")
        price_pos_left = price_elem[1].get("content").find("(")
        price_pos_right = price_elem[1].get("content").find(")")
        price = price_elem[1].get("content")[1 + price_pos_left:price_pos_right]

        scrap_data["title"].setdefault("title_" + str(c), title)
        scrap_data["body"].setdefault("body_" + str(c), body)
        scrap_data["price"].setdefault("price_" + str(c), price)
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
        data = Lancers(title=title, body=body, price=price)
        session.add(data)
        session.commit()
    session.close()


def show_db():
    Session = sessionmaker(bind=engine)
    session = Session()
    students = session.query(Lancers)
    for row in students:
        print(row.id,row.title)


def processing(data):
    return data.replace("\n", "").replace("\r", "").replace(" ", "")


def line_notify(scrap_data, i):
    line_notify_token = '9svqlHYyAN65WuseSjTohZolFGwgFMAfRTKL0NqjLiL'
    line_notify_api = 'https://notify-api.line.me/api/notify'
    header = {'Authorization': f'Bearer {line_notify_token}'}
    data = {
        'message': f'message: {"依頼タイトル:" + processing(scrap_data["title"]["title_" + str(i + 1)]), "依頼内容:" + processing(scrap_data["body"]["body_" + str(i + 1)]), "予算:" + processing(scrap_data["price"]["price_" + str(i + 1)])}'}
    requests.post(line_notify_api, headers=header, data=data)


def check_update_post(scrap_data):
    connect_db(scrap_detail())
    while True:
        read_file = open('history.txt', 'r', encoding='UTF-8')
        write_file = open('history.txt', 'w', encoding='UTF-8')
        for i in range(len(scrap_data["title"])):
            history_title = read_file.readlines()
            print(history_title)
            for latest_title in scrap_data["title"]:
                if latest_title not in history_title:
                    history_title[i + 1] = scrap_data["title"]["title_" + str(i + 1)]
                    # write_file.writelines(history_title[i + 1])
            write_file.close()
        read_file.close()


if __name__ == '__main__':
    show_db()