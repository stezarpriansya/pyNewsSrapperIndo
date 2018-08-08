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
import mysql.connector

class Otomart:
    def getAllBerita(self, details, page, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        category : berita-mobil, artikel-mobil, uncategorized
        """
        con = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='news_db')
        print("page ", page)
        url = "https://www.otomart.id/berita/page/"+str(page)
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
        div = soup.find('div', class_="wrap contentclass")
        indeks = div.findAll('article')
        flag = True
        for post in indeks:
            link = [post.find('a', href=True)['href'], '']
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
                if detail:
                    details.append(detail)
        if flag:
            el_page = el_page = soup.find('div', class_="wp-pagenavi")
            if el_page:
                last_page = int(el_page.findAll('a', href=True)[-1]['href'].split('page/')[-1].replace('\n', '').strip(' '))
                active_page = int(el_page.find('span', class_="current").text.replace('\n', '').strip(' '))

                if last_page > active_page:
                    time.sleep(10)
                    details = self.getAllBerita(details, int(active_page)+1,date)

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

        #extract subcategory from breadcrumb
        bc = soup.find('a', attrs={"rel":"category tag"}).text

        if ("foto" in bc.lower()) or  "video" in bc.lower():
            return False

        #category
        articles['category'] = 'Otomotif'
        articles['subcategory'] = bc

        #article_url
        articles['url'] = url

        #article
        article = soup.find('div', class_="entry-content")

        #extract date
        pubdate = soup.find('meta', attrs={"property":"article:published_time"})['content']
        pubdate = pubdate[0:19].strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        #articleid
        articles['id'] = int(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S").timestamp()) + len(url)

        #extract editor
        author = soup.find('span', class_="vcard author").find('span', class_="fn").text
        articles['author'] = author

        #extract title
        title = soup.find('h1', class_="entry-title").text
        articles['title'] = title

        #source
        articles['source'] = 'otomart.com'

        #extract comments count
        articles['comments'] = int(soup.find('span', class_="postcommentscount").text.strip(' \t\n\r'))

        #extract tags
        tags = soup.findAll('meta', attrs={"property":"article:tag"})
        articles['tags'] = ','.join([x['content'] for x in tags])

        #extract images
        image = soup.find('meta', attrs={"property":"og:image:secure_url"})
        if image:
            articles['image'] = image['content']
        else:
            articles['image'] = ''

        #hapus link sisip
        for link in article.findAll('figure'):
            link.decompose()

        for link in article.findAll('h4'):
            link.decompose()

        #extract content
        detail = BeautifulSoup(article.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',detail.text)
        articles['content'] = content
        #print('memasukkan berita id ', articles['id'])

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
