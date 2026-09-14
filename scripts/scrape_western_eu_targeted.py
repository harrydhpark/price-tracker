# -*- coding: utf-8 -*-
"""
Targeted Series Search & Inch-Expansion Scraper for Western Europe (Phase 1):
Countries:
- NL: MediaMarkt Netherlands (mediamarkt.nl)
- DE: MediaMarkt Germany (mediamarkt.de)
- ES: MediaMarkt Spain (mediamarkt.es)
- IT: MediaWorld Italy (mediaworld.it)
- FR: Fnac France (fnac.com)

Uses Firecrawl Stealth proxy API to execute targeted series searches,
recovering missing flagship OLED, MRGB, QNED/QLED, and UHD 4K models across all screen sizes.
Merges newly discovered products into data/raw_{retailer}_{brand}.json with lowest-price deduplication.
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
def _load_env_file():
    """Load key-value pairs from .env into os.environ if present."""
    env_path = os.path.join(ROOT_DIR, ".env")
    if os.path.isfile(env_path):
        try:
            with open(env_path, "r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip().lstrip("\ufeff")
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "").strip()
FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v1/scrape"

# ==============================================================================
# Non-TV & Purge Filters
# ==============================================================================
NON_TV_KEYWORDS = [
    "SOUNDBAR", "SOUND BAR", "BARRE DE SON", "BARRA DE SONIDO", "BUNDLE",
    "MONITOR", "MONITEUR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "REMOTE", "TELECOMANDO",
    "FERNBEDIENUNG", "TELECOMMANDE", "PROJECTOR", "PROJEKTOR", "PROJECTEUR", "PROIETTORE",
    "BEAMER", "CABLE", "SUPPORT", "HALTERUNG", "WANDHALTERUNG", "STAENDER", "STAND",
    "CASQUE", "HEADPHONE", "KOPFHÖRER", "CUFFIE", "AURICULARES", "EARBUDS",
    "FRIDGE", "FREEZER", "REFRIGERATOR", "KÜHLSCHRANK", "FRIGORIFERO", "FRIGORIFICO",
    "WASHING MACHINE", "WASCHMASCHINE", "LAVATRICE", "LAVADORA", "DRYER", "TROCKNER",
    "ASCIUGATRICE", "SECADORA", "DISHWASHER", "GESCHIRRSPÜLER", "LAVASTOVIGLIE", "LAVAVAJILLAS",
    "OVEN", "BACKOFEN", "FORNO", "HORNO", "MICROWAVE", "MIKROWELLE", "MICROONDE", "MICROONDAS",
    "HOOVER", "VACUUM", "STAUBSAUGER", "ASPIRAPOLVERE", "ASPIRADORA", "TABLET", "GALAXY PHONE",
    "SMARTPHONE", "HANDY", "CELLULARE", "WATCH", "SMARTWATCH", "ZUBEHÖR", "ACCESSOIRE", "ACCESSORIO",
    "ACCESORIO", "KLIMAANLAGE", "CONDIZIONATORE", "AIRE ACONDICIONADO", "CLIMATISEUR"
]

TV_INDICATORS = [
    " TV", "SMART TV", "TELEVISION", "TÉLÉVISEUR", "TELEVISORE", "TELEVISOR",
    "OLED", "QNED", "NEO QLED", "THE FRAME", "THE SERIF", "STANBYME", "MINI LED", "4K", "UHD"
]

# ==============================================================================
# Price & Screen Size Guards
# ==============================================================================
def clean_numeric_price(val):
    if not val:
        return 0.0
    p = str(val).replace('€', '').replace('£', '').replace('CHF', '').replace('\xa0', '').replace('\u202f', ' ').strip()
    if re.match(r'^\d{1,3}\.\d{3}(?:,\d{2})?$', p):
        p = p.replace('.', '').replace(',', '.')
    elif re.match(r'^\d{1,3},\d{3}(?:\.\d{2})?$', p):
        p = p.replace(',', '')
    elif ',' in p:
        p = p.replace(',', '.')
    m = re.findall(r'(\d+(?:\.\d{2})?)', p)
    if m:
        try:
            v = float(m[0])
            return v if v >= 50.0 else 0.0
        except ValueError:
            pass
    return 0.0

def passes_price_guard(disp, size, price):
    if price < 80.0:
        return False
    d = disp.upper()
    # OLED
    if "OLED" in d:
        if size <= 48 and price < 500.0:
            return False
        if size == 55 and price < 700.0:
            return False
        if size == 65 and price < 950.0:
            return False
        if size >= 77 and price < 1400.0:
            return False
        if size >= 83 and price < 2000.0:
            return False
    # Micro RGB
    elif "MICRO RGB" in d or "MRGB" in d:
        if size <= 65 and price < 600.0:
            return False
        if size >= 75 and price < 1500.0:
            return False
        if size >= 98 and price < 8000.0:
            return False
    # QNED / QLED / Neo QLED
    elif any(x in d for x in ["QNED", "QLED", "NEO QLED", "MINI LED"]):
        if size <= 43 and price < 200.0:
            return False
        if size in [50, 55] and price < 280.0:
            return False
        if size >= 65 and price < 450.0:
            return False
        if size >= 75 and price < 700.0:
            return False
    # UHD 4K
    elif "UHD" in d or "LED" in d or "4K" in d:
        if size <= 43 and price < 120.0:
            return False
        if size >= 55 and price < 180.0:
            return False
    return True

# ==============================================================================
# Smart Parser for MediaMarkt / MediaWorld Markdown Dumps
# ==============================================================================
def parse_mediamarkt_markdown(md_text, brand):
    items = []
    # Pattern matching markdown links with products:
    # [**LG Evo AI 55C67LA - Ultra HD 4K - OLED-tv - 55 inch - 2026**](https://www.mediamarkt.nl/nl/product/...)
    pattern = re.compile(
        r'\[\*\*([^\*\]]+)\*\*\]\((https?://www\.(?:mediamarkt|mediaworld)\.[a-z]{2}/[^\)]+/product/[^\)]+)\)(.*?)(?=\[\*\*|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    
    for m in pattern.finditer(md_text):
        title = m.group(1).strip()
        url = m.group(2).strip()
        chunk = m.group(3)
        u_title = title.upper()
        
        # 1. Check brand
        if brand.upper() not in u_title and not any(k in u_title for k in ['OLED', 'QNED', 'S90', 'S95', 'C6', 'G6', 'B6']):
            continue
            
        # 2. Non-TV purge
        if any(x in u_title for x in NON_TV_KEYWORDS):
            continue
            
        # 3. Price extraction
        price = 0.0
        # MediaMarkt formats: € 1899,–€1899,00 or € 1.899,- or 1.899,00 € or € 999.00
        p_matches = re.findall(r'(?:€|EUR)\s*([\d\.\s]+(?:,\d{2}|,–|-)?)|([\d\.\s]+(?:,\d{2}|,–|-)?)\s*(?:€|EUR)', chunk)
        for pm in p_matches:
            raw_p = (pm[0] or pm[1]).strip().replace(' ', '').replace('–', '').replace('-', '')
            if ',' in raw_p and '.' in raw_p:
                raw_p = raw_p.replace('.', '').replace(',', '.')
            elif '.' in raw_p and len(raw_p.split('.')[-1]) == 3:
                raw_p = raw_p.replace('.', '')
            elif ',' in raw_p:
                raw_p = raw_p.replace(',', '.')
            try:
                val = float(raw_p)
                if val >= 80.0:
                    price = val
                    break
            except ValueError:
                continue
                
        if price < 80.0:
            continue
            
        # 4. Cashback extraction
        cashback = 0
        cb_m = re.search(r'(?:€|EUR)\s*(\d+)[\s,-]*(?:cashback|terug|reembolso|rimborso|rabatt)', chunk, re.I)
        if not cb_m:
            cb_m = re.search(r'(\d+)[\s,-]*(?:€|EUR)?\s*(?:cashback|terug|reembolso|rimborso)', chunk, re.I)
        if cb_m:
            cashback = int(cb_m.group(1))
            
        promo = f"€{cashback} Cashback" if cashback > 0 else "None"
        
        # 5. Extract Size, Model Code, Year, Display Type
        rec = build_clean_record(brand, title, url, price, cashback, promo)
        if rec:
            items.append(rec)
            
    return items

# ==============================================================================
# Smart Parser for Fnac Markdown Dumps
# ==============================================================================
def parse_fnac_markdown(md_text, brand):
    items = []
    # Pattern matching Fnac product links:
    # [TV LG 4K OLED Evo OLED55C6 139 cm 2026](https://www.fnac.com/TV-LG-4K-OLED-Evo-OLED55C6-139-cm-2026/a23005754/w-4)
    pattern = re.compile(
        r'\[(?:\*\*)?([^\]\*\n]+)(?:\*\*)?\]\((https?://(?:www\.)?fnac\.com/[^\)]+/a\d+/[^\)]*)\)(.*?)(?=\n\[|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    
    for m in pattern.finditer(md_text):
        title = m.group(1).strip()
        url = m.group(2).strip()
        chunk = m.group(3)
        u_title = title.upper()
        
        if brand.upper() not in u_title and not any(k in u_title for k in ['OLED', 'QNED', 'S90', 'S95', 'C6', 'G6', 'B6']):
            continue
            
        if any(x in u_title for x in NON_TV_KEYWORDS):
            continue
            
        # Price extraction (handling \u202f narrow no-break space)
        t_chunk = chunk.replace('\u202f', ' ').replace('\xa0', ' ').replace('\u2009', ' ')
        t_chunk = re.sub(r'\b\d+\s*€\s*(?:de\s*remise|d\'économie|de\s*réduction|remise|réduction)\b', '', t_chunk, flags=re.IGNORECASE)
        t_chunk = re.sub(r'dès\s*[\d\s,.]+\s*€\s*\/\s*mois', '', t_chunk, flags=re.IGNORECASE)
        
        p_matches = re.findall(r'(\d+[\d\s]*[,\.]\d{2}|\d+[\d\s]*)\s*€', t_chunk)
        price = 0.0
        for raw in p_matches:
            cleaned = raw.strip().replace(' ', '').replace(',', '.')
            try:
                v = float(cleaned)
                if v >= 80.0:
                    price = v
                    break
            except ValueError:
                continue
                
        if price < 80.0:
            continue
            
        rec = build_clean_record(brand, title, url, price, 0, "None")
        if rec:
            items.append(rec)
            
    return items

# ==============================================================================
# Universal Product Clean Record Builder
# ==============================================================================
def build_clean_record(brand, title, url, price, cashback, promo):
    u_title = title.upper()
    
    # 1. Screen Size
    size = 0
    # Inch pattern
    m_inch = re.search(r'\b(98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:INCH|ZOLL|POUCES|POLLICI|\"|\b)', u_title)
    if m_inch:
        size = int(m_inch.group(1))
    if not size:
        m_cm = re.search(r'\b(\d{2,3})\s*CM\b', u_title)
        if m_cm:
            cm_val = int(m_cm.group(1))
            if cm_val > 100:
                size = int(round(cm_val / 2.54))
            elif cm_val >= 22:
                size = cm_val
                
    # 2. Model Code
    model_code = "Unknown"
    if brand.upper() == "LG":
        # LG OLED (OLEDxxC6, xxC6, OLEDxxG6, xxG6, OLEDxxB6, xxB6)
        m_oled = re.search(r'\b(OLED\d{2,3}[A-Z]{1,3}\d{0,2}[A-Z]*|\d{2}[CGB][56]\w*)\b', u_title)
        if m_oled:
            model_code = m_oled.group(1)
        else:
            m_lg = re.search(r'\b(\d{2,3}(?:QNED|NANO|MRGB|LX|NU|UA|UT|UR|UQ|LB|QLED)\w*)\b', u_title)
            if m_lg:
                model_code = m_lg.group(1)
        # Smart fallback for series
        if model_code == "Unknown":
            for w in u_title.split():
                cw = re.sub(r'[^\w-]', '', w)
                if any(char.isdigit() for char in cw) and len(cw) >= 5 and not any(j in cw for j in ["TV", "OLEDLG", "LEDLG"]):
                    model_code = cw
                    break
    else: # Samsung
        for w in u_title.split():
            cw = re.sub(r'[^\w-]', '', w)
            if any(cw.startswith(p) for p in ["GQ", "TQ", "QE", "UE", "GU", "MRE"]):
                model_code = cw
                break
        if model_code == "Unknown":
            patterns = [
                r'\b(QN\d{2,3}[FH])\b', r'\b(S\d{2,3}[FH])\b', r'\b(U\d{3,4}[FH])\b',
                r'\b(M\d{2,3}[FH])\b', r'\b(R\d{2,3}[FH])\b', r'\b(LS03[A-Z]{1,2})\b',
                r'\b(MR\d{2,3}[FH])\b'
            ]
            for pat in patterns:
                m_pat = re.search(pat, u_title)
                if m_pat:
                    ser = m_pat.group(1)
                    if ser.startswith('S') or ser.startswith('QN') or ser.startswith('LS'):
                        model_code = f"QE{size or 55}{ser}"
                    elif ser.startswith('U') or ser.startswith('M'):
                        model_code = f"UE{size or 55}{ser}"
                    elif ser.startswith('R') or ser.startswith('MR'):
                        model_code = f"MRE{size or 55}{ser}"
                    break
                    
    # Re-verify size from model code if explicit
    if model_code != "Unknown":
        c_nums = re.findall(r'\d+', model_code)
        if c_nums and len(c_nums[0]) in [2, 3]:
            parsed_sz = int(c_nums[0])
            if parsed_sz in [100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27]:
                size = parsed_sz
                
    if not size:
        size = 55
    if size < 22:
        return None
        
    # 3. Model Year Classification (Strict 2025/2026 only)
    year = None
    if brand.upper() == "SAMSUNG":
        if re.search(r'[A-Z0-9]{2}\d{2}[A-Z0-9]*D\b', model_code) or any(x in model_code for x in ["S90D", "S95D", "QN90D", "Q60D", "Q70D", "Q80D", "DU7", "DU8"]):
            return None # Reject 2024
        if len(model_code) > 3 and "H" in model_code[2:]:
            year = 2026
        elif len(model_code) > 3 and "F" in model_code[2:]:
            year = 2025
        elif "2026" in u_title:
            year = 2026
        elif "2025" in u_title:
            year = 2025
    elif brand.upper() == "LG":
        if any(x in model_code for x in ["C4", "G4", "B4", "M4", "UA73", "UT8", "LQ6"]):
            return None # Reject 2024
        if any(x in model_code for x in ["C6", "G6", "B6", "W6", "M6", "QNED86B", "QNED81B", "QNED80B", "QNED87B", "QNED72B", "QNED71B", "QNED70B", "MRGB87B", "MRGB96B", "27LX6", "NU850", "NU85", "NU800", "NU80"]):
            year = 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "W5", "M5", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED70A", "NANO81A", "QNED93A", "QNED84A", "UA75"]):
            year = 2025
        elif "2026" in u_title:
            year = 2026
        elif "2025" in u_title:
            year = 2025
            
    if year not in [2025, 2026]:
        return None
        
    # 4. Display Type
    display_type = "LED"
    c_up = model_code.upper()
    if brand.upper() == "SAMSUNG":
        if "OLED" in c_up or any(x in c_up for x in ["S90", "S91", "S92", "S93", "S94", "S95", "S99", "S85"]):
            display_type = "OLED"
        elif "MRE" in c_up or "MRGB" in c_up:
            display_type = "Micro RGB"
        elif "QN" in c_up:
            display_type = "Neo QLED"
        elif any(x in c_up for x in ["M70", "M72", "M74", "M80", "M82", "M84"]) or "MINI LED" in u_title:
            display_type = "Mini LED"
        elif "Q" in c_up or "LS" in c_up:
            display_type = "QLED"
        elif any(x in c_up for x in ["U8", "UA", "UT", "UR", "UQ"]):
            display_type = "UHD 4K"
    elif brand.upper() == "LG":
        if "MRGB" in c_up or "MRGB" in u_title:
            display_type = "Micro RGB"
        elif "QNED" in c_up or "QNED" in u_title:
            display_type = "QNED"
        elif "OLED" in c_up or "OLED" in u_title or re.search(r'\d{2}[CGB][56]', c_up):
            display_type = "OLED evo" if ("EVO" in u_title or any(x in c_up for x in ["G5", "G6", "C5", "C6"])) else "OLED"
        elif "NANO" in c_up:
            display_type = "NanoCell"
        elif any(x in c_up for x in ["NU90", "NU85", "NU80", "NU800", "NU850", "UA75", "UA77"]):
            display_type = "UHD 4K"
        elif "LX" in c_up or "STANBYME" in c_up:
            display_type = "Lifestyle"
            
    # 5. Price Guard Verification
    if not passes_price_guard(display_type, size, price):
        return None
        
    return {
        "brand": "Samsung" if brand.upper() == "SAMSUNG" else "LG",
        "year": year,
        "display": display_type,
        "display_type": display_type,
        "size": size,
        "model_code": model_code,
        "price": price,
        "shipping": "Free",
        "cashback": cashback,
        "promo": promo,
        "title": title,
        "url": url,
        "link": url
    }

# ==============================================================================
# Targeted Scraper Executor
# ==============================================================================
def fetch_firecrawl_url(target_info):
    cc, retailer, brand, query, url = target_info
    if not FIRECRAWL_API_KEY:
        print(f"    [AUTH ERROR] FIRECRAWL_API_KEY is not set in .env or environment. Skipping {cc} {query}...", flush=True)
        return cc, retailer, brand, query, [], 401
    headers = {'Authorization': f'Bearer {FIRECRAWL_API_KEY}'}
    payload = {'url': url, 'formats': ['markdown'], 'proxy': 'stealth'}
    
    for attempt in range(4):
        try:
            r = requests.post(FIRECRAWL_ENDPOINT, json=payload, headers=headers, timeout=50)
            if r.status_code == 200:
                data = r.json()
                md = data.get('data', {}).get('markdown', '')
                if retailer == "Fnac":
                    items = parse_fnac_markdown(md, brand)
                else:
                    items = parse_mediamarkt_markdown(md, brand)
                return cc, retailer, brand, query, items, r.status_code
            elif r.status_code == 429:
                err = r.json().get('error', '')
                m_sec = re.search(r'retry after (\d+)s', err)
                wait_sec = int(m_sec.group(1)) + 2 if m_sec else 12
                print(f"    [RATE LIMIT] Quota hit for {cc} {query}, waiting {wait_sec}s...", flush=True)
                time.sleep(wait_sec)
            else:
                time.sleep(2.0)
        except Exception as e:
            time.sleep(2.0)
    return cc, retailer, brand, query, [], 0

def run_targeted_western_eu():
    print("================================================================================")
    print(" 🇪🇺 STARTING PHASE 1: WESTERN EU TARGETED SERIES SEARCH & INCH-EXPANSION ")
    print(" Core Countries: NL (MediaMarkt), DE (MediaMarkt), ES (MediaMarkt), IT (MediaWorld), FR (Fnac)")
    print("================================================================================")
    
    # Streamlined 60-query high-yield matrix (12 queries per country)
    TARGET_MATRIX = [
        # 1. Netherlands (MediaMarkt NL)
        ("NL", "MediaMarkt", "Samsung", "OLED", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+OLED"),
        ("NL", "MediaMarkt", "Samsung", "Neo QLED", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+Neo+QLED"),
        ("NL", "MediaMarkt", "Samsung", "Mini LED", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+Mini+LED"),
        ("NL", "MediaMarkt", "Samsung", "U80", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+U80"),
        ("NL", "MediaMarkt", "Samsung", "Micro RGB", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+Micro+RGB"),
        ("NL", "MediaMarkt", "Samsung", "2026", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+2026"),
        ("NL", "MediaMarkt", "LG", "OLED", "https://www.mediamarkt.nl/nl/search.html?query=LG+OLED"),
        ("NL", "MediaMarkt", "LG", "C6", "https://www.mediamarkt.nl/nl/search.html?query=LG+C6"),
        ("NL", "MediaMarkt", "LG", "QNED", "https://www.mediamarkt.nl/nl/search.html?query=LG+QNED"),
        ("NL", "MediaMarkt", "LG", "NU8", "https://www.mediamarkt.nl/nl/search.html?query=LG+NU8"),
        ("NL", "MediaMarkt", "LG", "MRGB", "https://www.mediamarkt.nl/nl/search.html?query=LG+MRGB"),
        ("NL", "MediaMarkt", "LG", "2026", "https://www.mediamarkt.nl/nl/search.html?query=LG+2026"),
        
        # 2. Germany (MediaMarkt DE)
        ("DE", "MediaMarkt", "Samsung", "OLED", "https://www.mediamarkt.de/de/search.html?query=Samsung+OLED"),
        ("DE", "MediaMarkt", "Samsung", "Neo QLED", "https://www.mediamarkt.de/de/search.html?query=Samsung+Neo+QLED"),
        ("DE", "MediaMarkt", "Samsung", "Mini LED", "https://www.mediamarkt.de/de/search.html?query=Samsung+Mini+LED"),
        ("DE", "MediaMarkt", "Samsung", "U80", "https://www.mediamarkt.de/de/search.html?query=Samsung+U80"),
        ("DE", "MediaMarkt", "Samsung", "Micro RGB", "https://www.mediamarkt.de/de/search.html?query=Samsung+Micro+RGB"),
        ("DE", "MediaMarkt", "Samsung", "2026", "https://www.mediamarkt.de/de/search.html?query=Samsung+2026"),
        ("DE", "MediaMarkt", "LG", "OLED", "https://www.mediamarkt.de/de/search.html?query=LG+OLED"),
        ("DE", "MediaMarkt", "LG", "C6", "https://www.mediamarkt.de/de/search.html?query=LG+C6"),
        ("DE", "MediaMarkt", "LG", "QNED", "https://www.mediamarkt.de/de/search.html?query=LG+QNED"),
        ("DE", "MediaMarkt", "LG", "NU800", "https://www.mediamarkt.de/de/search.html?query=LG+NU800"),
        ("DE", "MediaMarkt", "LG", "MRGB", "https://www.mediamarkt.de/de/search.html?query=LG+MRGB"),
        ("DE", "MediaMarkt", "LG", "2026", "https://www.mediamarkt.de/de/search.html?query=LG+2026"),
        
        # 3. Spain (MediaMarkt ES)
        ("ES", "MediaMarkt", "Samsung", "OLED", "https://www.mediamarkt.es/es/search.html?query=Samsung+OLED"),
        ("ES", "MediaMarkt", "Samsung", "Neo QLED", "https://www.mediamarkt.es/es/search.html?query=Samsung+Neo+QLED"),
        ("ES", "MediaMarkt", "Samsung", "Mini LED", "https://www.mediamarkt.es/es/search.html?query=Samsung+Mini+LED"),
        ("ES", "MediaMarkt", "Samsung", "U80", "https://www.mediamarkt.es/es/search.html?query=Samsung+U80"),
        ("ES", "MediaMarkt", "Samsung", "Micro RGB", "https://www.mediamarkt.es/es/search.html?query=Samsung+Micro+RGB"),
        ("ES", "MediaMarkt", "Samsung", "2026", "https://www.mediamarkt.es/es/search.html?query=Samsung+2026"),
        ("ES", "MediaMarkt", "LG", "OLED", "https://www.mediamarkt.es/es/search.html?query=LG+OLED"),
        ("ES", "MediaMarkt", "LG", "C6", "https://www.mediamarkt.es/es/search.html?query=LG+C6"),
        ("ES", "MediaMarkt", "LG", "QNED", "https://www.mediamarkt.es/es/search.html?query=LG+QNED"),
        ("ES", "MediaMarkt", "LG", "NU8", "https://www.mediamarkt.es/es/search.html?query=LG+NU8"),
        ("ES", "MediaMarkt", "LG", "MRGB", "https://www.mediamarkt.es/es/search.html?query=LG+MRGB"),
        ("ES", "MediaMarkt", "LG", "2026", "https://www.mediamarkt.es/es/search.html?query=LG+2026"),
        
        # 4. Italy (MediaWorld IT)
        ("IT", "MediaWorld", "Samsung", "OLED", "https://www.mediaworld.it/it/search.html?query=Samsung+OLED"),
        ("IT", "MediaWorld", "Samsung", "Neo QLED", "https://www.mediaworld.it/it/search.html?query=Samsung+Neo+QLED"),
        ("IT", "MediaWorld", "Samsung", "Mini LED", "https://www.mediaworld.it/it/search.html?query=Samsung+Mini+LED"),
        ("IT", "MediaWorld", "Samsung", "U80", "https://www.mediaworld.it/it/search.html?query=Samsung+U80"),
        ("IT", "MediaWorld", "Samsung", "Micro RGB", "https://www.mediamarkt.it/it/search.html?query=Samsung+Micro+RGB" if False else "https://www.mediaworld.it/it/search.html?query=Samsung+Micro+RGB"),
        ("IT", "MediaWorld", "Samsung", "2026", "https://www.mediaworld.it/it/search.html?query=Samsung+2026"),
        ("IT", "MediaWorld", "LG", "OLED", "https://www.mediaworld.it/it/search.html?query=LG+OLED"),
        ("IT", "MediaWorld", "LG", "C6", "https://www.mediaworld.it/it/search.html?query=LG+C6"),
        ("IT", "MediaWorld", "LG", "QNED", "https://www.mediaworld.it/it/search.html?query=LG+QNED"),
        ("IT", "MediaWorld", "LG", "NU8", "https://www.mediaworld.it/it/search.html?query=LG+NU8"),
        ("IT", "MediaWorld", "LG", "MRGB", "https://www.mediaworld.it/it/search.html?query=LG+MRGB"),
        ("IT", "MediaWorld", "LG", "2026", "https://www.mediaworld.it/it/search.html?query=LG+2026"),
        
        # 5. France (Fnac FR)
        ("FR", "Fnac", "Samsung", "OLED", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+samsung+oled"),
        ("FR", "Fnac", "Samsung", "Neo QLED", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+samsung+neo+qled"),
        ("FR", "Fnac", "Samsung", "Mini LED", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+samsung+mini+led"),
        ("FR", "Fnac", "Samsung", "U80", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+samsung+u80"),
        ("FR", "Fnac", "Samsung", "The Frame", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+samsung+the+frame"),
        ("FR", "Fnac", "Samsung", "2026", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+samsung+2026"),
        ("FR", "Fnac", "LG", "OLED", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+lg+oled"),
        ("FR", "Fnac", "LG", "C6", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=LG+C6"),
        ("FR", "Fnac", "LG", "QNED", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+lg+qned"),
        ("FR", "Fnac", "LG", "NU85", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+lg+nu85"),
        ("FR", "Fnac", "LG", "MRGB", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+lg+micro+rgb"),
        ("FR", "Fnac", "LG", "2026", "https://www.fnac.com/SearchResult/ResultList.aspx?Search=tv+lg+2026")
    ]
    
    print(f"Total targeted queries to execute: {len(TARGET_MATRIX)}")
    
    # Store results grouped by (country, brand)
    gathered = {}
    
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for item in TARGET_MATRIX:
            futures.append(executor.submit(fetch_firecrawl_url, item))
            time.sleep(0.5) # Polite stagger to stay under 36 req/min limit
            
        for f in futures:
            cc, retailer, brand, query, items, status_code = f.result()
            key = (cc, brand)
            if key not in gathered:
                gathered[key] = []
            gathered[key].extend(items)
            print(f"  [{cc} - {retailer} - {brand.upper()}] Query: {query:<10} (HTTP {status_code}) -> Found {len(items)} matching products.", flush=True)
            
    print(f"\n✅ All targeted queries completed in {time.time() - t0:.1f}s.", flush=True)
    
    # Now merge into raw files
    file_map = {
        ("NL", "Samsung"): "raw_mm-nl_samsung.json",
        ("NL", "LG"): "raw_mm-nl_lg.json",
        ("DE", "Samsung"): "raw_mm-de_samsung.json",
        ("DE", "LG"): "raw_mm-de_lg.json",
        ("ES", "Samsung"): "raw_mm-es_samsung.json",
        ("ES", "LG"): "raw_mm-es_lg.json",
        ("IT", "Samsung"): "raw_mw-it_samsung.json",
        ("IT", "LG"): "raw_mw-it_lg.json",
        ("FR", "Samsung"): "raw_fnac_samsung.json",
        ("FR", "LG"): "raw_fnac_lg.json"
    }
    
    print("\n--- Merging Discovered Models with Lowest-Price Deduplication ---")
    for (cc, brand), fname in file_map.items():
        fpath = os.path.join(DATA_DIR, fname)
        existing = []
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                try:
                    existing = json.load(f)
                except Exception:
                    existing = []
                    
        # Key by model_code (or title fallback)
        model_dict = {}
        for item in existing:
            mc = item.get("model_code", "Unknown")
            if mc != "Unknown":
                model_dict[mc] = item
            else:
                model_dict[item.get("title", "")] = item
                
        before_count = len(model_dict)
        new_items = gathered.get((cc, brand), [])
        added_count = 0
        updated_price_count = 0
        
        for item in new_items:
            mc = item["model_code"]
            if mc != "Unknown":
                if mc not in model_dict:
                    model_dict[mc] = item
                    added_count += 1
                else:
                    # Update if new price is lower
                    if item["price"] < model_dict[mc].get("price", float("inf")):
                        model_dict[mc] = item
                        updated_price_count += 1
            else:
                t = item["title"]
                if t not in model_dict:
                    model_dict[t] = item
                    added_count += 1
                    
        final_list = list(model_dict.values())
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(final_list, f, ensure_ascii=False, indent=2)
            
        print(f"  • {fname:<25}: Before={before_count:>2} | Added={added_count:>2} new | Price Updated={updated_price_count:>2} | Total={len(final_list):>2}")

    print("\n================================================================================")
    print(" 🎉 PHASE 1 RAW DATA EXPANSION COMPLETE! READY FOR EXCEL & DASHBOARD SYNC ")
    print("================================================================================")

if __name__ == "__main__":
    run_targeted_western_eu()
