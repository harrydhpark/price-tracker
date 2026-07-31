# -*- coding: utf-8 -*-
import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')

with open("data/debug_public_samsung.html", "r", encoding="utf-8") as f:
    html = f.read()

# Search for hrefs containing /p/ or /product/
links = re.findall(r'href=["\']([^"\']*)["\']', html)
product_links = [l for l in set(links) if '/p/' in l or 'product' in l or 'sound-and-vision' in l]
print(f"Found {len(product_links)} links matching product patterns:")
for l in product_links[:10]:
    print(" ", l)

prices = re.findall(r'(\d+[\.,]\d{2})\s*€|€\s*(\d+[\.,]\d{2})', html)
print(f"Found {len(prices)} price matches in Public HTML")
if prices:
    print(" Sample prices:", prices[:5])
