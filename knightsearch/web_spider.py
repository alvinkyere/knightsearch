import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
import sqlite3
from urllib.parse import urljoin, urlparse


def crawler(start_url, max_pages = 1000000):
    conn = sqlite3.connect('crawled_pages.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS pages (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              url TEXT UNIQUE,
              content TEXT,
              cleaned_content TEXT,
              title TEXT,
              outgoing_links TEXT,
              pagerank REAL
        )
''')
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    url_frontier = start_url if isinstance(start_url, list) else [start_url]

    visited_pages = set()
    while url_frontier and len(visited_pages) < max_pages:
        url = url_frontier.pop(0)
        if url.endswith(".xml") or "sitemap" in url:
            continue
        if url in visited_pages:
            continue
        

        print(f"Crawling {url}")
        try:
           response = requests.get(url, timeout=5)
        except:
            continue
        if url.endswith(".xml") or "sitemap" in url:
            continue
        if response.status_code != 200:
            continue
        if "xml" in response.headers.get("Content-Type", ""):
            continue
        title = ""
        soup = BeautifulSoup(response.content, 'html.parser')
        if soup.find('title'):
            title = soup.find('title').string

        outgoing_links = []

        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                outgoing_links.append(href)

        c.execute('INSERT OR REPLACE INTO pages (url, content, cleaned_content, title, outgoing_links) VALUES (?, ?, ?, ?, ?)', 
                  (url, str(soup), soup.get_text(), title, ','.join(outgoing_links)))
        conn.commit()
        links = soup.find_all('a')
    
        print(links)

        for link in soup.find_all('a'):
            href = link.get("href")
            if not href:
                continue

            absolute_url = urljoin(url, href)
            parsed = urlparse(absolute_url)

            if (
                parsed.netloc.endswith("calvin.edu")
                and absolute_url not in visited_pages
                and absolute_url not in url_frontier
                and "sitemap" not in absolute_url
                and not absolute_url.endswith((".pdf", ".jpg", ".png", ".xml"))
            ):
                url_frontier.append(absolute_url)
        visited_pages.add(url)
    conn.close()
    print("CRAWLING COMPLETE")
seed_urls = ["https://calvin.edu"]
crawler(seed_urls, 500000)
