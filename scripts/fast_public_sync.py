# -*- coding: utf-8 -*-
import os
import sys
import io
import json
import re
import openpyxl
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')

def parse_price(price_str):
    if not price_str:
        return 0.0
    cleaned = str(price_str).replace('€', '').replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
    if not cleaned:
        return 0.0
    if ',' in cleaned and '.' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        val = float(cleaned)
        return val if val >= 50.0 else 0.0
    except ValueError:
        return 0.0

def extract_model_code_and_info(title_upper, brand, href):
    year_val = None
    series_code = "Unknown"
    model_code = "Unknown"
    size_val = 0

    url_str = str(href or '').lower()

    # Exclude hotel TV, signage, commercial monitors
    if any(x in url_str for x in ['hotel-tv', 'signage', 'pro-centric', 'othoni']):
        return None

    # 1. Size from URL slug
    m_url = re.search(r'-(24|27|32|40|42|43|48|50|55|65|70|75|77|83|85|86|98|100|115)-(?:4k|oled|qled|smart|full-hd|led|qned|micro|ultra)', url_str)
    if m_url:
        size_val = int(m_url.group(1))

    # 2. Size from title
    if not size_val:
        m_size = re.search(r'\b(24|27|32|40|42|43|48|50|55|65|70|75|77|83|85|86|98|100|115)[\"\”\s]*(?:4K|Smart|OLED|QLED|LED|QNED|Nano|Mini|Micro|Inch|\'\'|\")', title_upper)
        if m_size:
            try:
                size_val = int(m_size.group(1))
            except ValueError:
                size_val = 0
            
    if size_val < 22:
        return None

    if brand.lower() == "samsung":
        patterns_2026 = [
            (r'S99H', 'S99H', 2026), (r'S95H', 'S95H', 2026), (r'S90H', 'S90H', 2026), (r'S85H', 'S85H', 2026),
            (r'QN95H', 'QN95H', 2026), (r'QN90H', 'QN90H', 2026), (r'QN85H', 'QN85H', 2026),
            (r'QN80H', 'QN80H', 2026), (r'QN70H', 'QN70H', 2026), (r'M80H', 'M80H', 2026),
            (r'M70H', 'M70H', 2026), (r'R95H', 'R95H', 2026), (r'R86H', 'R86H', 2026), (r'R85H', 'R85H', 2026),
            (r'U8072H', 'U8000H', 2026), (r'U8070H', 'U8000H', 2026), (r'U8092H', 'U8000H', 2026),
            (r'U8072', 'U8000H', 2026), (r'U8092', 'U8000H', 2026), (r'U8000H', 'U8000H', 2026),
            (r'LS03HW', 'The Frame Pro', 2026), (r'LS03H', 'The Frame', 2026), (r'F6000H', 'F6000H', 2026)
        ]
        patterns_2025 = [
            (r'S95F', 'S95F', 2025), (r'S90F', 'S90F', 2025), (r'S85F', 'S85F', 2025),
            (r'QN95F', 'QN95F', 2025), (r'QN90F', 'QN90F', 2025), (r'QN85F', 'QN85F', 2025),
            (r'QN80F', 'QN80F', 2025), (r'QN70F', 'QN70F', 2025), (r'Q80F', 'Q8F', 2025),
            (r'Q8F', 'Q8F', 2025), (r'Q70F', 'Q7F', 2025), (r'Q7F', 'Q7F', 2025),
            (r'Q60F', 'Q6F', 2025), (r'Q6F', 'Q6F', 2025), (r'U8072F', 'U8000F', 2025), (r'U8000F', 'U8000F', 2025),
            (r'LS03F', 'The Frame', 2025), (r'MR95F', 'MR95F', 2025)
        ]

        slug_m = re.search(r'-(\d{2,3}[a-z]{1,4}\d{2,4}[a-z0-9]*)(?:-ai|-tv|/|\b)', url_str)
        if slug_m:
            model_code = slug_m.group(1).upper()
        else:
            m_code = re.search(r'([A-Z]{2}\d{2}[A-Z0-9]+|\b\d{2}[A-Z]{1,3}\d{2,3}[A-Z0-9]*\b)', title_upper)
            if m_code:
                model_code = m_code.group(1)

        for pat, ser, yr in patterns_2026:
            if re.search(pat, title_upper) or re.search(pat, model_code):
                series_code = ser
                year_val = yr
                break

        if not year_val:
            for pat, ser, yr in patterns_2025:
                if re.search(pat, title_upper) or re.search(pat, model_code):
                    series_code = ser
                    year_val = yr
                    break

        if not year_val:
            if "2026" in title_upper or ("AI TV" in title_upper and any(x in title_upper for x in ["H ", "H\b", "95H", "90H", "85H", "80H", "70H", "M80H", "M70H"])):
                year_val = 2026
            elif "2025" in title_upper:
                year_val = 2025

    elif brand.lower() == "lg":
        lg_2026 = [
            (r'QNED93B', 'QNED93B', 2026), (r'QNED87B', 'QNED87B', 2026), (r'QNED86B', 'QNED86B', 2026),
            (r'QNED85B', 'QNED85B', 2026), (r'QNED83B', 'QNED81B', 2026), (r'QNED82B', 'QNED82B', 2026),
            (r'QNED81B', 'QNED81B', 2026), (r'QNED80B', 'QNED80B', 2026),
            (r'QNED72B', 'QNED72B', 2026), (r'QNED71B', 'QNED70B', 2026), (r'QNED70B', 'QNED70B', 2026),
            (r'QNED7EB', 'QNED7EB', 2026),
            (r'MRGB96B', 'MRGB96B', 2026), (r'MRGB88B', 'MRGB88B', 2026),
            (r'MRGB87B', 'MRGB87B', 2026), (r'MRGB86B', 'MRGB86B', 2026), (r'MRGB85B', 'MRGB85B', 2026),
            (r'LX7B', 'LX7B', 2026), (r'LX6', 'LX6', 2026), (r'27LX6', '27LX6', 2026), (r'STANBYME', 'STANBYME', 2026),
            (r'OLED\d{2}G6', 'OLED G6', 2026), (r'G6[0-9]L', 'OLED G6', 2026), (r'G6[0-9]', 'OLED G6', 2026),
            (r'OLED\d{2}C6', 'OLED C6', 2026), (r'C6[0-9]L', 'OLED C6', 2026), (r'C6[0-9]', 'OLED C6', 2026),
            (r'OLED\d{2}B6', 'OLED B6', 2026), (r'B6[0-9]L', 'OLED B6', 2026), (r'B6[0-9]', 'OLED B6', 2026),
            (r'OLED\d{2}W6', 'OLED W6', 2026), (r'W6[0-9]L', 'OLED W6', 2026),
            (r'NU90', 'NU90', 2026), (r'NU85', 'NU85', 2026), (r'NU8E', 'NU85', 2026),
            (r'UA77', 'UA77', 2026), (r'LB650B', 'LB650B', 2026)
        ]
        lg_2025 = [
            (r'QNED93A', 'QNED93A', 2025),
            (r'QNED87A', 'QNED86A', 2025), (r'QNED86A', 'QNED86A', 2025), (r'QNED85A', 'QNED86A', 2025),
            (r'QNED84A', 'QNED80A', 2025), (r'QNED83A', 'QNED80A', 2025), (r'QNED82A', 'QNED80A', 2025),
            (r'QNED80A', 'QNED80A', 2025), (r'QNED8EA', 'QNED8EA', 2025),
            (r'QNED70A', 'QNED70A', 2025),
            (r'NANO90A', 'NANO90A', 2025), (r'NANO81A', 'NANO81A', 2025), (r'NANO80A', 'NANO80A', 2025),
            (r'OLED\d{2}G5', 'OLED G5', 2025), (r'G5[0-9]L', 'OLED G5', 2025), (r'G5[0-9]', 'OLED G5', 2025),
            (r'OLED\d{2}C5', 'OLED C5', 2025), (r'C5[0-9]L', 'OLED C5', 2025), (r'C5[0-9]', 'OLED C5', 2025),
            (r'OLED\d{2}B5', 'OLED B5', 2025), (r'B5[0-9]L', 'OLED B5', 2025), (r'B5[0-9]', 'OLED B5', 2025),
            (r'UA75', 'UA75', 2025), (r'UA74', 'UA75', 2025), (r'UA73', 'UA75', 2025),
            (r'LR60', 'LR60', 2025)
        ]

        # 1. Extract LG code from slug: e.g. tileorasi-100mrgb96b6-ai -> 100MRGB96B6
        slug_m = re.search(r'tileorasi-([a-z0-9]+)(?:-ai|-tv|/|$)', url_str)
        if slug_m and slug_m.group(1).lower() != 'tileorasi':
            model_code = slug_m.group(1).upper()
        else:
            # 2025 consumer OLED slug: e.g. -2025-oled77g55lw/
            slug_m2 = re.search(r'-(oled\d{2}[a-z0-9]+)/', url_str)
            if slug_m2:
                model_code = slug_m2.group(1).upper()
            else:
                m_code = re.search(r'([A-Z0-9]{2,4}\d{2}[A-Z0-9]+|\b\d{2}[A-Z0-9]{5,10}\b|\bOLED\d{2}[A-Z0-9]+\b)', title_upper)
                if m_code:
                    model_code = m_code.group(1)

        for pat, ser, yr in lg_2026:
            if re.search(pat, title_upper) or re.search(pat, model_code):
                series_code = ser
                year_val = yr
                break

        if not year_val:
            for pat, ser, yr in lg_2025:
                if re.search(pat, title_upper) or re.search(pat, model_code):
                    series_code = ser
                    year_val = yr
                    break

        if not year_val:
            if "2026" in title_upper:
                year_val = 2026
            elif "2025" in title_upper:
                year_val = 2025

    if not year_val:
        return None

    disp_type = "UHD 4K"
    if "OLED" in series_code.upper() or "OLED" in title_upper or "OLED" in model_code:
        disp_type = "OLED"
    elif "MRGB" in series_code.upper() or "MICRO RGB" in title_upper or "MR" in series_code.upper() or "MINI RGB" in title_upper:
        disp_type = "MRGB"
    elif "QNED" in series_code.upper() or "QNED" in title_upper:
        disp_type = "QNED/QLED"
    elif any(x in series_code.upper() or x in title_upper for x in ["QLED", "NEO QLED", "MINI LED", "Q8", "Q7", "QN", "M80", "M70"]):
        disp_type = "QNED/QLED"

    return {
        "brand": brand.upper(),
        "title": title_upper,
        "series": series_code,
        "model_code": model_code,
        "size": size_val,
        "year": year_val,
        "display_type": disp_type
    }

