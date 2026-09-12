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

def clean_fr_price(text, size=55, disp='LED'):
    t = text.replace('\u202f', ' ').replace('\xa0', ' ').replace('\u2009', ' ').replace('\u200b', ' ')
    # Strip discount mentions and installment fees
    t = re.sub(r'\b\d+\s*€\s*(?:de\s*remise|d\'économie|de\s*réduction|remise|réduction)\b', '', t, flags=re.IGNORECASE)
    t = re.sub(r'dès\s*[\d\s,.]+\s*€\s*\/\s*mois', '', t, flags=re.IGNORECASE)
    t = re.sub(r'Apport\s*[\d\s,.]+\s*€', '', t, flags=re.IGNORECASE)
    
    m = re.findall(r'(\d+[\d\s]*[,\.]\d{2}|\d+[\d\s]*)\s*€', t)
    vals = []
    for raw in m:
        cleaned = raw.strip().replace(' ', '').replace(',', '.')
        try:
            v = float(cleaned)
            if v >= 120.0:
                vals.append(v)
        except ValueError:
            pass
    if not vals:
        return 0.0
    # Guard against low discount badges on OLED flagships
    if disp == 'OLED':
        min_p = 650.0 if size <= 48 else (800.0 if size <= 55 else (1100.0 if size <= 65 else 1600.0))
        valid = [v for v in vals if v >= min_p]
        return min(valid) if valid else min(vals)
    return min(vals)

def parse_fr_item(chunk, brand):
    m_link = re.search(r'\[([^\]]+)\]\((https?://(?:www\.)?(?:fnac|darty)\.com/[^\)]+/a\d+/[^\)]*)\)', chunk)
    if not m_link:
        return None
    title = m_link.group(1).strip()
    href = m_link.group(2).strip()
    
    title_upper = title.upper()
    if any(x in title_upper for x in ['MONITOR', 'ODYSSEY', 'ULTRAGEAR', 'SOUNDBAR', 'BARRE DE SON', 'SUPPORT', 'CASQUE', 'COFFRET']):
        return None
    if brand.upper() not in title_upper and not any(k in title_upper for k in ['OLED', 'QNED', 'S90', 'S95', 'C6', 'G6', 'B6', 'C5', 'G5']):
        return None
        
    size = 0
    m_cm = re.search(r'\b(\d{2,3})\s*CM\b', title_upper)
    if m_cm:
        cm_val = int(m_cm.group(1))
        size = CM_TO_INCH.get(cm_val, int(round(cm_val / 2.54)))
    if not size:
        m_inch = re.search(r'\b(98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:POUCES|\"|\b)', title_upper)
        if m_inch:
            size = int(m_inch.group(1))
            
    m_code = 'Unknown'
    mc = re.search(r'\b(TU\d{2}[A-Z0-9]{3,8}|TQ\d{2}[A-Z0-9]{3,8}|QE\d{2}[A-Z0-9]{3,8}|OLED\d{2}[A-Z0-9]{1,8}|\d{2}QNED[A-Z0-9]{1,6}|\d{2}LB\d{3}[A-Z0-9]*|\d{2}UA\d{2}[A-Z0-9]{1,6}|\d{2}NU\d{3}[A-Z0-9]*|\d{2}NANO\d{2}[A-Z0-9]*|MRE\d{2}[A-Z0-9]{3,8}|STANBYME|27LX6[A-Z0-9]*)\b', title_upper)
    if mc:
        m_code = mc.group(1)
        if not size:
            m_sz = re.search(r'(?:TU|TQ|QE|OLED|MRE)?(\d{2})', m_code)
            if m_sz:
                size = int(m_sz.group(1))
    elif 'STANBYME' in title_upper:
        m_code = 'STANBYME'
        size = 27
        
    if not size:
        size = 55
    if size < 22:
        return None
        
    # Strict 2024 model exclusion
    if brand.upper() == "SAMSUNG":
        if re.search(r'[A-Z0-9]{2}\d{2}[A-Z0-9]*D\b', m_code) or any(x in m_code for x in ["S90D", "S95D", "QN90D", "QE1D", "Q60D", "Q70D", "Q80D", "DU7", "DU8"]):
            return None
    elif brand.upper() == "LG":
        if any(x in m_code for x in ["C4", "G4", "B4", "M4", "UA73", "UT8", "LQ6"]):
            return None

    year = 2025
    if any(x in title_upper for x in ['2026', 'M72H', 'U8005H', 'M80H', 'QN74H', 'LB700', 'B6', 'C6', 'G6', 'W6', 'M6', 'S90H', 'S95H', 'S99H', 'R85H', 'R95H', 'QNED86B', 'QNED81B', 'QNED80B', 'QNED87B', 'QNED72B', 'QNED71B', 'QNED70B', '27LX6', 'STANBYME 2', 'U8090H', 'M70H', 'NU850']):
        year = 2026
    elif any(x in title_upper for x in ['2025', 'Q5F', 'Q7F', 'QN90F', 'B5', 'C5', 'G5', 'W5', 'M5', 'S90F', 'S95F', 'QNED86A', 'QNED80A', 'QNED87A', 'QNED72A', 'QNED70A', 'NANO81', 'QNED93A', 'QNED84A']):
        year = 2025
    elif any(x in title_upper for x in ['2024', 'B4', 'C4', 'G4', 'S90D', 'LQ63', 'UT81', 'Z2']):
        year = 2024
        
    if year < 2025:
        return None
        
    if 'QNED' in m_code or 'QNED' in title_upper:
        disp = 'QNED'
    elif 'MRGB' in m_code or 'MICRO RGB' in title_upper or 'R85' in title_upper:
        disp = 'Micro RGB'
    elif 'OLED' in m_code or 'OLED' in title_upper:
        disp = 'OLED'
    elif 'QLED' in m_code or 'QLED' in title_upper or any(k in title_upper for k in ['LS03', 'QN8', 'QN9', 'QN7', 'M80', 'M72']):
        disp = 'QLED'
    elif 'NANO' in m_code or 'NANOCELL' in title_upper:
        disp = 'NanoCell'
    else:
        disp = 'UHD 4K'
        
    pval = clean_fr_price(chunk, size=size, disp=disp)
    if pval < 100.0:
        return None
        
    # Strict Category Price Floor Guard (prevents installment/discount false positives)
    if disp == "OLED":
        if size >= 83 and pval < 1800.0: return None
        if size >= 77 and pval < 1300.0: return None
        if size >= 70 and pval < 1100.0: return None
        if size >= 65 and pval < 850.0: return None
        if size >= 55 and pval < 650.0: return None
        if size in [42, 48] and pval < 500.0: return None
    elif disp in ["QNED", "QLED"]:
        if size >= 75 and pval < 600.0: return None
        if size >= 65 and pval < 450.0: return None
        if size >= 50 and pval < 280.0: return None
        if size >= 43 and pval < 200.0: return None
    else:
        if size >= 70 and pval < 450.0: return None
        if size >= 55 and pval < 180.0: return None
        if size >= 43 and pval < 120.0: return None
        
    return {
        'brand': brand,
        'name': title,
        'title': title,
        'year': year,
        'display': disp,
        'size': size,
        'model_code': m_code,
        'price': pval,
        'shipping': 'Free',
        'cashback': 0,
        'promo': 'None',
        'url': href
    }

