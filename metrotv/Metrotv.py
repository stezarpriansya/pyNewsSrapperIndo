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
import json
import mysql.connector

class Metrotv:
    def getAllBerita(self, details, page, offset, cat_link, category, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY-mm-dd
        cat_link :  internatiol
                    ekonomi
                    bola
                    olahraga
                    teknologi
                    otomotif
                    hiburan
                    rona
        """
        # dates = ['2018/07/30','2018/07/29','2018/07/28','2018/07/27','2018/07/26','2018/07/25']
        print("page ", page)
        url = "http://"+cat_link+".metrotvnews.com/index/"+date+"/"+ str(offset)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(5)
            details = self.getAllBerita(details, page, offset, cat_link, category, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', class_="style_06")
        for post in contentDiv.findAll('h2'):
            link = [post.find('a',href=True)['href']]
            detail = self.getDetailBerita(link)
            if detail:
                if self.insertDB(detail):
                    details.append(detail)

        el_page = soup.find('div', class_="grid")
        if el_page:
            a_page = el_page.findAll('div', class_='bu fr')[-1].find('a')
            max_page = int(a_page['data-ci-pagination-page'].replace('\n', '').strip(' '))

            if page < max_page:
                time.sleep(5)
                # cat_links = ['international', 'bola', 'olahraga', 'teknologi', 'hiburan','rona']
                # for cat in range(len(cat_links)):
                #     cat_link = cat_links[cat]
                details = self.getAllBerita(details, page+1, offset+30, cat_link, category, date)
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

        #extract subcategory from breadcrumb
        bc = soup.find('div', class_="breadcrumbs")
        if not bc:
            return False
        cat = bc.findAll('a')[-2].get_text(strip=True)
        sub = bc.findAll('a')[-1].get_text(strip=True)

        #articles
        article_id = soup.find('meta', attrs={"property":"og:image"})['content']
        articles['id'] = int(article_id.replace('//','').split('/')[6]) if article_id !="" else ''

        #category
        #category
        articles['category'] = cat
        articles['subcategory'] = sub

        articles['url'] = url

        article = soup.find('div', class_="tru")

        #extract date
        pubdate_author = soup.find('div', class_='reg').text
        pubdate_author_split = pubdate_author.split(' \xa0\xa0 • \xa0\xa0 ')
        pubdate = pubdate_author_split[1]
        pubdate = pubdate.strip(' \t\n\r')
        pubdate = pubdate.replace(' WIB','')
        pubdate = pubdate.replace('Aug', 'Agt').replace('Juli', 'Jul').replace('Juni', 'Jun')
        pubdate = datetime.strftime(datetime.strptime(pubdate, "%A, %d %b %Y %H:%M"), "%Y-%m-%d %H:%M:%S")
        articles['pubdate'] = pubdate

        #extract author
        author = pubdate_author_split[0]
        articles['author'] = author

        #extract title
        title = soup.find('meta', attrs={"property":"og:title"})
        articles['title'] = title['content'] if title else ''

        if ("foto" in sub.lower()) or  "video" in sub.lower():
            return False

        #source
        articles['source'] = 'metrotvnews'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = soup.find('div', class_="line").findAll('a', class_="tag")
        articles['tags'] = ','.join([x.get_text(strip=True) for x in tags])

        #extract images
        articles['images'] = soup.find('img', class_="pic")['src']

        #extract detail
        detail = soup.find('div', class_="tru")

        #hapus link sisip
        for link in detail.findAll('div', class_="related"):
            link.decompose()

        #hapus video sisip
        for tag in detail.findAll('iframe', class_="embedv"):
            tag.decompose()

        #hapus all setelah clear fix
        #for det in detail.find('div', class_="wfull fl rl"):
        #    det.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.get_text(strip=True)))
        articles['content'] = content.strip(' ')
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
