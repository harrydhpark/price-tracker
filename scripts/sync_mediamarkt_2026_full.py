import json
import os
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")

def sync_mediamarkt_2026():
    # 1. Load extracted Samsung 2026 from step 821
    step_821_path = r"C:\Users\harry.park\.gemini\antigravity\brain\b82f4db0-4973-4a68-b5f3-be3639f9b5e9\.system_generated\steps\821\output.txt"
    with open(step_821_path, "r", encoding="utf-8") as f:
        text_s = f.read()
    m_s = re.search(r'### Result\s*(\[.*?\])\s*### Ran Playwright', text_s, re.DOTALL)
    s_items = json.loads(m_s.group(1))

    # 2. Load extracted LG 2026 from step 825
    step_825_path = r"C:\Users\harry.park\.gemini\antigravity\brain\b82f4db0-4973-4a68-b5f3-be3639f9b5e9\.system_generated\steps\825\output.txt"
    with open(step_825_path, "r", encoding="utf-8") as f:
        text_l = f.read()
    m_l = re.search(r'### Result\s*(\[.*?\])\s*### Ran Playwright', text_l, re.DOTALL)
    l_items = json.loads(m_l.group(1))

    # Add StanbyME 2
    l_items.append({
        "title": 'LG StanbyME 2 27LX6TDGA Lifestyle TV (Flat, 27 " / 68 cm, QHD, Smart TV)',
        "url": "https://www.mediamarkt.ch/de/product/_lg-stanbyme-2-27lx6tdga-lifestyle-tv-flat-27-68-cm-qhd-smart-tv-2286379.html",
        "price": 789.0,
        "cardSnippet": "StanbyME 2 27LX6TDGA"
    })

    # Parse Samsung
    samsung_2026 = []
    for item in s_items:
        title = item["title"]
        url = item["url"]
        price = item["price"]
        t_up = title.upper()
        
        sm = re.search(r'(\d+)\s*"', title)
        size = int(sm.group(1)) if sm else 55
        
        if "S90H" in t_up:
            model_code = f"QE{size}S90H"
            series = "S90H"
            category = "OLED"
        elif "S99H" in t_up:
            model_code = f"QE{size}S99H"
            series = "S99H"
            category = "OLED"
        elif "S95H" in t_up:
            model_code = f"QE{size}S95H"
            series = "S95H"
            category = "OLED"
        elif "R85H" in t_up:
            model_code = f"MRE{size}R85H"
            series = "R85H"
            category = "MRGB"
        elif "QN80H" in t_up:
            model_code = f"QE{size}QN80H"
            series = "QN80H"
            category = "Neo QLED"
        elif "M70H" in t_up:
            model_code = f"UE{size}M70H"
            series = "M70H"
            category = "Mini LED"
        elif "U8090H" in t_up:
            model_code = f"UE{size}U8090H"
            series = "U8090H"
            category = "UHD"
        elif "LS03HE" in t_up or ("THE FRAME" in t_up and "2026" in t_up):
            model_code = f"QE{size}LS03HE"
            series = "The Frame"
            category = "Lifestyle"
        else:
            continue
            
        samsung_2026.append({
            "brand": "SAMSUNG",
            "retailer": "MediaMarkt",
            "title": title,
            "model_code": model_code,
            "size": size,
            "series": series,
            "category": category,
            "year": 2026,
            "price": price,
            "original_price": price,
            "net_price": price,
            "cashback": 0.0,
            "gift": "",
            "promo_text": "",
            "url": url
        })

    # Parse LG
    lg_2026 = []
    for item in l_items:
        title = item["title"]
        url = item["url"]
        price = item["price"]
        t_up = title.upper()
        
        mc_match = re.search(r'\b(OLED\d{2}[A-Z0-9]+|\d{2}QNED[A-Z0-9]+|\d{2}MRGB[A-Z0-9]+|\d{2}LX[A-Z0-9]+)\b', t_up)
        if mc_match:
            model_code = mc_match.group(1)
        else:
            sm = re.search(r'_lg-([a-z0-9]+)', url.lower())
            if sm and any(c.isdigit() for c in sm.group(1)) and len(sm.group(1)) >= 6:
                model_code = sm.group(1).upper()
            else:
                continue
                
        size = 55
        sz_m = re.findall(r'\d+', model_code)
        if sz_m and len(sz_m[0]) in [2, 3]:
            size = int(sz_m[0])
        else:
            sm2 = re.search(r'(\d+)\s*"', title)
            if sm2: size = int(sm2.group(1))
            
        category = "UHD"
        series = "Unknown"
        if "OLED" in model_code:
            category = "OLED"
            if "W6" in model_code: series = "W6"
            elif "G6" in model_code: series = "G6"
            elif "C6" in model_code: series = "C6"
            elif "B6" in model_code: series = "B6"
        elif "MRGB" in model_code:
            category = "MRGB"
            series = "MRGB87B"
        elif "QNED" in model_code:
            category = "QNED"
            if "86B" in model_code: series = "QNED86B"
            elif "71B" in model_code: series = "QNED71B"
            elif "70B" in model_code: series = "QNED70B"
        elif "LX" in model_code:
            category = "Lifestyle"
            if "LX7" in model_code: series = "LX7B"
            elif "LX6" in model_code: series = "StanbyME 2"

        lg_2026.append({
            "brand": "LG",
            "retailer": "MediaMarkt",
            "title": title,
            "model_code": model_code,
            "size": size,
            "series": series,
            "category": category,
            "year": 2026,
            "price": price,
            "original_price": price,
            "net_price": price,
            "cashback": 0.0,
            "gift": "",
            "promo_text": "",
            "url": url
        })

    print(f"[PARSED] Samsung 2026: {len(samsung_2026)} models, LG 2026: {len(lg_2026)} models")

    # 3. Merge with existing raw files (preserving 2025 models)
    raw_s_file = os.path.join(DATA_DIR, "raw_mediamarkt_samsung.json")
    with open(raw_s_file, "r", encoding="utf-8") as f:
        existing_s = json.load(f)
    # Keep 2025 models
    merged_s = [p for p in existing_s if p.get("year") != 2026]
    # Add new 2026 models
    merged_s.extend(samsung_2026)
    with open(raw_s_file, "w", encoding="utf-8") as f:
        json.dump(merged_s, f, ensure_ascii=False, indent=2)
    print(f"[SAVED] raw_mediamarkt_samsung.json total: {len(merged_s)} (2026 models: {len(samsung_2026)})")

    raw_l_file = os.path.join(DATA_DIR, "raw_mediamarkt_lg.json")
    with open(raw_l_file, "r", encoding="utf-8") as f:
        existing_l = json.load(f)
    # Keep 2025 models
    merged_l = [p for p in existing_l if p.get("year") != 2026]
    # Add new 2026 models
    merged_l.extend(lg_2026)
    with open(raw_l_file, "w", encoding="utf-8") as f:
        json.dump(merged_l, f, ensure_ascii=False, indent=2)
    print(f"[SAVED] raw_mediamarkt_lg.json total: {len(merged_l)} (2026 models: {len(lg_2026)})")

    # 4. Update data/master_product_urls.json
    master_file = os.path.join(DATA_DIR, "master_product_urls.json")
    if os.path.exists(master_file):
        with open(master_file, "r", encoding="utf-8") as f:
            master = json.load(f)
    else:
        master = {}

    added_master = 0
    for p in samsung_2026 + lg_2026:
        key = f"CH_MediaMarkt_{p['brand']}_{p['model_code']}"
        master[key] = {
            "country": "CH",
            "retailer": "MediaMarkt",
            "brand": p["brand"],
            "model_code": p["model_code"],
            "year": 2026,
            "size": p["size"],
            "title": p["title"],
            "url": p["url"],
            "last_updated": "2026-09-03"
        }
        added_master += 1

    with open(master_file, "w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)
    print(f"[SAVED] master_product_urls.json updated with {added_master} 2026 MediaMarkt entries.")

if __name__ == "__main__":
    sync_mediamarkt_2026()
