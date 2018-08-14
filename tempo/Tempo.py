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

class Tempo:
    def getAllBerita(self, details, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY-mm-dd
        """
    #     print("page ", page)
        url = "https://www.tempo.co/indeks/"+date
        print(url)

        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('section', {'id':'article'}).find('section', class_="list list-type-1")
        indeks = contentDiv.findAll('li')
        if indeks:
            for post in indeks:
                link = [post.find('a', {'class':'col'}, href=True)['href'], ""]
                con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
                cursor = con.cursor()
                query = "SELECT count(*) FROM article WHERE url like '"+link[0]+"'"
                cursor.execute(query)
                result = cursor.fetchone()
                cursor.close()
                con.close()
                if(result[0] <= 0):
                    detail = self.getDetailBerita(link)
                    if detail:
                        if self.insertDB(detail):
                            details.append(detail)
    #         links = getIndeksLink(links, date)

        return 'berhasil ambil semua berita'

    def getDetailBerita(self, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(5)
        articles = {}
        #link
        url = link[0]
        print(url)
        response = requests.get(url)
        html2 = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html2, "html5lib")

        #extract scrip json ld
        scripts_all = soup.findAll('script', attrs={'type':'application/ld+json'})
#         print(len(scripts_all))
        if scripts_all:
            scripts = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",scripts_all[0].get_text(strip=True)))
            scripts = re.sub(r'"articleBody".+', '', scripts)
            scripts = json.loads(html.unescape(scripts))
            scripts2 = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",scripts_all[1].get_text(strip=True)))
            scripts2 = json.loads(html.unescape(scripts2))
        else:
            return False
        #category
        articles['category'] = scripts2['itemListElement'][-2]['item']['name']
        articles['subcategory'] = scripts2['itemListElement'][-1]['item']['name']

        articles['url'] = url

        article = soup.find('article', {'itemtype':"http://schema.org/NewsArticle"})

        #extract date
        pubdate = scripts['datePublished']
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        id = soup.find('meta', {'property':"dable:item_id"})
        articles['id'] = int(id['content']) if id else int(datetime.strptime(pubdate, "%d-%b-%Y %H:%M").timestamp()) + len(url)

        #extract author
        articles['author'] = scripts['editor']['name']

        #extract title
        articles['title'] = scripts['headline']

        #source
        articles['source'] = 'tempo'

        #extract comments count
#         articles['comments'] = int(soup.find('span', class_="commentWidget-total").find('b').get_text(strip=True).strip(' \t\n\r'))
        articles['comments'] = 0

        #extract tags
        tags = article.find('div', class_="tags clearfix")
        articles['tags'] = ','.join([x.get_text(strip=True) for x in tags.findAll('a')]) if tags else ''

        #extract images
        articles['images'] = scripts['image']['url']

        #extract detail
        detail = article.find('div', attrs={'id':'isi'})

        #hapus div
        if detail.findAll('div'):
            for div in detail.findAll('div'):
                div.decompose()

        #hapus link sisip
        if detail.findAll('p'):
            for p in detail.findAll('p'):
                if ("baca:" in p.get_text(strip=True).lower()):
                    p.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
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
