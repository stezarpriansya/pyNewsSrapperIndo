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

class Otodriver:
    def getAllBerita(self, details, page, cat, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url otodriver
        link pada indeks category tertentu
        category = tips, berita
        date = Y/m/d
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "http://otodriver.com/"+cat+"?page="+str(page)+"&per-page=18"
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
        indeks = soup.findAll('div', class_="col-lg-4 col-xs-12 col-md-6")
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
                details.append(detail)

        if flag:
            el_page = soup.find('ul', class_="pagination")
            if el_page:
                last_page = int(el_page.findAll('li')[-2].text.replace('\n', '').strip(' '))
                # last_page = 3
                if last_page != page:
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

        article = soup.find('div', class_="left-content")

        #extract date
        pubdate = article.find('meta', {'itemprop':'datePublished'})['content']
        pubdate = pubdate.strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')
        articles['id'] = int(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S").timestamp()) + len(url)

        #extract author
        articles['author'] = soup.find('meta', {'property': 'article:author'})['content']

        #extract title
        articles['title'] = soup.find('meta', {'property': 'og:title'})['content']

        #source
        articles['source'] = 'otorider'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = article.find('div', class_="post-meta").findAll('a')
        articles['tags'] = ','.join([x.text.replace('#', '') for x in tags])

        #extract images
        articles['images'] = soup.find("meta", attrs={'property':'twitter:image'})['content']

        #extract detail
        detail = article.find('div', attrs={'class':'entry-content detail-content'})

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
