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

class Propertiterkini:
    def getAllBerita(self, details, page, cat_link, category):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        category :  berita-properti
                    tips-properti
                    inspirasi
                    bahan-bangunan
        """

        print("page ", page)
        url = "https://www.propertiterkini.com/category/"+cat_link+"/page/"+str(page)+"/"
        print(url)

        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(5)
            details = self.getAllBerita(details, page, cat_link, category, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', class_="post-listing archive-box")
        flag = True
        if contentDiv:
            for post in contentDiv.findAll('h2'):
                link = [post.find('a', href=True)['href'], category]
                # check if there are a post with same url
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
            el_page = soup.find('div', class_='pagination')
            if el_page:
                max_page = int(el_page.find('span', class_='pages').text.split(' ')[-1])
                if page < max_page:
                    time.sleep(5)
                    details = self.getAllBerita(details, page+1, cat_link, category)

        return 'berhasil ambil semua berita'

    def getDetailBerita(self, link):

        time.sleep(5)
        articles = {}
        #link
        url = link[0]
        response = requests.get(url)
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        #articleid
        # article_id = soup.find('article', class_='hentry main read-page--core-article')
        # articles['id'] = int(article_id['data-article-id']) if article_id else ''

        #extract title
        title = soup.find('h1', class_="name post-title entry-title")
        articles['title'] = title.find('span').text if title else ''

        # if ("foto:" in title.lower()) or  "video:" in title.lower():
        #     return False

        bc = soup.find('div', {'id':'crumbs'})
        if not bc:
            return False
        sub = bc.findAll('a')[-1].text

        #category
        articles['category'] = 'properti'
        articles['subcategory'] = sub

        #article_url
        articles['url'] = url

        #article
        article = soup.find('div', class_='entry')

        #extract date
        pubdate = soup.find('meta', {'property':'article:published_time'})['content']
        pubdate = pubdate.strip(' \t\n\r')
        pubdate = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S+07:00"), "%Y-%m-%d %H:%M:%S")
        articles['pubdate'] = pubdate
        articles['id'] = int(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S").timestamp()) + len(url)

        #extract author
        author = soup.find('span', class_='post-meta-author')
        articles['author'] = author.get_text(strip=True) if author else ''

        #source
        articles['source'] = 'propertiterkini'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = soup.find('p', class_='post-tag')
        articles['tags'] = ','.join([x.get_text(strip=True) for x in tags.findAll('a')]) if tags else ''


        #extract images
        images = soup.find('div', class_='single-post-thumb').find('img')
        articles['images'] = images['src'] if images else ''

        #hapus link sisip
        for div in article.findAll('div'):
            div.decompose()

        for related in article.findAll('section', {'id':'related_posts'}):
            related.decompose()

        for ul in article.findAll('ul'):
            ul.decompose()

        for baca in article.findAll('p'):
            if "baca juga:" in baca.text.lower():
                baca.decompose()

        for com in article.findAll('p'):
            if "propertiterkini.com" in com.text.lower():
                baca.decompose()

        #extract content
        detail = BeautifulSoup(article.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.get_text(strip=True)))
        articles['content'] = content
        #print('memasukkan berita id ', articles['id'])

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
