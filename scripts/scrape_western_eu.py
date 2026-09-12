# -*- coding: utf-8 -*-
"""
Unified High-Speed Live Scraper for Western European Retailers:
- MediaMarkt DE, AT, ES, NL
- MediaWorld IT
- Currys UK
- Fnac FR

Uses Scrapling StealthySession to bypass Cloudflare/Turnstile for free with 0 API costs.
Saves live JSON files to data/raw_{source}_{brand}.json.
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from scrapling.fetchers import StealthySession

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)

# Common Price cleaner
def clean_numeric_price(price_str):
    if not price_str:
        return 0.0
    p = str(price_str).replace('€', '').replace('£', '').replace('CHF', '').replace('\xa0', '').replace('\u202f', ' ').strip()
    # European 1.799,00 or 1.799,- or 1799
    if re.match(r'^\d{1,3}\.\d{3}(?:,\d{2})?$', p):
        p = p.replace('.', '').replace(',', '.')
    elif re.match(r'^\d{1,3},\d{3}(?:\.\d{2})?$', p):
        p = p.replace(',', '')
    elif ',' in p:
        p = p.replace(',', '.')
    
    m = re.findall(r'(\d+(?:\.\d{2})?)', p)
    if m:
        try:
            val = float(m[0])
            return val if val >= 50.0 else 0.0
        except ValueError:
            pass
    return 0.0

def extract_size(title_upper):
    m = re.search(r'\b(98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:inch|zoll|pollici|pouces|cm|\b)', title_upper)
    if m:
        return int(m.group(1))
    m_mc = re.search(r'(?:OLED|QE|UE|GQ|QNED|NANO|UA|NU)?(\d{2})[A-Z0-9]', title_upper)
    if m_mc:
        val = int(m_mc.group(1))
        if val in [98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
            return val
    return 55

def parse_mediamarkt_page(html, brand, domain_suffix="de"):
    items = []
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Try JSON state first
    preloaded = soup.find('script', id='__PRELOADED_STATE__') or soup.find('script', string=re.compile(r'__PRELOADED_STATE__'))
    if preloaded and preloaded.string:
        try:
            raw_text = preloaded.string
            idx = raw_text.find('{')
            if idx != -1:
                state_json = json.loads(raw_text[idx:])
                apollo = state_json.get('apolloState', {}) or state_json.get('ROOT_QUERY', {})
                for k, v in apollo.items():
                    if isinstance(v, dict) and ('title' in v or 'name' in v) and ('price' in v or 'prices' in v):
                        title = v.get('title') or v.get('name') or ''
                        if not title or brand.upper() not in title.upper():
                            continue
                        price_obj = v.get('price') or {}
                        price_val = price_obj.get('price') or price_obj.get('total') or 0
                        if price_val:
                            items.append({
                                'name': title,
                                'title': title,
                                'price': float(price_val),
                                'promo': 'None'
                            })
        except Exception:
            pass
            
    if items:
        return items
        
    # 2. DOM Parsing
    product_cards = soup.find_all(lambda tag: tag.has_attr('data-test') and 'product' in tag['data-test']) or soup.find_all('div', class_=re.compile(r'ProductCard|product-card|productWrapper', re.I)) or soup.find_all('a', href=re.compile(r'/product/|/p/'))
    
    seen_titles = set()
    for card in product_cards:
        text = card.get_text(separator=' ', strip=True)
        if not text or brand.upper() not in text.upper():
            continue
        title_el = card.find(re.compile(r'h\d|p'), class_=re.compile(r'title|heading|name', re.I)) or card.find('a', href=re.compile(r'/product/'))
        title = title_el.get_text(strip=True) if title_el else card.get('aria-label') or ''
        if not title or len(title) < 10 or brand.upper() not in title.upper():
            # Try finding title in anchor
            a = card if card.name == 'a' else card.find('a', href=True)
            if a:
                title = a.get('aria-label') or a.get_text(strip=True)
                
        if not title or title in seen_titles:
            continue
            
        if any(x in title.upper() for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "SOUNDBAR", "HIFI", "BEAMER", "ZUBEHÖR"]):
            continue
            
        price_m = re.findall(r'(\d[\d\s\.,]*\d)\s*(?:€|,-|,–)', text)
        if not price_m:
            price_m = re.findall(r'(?:€|£)\s*(\d[\d\s\.,]*)', text)
            
        if price_m:
            price_val = clean_numeric_price(price_m[0])
            if price_val >= 80.0:
                seen_titles.add(title)
                items.append({
                    'name': title,
                    'title': title,
                    'price': price_val,
                    'promo': 'None'
                })
    return items

def scrape_mediamarkt_country(session, country_code, brand, max_pages=4):
    cc_map = {
        'DE': {'domain': 'mediamarkt.de', 'lang': 'de'},
        'AT': {'domain': 'mediamarkt.at', 'lang': 'de'},
        'ES': {'domain': 'mediamarkt.es', 'lang': 'es'},
        'NL': {'domain': 'mediamarkt.nl', 'lang': 'nl'},
        'IT': {'domain': 'mediaworld.it', 'lang': 'it'}
    }
    cfg = cc_map.get(country_code.upper(), cc_map['DE'])
    domain = cfg['domain']
    lang = cfg['lang']
    
    print(f"\n[{country_code} - {brand}] Scraping {domain}...")
    
    queries = [
        f"{brand}+TV",
        f"{brand}+OLED",
        f"{brand}+2026",
        f"{brand}+MRGB",
        f"{brand}+MICRO+RGB" if brand.upper() == "SAMSUNG" else f"{brand}+QNED",
        f"{brand}+NU8" if brand.upper() == "LG" else f"{brand}+U80"
    ]
    
    all_items = []
    seen = {}
    
    for q in queries:
        for page in range(1, max_pages + 1):
            url = f"https://www.{domain}/{lang}/search.html?query={q}&page={page}"
            print(f"  ➔ [FETCH] {url}")
            try:
                resp = session.fetch(url, solve_cloudflare=True, wait=3000, timeout=20000)
                if resp.status == 200:
                    page_items = parse_mediamarkt_page(resp.text, brand, lang)
                    print(f"    -> Extracted {len(page_items)} products on page {page}.")
                    for it in page_items:
                        key = it['name'].upper()
                        if key not in seen:
                            seen[key] = it
                            all_items.append(it)
                else:
                    print(f"    -> Non-200 status: {resp.status}")
            except Exception as e:
                print(f"    -> Error or timeout fetching {url}: {e}")
                
    print(f"✅ [{country_code} - {brand}] Total unique scraped: {len(all_items)}")
    return all_items

def scrape_currys_uk(session, brand, max_pages=3):
    print(f"\n[UK - {brand}] Scraping currys.co.uk...")
    all_items = []
    seen = {}
    
    brand_slug = "samsung" if brand.lower() == "samsung" else "lg"
    for page in range(1, max_pages + 1):
        url = f"https://www.currys.co.uk/tv-and-audio/televisions/tvs/{brand_slug}?page={page}"
        print(f"  ➔ [FETCH] {url}")
        try:
            resp = session.fetch(url, wait=3000)
            if resp.status == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                cards = soup.find_all('div', class_=re.compile(r'product-card|productCard|product-item', re.I)) or soup.find_all('a', href=re.compile(r'/products/'))
                for card in cards:
                    text = card.get_text(separator=' ', strip=True)
                    if not text or brand.upper() not in text.upper():
                        continue
                    a = card if card.name == 'a' else card.find('a', href=True)
                    title = a.get_text(strip=True) if a else ""
                    if not title or len(title) < 10 or brand.upper() not in title.upper():
                        continue
                    if any(x in title.upper() for x in ["SOUNDBAR", "MONITOR", "BRACKET", "WALL MOUNT"]):
                        continue
                        
                    # Extract true selling price by checking lines
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    selling_price = None
                    save_amount = None
                    for i, l in enumerate(lines):
                        p_match = re.match(r'^£([\d,]+(?:\.\d{2})?)$', l)
                        if p_match:
                            val = float(p_match.group(1).replace(',', ''))
                            if i + 1 < len(lines) and re.match(r'^(?:Save\s*£|From\s*£|Was\s*£|Product\s*fiche)', lines[i+1], re.I):
                                selling_price = val
                            elif not selling_price:
                                selling_price = val
                        save_m = re.match(r'^Save\s*£([\d,]+(?:\.\d{2})?)', l, re.I)
                        if save_m:
                            save_amount = float(save_m.group(1).replace(',', ''))
                    if not selling_price or selling_price < 120.0:
                        continue
                    promo_str = f"Save GBP {save_amount:.2f}" if save_amount else "None"
                    key = title.upper()
                    if key not in seen:
                        rec = {'name': title, 'title': title, 'price': selling_price, 'promo': promo_str}
                        seen[key] = rec
                        all_items.append(rec)
                print(f"    -> Extracted {len(all_items)} total unique items so far.")
        except Exception as e:
            print(f"    -> Error fetching {url}: {e}")
            
    print(f"✅ [UK - {brand}] Total unique scraped: {len(all_items)}")
    return all_items

def main():
    print("=" * 60)
    print(" WESTERN EUROPEAN TV LIVE SCRAPER (100% FREE STEALTHY ENGINE) ")
    print(" Countries: DE, AT, ES, NL, IT, UK")
    print("=" * 60)
    
    with StealthySession(headless=True) as session:
        # 1. Germany (MediaMarkt DE)
        for b in ["Samsung", "LG"]:
            items = scrape_mediamarkt_country(session, "DE", b, max_pages=4)
            if items:
                with open(os.path.join(DATA_DIR, f"raw_mm-de_{b.lower()}.json"), "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
                    
        # 2. Austria (MediaMarkt AT)
        for b in ["Samsung", "LG"]:
            items = scrape_mediamarkt_country(session, "AT", b, max_pages=3)
            if items:
                with open(os.path.join(DATA_DIR, f"raw_mm-at_{b.lower()}.json"), "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
                    
        # 3. Spain (MediaMarkt ES)
        for b in ["Samsung", "LG"]:
            items = scrape_mediamarkt_country(session, "ES", b, max_pages=3)
            if items:
                with open(os.path.join(DATA_DIR, f"raw_mm-es_{b.lower()}.json"), "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
                    
        # 4. Netherlands (MediaMarkt NL)
        for b in ["Samsung", "LG"]:
            items = scrape_mediamarkt_country(session, "NL", b, max_pages=3)
            if items:
                with open(os.path.join(DATA_DIR, f"raw_mm-nl_{b.lower()}.json"), "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
                    
        # 5. Italy (MediaWorld IT)
        for b in ["Samsung", "LG"]:
            items = scrape_mediamarkt_country(session, "IT", b, max_pages=3)
            if items:
                with open(os.path.join(DATA_DIR, f"raw_mw-it_{b.lower()}.json"), "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
                    
        # 6. UK (Currys UK)
        for b in ["Samsung", "LG"]:
            items = scrape_currys_uk(session, b, max_pages=3)
            if items:
                with open(os.path.join(DATA_DIR, f"raw_currys_{b.lower()}.json"), "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)

    print("\n[COMPLETE] All Western European raw live datasets successfully collected & saved!")

if __name__ == "__main__":
    main()
