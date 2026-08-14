# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from scrapling.fetchers import StealthySession
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def test_mediamarkt_hu():
    urls_to_test = [
        "https://www.mediamarkt.hu/hu/category/_telev%C3%ADzi%C3%B3k-504930.html",
        "https://www.mediamarkt.hu/hu/search.html?query=LG+TV",
        "https://www.mediamarkt.hu/hu/search.html?query=Samsung+TV"
    ]
    
    with StealthySession(headless=True) as session:
        for url in urls_to_test:
            print(f"\n==========================================")
            print(f"[TESTING URL] {url}")
            print(f"==========================================")
            try:
                p = session.fetch(url, solve_cloudflare=True, wait=4000, timeout=45000)
                print(f"Status: {p.status}")
                html = str(p.html_content)
                print(f"HTML Length: {len(html)}")
                if "Verification Required" in html or "cf-chl" in html:
                    print("⚠️ Cloudflare challenge detected")
                else:
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.title.string if soup.title else "No Title"
                    print(f"Page Title: {title}")
                    
                    # Inspect product cards
                    links = soup.find_all('a', href=True)
                    prod_links = []
                    for l in links:
                        href = l['href']
                        if '/product/' in href or '/hu/product/' in href or '_tv' in href.lower() or '-tv-' in href.lower():
                            text = l.get_text(strip=True)
                            if len(text) > 8:
                                prod_links.append((text, href))
                    
                    print(f"Candidate product links found: {len(prod_links)}")
                    for t, h in prod_links[:5]:
                        print(f"  - Title: {t[:60]}... | Href: {h}")
                        
                    # Test price patterns in text
                    prices = re.findall(r'(\d[\d\s\.]*)\s*(?:Ft|HUF)', html)
                    print(f"Prices count: {len(prices)}")
                    if prices:
                        print("Sample prices (Ft):", prices[:5])
            except Exception as e:
                print(f"Error fetching {url}: {e}")

if __name__ == '__main__':
    test_mediamarkt_hu()
