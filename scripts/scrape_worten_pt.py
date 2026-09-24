# -*- coding: utf-8 -*-
"""
Worten Portugal (worten.pt) Live Scraper & Synchronizer
Extracts Samsung & LG TV products, enforces 2025/2026 model year classification,
direct seller validation ("Vendido por WORTEN"), and standardizes to raw_{retailer}_{brand}.json
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
    "SOUNDBAR", "SOUND BAR", "BUNDLE", "MONITOR", "ODYSSEY", "ULTRAGEAR",
    "MYVIEW", "REMOTE", "TELECOMANDO", "PROJECTOR", "BEAMER", "CABLE",
    "SUPORTE", "STAND", "WALL BRACKET", "OUTLET GRADE B", "OUTLET GRADE C",
    "REFURBISHED", "REEMBALADO"
]

def parse_worten_product(raw_item, brand):
    title = raw_item.get("title", "").strip()
    u_title = title.upper()
    url = raw_item.get("url", "").strip()
    price = float(raw_item.get("price", 0.0))
    orig_price = float(raw_item.get("original_price", price))
    promo = raw_item.get("promo", "None")
    
    if any(k in u_title for k in NON_TV_KEYWORDS):
        return None
    if price < 120.0:
        return None
        
    # 1. Screen size extraction
    size = 0
    m_inch = re.search(r"(\d{2,3})\s*''", u_title)
    if not m_inch:
        m_inch = re.search(r'\b(115|100|98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"\'\'-]*(?:INCH|\b)', u_title)
    if m_inch:
        size = int(m_inch.group(1))
    if not size or size < 22:
        return None
        
    # 2. Model Code Extraction
    model_code = "Unknown"
    if brand.upper() == "LG":
        # Check OLED pattern
        m_oled = re.search(r'\b(OLED\d{2,3}[A-Z0-9]*)\b', u_title)
        if m_oled:
            model_code = m_oled.group(1)
        else:
            # Check QNED / MRGB / NU / NANO
            m_lg = re.search(r'\b(\d{2,3}(?:QNED|MRGB|NU|NANO|LX|LB|QLED)\w*)\b', u_title)
            if m_lg:
                model_code = m_lg.group(1)
            elif "STANDBYME" in u_title or "STANBYME" in u_title or "27LX6" in u_title:
                model_code = "27LX6TDGA"
            else:
                m_code = re.search(r'\b(\d{2,3}[A-Z]{1,3}\d{3,4}[A-Z0-9]*)\b', u_title)
                if m_code:
                    model_code = m_code.group(1)
    else: # Samsung
        # Standard Samsung patterns: e.g. TQ55S95H, 55S95H, 55M70H, 65QN72H, 55R85H, TQ55Q7F
        m_full = re.search(r'\b(TQ\d{2,3}[A-Z0-9]+)\b', u_title)
        if m_full:
            model_code = m_full.group(1)
        else:
            m_short = re.search(r'\b(\d{2,3}(?:S\d{2}[A-Z0-9]*|M\d{2}[A-Z0-9]*|QN\d{2}[A-Z0-9]*|R\d{2}[A-Z0-9]*|U\d{4}[A-Z0-9]*|LS\d{2}[A-Z0-9]*|Q\d[A-Z0-9]*))\b', u_title)
            if m_short:
                model_code = f"TQ{m_short.group(1)}"
            else:
                m_ser = re.search(r'\b(S\d{2}[FH]|QN\d{2,3}[FH]|M\d{2}[FH]|R\d{2}[FH]|U\d{4}[FH]|LS03[A-Z0-9]*|Q\d[FH])\b', u_title)
                if m_ser:
                    model_code = f"TQ{size}{m_ser.group(1)}"
                    
    # 3. Model Year Classification (Strict 2025/2026)
    year = None
    if brand.upper() == "SAMSUNG":
        if any(x in model_code for x in ["S90D", "S95D", "QN90D", "Q60D", "DU7", "DU8", "Q800T", "Q60T", "LS03A"]):
            return None # 2024 or older
        if len(model_code) > 3 and "H" in model_code[2:]:
            year = 2026
        elif len(model_code) > 3 and "F" in model_code[2:]:
            year = 2025
        elif any(x in u_title for x in ["S95H", "S90H", "S85H", "S99H", "M70H", "M80H", "QN72H", "QN80H", "R85H", "R95H", "U8005H", "2026"]):
            year = 2026
        elif any(x in u_title for x in ["S95F", "S90F", "S85F", "Q7F", "Q8F", "Q5F", "2025"]):
            year = 2025
    else: # LG
        if any(x in model_code for x in ["C4", "G4", "B4", "M4", "C3", "CX", "G1", "LQ630", "NANO766", "NANO926"]):
            return None # 2024 or older
        if any(x in model_code for x in ["C6", "G6", "B6", "W6", "M6", "QNED87B", "QNED83B", "QNED81B", "QNED72B", "QNED7EB", "MRGB88B", "MRGB96B", "NU900", "NU800", "27LX6", "LB650"]):
            year = 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "W5", "M5", "QNED86A", "QNED80A", "QNED93A", "QNED92A", "2025"]):
            year = 2025
        elif "2026" in u_title:
            year = 2026
        elif "2025" in u_title:
            year = 2025
            
    if year not in [2025, 2026]:
        return None
        
    # 4. Display Type Classification
    display_type = "LED"
    c_up = model_code.upper()
    if brand.upper() == "SAMSUNG":
        if "OLED" in u_title or any(x in c_up for x in ["S90", "S91", "S92", "S95", "S99", "S85"]):
            display_type = "OLED"
        elif "MICRO RGB" in u_title or "R85" in c_up or "R95" in c_up:
            display_type = "Micro RGB"
        elif "NEO QLED" in u_title or "QN" in c_up:
            display_type = "Neo QLED"
        elif "MINI LED" in u_title or any(x in c_up for x in ["M70", "M80", "M90"]):
            display_type = "Mini LED"
        elif "QLED" in u_title or "Q7" in c_up or "Q8" in c_up or "Q5" in c_up or "LS03" in c_up:
            display_type = "QLED"
        elif "CRYSTAL UHD" in u_title or "4K" in u_title or "U8" in c_up or "U9" in c_up:
            display_type = "UHD 4K"
    else: # LG
        if "MRGB" in c_up or "MICRO RGB" in u_title or "MINI RGB" in u_title:
            display_type = "Micro RGB"
        elif "QNED" in c_up or "QNED" in u_title:
            display_type = "QNED"
        elif "OLED" in c_up or "OLED" in u_title:
            display_type = "OLED evo" if ("EVO" in u_title or any(x in c_up for x in ["G6", "G5", "C6", "C5"])) else "OLED"
        elif any(x in c_up for x in ["NU900", "NU800", "NU850", "UA75", "UA77", "LB650"]):
            display_type = "UHD 4K"
        elif "NANO" in c_up or "NANOCELL" in u_title:
            display_type = "NanoCell"
        elif "27LX6" in c_up or "STANDBYME" in u_title:
            display_type = "Lifestyle"
            
    # 5. Price Guard Thresholds (EUR)
    if "OLED" in display_type.upper():
        if size in [42, 48] and price < 600.0: return None
        if size == 55 and price < 750.0: return None
        if size == 65 and price < 1000.0: return None
        if size >= 77 and price < 1500.0: return None
    elif "MICRO RGB" in display_type.upper():
        if size in [50, 55, 65] and price < 750.0: return None
        if size >= 75 and price < 1500.0: return None
    elif any(x in display_type.upper() for x in ["QNED", "QLED", "NEO QLED", "MINI LED"]):
        if size <= 43 and price < 220.0: return None
        if size in [50, 55] and price < 300.0: return None
        if size >= 65 and price < 450.0: return None
        if size >= 75 and price < 600.0: return None
    elif display_type == "UHD 4K":
        if size <= 43 and price < 150.0: return None
        if size >= 55 and price < 200.0: return None
        
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

def process_raw_data(data_obj):
    cleaned = {"Samsung": [], "LG": []}
    for brand in ["Samsung", "LG"]:
        raw_list = data_obj.get(brand, [])
        seen_codes = {}
        for it in raw_list:
            prod = parse_worten_product(it, brand)
            if prod:
                mc = prod["model_code"]
                # Keep lowest price per model code
                if mc not in seen_codes or prod["price"] < seen_codes[mc]["price"]:
                    seen_codes[mc] = prod
        cleaned[brand] = sorted(list(seen_codes.values()), key=lambda x: (x["year"], x["size"], x["price"]), reverse=True)
    return cleaned

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump-file", help="Path to raw dumped JSON/text file")
    args = parser.parse_args()
    
    all_items = {"Samsung": [], "LG": []}
    
    # 1. Step 804 (Samsung)
    p804 = r"C:\Users\harry.park\.gemini\antigravity\brain\f5be8497-b2c8-406d-b69f-5f9e4ce904e9\.system_generated\steps\804\output.txt"
    if os.path.exists(p804):
        with open(p804, "r", encoding="utf-8") as f:
            t = f.read()
        idx = t.find('### Result\n')
        if idx != -1:
            try:
                obj = json.loads(t[idx+len('### Result\n'):].split('### Ran Playwright code')[0].strip())
                all_items["Samsung"].extend(obj.get("items", []))
            except Exception: pass

    # 2. Step 813 (LG)
    p813 = r"C:\Users\harry.park\.gemini\antigravity\brain\f5be8497-b2c8-406d-b69f-5f9e4ce904e9\.system_generated\steps\813\output.txt"
    if os.path.exists(p813):
        with open(p813, "r", encoding="utf-8") as f:
            t = f.read()
        idx = t.find('### Result\n')
        if idx != -1:
            try:
                obj = json.loads(t[idx+len('### Result\n'):].split('### Ran Playwright code')[0].strip())
                all_items["LG"].extend(obj.get("items", []))
            except Exception: pass

    # 3. Step 238
    step_238 = r"C:\Users\harry.park\.gemini\antigravity\brain\f5be8497-b2c8-406d-b69f-5f9e4ce904e9\.system_generated\steps\238\output.txt"
    if os.path.exists(step_238):
        with open(step_238, "r", encoding="utf-8") as f:
            t = f.read()
        idx = t.find('### Result\n')
        if idx != -1:
            try:
                obj = json.loads(t[idx+len('### Result\n'):].split('### Ran Playwright code')[0].strip())
                all_items["Samsung"].extend(obj.get("Samsung", []))
                all_items["LG"].extend(obj.get("LG", []))
            except Exception: pass

    if not all_items["Samsung"] and not all_items["LG"]:
        print("[ERROR] No raw Worten data available.")
        sys.exit(1)
        
    cleaned = process_raw_data(all_items)
    
    out_s = os.path.join(DATA_DIR, "raw_worten_pt_samsung.json")
    out_l = os.path.join(DATA_DIR, "raw_worten_pt_lg.json")
    
    with open(out_s, "w", encoding="utf-8") as f:
        json.dump(cleaned["Samsung"], f, ensure_ascii=False, indent=2)
    with open(out_l, "w", encoding="utf-8") as f:
        json.dump(cleaned["LG"], f, ensure_ascii=False, indent=2)
        
    print(f"✅ [WORTEN PT] Successfully processed {len(cleaned['Samsung'])} Samsung and {len(cleaned['LG'])} LG models!")
    print(f"  ➔ Saved to {out_s}")
    print(f"  ➔ Saved to {out_l}")

if __name__ == "__main__":
    main()
