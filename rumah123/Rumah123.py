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

class Rumah123:
    def getAllBerita(self, details, page, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url rajamobil
        link pada indeks category tertentu
        category = berita
        date = Y/m/d
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "https://artikel.rumah123.com/search?page="+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page, cat, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', {'class':'news-list-container'})
        indeks = contentDiv.findAll('li', class_="list-group-item")
        flag = True
        for post in indeks:
            link = [post.find('a', href=True)['href'], ""]
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
                    details.append(detail)

        if flag:
            el_page = soup.find('ul', class_="pagination")
            if el_page:
                max_page = int(el_page.findAll('li')[-2].get_text(strip=True).strip(' '))
                active_page = int(el_page.find('li', {'class':'active'}).get_text(strip=True).strip(' '))
                # max_page = 3
                if active_page != max_page:
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
        bc = soup.find('ol', class_="breadcrumb")
        #category
        articles['category'] = 'Properti'
        articles['subcategory'] = bc.findAll('li')[-2].get_text(strip=True)

        articles['url'] = url

        article = soup.find('div', class_="col-xs-12 col-sm-12 col-md-8 col-lg-8")

        #extract date
        pubdate = article.find('meta', {'itemprop':'datePublished'})['content']
        pubdate = pubdate.strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')
        articles['id'] = int(url.split('-')[-1])

        #extract author
        author = article.find('div', {'class': 'post-author'})
        articles['author'] = author.get_text(strip=True) if author else ''

        #extract title
        articles['title'] = soup.find('meta', {'property':'og:title'})['content']

        #source
        articles['source'] = 'rumah123'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        # tags = article.findAll('meta', {"property":"article:tag"})
        #tag tidak tersedia
        articles['tags'] = ''

        #extract images
        articles['images'] = soup.find("meta", attrs={'property':'og:image'})['content']

        #extract detail
        detail = article.find('div', attrs={"class":"post-text"})

        #hapus video sisip
        for div in detail.findAll('div'):
            div.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        #hapus all noscript
        for ns in detail.findAll('noscript'):
            ns.decompose()

        #hapus all figure
        for fig in detail.findAll('figure'):
            fig.decompose()

        #hapus linksisip
        for ls in detail.findAll('p'):
            if 'baca' in ls.find('p').get_text(strip=True).lower():
                if (ls.find('strong')) and (ls.find('a')):
                    ls.decompose()

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
