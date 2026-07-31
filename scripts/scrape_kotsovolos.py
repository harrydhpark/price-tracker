# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from bs4 import BeautifulSoup
from scrapling.fetchers import StealthySession

sys.stdout.reconfigure(encoding='utf-8')

TIMEOUT_MULTIPLIER = float(os.environ.get("TIMEOUT_MULTIPLIER", "1.0"))

price_regex = re.compile(r'€?\s*(\d[\d\s’\x27\x60,.]*[,.]\d{2}|\d+)\s*€?')

def extract_model_code_from_title(title_upper, brand, size_val):
    if brand.lower() == "samsung":
        patterns = [
            r'(QN\d{2,3}[FH])',
            r'(S\d{2}[FH])',
            r'(U\d{4}[FH])',
            r'(M\d{2}[FH])',
            r'(R\d{2}[FH])',
            r'(LS03[A-Z]{1,2})',
            r'(F\d{4})',
            r'(MR\d{2}[FH])'
        ]
        for pat in patterns:
            m = re.search(pat, title_upper)
            if m:
                matched_series = m.group(1)
                if "R85" in matched_series or "R95" in matched_series or "MR" in matched_series:
                    return f"MRE{size_val}{matched_series}"
                elif "U8" in matched_series or "M7" in matched_series or "F6" in matched_series:
                    return f"UE{size_val}{matched_series}"
                else:
                    return f"QE{size_val}{matched_series}"
    elif brand.lower() == "lg":
        patterns = [
            r'(\d{2,3}[A-Z0-9]*[CGBM]\d[0-9A-Z]*)',
            r'(\d{2,3}QNED\d{1,2}[A-Z0-9]*)',
            r'(\d{2,3}UA\d{2}[A-Z0-9]*)',
            r'(\d{2,3}NU\d{2}[A-Z0-9]*)'
        ]
        for pat in patterns:
            m = re.search(pat, title_upper)
            if m:
                return m.group(1)
    return "Unknown"

def parse_kotsovolos_html(html, brand):
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    seen_titles = set()

    # Find all anchor tags with title or text containing brand
    links = soup.find_all('a')
    for link in links:
        title = link.get_text(strip=True) or link.get('title', '')
        if not title or len(title) < 10:
            continue
            
        title_upper = title.upper()
        if brand.lower() not in title.lower():
            continue
        if not any(x in title_upper for x in ["TV", "ΤΗΛΕΟΡΑΣΗ", "OLED", "QNED", "UHD", "SMART", "4K", "CRYSTAL"]):
            continue
            
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        url = link.get('href', '')
        if url and not url.startswith('http'):
            url = "https://www.kotsovolos.gr" + url
            
        card = link.parent
        for _ in range(4):
            if card and card.parent:
                card = card.parent
            else:
                break
                
        price_val = 0.0
        if card:
            card_text = card.get_text()
            price_m = re.search(r'€\s*([\d.]+)', card_text)
            if price_m:
                try:
                    price_val = float(price_m.group(1))
                except ValueError:
                    price_val = 0.0
                    
        size_m = re.search(r'(\d{2,3})\s*(?:[″"]|inch|인치)', title)
        size_val = int(size_m.group(1)) if size_m else 55
        model_code = extract_model_code_from_title(title.upper(), brand, size_val)
        
        products.append({
            "title": title,
            "model_code": model_code,
            "price": price_val,
            "url": url,
            "in_stock": True,
            "cashback": 0,
            "promo": ""
        })
        
    return products

def scrape_kotsovolos():
    print("[KOTSOVOLOS] Starting scraping Kotsovolos Greece...")
    os.makedirs("data", exist_ok=True)
    
    brand_urls = {
        "samsung": [
            "https://www.kotsovolos.gr/sound-vision/televisions/led-lcd",
            "https://www.kotsovolos.gr/sound-vision/televisions/samsung-oled",
            "https://www.kotsovolos.gr/sound-vision/televisions?manufacturer=samsung"
        ],
        "lg": [
            "https://www.kotsovolos.gr/sound-vision/televisions/led-lcd",
            "https://www.kotsovolos.gr/sound-vision/televisions/oled",
            "https://www.kotsovolos.gr/sound-vision/televisions?manufacturer=lg"
        ]
    }
    
    with StealthySession(headless=True) as session:
        for brand, urls in brand_urls.items():
            print(f"➔ Scrape Kotsovolos {brand.upper()} across {len(urls)} targeted category URLs...")
            all_prods = []
            seen_titles = set()
            for url in urls:
                try:
                    res = session.fetch(url, wait=int(2500 * TIMEOUT_MULTIPLIER))
                    body = res.body if hasattr(res, 'body') else str(res)
                    if isinstance(body, bytes):
                        body = body.decode('utf-8', errors='ignore')
                        
                    prods = parse_kotsovolos_html(body, brand)
                    for p in prods:
                        if p["title"] not in seen_titles:
                            seen_titles.add(p["title"])
                            all_prods.append(p)
                except Exception as e:
                    print(f"  ⚠️ Fetch error for {url}: {e}")
                    
            print(f"  ➔ Total unique extracted products for Kotsovolos {brand.upper()}: {len(all_prods)}")
            out_file = f"data/raw_kotsovolos_{brand}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(all_prods, f, ensure_ascii=False, indent=2)
            print(f"  ➔ Saved {len(all_prods)} records to {out_file}")

if __name__ == '__main__':
    scrape_kotsovolos()
