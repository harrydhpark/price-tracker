import openpyxl
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))
data_dir = os.path.join(root_dir, "data")
from datetime import datetime
today_mmdd = datetime.now().strftime("%m%d") # e.g. "0705"
excel_path = os.path.join(data_dir, f"Swiss_ATA_Comparison_2026_{today_mmdd}_v1.xlsx")
if not os.path.exists(excel_path):
    excel_path = os.path.join(data_dir, f"Swiss_ATA_Comparison_2026_{today_mmdd}.xlsx")
if not os.path.exists(excel_path):
    import glob
    candidates = sorted(glob.glob(os.path.join(data_dir, "Swiss_ATA_Comparison_2026_*.xlsx")))
    if candidates:
        excel_path = candidates[-1]

# Use the copied template path in the workspace data directory
template_path = os.path.join(data_dir, "swiss_price_dashboard_template.html")

# Dynamic current brain directory based on environment
artifact_dir = os.environ.get("ANTIGRAVITY_ARTIFACT_DIR")
workspace_dashboard_path = os.path.join(data_dir, "swiss_price_dashboard.html")
artifact_dashboard_path = os.path.join(artifact_dir, "swiss_price_dashboard.html") if artifact_dir else None

# Sizing lists and model series configurations for 1:1 pairings
pairs_config_2025 = {
    "OLED": [
        {"lg": "G5", "sam": "S95F", "sizes": ["83", "77", "65", "55"]},
        {"lg": "C5", "sam": "S90F", "sizes": ["83", "77", "65", "55", "48", "42"]},
        {"lg": "B5", "sam": "S85F", "sizes": ["83", "77", "65", "55", "48"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED86A", "sam": "QN80F", "sizes": ["100", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED86A", "sam": "QN70F", "sizes": ["100", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED80A", "sam": "Q8F", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED80A", "sam": "Q7F", "sizes": ["86", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": [
        {"lg": "UA75", "sam": "U8000F", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ]
}

pairs_config_2026 = {
    "OLED": [
        {"lg": "G6", "sam": "S99H", "sizes": ["83", "77", "65", "55"]},
        {"lg": "G6", "sam": "S95H", "sizes": ["83", "77", "65", "55"]},
        {"lg": "C6", "sam": "S90H", "sizes": ["83", "77", "65", "55", "48", "42"]},
        {"lg": "B6", "sam": "S85H", "sizes": ["83", "77", "65", "55", "48"]}
    ],
    "MRGB": [
        {"lg_series": "86MRGB87B", "sam_series": "85R85H", "lg_lookup": "86MRGB85", "sam_lookup": "85R85H"},
        {"lg_series": "75MRGB87B", "sam_series": "75R85H", "lg_lookup": "75MRGB85", "sam_lookup": "75R85H"},
        {"lg_series": "65MRGB87B", "sam_series": "65R85H", "lg_lookup": "65MRGB85", "sam_lookup": "65R85H"},
        {"lg_series": "55MRGB87B", "sam_series": "55R85H", "lg_lookup": "55MRGB85", "sam_lookup": "55R85H"},
        {"lg_series": "50MRGB87B", "sam_series": "50R85H", "lg_lookup": "50MRGB85", "sam_lookup": "50R85H"}
    ],
    "QNED/QLED": [
        # 1. QNED86B vs QN80H (프리미엄 라인업)
        {"lg_series": "100QNED86B", "sam_series": "100QN80H", "lg_lookup": "100QNED85", "sam_lookup": "100QN80H"},
        {"lg_series": "86QNED86B", "sam_series": "85QN80H", "lg_lookup": "86QNED85", "sam_lookup": "85QN80H"},
        {"lg_series": "75QNED86B", "sam_series": "75QN80H", "lg_lookup": "75QNED85", "sam_lookup": "75QN80H"},
        {"lg_series": "65QNED86B", "sam_series": "65QN80H", "lg_lookup": "65QNED85", "sam_lookup": "65QN80H"},
        {"lg_series": "55QNED86B", "sam_series": "55QN80H", "lg_lookup": "55QNED85", "sam_lookup": "55QN80H"},
        {"lg_series": "50QNED86B", "sam_series": "50QN80H", "lg_lookup": "50QNED85", "sam_lookup": "50QN80H"},
        {"lg_series": "43QNED86B", "sam_series": "43QN80H", "lg_lookup": "43QNED85", "sam_lookup": "43QN80H"},
        # 2. QNED71B vs M70H (표준/볼륨 라인업)
        {"lg_series": "65QNED71B", "sam_series": "65M70H", "lg_lookup": "65QNED80", "sam_lookup": "65M70H"},
        {"lg_series": "55QNED71B", "sam_series": "55M70H", "lg_lookup": "55QNED80", "sam_lookup": "55M70H"},
        {"lg_series": "50QNED71B", "sam_series": "50M70H", "lg_lookup": "50QNED80", "sam_lookup": "50M70H"},
        {"lg_series": "43QNED71B", "sam_series": "43M70H", "lg_lookup": "43QNED80", "sam_lookup": "43M70H"},
        # 3. QNED70B vs M70H (대형 보급 라인업)
        {"lg_series": "86QNED70B", "sam_series": "85M70H", "lg_lookup": "86QNED70", "sam_lookup": "85M70H"},
        {"lg_series": "75QNED70B", "sam_series": "75M70H", "lg_lookup": "75QNED70", "sam_lookup": "75M70H"}
    ],
    "UHD 4K": [
        {"lg_series": "85NU85", "sam_series": "85U8090H", "lg_lookup": "85NU85", "sam_lookup": "85U8000H"},
        {"lg_series": "75NU85", "sam_series": "75U8090H", "lg_lookup": "75NU85", "sam_lookup": "75U8000H"},
        {"lg_series": "65NU85", "sam_series": "65U8090H", "lg_lookup": "65NU85", "sam_lookup": "65U8000H"},
        {"lg_series": "55NU85", "sam_series": "55U8090H", "lg_lookup": "55NU85", "sam_lookup": "55U8000H"},
        {"lg_series": "50NU85", "sam_series": "50U8090H", "lg_lookup": "50NU85", "sam_lookup": "50U8000H"},
        {"lg_series": "43NU85", "sam_series": "43U8090H", "lg_lookup": "43NU85", "sam_lookup": "43U8000H"}
    ]
}

def clean_price(val):
    if val is None or val == "" or val == "None":
        return 0
    if isinstance(val, (int, float)):
        fval = float(val)
        if 0 < fval < 10.0 and round(fval, 3) != round(fval, 2):
            fval = fval * 1000.0
        return int(round(fval)) if fval >= 50.0 else 0
        
    s = str(val).replace("€", "").replace("£", "").replace("kr", "").replace("SEK", "").replace("EUR", "").replace("GBP", "").replace("CHF", "").strip()
    if re.match(r'^\d{1,3}\.\d{3}$', s):
        s = s.replace(".", "")
    elif re.match(r'^\d{1,3},\d{3}$', s):
        s = s.replace(",", "")
    elif "," in s and "." in s:
        if s.find(".") < s.find(","):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts[-1]) == 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
            
    cleaned = re.sub(r'[^\d.]', '', s)
    try:
        fval = float(cleaned) if cleaned else 0.0
        if 0 < fval < 10.0:
            fval = fval * 1000.0
        return int(round(fval)) if fval >= 50.0 else 0
    except ValueError:
        return 0

def extract_sheet_data(sheet, last_row, promo_maps=None):
    data = {}
    for r in range(4, last_row + 1):
        series_val = sheet.cell(row=r, column=2).value
        if not series_val:
            continue
            
        series_key = str(series_val).strip()
        disp_type = str(sheet.cell(row=r, column=1).value or "").strip()
        
        msh_price = clean_price(sheet.cell(row=r, column=5).value)
        id_price = clean_price(sheet.cell(row=r, column=10).value)
        digi_price = clean_price(sheet.cell(row=r, column=15).value)
        
        msh_cb = clean_price(sheet.cell(row=r, column=6).value)
        id_cb = clean_price(sheet.cell(row=r, column=11).value)
        digi_cb = clean_price(sheet.cell(row=r, column=16).value)
        
        msh_net_val = sheet.cell(row=r, column=4).value
        id_net_val = sheet.cell(row=r, column=9).value
        digi_net_val = sheet.cell(row=r, column=14).value
        
        if msh_net_val is None or str(msh_net_val).startswith('='):
            msh_net = max(0, msh_price - msh_cb) if msh_price > 0 else 0
        else:
            msh_net = clean_price(msh_net_val)
            
        if id_net_val is None or str(id_net_val).startswith('='):
            id_net = max(0, id_price - id_cb) if id_price > 0 else 0
        else:
            id_net = clean_price(id_net_val)
            
        if digi_net_val is None or str(digi_net_val).startswith('='):
            digi_net = max(0, digi_price - digi_cb) if digi_price > 0 else 0
        else:
            digi_net = clean_price(digi_net_val)
            
        # Extract model codes from columns 3, 8, 13
        msh_code = sheet.cell(row=r, column=3).value
        id_code = sheet.cell(row=r, column=8).value
        digi_code = sheet.cell(row=r, column=13).value
        
        msh_promo = ""
        id_promo = ""
        digi_promo = ""
        
        if promo_maps:
            if msh_code:
                msh_promo = promo_maps["msh"].get(str(msh_code).strip().upper(), "")
            if id_code:
                id_promo = promo_maps["id"].get(str(id_code).strip().upper(), "")
            if digi_code:
                digi_promo = promo_maps["digi"].get(str(digi_code).strip().upper(), "")
        
        data[series_key] = {
            "series": series_key,
            "display": disp_type,
            "msh_price": msh_price,
            "id_price": id_price,
            "digi_price": digi_price,
            "msh_net": msh_net,
            "id_net": id_net,
            "digi_net": digi_net,
            "msh_promo": msh_promo,
            "id_promo": id_promo,
            "digi_promo": digi_promo,
            "msh_model": str(msh_code).strip() if msh_code else "",
            "id_model": str(id_code).strip() if id_code else "",
            "digi_model": str(digi_code).strip() if digi_code else ""
        }
    return data

def build_paired_json(sheet_data, config):
    output = {}
    default_rec = {
        "msh_price": 0, "id_price": 0, "digi_price": 0,
        "msh_net": 0, "id_net": 0, "digi_net": 0,
        "msh_promo": "", "id_promo": "", "digi_promo": "",
        "msh_model": "", "id_model": "", "digi_model": ""
    }
    for cat, mappings in config.items():
        output[cat] = []
        for map_item in mappings:
            if "lg_series" in map_item:
                # Explicit pair mapping
                lg_series = map_item["lg_series"]
                sam_series = map_item["sam_series"]
                lg_lookup = map_item.get("lg_lookup", lg_series)
                sam_lookup = map_item.get("sam_lookup", sam_series)
                lg_rec = dict(sheet_data.get(lg_lookup, default_rec))
                # Fallback for Interdiscount QNED if primary lookup has no ID price
                if lg_rec.get("id_price", 0) == 0 and "QNED" in lg_lookup:
                    size_m = re.match(r'^(\d+)', lg_lookup)
                    if size_m:
                        sz = size_m.group(1)
                        fb_keys = [f"{sz}QNED70", f"{sz}QNED72", f"{sz}QNED80"]
                        for fbk in fb_keys:
                            if fbk != lg_lookup and fbk in sheet_data and sheet_data[fbk].get("id_price", 0) > 0:
                                fb_rec = sheet_data[fbk]
                                lg_rec["id_price"] = fb_rec["id_price"]
                                lg_rec["id_net"] = fb_rec["id_net"]
                                lg_rec["id_promo"] = fb_rec.get("id_promo", "")
                                lg_rec["id_model"] = fb_rec.get("id_model", "")
                                break
                sam_rec = dict(sheet_data.get(sam_lookup, default_rec))
                # Fallback for Samsung U8090H / U8000H
                if sam_rec.get("id_price", 0) == 0 and ("U8000" in sam_lookup or "U8090" in sam_lookup):
                    size_m = re.match(r'^(\d+)', sam_lookup)
                    if size_m:
                        sz = size_m.group(1)
                        fb_keys = [f"{sz}U8090H", f"{sz}U8000H", f"{sz}U8070H"]
                        for fbk in fb_keys:
                            if fbk != sam_lookup and fbk in sheet_data and sheet_data[fbk].get("id_price", 0) > 0:
                                fb_rec = sheet_data[fbk]
                                sam_rec["id_price"] = fb_rec["id_price"]
                                sam_rec["id_net"] = fb_rec["id_net"]
                                sam_rec["id_promo"] = fb_rec.get("id_promo", "")
                                sam_rec["id_model"] = fb_rec.get("id_model", "")
                                break
                output[cat].append({
                    "lg_series": lg_series,
                    "sam_series": sam_series,
                    "lg_price_msh": lg_rec["msh_price"],
                    "lg_price_id": lg_rec["id_price"],
                    "lg_price_digi": lg_rec["digi_price"],
                    "sam_price_msh": sam_rec["msh_price"],
                    "sam_price_id": sam_rec["id_price"],
                    "sam_price_digi": sam_rec["digi_price"],
                    "lg_net_msh": lg_rec["msh_net"],
                    "lg_net_id": lg_rec["id_net"],
                    "lg_net_digi": lg_rec["digi_net"],
                    "sam_net_msh": sam_rec["msh_net"],
                    "sam_net_id": sam_rec["id_net"],
                    "sam_net_digi": sam_rec["digi_net"],
                    # Promos
                    "lg_promo_msh": lg_rec.get("msh_promo", ""),
                    "lg_promo_id": lg_rec.get("id_promo", ""),
                    "lg_promo_digi": lg_rec.get("digi_promo", ""),
                    "sam_promo_msh": sam_rec.get("msh_promo", ""),
                    "sam_promo_id": sam_rec.get("id_promo", ""),
                    "sam_promo_digi": sam_rec.get("digi_promo", ""),
                    # Models
                    "lg_model_msh": lg_rec.get("msh_model", ""),
                    "lg_model_id": lg_rec.get("id_model", ""),
                    "lg_model_digi": lg_rec.get("digi_model", ""),
                    "sam_model_msh": sam_rec.get("msh_model", ""),
                    "sam_model_id": sam_rec.get("id_model", ""),
                    "sam_model_digi": sam_rec.get("digi_model", "")
                })
            else:
                # Parameterized size list pairing
                lg_fam = map_item["lg"]
                sam_fam = map_item["sam"]
                for sz in map_item["sizes"]:
                    lg_series = f"{sz}{lg_fam}"
                    sam_series = f"{sz}{sam_fam}"
                    lg_rec = sheet_data.get(lg_series, default_rec)
                    sam_rec = sheet_data.get(sam_series, default_rec)
                    output[cat].append({
                        "lg_series": lg_series,
                        "sam_series": sam_series,
                        "lg_price_msh": lg_rec["msh_price"],
                        "lg_price_id": lg_rec["id_price"],
                        "lg_price_digi": lg_rec["digi_price"],
                        "sam_price_msh": sam_rec["msh_price"],
                        "sam_price_id": sam_rec["id_price"],
                        "sam_price_digi": sam_rec["digi_price"],
                        "lg_net_msh": lg_rec["msh_net"],
                        "lg_net_id": lg_rec["id_net"],
                        "lg_net_digi": lg_rec["digi_net"],
                        "sam_net_msh": sam_rec["msh_net"],
                        "sam_net_id": sam_rec["id_net"],
                        "sam_net_digi": sam_rec["digi_net"],
                        # Promos
                        "lg_promo_msh": lg_rec.get("msh_promo", ""),
                        "lg_promo_id": lg_rec.get("id_promo", ""),
                        "lg_promo_digi": lg_rec.get("digi_promo", ""),
                        "sam_promo_msh": sam_rec.get("msh_promo", ""),
                        "sam_promo_id": sam_rec.get("id_promo", ""),
                        "sam_promo_digi": sam_rec.get("digi_promo", ""),
                        # Models
                        "lg_model_msh": lg_rec.get("msh_model", ""),
                        "lg_model_id": lg_rec.get("id_model", ""),
                        "lg_model_digi": lg_rec.get("digi_model", ""),
                        "sam_model_msh": sam_rec.get("msh_model", ""),
                        "sam_model_id": sam_rec.get("id_model", ""),
                        "sam_model_digi": sam_rec.get("digi_model", "")
                    })
    return output

def scan_history_data():
    history_dir = os.path.join(root_dir, "History")
    if not os.path.exists(history_dir):
        print(f"[WARN] History directory not found: {history_dir}")
        return {"2025": {}, "2026": {}}
        
    date_folders = []
    # Find folders like "2026 0704", "2026 0705", etc.
    for name in os.listdir(history_dir):
        path = os.path.join(history_dir, name)
        if os.path.isdir(path) and re.match(r'^\d{4}\s+\d{4}$', name):
            date_folders.append(name)
            
    # Sort folders by date ascending (oldest first)
    date_folders.sort()
    
    historical_data = {
        "2025": {},
        "2026": {}
    }
    
    for folder in date_folders:
        folder_path = os.path.join(history_dir, folder)
        # Find best Swiss_ATA_Comparison file in this folder
        comparison_files = []
        for fname in os.listdir(folder_path):
            if fname.startswith("Swiss_ATA_Comparison_2026_") and fname.endswith(".xlsx"):
                comparison_files.append(fname)
                
        if not comparison_files:
            continue
            
        # Select best version by suffix, e.g. v2 > v1 > none
        comparison_files.sort()
        best_file = comparison_files[-1]
        best_filepath = os.path.join(folder_path, best_file)
        
        # Parse MMDD date string from folder name, e.g. "2026 0704" -> "07/04"
        parts = folder.split()
        date_str = f"{parts[1][:2]}/{parts[1][2:]}" # e.g. "07/04"
        
        print(f"  ➔ Scanning historical date: {date_str} from {best_file}")
        
        try:
            wb = openpyxl.load_workbook(best_filepath, data_only=True)
            for year, last_row in [("2025", 85), ("2026", 131)]:
                sheetname = f"Swiss_{year}"
                if sheetname not in wb.sheetnames:
                    continue
                sheet = wb[sheetname]
                sheet_data = extract_sheet_data(sheet, last_row)
                
                for series, records in sheet_data.items():
                    if series not in historical_data[year]:
                        historical_data[year][series] = {
                            "series": series,
                            "display": records["display"],
                            "history": []
                        }
                    historical_data[year][series]["history"].append({
                        "date": date_str,
                        "msh_price": records["msh_price"],
                        "id_price": records["id_price"],
                        "digi_price": records["digi_price"],
                        "msh_net": records["msh_net"],
                        "id_net": records["id_net"],
                        "digi_net": records["digi_net"]
                    })
            wb.close()
        except Exception as e:
            print(f"  ➔ [ERROR] Failed to parse historical comparison {best_filepath}: {e}")
            
    return historical_data

SWISS_RETAILERS = ['MediaMarkt', 'Interdiscount', 'Digitec']

def check_is_benchmark_swiss(brand, year, size, model_code, title):
    if year != 2026: return False
    b_up = str(brand).upper()
    mc_up = str(model_code).upper()
    t_up = str(title).upper()
    
    for cat, pair_list in pairs_config_2026.items():
        for pair in pair_list:
            if 'sizes' in pair and str(size) in [str(s) for s in pair.get('sizes', [])]:
                target_series = pair['lg'] if b_up == 'LG' else pair['sam']
                if target_series.upper() in mc_up or target_series.upper() in t_up:
                    return True
            elif 'lg_series' in pair:
                target_series = pair['lg_series'] if b_up == 'LG' else pair['sam_series']
                if target_series.upper() in mc_up or target_series.upper() in t_up:
                    return True
    return False

def load_swiss_catalog(wb_path):
    if not os.path.exists(wb_path):
        return {}
    wb = openpyxl.load_workbook(wb_path, data_only=True)
    catalog = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        retailer = 'MediaMarkt'
        if 'INTERDISCOUNT' in sheet_name.upper(): retailer = 'Interdiscount'
        elif 'DIGITEC' in sheet_name.upper(): retailer = 'Digitec'
        
        brand = 'SAMSUNG' if 'SAMSUNG' in sheet_name.upper() else 'LG'
        
        headers = [str(ws.cell(row=1, column=c).value or '').lower() for c in range(1, ws.max_column + 1)]
        
        code_col, year_col, size_col, price_col, cb_col, promo_col, title_col, disp_col = 5, 2, 4, 6, 9, 10, 13, 3
        for idx, h in enumerate(headers):
            if any(x in h for x in ['model code', 'code', 'modell']) and not ('was' in h or 'strike' in h):
                code_col = idx + 1
            elif any(x in h for x in ['year', 'jahr']): year_col = idx + 1
            elif any(x in h for x in ['display', 'panel', 'type']): disp_col = idx + 1
            elif any(x in h for x in ['size', 'zoll', 'inch']): size_col = idx + 1
            elif any(x in h for x in ['selling price', 'price']) and not ('was' in h or 'strike' in h or 'original' in h):
                price_col = idx + 1
            elif any(x in h for x in ['cashback', 'cb']): cb_col = idx + 1
            elif any(x in h for x in ['promotion', 'promo', 'general']): promo_col = idx + 1
            elif any(x in h for x in ['title', 'name', 'product']): title_col = idx + 1
            
        for r in range(2, ws.max_row + 1):
            c_code = ws.cell(row=r, column=code_col).value
            if not c_code or str(c_code).strip() in ['', 'Unknown']:
                continue
            c_code = str(c_code).strip()
            
            c_brand = ws.cell(row=r, column=1).value or brand
            c_year = ws.cell(row=r, column=year_col).value
            c_disp = ws.cell(row=r, column=disp_col).value if disp_col <= ws.max_column else 'LED'
            c_size = ws.cell(row=r, column=size_col).value
            c_price = ws.cell(row=r, column=price_col).value
            c_cb = ws.cell(row=r, column=cb_col).value or 0
            c_promo = ws.cell(row=r, column=promo_col).value or 'None'
            c_title = ws.cell(row=r, column=title_col).value if title_col <= ws.max_column else ''
            
            try: price_val = float(str(c_price).replace(',', '').replace(' ', '')) if c_price is not None else 0.0
            except: price_val = 0.0
            try: cb_val = float(str(c_cb).replace(',', '').replace(' ', '')) if c_cb is not None else 0.0
            except: cb_val = 0.0
            
            if price_val <= 0:
                continue
                
            try: yr_val = int(c_year) if c_year and str(c_year).isdigit() else 2025
            except: yr_val = 2025
            
            if yr_val != 2026:
                continue
                
            key = f'{retailer}_{c_brand}_{c_code}'.upper()
            catalog[key] = {
                'country': 'CH',
                'retailer': retailer,
                'brand': 'LG' if 'LG' in str(c_brand).upper() else 'SAMSUNG',
                'year': yr_val,
                'display': str(c_disp or 'LED').strip(),
                'size': int(c_size) if c_size and str(c_size).isdigit() else 55,
                'model_code': c_code,
                'currency': 'CHF',
                'currency_sym': 'CHF ',
                'price': price_val,
                'cashback': cb_val,
                'net_price': max(0.0, price_val - cb_val),
                'promo': str(c_promo).strip(),
                'title': str(c_title or c_code).strip()
            }
    wb.close()
    return catalog

def compute_weekly_changes_swiss():
    print("[PARSING WEEKLY CHANGES] Analyzing Swiss week-over-week changes (W31, W32, W33, W34)...")
    history_dir = os.path.join(root_dir, "History")
    w30_path = os.path.join(history_dir, "2026 0725", "price tracker_swiss_2026 0725_v1.xlsx")
    w31_path = os.path.join(history_dir, "2026 0728", "price tracker_swiss_2026 0728_v1.xlsx")
    w32_path = os.path.join(history_dir, "2026 0806", "price tracker_swiss_2026 0806_v1.xlsx")
    w33_path = os.path.join(history_dir, "2026 0814", "price tracker_swiss_2026 0814_v1.xlsx")
    if not os.path.exists(w33_path):
        w33_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_swiss_2026 0814*.xlsx")))
        if w33_cands: w33_path = w33_cands[-1]

    w34_path = os.path.join(history_dir, "2026 0817", "price tracker_swiss_2026 0817_v1.xlsx")
    if not os.path.exists(w34_path):
        w34_path = os.path.join(data_dir, "price tracker_swiss_2026 0817_v1.xlsx")
    if not os.path.exists(w34_path):
        w34_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_swiss_2026 0817*.xlsx")))
        if w34_cands: w34_path = w34_cands[-1]

    w35_path = os.path.join(history_dir, "2026 0828", "price tracker_swiss_2026 0828_v1.xlsx")
    if not os.path.exists(w35_path):
        w35_path = os.path.join(data_dir, "price tracker_swiss_2026 0828_v1.xlsx")
    if not os.path.exists(w35_path):
        w35_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_swiss_2026 0828*.xlsx")))
        if w35_cands: w35_path = w35_cands[-1]

    w36_path = os.path.join(history_dir, "2026 0903", "price tracker_swiss_2026 0903_v1.xlsx")
    if not os.path.exists(w36_path):
        w36_path = os.path.join(history_dir, "2026 0901", "price tracker_swiss_2026 0901_v1.xlsx")
    if not os.path.exists(w36_path):
        w36_path = os.path.join(data_dir, "price tracker_swiss_2026 0903_v1.xlsx")
    if not os.path.exists(w36_path):
        w36_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_swiss_2026 0903*.xlsx")))
        if w36_cands: w36_path = w36_cands[-1]

    w37_path = os.path.join(history_dir, "2026 0907", "price tracker_swiss_2026 0907_v1.xlsx")
    if not os.path.exists(w37_path):
        w37_path = os.path.join(data_dir, "price tracker_swiss_2026 0907_v1.xlsx")
    if not os.path.exists(w37_path):
        w37_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_swiss_2026 0907*.xlsx")))
        if w37_cands: w37_path = w37_cands[-1]

    cat_w30 = load_swiss_catalog(w30_path)
    cat_w31 = load_swiss_catalog(w31_path)
    cat_w32 = load_swiss_catalog(w32_path)
    cat_w33 = load_swiss_catalog(w33_path)
    cat_w34 = load_swiss_catalog(w34_path)
    cat_w35 = load_swiss_catalog(w35_path)
    cat_w36 = load_swiss_catalog(w36_path)
    cat_w37 = load_swiss_catalog(w37_path)

    transitions = [
        ("W37", "W37(09.07) vs W36(09.03)", "2026.09.07", "2026.09.03", cat_w36, cat_w37),
        ("W36", "W36(09.03) vs W35(08.28)", "2026.09.03", "2026.08.28", cat_w35, cat_w36),
        ("W35", "W35(08.28) vs W34(08.17)", "2026.08.28", "2026.08.17", cat_w34, cat_w35),
        ("W34", "W34(08.17) vs W33(08.14)", "2026.08.17", "2026.08.14", cat_w33, cat_w34),
        ("W33", "W33(08.14) vs W32(08.06)", "2026.08.14", "2026.08.06", cat_w32, cat_w33),
        ("W32", "W32(08.06) vs W31(07.28)", "2026.08.06", "2026.07.28", cat_w31, cat_w32),
        ("W31", "W31(07.28) vs W30(07.25)", "2026.07.28", "2026.07.25", cat_w30, cat_w31)
    ]

    weekly_changes_data = {}

    for week_key, period_label, curr_d, prev_d, prev_cat, curr_cat in transitions:
        items = []
        price_drops = 0
        price_hikes = 0
        promo_changes = 0
        new_models = 0
        delisted_models = 0
        
        drop_pcts = []
        hike_pcts = []
        
        ret_stats = {r: {"drops": 0, "hikes": 0, "promos": 0, "news": 0, "delisted": 0} for r in SWISS_RETAILERS}
        
        for key, curr_item in curr_cat.items():
            if curr_item.get("year") != 2026:
                continue
            ret = curr_item["retailer"]
            brand = curr_item["brand"]
            size = curr_item["size"]
            model_code = curr_item["model_code"]
            title = curr_item["title"]
            is_bm = check_is_benchmark_swiss(brand, 2026, size, model_code, title)
            
            if key in prev_cat:
                prev_item = prev_cat[key]
                p_prev = prev_item["price"]
                p_curr = curr_item["price"]
                cb_prev = prev_item["cashback"]
                cb_curr = curr_item["cashback"]
                net_prev = prev_item["net_price"]
                net_curr = curr_item["net_price"]
                promo_prev = prev_item["promo"]
                promo_curr = curr_item["promo"]
                
                p_diff = round(p_curr - p_prev, 2)
                p_diff_pct = round((p_diff / p_prev) * 100, 1) if p_prev > 0 else 0.0
                net_diff = round(net_curr - net_prev, 2)
                
                tags = []
                if p_diff < -0.5:
                    tags.append("PRICE_DROP")
                    price_drops += 1
                    drop_pcts.append(abs(p_diff_pct))
                    if ret in ret_stats: ret_stats[ret]["drops"] += 1
                elif p_diff > 0.5:
                    tags.append("PRICE_HIKE")
                    price_hikes += 1
                    hike_pcts.append(abs(p_diff_pct))
                    if ret in ret_stats: ret_stats[ret]["hikes"] += 1
                    
                promo_changed = False
                if promo_curr != promo_prev:
                    promo_changed = True
                    if promo_prev in ["None", "", "-"] and promo_curr not in ["None", "", "-"]: tags.append("PROMO_NEW")
                    elif promo_prev not in ["None", "", "-"] and promo_curr in ["None", "", "-"]: tags.append("PROMO_ENDED")
                    else: tags.append("PROMO_CHANGED")
                if cb_curr != cb_prev:
                    promo_changed = True
                    tags.append("CASHBACK_CHANGED")
                if promo_changed:
                    promo_changes += 1
                    if ret in ret_stats: ret_stats[ret]["promos"] += 1
                    
                if tags:
                    items.append({
                        "key": key,
                        "retailer": ret,
                        "brand": brand,
                        "year": 2026,
                        "display": curr_item["display"],
                        "size": size,
                        "model_code": model_code,
                        "title": title,
                        "currency": "CHF",
                        "currency_sym": "CHF ",
                        "prev_price": p_prev,
                        "curr_price": p_curr,
                        "price_diff": p_diff,
                        "price_diff_pct": p_diff_pct,
                        "prev_cb": cb_prev,
                        "curr_cb": cb_curr,
                        "prev_net": net_prev,
                        "curr_net": net_curr,
                        "net_diff": net_diff,
                        "prev_promo": promo_prev,
                        "curr_promo": promo_curr,
                        "tags": tags,
                        "is_benchmark_pair": is_bm
                    })
            else:
                new_models += 1
                if ret in ret_stats: ret_stats[ret]["news"] += 1
                items.append({
                    "key": key,
                    "retailer": ret,
                    "brand": brand,
                    "year": 2026,
                    "display": curr_item["display"],
                    "size": size,
                    "model_code": model_code,
                    "title": title,
                    "currency": "CHF",
                    "currency_sym": "CHF ",
                    "prev_price": 0,
                    "curr_price": curr_item["price"],
                    "price_diff": 0,
                    "price_diff_pct": 0,
                    "prev_cb": 0,
                    "curr_cb": curr_item["cashback"],
                    "prev_net": 0,
                    "curr_net": curr_item["net_price"],
                    "net_diff": 0,
                    "prev_promo": "-",
                    "curr_promo": curr_item["promo"],
                    "tags": ["NEW_MODEL"],
                    "is_benchmark_pair": is_bm
                })
                
        for key, prev_item in prev_cat.items():
            if prev_item.get("year") != 2026:
                continue
            if key not in curr_cat:
                ret = prev_item["retailer"]
                brand = prev_item["brand"]
                size = prev_item["size"]
                model_code = prev_item["model_code"]
                title = prev_item["title"]
                is_bm = check_is_benchmark_swiss(brand, 2026, size, model_code, title)
                delisted_models += 1
                if ret in ret_stats: ret_stats[ret]["delisted"] += 1
                items.append({
                    "key": key,
                    "retailer": ret,
                    "brand": brand,
                    "year": 2026,
                    "display": prev_item["display"],
                    "size": size,
                    "model_code": model_code,
                    "title": title,
                    "currency": "CHF",
                    "currency_sym": "CHF ",
                    "prev_price": prev_item["price"],
                    "curr_price": 0,
                    "price_diff": 0,
                    "price_diff_pct": 0,
                    "prev_cb": prev_item["cashback"],
                    "curr_cb": 0,
                    "prev_net": prev_item["net_price"],
                    "curr_net": 0,
                    "net_diff": 0,
                    "prev_promo": prev_item["promo"],
                    "curr_promo": "Delisted / Out of Stock",
                    "tags": ["DELISTED"],
                    "is_benchmark_pair": is_bm
                })
                
        def sort_priority(it):
            bm_score = 0 if it["is_benchmark_pair"] else 1
            if "PRICE_DROP" in it["tags"]: tag_score = 1
            elif "PRICE_HIKE" in it["tags"]: tag_score = 2
            elif "PROMO_NEW" in it["tags"] or "PROMO_CHANGED" in it["tags"] or "CASHBACK_CHANGED" in it["tags"]: tag_score = 3
            elif "NEW_MODEL" in it["tags"]: tag_score = 4
            else: tag_score = 5
            return (bm_score, tag_score, it["price_diff"], -it["size"])
            
        items.sort(key=sort_priority)
        
        avg_drop = round(sum(drop_pcts) / len(drop_pcts), 1) if drop_pcts else 0.0
        avg_hike = round(sum(hike_pcts) / len(hike_pcts), 1) if hike_pcts else 0.0
        
        weekly_changes_data[week_key] = {
            "period": period_label,
            "curr_date": curr_d,
            "prev_date": prev_d,
            "summary": {
                "total_changes": len(items),
                "price_drops": price_drops,
                "price_hikes": price_hikes,
                "promo_changes": promo_changes,
                "new_models": new_models,
                "delisted_models": delisted_models,
                "avg_drop_pct": avg_drop,
                "avg_hike_pct": avg_hike
            },
            "retailer_stats": ret_stats,
            "items": items
        }
        print(f"  ➔ [SWISS WEEKLY CHANGES] {week_key}: {len(items)} change items (Drops: {price_drops}, Hikes: {price_hikes}, Promos: {promo_changes}, New: {new_models})")
        
    return weekly_changes_data

def main():
    if not os.path.exists(excel_path):
        print(f"[ERROR] Excel comparison workbook not found: {excel_path}")
        return
        
    # Build today's promo maps from raw price tracker excel
    promo_maps = {
        "msh": {},
        "id": {},
        "digi": {}
    }
    pt_path = os.path.join(data_dir, f"price tracker_swiss_2026 {today_mmdd}_v1.xlsx")
    if not os.path.exists(pt_path):
        pt_path = os.path.join(data_dir, f"price tracker_swiss_2026 {today_mmdd}.xlsx")
        
    if os.path.exists(pt_path):
        print(f"[PARSING RAW EXCEL] Loading raw tracker: {pt_path} for promotions...")
        pt_wb = openpyxl.load_workbook(pt_path, data_only=True)
        # MediaMarkt
        for sname in ["MediaMarkt_Samsung_Full", "MediaMarkt_LG_Full"]:
            if sname in pt_wb.sheetnames:
                sheet = pt_wb[sname]
                for r in range(2, sheet.max_row + 1):
                    code = sheet.cell(row=r, column=5).value
                    promo = sheet.cell(row=r, column=10).value
                    if code:
                        promo_maps["msh"][str(code).strip().upper()] = str(promo or "").strip()
        # Interdiscount
        for sname in ["Interdiscount_Samsung_Full", "Interdiscount_LG_Full"]:
            if sname in pt_wb.sheetnames:
                sheet = pt_wb[sname]
                for r in range(2, sheet.max_row + 1):
                    code = sheet.cell(row=r, column=5).value
                    promo = sheet.cell(row=r, column=10).value
                    if code:
                        promo_maps["id"][str(code).strip().upper()] = str(promo or "").strip()
        # Digitec
        for sname in ["Digitec_Samsung_Full", "Digitec_LG_Full"]:
            if sname in pt_wb.sheetnames:
                sheet = pt_wb[sname]
                for r in range(2, sheet.max_row + 1):
                    code = sheet.cell(row=r, column=5).value
                    promo = sheet.cell(row=r, column=10).value
                    if code:
                        promo_maps["digi"][str(code).strip().upper()] = str(promo or "").strip()
        pt_wb.close()
    else:
        print(f"[WARN] Raw tracker not found at {pt_path}, promotions will be empty.")

    print(f"[PARSING EXCEL] Loading comparison report: {excel_path}...")
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    
    # 1. Parse sheets with dynamic last_row calculation based on summary_start
    s2025 = wb["Swiss_2025"]
    summary_start_2025 = None
    for r in range(4, 300):
        val_b = s2025.cell(row=r, column=2).value
        if val_b == "Series" and r > 10:
            summary_start_2025 = r
            break
    if summary_start_2025 is None:
        summary_start_2025 = 86
    last_row_2025 = summary_start_2025 - 1
    while last_row_2025 > 4:
        val_b = s2025.cell(row=last_row_2025, column=2).value
        if val_b and str(val_b).strip():
            break
        last_row_2025 -= 1
        
    s2026 = wb["Swiss_2026"]
    summary_start_2026 = None
    for r in range(4, 300):
        val_b = s2026.cell(row=r, column=2).value
        if val_b == "Series" and r > 10:
            summary_start_2026 = r
            break
    if summary_start_2026 is None:
        summary_start_2026 = 132
    last_row_2026 = summary_start_2026 - 1
    while last_row_2026 > 4:
        val_b = s2026.cell(row=last_row_2026, column=2).value
        if val_b and str(val_b).strip():
            break
        last_row_2026 -= 1
        
    print(f"  ➔ [DYNAMIC INDEX] 2025 Dynamic last_row: {last_row_2025} | 2026 Dynamic last_row: {last_row_2026}")
    
    data_2025 = extract_sheet_data(s2025, last_row=last_row_2025, promo_maps=promo_maps)
    data_2026 = extract_sheet_data(s2026, last_row=last_row_2026, promo_maps=promo_maps)
    wb.close()
    
    # 2. Build pairs
    pairs_2025 = build_paired_json(data_2025, pairs_config_2025)
    pairs_2026 = build_paired_json(data_2026, pairs_config_2026)
    
    # 3. Scan historical data
    print("[PARSING HISTORY] Scanning all historical survey folders...")
    history_data = scan_history_data()
    
    weekly_changes_data = compute_weekly_changes_swiss()
    
    price_data = {
        "2025": pairs_2025,
        "2026": pairs_2026,
        "history": history_data,
        "weekly_changes": weekly_changes_data
    }
    
    # 4. Inject into HTML Template
    if not os.path.exists(template_path):
        print(f"[ERROR] HTML base template not found: {template_path}")
        return
        
    print(f"[COMPILING DASHBOARD] Injecting JSON data and survey dates into template...")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    # Isolate data block inject
    json_str = json.dumps(price_data, indent=2)
    injection_block = f"const priceData = {json_str};"
    
    # Dynamic Date Strings based on Excel Date
    now_dt = datetime.now()
    week_no = now_dt.isocalendar()[1]
    survey_date = now_dt.strftime(f"%Y년 %m월 %d일 (W{week_no})")
    survey_date_dot = now_dt.strftime(f"%Y.%m.%d(W{week_no})")
    
    compiled_html = html_content.replace("// {{INSERT_PRICE_DATA}}", injection_block)
    compiled_html = compiled_html.replace("{{SURVEY_DATE}}", survey_date)
    compiled_html = compiled_html.replace("{{SURVEY_DATE_DOT}}", survey_date_dot)
    
    # 5. Save to target files
    with open(workspace_dashboard_path, "w", encoding="utf-8") as f:
        f.write(compiled_html)
    print(f"  ➔ [SAVED] Compiled HTML saved to Workspace: {workspace_dashboard_path}")
    
    if artifact_dir and artifact_dashboard_path:
        os.makedirs(artifact_dir, exist_ok=True)
        with open(artifact_dashboard_path, "w", encoding="utf-8") as f:
            f.write(compiled_html)
        print(f"  ➔ [SAVED] Compiled HTML saved to Artifact: {artifact_dashboard_path}")
    
    # 6. Save to firebase public folder if it exists
    firebase_public_path = os.path.join(root_dir, "public", "index.html")
    if os.path.exists(os.path.dirname(firebase_public_path)):
        with open(firebase_public_path, "w", encoding="utf-8") as f:
            f.write(compiled_html)
        print(f"  ➔ [SAVED] Compiled HTML saved to Firebase Public: {firebase_public_path}")
        
    # 7. Mirror to History folder
    history_latest_dir = os.path.join(root_dir, "History", f"2026 {today_mmdd}")
    if os.path.exists(history_latest_dir):
        history_dashboard_path = os.path.join(history_latest_dir, "swiss_price_dashboard.html")
        with open(history_dashboard_path, "w", encoding="utf-8") as f:
            f.write(compiled_html)
        print(f"  ➔ [SAVED] Compiled HTML saved to History: {history_dashboard_path}")
    
    print("\n[DASHBOARD COMPILATION COMPLETED SUCCESSFULLY]")

if __name__ == "__main__":
    main()
