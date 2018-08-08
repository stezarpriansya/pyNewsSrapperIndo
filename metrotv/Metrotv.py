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

class Metrotv:
    def getAllBerita(self, details, page, offset, cat_link, category, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY-mm-dd
        """
        print("page ", page)
        url = "http://"+cat_link+".metrotvnews.com/index/"+date+"/"+ str(offset)
        print(url)
        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            details = self.getAllBerita(details, page+1, offset+30, cat_link, category, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")
        contentDiv = soup.find('div', class_="style_06").findAll('h2')
        contentDiv
        for post in contentDiv:
            link = [post.find('a',href=True)['href']]
            detail = self.getDetailBerita(link)
        details.append(detail)

        el_page = soup.find('div', class_="grid")
        if el_page:
            a_page = el_page.findAll('div', class_='bu fr')[-1].find('a')
            max_page = int(a_page['data-ci-pagination-page'].replace('\n', '').strip(' '))

            if page < max_page:
                time.sleep(10)
                details = self.getAllBerita(details, page+1, offset+30, cat_link, category, date)

        return links

    def getDetailBerita(self, url):
        time.sleep(10)
        articles = {}
        #link
        url = link[0]
        #print(url)
        response = requests.get(url)
        html = response.text

        #Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        #extract subcategory from breadcrumb
        bc = soup.find('div', class_="breadcrumbs")
        if not bc:
            continue
        cat = bc.findAll('a')[-2].text
        sub = bc.findAll('a')[-1].text

        #articles
        article_id = int(soup.find('meta', attrs={"property":"og:image"})['content'].replace('//','').split('/')[6])
        articles['id'] = article_id

        #category
        #category
        articles['category'] = cat
        articles['subcategory'] = sub

        articles['url'] = url

        article = soup.find('div', class_="tru")

        #extract date
        pubdate_author = soup.find("div",class_="reg").text
        pubdate_author_split = pubdate_author.split(' \xa0\xa0 • \xa0\xa0 ')
        pubdate = pubdate_author_split[1]
        pubdate = pubdate.strip(' ')
        pubdate = pubdate.replace(' WIB','')
        pubdate = datetime.strftime(datetime.strptime(pubdate, "%A, %d %b %Y %H:%M"), "%Y-%m-%d %H:%M:%S")
        articles['pubdate'] = pubdate

        #extract author
        author = pubdate_author_split[0]
        articles['author'] = author

        #extract title
        articles['title'] = soup.find('meta', attrs={"property":"og:title"})['content']
        if ("foto" in sub.lower()) or  "video" in sub.lower():
            continue

        #source
        articles['source'] = 'metrotvnews'

        #extract comments count
        articles['comment'] = 0

        #extract tags
        tags = soup.find('div', class_="line").findAll('a', class_="tag")
        articles['tags'] = ','.join([x.text for x in tags])

        #extract images
        articles['images'] = soup.find('img', class_="pic")['src']

        #extract detail
        detail = soup.find('div', class_="tru")

        #hapus link sisip
        for link in detail.findAll('div', class_="related"):
            link.decompose()

        #hapus video sisip
        for tag in detail.findAll('iframe', class_="embedv"):
            tag.decompose()

        #hapus all setelah clear fix
        #for det in detail.find('div', class_="wfull fl rl"):
        #    det.decompose()

        #hapus all script
        for script in detail.findAll('script'):
            script.decompose()

        #extract content
        detail = BeautifulSoup(detail.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',detail.text)
        articles['content'] = content.strip(' ')
        #print('memasukkan berita id ', articles['id'])

        return all_articles
