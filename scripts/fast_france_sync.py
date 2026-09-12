# -*- coding: utf-8 -*-
"""
Fast France (Fnac & Darty) Parser from Firecrawl Markdown Dumps
"""

import os
import sys
import json
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

CM_TO_INCH = {
    61: 24, 68: 27, 80: 32, 81: 32, 108: 43, 109: 43, 126: 50, 127: 50,
    139: 55, 140: 55, 164: 65, 165: 65, 189: 75, 190: 75, 195: 77, 196: 77,
    210: 83, 215: 85, 218: 86, 248: 98, 252: 100
}

def clean_fr_price(text):
    t = text.replace('\u202f', ' ').replace('\xa0', ' ').replace('\u2009', ' ')
    t = re.sub(r'\d+€\s*(?:de\s*remise|d\'économie|de\s*réduction)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'dès\s*[\d\s,.]+\s*€\s*\/\s*mois', '', t, flags=re.IGNORECASE)
    
    m = re.findall(r'(\d+[\d\s]*[,\.]\d{2}|\d+[\d\s]*)\s*€', t)
    vals = []
    for raw in m:
        cleaned = raw.strip().replace(' ', '').replace(',', '.')
        try:
            v = float(cleaned)
            if v >= 100.0:
                vals.append(v)
        except ValueError:
            pass
    return min(vals) if vals else 0.0

def parse_fr_item(chunk, brand):
    m_link = re.search(r'\[([^\]]+)\]\((https?://(?:www\.)?(?:fnac|darty)\.com/[^\)]+)\)', chunk)
    if not m_link:
        return None
    title = m_link.group(1).strip()
    href = m_link.group(2).strip()
    
    title_upper = title.upper()
    if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "SOUNDBAR", "BARRE DE SON", "SUPPORT", "CASQUE"]):
        return None
        
    # Size from cm or inch or model code
    size = 0
    m_inch = re.search(r'\b(98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:POUCES|\"|\b)', title_upper)
    if m_inch:
        size = int(m_inch.group(1))
    else:
        m_cm = re.search(r'\b(\d{2,3})\s*CM\b', title_upper)
        if m_cm:
            cm_val = int(m_cm.group(1))
            size = CM_TO_INCH.get(cm_val, int(round(cm_val / 2.54)))
            
    # Model code
    m_code = "Unknown"
    mc = re.search(r'\b(TU\d{2}[A-Z0-9]{3,8}|TQ\d{2}[A-Z0-9]{3,8}|QE\d{2}[A-Z0-9]{3,8}|OLED\d{2}[A-Z0-9]{3,8}|\d{2}QNED[A-Z0-9]{2,6}|\d{2}LB\d{3}[A-Z0-9]*|\d{2}UA\d{2}[A-Z0-9]{2,6}|MRE\d{2}[A-Z0-9]{3,8}|STANBYME|27LX6[A-Z0-9]*)\b', title_upper)
    if mc:
        m_code = mc.group(1)
        if not size:
            m_sz_in_code = re.search(r'\b(?:TU|TQ|QE|OLED|MRE)?(\d{2})', m_code)
            if m_sz_in_code:
                size = int(m_sz_in_code.group(1))
    elif 'STANBYME' in title_upper:
        m_code = 'STANBYME'
        size = 27
        
    if not size:
        size = 55
        
    if size < 22:
        return None
        
    year = 2025
    if any(x in title_upper for x in ["2026", "M72H", "U8005H", "M80H", "QN74H", "LB700", "B6", "C6", "G6", "S90H", "S95H", "S99H", "R85H", "R95H", "QNED86B", "QNED81B", "QNED80B", "QNED72B", "QNED71B", "QNED70B", "27LX6", "STANBYME 2", "U8090H", "M70H"]):
        year = 2026
    elif any(x in title_upper for x in ["2025", "Q5F", "Q7F", "QN90F", "B5", "C5", "G5", "S90F", "S95F", "QNED86A", "QNED80A", "QNED72A", "QNED70A"]):
        year = 2025
    elif any(x in title_upper for x in ["2024", "B4", "C4", "G4", "S90D"]):
        year = 2024
        
    pval = clean_fr_price(chunk)
    if pval < 100.0:
        return None
        
    if "QNED" in m_code or "QNED" in title_upper:
        disp = "QNED"
    elif "MRGB" in m_code or "MICRO RGB" in title_upper or "R85" in title_upper:
        disp = "Micro RGB"
    elif "OLED" in m_code or "OLED" in title_upper:
        disp = "OLED"
    elif "QLED" in m_code or "QLED" in title_upper or any(k in title_upper for k in ["LS03", "QN8", "QN9", "QN7"]):
        disp = "QLED"
    else:
        disp = "UHD 4K"
    return {
        "brand": brand,
        "name": title,
        "title": title,
        "year": year,
        "display": disp,
        "size": size,
        "model_code": m_code,
        "price": pval,
        "shipping": "Free",
        "cashback": 0,
        "promo": "None",
        "url": href
    }

def process_dumps(samsung_path, lg_path):
    # Samsung
    samsungs = []
    seen_s = {}
    with open(samsung_path, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        content = json.loads(content).get("markdown", content)
    except Exception:
        pass

    chunks = content.split("###") if "###" in content else re.split(r'(?=\[TV\s+)', content)
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
    try:
        content = json.loads(content).get("markdown", content)
    except Exception:
        pass

    chunks = content.split("###") if "###" in content else re.split(r'(?=\[TV\s+)', content)
    for ch in chunks:
        it = parse_fr_item(ch, "LG")
        if it and it["year"] in [2025, 2026] and it["size"] >= 22:
            m = it["model_code"]
            if m not in seen_l or it["price"] < seen_l[m]["price"]:
                seen_l[m] = it
    lgs = list(seen_l.values())
    
    print(f"Parsed {len(samsungs)} Samsung and {len(lgs)} LG live products for France.")
    if samsungs:
        out_s = os.path.join(DATA_DIR, "raw_fnac_samsung.json")
        with open(out_s, "w", encoding="utf-8") as f:
            json.dump(samsungs, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(samsungs)} items to {out_s}")
    if lgs:
        out_l = os.path.join(DATA_DIR, "raw_fnac_lg.json")
        with open(out_l, "w", encoding="utf-8") as f:
            json.dump(lgs, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(lgs)} items to {out_l}")

if __name__ == "__main__":
    s_path = sys.argv[1] if len(sys.argv) >= 2 else r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1296\output.txt"
    l_path = sys.argv[2] if len(sys.argv) >= 3 else r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1304\output.txt"
    process_dumps(s_path, l_path)

