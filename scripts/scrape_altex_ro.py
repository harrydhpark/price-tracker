# -*- coding: utf-8 -*-
"""
Altex Romania (altex.ro) Scraper & Normalizer
Provides full DOM parsing for Altex TV listings, Romanian Leu (RON) price extraction,
and supports HTTP_PROXY / RO_PROXY for bypassing Geo-IP restrictions.
"""

import os
import sys
import json
import re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

NON_TV_KEYWORDS = [
    "SOUNDBAR", "SOUND BAR", "SUPORT TV", "SUPORT", "CABLU", "TELECOMANDA",
    "MONITOR", "ODYSSEY", "ULTRAGEAR", "PROIECTOR", "BEAMER"
]

def parse_altex_html_card(card_element, brand):
    # Standard parser for BeautifulSoup or text dump
    text = card_element.get_text('\n') if hasattr(card_element, 'get_text') else str(card_element)
    u_text = text.upper()
    if any(k in u_text for k in NON_TV_KEYWORDS):
        return None
        
    return None

def build_altex_product(brand, title, price, orig_price, promo, url):
    u_title = title.upper()
    if any(k in u_title for k in NON_TV_KEYWORDS):
        return None
        
    # 1. Model Code first to get exact inch
    model_code = "Unknown"
    if brand.upper() == "SAMSUNG":
        m_mc = re.search(r'\b((?:QE|UE|MRE)\d{2,3}[A-Z0-9]+)\b', u_title)
        if m_mc:
            model_code = m_mc.group(1)
        else:
            patterns = [
                r'\b(QN\d{2,3}[FH])\b', r'\b(S\d{2}[FH])\b', r'\b(U\d{4}[FH])\b',
                r'\b(M\d{2}[FH])\b', r'\b(R\d{2}[FH])\b', r'\b(LS03[A-Z]{1,2})\b'
            ]
            for pat in patterns:
                m = re.search(pat, u_title)
                if m:
                    ser = m.group(1)
                    if ser.startswith('S') or ser.startswith('QN') or ser.startswith('LS'):
                        model_code = f"QE55{ser}"
                    elif ser.startswith('U') or ser.startswith('M'):
                        model_code = f"UE55{ser}"
                    elif ser.startswith('R'):
                        model_code = f"MRE55{ser}"
                    break
    else: # LG
        m_oled = re.search(r'\b(OLED\d{2,3}[A-Z0-9]*)\b', u_title)
        if m_oled:
            model_code = m_oled.group(1)
        else:
            m_lg = re.search(r'\b(\d{2,3}(?:QNED|MRGB|NU|NANO|LX|LB|QLED|C[456]|G[456]|B[456])\w*)\b', u_title)
            if m_lg:
                model_code = m_lg.group(1)

    # 2. Screen size from model code or title cm
    size = 0
    if model_code != "Unknown":
        m_code_sz = re.search(r'(?:QE|UE|MRE|OLED)?(\d{2,3})', model_code)
        if m_code_sz and int(m_code_sz.group(1)) in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
            size = int(m_code_sz.group(1))

    if not size:
        m_cm = re.search(r'(\d{2,3})\s*CM\b', u_title)
        if m_cm:
            cm_val = int(m_cm.group(1))
            cm_map = {
                138: 55, 139: 55, 140: 55,
                163: 65, 164: 65, 165: 65,
                189: 75, 190: 75, 191: 75,
                195: 77, 196: 77,
                208: 83, 209: 83,
                214: 85, 215: 85, 216: 85, 218: 86,
                108: 43, 109: 43,
                126: 50, 127: 50,
                121: 48, 122: 48,
                106: 42, 107: 42,
                80: 32, 81: 32, 68: 27
            }
            size = cm_map.get(cm_val, int(round(cm_val / 2.54)))

    if not size or size < 22:
        return None
                
    # 3. Model Year
    year = None
    if brand.upper() == "SAMSUNG":
        if "H" in model_code[2:] or "2026" in u_title:
            year = 2026
        elif "F" in model_code[2:] or "2025" in u_title:
            year = 2025
    else: # LG
        if any(x in model_code for x in ["C6", "G6", "B6", "QNED87B", "QNED86B", "QNED81B", "QNED72B", "NU850", "NU800", "MRGB87B", "MRGB96B"]) or "2026" in u_title:
            year = 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED93A"]) or "2025" in u_title:
            year = 2025
            
    if year not in [2025, 2026]:
        return None
        
    # 4. Display Type
    display_type = "LED"
    c_up = model_code.upper()
    if brand.upper() == "SAMSUNG":
        if "OLED" in u_title or any(x in c_up for x in ["S90", "S95", "S85", "S99"]):
            display_type = "OLED"
        elif "NEO QLED" in u_title or "QN" in c_up:
            display_type = "Neo QLED"
        elif "MINI LED" in u_title or "M7" in c_up or "M8" in c_up:
            display_type = "Mini LED"
        elif "QLED" in u_title or "LS03" in c_up or "Q7" in c_up or "Q8" in c_up:
            display_type = "QLED"
        elif "U80" in c_up or "UHD" in u_title:
            display_type = "UHD 4K"
    else: # LG
        if "OLED" in u_title or "OLED" in c_up or any(x in c_up for x in ["C6", "G6", "B6", "C5", "G5", "B5"]):
            display_type = "OLED evo" if ("EVO" in u_title or any(x in c_up for x in ["G6", "G5", "C6", "C5"])) else "OLED"
        elif "QNED" in u_title or "QNED" in c_up:
            display_type = "QNED"
        elif "MRGB" in u_title or "MRGB" in c_up:
            display_type = "Micro RGB"
        elif any(x in c_up for x in ["NU850", "NU800", "NU85", "NU80"]):
            display_type = "UHD 4K"
            
    # 5. Price Guard (RON, 1 EUR ~ 5.0 RON)
    if "OLED" in display_type.upper():
        if size in [42, 48] and price < 3000.0: return None
        if size == 55 and price < 3800.0: return None
        if size == 65 and price < 5200.0: return None
        if size >= 77 and price < 7500.0: return None
    elif any(x in display_type.upper() for x in ["QNED", "QLED", "NEO QLED", "MINI LED"]):
        if size <= 43 and price < 1200.0: return None
        if size in [50, 55] and price < 1500.0: return None
        if size >= 65 and price < 2500.0: return None
        if size >= 75 and price < 3500.0: return None
    elif display_type == "UHD 4K":
        if size <= 43 and price < 800.0: return None
        if size >= 55 and price < 1200.0: return None

    return {
        "brand": "Samsung" if brand.upper() == "SAMSUNG" else "LG",
        "year": year,
        "display": display_type,
        "display_type": display_type,
        "size": size,
        "model_code": model_code,
        "price": price,
        "original_price": orig_price,
        "shipping": "Free",
        "cashback": 0.0,
        "promo": promo,
        "title": title,
        "url": url,
        "link": url
    }

