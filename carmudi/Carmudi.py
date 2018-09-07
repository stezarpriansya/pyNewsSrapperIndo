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
        print("page ", page)
        url = "https://www.carmudi.co.id/journal/page/"+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', class_="vw-loop vw-loop--medium vw-loop--medium-6 vw-loop--col-2")
        indeks = contentDiv.findAll('a', class_="vw-post-box__read-more vw-button vw-button--small vw-button--accent", href=True)
        flag = True
        for post in indeks:
            link = [post['href'], ""]
            #check if there are a post with same url
            con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
            cursor = con.cursor()
            query = "SELECT count(*) FROM article WHERE url like '"+link[0]+"'"
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            con.close()
            # comment sementara
            if(result[0] > 0):
                flag = False
                break
            else:
                detail = self.getDetailBerita(link)
                if detail:
                    if self.insertDB(detail):
                        details.append(detail)

        if flag:
            el_page = soup.find('div', class_="vw-page-navigation-pagination")
            if el_page:
                max_page = int(el_page.findAll('a')[-2].get_text(strip=True).replace('\n', '').strip(' '))

                if page < max_page:
                    time.sleep(10)
                    details = self.getAllBerita(details, page+1)

        return 'berhasil ambil semua berita'

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
        bc = soup.find('div', class_="vw-breadcrumb vw-breadcrumb-envirra")
        if not bc:
            return False

        sub = bc.findAll('span', {'typeof':'v:Breadcrumb'})
        articles['subcategory'] = sub[1].get_text(strip=True) if sub else ''
        #category
        articles['category'] = 'Otomotif'
        articles['url'] = url

        article = soup.find('article', class_="vw-main-post")

        #extract date
        #2018-07-27T15:18:00+00:00
        pubdate = article.find("time", attrs={'itemprop':'datePublished'})
        pubdate = pubdate['datetime'] if pubdate else '1970-01-01T01:01:01+00:00'
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        id = soup.find("a", class_="vw-post-shares-social vw-post-shares-social-facebook")
        articles['id'] = int(id['data-post-id']) if id else int(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S").timestamp()) + len(url)

        #extract author
        author = article.find("a", class_="author-name")
        articles['author'] = author.get_text(strip=True) if author else ''

        #extract title
        title = article.find('h1', class_="entry-title")
        articles['title'] = title.get_text(strip=True) if title else ''

        #source
        articles['source'] = 'carmudi'

        #extract comments count
        comments = soup.find('a', class_="vw-post-meta-icon vw-post-comment-count")
        articles['comments'] = int(comments.get_text(strip=True).strip(' \t\n\r') if comments else '0')

        #extract tags
        tags = article.find('div', class_="vw-tag-links")
        articles['tags'] = ','.join([x.get_text(strip=True) for x in tags.findAll('a')]) if tags else ''

        #extract images
        images = soup.find('meta', attrs={'property':'og:image'})
        articles['images'] = images['content'] if images else ''

        #extract detail
        detail = article.find('div', class_="vw-post-content clearfix")

        #hapus div
        if detail.findAll('div'):
            for div in detail.findAll('div'):
                if div.find('script'):
                    div.decompose()

        #hapus figure sisip
        for figure in detail.findAll('figure'):
            figure.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        for p in detail.findAll('p'):
           if ("baca juga" in p.get_text(strip=True).lower()) and (p.find('a')):
               p.decompose()
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