def process_all_cards(cards):
    seen_sec = {}
    seen_lg = {}

    for c in cards:
        href = c.get('url') or c.get('href') or ''
        title = c.get('title') or ''
        snippet = c.get('snippet') or ''
        price_raw = c.get('price_raw') or ''
        text = c.get('text') or f"{title} {snippet} {price_raw}"
        text_clean = text.replace('\n', ' ')
        title_upper = text_clean.upper()

        url_lower = href.lower()
        if '/lg-' in url_lower or '/tileoraseis/lg-' in url_lower:
            brand = 'LG'
        elif '/samsung-' in url_lower or '/tileoraseis/samsung-' in url_lower:
            brand = 'Samsung'
        else:
            text_no_sp = re.sub(r'SAMSUNG\s+PAY', '', title_upper)
            if 'LG' in text_no_sp and 'SAMSUNG' not in text_no_sp:
                brand = 'LG'
            elif 'SAMSUNG' in text_no_sp:
                brand = 'Samsung'
            else:
                continue

        info = extract_model_code_and_info(title_upper, brand, href)
        if not info:
            continue

        clean_text = re.sub(r'(?:Κέρδος|Έκπτωση|όφελος|Δωροεπιταγή|Δώρο|από|-\s*)\s*\d[\d\.\s]*[,\.]\d{2}\s*€', '', text_clean, flags=re.IGNORECASE)
        prices = re.findall(r'(\d[\d\.\s]*[,\.]\d{2})\s*€', clean_text)
        if not prices:
            prices = re.findall(r'(\d[\d\.\s]*[,\.]\d{2})\s*€', text_clean)

        parsed_prices = [parse_price(p) for p in prices if parse_price(p) >= 80.0]
        if not parsed_prices:
            continue

        selling_price = min(parsed_prices)
        orig_price = max(parsed_prices) if len(parsed_prices) > 1 else selling_price

        size_val = info['size']
        disp = info['display_type']
        if disp == 'OLED':
            if size_val >= 83 and selling_price < 1200: continue
            elif size_val >= 77 and selling_price < 1000: continue
            elif size_val >= 65 and selling_price < 750: continue
            elif size_val >= 55 and selling_price < 550: continue
            elif selling_price < 350: continue
        elif disp == 'MRGB':
            if size_val >= 75 and selling_price < 1000: continue
            elif selling_price < 500: continue
        elif disp == 'QNED/QLED':
            if size_val >= 75 and selling_price < 500: continue
            elif size_val >= 55 and selling_price < 300: continue
            elif selling_price < 180: continue
        else:
            if size_val >= 70 and selling_price < 350: continue
            elif selling_price < 100: continue

        cashback = 0
        cb_m = re.findall(r'(\d+)\s*€\s*Public\s*επιστροφή', text_clean, re.I)
        if cb_m:
            cashback = int(cb_m[0])

        item = {
            'brand': brand.upper(),
            'year': info['year'],
            'display_type': disp,
            'size': size_val,
            'model_code': info['model_code'],
            'price': selling_price,
            'original_price': orig_price,
            'series': info['series'],
            'cashback': cashback,
            'promotion': f"Snappi Cashback: {cashback}€" if cashback else "None",
            'url': href,
            'title': text_clean[:120]
        }

        code_key = info['model_code']
        if brand.upper() == 'SAMSUNG':
            if code_key not in seen_sec or seen_sec[code_key]['price'] > selling_price:
                seen_sec[code_key] = item
        else:
            if code_key not in seen_lg or seen_lg[code_key]['price'] > selling_price:
                seen_lg[code_key] = item

    return list(seen_sec.values()), list(seen_lg.values())

