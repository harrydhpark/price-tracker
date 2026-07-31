# -*- coding: utf-8 -*-
import sys
import os
import re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

with open("data/debug_public_search_lg.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
links = soup.find_all('a', href=True)
prod_links = []
for l in links:
    href = l['href']
    txt = l.get_text(strip=True)
    if 'tv' in href.lower() or 'lg' in href.lower() or 'sound-and-vision' in href.lower() or 'p/' in href:
        if len(txt) > 5:
            prod_links.append((href, txt))

print(f"➔ Public Search LG matching links: {len(prod_links)}")
for h, t in prod_links[:15]:
    print(f"  Href: {h[:60]} | Text: {t[:60]}")
