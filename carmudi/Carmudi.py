import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import locale
locale.setlocale(locale.LC_ALL, 'ID')
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from requests.exceptions import ConnectionError
import unicodedata
import mysql.connector

class Carmudi:
    def getAllBerita(self, details, page):
        """
        Untuk mengambil seluruh url dalam post carmudi.co.id
        link pada indeks category tertentu
        date format : dd/mm/YYYY
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "https://www.carmudi.co.id/journal/page/"+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page+1)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', class_="vw-loop vw-loop--medium vw-loop--medium-6 vw-loop--col-2")
        indeks = contentDiv.findAll('a', class_="vw-post-box__read-more vw-button vw-button--small vw-button--accent")
        for post in indeks:
            link = [post.find('a', href=True)['href'], ""]
            detail = self.getDetailBerita(link)
            if self.insertDB(con, detail):
                print("Insert berita ", detail['title'])
                details.append(detail)

        el_page = soup.find('div', class_="vw-page-navigation-pagination")
        if el_page:
            max_page = int(el_page.findAll('a')[-2].text.replace('\n', '').strip(' '))

            if page < max_page:
                time.sleep(10)
                details = self.getAllBerita(details, page+1)
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

        #extract subcategory & category from breadcrumb
        bc = soup.find('div', class_="vw-post-categories")
        if not bc:
            return False

        if len(bc.findAll('a')) > 2 :
            cat = bc.findAll('a')[1].text
            sub = bc.findAll('a')[2].text
        else:
            cat = bc.findAll('a')[1].text
            sub = ''

        articles['subcategory'] = sub

        articles['id'] = int(soup.find("a", class_="vw-post-shares-social vw-post-shares-social-facebook")['data-post-id'])
        #category
        articles['category'] = cat
        articles['url'] = url

        article = soup.find('article', class_="vw-main-post")

        #extract date
        #2018-07-27T15:18:00+00:00
        pubdate = article.find("time", attrs={'itemprop':'datePublished'})['datetime']
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        #extract author
        articles['author'] = article.find("a", class_="author-name").text

        #extract title
        articles['title'] = article.find('h1', class_="entry-title").text

        #source
        articles['source'] = 'carmudi'

        #extract comments count
        articles['comments'] = int(soup.find('a', class_="vw-post-meta-icon vw-post-comment-count").strip(' \t\n\r'))

        #extract tags
        tags = article.find('div', class_="vw-tag-links").findAll('a')
        articles['tags'] = ','.join([x.text for x in tags])

        #extract images
        articles['images'] = soup.find('meta', attrs={'property':'og:image'})['content']

        #extract detail
        detail = article.find('div', class_="vw-post-content clearfix")

        #hapus div
        for div in detail.findAll('div'):
            div.decompose()

        #hapus figure sisip
        for figure in detail.findAll('figure'):
            figure.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        for p in detail.findAll('p'):
           if ("baca juga" in p.text.lower()) and (p.find('a')):
               p.decompose()
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
            if cursor.execute(add_article, articles):
                cursor.close()
                return True
            else:
                cursor.close()
                return False
        else:
            cursor.close()
            return False
