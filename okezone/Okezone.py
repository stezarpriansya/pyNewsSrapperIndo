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

class Okezone:
    def getAllBerita(self, details, page, offset=0, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url okezone
        link pada indeks category tertentu
        date format : dd/mm/YYYY
        """

        print("page ", page)
        url = "https://index.okezone.com/bydate/index/"+date+"/"+str(offset)+"/"
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page, page*15, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', class_="news-content")
        indeks = contentDiv.findAll('li')
        for post in indeks:
            link = [post.find('a', href=True)['href'], ""]
            detail = self.getDetailBerita(link)
            if detail:
                if self.insertDB(detail):
                    details.append(detail)

        el_page = soup.find('div', class_="pagination-indexs")
        if el_page.findAll('a'):
            max_page = (int(el_page.findAll('a')[-1]['href'][50:-1])/15)+1

            if page < max_page:
                time.sleep(2)
                details = self.getAllBerita(details, page+1, page*15, date)

        return 'berhasil ambil semua berita'

    def getDetailBerita(self, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(2)
        articles = {}
        #link
        url = link[0]
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            self.getDetailBerita(link)
        except:
            return False
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        #extract scrip json ld
        scripts_all = soup.findAll('script', attrs={'type':'application/ld+json'})
        if scripts_all:
            scripts = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",scripts_all[-1].get_text(strip=True)))
            scripts = json.loads(scripts)
            if scripts['datePublished'] == '':
                scripts = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",scripts_all[0].get_text(strip=True)))
                scripts = json.loads(scripts)
        else:
            return False

        #extract subcategory from breadcrumb
        bc = soup.find('div', class_="breadcrumb")
        if not bc:
            return False
        cat = bc.findAll('a')[-2].get_text(strip=True)
        sub = bc.findAll('a')[-1].get_text(strip=True)
        if ("foto" in sub.lower()) or  ("video" in sub.lower()):
            return False

        #category
        articles['category'] = cat
        articles['subcategory'] = sub

        articles['url'] = url

        article = soup.find('div', class_="container-bodyhome-left")
        # print(scripts)
        #extract date
        pubdate = scripts['datePublished']
        pubdate = pubdate.strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        id = scripts['mainEntityOfPage']['@id']
        try:
            articles['id'] = int(id)
        except ValueError as verr:
            articles['id'] = int(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S").timestamp()) + len(url)
        except Exception as ex:
            articles['id'] = int(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S").timestamp()) + len(url)

        #extract author
        articles['author'] = scripts['author']['name']

        #extract title
        articles['title'] = scripts['headline']

        #source
        articles['source'] = 'okezone'

        #extract comments count
        komentar = soup.find('span', class_="commentWidget-total")
        articles['comments'] = int(komentar.find('b').get_text(strip=True).strip(' \t\n\r')) if komentar else 0

        #extract tags
        tags = article.find('div', class_="detail-tag")
        articles['tags'] = ','.join([x.get_text(strip=True) for x in tags.findAll('a')]) if tags else ''

        #extract images
        images = soup.find("meta", attrs={'property':'og:image'})
        articles['images'] = images['content'] if images else ''

        #extract detail
        detail = article.find('div', attrs={'id':'contentx', 'class':'read'})

        #hapus link sisip
        for link in detail.findAll('table', class_="linksisip"):
            link.decompose()

        #hapus video sisip
        if detail.findAll('div'):
            for div in detail.findAll('div'):
                if div.find('script'):
                    div.decompose()
        #hapus all setelah clear fix
        mb20 = detail.find('div', class_="clearfix mb20")
        if mb20:
            for det in mb20.findAllNext():
                det.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        #hapus all noscript
        for ns in detail.findAll('noscript'):
            ns.decompose()

        #hapus linksisip
        for ls in detail.findAll('a'):
            if ls.find('strong'):
                if 'baca' in ls.find('strong').get_text(strip=True).lower():
                    ls.decompose()

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
