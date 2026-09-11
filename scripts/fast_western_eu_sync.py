# -*- coding: utf-8 -*-
"""
Fast Western Europe (DE, AT, ES, NL, IT) Sync from Playwright MCP Dump
"""

import os
import sys
import json
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def clean_eu_price(card_text):
    # Remove installment text
    lines = card_text.split('\n')
    valid_lines = [l for l in lines if not any(x in l.upper() for x in ["RATEN", "MONAT", "MESES", "FINANZIERUNG", "CUOTAS", "RATES", "TAEG"])]
    text = " ".join(valid_lines)
    
    # 1. Look for strike-through / selling price pattern
    # e.g., 539,99 €
    m = re.findall(r'(\d[\d\s\.,]*\d)\s*(?:€|,-|,–)', text)
    if not m:
        m = re.findall(r'(?:€|£)\s*(\d[\d\s\.,]*)', text)
        
    prices = []
    for raw in m:
        p = str(raw).replace('\xa0', '').replace('\u202f', ' ').strip()
        if re.match(r'^\d{1,3}\.\d{3}(?:,\d{2})?$', p):
            p = p.replace('.', '').replace(',', '.')
        elif re.match(r'^\d{1,3},\d{3}(?:\.\d{2})?$', p):
            p = p.replace(',', '')
        elif ',' in p:
            p = p.replace(',', '.')
        
        m_num = re.findall(r'(\d+(?:\.\d{2})?)', p)
        if m_num:
            try:
                val = float(m_num[0])
                if val >= 80.0:
                    prices.append(val)
            except ValueError:
                pass
                
    if prices:
        # Selling price is typically the lowest non-accessory price or the last price
        return min(prices)
    return 0.0

def extract_model_and_meta(card_text, brand):
    upper = card_text.upper()
    
    # Exclude non-TVs
    if any(x in upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "WASCHMASCHINE", "HALTERUNG", "WANDHALTERUNG", "SUBWOOFER"]):
        return None, 0, 0, ""
        
    # Size
    size_m = re.search(r'\b(98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:ZOLL|INCH|POUCES|POLLICI|CM|\b)', upper)
    size = int(size_m.group(1)) if size_m else 55
    
    # Model code
    # Samsung: GQ65Q7F, QE55S90F, TQ65S95H, UE55U8070F, MRE55R85H
    # LG: OLED55C54LA, OLED65G6, 55QNED86A, 65UA75006LA, 86MRGB87B
    model_code = "Unknown"
    code_m = re.search(r'\b([A-Z0-9]{2}\d{2}[A-Z0-9]{3,10}|\d{2}[A-Z]{3,6}\d{2}[A-Z0-9]{2,6}|OLED\d{2}[A-Z0-9]{2,6}|MRE\d{2}[A-Z0-9]{2,6})\b', upper)
    if code_m:
        model_code = code_m.group(1)
        
    # Year
    year = 2025
    if any(x in upper for x in ["2026", "B6", "C6", "G6", "R85H", "R95H", "S90H", "S95H", "S99H", "QNED86B", "QNED81B", "QNED80B", "QNED72B", "QNED71B", "QNED70B", "27LX6", "STANBYME 2", "U8090H", "M70H"]):
        year = 2026
    elif any(x in upper for x in ["2025", "B5", "C5", "G5", "S90F", "S95F", "QNED86A", "QNED80A", "QNED72A", "QNED70A"]):
        year = 2025
    elif any(x in upper for x in ["2024", "B4", "C4", "G4", "S90D"]):
        year = 2024
        
    display = "OLED" if "OLED" in upper else ("QNED" if "QNED" in upper else ("QLED" if "QLED" in upper else "UHD 4K"))
    return model_code, size, year, display

def process_dump(output_path):
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith("### Result"):
        content = content[len("### Result"):].strip()
    idx = content.find("### Ran Playwright code")
    if idx != -1:
        content = content[:idx].strip()
        
    raw_data = json.loads(content)
    all_data = raw_data.get("data", {})
    
    for country_key, brands_data in all_data.items():
        samsungs_raw = brands_data.get("samsung", [])
        lgs_raw = brands_data.get("lg", [])
        
        samsungs = []
        seen_s = {}
        for item in samsungs_raw:
            card_text = item.get("cardText", "")
            href = item.get("href", "")
            pval = clean_eu_price(card_text)
            if pval < 80.0:
                continue
            m_code, size, year, disp = extract_model_and_meta(card_text, "Samsung")
            if not m_code or size < 22 or year not in [2025, 2026]:
                continue
            rec = {
                "brand": "Samsung",
                "year": year,
                "display": disp,
                "size": size,
                "model_code": m_code,
                "price": pval,
                "shipping": "Free",
                "cashback": 0,
                "promo": "None",
                "title": card_text.split('\n')[0][:80],
                "link": href
            }
            if m_code not in seen_s or pval < seen_s[m_code]["price"]:
                seen_s[m_code] = rec
        samsungs = list(seen_s.values())
        
        lgs = []
        seen_l = {}
        for item in lgs_raw:
            card_text = item.get("cardText", "")
            href = item.get("href", "")
            pval = clean_eu_price(card_text)
            if pval < 80.0:
                continue
            m_code, size, year, disp = extract_model_and_meta(card_text, "LG")
            if not m_code or size < 22 or year not in [2025, 2026]:
                continue
            rec = {
                "brand": "LG",
                "year": year,
                "display": disp,
                "size": size,
                "model_code": m_code,
                "price": pval,
                "shipping": "Free",
                "cashback": 0,
                "promo": "None",
                "title": card_text.split('\n')[0][:80],
                "link": href
            }
            if m_code not in seen_l or pval < seen_l[m_code]["price"]:
                seen_l[m_code] = rec
        lgs = list(seen_l.values())
        
        print(f"[{country_key}] Parsed {len(samsungs)} Samsung and {len(lgs)} LG live products.")
        
        s_file = os.path.join(DATA_DIR, f"raw_{country_key}_samsung.json")
        l_file = os.path.join(DATA_DIR, f"raw_{country_key}_lg.json")
        
        # Only overwrite if items found
        if samsungs:
            with open(s_file, "w", encoding="utf-8") as f:
                json.dump(samsungs, f, ensure_ascii=False, indent=2)
        if lgs:
            with open(l_file, "w", encoding="utf-8") as f:
                json.dump(lgs, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_dump(sys.argv[1])
