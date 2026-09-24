# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import time
import urllib.request
import openpyxl
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from scrapling.fetchers import StealthySession

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
HISTORY_EU_DIR = os.path.join(ROOT_DIR, 'History_EU')
MASTER_REGISTRY_PATH = os.path.join(DATA_DIR, 'master_product_urls.json')
OUTPUT_PROBE_PATH = os.path.join(DATA_DIR, 'live_pdp_probed_models.json')

HEADERS_COMMON = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
}

def parse_price_number(text):
    if not text:
        return 0.0
    s = str(text).replace('€', '').replace('£', '').replace('CHF', '').replace('Kč', '').replace('Ft', '')
    s = s.replace('\xa0', '').replace('\u202f', '').replace(' ', '').strip()
    if not s:
        return 0.0
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    nums = re.findall(r'\d+(?:\.\d+)?', s)
    return float(nums[0]) if nums else 0.0

def probe_currys(url):
    try:
        html = None
        status = 200
        req = urllib.request.Request(url, headers=HEADERS_COMMON)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                status = resp.status
        except urllib.error.HTTPError as he:
            if he.code in [403, 301, 302, 307]:
                r = cffi_requests.get(url, impersonate='chrome124', timeout=10)
                html = r.text
                status = r.status_code
            else:
                return None
        except Exception:
            r = cffi_requests.get(url, impersonate='chrome124', timeout=10)
            html = r.text
            status = r.status_code

        if status != 200 or not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')
        text_lower = soup.get_text(' ', strip=True).lower()
        if any(x in text_lower for x in ['out of stock', 'currently unavailable', 'no longer available', 'sorry, this product is no longer']):
            return None

        price = None
        avail = 'InStock'
        for s in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(s.string)
                if isinstance(data, dict) and 'offers' in data:
                    offers = data['offers']
                    if isinstance(offers, dict):
                        price = offers.get('price')
                        avail = offers.get('availability', '')
                    elif isinstance(offers, list):
                        price = offers[0].get('price')
                        avail = offers[0].get('availability', '')
            except Exception:
                pass

        if avail and 'outofstock' in str(avail).lower():
            return None

        pval = float(price) if price else 0.0
        if pval < 100.0:
            m = re.findall(r'£\s*(\d[\d,]*\d(?:\.\d{2})?)', text_lower)
            if m:
                pval = float(m[0].replace(',', ''))

        if pval < 100.0:
            return None

        return {
            'price': pval,
            'orig_price': None,
            'in_stock': True,
            'currency': 'GBP'
        }
    except Exception:
        return None

def probe_public_gr(session, url, brand, size_val):
    try:
        res = session.fetch(url, wait=2500)
        if res.status != 200:
            return None
            
        soup = BeautifulSoup(res.body, 'html.parser')
        title = soup.title.string if soup.title else ''
        text = soup.get_text(' ', strip=True)
        text_upper = text.upper()

        # Check if redirected to book / comic / manga or accessory
        if any(x in url.lower() for x in ['/books/', '/comics/', '/manga/']) or any(x in title.lower() for x in ['manga', 'βιβλίο', 'comic']):
            return None
        if not any(x in text_upper for x in ['ΤΗΛΕΟΡΑΣΗ', 'TILEORASI', 'TV', 'OLED', 'QNED', 'SMART']):
            return None

        # Check out of stock
        if any(x in text_upper for x in ['ΕΞΑΝΤΛΗΘΗΚΕ', 'ΜΗ ΔΙΑΘΕΣΙΜΟ', 'OUT OF STOCK', 'ΠΡΟΣΩΡΙΝΑ ΜΗ ΔΙΑΘΕΣΙΜΟ']):
            return None

        # Price from LD+JSON
        ld_price = None
        for s in soup.find_all('script', type='application/ld+json'):
            try:
                d = json.loads(s.string)
                if isinstance(d, dict) and 'offers' in d:
                    ld_price = d['offers'].get('price')
                    break
            except Exception:
                pass

        pval = 0.0
        if ld_price:
            try:
                pval = float(ld_price)
            except Exception:
                pass

        if pval < 100.0:
            # Clean text price
            clean_text = re.sub(r'(?:Κέρδος|Έκπτωση|όφελος|Δωροεπιταγή|Δώρο|από|-\s*)\s*\d[\d\.\s]*[,\.]\d{2}\s*€', '', text, flags=re.IGNORECASE)
            prices = re.findall(r'(\d[\d\.\s]*[,\.]\d{2})\s*€', clean_text)
            for p in prices:
                val = parse_price_number(p)
                if val >= 120.0:
                    pval = val
                    break

        if pval < 120.0:
            return None

        # Screen-size guard
        if size_val >= 70 and pval < 500.0:
            return None
        if size_val >= 55 and pval < 300.0:
            return None

        return {
            'price': pval,
            'orig_price': None,
            'in_stock': True,
            'currency': 'EUR'
        }
    except Exception:
        return None

