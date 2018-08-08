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
        date = datetime.strptime(date, '%Y/%m/%d')
        url = "https://www.gridoto.com/index?day="+str(date.date().day)+"&month="+str(date.date().month)+"&year="+str(date.date().year)+"&section=all&page="+str(page)
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
        indeks = soup.findAll('div', class_="news-list__item l-index clearfix")
        flag = True
        for post in indeks:
            subcategory = post.find('a', class_="cateskew").text.strip(' \t\n\r')
            link = [post.find('a', class_="news-list__link", href=True)['href'], subcategory]
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
            el_page = soup.find('ul', class_="pagination_number")
            if el_page:
                last_page = int(el_page.findAll('li')[-1].text.replace('\n', '').strip(' '))
                active_page = int(el_page.find('li', class_="active").text.replace('\n', '').strip(' '))
                # last_page = 3
                if last_page != active_page:
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

        scripts = json.loads(soup.findAll('script', {'type':'application/ld+json'})[-1].text)
        #category
        articles['category'] = 'Otomotif'
        articles['subcategory'] = link[1]

        articles['url'] = url

        article = soup.find('div', class_="read__article clearfix")

        #extract date
        pubdate = soup.find('meta', {'name':'content_date'})['content']
        pubdate = pubdate.strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')
        articles['id'] = int(soup.find('meta', {'name':'content_id'})['content'])

        #extract author
        articles['author'] = soup.find('meta', {'name':'content_author'})['content']

        #extract title
        articles['title'] = scripts['headline']

        #source
        articles['source'] = 'gridoto'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = soup.find('meta', {'name':'content_tag'})['content']
        articles['tags'] = tags

        #extract images
        articles['images'] = soup.find("meta", attrs={'property':'og:image'})['content']

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
                if 'baca' in ls.find('strong').text.lower():
                    ls.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',detail.text)
        articles['content'] = content
        print('memasukkan berita id ', articles['id'])

        return articles
