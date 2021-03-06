import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import locale
locale.setlocale(locale.LC_ALL, 'ID')
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from requests.exceptions import ConnectionError
import unicodedata
import mysql.connector

class Rumahku:
    def getAllBerita(self, details, page):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        """

        print("page ", page)
        url = "http://www.rumahku.com/artikel/berita/page:"+str(page)+"/"
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(5)
            details = self.getAllBerita(details, page)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', {'id':'advice-category-list', 'class':'for-article news'})
        flag = True
        for post in contentDiv.findAll('div', class_='text content-right-news big'):
            link = ["http://www.rumahku.com"+post.find('a', href=True)['href'], '']
            # check if there are a post with same url
            con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
            cursor = con.cursor()
            query = "SELECT count(*) FROM article WHERE url like '"+link[0]+"'"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            con.close()
            if(result[0] > 0):
                flag = False
                break
            else:
                detail = self.getDetailBerita(link)
                if detail:
                    if self.insertDB(detail):
                        details.append(detail)
        if flag:
            el_page = soup.find('div', class_='pagination')
            if el_page:
                next_page = el_page.findAll('li', class_='next')
                if next_page:
                    time.sleep(5)
                    details = self.getAllBerita(details, page+1)

        return 'berhasil ambil semua berita'

    def getDetailBerita(self, link):

        time.sleep(5)
        articles = {}
        #link
        url = link[0]
        print(url)
        response = requests.get(url)
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        #extract title
        title = soup.find('h4', class_='margin-bottom-2')
        articles['title'] = title.text if title else ''

        # if ("foto:" in title.lower()) or  "video:" in title.lower():
        #     return False
        #
        # if ("foto" in title.lower()) or  "video" in title.lower():
        #     return False

        bc = soup.find('div', {'class':'container'}).find('ul')
        if not bc:
            return False
        sub = bc.findAll('li')[-2] if bc else ''

        #category
        articles['category'] = 'properti'
        articles['subcategory'] = sub.text

        #article_url
        articles['url'] = url

        # articleid
        article_id = url.replace('/','').replace('.','').split('-')[-1]
        articles['id'] = int(article_id)

        #article
        article = soup.find('div', class_='text-article').find('div', class_='text')

        #extract date
        pubdate = soup.findAll('span', class_='date small-text')[-2].text
        pubdate = pubdate.replace('WIB','')
        pubdate = pubdate.replace('Agu','Agt')
        pubdate = pubdate.strip(' \t\n\r')
        pubdate = datetime.strftime(datetime.strptime(pubdate, "%d %b %Y, %H:%M"), "%Y-%m-%d %H:%M:%S")
        articles['pubdate'] = pubdate
        # articles['id'] = int(datetime.strptime(pubdate, "%d %b %Y, %H:%M").timestamp()) + len(url)

        #extract author
        author = soup.find('div', class_='title-article margin-bottom-4').find('label', class_='normal t-purple')
        articles['author'] = author.text if author else ''

        #source
        articles['source'] = 'rumahku'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        # tags = soup.find('p', class_='post-tag').findAll('a')
        # articles['tags'] = ','.join([x.get_text(strip=True) for x in tags]) if tags else ''
        articles['tags'] = ''

        #extract images
        images = soup.find('meta', {'property':'og:image'})
        articles['images'] = images['content'] if images else ''

        #hapus link sisip
        # for div in article.findAll('div'):
        #     div.decompose()

        if "untuk keperluan info bisa kunjungi website" in article.text.lower():
            for ket in article.findAll('p')[-7:]:
                ket.decompose()

        if "baca juga" in article.text.lower():
            for baca in article.findAll('span', attrs = {'style':'font-size:20px;'}):
                baca.decompose()

        #extract content
        detail = BeautifulSoup(article.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.get_text(strip=True)))
        articles['content'] = content
        print('memasukkan berita id ', articles['id'])

        return articles

    def insertDB(self, articles):
        """
        Untuk memasukkan berita ke DB
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
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
            con.close()
            return True
        else:
            cursor.close()
            print('salah2')
            con.close()
            return False
