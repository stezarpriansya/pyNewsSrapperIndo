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

class Tempo:
    def getIndeksLink(self, links, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY-mm-dd
        """
    #     print("page ", page)
        url = "https://www.tempo.co/indeks/"+date
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            links = self.getIndeksLink(links, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('section', {'id':'article'}).find('section', class_="list list-type-1")
        indeks = contentDiv.findAll('li')
        if indeks:
            for post in indeks:
                link = [post.find('a', {'class':'col'}, href=True)['href'], ""]
                links.append(link)
    #         links = getIndeksLink(links, date)
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
            print(url)
            response = requests.get(url)
            html = response.text
            # Create a BeautifulSoup object from the HTML: soup
            soup = BeautifulSoup(html, "html5lib")

            #extract scrip json ld
            scripts_all = soup.findAll('script', attrs={'type':'application/ld+json'})
    #         print(len(scripts_all))
            scripts = json.loads(scripts_all[0].text)
            scripts2 = json.loads(scripts_all[1].text)

            #category
            articles['category'] = scripts2['itemListElement'][-2]['item']['name']
            articles['subcategory'] = scripts2['itemListElement'][-1]['item']['name']

            articles['url'] = url

            article = soup.find('article', {'itemtype':"http://schema.org/NewsArticle"})

            #extract date
            pubdate = scripts['datePublished']
            pubdate = pubdate[0:19].strip(' \t\n\r')
            articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')
            articles['id'] = int(soup.find('meta', {'property':"dable:item_id"})['content'])

            #extract author
            articles['author'] = scripts['editor']['name']

            #extract title
            articles['title'] = scripts['headline']

            #source
            articles['source'] = 'tempo'

            #extract comments count
    #         articles['comments'] = int(soup.find('span', class_="commentWidget-total").find('b').text.strip(' \t\n\r'))
            articles['comments'] = 0

            #extract tags
            tags = article.find('div', class_="tags clearfix").findAll('a')
            articles['tags'] = ','.join([x.text for x in tags])

            #extract images
            articles['images'] = scripts['image']['url']

            #extract detail
            detail = article.find('div', attrs={'id':'isi'})

            #hapus div
            if detail.findAll('div'):
                for div in detail.findAll('div'):
                    div.decompose()

            #hapus link sisip
            if detail.findAll('p'):
                for p in detail.findAll('p'):
                    if ("baca:" in p.text.lower()):
                        p.decompose()

            #extract content
            detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
            content = re.sub(r'\n|\t|\b|\r','',detail.text)
            articles['content'] = content
            print('memasukkan berita id ', articles['id'])
            all_articles.append(articles)
        return all_articles
