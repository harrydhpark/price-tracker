# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def inspect_kotsovolos_cards():
    path = "data/debug_kotsovolos_samsung.html"
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.product, [class*="productCard"], [class*="product-card"], .product-item, .product-tile')
    print(f"➔ Found {len(cards)} cards in Kotsovolos")
    for i, c in enumerate(cards[:10]):
        title_el = c.select_one('[class*="title"], h2, h3, a[title], .product-title, .title')
        price_el = c.select_one('[class*="price"], .current-price, .sale-price, .price')
        link_el = c.select_one('a[href]')
        t = title_el.get_text(strip=True) if title_el else "N/A"
        p = price_el.get_text(strip=True) if price_el else "N/A"
        l = link_el['href'] if link_el else "N/A"
        print(f"  [{i+1}] Title: {t[:60]} | Price: {p} | Link: {l}")

if __name__ == '__main__':
    inspect_kotsovolos_cards()
