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

class Sindonews:
    def getAllBerita(self, details, page, cat_link, offset=0, date=datetime.strftime(datetime.today(), '%Y-%m-%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        """
        print("page ", page)
        url = "https://index.sindonews.com/index/"+ str(cat_link)+ "/" + str(offset)+ "?t="+ date
        print(url)

        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page+1, cat_link, offset+10, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        contentDiv = soup.find('div', class_="indeks-news")
        if contentDiv:
            for post in contentDiv.findAll('div', class_="indeks-title"):
                link = [post.find('a', href=True)['href'], ""]
                detail = self.getDetailBerita(link)
                details.append(detail)

        el_page = soup.find('div', class_="pagination")
        if el_page:
            max_page = int(soup.find('div', class_="pagination").findAll('a')[-2]['data-ci-pagination-page'])

            if page < max_page:
                time.sleep(10)
                details = self.getAllBerita(details, page+1, cat_link, offset+10, date)

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
        bc = soup.find('ul', class_="breadcrumb")
        if not bc:
            return False
        cat = bc.findAll('a')[-2].text
        sub = bc.findAll('a')[-1].text

        #articleid
        url_split = url.replace('//','').split('/')
        article_id = url_split[2]
        articles['id'] = article_id

        #category
        articles['category'] = cat
        articles['subcategory'] = sub

        #article_url
        articles['url'] = url

        #article
        article = soup.find("div", id="content")

        #extract date
        pubdate = soup.find('time').text
        pubdate = pubdate.strip(' \t\n\r')
        pubdate = pubdate.replace(' WIB','')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%A, %d %B %Y - %H:%M"), "%Y-%m-%d %H:%M:%S")

        #extract author
        reporter = soup.find('div', class_="reporter")
        author = reporter.find('p', class_="author").find('a').text.strip(' ')
        articles['author'] = author

        #extract title
        title = soup.find('div', class_="article").find('h1').text
        if ("foto" in title.lower()) or  "video" in title.lower():
            return False
        articles['title'] = title

        #source
        articles['source'] = 'Sindonews'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        #tags = soup.findAll('span', class_="tags--snippet__name")
        #tags = ','.join([x.text for x in tags])
        #articles['tags'] = tags

        #extract images
        image = soup.find('div', class_="article").find('img')['src']
        articles['image'] = image

        #hapus link sisip image
        for link in article.findAll('img'):
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