def process_file_list(file_paths, brand):
    seen = {}
    for p in file_paths:
        if not os.path.exists(p):
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    content = data.get("markdown", content)
            except Exception:
                pass
            matches = list(re.finditer(r'\[([^\]]+)\]\((https?://(?:www\.)?(?:fnac|darty)\.com/[^\)]+/a\d+/[^\)]*)\)', content))
            for i, m in enumerate(matches):
                start = m.start()
                end = matches[i+1].start() if i + 1 < len(matches) else start + 1500
                chunk = content[start:end]
                it = parse_fr_item(chunk, brand)
                if it and it["year"] in [2025, 2026] and it["size"] >= 22:
                    mc = it["model_code"]
                    if mc not in seen or it["price"] < seen[mc]["price"]:
                        seen[mc] = it
        except Exception as e:
            print(f"Error reading {p}: {e}")
    return list(seen.values())

def sync_france(samsung_paths=None, lg_paths=None):
    if not samsung_paths:
        samsung_paths = [
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1895\output.txt",
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1903\output.txt",
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1905\output.txt",
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1913\output.txt",
        ]
    if not lg_paths:
        lg_paths = [
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1907\output.txt",
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1909\output.txt",
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1911\output.txt",
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1915\output.txt",
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1929\output.txt",
            r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\1931\output.txt",
        ]

    samsungs = process_file_list(samsung_paths, "Samsung")
    lgs = process_file_list(lg_paths, "LG")

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
    if len(sys.argv) >= 3:
        sync_france([sys.argv[1]], [sys.argv[2]])
    else:
        sync_france()

