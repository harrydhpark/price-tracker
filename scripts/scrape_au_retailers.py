# -*- coding: utf-8 -*-
"""
Australia TV Retailer Scraping & Cleansing Engine
Scrapes and parses:
1. JB Hi-Fi (jbhifi.com.au)
2. The Good Guys (thegoodguys.com.au)
3. Harvey Norman (harveynorman.com.au)
Filters strictly for Model Year 2025 and 2026, purges non-TV displays,
and outputs clean raw JSON files in data/.
"""

import os, sys, json, re
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def extract_size(text, url=""):
    if url:
        slug = url.split('/')[-1].replace('.html', '').lower()
        m_sz = re.search(r'(?:samsung|lg)-(\d{2,3})(?:-inch)?-', slug)
        if m_sz:
            val = int(m_sz.group(1))
            if val in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
                return val
    m = re.search(r'\b(115|100|98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\x27-]*(?:inch|zoll|pollici|pouces|cm|\b)', text.upper())
    if m:
        return int(m.group(1))
    m_mc = re.search(r'(?:OLED|QA|UA|QNED|QN)?(\d{2,3})[A-Z0-9]', text.upper())
    if m_mc:
        val = int(m_mc.group(1))
        if val in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
            return val
    return 55

def extract_year(text, model_code="", url=""):
    t_up = text.upper()
    mc_up = model_code.upper()
    slug = url.split('/')[-1].replace('.html', '').lower() if url else ""
    
    # 2026 Indicators
    if any(x in slug for x in ["2026", "-c6-", "-g6-", "-b6-", "s90h", "s95h", "s85h", "s99h", "r95h", "r85h", "m80h", "m70h", "qn80h", "qn90h", "qn85h", "ls03h", "qned86b", "qned80b", "qned87b", "qned70b", "qned72b", "mrgb87b"]):
        return 2026
    if any(x in t_up for x in ["2026", " C6", " G6", " B6", " W6", "S90H", "S95H", "S85H", "S99H", "R95H", "R85H", "M80H", "M70H", "U8000H", "QN80H", "QN90H", "QN85H", "LS03H", "QNED86B", "QNED80B", "QNED87B", "QNED70B", "QNED72B", "MRGB87B", "MRGB96B"]):
        return 2026
    if any(x in mc_up for x in ["C6", "G6", "B6", "W6", "M6", "QNED86B", "QNED80B", "QNED87B", "QNED70B", "QNED72B", "MRGB87B", "MRGB96B", "S95H", "S90H", "S85H", "S99H", "R95H", "R85H", "M80H", "M70H", "LS03H", "QN80H", "QN90H", "QN85H"]):
        return 2026
        
    # 2025 Indicators
    if any(x in slug for x in ["2025", "-c5-", "-g5-", "-b5-", "s90f", "s95f", "s85f", "qn90f", "qn85f", "qn80f", "q7f", "q8f", "q6f", "q5f", "ls03f", "f6000"]):
        return 2025
    if any(x in t_up for x in ["2025", " C5", " G5", " B5", "S90F", "S95F", "S85F", "QN90F", "QN85F", "QN80F", "Q7F", "Q8F", "Q6F", "Q5F", "LS03F", "U8000F", "F6000"]):
        return 2025
    if any(x in mc_up for x in ["C5", "G5", "B5", "M5", "QNED86A", "QNED80A", "QNED87A", "QNED70A", "QNED72A", "UA75", "MRGB87A", "S95F", "S90F", "S85F", "QN90F", "QN85F", "QN80F", "Q7F", "Q8F", "Q6F", "Q5F", "LS03F", "F6000"]):
        return 2025
        
    return None

