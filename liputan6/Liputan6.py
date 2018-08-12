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

class Liputan6:
    def getAllBerita(self, details, page, cat_link, category, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "https://www.liputan6.com/"+cat_link+"/indeks/"+date+"?page="+str(page)
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

        contentDiv = soup.find('div', class_="articles--list articles--list_rows")
        flag = True
        for post in contentDiv.findAll('figure'):
            link = [post.find('a', href=True)['href'], category]
            detail = self.getDetailBerita(link)
            if self.insertDB(con, detail):
                details.append(detail)

        if flag:
            el_page = soup.find('div', class_="simple-pagination__container")
            if el_page:
                a_page = el_page.find('ul').findAll('li', class_="simple-pagination__page-number")[-1].find('span')
                if el_page.find('ul').findAll('li', class_="simple-pagination__page-number")[-1].find('span', class_="simple-pagination__page-number-link simple-pagination__page-number-link_active"):
                    max_page = page
                else:
                    max_page = el_page.find('ul').findAll('li', class_="simple-pagination__page-number")[-1]
                    max_page = int(max_page['data-page'].replace('\n', '').strip(' '))

                if page < max_page:
                    time.sleep(5)
                    details = self.getAllBerita(details, page+1, cat_link, category, date)
        con.close()
        return details

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
        article_id = soup.find('article', class_='hentry main read-page--core-article')
        articles['id'] = int(article_id['data-article-id']) if article_id else ''

        #extract title
        title = soup.find('meta', attrs={"property":"og:title"})['content']
        articles['title'] = title
        if ("foto:" in title.lower()) or  "video:" in title.lower():
            return False

        bc = soup.find('ul', class_="read-page--breadcrumb")
        if not bc:
            return False
        cat = bc.findAll('a')[-2].get_text(strip=True)
        sub = bc.findAll('a')[-1].get_text(strip=True)

        #category
        articles['category'] = cat
        articles['subcategory'] = sub

        #article_url
        articles['url'] = url

        #article
        article = soup.find("div", class_="article-content-body__item-content")

        #extract date
        pubdate = soup.find('p', class_="read-page--header--author__datetime-wrapper").find('time')['datetime']
        pubdate = pubdate.strip(' \t\n\r')
        # pubdate = pubdate.replace(' WIB','').replace('Ags', 'Agt')
        articles['pubdate']= datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
        articles['pubdate'] = pubdate

        #extract author
        author = soup.find('a', class_="read-page--header--author__link url fn").find('span', class_="read-page--header--author__name fn").get_text(strip=True)
        articles['author'] = author

        #source
        articles['source'] = 'Liputan6'

        #extract comments count
        comments = soup.find('li', class_="read-page--social-share__list-item js-social-share-comment").find('a')
        comments = int(comments.find('span', class_="read-page--social-share__comment-total").get_text(strip=True))
        articles['comments'] = comments

        #extract tags
        tags = soup.findAll('span', class_="tags--snippet__name")
        articles['tags'] = ','.join([x.get_text(strip=True) for x in tags]) if tags else ''

        #extract images
        image = soup.find('picture', class_="read-page--photo-gallery--item__picture")
        articles['images'] = image.find('img')['src'] if image else ''


        #hapus link sisip
        for link in article.findAll('div', class_="baca-juga"):
            link.decompose()

        #hapus video sisip
        #         for tag in detail.findAll('div', class_="detail_tag"):
        #             tag.decompose()

        #hapus all setelah clear fix
        #for det in detail.find('div', class_="wfull fl rl"):
        #     det.decompose()

        #hapus all script
        #for script in article.findAll('script'):
        #script.decompose()

        #extract content
        detail = BeautifulSoup(article.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',unicodedata.normalize("NFKD",detail.get_text(strip=True)))
        articles['content'] = content
        #print('memasukkan berita id ', articles['id'])

        return articles

    def insertDB(self, con, articles):
        """
        Untuk memasukkan berita ke DB
        """
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
            return True
        else:
            cursor.close()
            print('salah2')
            return False
