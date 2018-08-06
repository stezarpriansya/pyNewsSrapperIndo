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

class Rajamobil:
    def getIndeksLink(self, links, page, cat, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url okezone
        link pada indeks category tertentu
        category = berita
        """
        print("page ", page)
        url = "https://"+cat+".rajamobil.com/page/"+str(page)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            links = self.getIndeksLink(links, page+1, cat, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        indeks = soup.findAll('div', class_="td-block-span4")
        for post in indeks:
            link = [post.find('a', href=True)['href'], cat]
            links.append(link)

        el_page = soup.find('div', class_="page-nav td-pb-padding-side")
        if el_page:
            max_page = int(el_page.find('a', class_="last").text.strip(' '))

            if page < max_page:
                time.sleep(10)
                links = self.getIndeksLink(links, page+1, cat, date)

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

            #category
            articles['category'] = 'Otomotif'
            articles['subcategory'] = link[1]

            articles['url'] = url

            article = soup.find('div', class_="td-pb-span8 td-main-content")

            #extract date
            pubdate = article.find('meta', {'property':'article:published_time'})['content']
            pubdate = pubdate[0:19].strip(' \t\n\r')
            articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%dT%H:%M:%S"), '%Y-%m-%d %H:%M:%S')
            articles['id'] = soup.find('input', {'id':'comment_post_ID'}).get('value')

            #extract author
            articles['author'] = article.find('span', {'class': 'blue-clr text-right full-width display-ib'}).text

            #extract title
            articles['title'] = soup.find('div', {'class': 'td-author-by'}).find('a').text.strip(' \t\n\r')

            #source
            articles['source'] = 'rajamobil'

            #extract comments count
            articles['comments'] = 0

            #extract tags
            tags = article.findAll('meta', {"property":"article:tag"})
            articles['tags'] = ','.join([x['content'] for x in tags])

            #extract images
            articles['images'] = soup.find("meta", attrs={'property':'og:image'})['content']

            #extract detail
            detail = article.find('div', attrs={"class":"td-post-content"})

            #hapus video sisip
            for div in detail.findAll('div'):
                div.decompose()

            #hapus all script
            for script in detail.findAll('script'):
                script.decompose()

            #hapus all noscript
            for ns in detail.findAll('noscript'):
                ns.decompose()

            #hapus all figure
            for fig in detail.findAll('figure'):
                fig.decompose()

            #hapus linksisip
            for ls in detail.findAll('ul'):
                if ls.find('em'):
                    if 'baca' in ls.find('em').text.lower():
                        ls.decompose()

            #extract content
            detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
            content = re.sub(r'\n|\t|\b|\r','',detail.text)
            articles['content'] = content
            print('memasukkan berita id ', articles['id'])
            all_articles.append(articles)
        return all_articles