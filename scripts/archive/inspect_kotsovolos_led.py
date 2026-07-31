# -*- coding: utf-8 -*-
import sys
import os
import re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

with open("data/debug_kotsovolos_led.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
links = soup.find_all('a', href=re.compile(r'/sound-vision/televisions/'))
prods = []
for l in links:
    href = l.get('href', '')
    title = l.get_text(strip=True) or l.get('title', '')
    if title and ("samsung" in title.lower() or "lg" in title.lower() or "tv" in title.lower() or "τηλεοραση" in title.lower()):
        prods.append((href, title))

print(f"➔ Kotsovolos LED extracted product links: {len(prods)}")
for h, t in prods[:10]:
    print(f"  Title: {t[:60]} | Href: {h[:60]}")