def load_cards_from_step(step_num):
    path = f'C:/Users/harry.park/.gemini/antigravity/brain/3ab78781-4c94-4dca-b46c-0d714af4d29e/.system_generated/steps/{step_num}/output.txt'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    idx = text.rfind('Result')
    json_start = text.find('{', idx)
    data, _ = json.JSONDecoder().raw_decode(text[json_start:])
    return data.get('cards', [])

def main():
    print("Loading Public.gr live extracted cards...")
    s_cards = load_cards_from_step(2571)
    l_cards = load_cards_from_step(2576)
    all_cards = s_cards + l_cards
    print(f"Total raw cards loaded: {len(all_cards)} (Samsung: {len(s_cards)}, LG: {len(l_cards)})")

    sec_items, lg_items = process_all_cards(all_cards)
    print(f"Processed into unique models: {len(sec_items)} Samsung, {len(lg_items)} LG models.")

    sec_2026 = [x for x in sec_items if x['year'] == 2026]
    lg_2026 = [x for x in lg_items if x['year'] == 2026]
    print(f"  -> Samsung 2026: {len(sec_2026)} models, 2025: {len(sec_items)-len(sec_2026)} models")
    print(f"  -> LG 2026: {len(lg_2026)} models, 2025: {len(lg_items)-len(lg_2026)} models")

    # Save clean json
    with open(os.path.join(DATA_DIR, 'raw_public_gr_samsung.json'), 'w', encoding='utf-8') as f:
        json.dump(sec_items, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_DIR, 'raw_public_gr_lg.json'), 'w', encoding='utf-8') as f:
        json.dump(lg_items, f, ensure_ascii=False, indent=2)
    print("Saved clean raw_public_gr_*.json files.")

    # Update today's Excel workbook
    target_wb = os.path.join(DATA_DIR, 'price tracker_EU_2026 0924_v1.xlsx')
    wb = openpyxl.load_workbook(target_wb)

    sheets_config = [
        ("Public_GR_Samsung", sec_items),
        ("Public_GR_LG", lg_items)
    ]

    headers = [
        "Brand", "Model Year", "Display Type", "Size (Inch)", "Model Code",
        "Price (EUR)", "Original Price (EUR)", "Series", "Cashback", "General Promotions",
        "URL", "Title"
    ]

    for sheet_name, items in sheets_config:
        if sheet_name in wb.sheetnames:
            del wb[sheet_name]
        ws = wb.create_sheet(title=sheet_name)
        ws.append(headers)
        for it in items:
            ws.append([
                it["brand"], it["year"], it["display_type"], it["size"], it["model_code"],
                it["price"], it["original_price"], it["series"], it["cashback"], it["promotion"],
                it["url"], it["title"]
            ])

    wb.save(target_wb)
    print(f"Updated {target_wb} with {len(sec_items)} Samsung and {len(lg_items)} LG rows!")

    # Auto-register newly verified URLs into Master Registry
    master_path = os.path.join(DATA_DIR, 'master_product_urls.json')
    with open(master_path, 'r', encoding='utf-8') as f:
        master = json.load(f)

    added_count = 0
    for it in sec_items + lg_items:
        key = f"GR_Public_{it['model_code']}"
        if key not in master:
            master[key] = {
                "country": "GR",
                "retailer": "Public",
                "brand": it["brand"],
                "model_code": it["model_code"],
                "year": it["year"],
                "size": it["size"],
                "title": it["title"],
                "url": it["url"],
                "last_updated": "2026-09-24"
            }
            added_count += 1

    if added_count > 0:
        with open(master_path, 'w', encoding='utf-8') as f:
            json.dump(master, f, ensure_ascii=False, indent=2)
        print(f"Registered {added_count} new Public.gr products into {master_path}.")

if __name__ == '__main__':
    main()
