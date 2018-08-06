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

class Okezone:
    def getIndeksLink(self, links, page, offset=0, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url okezone
        link pada indeks category tertentu
        date format : dd/mm/YYYY
        """
        print("page ", page)
        url = "https://index.okezone.com/bydate/index/"+date+"/"+str(offset)+"/"
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            links = self.getIndeksLink(links, page+1, page*15, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', class_="news-content")
        indeks = contentDiv.findAll('li')
        for post in indeks:
            link = [post.find('a', href=True)['href'], ""]
            links.append(link)

        el_page = soup.find('div', class_="pagination-indexs")
        if el_page:
            max_page = (int(el_page.findAll('a')[-1]['href'][50:-1])/15)+1

            if page < max_page:
                time.sleep(10)
                links = self.getIndeksLink(links, page+1, page*15, date)

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

            #extract scrip json ld
            scripts = soup.findAll('script', attrs={'type':'application/ld+json'})[-1].text
            scripts = json.loads(scripts)

            #extract subcategory from breadcrumb
            bc = soup.find('div', class_="breadcrumb")
            if not bc:
                continue
            cat = bc.findAll('a')[-2].text
            sub = bc.findAll('a')[-1].text
            if ("foto" in sub.lower()) or  ("video" in sub.lower()):
                continue

            #category
            articles['category'] = cat
            articles['subcategory'] = sub

            articles['id'] = int(scripts['mainEntityOfPage']['@id'])

            articles['url'] = url

            article = soup.find('div', class_="container-bodyhome-left")

            #extract date
            pubdate = scripts['datePublished']
            pubdate = pubdate.strip(' \t\n\r')
            articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y-%m-%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')

            #extract author
            articles['author'] = scripts['author']['name']

            #extract title
            articles['title'] = scripts['headline']

            #source
            articles['source'] = 'okezone'

            #extract comments count
            articles['comments'] = int(soup.find('span', class_="commentWidget-total").find('b').text.strip(' \t\n\r'))

            #extract tags
            tags = article.find('div', class_="detail-tag").findAll('a')
            articles['tags'] = ','.join([x.text for x in tags])

            #extract images
            articles['images'] = soup.find("meta", attrs={'property':'og:image'})['content']

            #extract detail
            detail = article.find('div', attrs={'id':'contentx', 'class':'read'})

            #hapus link sisip
            for link in detail.findAll('table', class_="linksisip"):
                link.decompose()

            #hapus video sisip
            for div in detail.findAll('div'):
                div.decompose()

            #hapus all setelah clear fix
            for det in detail.find('div', class_="clearfix mb20").findAllNext():
                det.decompose()

            #hapus all script
            for script in detail.findAll('script'):
                script.decompose()

            #hapus all noscript
            for ns in detail.findAll('noscript'):
                ns.decompose()

            #hapus linksisip
            for ls in detail.findAll('a'):
                if ls.find('strong'):
                    if 'baca' in ls.find('strong').text.lower():
                        ls.decompose()

            #extract content
            detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
            content = re.sub(r'\n|\t|\b|\r','',detail.text)
            articles['content'] = content
            print('memasukkan berita id ', articles['id'])
            all_articles.append(articles)
        return all_articles
