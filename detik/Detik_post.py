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

class Detik_post:
    def getAllBerita(self, details, cat_link, category, date=datetime.strftime(datetime.today(), '%m/%d/%Y')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : dd/mm/YYYY
        """

        # print("page ", page)
        # s = requests.Session()
        url = "https://"+cat_link+".detik.com/indeks/"
        formdata = {}
        formdata['datepick'] = date
        # Make the request and create the response object: response
        try:
            response = requests.post(url, data=formdata)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, cat_link, category, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', attrs={'class':'lf_content'})
        if not contentDiv:
            contentDiv = soup.find('div', attrs={'class':'content right'})
            if not contentDiv:
                contentDiv = soup.find('div', attrs={'class':'rm_content'})
        indeks = contentDiv.findAll('article')
        for post in indeks:
            cek_foto = post.find('span', {'class':'sub_judul'})
            if cek_foto:
                print(cek_foto.get_text(strip=True).lower())
                if ("foto" in cek_foto.get_text(strip=True).lower()) or ("video" in cek_foto.get_text(strip=True).lower()) or ("fotoinet" in cek_foto.get_text(strip=True).lower()) or ("videoinet" in cek_foto.get_text(strip=True).lower()):
                    continue
            link = [post.find('a', href=True)['href'], category]
            detail = self.getDetailBerita(0, link)
            if detail:
                if self.insertDB(detail):
                    details.append(detail)

        el_page = soup.find('div', class_="paging paging2")
        if el_page:
            max_page = int(soup.find('div', class_="paging paging2").findAll('a')[-2].get_text(strip=True).replace('\n', '').strip(' '))

            if page < max_page:
                time.sleep(10)
                details = self.getAllBerita(details, cat_link, category, date)

        return 'berhasil ambil semua berita'

    def getDetailBerita(self, count, link):
        """
        Mengambil seluruh element dari halaman berita
        """
        time.sleep(10)
        articles = {}
        #link
        url = link[0]

        print(url)
        try:
            response = requests.get(url)
        except:
            return False
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        # print(soup)
        #extract subcategory from breadcrumb
        bc = soup.find('div', class_="breadcrumb")
        if not bc:
            return False

        sub = bc.findAll('a')[1].get_text(strip=True)
        if ("foto" in sub.lower()) or ("detiktv" in sub.lower()) or ("video" in sub.lower()) or ("photos" in sub.lower()) or ("videos" in sub.lower()):
            return False

        articles['subcategory'] = sub
        #category
        articles['category'] = link[1]
        articles['url'] = url

        article = soup.find('article')

        #extract date
        pubdate = soup.find("meta", attrs={'name':'publishdate'})
        if pubdate:
            pubdate = pubdate['content'].strip(' \t\n\r')
            articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y/%m/%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')
            id = soup.find("meta", attrs={'name':'articleid'})
            articles['id'] = int(id['content']) if id else int(datetime.strptime(pubdate, "%Y/%m/%d %H:%M:%S").timestamp()) + len(url)
        else:
            pubdate = soup.find('span', {'class':'date'})
            pubdate = pubdate.get_text(strip=True).strip(' \t\n\r').replace(" WIB", '')
            articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%A, %d %b %Y %H:%M"), '%Y-%m-%d %H:%M:%S')

            id = soup.find("meta", attrs={'name':'articleid'})
            articles['id'] = int(id['content']) if id else int(datetime.strptime(pubdate, "%A, %d %b %Y %H:%M").timestamp()) + len(url)

        #extract author
        author = soup.find("meta", attrs={'name':'author'})
        articles['author'] = author['content'] if author else ''

        #extract title
        title =  article.find('meta', {"property":"og:title"})
        articles['title'] = title.get_text(strip=True) if title else ''

        #source
        articles['source'] = 'detik'

        #extract comments count
        komentar = soup.find('a', class_="komentar")
        articles['comments'] = int(komentar.find('span').get_text(strip=True).replace('Komentar', '').strip(' \t\n\r')) if komentar else 0

        #extract tags
        tags = article.find('div', class_="detail_tag")
        articles['tags'] = ','.join([x.get_text(strip=True) for x in tags.findAll('a')]) if tags else ''

        #extract images
        images = article.find('div', class_="pic_artikel")
        articles['images'] = images.find('img')['src'] if images else ''

        #extract detail
        if articles['category'] == 'news':
            detail = article.find('div', class_="detail_text")
        else:
            detail = article.find('div', attrs={"id": "detikdetailtext"})
            if not detail:
                detail = soup.find('div', attrs={"class": "read__content full mt20"})
                if not detail:
                    detail = soup.find('div', attrs={"id": "detikdetailtext"})
        if not detail:
            return False
        #hapus link sisip
        if detail.findAll('table', class_="linksisip"):
            for link in detail.findAll('table', class_="linksisip"):
                link.decompose()

        #hapus video sisip
        if detail.findAll('div', class_="sisip_embed_sosmed"):
            for tag in detail.findAll('div', class_="sisip_embed_sosmed"):
                tag.decompose()

        #hapus all setelah clear fix
        if detail.find('div', class_="clearfix mb20"):
            for det in detail.find('div', class_="clearfix mb20").findAllNext():
                det.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        for p in detail.findAll('p'):
           if ("baca juga" in p.get_text(strip=True).lower()) and (p.find('a')):
               p.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.get_text(strip=True)))
        articles['content'] = re.sub(r'(Tonton juga).*','', content)
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
