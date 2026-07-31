# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from bs4 import BeautifulSoup
from scrapling.fetchers import StealthySession

sys.stdout.reconfigure(encoding='utf-8')

TIMEOUT_MULTIPLIER = float(os.environ.get("TIMEOUT_MULTIPLIER", "1.0"))

price_regex = re.compile(r'(\d[\d\s’\x27\x60,.]*[,.]\d{2}|\d[\d\s’\x27\x60,.]*)')

def extract_model_code_from_title(title_upper, brand, size_val):
    if brand.lower() == "samsung":
        patterns = [
            r'(QN\d{2,3}[FH])',    # QN900H, QN90F 등
            r'(S\d{2}[FH])',       # S95F, S90H, S85F 등
            r'(U\d{4}[FH])',       # U8000F, U8090H 등
            r'(M\d{2}[FH])',       # M70H 등
            r'(R\d{2}[FH])',       # R85H, R95H 등
            r'(LS03[A-Z]{1,2})',   # LS03HE, LS03F 등
            r'(F\d{4})',           # F6000 등
            r'(MR\d{2}[FH])'       # MR95F 등
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
            r'([OLED]*[A-Z0-9]*[CGBM]\d[0-9A-Z]*)',
            r'(QNED\d{2}[A-Z0-9]*)',
            r'(UA\d{2}[A-Z0-9]*)',
            r'(NU\d{2}[A-Z0-9]*)'
        ]
        for pat in patterns:
            m = re.search(pat, title_upper)
            if m:
                return m.group(1)
    return "Unknown"

def parse_public_html(html, brand):
    soup = BeautifulSoup(html, 'html.parser')
    products = []
    
    # Check JSON-LD
    json_ld_tags = soup.find_all('script', type='application/ld+json')
    for tag in json_ld_tags:
        try:
            data = json.loads(tag.string)
            if isinstance(data, dict) and data.get('@type') == 'Product':
                title = data.get('name', '')
                price = data.get('offers', {}).get('price', 0.0)
                url = data.get('offers', {}).get('url', '')
                model_code = data.get('sku', '') or data.get('mpn', '') or "Unknown"
                if title:
                    products.append({
                        "title": title,
                        "model_code": model_code,
                        "price": float(price) if price else 0.0,
                        "url": url,
                        "in_stock": True,
                        "cashback": 0,
                        "promo": ""
                    })
        except Exception:
            pass

    cards = soup.select('.product, [class*="productCard"], [class*="product-card"], .product-item, [data-testid="product-card"]')
    for card in cards:
        title_el = card.select_one('[class*="title"], h2, h3, a[title], [data-testid="product-title"]')
        if not title_el:
            continue
        title = title_el.get_text(strip=True) or title_el.get('title', '')
        if not title or brand.lower() not in title.lower():
            continue
            
        link_el = card.select_one('a[href]')
        url = link_el['href'] if link_el else ""
        if url and not url.startswith('http'):
            url = "https://www.public.gr" + url
            
        price_el = card.select_one('[class*="price"], .current-price, .sale-price, [data-testid="product-price"]')
        price_val = 0.0
        if price_el:
            price_str = price_el.get_text(strip=True).replace('€', '').replace(' ', '').replace('.', '').replace(',', '.')
            p_match = price_regex.search(price_str)
            if p_match:
                try:
                    price_val = float(p_match.group(1))
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

def scrape_public():
    print("[PUBLIC] Starting scraping Public Greece...")
    os.makedirs("data", exist_ok=True)
    
    configs = [
        ("samsung", "https://www.public.gr/cat/sound-and-vision/tvs?m=samsung"),
        ("lg", "https://www.public.gr/cat/sound-and-vision/tvs?m=lg")
    ]
    
    with StealthySession(headless=True) as session:
        for brand, url in configs:
            print(f"➔ Scrape Public {brand.upper()}: {url}")
            all_prods = []
            try:
                res = session.fetch(url, wait=int(3000 * TIMEOUT_MULTIPLIER))
                body = res.body if hasattr(res, 'body') else str(res)
                if isinstance(body, bytes):
                    body = body.decode('utf-8', errors='ignore')
                    
                prods = parse_public_html(body, brand)
                all_prods.extend(prods)
                print(f"  ➔ Extracted {len(prods)} products for Public {brand.upper()}")
            except Exception as e:
                print(f"  ❌ Error fetching Public {brand}: {e}")
                
            out_file = f"data/raw_public_{brand}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(all_prods, f, ensure_ascii=False, indent=2)
            print(f"  ➔ Saved {len(all_prods)} records to {out_file}")

if __name__ == '__main__':
    scrape_public()
