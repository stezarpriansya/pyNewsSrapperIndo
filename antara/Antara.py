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

class Antara:
    def getAllBerita(self, details, page, date=datetime.strftime(datetime.today(), '%d-%m-%Y')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : dd-mm-YYYY
        """
        print("page ", page)
        url = "https://www.antaranews.com/search/%20/"+date+"/"+date+"/"+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, int(active_page)+1, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', attrs={'class':'post-content clearfix'})
        indeks = contentDiv.findAll('article')
        for post in indeks:
            link = [post.find('a', href=True)['href'], ""]
            detail = self.getDetailBerita(link)
            details.append(detail)

        el_page = soup.find('ul', class_="pagination pagination-sm")
        if el_page:
            last_page = el_page.findAll('a')[-1].text.replace('\n', '').strip(' ')
            active_page = el_page.find('li', class_="active").text.replace('\n', '').strip(' ')

            if last_page != active_page:
                time.sleep(10)
                details = self.getAllBerita(details, int(active_page)+1, date)

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

        #extract scrip json ld
        scripts = soup.findAll('script', attrs={'type':'application/ld+json'})[0].text
        scripts = json.loads(scripts)

        #category
        articles['category'] = scripts['"keywords"'][0][0].split(':')[1]
        articles['subcategory'] = ''

        articles['id'] = soup.find('input', {'name': 'news_id'}).get('value')

        articles['url'] = url

        article = soup.find('section', class_="content-post clearfix")

        #extract date
        pubdate = scripts['datePublished']
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        #extract author
        articles['author'] = scripts['author']['name']

        #extract title
        articles['title'] = scripts['headline']

        #source
        articles['source'] = 'antara'

        #extract comments count
#         articles['comments'] = int(soup.find('span', class_="commentWidget-total").find('b').text.strip(' \t\n\r'))
        articles['comments'] = 0

        #extract tags
        tags = article.find('ul', class_="tags-widget clearfix").findAll('a')
        articles['tags'] = ','.join([x.text for x in tags])

        #extract images
        articles['images'] = soup.find("meta", attrs={'name':"twitter:image"})['content']

        #extract detail
        detail = article.find('div', attrs={'class':'post-content clearfix'})

        #hapus pewarta
        for p in detail.findAll('p', class_="text-muted small"):
            p.decompose()

        #hapus video sisip
        for div in detail.findAll('div'):
            div.decompose()

        #hapus video sisip
        for strong in detail.findAll('strong'):
            if ("foto" in sub.text.lower()) or  ("video" in sub.text.lower()):
                strong.decompose()

        #hapus link sisip
        for b in detail.findAll('b'):
            if ("baca juga" in b.text.lower()):
                b.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',detail.text)
        articles['content'] = content
        print('memasukkan berita id ', articles['id'])

        return articles
