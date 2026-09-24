from scrapling.fetchers import StealthySession
from bs4 import BeautifulSoup
import re, json

url = 'https://www.public.gr/product/tileoraseis/tileoraseis/samsung-neo-qled-50-4k-smart-tileorasi-qe50qn80fatxxh/2043689'
with StealthySession(headless=True) as session:
    res = session.fetch(url, wait=3000)
    soup = BeautifulSoup(res.body, 'html.parser')
    print('Title:', soup.title.string if soup.title else 'No title')
    
    # Check meta tags
    for meta in soup.find_all('meta'):
        p = meta.get('property', '') or meta.get('name', '')
        c = meta.get('content', '')
        if any(x in p.lower() for x in ['price', 'avail', 'stock', 'product:price']):
            print(f'Meta: {p} = {c}')
            
    # Check elements with price class
    for el in soup.find_all(class_=re.compile(r'price', re.I)):
        text = el.get_text(' ', strip=True)
        if '€' in text and len(text) < 100:
            print(f'Price element ({el.get("class")}): {text}')
