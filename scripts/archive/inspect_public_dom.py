# -*- coding: utf-8 -*-
import sys
import os
import re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

with open("data/debug_public_samsung.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
print("HTML length:", len(html))

# Check for product containers
elements = soup.find_all(attrs={"class": re.compile(r'product|item|card|tile|grid', re.I)})
print(f"Found {len(elements)} matching class elements")

for el in elements[:20]:
    t = el.get_text(strip=True)
    if "samsung" in t.lower() or "tv" in t.lower() or "€" in t:
        print(f"  Class: {el.get('class')} | Text: {t[:100]}")
