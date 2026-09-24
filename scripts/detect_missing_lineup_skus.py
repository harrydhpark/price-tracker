import sys
sys.path.insert(0, '.')
import json
import re
import openpyxl
from scripts.generate_eu_dashboard import extract_products_from_sheet, find_sheet, find_product

wb = openpyxl.load_workbook('data/price tracker_EU_2026 0915_v1.xlsx', data_only=True)

with open('data/master_product_urls.json', 'r', encoding='utf-8') as f:
    master_registry = json.load(f)

retailer_configs = [
    {"country": "UK", "retailer": "Currys", "sheets": ["Currys_UK_SAMSUNG_Full", "Currys_UK_LG_Full"], "currency": "GBP", "domain": "currys.co.uk"},
    {"country": "DE", "retailer": "MediaMarkt", "sheets": ["MediaMarkt_DE_SAMSUNG_Full", "MediaMarkt_DE_LG_Full"], "currency": "EUR", "domain": "mediamarkt.de"},
    {"country": "FR", "retailer": "Fnac", "sheets": ["Fnac_FR_SAMSUNG_Full", "Fnac_FR_LG_Full"], "currency": "EUR", "domain": "fnac.com"},
    {"country": "ES", "retailer": "MediaMarkt", "sheets": ["MediaMarkt_ES_SAMSUNG_Full", "MediaMarkt_ES_LG_Full"], "currency": "EUR", "domain": "mediamarkt.es"},
    {"country": "IT", "retailer": "MediaWorld", "sheets": ["MediaWorld_IT_SAMSUNG_Full", "MediaWorld_IT_LG_Full"], "currency": "EUR", "domain": "mediaworld.it"},
    {"country": "NL", "retailer": "MediaMarkt", "sheets": ["MediaMarkt_NL_SAMSUNG_Full", "MediaMarkt_NL_LG_Full"], "currency": "EUR", "domain": "mediamarkt.nl"},
    {"country": "AT", "retailer": "MediaMarkt", "sheets": ["MediaMarkt_AT_SAMSUNG_Full", "MediaMarkt_AT_LG_Full"], "currency": "EUR", "domain": "mediamarkt.at"},
    {"country": "CH", "retailer": "MediaMarkt", "sheets": ["MediaMarkt_CH_SAMSUNG_Full", "MediaMarkt_CH_LG_Full"], "currency": "CHF", "domain": "mediamarkt.ch"},
    {"country": "CZ", "retailer": "Alza", "sheets": ["Alza_CZ_Samsung", "Alza_CZ_LG"], "currency": "CZK", "domain": "alza.cz"},
    {"country": "GR", "retailer": "Public", "sheets": ["Public_GR_Samsung", "Public_GR_LG"], "currency": "EUR", "domain": "public.gr"},
    {"country": "HU", "retailer": "MediaMarkt", "sheets": ["MediaMarkt_HU_Samsung", "MediaMarkt_HU_LG"], "currency": "HUF", "domain": "mediamarkt.hu"},
    {"country": "SE", "retailer": "Elgiganten", "sheets": ["Elgiganten_SE_Samsung", "Elgiganten_SE_LG"], "currency": "SEK", "domain": "elgiganten.se"},
    {"country": "PL", "retailer": "MediaExpert", "sheets": ["MediaExpert_PL_Samsung", "MediaExpert_PL_LG"], "currency": "PLN", "domain": "mediaexpert.pl"},
    {"country": "PT", "retailer": "Worten", "sheets": ["Worten_PT_Samsung", "Worten_PT_LG"], "currency": "EUR", "domain": "worten.pt"},
    {"country": "RO", "retailer": "Altex", "sheets": ["Altex_RO_Samsung", "Altex_RO_LG"], "currency": "RON", "domain": "altex.ro"}
]

