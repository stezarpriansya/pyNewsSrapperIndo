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
import json
import time
from requests.exceptions import ConnectionError
import unicodedata
import mysql.connector
import math

class Oto:
    def getAllBerita(self, details, page, cat, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        category : berita-mobil, berita-motor
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "https://www.oto.com/"+cat+"?page="+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(5)
            details = self.getAllBerita(details, page, cat, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        indeks = soup.findAll('li', class_="card")
        flag = True
        for post in indeks:
            link = [post.find('a', href=True)['href'], "cat"]
            #check if there are a post with same url
            cursor = con.cursor()
            query = "SELECT count(*) FROM article WHERE url like '"+link[0]+"'"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            # if(result[0] > 0):
            #     flag = False
            #     break
            # else:
            detail = self.getDetailBerita(link)
            if self.insertDB(con, detail):
                details.append(detail)
        if flag:
            max_page = math.ceil((int(soup.find('div', class_="news-count").find('span').get_text(strip=True)))/12)
            # max_page = 2
            if page <= max_page:
                time.sleep(5)
                details = self.getAllBerita(details, page+1, cat, date)
        con.close
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
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        #extract subcategory from breadcrumb
        bc = soup.find('ul', class_="breadcrumb")
        if not bc:
            return False

        sub = bc.findAll('li')[-2].get_text(strip=True)

        if ("foto" in sub.lower()) or  "video" in sub.lower():
            return False

        #category
        articles['category'] = 'Otomotif'
        articles['subcategory'] = sub

        #article_url
        articles['url'] = url

        #article
        article = soup.find('div', class_="content")

        #extract date
        scripts = json.loads(soup.findAll('script', {'type':'application/ld+json'})[-1].get_text(strip=True))
        pubdate = scripts['datePublished']
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        #articleid
        articleid = url.replace('/','')
        articleid = url.split('-')
        articleid = int(articleid[-1][-5:])
        articles['id'] = articleid

        #extract editor
        author = soup.find('div', class_="publish-cont").find('a').get_text(strip=True)
        articles['author'] = author

        #extract title
        title = soup.find('article', class_="newslistouter container-base").find('h1').get_text(strip=True)
        articles['title'] = title if title else ''

        #source
        articles['source'] = 'oto'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        articles['tags'] = scripts['keywords']

        #extract images
        image = article.find('img')['src']
        articles['images'] = image

        detail = article
        #hapus link sisip
        for img in detail.findAll('img'):
            img.decompose()

        for div in detail.findAll('div'):
            div.decompose()

        for src in detail.findAll('p'):
            if ("sumber:" in src.get_text(strip=True).lower()):
                src.decompose()

        for p in detail.findAll('p'):
            if ("baca juga" in p.get_text(strip=True).lower()) and (p.find('a')):
                p.decompose()
        # print(detail)
        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.get_text(strip=True)))
        # print(content)
        articles['content'] = content
        #print('memasukkan berita id ', articles['id'])

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
