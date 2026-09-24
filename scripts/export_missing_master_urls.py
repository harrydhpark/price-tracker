import os
import json
import openpyxl

DATA_DIR = os.path.abspath('data')
print("Loading master_product_urls.json...", flush=True)
with open(os.path.join(DATA_DIR, 'master_product_urls.json'), 'r', encoding='utf-8') as f:
    master = json.load(f)
print(f"Master loaded: {len(master)} entries", flush=True)

# Load today's EU and Swiss workbooks
print("Loading EU workbook...", flush=True)
wb_eu = openpyxl.load_workbook(os.path.join(DATA_DIR, 'price tracker_EU_2026 0924_v1.xlsx'), data_only=True, read_only=True)
print("Loading CH workbook...", flush=True)
wb_ch = openpyxl.load_workbook(os.path.join(DATA_DIR, 'price tracker_swiss_2026 0924_v1.xlsx'), data_only=True, read_only=True)
print("Workbooks loaded.", flush=True)

sheet_map_eu = {
    'Currys_UK_SAMSUNG_Full': ('UK', 'Currys', 'SAMSUNG'),
    'Currys_UK_LG_Full': ('UK', 'Currys', 'LG'),
    'MediaMarkt_DE_SAMSUNG_Full': ('DE', 'MediaMarkt', 'SAMSUNG'),
    'MediaMarkt_DE_LG_Full': ('DE', 'MediaMarkt', 'LG'),
    'MediaMarkt_AT_SAMSUNG_Full': ('AT', 'MediaMarkt', 'SAMSUNG'),
    'MediaMarkt_AT_LG_Full': ('AT', 'MediaMarkt', 'LG'),
    'MediaMarkt_ES_SAMSUNG_Full': ('ES', 'MediaMarkt', 'SAMSUNG'),
    'MediaMarkt_ES_LG_Full': ('ES', 'MediaMarkt', 'LG'),
    'MediaMarkt_NL_SAMSUNG_Full': ('NL', 'MediaMarkt', 'SAMSUNG'),
    'MediaMarkt_NL_LG_Full': ('NL', 'MediaMarkt', 'LG'),
    'MediaWorld_IT_SAMSUNG_Full': ('IT', 'MediaWorld', 'SAMSUNG'),
    'MediaWorld_IT_LG_Full': ('IT', 'MediaWorld', 'LG'),
    'Fnac_FR_SAMSUNG_Full': ('FR', 'Fnac', 'SAMSUNG'),
    'Fnac_FR_LG_Full': ('FR', 'Fnac', 'LG'),
    'Alza_CZ_Samsung': ('CZ', 'Alza', 'SAMSUNG'),
    'Alza_CZ_LG': ('CZ', 'Alza', 'LG'),
    'Public_GR_Samsung': ('GR', 'Public', 'SAMSUNG'),
    'Public_GR_LG': ('GR', 'Public', 'LG'),
    'MediaMarkt_HU_Samsung': ('HU', 'MediaMarkt', 'SAMSUNG'),
    'MediaMarkt_HU_LG': ('HU', 'MediaMarkt', 'LG'),
    'MediaExpert_PL_Samsung': ('PL', 'MediaExpert', 'SAMSUNG'),
    'MediaExpert_PL_LG': ('PL', 'MediaExpert', 'LG'),
    'Worten_PT_Samsung': ('PT', 'Worten', 'SAMSUNG'),
    'Worten_PT_LG': ('PT', 'Worten', 'LG'),
    'Altex_RO_Samsung': ('RO', 'Altex', 'SAMSUNG'),
    'Altex_RO_LG': ('RO', 'Altex', 'LG'),
    'Elgiganten_SE_Samsung': ('SE', 'Elgiganten', 'SAMSUNG'),
    'Elgiganten_SE_LG': ('SE', 'Elgiganten', 'LG'),
    'MediaMarkt_CH_SAMSUNG_Full': ('CH', 'MediaMarkt', 'SAMSUNG'),
    'MediaMarkt_CH_LG_Full': ('CH', 'MediaMarkt', 'LG')
}

sheet_map_ch = {
    'MediaMarkt_Samsung_Full': ('CH', 'MediaMarkt', 'SAMSUNG'),
    'MediaMarkt_LG_Full': ('CH', 'MediaMarkt', 'LG'),
    'Interdiscount_Samsung_Full': ('CH', 'Interdiscount', 'SAMSUNG'),
    'Interdiscount_LG_Full': ('CH', 'Interdiscount', 'LG'),
    'Digitec_Samsung_Full': ('CH', 'Digitec', 'SAMSUNG'),
    'Digitec_LG_Full': ('CH', 'Digitec', 'LG')
}

surveyed_models = set()
surveyed_urls = set()

def extract_surveyed(wb, sheet_map):
    for s_name, (c_code, r_name, b_name) in sheet_map.items():
        if s_name not in wb.sheetnames:
            continue
        ws = wb[s_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        header = [str(c).lower().strip() if c else '' for c in rows[0]]
        code_col = 4
        url_col = 10
        for idx, h in enumerate(header):
            if any(k in h for k in ['model code', 'model_code', 'code']):
                code_col = idx
            if any(k in h for k in ['url', 'link']):
                url_col = idx
        for r in rows[1:]:
            if r and len(r) > code_col and r[code_col]:
                code = str(r[code_col]).strip().upper()
                surveyed_models.add((c_code, r_name.lower(), b_name.lower(), code))
            if r and len(r) > url_col and r[url_col]:
                u = str(r[url_col]).strip()
                surveyed_urls.add(u)

extract_surveyed(wb_eu, sheet_map_eu)
extract_surveyed(wb_ch, sheet_map_ch)

matched_items = []
missing_items = []

for k, entry in master.items():
    if not isinstance(entry, dict):
        continue
    c = str(entry.get('country', '')).strip().upper()
    r = str(entry.get('retailer', '')).strip().lower()
    b = str(entry.get('brand', '')).strip().lower()
    m = str(entry.get('model_code', '')).strip().upper()
    u = str(entry.get('url', '')).strip()

    entry_copy = dict(entry)
    entry_copy['master_key'] = k

    if (c, r, b, m) in surveyed_models or u in surveyed_urls:
        matched_items.append(entry_copy)
    else:
        missing_items.append(entry_copy)

out_file = os.path.join(DATA_DIR, 'master_urls_missing_713.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(missing_items, f, indent=2, ensure_ascii=False)

print(f"Exported {len(missing_items)} missing items to {out_file}")
