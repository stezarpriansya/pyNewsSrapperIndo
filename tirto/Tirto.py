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
import unicodedata

class Tirto:
    def getAllBerita(self, details, page, date=datetime.strftime(datetime.today(), '%Y-%m-%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        """
        print("page ", page)
        url = "https://tirto.id/indeks/"+str(page)+"?date="+date
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

        main_el = soup.find('div', attrs={'id':'__nuxt'})
        script = main_el.findNextSiblings()
        tes = script[0].text.replace('window.__NUXT__=', '')[:-1]
        json_mobil = json.loads(tes)

        link_articles = json_mobil['data'][0]['listarticle']
        if link_articles:
            for art in link_articles:
                link = ['https://tirto.id'+art['articleUrl'], '']
                detail = self.getDetailBerita(link)
                if self.insertDB(con, detail):
                    print("Insert berita ", detail['title'])
                    details.append(detail)

        el_page = soup.find('ul', class_="custom-pagination p-0 text-center mb-5 col-10 offset-1")
        if el_page:
            max_page = int(el_page.findAll('a')[-2].text)

            if page < max_page:
                time.sleep(10)
                details = self.getAllBerita(details, page+1, date)

        return details

    def getDetailBerita(self, link):
        time.sleep(10)
        articles = {}
        #link
        url = link[0]
        response = requests.get(url)
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        #extract subcategory from breadcrumb
        bc = soup.find('ol', class_="breadcrumbs")
        if not bc:
            return False
        cat = bc.findAll('a')[-1].text
        #sub = bc.findAll('a')[-1].text

        #category
        articles['category'] = cat
        articles['subcategory'] = ""

        #article_url
        articles['url'] = url

        #article
        intro = soup.find('article', class_="col-12 content-detail-holder my-4").findAll('div', class_="content-text-editor")[0]
        article = soup.find('article', class_="col-12 content-detail-holder my-4").findAll('div', class_="content-text-editor")[1]
        author = soup.find('article', class_="col-12 content-detail-holder my-4").findAll('div', class_="content-text-editor")[2]

        #extract date
        author_pubdate = soup.find('div', class_="col-md-6").text.replace('Oleh: ','')
        author_pubdate = author_pubdate.split(' - ')
        pubdate = author_pubdate[1]
        pubdate = pubdate.strip(' ')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%d %B %Y"), "%Y-%m-%d %H:%M:%S")

        articles['id'] = int(datetime.strptime(pubdate, "%d %B %Y").timestamp()) + len(url)
        #extract author
        credit = soup.find('div', class_="credit").findAll('span', class_="reporter-grup")
        reporter_sumber = credit[0].text.replace('Reporter: ','')
        author = credit[1].text.replace('Penulis: ','')
        editor = credit[2].text.replace('Editor: ','')
        articles['author'] = author

        #extract title
        title = soup.find('h1', class_="news-detail-title text-center animated zoomInUp my-3").text
        if ("foto" in title.lower()) or  "video" in title.lower():
            return False
        articles['title'] = title

        #source
        articles['source'] = 'tirto.id'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = soup.find('meta', attrs={"name":"keywords"})['content']
        articles['tags'] = tags

        #extract images
        image = soup.findAll('meta', attrs={"name":"thumbnail"})[0]['content']
        articles['image'] = image

        #hapus link sisip
        for link in article.findAll('div'):
            link.decompose()

        #extract content
        detail = BeautifulSoup(article.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.text))

        #articles['content'] = re.sub('google*','', content).strip(' ')
        articles['content'] = content
        #print('memasukkan berita id ', articles['id'])

        return articles

    def insertDB(self, con, articles):
        """
        Untuk memasukkan berita ke DB
        """
        print(articles)
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
            return True
        else:
            cursor.close()
            print('salah2')
            return False
