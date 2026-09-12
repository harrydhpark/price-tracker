import os, sys, json, re, time
from curl_cffi import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrape_currys_live import parse_currys_tile, passes_uk_price_guard

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")

TARGET_SERIES_SAMSUNG = [
    'S99H', 'S95H', 'S90H', 'S85H', 'R95H', 'R85H', 
    'QN80H', 'QN70H', 'M90H', 'M80H', 'M70H', 'U8000H', 'U9000H',
    'QN90F', 'S95F', 'S90F', 'S85F', 'QN80F', 'QN70F', 'Q8F', 'Q7F', 'U8000F'
]

TARGET_SERIES_LG = [
    'G6', 'C6', 'B6', 'W6', 'MRGB96', 'MRGB88', 
    'QNED93', 'QNED87', 'QNED86', 'QNED83', 'QNED72', 'NU90', 'NU85', 'NU80',
    'G5', 'C5', 'B5', 'QNED86A', 'QNED80A', 'QNED72A', 'UA75', 'LX7'
]

NON_TV_KEYWORDS = [
    "SOUNDBAR", "SOUND BAR", "BUNDLE", "MONITOR", "ODYSSEY", "ULTRAGEAR", 
    "REMOTE", "PROJECTOR", "BEAMER", "CABLE", "REFURBISHED", "FRIDGE", 
    "FREEZER", "REFRIGERATOR", "WASHING MACHINE", "DRYER", "DISHWASHER", 
    "OVEN", "MICROWAVE", "HOOVER", "VACUUM", "TABLET", "GALAXY", "PHONE", 
    "WATCH", "HEADPHONE", "EARBUDS"
]

TV_INDICATORS = [
    " TV", "SMART TV", "TELEVISION", "OLED", "QNED", "NEO QLED", 
    "THE FRAME", "THE SERIF", "STANBYME", "MINI LED"
]

def clean_currys_tile(tile, brand):
    rec = parse_currys_tile(tile, brand)
    if not rec:
        return None
        
    u_title = rec.get("title", "").upper()
    
    # 1. Non-TV purge
    if any(k in u_title for k in NON_TV_KEYWORDS):
        return None
        
    # 2. Must be a TV
    if not any(k in u_title for k in TV_INDICATORS):
        return None
        
    # 3. Model code must not look like an appliance
    mc = rec.get("model_code", "").upper()
    if any(mc.startswith(p) for p in ["RS", "RB", "WW", "DV", "DW", "NV", "NK"]):
        return None
        
    # 4. UK price guard
    if not passes_uk_price_guard(rec['display'], rec['size'], rec['price']):
        return None
        
    return rec

def fetch_search_query(brand, series):
    items = []
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    }
    
    for start in [0, 20]:
        query = f"{brand} {series} TV"
        url = f"https://www.currys.co.uk/search?q={query.replace(' ', '+')}&start={start}&sz=20"
        success = False
        
        for attempt in range(3):
            try:
                r = requests.get(url, impersonate="chrome124", headers=headers, timeout=20)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    tiles = soup.find_all('div', class_=lambda c: c and 'product-tile' in c and 'pt-md-0' in c)
                    if not tiles:
                        tiles = soup.find_all('div', class_=lambda c: c and 'product-tile' in c)
                    
                    for t in tiles:
                        rec = clean_currys_tile(t, brand)
                        if rec:
                            items.append(rec)
                    success = True
                    break
                elif r.status_code == 403:
                    time.sleep(3.0 * (attempt + 1))
                else:
                    break
            except Exception as e:
                time.sleep(2.0)
                
        if not success or len(items) == 0:
            break
            
        time.sleep(1.8) # Polite delay
        
    return items

def run_targeted_currys_scrape():
    print("==================================================")
    print(" 🇬🇧 STARTING CURRYS UK TARGETED SERIES PROBE ")
    print("==================================================")
    
    s_file = os.path.join(DATA_DIR, "raw_currys_samsung.json")
    l_file = os.path.join(DATA_DIR, "raw_currys_lg.json")
    
    s_existing = []
    if os.path.exists(s_file):
        with open(s_file, "r", encoding="utf-8") as f:
            s_existing = json.load(f)
            
    l_existing = []
    if os.path.exists(l_file):
        with open(l_file, "r", encoding="utf-8") as f:
            l_existing = json.load(f)
            
    # Purge any non-TV from existing lists first
    s_dict = {}
    for item in s_existing:
        mc = item.get("model_code", "")
        u_title = item.get("title", "").upper()
        if mc and not any(k in u_title for k in NON_TV_KEYWORDS) and not any(mc.startswith(p) for p in ["RS", "RB", "WW", "DV", "DW"]):
            s_dict[mc] = item
            
    l_dict = {}
    for item in l_existing:
        mc = item.get("model_code", "")
        u_title = item.get("title", "").upper()
        if mc and not any(k in u_title for k in NON_TV_KEYWORDS):
            l_dict[mc] = item
    
    initial_s_count = len(s_dict)
    initial_l_count = len(l_dict)
    print(f"Initial clean existing models: Samsung={initial_s_count}, LG={initial_l_count}")
    
    # 1. Probe Samsung Series
    print("\n--- Probing Samsung Target Series ---")
    s_new_found = 0
    for series in TARGET_SERIES_SAMSUNG:
        print(f"  Searching Samsung {series} TV...", end=" ", flush=True)
        items = fetch_search_query("Samsung", series)
        added_for_series = 0
        for rec in items:
            mc = rec["model_code"]
            if mc not in s_dict:
                s_dict[mc] = rec
                s_new_found += 1
                added_for_series += 1
                print(f"\n    ★ NEW: {rec['size']}\" {mc} - £{rec['price']}", end="", flush=True)
            elif rec["price"] < s_dict[mc]["price"]:
                s_dict[mc] = rec
        print(f" -> Found {len(items)} items (+{added_for_series} new)")
        time.sleep(1.5)
        
    # 2. Probe LG Series
    print("\n--- Probing LG Target Series ---")
    l_new_found = 0
    for series in TARGET_SERIES_LG:
        print(f"  Searching LG {series} TV...", end=" ", flush=True)
        items = fetch_search_query("LG", series)
        added_for_series = 0
        for rec in items:
            mc = rec["model_code"]
            if mc not in l_dict:
                l_dict[mc] = rec
                l_new_found += 1
                added_for_series += 1
                print(f"\n    ★ NEW: {rec['size']}\" {mc} - £{rec['price']}", end="", flush=True)
            elif rec["price"] < l_dict[mc]["price"]:
                l_dict[mc] = rec
        print(f" -> Found {len(items)} items (+{added_for_series} new)")
        time.sleep(1.5)
        
    final_sams = list(s_dict.values())
    final_lgs = list(l_dict.values())
    
    # Save back to raw JSON files
    with open(s_file, "w", encoding="utf-8") as f:
        json.dump(final_sams, f, ensure_ascii=False, indent=2)
    with open(l_file, "w", encoding="utf-8") as f:
        json.dump(final_lgs, f, ensure_ascii=False, indent=2)
        
    print("\n==================================================")
    print(f" [PROBE SUMMARY] Samsung: {initial_s_count} -> {len(final_sams)} (+{s_new_found} newly recovered)")
    print(f" [PROBE SUMMARY] LG:      {initial_l_count} -> {len(final_lgs)} (+{l_new_found} newly recovered)")
    print("==================================================")

if __name__ == "__main__":
    run_targeted_currys_scrape()
