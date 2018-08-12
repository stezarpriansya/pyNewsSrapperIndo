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

class Gridoto:
    def getAllBerita(self, details, page, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url carreview
        link pada indeks category tertentu
        category = all
        date = Y/m/d
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        date2 = datetime.strptime(date, '%Y/%m/%d')
        url = "https://www.gridoto.com/index?day="+str(date2.date().day)+"&month="+str(date2.date().month)+"&year="+str(date2.date().year)+"&section=all&page="+str(page)
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
        indeks = soup.findAll('div', class_="news-list__item l-index clearfix")
        flag = True
        for post in indeks:
            subcategory = post.find('a', class_="cateskew").get_text(strip=True).strip(' \t\n\r')
            link = [post.find('a', class_="news-list__link", href=True)['href'], subcategory]
            #check if there are a post with same url
            cursor = con.cursor()
            query = "SELECT count(*) FROM article WHERE url like '"+link[0]+"'"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            #comment sementara
            # if(result[0] > 0):
            #     flag = False
            #     break
            # else:
            detail = self.getDetailBerita(link)
            if detail:
                if self.insertDB(con, detail):
                    # print("Insert berita ", articles['title'])
                    details.append(detail)

        if flag:
            el_page = soup.find('ul', class_="pagination_number")
            if el_page:
                last_page = el_page.findAll('li')[-1].get_text(strip=True).replace('\n', '').strip(' ')
                active_page = el_page.find('li', class_="active").get_text(strip=True).replace('\n', '').strip(' ')
                # last_page = 2
                if last_page != active_page:
                    time.sleep(5)
                    details = self.getAllBerita(details, page+1, date)

        con.close()
        return 'berhasil ambil semua berita'

    def getDetailBerita(self, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(5)
        articles = {}
        #link
        url = link[0]+'?page=all'
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getDetailBerita(link)
        html2 = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html2, "html5lib")
        print(url)
        scripts = soup.findAll('script', attrs={'type':'application/ld+json'})
        if scripts:
            scripts = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",scripts[-1].get_text(strip=True)))
            scripts = json.loads(scripts)
        else:
            return False
        #category
        articles['category'] = 'Otomotif'
        articles['subcategory'] = link[1]

        articles['url'] = url

        article = soup.find('div', class_="read__article clearfix")

        #extract date
        pubdate = soup.find('meta', {'name':'content_date'})
        pubdate = pubdate['content'] if pubdate else '1970-01-01 00:00:00'
        pubdate = pubdate.strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        id = soup.find('meta', {'name':'content_id'})
        articles['id'] = int(id['content']) if id else int(datetime.strptime(pubdate, "%d-%b-%Y %H:%M").timestamp()) + len(url)

        #extract author
        author = soup.find('meta', {'name':'content_author'})
        articles['author'] = author['content'] if author else ''

        #extract title
        articles['title'] = scripts['headline']

        #source
        articles['source'] = 'gridoto'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = soup.find('meta', {'name':'content_tag'})
        articles['tags'] = tags['content'] if tags else ''

        #extract images
        images = soup.find("meta", attrs={'property':'og:image'})
        articles['images'] = images['content'] if images else ''

        #extract detail
        detail = article.find('div', attrs={'class':'read__right'})

        #hapus video sisip
        for div in detail.findAll('div'):
            div.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        #hapus all noscript
        for ns in detail.findAll('noscript'):
            ns.decompose()

        #hapus linksisip
        for ls in detail.findAll('p'):
            if ls.find('strong'):
                if 'baca' in ls.find('strong').get_text(strip=True).lower():
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
        print(articles['title'])
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