def probe_alza_cz(session, url, brand, size_val):
    try:
        res = session.fetch(url, wait=2500)
        if res.status != 200:
            return None
            
        soup = BeautifulSoup(res.body, 'html.parser')
        text = soup.get_text(' ', strip=True)
        text_lower = text.lower()

        # Out of stock check
        if any(x in text_lower for x in ['prodej skončil', 'těšíme se na další', 'nedostupné', 'ukončen prodej', 'není skladem']):
            return None

        price_el = soup.select_one('.js-price-box__primary-price__value, .ads-pb__price-value, .price-box__primary-price, .c2')
        pval = 0.0
        if price_el:
            pval = parse_price_number(price_el.get_text(strip=True))

        if pval < 1000.0:
            prices = re.findall(r'(\d[\d\s\xa0]*)(?:,-|Kč)', text)
            for pr in prices:
                val = parse_price_number(pr)
                if val >= 3000.0 and val != 100000.0:
                    pval = val
                    break

        if pval < 2500.0:
            return None

        # Screen-size floor guard (eliminate accessories/frames)
        if size_val >= 70 and pval < 12000.0:
            return None
        elif size_val >= 50 and pval < 6000.0:
            return None
        elif size_val >= 40 and pval < 4000.0:
            return None

        return {
            'price': pval,
            'orig_price': None,
            'in_stock': True,
            'currency': 'CZK'
        }
    except Exception:
        return None

def probe_mediamarkt_ch(session, url, brand, size_val):
    try:
        res = session.fetch(url, wait=2500)
        if res.status != 200:
            return None
            
        soup = BeautifulSoup(res.body, 'html.parser')
        text = soup.get_text(' ', strip=True)
        text_upper = text.upper()

        if any(x in text_upper for x in ['NICHT MEHR VERFÜGBAR', 'AUSVERKAUFT', 'CURRENTLY UNAVAILABLE']):
            return None

        # Check seller
        seller_m = re.search(r'(?:Verkauft durch|Sold by)\s+([^\n\r.]+)', text, re.I)
        if seller_m:
            seller = seller_m.group(1).upper()
            if 'MEDIAMARKT' not in seller or 'PARTNER' in seller:
                return None

        # Price
        pval = 0.0
        clean_text = re.sub(r'CHF\s*\d+[\d\s’\x27\x60,.]*\s*(?:Cashback|Rabatt|Gutschein|Coupon|Zusatzrabatt|Ersparnis|Geschenk|Sparen)', '', text, flags=re.I)
        m = re.findall(r'CHF\s*([\d\s’\x27\x60,.]*(?:[.–]|,\d{2}|\.\d{2}))', clean_text)
        for raw in m:
            val = parse_price_number(raw)
            if val >= 100.0 and val not in [2025, 2026]:
                pval = val
                break

        if pval < 100.0:
            return None

        return {
            'price': pval,
            'orig_price': None,
            'in_stock': True,
            'currency': 'CHF'
        }
    except Exception:
        return None

