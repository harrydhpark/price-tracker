# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
HISTORY_EU_DIR = os.path.join(ROOT_DIR, 'History_EU')
PROBE_RESULTS_PATH = os.path.join(DATA_DIR, 'live_pdp_probed_models.json')
EU_FILE = os.path.join(DATA_DIR, 'price tracker_EU_2026 0915_v1.xlsx')

def clean_model_code_from_url_and_text(brand, raw_code, url, size_val):
    url_lower = url.lower()
    
    # 1. Currys White fix
    if brand.lower() == 'samsung' and (raw_code == 'WHITE' or 'movingstyle' in url_lower):
        m = re.search(r'(ue\d{2}[a-z0-9]+)', url_lower)
        if m:
            return m.group(1).upper()
        return f'UE{size_val}LSM7FA'

    # 2. Public GR URL slug extraction
    slug_match = re.search(r'/([a-z0-9\-]+)/\d+$', url_lower)
    if slug_match:
        slug = slug_match.group(1)
        # Check standard LG patterns in slug
        # e.g. oled65c55la, 55nano81a6a, 50qned72b6b, 65mrgb87b6b, 100mrgb96b6
        lg_m = re.search(r'(oled\d{2}[a-z0-9]+|\d{2,3}(?:nano|qned|mrgb|nu|ua|lx)\w+)', slug)
        if lg_m:
            return lg_m.group(1).upper()
            
        sam_m = re.search(r'([qum]\w*\d{2}[a-z0-9]+|\b\d{2}[sm]\d{2}[a-z0-9]*)', slug)
        if sam_m:
            c = sam_m.group(1).upper()
            if not c.startswith(('QE', 'UE', 'MRE')) and len(c) >= 5:
                if c[2:].startswith(('M7', 'U8')):
                    c = f'UE{c}'
                else:
                    c = f'QE{c}'
            return c

    # Fallback to existing raw_code with prefix cleanup if truncated
    if raw_code.startswith('ED') and len(raw_code) >= 6:
        # e.g. ED72B6B -> QNED72B6B
        return f'{size_val}QN' + raw_code
    elif raw_code.startswith('NO') and len(raw_code) >= 6:
        return f'{size_val}NA' + raw_code
    elif raw_code.startswith('GB') and len(raw_code) >= 5:
        return f'{size_val}MR' + raw_code

    return raw_code

def run():
    with open(PROBE_RESULTS_PATH, 'r', encoding='utf-8') as f:
        items = json.load(f)

    wb_eu = openpyxl.load_workbook(EU_FILE)
    
    replenished = []
    added_counts = {}

    for item in items:
        s_name = item['sheet']
        if s_name not in wb_eu.sheetnames:
            continue
            
        ws = wb_eu[s_name]
        brand = item['brand']
        raw_code = item['model_code']
        url = item['url']
        size_val = item['size']
        probed_price = item['probed_price']
        probed_orig_price = item.get('probed_orig_price')
        row_prev = list(item['row_prev'])

        # Clean model code
        clean_code = clean_model_code_from_url_and_text(brand, raw_code, url, size_val)
        
        # Check if already present in today's sheet
        header = [str(c).strip().lower() if c else '' for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
        code_idx = 4
        price_idx = 5
        orig_price_idx = 6
        for idx, h in enumerate(header):
            if any(x in h for x in ['model code', 'model_code', 'code']):
                code_idx = idx
            elif any(x in h for x in ['selling price', 'price (', 'price(']):
                price_idx = idx
            elif any(x in h for x in ['was price', 'original price']):
                orig_price_idx = idx

        existing_codes = set(str(r[code_idx]).strip().upper() for r in ws.iter_rows(min_row=2, values_only=True) if r and len(r) > code_idx and r[code_idx])
        if clean_code in existing_codes:
            print(f'Skipping already present code: {clean_code} in {s_name}')
            continue

        # Prepare row
        new_row = list(row_prev)
        if len(new_row) > code_idx:
            new_row[code_idx] = clean_code
        if len(new_row) > price_idx:
            new_row[price_idx] = probed_price
        if probed_orig_price and len(new_row) > orig_price_idx:
            new_row[orig_price_idx] = probed_orig_price

        ws.append(new_row)
        added_counts[s_name] = added_counts.get(s_name, 0) + 1
        replenished.append((s_name, clean_code, size_val, probed_price))

    wb_eu.save(EU_FILE)
    print(f'\n=== Replenishment Complete ===')
    print(f'Workbook saved: {EU_FILE}')
    for s, count in added_counts.items():
        print(f'  + {s}: {count} models replenished')
    print(f'Total uniquely replenished: {len(replenished)}')
    for s, c, sz, p in replenished:
        print(f'   -> [{s}] {c} ({sz}in): {p}')

    # Auto mirror to History_EU
    hist_dest = os.path.join(HISTORY_EU_DIR, '2026 0915', 'price tracker_EU_2026 0915_v1.xlsx')
    if os.path.exists(os.path.dirname(hist_dest)):
        import shutil
        shutil.copy2(EU_FILE, hist_dest)
        print(f'\nHistory mirrored to: {hist_dest}')

if __name__ == '__main__':
    run()
