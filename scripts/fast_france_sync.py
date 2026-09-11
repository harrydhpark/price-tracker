# -*- coding: utf-8 -*-
"""
Fast France Fnac Parser from Firecrawl Markdown Dumps
"""

import os
import sys
import json
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def clean_fr_price(text):
    t = text.replace('\u202f', ' ').replace('\xa0', ' ').replace('\u2009', ' ')
    # Pre-strip discount mentions
    t = re.sub(r'\d+€\s*(?:de\s*remise|d\'économie|de\s*réduction)', '', t, flags=re.IGNORECASE)
    # Pre-strip monthly
    t = re.sub(r'dès\s*[\d\s,.]+\s*€\s*\/\s*mois', '', t, flags=re.IGNORECASE)
    
    # Match 1 299 € or 999 €
    m = re.findall(r'(\d[\d\s]*\d|\d+)\s*€', t)
    vals = []
    for raw in m:
        cleaned = raw.replace(' ', '').replace(',', '.')
        try:
            v = float(cleaned)
            if v >= 100.0:
                vals.append(v)
        except ValueError:
            pass
    return min(vals) if vals else 0.0

def parse_fr_item(chunk, brand):
    # Link and title
    m_link = re.search(r'\[([^\]]+)\]\((https?://www\.fnac\.com/[^\)]+)\)', chunk)
    if not m_link:
        return None
    title = m_link.group(1).strip()
    href = m_link.group(2).strip()
    
    title_upper = title.upper()
    if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "SOUNDBAR", "BARRE DE SON", "SUPPORT", "CASQUE"]):
        return None
        
    size_m = re.search(r'\b(98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:POUCES|CM|\b)', title_upper)
    size = int(size_m.group(1)) if size_m else 55
    
    # Model code
    m_code = "Unknown"
    code_match = re.search(r'\b(TQ\d{2}[A-Z0-9]{3,8}|QE\d{2}[A-Z0-9]{3,8}|OLED\d{2}[A-Z0-9]{3,8}|\d{2}QNED[A-Z0-9]{2,6}|\d{2}UA\d{2}[A-Z0-9]{2,6}|MRE\d{2}[A-Z0-9]{3,8}|27LX6[A-Z0-9]*)\b', title_upper)
    if code_match:
        m_code = code_match.group(1)
        
    year = 2025
    if any(x in title_upper for x in ["2026", "B6", "C6", "G6", "S90H", "S95H", "S99H", "R85H", "R95H", "QNED86B", "QNED81B", "QNED80B", "QNED72B", "QNED71B", "QNED70B", "27LX6", "STANBYME 2", "U8090H", "M70H"]):
        year = 2026
    elif any(x in title_upper for x in ["2025", "B5", "C5", "G5", "S90F", "S95F", "QNED86A", "QNED80A", "QNED72A", "QNED70A"]):
        year = 2025
    elif any(x in title_upper for x in ["2024", "B4", "C4", "G4", "S90D"]):
        year = 2024
        
    pval = clean_fr_price(chunk)
    if pval < 100.0:
        return None
        
    disp = "OLED" if "OLED" in title_upper else ("QNED" if "QNED" in title_upper else ("QLED" if "QLED" in title_upper else "UHD 4K"))
    return {
        "brand": brand,
        "year": year,
        "display": disp,
        "size": size,
        "model_code": m_code,
        "price": pval,
        "shipping": "Free",
        "cashback": 0,
        "promo": "None",
        "title": title,
        "link": href
    }

def process_dumps(samsung_path, lg_path):
    # Samsung
    samsungs = []
    seen_s = {}
    with open(samsung_path, "r", encoding="utf-8") as f:
        content = f.read()
    chunks = content.split("###")
    for ch in chunks:
        it = parse_fr_item(ch, "Samsung")
        if it and it["year"] in [2025, 2026] and it["size"] >= 22:
            m = it["model_code"]
            if m not in seen_s or it["price"] < seen_s[m]["price"]:
                seen_s[m] = it
    samsungs = list(seen_s.values())
    
    # LG
    lgs = []
    seen_l = {}
    with open(lg_path, "r", encoding="utf-8") as f:
        content = f.read()
    chunks = content.split("###")
    for ch in chunks:
        it = parse_fr_item(ch, "LG")
        if it and it["year"] in [2025, 2026] and it["size"] >= 22:
            m = it["model_code"]
            if m not in seen_l or it["price"] < seen_l[m]["price"]:
                seen_l[m] = it
    lgs = list(seen_l.values())
    
    print(f"Parsed {len(samsungs)} Samsung and {len(lgs)} LG live products for France Fnac.")
    if samsungs:
        with open(os.path.join(DATA_DIR, "raw_fnac_samsung.json"), "w", encoding="utf-8") as f:
            json.dump(samsungs, f, ensure_ascii=False, indent=2)
    if lgs:
        with open(os.path.join(DATA_DIR, "raw_fnac_lg.json"), "w", encoding="utf-8") as f:
            json.dump(lgs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        process_dumps(sys.argv[1], sys.argv[2])
