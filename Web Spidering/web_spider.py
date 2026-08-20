import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
import sqlite3

def crawler(start_url, max_pages = 200):
    conn = sqlite3.connect('crawled_pages.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS pages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              url TEXT UNIQUE,
              content TEXT
        )
''')
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    url_frontier = [start_url]

    visited_pages = set()
    while url_frontier and len(visited_pages) < max_pages:
        url = url_frontier.pop(0)
        if url in visited_pages:
            continue
        

        print(f"Crawling {url}")
        response = requests.get(url)


        if response.status_code != 200:
            continue


        soup = BeautifulSoup(response.content, 'html.parser')

        c.execute('INSERT OR IGNORE INTO pages (url, content) VALUES (?, ?)', (url, str(soup)))
        conn.commit()
        links = soup.find_all('a')
    
        print(links)

        for link in links:
            href = link.get("href")
            if href and 'http' in href and href not in visited_pages:
                url_frontier.append(href)
        visited_pages.add(url)
    conn.close()
    print("CRAWLING COMPLETE")
seed_urls = ["https://live-calvin-university.pantheonsite.io/sitemaps/default/sitemap.xml?page=1",
              "https://live-calvin-university.pantheonsite.io/sitemaps/default/sitemap.xml?page=2",
              "https://live-calvin-university.pantheonsite.io/sitemaps/default/sitemap.xml?page=3",
              "https://live-calvin-university.pantheonsite.io/sitemaps/default/sitemap.xml?page=4",
              "https://live-calvin-university.pantheonsite.io/sitemaps/default/sitemap.xml?page=5",
              "https://live-calvin-university.pantheonsite.io/sitemaps/default/sitemap.xml?page=6",
              "https://live-calvin-university.pantheonsite.io/sitemaps/default/sitemap.xml?page=7",
              "https://live-calvin-university.pantheonsite.io/sitemaps/default/sitemap.xml?page=8",
              "https://live-calvin-university.pantheonsite.io/sitemaps/default/sitemap.xml?page=9"]
for url in seed_urls:
    crawler(url, 10000)
