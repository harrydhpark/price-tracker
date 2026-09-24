import os
import sys
import io
import json
import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT_DIR = r"d:\TV 유럽영업\15. AX Task\2026 AX 실행과제\04. Price Tracker"
DATA_DIR = os.path.join(ROOT_DIR, 'data')

# 1. Load master 2026 models
master_path = os.path.join(DATA_DIR, 'master_product_urls.json')
with open(master_path, 'r', encoding='utf-8') as f:
    master = json.load(f)

master_2026 = {k: v for k, v in master.items() if v.get('year') == 2026}
print(f"Total Master 2026 models: {len(master_2026)}")

# 2. Load today's EU workbook models
wb_eu_path = os.path.join(DATA_DIR, 'price tracker_EU_2026 0924_v1.xlsx')
wb_eu = openpyxl.load_workbook(wb_eu_path, read_only=True)

eu_models_by_country = {}
for sheet in wb_eu.sheetnames:
    ws = wb_eu[sheet]
    rows = list(ws.iter_rows(values_only=True))
    if not rows: continue
    headers = [str(h).lower() if h else '' for h in rows[0]]
    code_idx = -1
    year_idx = -1
    for i, h in enumerate(headers):
        if 'code' in h or 'model' in h and 'year' not in h:
            code_idx = i
        if 'year' in h:
            year_idx = i
    
    # derive country/retailer from sheet name
    parts = sheet.split('_')
    ret = parts[0]
    ctry = parts[1] if len(parts) > 1 and len(parts[1]) == 2 else 'EU'
    # Check sheet mapping
    for r in rows[1:]:
        if len(r) > max(code_idx, year_idx):
            code = str(r[code_idx]).strip() if code_idx != -1 else ''
            yr = r[year_idx] if year_idx != -1 else None
            if code and (yr == 2026 or '2026' in str(yr)):
                eu_models_by_country[f"{sheet}_{code}"] = code

# Also Swiss workbook
wb_ch_path = os.path.join(DATA_DIR, 'price tracker_swiss_2026 0924_v1.xlsx')
if os.path.exists(wb_ch_path):
    wb_ch = openpyxl.load_workbook(wb_ch_path, read_only=True)
    for sheet in wb_ch.sheetnames:
        ws = wb_ch[sheet]
        rows = list(ws.iter_rows(values_only=True))
        if not rows: continue
        headers = [str(h).lower() if h else '' for h in rows[0]]
        code_idx = 4 if len(headers) > 4 else -1
        year_idx = 1 if len(headers) > 1 else -1
        for r in rows[1:]:
            if len(r) > max(code_idx, year_idx):
                code = str(r[code_idx]).strip()
                yr = r[year_idx]
                if code and (yr == 2026 or '2026' in str(yr)):
                    eu_models_by_country[f"CH_{sheet}_{code}"] = code

print(f"Total 2026 surveyed models active today: {len(eu_models_by_country)}")

# Compare per country
by_country_missing = {}
for k, v in master_2026.items():
    ctry = v.get('country')
    ret = v.get('retailer')
    code = v.get('model_code')
    found = False
    for active_k in eu_models_by_country:
        if code.lower() in active_k.lower() or active_k.lower().endswith(f"_{code.lower()}"):
            found = True
            break
    if not found:
        by_country_missing.setdefault(f"{ctry} ({ret})", []).append(v)

print("\n--- Missing 2026 models by Country/Retailer ---")
for cr, items in sorted(by_country_missing.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"{cr}: {len(items)} models missing")
    for it in items[:3]:
        print(f"   - {it.get('brand')} {it.get('model_code')} ({it.get('size')}\") -> {it.get('url')}")
