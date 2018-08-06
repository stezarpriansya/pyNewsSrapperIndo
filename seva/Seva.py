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
import time
from requests.exceptions import ConnectionError

class Seva:
    def getIndeksLink(self, links, page, cat_link, category):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : dd/mm/YYYY
        """
        print("page ", page)
        url = "https://www.seva.id/otomotif/blog/category/"+cat_link+"/page/"+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            links = self.getIndeksLink(links, page+1, cat_link, category)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', class_="col-md-6")
        indeks = contentDiv.findAll('div', class_='article-box')
        for post in indeks:
            link = [post.find('a', href=True)['href'], category]
            links.append(link)

        el_page = soup.find('nav', attrs={'aria-label':'Page navigation example'})
        if el_page:
            max_page = int(soup.find('ul', class_="pagination").findAll('li')[-2].find('a').text.replace('\n', '').strip(' '))

            if page < max_page:
                time.sleep(10)
                links = self.getIndeksLink(links, page+1, cat_link, category)

        return links

    def getDetailBerita(self, links):
        """
        Mengambil seluruh element dari halaman berita
        """
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

            #extract subcategory from meta
            sub = html.unescape(soup.find('meta', attrs={'property': 'article:section'})['content'])

            articles['subcategory'] = sub

            articles['id'] = int(soup.find("link", attrs={'rel':'shortlink'})['href'].replace("https://www.seva.id/otomotif/?p=", "").strip(' \t\n\r'))
            #category
            articles['category'] = link[1]
            articles['url'] = url

            article = soup.find('div', class_="news-content border-list")

            #extract date
            #2018-07-27T15:18:00+00:00
            pubdate = soup.find("meta", attrs={'property':'article:published_time'})['content']
            pubdate = pubdate[0:19].strip(' \t\n\r')
            articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')

            #extract author
            articles['author'] = soup.find("div", class_="col-md-8").find('div', class_='col-md-10').find('div', class_="details").text

            #extract title
            articles['title'] = article.find('div', class_="title").find('h1').text

            #source
            articles['source'] = 'seva'

            #extract comments count
            articles['comments'] = 0

            #extract tags
            tags = soup.findAll('meta', attrs={'property':'article:tag'})
            articles['tags'] = ','.join([x['content'] for x in tags])

            #extract images
            articles['images'] = soup.find('meta', attrs={'property':'og:image'})['content']

            #extract detail
            detail = article.find('div', class_="content")


            #extract content
            detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
            content = re.sub(r'\n|\t|\b|\r','',detail.text)
            articles['content'] = html.unescape(content)
            print('memasukkan berita id ', articles['id'])
            all_articles.append(articles)
        return all_articles
