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

class Carreview:
    def getAllBerita(self, details, page, cat, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url carreview
        link pada indeks category tertentu
        category = how-to, news, carpedia, versus
        date = Y/m/d
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "http://carreview.id/"+cat+"?page="+str(page)
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
        indeks = soup.findAll('div', class_="post")
        flag = True
        for post in indeks:
            link = [post.find('a', href=True)['href'], cat]
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
            el_page = soup.find('ul', class_="pagination")
            if el_page:
                last_page = int(el_page.findAll('li')[-2].text.replace('\n', '').strip(' '))
                # last_page = 3
                if last_page != page:
                    time.sleep(5)
                    details = self.getAllBerita(details, page+1, cat, date)

        con.close()
        return details

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

        #category
        articles['category'] = 'Otomotif'
        articles['subcategory'] = link[1]

        articles['url'] = url

        article = soup.find('div', class_="left-content")

        #extract date
        pubdate = article.find('li', {'class':'publish-date'}).text.split(',')
        pubdate = pubdate[1].strip(' \t\n\r').replace('Ags', 'Agt')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%d-%b-%Y %H:%M"), '%Y-%m-%d %H:%M:%S')
        articles['id'] = int(datetime.strptime(pubdate, "%d-%b-%Y %H:%M").timestamp()) + len(url)

        #extract author
        articles['author'] = article.find('span', {'itemprop': 'author'}).text

        #extract title
        articles['title'] = article.find('h1', {'class': 'entry-title'}).text

        #source
        articles['source'] = 'carreview'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = article.find('div', class_="post-meta").findAll('a')
        articles['tags'] = ','.join([x.text.replace('#', '') for x in tags])

        #extract images
        articles['images'] = soup.find("meta", attrs={'property':'og:image'})['content']

        #extract detail
        detail = article.find('div', attrs={'class':'entry-content'})

        #hapus video sisip
        for div in detail.findAll('div'):
            div.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        #hapus all noscript
        for ns in detail.findAll('noscript'):
            ns.decompose()

        #hapus desc
        for p in detail.findAll('p', class_="lead"):
            p.decompose()

        #hapus linksisip
        for ls in detail.findAll('a'):
            if ls.find('strong'):
                if 'baca' in ls.find('strong').text.lower():
                    ls.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.text))
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
            cursor.execute(add_article, articles)
            con.commit()
            print('masuk')
            cursor.close()
            return True
        else:
            cursor.close()
            print('salah2')
            return False