def main():
    print('=' * 65)
    print(' 🌐 HIGH-SPEED LIVE PDP PROBE & REPLENISHMENT ENGINE ')
    print('=' * 65)

    f_prev = os.path.join(HISTORY_EU_DIR, '2026 0914', 'price tracker_EU_2026 0914_v1.xlsx')
    f_today = os.path.join(DATA_DIR, 'price tracker_EU_2026 0915_v1.xlsx')

    if not os.path.exists(f_prev) or not os.path.exists(f_today):
        print('[ERROR] Workbooks not found.')
        return

    wb_p = openpyxl.load_workbook(f_prev, read_only=True)
    wb_t = openpyxl.load_workbook(f_today, read_only=True)

    with open(MASTER_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        master = json.load(f)

    master_map = {}
    for k, v in master.items():
        c = str(v.get('country', '')).strip().upper()
        b = str(v.get('brand', '')).strip().lower()
        m = str(v.get('model_code', '')).strip().upper()
        master_map[(c, b, m)] = v

    sheet_meta = {
        'Currys_UK_SAMSUNG_Full': ('UK', 'samsung', 'Currys'),
        'Currys_UK_LG_Full': ('UK', 'lg', 'Currys'),
        'Public_GR_Samsung': ('GR', 'samsung', 'Public'),
        'Public_GR_LG': ('GR', 'lg', 'Public'),
        'Alza_CZ_Samsung': ('CZ', 'samsung', 'Alza'),
        'Alza_CZ_LG': ('CZ', 'lg', 'Alza'),
        'MediaMarkt_CH_SAMSUNG_Full': ('CH', 'samsung', 'MediaMarkt'),
        'MediaMarkt_CH_LG_Full': ('CH', 'lg', 'MediaMarkt'),
    }

    candidates = []
    for s_name, (c_code, b_name, r_name) in sheet_meta.items():
        if s_name not in wb_p.sheetnames or s_name not in wb_t.sheetnames:
            continue
        sp = wb_p[s_name]
        st = wb_t[s_name]
        rows_p = list(sp.iter_rows(values_only=True))
        rows_t = list(st.iter_rows(values_only=True))

        code_idx_p = 4
        url_idx_p = -1
        for idx, h in enumerate(rows_p[0]):
            h_str = str(h).lower() if h else ''
            if 'model code' in h_str or 'model_code' in h_str:
                code_idx_p = idx
            if 'url' in h_str or 'link' in h_str:
                url_idx_p = idx

        code_idx_t = 4
        for idx, h in enumerate(rows_t[0]):
            h_str = str(h).lower() if h else ''
            if 'model code' in h_str or 'model_code' in h_str:
                code_idx_t = idx

        models_t = set()
        for r in rows_t[1:]:
            if r and len(r) > code_idx_t and r[code_idx_t]:
                models_t.add(str(r[code_idx_t]).strip().upper())

        for r in rows_p[1:]:
            if r and len(r) > code_idx_p and r[code_idx_p]:
                m_code = str(r[code_idx_p]).strip().upper()
                if m_code not in models_t:
                    url = None
                    if url_idx_p >= 0 and len(r) > url_idx_p and r[url_idx_p]:
                        url = str(r[url_idx_p]).strip()
                    if not url:
                        m_entry = master_map.get((c_code, b_name, m_code))
                        if m_entry:
                            url = m_entry.get('url')
                    if url:
                        size_val = r[3] if len(r) > 3 and isinstance(r[3], (int, float)) else 55
                        candidates.append({
                            'sheet': s_name,
                            'country': c_code,
                            'brand': b_name,
                            'retailer': r_name,
                            'model_code': m_code,
                            'size': size_val,
                            'url': url,
                            'row_prev': list(r)
                        })

    print(f'Total 09.14 missing candidates identified with registered URLs: {len(candidates)}')

    probed_results = []
    # 1. Currys UK probes (Fast HTTP)
    currys_cands = [c for c in candidates if c['retailer'] == 'Currys']
    print(f'\n--- Probing Currys UK ({len(currys_cands)} models) ---')
    for item in currys_cands:
        res = probe_currys(item['url'])
        if res and res.get('in_stock'):
            item['probed_price'] = res['price']
            item['probed_orig_price'] = res['orig_price']
            item['currency'] = res['currency']
            probed_results.append(item)
            print(f" [VALID IN-STOCK] {item['model_code']} ({item['size']}\"): £{res['price']}")
        else:
            print(f" [OUT OF STOCK / DELISTED] {item['model_code']}")

    # 2. StealthySession for Public GR, Alza CZ, MediaMarkt CH
    stealth_cands = [c for c in candidates if c['retailer'] != 'Currys']
    print(f'\n--- Probing with StealthySession ({len(stealth_cands)} models across GR, CZ, CH) ---')
    with StealthySession(headless=True) as session:
        for idx, item in enumerate(stealth_cands, 1):
            r_name = item['retailer']
            m_code = item['model_code']
            size_val = item['size']
            url = item['url']
            brand = item['brand']
            
            res = None
            if r_name == 'Public':
                res = probe_public_gr(session, url, brand, size_val)
            elif r_name == 'Alza':
                res = probe_alza_cz(session, url, brand, size_val)
            elif r_name == 'MediaMarkt':
                res = probe_mediamarkt_ch(session, url, brand, size_val)

            if res and res.get('in_stock') and res.get('price', 0) > 0:
                item['probed_price'] = res['price']
                item['probed_orig_price'] = res['orig_price']
                item['currency'] = res['currency']
                probed_results.append(item)
                print(f" [{idx}/{len(stealth_cands)}] [VALID IN-STOCK] {r_name} - {m_code} ({size_val}\"): {res['price']} {res['currency']}")
            else:
                print(f" [{idx}/{len(stealth_cands)}] [OUT OF STOCK / DELISTED] {r_name} - {m_code}")

    print(f'\nTotal Valid In-Stock Live Probed Models: {len(probed_results)} / {len(candidates)}')
    with open(OUTPUT_PROBE_PATH, 'w', encoding='utf-8') as f:
        json.dump(probed_results, f, ensure_ascii=False, indent=2)
    print(f'Probed results saved to: {OUTPUT_PROBE_PATH}')

if __name__ == '__main__':
    main()
