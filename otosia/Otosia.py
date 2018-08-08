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

class Otosia:
    def getIndeksLink(self, links, page, cat_link, cat, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        category : berita, tips, lifetyle, selebriti, komunitas, galeri
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "https://www.otosia.com/"+cat_link+"/index"+str(page)+".html"
        print(url)

        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            links = self.getIndeksLink(links, page+1, cat, category, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        indeks = soup.find('div', attrs={"id":"mobart-box-big"})
        flag = True
        for post in indeks.findAll('h2'):
            link = ["https://www.otosia.com"+ post.find('a', href=True)['href'], cat]
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
            el_page = soup.find('div', class_="simple-pagination__container")
            if el_page:
                last_page = el_page.findAll('a')[-2].text
                active_page = el_page.find('span', class_="mpnolink").text

                if last_page > active_page:
                    time.sleep(10)
                    links = self.getIndeksLink(links, int(active_page)+1, cat, date)

        con.close()
        return links

    def getDetailBerita(self, links):
        """
        Mengambil seluruh element dari halaman berita
        """
        all_articles = []
        for link in links:
            time.sleep(10)
            #link
            url = link[0]
            response = requests.get(url)
            html = response.text
            # Create a BeautifulSoup object from the HTML: soup
            soup = BeautifulSoup(html, "html5lib")

            #extract subcategory from breadcrumb
            bc = soup.find('div', attrs={"id":"v5-navigation"})
            if not bc:
                continue

            sub = bc.findAll('a')[-1].text
            if ("foto" in sub.lower()) or  "video" in sub.lower():
                continue

            #category
            articles['category'] = 'Otomotif'
            articles['subcategory'] = sub

            #article_url
            articles['url'] = url

            #article
            article = soup.find('div', class_="OtoDetailNews")

            #extract date
            pubdate = soup.find('span', class_="newsdetail-schedule").text
            pubdate = pubdate.strip(' \t\n\r')
            articles['pubdate']=datetime.strftime(datetime.strptime(pubdate, "%A, %d %B %Y %H:%M"), "%Y-%m-%d %H:%M:%S")
            articles['pubdate']

            #articleid
            articles['id'] = int(datetime.strptime(pubdate, "%d %B %Y").timestamp()) + len(url)

            #extract editor
            author = soup.findAll('span', class_="newsdetail-schedule")[1].text
            author = author.replace('Editor : ',"")
            author = author.strip(' ')
            articles['author'] = author

            #extract title
            title = soup.find('h1', class_="OtoDetailT").text
            articles['title'] = title

            #source
            articles['source'] = 'otosia.com'

            #extract comments count
            articles['comments'] = 0

            #extract tags
            tags = soup.find('div', class_='detags').findAll('a')
            tags = ','.join([x.text for x in tags])
            articles['tags'] = tags

            #extract images
            image = soup.find('img', class_="lazy_loaded")['data-src']
            articles['image'] = image

            #hapus link sisip
            for link in article.findAll('div'):
                link.decompose()

            #extract content
            detail = BeautifulSoup(article.decode_contents().replace('<br/>', ' '), "html5lib")
            content = re.sub(r'\n|\t|\b|\r','',detail.text)
            articles['content']
            #print('memasukkan berita id ', articles['id'])
            all_articles.append(articles)
        return all_articles
