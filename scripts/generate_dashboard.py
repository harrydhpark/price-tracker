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

# Dynamic current brain directory based on current conversation ID
artifact_dir = r"C:\Users\harry.park\.gemini\antigravity\brain\02947bc7-1209-42f6-ac10-ab9b6ba3e82a"
workspace_dashboard_path = os.path.join(data_dir, "swiss_price_dashboard.html")
artifact_dashboard_path = os.path.join(artifact_dir, "swiss_price_dashboard.html")

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
        {"lg_series": "86MRGB95", "sam_series": "85R95H"},
        {"lg_series": "75MRGB95", "sam_series": "75R95H"},
        {"lg_series": "86MRGB85", "sam_series": "85R85H"},
        {"lg_series": "75MRGB85", "sam_series": "75R85H"},
        {"lg_series": "65MRGB85", "sam_series": "65R85H"},
        {"lg_series": "55MRGB85", "sam_series": "55R85H"},
        {"lg_series": "50MRGB85", "sam_series": "50R85H"}
    ],
    "QNED/QLED": [
        {"lg": "QNED93", "sam": "QN80H", "sizes": ["100", "85", "75", "65", "55", "50"]},
        {"lg": "QNED85", "sam": "QN70H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED80", "sam": "R95H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70", "sam": "R85H", "sizes": ["86", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": [
        {"lg": "NU85", "sam": "U8000H", "sizes": ["85", "75", "65", "55", "50", "43"]}
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
    
    price_data = {
        "2025": pairs_2025,
        "2026": pairs_2026,
        "history": history_data
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
    survey_date = datetime.now().strftime("%Y년 %m월 %d일")
    survey_date_dot = datetime.now().strftime("%Y.%m.%d")
    
    def format_python_date_with_week(date_str, format_type='dot'):
        # date_str: "2026.08.13" or "2026년 08월 13일"
        match = re.search(r'2026.*?0?8.*?(\d+)', date_str)
        if match:
            day = int(match.group(1))
            week = ""
            if 2 <= day <= 8:
                week = "32W"
            elif 9 <= day <= 15:
                week = "33W"
            
            if week:
                if format_type == 'korean':
                    return f"{date_str} ({week})"
                else:
                    return f"{date_str}({week})"
        return date_str

    survey_date = format_python_date_with_week(survey_date, 'korean')
    survey_date_dot = format_python_date_with_week(survey_date_dot, 'dot')
    
    compiled_html = html_content.replace("// {{INSERT_PRICE_DATA}}", injection_block)
    compiled_html = compiled_html.replace("{{SURVEY_DATE}}", survey_date)
    compiled_html = compiled_html.replace("{{SURVEY_DATE_DOT}}", survey_date_dot)
    
    # 5. Save to target files
    with open(workspace_dashboard_path, "w", encoding="utf-8") as f:
        f.write(compiled_html)
    print(f"  ➔ [SAVED] Compiled HTML saved to Workspace: {workspace_dashboard_path}")
    
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
    
    print("\n[DASHBOARD COMPILATION COMPLETED SUCCESSFULLY]")

if __name__ == "__main__":
    main()
