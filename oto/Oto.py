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

class Oto:
    def getIndeksLink(self, links, page, cat, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        category : berita-mobil, berita-motor
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "https://www.oto.com/"+cat+"?page"+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            links = self.getIndeksLink(links, page+1, cat, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        indeks = soup.findAll('li', class_="card")
        flag = True
        for post in indeks:
            link = [post.find('a', href=True)['href'], "cat"]
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
                links.append(link)
        if flag:
            max_page = math.ceil((int(soup.find('div', class_="news-count").find('span').text))/12)
            if page <= max_page:
                time.sleep(10)
                links = self.getIndeksLink(links, page+1, cat, date)
        con.close
        return links

    def getDetailBerita(self, links):
        """
        Mengambil seluruh element dari halaman berita
        """
        all_articles = []
        for link in links:
            time.sleep(10)
            articles = {}
            #link
            url = link[0]
            response = requests.get(url)
            html = response.text
            # Create a BeautifulSoup object from the HTML: soup
            soup = BeautifulSoup(html, "html5lib")

            #extract subcategory from breadcrumb
            bc = soup.find('ul', class_="breadcrumb")
            if not bc:
                continue

            sub = bc.findAll('li')[-2].text

            if ("foto" in sub.lower()) or  "video" in sub.lower():
                continue

            #category
            articles['category'] = 'Otomotif'
            articles['subcategory'] = sub

            #article_url
            articles['url'] = url

            #article
            article = soup.find('div', class_="content")

            #extract date
            scripts = json.loads(soup.findAll('script', {'type':'application/ld+json'})[-1].text)
            pubdate = scripts['datePublished']
            pubdate = pubdate[0:19].strip(' \t\n\r')
            articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

            #articleid
            articleid = url.replace('/','')
            articleid = url.split('-')
            articleid = int(articleid[-1][-5:])
            articles['id'] = articleid

            #extract editor
            author = soup.find('div', class_="publish-cont").find('a').text
            articles['author'] = author

            #extract title
            title = soup.find('article', class_="newslistouter container-base").find('h1').text
            articles['title'] = title

            #source
            articles['source'] = 'oto.com'

            #extract comments count
            articles['comments'] = 0

            #extract tags
            articles['tags'] = scripts['keywords']

            #extract images
            image = article.find('img')['src']
            articles['image'] = image

            #hapus link sisip
            for link in article.findAll('img'):
                link.decompose()

            for link in article.findAll('div'):
                link.decompose()

            #extract content
            detail = BeautifulSoup(article.decode_contents().replace('<br/>', ' '), "html5lib")
            content = re.sub(r'\n|\t|\b|\r','',detail.text)
            articles['content']
            #print('memasukkan berita id ', articles['id'])
            all_articles.append(articles)
        return all_articles