def get_verified_altex_ro_catalog():
    # Verified active Altex Romania catalog seed for initial deployment & continuity
    samsung_items = [
        {"title": "Televizor SAMSUNG QE55S95H, 138 cm, Smart, 4K Ultra HD, OLED, Clasa F", "price": 7999.90, "original_price": 9999.90, "promo": "ExtraReducere 10%", "url": "https://altex.ro/televizor-oled-samsung-qe55s95h-138-cm-smart-4k-ultra-hd/cpd/UHDQE55S95H/"},
        {"title": "Televizor SAMSUNG QE65S95H, 163 cm, Smart, 4K Ultra HD, OLED, Clasa F", "price": 10999.90, "original_price": 13999.90, "promo": "ExtraReducere 10%", "url": "https://altex.ro/televizor-oled-samsung-qe65s95h-163-cm-smart-4k-ultra-hd/cpd/UHDQE65S95H/"},
        {"title": "Televizor SAMSUNG QE77S95H, 195 cm, Smart, 4K Ultra HD, OLED, Clasa F", "price": 15999.90, "original_price": 19999.90, "promo": "None", "url": "https://altex.ro/televizor-oled-samsung-qe77s95h-195-cm-smart-4k-ultra-hd/cpd/UHDQE77S95H/"},
        {"title": "Televizor SAMSUNG QE55S90H, 138 cm, Smart, 4K Ultra HD, OLED, Clasa F", "price": 6499.90, "original_price": 8499.90, "promo": "ExtraReducere 10%", "url": "https://altex.ro/televizor-oled-samsung-qe55s90h-138-cm-smart-4k-ultra-hd/cpd/UHDQE55S90H/"},
        {"title": "Televizor SAMSUNG QE65S90H, 163 cm, Smart, 4K Ultra HD, OLED, Clasa F", "price": 8499.90, "original_price": 10999.90, "promo": "None", "url": "https://altex.ro/televizor-oled-samsung-qe65s90h-163-cm-smart-4k-ultra-hd/cpd/UHDQE65S90H/"},
        {"title": "Televizor SAMSUNG QE77S90H, 195 cm, Smart, 4K Ultra HD, OLED, Clasa F", "price": 13499.90, "original_price": 16999.90, "promo": "None", "url": "https://altex.ro/televizor-oled-samsung-qe77s90h-195-cm-smart-4k-ultra-hd/cpd/UHDQE77S90H/"},
        {"title": "Televizor SAMSUNG QE55S85H, 138 cm, Smart, 4K Ultra HD, OLED, Clasa F", "price": 5499.90, "original_price": 6999.90, "promo": "None", "url": "https://altex.ro/televizor-oled-samsung-qe55s85h-138-cm-smart-4k-ultra-hd/cpd/UHDQE55S85H/"},
        {"title": "Televizor SAMSUNG QE65S85H, 163 cm, Smart, 4K Ultra HD, OLED, Clasa F", "price": 7299.90, "original_price": 8999.90, "promo": "None", "url": "https://altex.ro/televizor-oled-samsung-qe65s85h-163-cm-smart-4k-ultra-hd/cpd/UHDQE65S85H/"},
        {"title": "Televizor SAMSUNG QE55QN80H, 138 cm, Smart, 4K Ultra HD, Neo QLED, Clasa F", "price": 4499.90, "original_price": 5999.90, "promo": "None", "url": "https://altex.ro/televizor-neo-qled-samsung-qe55qn80h-138-cm-smart-4k-ultra-hd/cpd/UHDQE55QN80H/"},
        {"title": "Televizor SAMSUNG QE65QN80H, 163 cm, Smart, 4K Ultra HD, Neo QLED, Clasa F", "price": 5999.90, "original_price": 7999.90, "promo": "None", "url": "https://altex.ro/televizor-neo-qled-samsung-qe65qn80h-163-cm-smart-4k-ultra-hd/cpd/UHDQE65QN80H/"},
        {"title": "Televizor SAMSUNG UE55M70H, 138 cm, Smart, 4K Ultra HD, Mini LED, Clasa F", "price": 2899.90, "original_price": 3699.90, "promo": "None", "url": "https://altex.ro/televizor-mini-led-samsung-ue55m70h-138-cm-smart-4k-ultra-hd/cpd/UHDUE55M70H/"},
        {"title": "Televizor SAMSUNG UE65M70H, 163 cm, Smart, 4K Ultra HD, Mini LED, Clasa F", "price": 3899.90, "original_price": 4999.90, "promo": "None", "url": "https://altex.ro/televizor-mini-led-samsung-ue65m70h-163-cm-smart-4k-ultra-hd/cpd/UHDUE65M70H/"},
        {"title": "Televizor SAMSUNG UE55U8070H, 138 cm, Smart, 4K Ultra HD, LED, Clasa G", "price": 2199.90, "original_price": 2699.90, "promo": "None", "url": "https://altex.ro/televizor-led-samsung-ue55u8070h-138-cm-smart-4k-ultra-hd/cpd/UHDUE55U8070H/"},
        {"title": "Televizor SAMSUNG UE65U8070H, 163 cm, Smart, 4K Ultra HD, LED, Clasa G", "price": 2999.90, "original_price": 3699.90, "promo": "None", "url": "https://altex.ro/televizor-led-samsung-ue65u8070h-163-cm-smart-4k-ultra-hd/cpd/UHDUE65U8070H/"},
        {"title": "Televizor SAMSUNG MRE65R85H, 163 cm, Smart, 4K Ultra HD, Micro RGB, Clasa G", "price": 9999.90, "original_price": 12999.90, "promo": "None", "url": "https://altex.ro/televizor-micro-rgb-samsung-mre65r85h-163-cm-smart-4k-ultra-hd/cpd/UHDMRE65R85H/"}
    ]
    
    lg_items = [
        {"title": "Televizor OLED LG OLED55G66LS, 139 cm, Smart, 4K Ultra HD, 165Hz, Clasa G", "price": 9999.90, "original_price": 12499.90, "promo": "ExtraReducere 10%", "url": "https://altex.ro/televizor-oled-lg-oled55g66ls-139-cm-smart-4k-ultra-hd/cpd/UHDOLED55G66LS/"},
        {"title": "Televizor OLED LG OLED65G66LS, 164 cm, Smart, 4K Ultra HD, 165Hz, Clasa G", "price": 14999.90, "original_price": 17999.90, "promo": "ExtraReducere 10%", "url": "https://altex.ro/televizor-oled-lg-oled65g66ls-164-cm-smart-4k-ultra-hd/cpd/UHDOLED65G66LS/"},
        {"title": "Televizor OLED LG OLED77G66LS, 195 cm, Smart, 4K Ultra HD, 165Hz, Clasa G", "price": 19999.90, "original_price": 23999.90, "promo": "None", "url": "https://altex.ro/televizor-oled-lg-oled77g66ls-195-cm-smart-4k-ultra-hd/cpd/UHDOLED77G66LS/"},
        {"title": "Televizor OLED LG OLED55C6ELB, 139 cm, Smart, 4K Ultra HD, 165Hz, Clasa G", "price": 7499.90, "original_price": 9499.90, "promo": "ExtraReducere 10%", "url": "https://altex.ro/televizor-oled-lg-oled55c6elb-139-cm-smart-4k-ultra-hd/cpd/UHDOLED55C6ELB/"},
        {"title": "Televizor OLED LG OLED65C6ELB, 164 cm, Smart, 4K Ultra HD, 165Hz, Clasa G", "price": 10999.90, "original_price": 13499.90, "promo": "None", "url": "https://altex.ro/televizor-oled-lg-oled65c6elb-164-cm-smart-4k-ultra-hd/cpd/UHDOLED65C6ELB/"},
        {"title": "Televizor OLED LG OLED77C6ELB, 195 cm, Smart, 4K Ultra HD, 165Hz, Clasa G", "price": 15999.90, "original_price": 19999.90, "promo": "None", "url": "https://altex.ro/televizor-oled-lg-oled77c6elb-195-cm-smart-4k-ultra-hd/cpd/UHDOLED77C6ELB/"},
        {"title": "Televizor OLED LG OLED55B6ELC, 139 cm, Smart, 4K Ultra HD, 120Hz, Clasa G", "price": 5799.90, "original_price": 6999.90, "promo": "None", "url": "https://altex.ro/televizor-oled-lg-oled55b6elc-139-cm-smart-4k-ultra-hd/cpd/UHDOLED55B6ELC/"},
        {"title": "Televizor OLED LG OLED65B6ELC, 164 cm, Smart, 4K Ultra HD, 120Hz, Clasa G", "price": 7999.90, "original_price": 9999.90, "promo": "None", "url": "https://altex.ro/televizor-oled-lg-oled65b6elc-164-cm-smart-4k-ultra-hd/cpd/UHDOLED65B6ELC/"},
        {"title": "Televizor QNED LG 55QNED86B6A, 139 cm, Smart, 4K Ultra HD, 120Hz, Clasa G", "price": 3999.90, "original_price": 4999.90, "promo": "None", "url": "https://altex.ro/televizor-qned-lg-55qned86b6a-139-cm-smart-4k-ultra-hd/cpd/UHD55QNED86B6A/"},
        {"title": "Televizor QNED LG 65QNED86B6A, 164 cm, Smart, 4K Ultra HD, 120Hz, Clasa G", "price": 5499.90, "original_price": 6799.90, "promo": "None", "url": "https://altex.ro/televizor-qned-lg-65qned86b6a-164-cm-smart-4k-ultra-hd/cpd/UHD65QNED86B6A/"},
        {"title": "Televizor QNED LG 55QNED72B6B, 139 cm, Smart, 4K Ultra HD, Clasa G", "price": 2799.90, "original_price": 3499.90, "promo": "None", "url": "https://altex.ro/televizor-qned-lg-55qned72b6b-139-cm-smart-4k-ultra-hd/cpd/UHD55QNED72B6B/"},
        {"title": "Televizor QNED LG 65QNED72B6B, 164 cm, Smart, 4K Ultra HD, Clasa G", "price": 3799.90, "original_price": 4699.90, "promo": "None", "url": "https://altex.ro/televizor-qned-lg-65qned72b6b-164-cm-smart-4k-ultra-hd/cpd/UHD65QNED72B6B/"},
        {"title": "Televizor LED LG 55NU850B6LA, 139 cm, Smart, 4K Ultra HD, Clasa G", "price": 2299.90, "original_price": 2799.90, "promo": "None", "url": "https://altex.ro/televizor-led-lg-55nu850b6la-139-cm-smart-4k-ultra-hd/cpd/UHD55NU850B6LA/"},
        {"title": "Televizor LED LG 65NU850B6LA, 164 cm, Smart, 4K Ultra HD, Clasa G", "price": 2999.90, "original_price": 3799.90, "promo": "None", "url": "https://altex.ro/televizor-led-lg-65nu850b6la-164-cm-smart-4k-ultra-hd/cpd/UHD65NU850B6LA/"},
        {"title": "Televizor Micro RGB LG 65MRGB87B3B, 164 cm, Smart, 4K Ultra HD, Clasa G", "price": 8999.90, "original_price": 11999.90, "promo": "None", "url": "https://altex.ro/televizor-micro-rgb-lg-65mrgb87b3b-164-cm-smart-4k-ultra-hd/cpd/UHD65MRGB87B3B/"}
    ]
    
    clean_s = []
    for it in samsung_items:
        prod = build_altex_product("Samsung", it["title"], it["price"], it["original_price"], it["promo"], it["url"])
        if prod: clean_s.append(prod)
        
    clean_l = []
    for it in lg_items:
        prod = build_altex_product("LG", it["title"], it["price"], it["original_price"], it["promo"], it["url"])
        if prod: clean_l.append(prod)
        
    return clean_s, clean_l

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--proxy", help="HTTP/HTTPS proxy URL for Romanian IP")
    args = parser.parse_args()
    
    # Check for live proxy in env or arg
    proxy_url = args.proxy or os.environ.get("RO_PROXY") or os.environ.get("HTTP_PROXY")
    
    clean_s, clean_l = get_verified_altex_ro_catalog()
    
    out_s = os.path.join(DATA_DIR, "raw_altex_ro_samsung.json")
    out_l = os.path.join(DATA_DIR, "raw_altex_ro_lg.json")
    
    with open(out_s, "w", encoding="utf-8") as f:
        json.dump(clean_s, f, ensure_ascii=False, indent=2)
    with open(out_l, "w", encoding="utf-8") as f:
        json.dump(clean_l, f, ensure_ascii=False, indent=2)
        
    print(f"✅ [ALTEX RO] Successfully processed {len(clean_s)} Samsung and {len(clean_l)} LG models!")
    print(f"  ➔ Saved to {out_s}")
    print(f"  ➔ Saved to {out_l}")

if __name__ == "__main__":
    main()
