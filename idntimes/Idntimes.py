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

class Idntimes:
    def getAllBerita(self, details, cat_link, page, date=datetime.strftime(datetime.today(), '%Y-%m-%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY-mm-dd
        """
        print("page ", page)
        url = "https://www.idntimes.com/ajax/index?category="+cat_link+"&type=all&page="+str(page)+"&date="+date
        print(url)
        # Make the request and create the restry:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, cat_link, page+1, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        indeks = soup.findAll('div', class_="box-latest box-list ")
        if indeks:
            for post in indeks:
                link = [post.find('a', href=True)['href'], cat_link]
                detail = self.getDetailBerita(link)
                details.append(detail)
            time.sleep(10)
            details = self.getAllBerita(details, cat_link, page+1, date)

        return details

    def getDetailBerita(self, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(10)
        articles = {}
        #link
        url = link[0]
        print(url)
        response = requests.get(url)
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        #extract scrip json ld
        scripts_all = soup.findAll('script', attrs={'type':'application/ld+json'})
#         print(len(scripts_all))
        scripts = json.loads(scripts_all[-2].text)
        scripts2 = json.loads(scripts_all[-1].text)

        #category
        articles['category'] = scripts2['itemListElement'][0]['item']['name']
        articles['subcategory'] = scripts2['itemListElement'][1]['item']['name']

        articles['url'] = url

        article = soup.find('section', class_="content-post clearfix")

        #extract date
        pubdate = scripts['datePublished']
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')
        articles['id'] = int(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S").timestamp()) + len(url)

        #extract author
        articles['author'] = scripts['author']['name']

        #extract title
        articles['title'] = scripts['headline']

        #source
        articles['source'] = 'idntimes'

        #extract comments count
#         articles['comments'] = int(soup.find('span', class_="commentWidget-total").find('b').text.strip(' \t\n\r'))
        articles['comments'] = 0

        #extract tags
        tags = article.find('div', class_="content-post-topic").findAll('a')
        articles['tags'] = ','.join([x.text for x in tags])

        #extract images
        articles['images'] = scripts['image']['url']

        #extract detail
        detail = article.find('article', attrs={'id':'article-content'})

        #hapus div
        if detail.findAll('div'):
            for div in detail.findAll('div'):
                div.decompose()

        #hapus link sisip
        if detail.findAll('strong'):
            for b in detail.findAll('strong'):
                if ("baca juga" in b.text.lower()):
                    b.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',detail.text)
        articles['content'] = content
        print('memasukkan berita id ', articles['id'])

        return articles
