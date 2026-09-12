# -*- coding: utf-8 -*-
"""
Currys UK Accurate Parser & Synchronizer from Playwright MCP Dump
Extracts true selling prices, original prices, and cleans promotional text (trade-in, soundbar, cashback, voucher).
Applies UK Category-Aware & Screen-Size Price Guards according to SKILL.md.
"""

import os
import sys
import json
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def passes_uk_price_guard(display, size, price):
    d_up = display.upper()
    p = float(price)
    
    if "OLED" in d_up:
        if size in [42, 48] and p < 650.0: return False
        elif size == 55 and p < 800.0: return False
        elif size == 65 and p < 1100.0: return False
        elif size in [77, 83] and p < 1600.0: return False
        elif size >= 83 and p < 2400.0: return False
    elif "MICRO RGB" in d_up or "MRGB" in d_up or "R85" in d_up or "R95" in d_up:
        if size >= 100 and p < 10000.0: return False
        elif size >= 75 and p < 2000.0: return False
        elif size >= 50 and p < 850.0: return False
    elif any(x in d_up for x in ["QNED", "QLED", "NEO QLED"]):
        if size >= 75 and p < 900.0: return False
        elif size >= 65 and p < 550.0: return False
        elif size >= 50 and p < 350.0: return False
        elif size >= 43 and p < 250.0: return False
    else: # UHD 4K
        if size >= 55 and p < 200.0: return False
        elif size >= 43 and p < 150.0: return False
        
    return p >= 120.0

def parse_currys_card_accurate(card_text, card_title, card_href, brand):
    combined = (card_title + ' ' + card_text).upper()
    if any(x in combined for x in ['SOUNDBAR', 'MONITOR', 'ODYSSEY', 'ULTRAGEAR', 'BRACKET', 'WALL MOUNT', 'REMOTE', 'PROJECTOR', 'BEAMER', 'CABLE']):
        return None
        
    lines = [l.strip() for l in card_text.split('\n') if l.strip()]
    
    selling_price = None
    save_amount = None
    was_price = None
    promo_lines = []
    
    for i, l in enumerate(lines):
        p_match = re.match(r'^£([\d,]+(?:\.\d{2})?)$', l)
        if p_match:
            val = float(p_match.group(1).replace(',', ''))
            if i + 1 < len(lines):
                next_l = lines[i+1]
                if re.match(r'^(?:Save\s*£|From\s*£|Was\s*£|Product\s*fiche)', next_l, re.I):
                    selling_price = val
            elif not selling_price:
                selling_price = val
                
        save_m = re.match(r'^Save\s*£([\d,]+(?:\.\d{2})?)', l, re.I)
        if save_m:
            save_amount = float(save_m.group(1).replace(',', ''))
            
        was_m = re.match(r'^Was\s*£([\d,]+(?:\.\d{2})?)', l, re.I)
        if was_m:
            was_price = float(was_m.group(1).replace(',', ''))
            
        if any(x in l.lower() for x in ['trade-in', 'trade in', 'cashback', 'soundbar', 'code', 'off this tv', 'more offers']):
            if not l.startswith('From £') and not l.startswith('£'):
                promo_lines.append(l)

    if not selling_price or selling_price < 80.0:
        return None
        
    orig_price = None
    if was_price and was_price > selling_price:
        orig_price = was_price
    elif save_amount:
        orig_price = round(selling_price + save_amount, 2)
        
    title_line = lines[0] if lines else card_title
    if brand.upper() not in title_line.upper():
        title_line = card_title
        
    # Model Code
    model_code = 'Unknown'
    dash_m = re.search(r'-\s*([A-Z0-9]{5,15})', title_line.upper())
    if dash_m:
        model_code = dash_m.group(1)
    else:
        m_cand = re.search(r'\b([A-Z0-9]{2}\d{2,3}[A-Z0-9]{3,10}|\d{2,3}[A-Z]{3,6}\d{2}[A-Z0-9]{1,6}|OLED\d{2}[A-Z0-9]{2,8}|MRE\d{2,3}[A-Z0-9]{2,6}|QE\d{2,3}[A-Z0-9]{2,8}|UE\d{2,3}[A-Z0-9]{2,8})\b', title_line.upper())
        model_code = m_cand.group(1) if m_cand else 'Unknown'
        
    # Exclude non-model strings
    if model_code.upper() in ["MONTH", "CLAIM", "TRADE", "STARS", "SAMSUNG", "LG", "UNKNOWN", "TELEVISION", "OFFER", "REVIEWS"]:
        return None

    # Screen Size Extraction (Include 115, 100 and model code fallback)
    size_m = re.search(r'\b(115|100|98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s\"”\'-]*(?:INCH|\b)', title_line.upper())
    if size_m:
        size = int(size_m.group(1))
    else:
        c_sz = re.search(r'(?:^|[A-Z]{1,3})(\d{2,3})(?:[A-Z]|$)', model_code)
        if c_sz and int(c_sz.group(1)) in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
            size = int(c_sz.group(1))
        else:
            size = 55
    if size < 22:
        return None
        
    year = 2025
    u_title = title_line.upper()
    if any(x in u_title for x in ['2026', ' H', 'B6', 'C6', 'G6', 'S90H', 'S95H', 'S85H', 'S99H', 'QN80H', 'QN70H', 'M70H', 'M80H', 'R85H', 'R95H', 'QNED86B', 'QNED81B', 'QNED80B', 'QNED72B', 'QNED71B', 'QNED70B', 'MRGB88B', 'MRGB96B', '27LX6', 'STANBYME 2', 'STANBYME', 'NU85', 'NU80']):
        year = 2026
    elif any(x in u_title for x in ['2025', ' F', 'B5', 'C5', 'G5', 'S90F', 'S95F', 'QN90F', 'QN80F', 'QN70F', 'Q7F', 'Q8F', 'QNED86A', 'QNED80A', 'QNED70A', 'UA75', 'LX7']):
        year = 2025
    elif any(x in u_title for x in ['2024', ' D', 'B4', 'C4', 'G4', 'S90D']):
        year = 2024
        
    if year < 2025:
        return None
        
    display = 'OLED' if 'OLED' in u_title else ('MICRO RGB' if ('MICRO RGB' in u_title or 'MRGB' in u_title or 'R85' in u_title or 'R95' in u_title) else ('QNED' if 'QNED' in u_title else ('QLED' if ('QLED' in u_title or 'NEO QLED' in u_title) else 'UHD 4K')))
    
    if not passes_uk_price_guard(display, size, selling_price):
        return None
        
    promo_str = 'None'
    clean_promos = []
    if save_amount:
        clean_promos.append(f'Save GBP {save_amount:.2f}')
    for pl in promo_lines:
        if '+more offers' in pl or pl.startswith('+'): continue
        ti_m = re.search(r'Get £(\d+)\s*off.*?trade-in.*?(?:Use\s*([A-Z0-9]+))?', pl, re.I)
        if ti_m:
            code_str = f' (Code: {ti_m.group(2)})' if ti_m.group(2) else ''
            clean_promos.append(f'Trade-in GBP {ti_m.group(1)} off{code_str}')
            continue
        sb_m = re.search(r'(?:Free|Get)\s*([^.]+?Soundbar[^.]*)', pl, re.I)
        if sb_m:
            clean_promos.append(sb_m.group(0).strip())
            continue
        cb_m = re.search(r'£(\d+)\s*cashback', pl, re.I)
        if cb_m:
            clean_promos.append(f'GBP {cb_m.group(1)} Cashback')
            continue
        if len(pl) < 80:
            clean_promos.append(pl)
    if clean_promos:
        promo_str = '; '.join(dict.fromkeys(clean_promos))
        
    return {
        'brand': brand.capitalize(),
        'year': year,
        'display': display,
        'size': size,
        'model_code': model_code,
        'price': selling_price,
        'orig_price': orig_price,
        'shipping': 'Free',
        'cashback': 0,
        'promo': promo_str,
        'title': title_line,
        'link': card_href
    }

