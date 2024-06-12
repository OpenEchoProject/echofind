# Écho Find

import sqlite3
import requests
from bs4 import BeautifulSoup
import time
from urllib.robotparser import RobotFileParser
from requests.exceptions import HTTPError

# Initialize the database and create table
conn = sqlite3.connect('crawled_links.db')
c = conn.cursor()
c.execute('''
          CREATE TABLE IF NOT EXISTS links
          ([generated_id] INTEGER PRIMARY KEY, [url] text, [title] text)
          ''')
conn.commit()

def can_crawl(url, rp):
    return rp.can_fetch("*", url)

def crawl(start_url):
    rp = RobotFileParser()
    rp.set_url(requests.compat.urljoin(start_url, '/robots.txt'))
    rp.read()

    urls_to_crawl = {start_url}
    crawled_urls = set()

    while urls_to_crawl:
        current_url = urls_to_crawl.pop()
        if current_url in crawled_urls or not can_crawl(current_url, rp):
            continue

        try:
            response = requests.get(current_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            continue

        crawled_urls.add(current_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').get_text() if soup.title else 'No title found'

        # Insert link into the database
        c.execute('INSERT INTO links (url, title) VALUES (?, ?)', (current_url, title))
        conn.commit()

        for link in soup.find_all('a', href=True):
            absolute_link = requests.compat.urljoin(current_url, link['href'])
            if absolute_link not in crawled_urls and absolute_link not in urls_to_crawl:
                urls_to_crawl.add(absolute_link)
    while urls_to_crawl:
        current_url = urls_to_crawl.pop()
        if current_url in crawled_urls or not can_crawl(current_url, rp):
            continue

        try:
            response = requests.get(current_url)
            response.raise_for_status()
        except HTTPError as e:
            if e.response.status_code == 404:
                print(f"404: Not found: {current_url}")
            elif e.response.status_code == 200:
                print(f"200: OK: {current_url}")
            else:
                print(f"HTTP error: {e}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            continue
    conn.close()

def print_crawled_links():
    # Reconnect to the database
    conn = sqlite3.connect('crawled_links.db')
    c = conn.cursor()
    
    # Query the database for all links
    c.execute('SELECT * FROM links')
    
    # Fetch all rows
    links = c.fetchall()
    
    # Print each link
    for link in links:
        print(f"ID: {link[0]}, URL: {link[1]}, Title: {link[2]}")
    
    # Close the connection
    conn.close()

print_crawled_links()


if __name__ == "__main__":
    start_url = 'https://wikipedia.org/'
    crawl(start_url)
