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
import mysql.connector

class Cintamobil:
    def getAllBerita(self, details, page, cat, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url cintamobil
        link pada indeks category tertentu
        category = berita-mobil, tips-trik
        date = Y/m/d
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "https://cintamobil.com/"+cat+"/"+cat+"/p"+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page+1, cat, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        indeks = soup.findAll('li', class_="item-carreview")
        flag = True
        for post in indeks:
            link = ["https://cintamobil.com"+post.find('a', href=True)['href'], cat.replace('-', '')]
            #check if there are a post with same url
            cursor = con.cursor()
            query = "SELECT count(*) FROM article WHERE url like '"+link[0]+"'"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            if(result[0] > 0):
                flag = False
                break
            else:
                detail = self.getDetailBerita(link)
                if self.insertDB(con, detail):
                    print("Insert berita ", detail['title'])
                    details.append(detail)

        if flag:
            el_page = soup.find('ul', class_="paging pull-right")
            if el_page:
                max_page = int(el_page.findAll('li')[-1].find('a', href=True)['href'].split('/')[-1].replace('p', '').strip(' '))
                # max_page = 3
                if page < max_page:
                    time.sleep(10)
                    details = self.getAllBerita(details, page+1, cat, date)
        con.close()
        return details

    def getDetailBerita(self, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(10)
        articles = {}
        #link
        url = link[0]
        response = requests.get(url)
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        #category
        articles['category'] = 'Otomotif'
        articles['subcategory'] = link[1]

        articles['url'] = url

        article = soup.find('div', class_="list-review w--100 pull-left")

        #extract date
        pubdate = article.find('div', {'class':'pull-left w--100'}).text
        pubdate = pubdate.strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%d/%m/%Y"), '%Y-%m-%d %H:%M:%S')
        articles['id'] = soup.find('input', {'id':'ArticleId'}).get('value')

        #extract author
        articles['author'] = article.find('span', {'class': 'blue-clr text-right full-width display-ib'}).text

        #extract title
        articles['title'] = soup.find('meta', {'property': 'og:title'})['content']

        #source
        articles['source'] = 'cintamobil'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = article.find('div', class_="w--100 pull-left text-left mg-top-20").findAll('a')
        articles['tags'] = ','.join([x.text for x in tags])

        #extract images
        articles['images'] = soup.find("meta", attrs={'property':'og:image'})['content']

        #extract detail
        detail = article.find('div', attrs={'class':'w--100 pull-left set-relative detail-font'})

        #hapus video sisip
        for div in detail.findAll('div'):
            div.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        #hapus all noscript
        for ns in detail.findAll('noscript'):
            ns.decompose()

        #hapus detailsisip
        for ls in detail.findAll('a'):
            if ls.find('strong'):
                if 'baca' in ls.find('strong').text.lower():
                    ls.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',detail.text)
        articles['content'] = content
        print('memasukkan berita id ', articles['id'])

        return articles

    def insertDB(self, con, articles):
        """
        Untuk memasukkan berita ke DB
        """
        cursor = con.cursor()
        query = "SELECT count(*) FROM article WHERE url like '"+articles['url']+"'"
        cursor.execute(query)
        result = cursor.fetchone()
        if result[0] <= 0:
            add_article = ("INSERT INTO article (post_id, author, pubdate, category, subcategory, content, comments, images, title, tags, url, source) VALUES (%(id)s, %(author)s, %(pubdate)s, %(category)s, %(subcategory)s, %(content)s, %(comments)s, %(images)s, %(title)s, %(tags)s, %(url)s, %(source)s)")
            # Insert article
            if cursor.execute(add_article, articles):
                cursor.close()
                return True
            else:
                cursor.close()
                return False
        else:
            cursor.close()
            return False
