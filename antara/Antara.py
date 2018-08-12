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

class Antara:
    def getAllBerita(self, details, page, date=datetime.strftime(datetime.today(), '%d-%m-%Y')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : dd-mm-YYYY
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "https://www.antaranews.com/search/%20/"+date+"/"+date+"/"+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', attrs={'class':'post-content clearfix'})
        indeks = contentDiv.findAll('article')
        for post in indeks:
            link = [post.find('a', href=True)['href'], ""]
            detail = self.getDetailBerita(link)
            if detail:
                if self.insertDB(con, detail):
                    # print("Insert berita ", articles['title'])
                    details.append(detail)

        el_page = soup.find('ul', class_="pagination pagination-sm")
        if el_page:
            last_page = el_page.findAll('a')[-1].get_text(strip=True).replace('\n', '').strip(' ')
            active_page = el_page.find('li', class_="active").get_text(strip=True).replace('\n', '').strip(' ')

            if last_page != active_page:
                time.sleep(10)
                details = self.getAllBerita(details, int(active_page)+1, date)
        con.close()
        return 'berhasil ambil semua berita'

    def getDetailBerita(self, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(10)
        articles = {}
        #link
        url = link[0]
        if ('video' in url.split('/')) or ('foto' in url.split('/')):
            return False
        
        response = requests.get(url)
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        #extract scrip json ld
        scripts = soup.findAll('script', attrs={'type':'application/ld+json'})
        if scripts:
            scripts = json.loads(scripts[0].get_text(strip=True))
        else:
            return False

        #category
        articles['category'] = scripts["keywords"][0][0].split(':')[0]
        articles['subcategory'] = scripts["keywords"][0][0].split(':')[1]

        articles['url'] = url

        article = soup.find('article', class_="post-wrapper clearfix")

        #extract date
        pubdate = scripts['datePublished']
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        id = soup.find('input', {'name': 'news_id'})
        articles['id'] = int(id.get('value')) if id else int(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S").timestamp()) + len(url)

        #extract author
        articles['author'] = scripts['author']['name']

        #extract title
        articles['title'] = scripts['headline']

        #source
        articles['source'] = 'antara'

        #extract comments count
#         articles['comments'] = int(soup.find('span', class_="commentWidget-total").find('b').get_text(strip=True).strip(' \t\n\r'))
        articles['comments'] = 0

        #extract tags
        tags = soup.find('ul', class_="tags-widget clearfix")
        articles['tags'] = ','.join([x.get_text(strip=True) for x in tags.findAll('a')]) if tags else ''

        #extract images
        images =  soup.find("meta", attrs={'name':"twitter:image"})
        articles['images'] = images['content'] if images else ''

        #extract detail
        detail = article.find('div', attrs={'class':'post-content clearfix'})

        #hapus pewarta
        for p in detail.findAll('p', class_="text-muted small"):
            p.decompose()

        #hapus video sisip
        for div in detail.findAll('div'):
            div.decompose()

        #hapus video sisip
        for strong in detail.findAll('strong'):
            if ("foto" in sub.get_text(strip=True).lower()) or  ("video" in sub.get_text(strip=True).lower()):
                strong.decompose()

        #hapus link sisip
        for b in detail.findAll('b'):
            if ("baca juga" in b.get_text(strip=True).lower()):
                b.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.get_text(strip=True)))
        articles['content'] = content
        print('memasukkan berita id ', articles['id'])

        return articles

    def insertDB(self, con, articles):
        """
        Untuk memasukkan berita ke DB
        """
        if articles==False:
            return False
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
