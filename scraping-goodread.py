import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import glob
import dash
from dash import dcc
from dash import html
from dash import Dash, dash_table
from dash.dependencies import Input, Output
import plotly.express as px

"""
Part 1 gets lots of book urls and saves them to .txt

"""

base_url = "https://www.goodreads.com/list/show/1.Best_Books_Ever?page="
urls = [base_url + str(i) for i in range(1, 101)]

book_link_tags = []

for url in urls:
    print(url[-2:])
    
    page = requests.get(url)
    soup = bs(page.content, 'html.parser')

    book_link_tags += soup.find_all('a', class_='bookTitle')
    

book_urls = ['https://www.goodreads.com' + book_link_tag.get('href')
              for book_link_tag in book_link_tags]

with open('book_urls.txt', 'w') as f:
    f.write("\n".join(book_urls))

"""
Part 2 save each book page to local

"""

will save first n book htmls. Increase gradually
n = 300

# prepare the book urls
with open('/Users/hieunguyen/Desktop/goodreads/book_urls.txt') as f:
    book_urls = f.readlines()
    book_urls = [book_url.strip() for book_url in book_urls]

saved_htmls = glob.glob('books/*.html')
saved_htmls = ['https://www.goodreads.com/book/show/' + saved_html.split('/')[1] for saved_html in saved_htmls]

# request each book html and save to disk if not already saved
for book_url in book_urls[:n]:
    
    if book_url + ".html" in saved_htmls:
        continue

    book_page = requests.get(book_url, headers={"User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"})
    
    with open('/Users/hieunguyen/Desktop/goodreads/books/' + book_url.split('/')[-1] + '.html', 'w') as f:
        f.write(book_page.text)
 

"""
Part 3 scrape each book page from local
"""

df = pd.DataFrame()

book_htmls = glob.glob('/Users/hieunguyen/Desktop/goodreads/books/*.html')
#book_htmls = glob.glob('/Users/hieunguyen/Desktop/goodreads/books/4934.The_Brothers_Karamazov.html')

for book_html in book_htmls:
    
    with open(book_html) as f:
        book_page = f.read()
    
    book_id = book_html.split('/')[6].split('.')[0].split('-')[0]
    book_soup = bs(book_page, 'html.parser')

    df.loc[book_id, 'url'] = book_html
    df.loc[book_id, 'title'] = book_soup.select('h1')[0].text.strip()
    try:
        df.loc[book_id, 'author'] = book_soup.select('span[data-testid="name"]')[0].text.strip()
    except:
        df.loc[book_id, 'author'] = book_soup.select('.authorName')[0].text.strip()
    try:
        df.loc[book_id, 'avg_rating'] = book_soup.select('.RatingStatistics__rating')[0].text.strip()
    except:
        df.loc[book_id, 'avg_rating'] = book_soup.select('span[itemprop="ratingValue"]')[0].text.strip()
    try:
        df.loc[book_id, 'rating_count'] = book_soup.select('span[data-testid="ratingsCount"]')[0].text.split()[0].strip()
    except:
        df.loc[book_id, 'rating_count'] = book_soup.select('meta[itemprop="ratingCount"]')[0].text.split()[0].strip()
    try:
        df.loc[book_id, 'description'] = book_soup.select('div[data-testid="description"]')[0].text.strip()
    except:
        df.loc[book_id, 'description'] = book_soup.select('#description')[0].text.strip()
    try:
        num_review = " ".join(book_soup.select('.reviewControls--left.greyText')[0].text.split())
        df.loc[book_id, 'num_reviews'] = num_review.split(' ')[-2]
    except:
        df.loc[book_id, 'num_reviews'] = book_soup.select('[data-testid="reviewsCount"]')[0].text.strip().split()[0]
    
df.index.name = 'book_id'
df.to_csv('/Users/hieunguyen/Desktop/goodreads/books2.csv', encoding='utf-8')
