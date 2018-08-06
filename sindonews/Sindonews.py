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

class Sindonews:
    def getIndeksLink(self, links, page, cat_link, offset=0, date=datetime.strftime(datetime.today(), '%Y-%m-%d')):
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
            links = self.getIndeksLink(links, page+1, cat_link, offset+10, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        contentDiv = soup.find('div', class_="indeks-news")
        if contentDiv:
            for post in contentDiv.findAll('div', class_="indeks-title"):
                link = [post.find('a', href=True)['href'], ""]
                links.append(link)

        el_page = soup.find('div', class_="pagination")
        if el_page:
            max_page = int(soup.find('div', class_="pagination").findAll('a')[-2]['data-ci-pagination-page'])

            if page < max_page:
                time.sleep(10)
                links = self.getIndeksLink(links, page+1, cat_link, offset+10, date)

        return links

    def getDetailBerita(self, links):
        all_articles = []
        for link in links:
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
                continue
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
                continue
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
            content = re.sub(r'\n|\t|\b|\r','',detail.text)

            #articles['content'] = re.sub('google*','', content).strip(' ')
            articles['content'] = content
            #print('memasukkan berita id ', articles['id'])
            all_articles.append(articles)
        return all_articles
