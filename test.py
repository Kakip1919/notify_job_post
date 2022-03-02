from time import sleep
import requests
from bs4 import BeautifulSoup

ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
headers = {'User-Agent': ua}


def Get_Post_Urls():
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
    for post_url in Get_Post_Urls():
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


if __name__ == '__main__':
    print(scrap_detail())
