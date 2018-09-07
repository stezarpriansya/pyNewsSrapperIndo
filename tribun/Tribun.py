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

        print("page ", page)
        url = "http://www.tribunnews.com/index-news?date="+date+"&page="+str(page)
        print(url)
        # Make the request and create the response object: response
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')  # Last I checked this was necessary.
        options.add_argument('--disable-extensions')
        options.add_argument("--incognito");

        driver = webdriver.Chrome("../chromedriver.exe", chrome_options=options)
        html = ''
        try:
            driver.get(url)
        except ConnectionError:
            driver.quit()
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page, date)
        # Extract HTML texts contained in Response object: html
        html = driver.page_source
        driver.quit()
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        indeks = soup.findAll('li', class_="ptb15")
        flag = True
        for post in indeks:
            link = [post.find('h3').find('a', href=True)['href'], ""]
            #check if there are a post with same url
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
            el_page = soup.find('div', class_="paging")
            if el_page:
                check_link = el_page.findAll('a')[-1]
                if "id" in check_link:
                    max_page = page
                else:
                    max_page = int(check_link['href'].replace('\n', '').split('page=')[-1])

                if page < max_page:
                    time.sleep(5)
                    details = self.getAllBerita(details, page+1, date)


        return soup

    def getDetailBerita(self, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(5)
        articles = {}
        #link
        url = link[0]+'?page=all'
        print(url)
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')  # Last I checked this was necessary.
        options.add_argument('--disable-extensions')
        options.add_argument("--incognito");

        driver = webdriver.Chrome("../chromedriver.exe", chrome_options=options)
        html = ''
        try:
            driver.get(url)
            # Extract HTML texts contained in Response object: html
        except ConnectionError:
            driver.quit()
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getDetailBerita(link)

        html = driver.page_source
        driver.quit()

        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        scripts = soup.findAll('script', {'type':'application/ld+json'})
        if scripts:
            scripts = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",scripts[0].get_text(strip=True)))
            scripts = json.loads(scripts)
        else:
            return False
        #category
        categories = soup.findAll('meta', {'name':'cXenseParse:category'})

        articles['category'] = categories[0]['content'] if categories else 'Berita'
        if len(categories) > 1:
            articles['subcategory'] = categories[1]['content'] if categories else ''
        else:
            articles['subcategory'] = ''

        articles['url'] = url

        article = soup.find('div', {'id':'article_con'})

        #extract date
        pubdate = scripts['datePublished']
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        id = soup.find('meta', {"property":"android:app_id"})
        articles['id'] = int(id['content']) if id else int(datetime.strptime(pubdate, "%d-%b-%Y %H:%M").timestamp()) + len(url)

        #extract author
        articles['author'] = scripts['author']['name']

        #extract title
        articles['title'] = scripts['headline']

        #source
        articles['source'] = 'tribunnews'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = article.find('div', class_="mb10 f16 ln24 mb10 mt5")
        articles['tags'] = ','.join([x.get_text(strip=True).replace('#', '') for x in tags.findAll('a')]) if tags else ''

        #extract images
        articles['images'] = scripts['image']['url']

        #extract detail
        detail = article.find('div', attrs={'class':'side-article txt-article'})

        #hapus video sisip
        if detail.findAll('div'):
            for div in detail.findAll('div'):
                if div.find('script'):
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