TARGET_SERIES_CHECK = [
    # Category, Brand, Series Name, Sizes, Typical Model Code Patterns
    ("OLED", "LG", "G6", [83, 77, 65, 55, 48], ["OLED{sz}G6", "{sz}G6"]),
    ("OLED", "SAMSUNG", "S95H", [83, 77, 65, 55, 48], ["QE{sz}S95H", "TQ{sz}S95H", "GQ{sz}S95H", "{sz}S95H"]),
    ("OLED", "SAMSUNG", "S99H", [83, 77, 65, 55], ["QE{sz}S99H", "TQ{sz}S99H", "GQ{sz}S99H", "{sz}S99H"]),
    ("OLED", "LG", "C6", [83, 77, 65, 55, 48, 42], ["OLED{sz}C6", "{sz}C6"]),
    ("OLED", "SAMSUNG", "S90H", [83, 77, 65, 55, 48, 42], ["QE{sz}S90H", "TQ{sz}S90H", "GQ{sz}S90H", "QE{sz}S92H", "{sz}S90H"]),
    ("OLED", "LG", "B6", [83, 77, 65, 55, 48], ["OLED{sz}B6", "{sz}B6"]),
    ("OLED", "SAMSUNG", "S85H", [83, 77, 65, 55, 48], ["QE{sz}S85H", "TQ{sz}S85H", "GQ{sz}S85H", "{sz}S85H"]),

    ("MRGB", "LG", "MRGB96B", [100, 86, 75, 65], ["100MRGB96B", "{sz}MRGB96B", "{sz}MRGB95"]),
    ("MRGB", "SAMSUNG", "R95H", [100, 85, 75, 65], ["MRE{sz}R95H", "RE{sz}R95H", "{sz}R95H"]),
    ("MRGB", "LG", "MRGB87B", [86, 75, 65, 55, 50], ["{sz}MRGB87B", "{sz}MRGB88B", "{sz}MRGB86B", "{sz}MRGB85"]),
    ("MRGB", "SAMSUNG", "R85H", [85, 75, 65, 55, 50], ["MRE{sz}R85H", "MRE{sz}R86H", "RE{sz}R85H", "{sz}R85H"]),

    ("QNED/QLED", "LG", "QNED86B", [100, 86, 75, 65, 55, 50], ["100QNED87B", "{sz}QNED86B", "{sz}QNED87B"]),
    ("QNED/QLED", "SAMSUNG", "QN80H", [100, 85, 75, 65, 55, 50], ["QE{sz}QN80H", "TQ{sz}QN80H", "GQ{sz}QN80H", "{sz}QN80H"]),
    
    ("QNED/QLED", "LG", "QNED80B", [86, 75, 65, 55, 50, 43], ["{sz}QNED80B", "{sz}QNED81B", "{sz}QNED82B", "{sz}QNED83B"]),
    ("QNED/QLED", "SAMSUNG", "M80H", [85, 75, 65, 55, 50, 43], ["UE{sz}M80H", "TU{sz}M80H", "GU{sz}M80H", "UE{sz}M82H", "{sz}M80H"]),

    ("QNED/QLED", "LG", "QNED70B", [86, 75, 65, 55, 50, 43], ["{sz}QNED70B", "{sz}QNED71B", "{sz}QNED72B", "{sz}QNED7EB"]),
    ("QNED/QLED", "SAMSUNG", "M70H", [85, 75, 65, 55, 50, 43], ["UE{sz}M70H", "TU{sz}M70H", "GU{sz}M70H", "UE{sz}M72H", "UE{sz}M74H", "{sz}M70H"]),

    ("UHD 4K", "LG", "NU85", [85, 75, 65, 55, 50, 43], ["{sz}NU85", "{sz}NU800", "{sz}NU8E", "{sz}UA77"]),
    ("UHD 4K", "SAMSUNG", "U8000H", [85, 75, 65, 55, 50, 43], ["UE{sz}U8000H", "UE{sz}U8070H", "UE{sz}U8090H", "UE{sz}U8072H", "{sz}U8000H"])
]

