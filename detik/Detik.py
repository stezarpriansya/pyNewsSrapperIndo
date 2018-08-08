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

class Detik:
    def getAllBerita(self, details, page, cat_link, category, date=datetime.strftime(datetime.today(), '%m/%d/%Y')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : dd/mm/YYYY
        """
        print("page ", page)
        if cat_link == 'news':
            url = "https://"+cat_link+".detik.com/indeks/all/"+str(page)+"?date="+date
        else :
            url = "https://"+cat_link+".detik.com/indeks/"+str(page)+"?date="+date
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page+1, cat_link, category, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('ul', attrs={'id':'indeks-container'})
        indeks = contentDiv.findAll('article')
        for post in indeks:
            link = [post.find('a', href=True)['href'], category]
            detail = self.getDetailBerita(link)
            details.append(detail)

        el_page = soup.find('div', class_="paging paging2")
        if el_page:
            max_page = int(soup.find('div', class_="paging paging2").findAll('a')[-2].text.replace('\n', '').strip(' '))

            if page < max_page:
                time.sleep(10)
                details = self.getAllBerita(details, page+1, cat_link, category, date)

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
        bc = soup.find('div', class_="breadcrumb")
        if not bc:
            continue

        sub = bc.findAll('a')[1].text
        if ("foto" in sub.lower()) or  "video" in sub.lower():
            continue

        articles['subcategory'] = sub

        articles['id'] = int(soup.find("meta", attrs={'name':'articleid'})['content'])
        #category
        articles['category'] = link[1]
        articles['url'] = url

        article = soup.find('article')

        #extract date
        pubdate = soup.find("meta", attrs={'name':'publishdate'})['content']
        pubdate = pubdate.strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%Y/%m/%d %H:%M:%S"), '%Y-%m-%d %H:%M:%S')

        #extract author
        articles['author'] = soup.find("meta", attrs={'name':'author'})['content']

        #extract title
        articles['title'] = article.find('div', class_="jdl").find('h1').text

        #source
        articles['source'] = 'detik'

        #extract comments count
        articles['comments'] = int(soup.find('a', class_="komentar").find('span').text.replace('Komentar', '').strip(' \t\n\r'))

        #extract tags
        tags = article.find('div', class_="detail_tag").findAll('a')
        articles['tags'] = ','.join([x.text for x in tags])

        #extract images
        articles['images'] = article.find('div', class_="pic_artikel").find('img')['src']

        #extract detail
        detail = article.find('div', class_="detail_text")

        #hapus link sisip
        for link in detail.findAll('table', class_="linksisip"):
            link.decompose()

        #hapus video sisip
        for tag in detail.findAll('div', class_="sisip_embed_sosmed"):
            tag.decompose()

        #hapus all setelah clear fix
        for det in detail.find('div', class_="clearfix mb20").findAllNext():
            det.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',detail.text)
        articles['content'] = re.sub(r'(Tonton juga).*','', content)
        print('memasukkan berita id ', articles['id'])

        return articles
