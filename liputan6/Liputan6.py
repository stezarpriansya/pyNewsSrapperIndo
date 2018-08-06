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

class Liputan6:
    def getIndeksLink(self, links, page, cat_link, category, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
        """
        Untuk mengambil seluruh url
        link pada indeks category tertentu
        date format : YYYY/mm/dd
        """
        print("page ", page)
        url = "https://www.liputan6.com/"+cat_link+"/indeks/"+date+"?page="+str(page)
        print(url)

        # Make the request and create the response object: response
        try:
            response = requests.get(url)
        except ConnectionError:
            print("Connection Error, but it's still trying...")
            time.sleep(10)
            links = self.getIndeksLink(links, page+1, cat_link, category, date)
        # Extract HTML texts contained in Response object: html
        html = response.text
        # Create a BeautifulSoup object from the HTML: soup
        soup = BeautifulSoup(html, "html5lib")

        contentDiv = soup.find('div', class_="articles--list articles--list_rows")
        if contentDiv:
            for post in contentDiv.findAll('figure'):
                link = [post.find('a', href=True)['href'], category]
                links.append(link)

        el_page = soup.find('div', class_="simple-pagination__container")
        if el_page:
            a_page = el_page.find('ul').findAll('li', class_="simple-pagination__page-number")[-1].find('span')
            if el_page.find('ul').findAll('li', class_="simple-pagination__page-number")[-1].find('span', class_="simple-pagination__page-number-link simple-pagination__page-number-link_active"):
                max_page = page
            else:
                max_page = el_page.find('ul').findAll('li', class_="simple-pagination__page-number")[-1]
                max_page = int(max_page['data-page'].replace('\n', '').strip(' '))

            if page < max_page:
                time.sleep(10)
                links = self.getIndeksLink(links, page+1, cat_link, category, date)

        return links

    def getDetailBerita(self, links):
        all_articles = {}
        for link in links:
            time.sleep(10)
            #link
            url = link[0]
            response = requests.get(url)
            html = response.text
            # Create a BeautifulSoup object from the HTML: soup
            soup = BeautifulSoup(html, "html5lib")

            #articleid
            articles['id'] = int(soup.find('article', class_="navbar--menu--item__headline")["data-article-id"])
            articles['id']

            #extract subcategory from breadcrumb
            bc = soup.find('ul', class_="breadcrumb__wrap")
            if not bc:
                continue

            bc = soup.find('ul', class_="read-page--breadcrumb")
            if not bc:
                continue
            cat = bc.findAll('a')[-2].text
            sub = bc.findAll('a')[-1].text
            if ("foto" in sub.lower()) or  "video" in sub.lower():
                continue

            #category
            articles['category'] = cat
            articles['subcategory'] = sub

            #article_url
            articles['url'] = url

            #article
            article = soup.find("div", class_="article-content-body__item-content")

            #extract date
            pubdate = soup.find('p', class_="read-page--header--author__datetime-wrapper").find('time').text
            pubdate = pubdate.strip(' \t\n\r')
            pubdate = pubdate.replace(' WIB','')
            articles['pubdate']=datetime.strftime(datetime.strptime(pubdate, "%d %b %Y, %H:%M"), "%Y-%m-%d %H:%M:%S")
            articles['pubdate']

            #extract author
            author = soup.find('a', class_="read-page--header--author__link url fn").find('span', class_="read-page--header--author__name fn").text
            articles['author'] = author

            #extract title
            title = soup.find('header', class_="read-page--header").find('h1').text
            articles['title'] = title

            #source
            articles['source'] = 'Liputan6'

            #extract comments count
            comments = soup.find('li', class_="read-page--social-share__list-item js-social-share-comment").find('a')
            comments = int(comments.find('span', class_="read-page--social-share__comment-total").text)
            articles['comments'] = comments

            #extract tags
            tags = soup.findAll('span', class_="tags--snippet__name")
            tags = ','.join([x.text for x in tags])
            articles['tags'] = tags

            #extract images
            image = soup.find('picture', class_="read-page--photo-gallery--item__picture").find('img')['src']
            articles['image'] = image


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
            content = re.sub(r'\n|\t|\b|\r','',detail.text)
            articles['content']
            #print('memasukkan berita id ', articles['id'])
            all_articles.append(articles)
        return all_articles