def extract_model_code(text, url=""):
    if url:
        slug = url.split('/')[-1].replace('.html', '').lower()
        m_sz = re.search(r'(?:samsung|lg)-(\d{2,3})(?:-inch)?-', slug)
        s_sz = int(m_sz.group(1)) if m_sz else extract_size(text, url)
        if 'samsung' in slug:
            for s in ['s95h', 's90h', 's85h', 's99h', 'r95h', 'r85h', 'm80h', 'm70h', 'qn90h', 'qn80h', 'qn85h', 'qn90f', 'qn85f', 'qn80f', 'q7f', 'q8f', 'q5f', 's95f', 's90f', 's85f', 'ls03h', 'ls03f', 'f6000']:
                if s in slug:
                    return f"QA{s_sz}{s.upper()}"
        elif 'lg' in slug:
            for s in ['c6', 'g6', 'b6', 'w6', 'm6', 'c5', 'g5', 'b5', 'm5', 'qned86b', 'qned80b', 'qned70b', 'qned86a', 'qned80a', 'mrgb87b']:
                if s in slug:
                    if s.startswith('qned') or s.startswith('mrgb'):
                        return f"{s_sz}{s.upper()}"
                    else:
                        return f"OLED{s_sz}{s.upper()}"

    text_u = text.upper()
    m = re.search(r'\b(OLED\d{2}[A-Z0-9]{3,8}|\d{2,3}[A-Z]{3,6}\d{2}[A-Z0-9]{2,6}|QA\d{2,3}[A-Z0-9]{4,12}|UA\d{2,3}[A-Z0-9]{4,12})\b', text_u)
    if m:
        return m.group(1)
        
    size = extract_size(text, url)
    for s_series in ["S95H", "S90H", "S85H", "S99H", "R95H", "R85H", "M80H", "M70H", "QN80H", "QN90H", "QN85H", "Q7F", "Q8F", "Q5F", "S95F", "S90F", "S85F", "QN90F", "LS03H", "LS03F", "F6000"]:
        if s_series in text_u:
            return f"QA{size}{s_series}"
            
    for l_series in ["W6", "G6", "C6", "B6", "C5", "G5", "B5", "QNED70B", "QNED86B", "QNED80B", "QNED70A", "QNED86A", "MRGB87B", "MRGB96B", "NU85", "NU80", "UA75"]:
        if l_series in text_u:
            if l_series.startswith("QNED") or l_series.startswith("MRGB") or l_series.startswith("NU") or l_series.startswith("UA"):
                return f"{size}{l_series}"
            else:
                return f"OLED{size}{l_series}"
                
    return ""

