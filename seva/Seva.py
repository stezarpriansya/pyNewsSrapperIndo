import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import locale
locale.setlocale(locale.LC_ALL, 'ID')
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import html
import time
from requests.exceptions import ConnectionError
import unicodedata
import mysql.connector

class Seva:
    def getAllBerita(self, details, page, cat_link, category):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : dd/mm/YYYY
        category: otomotif, properti
        cat_link = Tips & Rekomendasi
                    Review Otomotif
                    Berita Terbaru
                    Travel & Lifestyle
                    Berita Otomotif
                    Keuangan
                    Hobi & Komunitas
                    Modifikasi
                    Editor's Pick
                    tips-n-rekomendasi khusus untuk properti
        """
        print("page ", page)
        url = "https://www.seva.id/"+category+"/blog/category/"+cat_link+"/page/"+str(page)
        print(url)
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page, cat_link, category)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        # contentDiv = soup.find('div', class_="col-md-6")
        flag = True
        indeks = soup.findAll('div', class_='article-box')
        for post in indeks:
            link = [post.find('a', href=True)['href'], cat_link, category]
            #check if there are a post with same url
            cursor = con.cursor()
            query = "SELECT count(*) FROM article WHERE url like '"+link[0]+"'"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            if result[0] > 0:
                flag = False
                break
            else:
                detail = self.getDetailBerita(link)
                if detail:
                    if self.insertDB(con, detail):
                        details.append(detail)
        if flag:
            el_page = soup.find('nav', attrs={'aria-label':'Page navigation example'})
            if el_page:
                max_page = int(soup.find('ul', class_="pagination").findAll('li')[-2].find('a').get_text(strip=True).replace('\n', '').strip(' '))

                if page < max_page:
                    time.sleep(5)
                    details = self.getAllBerita(details, page+1, cat_link, category)
        con.close()
        return 'berhasil ambil semua berita'

    def getDetailBerita(self, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(5)
        articles = {}
        #link
        url = link[0]
        response = requests.get(url)
        html2 = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html2, "html5lib")

        #extract subcategory from meta
        sub = html.unescape(soup.find('meta', attrs={'property': 'article:section'})['content'])

        articles['subcategory'] = link[1]

        articles['id'] = int(soup.find("link", attrs={'rel':'shortlink'})['href'].replace("https://www.seva.id/"+link[2]+"/?p=", "").strip(' \t\n\r'))
        #category
        articles['category'] = link[2]
        articles['url'] = url

        article = soup.find('div', class_="news-content border-list")

        #extract date
        #2018-07-27T15:18:00+00:00
        pubdate = soup.find("meta", attrs={'property':'article:published_time'})
        pubdate = pubdate['content'] if pubdate else '1970-01-01T00:00:01+00:00'
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        #extract author
        author = soup.find("div", class_="col-md-8").find('div', class_='col-md-10')
        articles['author'] = author.find('div', class_="details").get_text(strip=True) if author else ''

        #extract title
        title = article.find('div', class_="title").find('h1')
        articles['title'] = title.get_text(strip=True) if title else ''

        #source
        articles['source'] = 'seva'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = soup.findAll('meta', attrs={'property':'article:tag'})
        articles['tags'] = ','.join([x['content'] for x in tags]) if tags else ''

        #extract images
        images = soup.find('meta', attrs={'property':'og:image'})
        articles['images'] = images['content']

        #extract detail
        detail = article.find('div', class_="content")


        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.get_text(strip=True)))
        articles['content'] = html.unescape(content)
        print('memasukkan berita id ', articles['id'])

        return articles

    def insertDB(self, con, articles):
        """
        Untuk memasukkan berita ke DB
        """
        print("Insert berita ", articles['title'])
        cursor = con.cursor()
        query = "SELECT count(*) FROM article WHERE url like '"+articles['url']+"'"
        cursor.execute(query)
        result = cursor.fetchone()
        if result[0] <= 0:
            add_article = ("INSERT INTO article (post_id, author, pubdate, category, subcategory, content, comments, images, title, tags, url, source) VALUES (%(id)s, %(author)s, %(pubdate)s, %(category)s, %(subcategory)s, %(content)s, %(comments)s, %(images)s, %(title)s, %(tags)s, %(url)s, %(source)s)")
            # Insert article
            cursor.execute(add_article, articles)
            con.commit()
            print('masuk')
            cursor.close()
            return True
        else:
            cursor.close()
            print('salah2')
            return False
