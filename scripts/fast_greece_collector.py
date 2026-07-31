# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from scrapling.fetchers import StealthySession

sys.stdout.reconfigure(encoding='utf-8')

TIMEOUT_MULTIPLIER = float(os.environ.get("TIMEOUT_MULTIPLIER", "1.0"))

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

def parse_items_from_body(body, brand):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, 'html.parser')
    products = []
    seen = set()

    # Search for all links with title or text containing brand
    links = soup.find_all('a')
    for link in links:
        title = link.get_text(strip=True) or link.get('title', '')
        if not title or len(title) < 8:
            continue
            
        title_upper = title.upper()
        if brand.lower() not in title.lower():
            continue
            
        if not any(x in title_upper for x in ["TV", "ΤΗΛΕΟΡΑΣΗ", "OLED", "QNED", "UHD", "SMART", "4K", "CRYSTAL", "QLED", "MINI LED"]):
            continue
            
        if title in seen:
            continue
        seen.add(title)
        
        url = link.get('href', '')
        if url and not url.startswith('http'):
            if "kotsovolos" in url or not url.startswith('/'):
                url = "https://www.kotsovolos.gr" + url
            else:
                url = "https://www.public.gr" + url
                
        card = link.parent
        for _ in range(4):
            if card and card.parent:
                card = card.parent
            else:
                break
                
        price_val = 0.0
        if card:
            card_text = card.get_text()
            price_m = re.search(r'€\s*([\d.]+)', card_text) or re.search(r'([\d.]+)\s*€', card_text)
            if price_m:
                try:
                    price_val = float(price_m.group(1))
                except ValueError:
                    price_val = 0.0
                    
        size_m = re.search(r'(\d{2,3})\s*(?:[″"]|inch|인치)', title)
        size_val = int(size_m.group(1)) if size_m else 55
        model_code = extract_model_code_from_title(title_upper, brand, size_val)
        
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

def collect_greece_volume():
    print("--------------------------------------------------")
    print("🇬🇷 Running Multi-Page Volume Extractor for Greece (Goal: 100+ items)")
    print("--------------------------------------------------")
    
    os.makedirs("data", exist_ok=True)
    
    # 1. Kotsovolos Pages 1..5 across categories
    kotsovolos_configs = {
        "samsung": [
            "https://www.kotsovolos.gr/sound-vision/televisions/led-lcd?page={p}",
            "https://www.kotsovolos.gr/sound-vision/televisions/samsung-oled?page={p}",
            "https://www.kotsovolos.gr/sound-vision/televisions?manufacturer=samsung&page={p}"
        ],
        "lg": [
            "https://www.kotsovolos.gr/sound-vision/televisions/led-lcd?page={p}",
            "https://www.kotsovolos.gr/sound-vision/televisions/oled?page={p}",
            "https://www.kotsovolos.gr/sound-vision/televisions?manufacturer=lg&page={p}"
        ]
    }
    
    # 2. Public Pages 1..5 across categories
    public_configs = {
        "samsung": [
            "https://www.public.gr/cat/sound-and-vision/tvs/qled?page={p}",
            "https://www.public.gr/cat/sound-and-vision/tvs/oled?page={p}",
            "https://www.public.gr/cat/sound-and-vision/tvs/4k-ultra-hd?page={p}"
        ],
        "lg": [
            "https://www.public.gr/cat/sound-and-vision/tvs/oled?page={p}",
            "https://www.public.gr/cat/sound-and-vision/tvs/4k-ultra-hd?page={p}",
            "https://www.public.gr/cat/sound-and-vision/tvs/qled?page={p}"
        ]
    }
    
    with StealthySession(headless=True) as session:
        # Process Kotsovolos
        for brand, url_templates in kotsovolos_configs.items():
            print(f"\n[KOTSOVOLOS] Collecting {brand.upper()} multi-page catalog...")
            all_items = []
            seen_titles = set()
            for tmpl in url_templates:
                for p in range(1, 4): # Pages 1..3
                    url = tmpl.format(p=p)
                    try:
                        res = session.fetch(url, wait=int(2500 * TIMEOUT_MULTIPLIER))
                        body = res.body if hasattr(res, 'body') else str(res)
                        if isinstance(body, bytes):
                            body = body.decode('utf-8', errors='ignore')
                        parsed = parse_items_from_body(body, brand)
                        new_count = 0
                        for item in parsed:
                            if item["title"] not in seen_titles:
                                seen_titles.add(item["title"])
                                all_items.append(item)
                                new_count += 1
                        print(f"  ➔ Page {p} ({url[:60]}...): +{new_count} new items")
                    except Exception as e:
                        print(f"  ⚠️ Page {p} error ({url[:60]}...): {e}")
                        
            out_file = f"data/raw_kotsovolos_{brand}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(all_items, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved {len(all_items)} total items to {out_file}")

        # Process Public
        for brand, url_templates in public_configs.items():
            print(f"\n[PUBLIC] Collecting {brand.upper()} multi-page catalog...")
            all_items = []
            seen_titles = set()
            for tmpl in url_templates:
                for p in range(1, 4): # Pages 1..3
                    url = tmpl.format(p=p)
                    try:
                        res = session.fetch(url, wait=int(2500 * TIMEOUT_MULTIPLIER))
                        body = res.body if hasattr(res, 'body') else str(res)
                        if isinstance(body, bytes):
                            body = body.decode('utf-8', errors='ignore')
                        parsed = parse_items_from_body(body, brand)
                        new_count = 0
                        for item in parsed:
                            if item["title"] not in seen_titles:
                                seen_titles.add(item["title"])
                                all_items.append(item)
                                new_count += 1
                        print(f"  ➔ Page {p} ({url[:60]}...): +{new_count} new items")
                    except Exception as e:
                        print(f"  ⚠️ Page {p} error ({url[:60]}...): {e}")
                        
            out_file = f"data/raw_public_{brand}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(all_items, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved {len(all_items)} total items to {out_file}")

if __name__ == '__main__':
    collect_greece_volume()