def matches_target_model(cat, brand, series, sz, patterns, item):
    if item.get("brand") != brand or item.get("size") != sz or item.get("year") != 2026:
        return False
    mc = str(item.get("model_code", "")).upper()
    title = str(item.get("title", "")).upper()
    
    # OLED Guard
    if cat == "OLED":
        if "QNED" in mc or "QNED" in title or "NANOCELL" in title or "UHD" in title:
            return False
        if brand == "LG":
            if series == "B6" and not (re.search(r'\bOLED\w*B6', mc) or re.search(r'\bB6[0-9A-Z]', mc) or "B6" in title and "OLED" in title):
                return False
            if series == "C6" and not (re.search(r'\bOLED\w*C6', mc) or re.search(r'\bC6[0-9A-Z]', mc) or "C6" in title and "OLED" in title):
                return False
            if series == "G6" and not (re.search(r'\bOLED\w*G6', mc) or re.search(r'\bG6[0-9A-Z]', mc) or "G6" in title and "OLED" in title):
                return False
        elif brand == "SAMSUNG":
            if not ("S9" in mc or "S8" in mc or "OLED" in title):
                return False
    
    # QNED Guard
    if cat == "QNED/QLED":
        if brand == "LG" and ("OLED" in mc or "OLED" in title):
            return False
            
    # Series code matching
    for p in patterns:
        p_code = p.replace("{sz}", str(sz))
        if p_code in mc or p_code in title:
            return True
    if series in mc or series in title:
        return True
    return False

missing_search_tasks = []

for ret_info in retailer_configs:
    c = ret_info["country"]
    r_name = ret_info["retailer"]
    domain = ret_info["domain"]
    
    sam_sheet = find_sheet(wb, [ret_info["sheets"][0]])
    lg_sheet = find_sheet(wb, [ret_info["sheets"][1]])
    
    sam_prods = extract_products_from_sheet(sam_sheet) if sam_sheet else []
    lg_prods = extract_products_from_sheet(lg_sheet) if lg_sheet else []
    
    # Match registry for this retailer specifically
    master_for_ret = []
    for v in master_registry.values():
        if v.get("country") == c:
            v_ret = str(v.get("retailer", "")).lower()
            v_url = str(v.get("url", "")).lower()
            # retailer or domain match
            if domain in v_url or r_name.lower() in v_ret:
                master_for_ret.append(v)

    for cat, brand, series, sizes, patterns in TARGET_SERIES_CHECK:
        prods_to_check = lg_prods if brand == "LG" else sam_prods
        for sz in sizes:
            found_prod = find_product(prods_to_check, brand, sz, series, 2026)
            if not found_prod:
                # Check in master registry
                found_in_master = None
                for mv in master_for_ret:
                    if matches_target_model(cat, brand, series, sz, patterns, mv):
                        found_in_master = mv
                        break
                        
                missing_search_tasks.append({
                    "country": c,
                    "retailer": r_name,
                    "domain": domain,
                    "category": cat,
                    "brand": brand,
                    "series": series,
                    "size": sz,
                    "in_master": bool(found_in_master),
                    "master_url": found_in_master.get("url") if found_in_master else None,
                    "master_code": found_in_master.get("model_code") if found_in_master else None,
                    "search_queries": [f"{brand} {p.replace('{sz}', str(sz))}" for p in patterns[:2]] + [f"{brand} {sz} {series}"]
                })

print(f"Total missing targets found across 11 retailers: {len(missing_search_tasks)}")
in_master_cnt = sum(1 for t in missing_search_tasks if t["in_master"])
print(f"  - Already in Master Registry (ready to live-probe): {in_master_cnt}")
print(f"  - Need live retailer search: {len(missing_search_tasks) - in_master_cnt}")

import os
os.makedirs('scratch', exist_ok=True)
with open('scratch/missing_targets.json', 'w', encoding='utf-8') as f:
    json.dump(missing_search_tasks, f, indent=2, ensure_ascii=False)

print("Saved scratch/missing_targets.json with strict validation!")
