# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from scrapling.fetchers import StealthySession
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def inspect_page():
    url = "https://www.mediamarkt.hu/hu/search.html?query=LG+TV"
    with StealthySession(headless=True) as session:
        p = session.fetch(url, solve_cloudflare=True, wait=4000, timeout=45000)
        html = str(p.html_content)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Save HTML for inspection
        with open("scripts/sample_mm_hu_search.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print(f"Saved sample HTML ({len(html)} bytes).")
        
        # Look for product cards / items
        # Usually MediaMarkt uses data-test attributes or specific container classes
        cards = soup.find_all(lambda tag: tag.has_attr('data-test') and 'product' in str(tag.get('data-test', '')).lower())
        print(f"Found {len(cards)} tags with product data-test")
        
        # Look for all links with /hu/product/
        product_links = soup.find_all('a', href=lambda h: h and '/hu/product/' in h)
        print(f"Found {len(product_links)} /hu/product/ links")
        
        extracted = []
        seen = set()
        for link in product_links:
            href = link.get('href', '')
            # Find closest card or container
            container = link
            for _ in range(6):
                if not container:
                    break
                # Check text in container
                txt = container.get_text(" ", strip=True)
                if 'Ft' in txt and ('LG' in txt.upper() or 'SAMSUNG' in txt.upper()):
                    break
                container = container.parent
                
            if container:
                txt = container.get_text(" ", strip=True)
                # Find title
                title_elem = container.find(['h2', 'h3', 'p', 'span'], class_=lambda c: c and any(k in str(c).lower() for k in ['title', 'name', 'heading']))
                title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
                
                if title in seen or len(title) < 10:
                    continue
                seen.add(title)
                
                # Extract price (e.g. 129 999 Ft or 129.999 Ft)
                price_m = re.search(r'([\d\s\xa0\.]+)\s*Ft', txt)
                price_str = price_m.group(1).replace('\xa0', ' ').strip() if price_m else "N/A"
                
                extracted.append({
                    "title": title,
                    "price_ft": price_str,
                    "href": href,
                    "text_snippet": txt[:150]
                })
                
        print(f"Extracted {len(extracted)} products:")
        for idx, item in enumerate(extracted[:10]):
            print(f"[{idx+1}] {item['title']} | Price: {item['price_ft']} Ft | Link: {item['href'][:50]}")

if __name__ == '__main__':
    inspect_page()
