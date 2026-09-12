# -*- coding: utf-8 -*-
import os, sys, json, glob, openpyxl
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

DATA_DIR = os.path.abspath('data')
candidates = glob.glob(os.path.join(DATA_DIR, 'price tracker_EU_2026 0912*.xlsx'))
if not candidates:
    candidates = glob.glob(os.path.join(DATA_DIR, 'price tracker_EU_2026 *.xlsx'))
target_wb = sorted(candidates)[-1]

print(f"Target workbook: {target_wb}")

# 1. Alza Czech Republic
from scripts.scrape_alza import update_eu_excel_tracker
with open(os.path.join(DATA_DIR, 'raw_alza_lg.json'), 'r', encoding='utf-8') as f:
    alza_lg = json.load(f)
with open(os.path.join(DATA_DIR, 'raw_alza_samsung.json'), 'r', encoding='utf-8') as f:
    alza_samsung = json.load(f)

update_eu_excel_tracker(alza_lg, alza_samsung)
print("✅ Alza Czech Republic synced to Excel.")

# 2. Public Greece
with open(os.path.join(DATA_DIR, 'raw_public_gr_samsung.json'), 'r', encoding='utf-8') as f:
    gr_samsung = json.load(f)
with open(os.path.join(DATA_DIR, 'raw_public_gr_lg.json'), 'r', encoding='utf-8') as f:
    gr_lg = json.load(f)

wb = openpyxl.load_workbook(target_wb)
sheets_config = [
    ("Public_GR_Samsung", gr_samsung),
    ("Public_GR_LG", gr_lg)
]

for sheet_name, items in sheets_config:
    if sheet_name in wb.sheetnames:
        del wb[sheet_name]
    ws = wb.create_sheet(title=sheet_name)
    headers = [
        "Brand", "Model Year", "Display Type", "Size (Inch)", "Model Code",
        "Price (EUR)", "Original Price (EUR)", "Series", "Cashback", "General Promotions",
        "URL", "Title"
    ]
    ws.append(headers)
    for it in items:
        ws.append([
            it.get("brand", "Samsung" if "Samsung" in sheet_name else "LG"),
            it.get("year", 2025),
            it.get("display_type") or it.get("display", "LED"),
            it.get("size", 55),
            it.get("model_code", "Unknown"),
            it.get("price", 0.0),
            it.get("original_price") or it.get("price", 0.0),
            it.get("series", "Unknown"),
            it.get("cashback", 0),
            it.get("promotion") or it.get("promo", "None"),
            it.get("url") or it.get("link", ""),
            it.get("title", "")
        ])

wb.save(target_wb)
wb.close()
print("✅ Public Greece synced to Excel.")

# 3. Hungary MediaMarkt
from scripts.scrape_and_sync_hungary import write_standard_sheet
with open(os.path.join(DATA_DIR, 'raw_mediamarkt_hu_deep.json'), 'r', encoding='utf-8') as f:
    hu_raw = json.load(f)

if isinstance(hu_raw, dict):
    all_items = []
    for b, lst in hu_raw.items():
        if isinstance(lst, list):
            for x in lst:
                if isinstance(x, dict):
                    x['brand'] = b.capitalize()
                    all_items.append(x)
    hu_raw = all_items

clean_sec = []
clean_lg = []
for it in hu_raw:
    p_huf = it.get('price', 0.0)
    p_eur = round(p_huf / 398.0, 2)
    rec = {
        "Brand": it.get('brand', 'Samsung'),
        "Model Year": it.get('year', 2025),
        "Series": it.get('display', 'Standard'),
        "Size (inch)": it.get('size', 55),
        "Model Code": it.get('model_code', 'Unknown'),
        "Selling Price (HUF)": p_huf,
        "Selling Price (EUR)": p_eur,
        "Was Price (HUF)": it.get('was_price', p_huf),
        "Discount (%)": it.get('discount_pct', 0.0),
        "Promotion": it.get('promo', 'Standard'),
        "Cashback (HUF)": it.get('cashback', 0),
        "Product Link": it.get('link', ''),
        "Title": it.get('title', '')
    }
    if str(it.get('brand', '')).lower() == 'samsung':
        clean_sec.append(rec)
    else:
        clean_lg.append(rec)

wb = openpyxl.load_workbook(target_wb)
for sname in ["MediaMarkt_HU_Samsung", "MediaMarkt_HU_LG"]:
    if sname in wb.sheetnames:
        del wb[sname]

ws_sec = wb.create_sheet(title="MediaMarkt_HU_Samsung")
write_standard_sheet(ws_sec, clean_sec, "MediaMarkt_HU_Samsung")

ws_lg = wb.create_sheet(title="MediaMarkt_HU_LG")
write_standard_sheet(ws_lg, clean_lg, "MediaMarkt_HU_LG")

wb.save(target_wb)
wb.close()
print(f"✅ MediaMarkt Hungary synced to Excel ({len(clean_sec)} Samsung, {len(clean_lg)} LG).")

# Mirror to History_EU
hist_dir = os.path.join('History_EU', '2026 0912')
os.makedirs(hist_dir, exist_ok=True)
import shutil
shutil.copy2(target_wb, os.path.join(hist_dir, os.path.basename(target_wb)))
print(f"✅ Mirrored complete 22-sheet workbook to {os.path.join(hist_dir, os.path.basename(target_wb))}.")
