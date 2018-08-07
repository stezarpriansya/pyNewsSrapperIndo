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

class Mobil123:
	def getIndeksLink(self, links, page, cat_link, cat, date=datetime.strftime(datetime.today(), '%Y/%m/%d')):
	    """
	    Untuk mengambil seluruh url
	    link pada indeks category tertentu
	    date format : YYYY/mm/dd
		category : berita-otomotif, mobil-baru, review, panduan-pembeli, 
	    """
	    print("page ", page)
	    url = "https://www.mobil123.com/berita/"+cat+"?page_number="+str(page)
	    print(url)

	    # Make the request and create the response object: response
	    try:
	        response = requests.get(url)
	    except ConnectionError:
	        print("Connection Error, but it's still trying...")
	        time.sleep(10)
	        links = self.getIndeksLink(links, page+1, cat, category, date)
	    # Extract HTML texts contained in Response object: html
	    html = response.text
	    # Create a BeautifulSoup object from the HTML: soup
	    soup = BeautifulSoup(html, "html5lib")

	    contentDiv = soup.findAll('article', class_="article")
	    if contentDiv:
	        for post in contentDiv.findAll('a'):
	            link = [post.find('a', href=True)['href'], cat]
	            links.append(link)

	    el_page = el_page = soup.find('ul', class_="pagination")
	    if el_page:
	        last_page = el_page.findAll('a')[-3].text
	        active_page = el_page.find('li', class_="active").text

	        if last_page > active_page:
	            time.sleep(10)
	            links = self.getIndeksLink(links, int(active_page)+1, cat, date)
	        
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

        #extract subcategory from breadcrumb
        bc = soup.find('div', class_="article__content--header")
        if not bc:
            continue

        sub = bc.findAll('a')[0].text
        if ("foto" in sub.lower()) or  "video" in sub.lower():
            continue

        #category
        articles['category'] = 'Otomotif'
        articles['subcategory'] = sub

        #article_url
        articles['url'] = url

        #article
        article = soup.find('div', class_="article__story-more")

        #extract date
        pubdate = soup.find('div', class_="article__meta").find('span', attrs={"itemprop":"datePublished"}).text
        pubdate = pubdate.strip(' \t\n\r')
        articles['pubdate'] = datetime.strftime(datetime.strptime(pubdate, "%d %B %Y %H:%M"), "%Y-%m-%d %H:%M:%S")

        #articleid
        articles['id'] = int(soup.find('meta', attrs={"name":"ga:cns:details:news_id"})['content'])
        
        #extract editor
        author = soup.find('meta', attrs={"name":"ga:cns:details:author"})['content']
        articles['author'] = author

        #extract title
        title = soup.find('h1', class_="article__title").text
        articles['title'] = title

        #source
        articles['source'] = 'mobil123.com'

        #extract comments count
        articles['comments'] = 0

        #extract tags
        tags = soup.find('meta', attrs={"name":"keywords"})['content']
        articles['tags'] = tags

        #extract images
        image = soup.find('div', attrs={"itemprop":"image"}).find('img')['data-src']
        articles['image'] = image

        #hapus link sisip
        for link in article.findAll('div'):
            link.decompose()
            
        for link in article.findAll('small'):
            link.decompose()
    
        #extract content
        detail = BeautifulSoup(article.decode_contents().replace('<br/>', ' '), "html5lib")
        content = re.sub(r'\n|\t|\b|\r','',detail.text)
        articles['content']
        #print('memasukkan berita id ', articles['id'])
        all_articles.append(articles)
    return all_articles