def parse_dump(dump_path, retailer_name, brand_hint=None):
    if not os.path.exists(dump_path):
        return []
    with open(dump_path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    md = d.get('markdown', '')
    
    items = []
    lines = md.splitlines()
    
    # 1. Partition markdown into distinct product card chunks by URL
    cards = []
    curr_url, curr_lines = None, []
    url_pat = re.compile(r'\((https://(?:www\.)?(?:jbhifi|thegoodguys|harveynorman)\.com\.au/(?:products/|[a-z0-9-]+-(?:tv|smart-tv))[^\)]*)\)')
    
    for line in lines:
        m = url_pat.search(line)
        if m:
            u = m.group(1).split('#')[0]
            if curr_url and curr_url != u:
                cards.append((curr_url, '\n'.join(curr_lines)))
                curr_lines = []
            curr_url = u
        if curr_url:
            curr_lines.append(line)
    if curr_url:
        cards.append((curr_url, '\n'.join(curr_lines)))
        
    # 2. Extract structured TV product from each card
    for url, block in cards:
        url_lower = url.lower()
        if any(b in url_lower for b in ["toshiba", "philips", "ffalcon", "tcl", "hisense", "sony", "panasonic"]):
            continue
        b_up = block.upper()
        if not ("SAMSUNG" in url_lower or "LG" in url_lower or "SAMSUNG" in b_up or "LG " in b_up or "OLED" in url_lower or "OLED" in b_up):
            continue
            
        brand = "SAMSUNG" if ("samsung" in url_lower or "samsung" in b_up) else "LG"
            
        year = extract_year(block, url=url)
        if year not in [2025, 2026]:
            continue
            
        size = extract_size(block, url=url)
        if size < 24:
            continue
            
        mc = extract_model_code(block, url=url)
        if not mc:
            continue
            
        # Clean block of savings badges
        clean_block = re.sub(r'SAVE\s*\$\s*\d+(?:,\d{3})*', '', block, flags=re.I)
        clean_block = re.sub(r'\$\s*\d+(?:,\d{3})*\s*OFF\^?', '', clean_block, flags=re.I)
        clean_block = re.sub(r'TICKET[¤\s]*\$\s*\d+(?:,\d{3})*', '', clean_block, flags=re.I)
        clean_block = re.sub(r'CASHBACK\s*\$\s*\d+(?:,\d{3})*', '', clean_block, flags=re.I)
        
        m_p = re.findall(r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', clean_block)
        prices = []
        for raw in m_p:
            v = float(raw.replace(',', ''))
            # Screen size & category price floor in AUD
            if "OLED" in mc:
                if size >= 83 and v < 3000.0: continue
                elif size >= 77 and v < 2200.0: continue
                elif size >= 65 and v < 1400.0: continue
                elif size >= 55 and v < 1000.0: continue
                elif size in [42, 48] and v < 750.0: continue
                elif v < 550.0: continue
            elif "MRGB" in mc or "R85" in mc or "R95" in mc:
                if size >= 75 and v < 2000.0: continue
                elif size >= 50 and v < 1000.0: continue
                elif v < 600.0: continue
            elif "QNED" in mc or "QN" in mc:
                if size >= 75 and v < 1000.0: continue
                elif size >= 65 and v < 750.0: continue
                elif size >= 50 and v < 450.0: continue
                elif size >= 43 and v < 350.0: continue
            else: # UHD 4K
                if size >= 70 and v < 750.0: continue
                elif size >= 55 and v < 300.0: continue
                elif size >= 43 and v < 200.0: continue
            if v >= 250.0:
                prices.append(v)
                
        if not prices:
            continue
            
        price = min(prices)
        title = ""
        m_title = re.search(r'\[([^\]]+)\]\((?:https://[^\)]+)\)', block)
        if m_title:
            title = m_title.group(1).strip()
        else:
            title = f"{brand} {size}inch {mc} ({year})"
            
        category = "UHD"
        if "OLED" in mc or "OLED" in title.upper() or "OLED" in block.upper():
            category = "OLED"
        elif "MRGB" in mc or "R85" in mc or "R95" in mc:
            category = "MRGB"
        elif "QNED" in mc or "QNED" in title.upper():
            category = "QNED"
        elif "QN" in mc or "QLED" in title.upper() or "NEO" in title.upper() or "Q7" in mc or "Q8" in mc:
            category = "QLED"
            
        items.append({
            'name': title,
            'title': title,
            'model_code': mc,
            'brand': brand,
            'year': year,
            'category': category,
            'size': size,
            'price': price,
            'original_price': max(prices) if len(prices) > 1 and max(prices) > price else price,
            'promo': 'None',
            'retailer': retailer_name,
            'url': url
        })
        
    return items

def main():
    print("=" * 65)
    print(" 🇦🇺 AUSTRALIA TV RETAILERS EXPANDED SCRAPING & CLEANSING")
    print("=" * 65)
    
    retailer_dumps = {
        'jbhifi': ('JB Hi-Fi', [
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1695\output.txt', None), # OLED Page 1
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1697\output.txt', None), # OLED Page 2
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1608\output.txt', 'SAMSUNG'),
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1610\output.txt', 'LG'),
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1308\output.txt', None),
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1699\output.txt', 'SAMSUNG')
        ]),
        'goodguys': ('The Good Guys', [
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1612\output.txt', 'SAMSUNG'),
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1614\output.txt', 'LG'),
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1314\output.txt', None)
        ]),
        'harveynorman': ('Harvey Norman', [
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1616\output.txt', 'SAMSUNG'),
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1618\output.txt', 'LG'),
            (r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1320\output.txt', None)
        ])
    }
    
    total_extracted = 0
    all_registry_items = []
    
    for r_key, (r_name, dump_list) in retailer_dumps.items():
        items = []
        for dp, bh in dump_list:
            items.extend(parse_dump(dp, r_name, bh))
            
        dedup = {}
        for it in items:
            mc = it['model_code']
            if mc not in dedup or it['price'] < dedup[mc]['price']:
                dedup[mc] = it
                
        final_items = list(dedup.values())
        samsung_items = [it for it in final_items if it['brand'] == 'SAMSUNG']
        lg_items = [it for it in final_items if it['brand'] == 'LG']
        
        s_path = os.path.join(DATA_DIR, f"raw_{r_key}_samsung.json")
        l_path = os.path.join(DATA_DIR, f"raw_{r_key}_lg.json")
        
        with open(s_path, 'w', encoding='utf-8') as f:
            json.dump(samsung_items, f, ensure_ascii=False, indent=2)
            
        with open(l_path, 'w', encoding='utf-8') as f:
            json.dump(lg_items, f, ensure_ascii=False, indent=2)
            
        print(f"✅ [{r_name}] Extracted {len(samsung_items)} Samsung, {len(lg_items)} LG (Total: {len(final_items)})")
        total_extracted += len(final_items)
        all_registry_items.extend(final_items)
        
    # Build or update master_product_urls_au.json
    registry_path = os.path.join(DATA_DIR, "master_product_urls_au.json")
    master_reg = {}
    if os.path.exists(registry_path):
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                master_reg = json.load(f)
        except Exception:
            master_reg = {}
            
    added_urls = 0
    for it in all_registry_items:
        key = f"{it['retailer']}_{it['model_code']}"
        if key not in master_reg:
            master_reg[key] = {
                "retailer": it['retailer'],
                "brand": it['brand'],
                "year": it['year'],
                "category": it['category'],
                "size": it['size'],
                "model_code": it['model_code'],
                "url": it['url'],
                "last_verified": datetime.now().strftime("%Y-%m-%d")
            }
            added_urls += 1
            
    with open(registry_path, 'w', encoding='utf-8') as f:
        json.dump(master_reg, f, ensure_ascii=False, indent=2)
        
    print(f"\n📦 [AU MASTER REGISTRY] Total {len(master_reg)} registered product URLs (Added: {added_urls})")
    print(f"🎉 TOTAL EXPANDED UNIQUE MODELS ACROSS AU: {total_extracted}")

if __name__ == '__main__':
    main()
