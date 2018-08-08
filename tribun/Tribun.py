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

class Tribun:
    def getAllBerita(self, details, page, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url carreview
        link pada indeks category tertentu
        category = all
        date = Y/m/d
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "http://www.tribunnews.com/index-news?date="+date+"&page="+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page+1, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        indeks = soup.findAll('div', class_="ptb15")
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
                    print("Insert berita ", detail['title'])
                    details.append(detail)

        if flag:
            el_page = soup.find('div', class_="paging")
            if el_page:
                check_link = el_page.findAll('a')[-1]
                if "id" in check_link:
                    max_page = page
                else:
                    max_page = int(check_link['href'].replace('\n', '').split('page=')[-1])

                if page < max_page:
                    time.sleep(10)
                    details = self.getAllBerita(details, page+1, date)

        con.close()
        return details

    def getDetailBerita(self, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(10)
        articles = {}
        #link
        url = link[0]+'?page=all'
        response = requests.get(url)
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        scripts = json.loads(soup.findAll('script', {'type':'application/ld+json'})[0].text)
        #category
        categories = soup.findAll('meta', {'name':'cXenseParse:category'})
        articles['category'] = categories[0]['content']
        articles['subcategory'] = categories[1]['content']

        articles['url'] = url

        article = soup.find('div', {'id':'article_con'})

        #extract date
        pubdate = scripts['datePublished']
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')
        articles['id'] = int(soup.find('meta', {"property":"android:app_id"})['content'])

        #extract author
        articles['author'] = scripts['author']['name']

        #extract title
        articles['title'] = scripts['headline']

        #source
        articles['source'] = 'tribunnews'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = article.find('div', class_="mb10 f16 ln24 mb10 mt5").findAll('a')
        articles['tags'] = ','.join([x.text.replace('#', '') for x in tags])

        #extract images
        articles['images'] = scripts['image']['url']

        #extract detail
        detail = article.find('div', attrs={'class':'side-article txt-article'})

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
        for ls in detail.findAll('p', class_="baca"):
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