def process_currys_dump(output_path):
    print(f"Loading Currys dump from: {output_path}")
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith("### Result"):
        content = content[len("### Result"):].strip()
    idx = content.find("### Ran Playwright code")
    if idx != -1:
        content = content[:idx].strip()
        
    raw_data = json.loads(content)
    if "data" in raw_data and isinstance(raw_data["data"], dict):
        samsungs_raw = raw_data["data"].get("samsung", [])
        lgs_raw = raw_data["data"].get("lg", [])
    else:
        samsungs_raw = raw_data.get("samsung", [])
        lgs_raw = raw_data.get("lg", [])
    
    # Process Samsung
    s_seen = {}
    for c in samsungs_raw:
        rec = parse_currys_card_accurate(c.get('text', ''), c.get('title', ''), c.get('href', ''), 'Samsung')
        if rec and rec['model_code'] != 'Unknown':
            mc = rec['model_code']
            if mc not in s_seen or rec['price'] < s_seen[mc]['price']:
                s_seen[mc] = rec
    samsungs = sorted(list(s_seen.values()), key=lambda x: (x['year'], x['size'], x['price']), reverse=True)
    
    # Process LG
    l_seen = {}
    for c in lgs_raw:
        rec = parse_currys_card_accurate(c.get('text', ''), c.get('title', ''), c.get('href', ''), 'LG')
        if rec and rec['model_code'] != 'Unknown':
            mc = rec['model_code']
            if mc not in l_seen or rec['price'] < l_seen[mc]['price']:
                l_seen[mc] = rec
    lgs = sorted(list(l_seen.values()), key=lambda x: (x['year'], x['size'], x['price']), reverse=True)
    
    print(f"✅ Extracted {len(samsungs)} Samsung and {len(lgs)} LG valid models from Currys UK.")
    
    out_s = os.path.join(DATA_DIR, "raw_currys_samsung.json")
    with open(out_s, "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    print(f"Saved Samsung data to: {out_s}")
    
    out_l = os.path.join(DATA_DIR, "raw_currys_lg.json")
    with open(out_l, "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
    print(f"Saved LG data to: {out_l}")
    
    return samsungs, lgs

if __name__ == "__main__":
    dump_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\harry.park\.gemini\antigravity\brain\c4e89f42-4283-436e-907c-28b97a4e6da0\.system_generated\steps\413\output.txt"
    process_currys_dump(dump_path)
