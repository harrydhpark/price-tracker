# -*- coding: utf-8 -*-
"""
Synchronizer for 4 New EU Retailers (PL, PT, RO, SE)
Injects 8 new standardized sheets into price tracker_EU_2026 {MMDD}_v1.xlsx:
- MediaExpert_PL_Samsung, MediaExpert_PL_LG (PLN)
- Worten_PT_Samsung, Worten_PT_LG (EUR)
- Altex_RO_Samsung, Altex_RO_LG (RON)
- Elgiganten_SE_Samsung, Elgiganten_SE_LG (SEK)
"""

import os
import sys
import json
import glob
import re
import shutil
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")

NEW_RETAILER_CONFIGS = [
    {
        "cc": "PL", "retailer": "MediaExpert", "currency": "PLN",
        "sheet_samsung": "MediaExpert_PL_Samsung", "sheet_lg": "MediaExpert_PL_LG",
        "file_samsung": "raw_mediaexpert_pl_samsung.json", "file_lg": "raw_mediaexpert_pl_lg.json"
    },
    {
        "cc": "PT", "retailer": "Worten", "currency": "EUR",
        "sheet_samsung": "Worten_PT_Samsung", "sheet_lg": "Worten_PT_LG",
        "file_samsung": "raw_worten_pt_samsung.json", "file_lg": "raw_worten_pt_lg.json"
    },
    {
        "cc": "RO", "retailer": "Altex", "currency": "RON",
        "sheet_samsung": "Altex_RO_Samsung", "sheet_lg": "Altex_RO_LG",
        "file_samsung": "raw_altex_ro_samsung.json", "file_lg": "raw_altex_ro_lg.json"
    },
    {
        "cc": "SE", "retailer": "Elgiganten", "currency": "SEK",
        "sheet_samsung": "Elgiganten_SE_Samsung", "sheet_lg": "Elgiganten_SE_LG",
        "file_samsung": "raw_elgiganten_se_samsung.json", "file_lg": "raw_elgiganten_se_lg.json"
    }
]

def find_target_workbook():
    today_mmdd = datetime.now().strftime("%m%d")
    exact = os.path.join(DATA_DIR, f"price tracker_EU_2026 {today_mmdd}_v1.xlsx")
    if os.path.exists(exact):
        return exact
    candidates = glob.glob(os.path.join(DATA_DIR, "price tracker_EU_2026 *.xlsx"))
    candidates = [f for f in candidates if not os.path.basename(f).startswith("~$")]
    if candidates:
        return sorted(candidates)[-1]
    # Fallback to create new
    return exact

def write_sheet(ws, items, brand_name, currency):
    # Header styling
    header_fill = PatternFill(start_color="1F4E79" if brand_name == "Samsung" else "A61C1C",
                              end_color="1F4E79" if brand_name == "Samsung" else "A61C1C",
                              fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    headers = [
        "Brand", "Model Year", "Display Type", "Size (Inch)", "Model Code",
        f"Price ({currency})", f"Original Price ({currency})", "Series",
        "Cashback", "General Promotions", "URL", "Title"
    ]
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center

    for it in items:
        # Infer series
        mc = it.get("model_code", "Unknown")
        series = it.get("series") or "Unknown"
        if series == "Unknown" and mc != "Unknown":
            m_s = re.search(r'(?:QE|UE|MRE|OLED)?\d{2,3}([A-Z0-9]+)', mc)
            if m_s:
                series = m_s.group(1)

        row_vals = [
            it.get("brand", brand_name),
            it.get("year", 2026),
            it.get("display_type") or it.get("display", "LED"),
            it.get("size", 55),
            mc,
            it.get("price", 0.0),
            it.get("original_price") or it.get("price", 0.0),
            series,
            it.get("cashback", 0.0),
            it.get("promo") or it.get("promotion", "None"),
            it.get("url") or it.get("link", ""),
            it.get("title", "")
        ]
        ws.append(row_vals)
        r_idx = ws.max_row
        for c_idx in range(1, len(row_vals) + 1):
            c = ws.cell(row=r_idx, column=c_idx)
            c.font = data_font
            if c_idx in [2, 4]:
                c.alignment = align_center
            elif c_idx in [6, 7, 9]:
                c.alignment = align_right
                c.number_format = "#,##0.00"
            else:
                c.alignment = align_left

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

def sync_new_retailers():
    wb_path = find_target_workbook()
    print(f"🔄 [EXCEL SYNC] Target EU Workbook: {wb_path}")
    
    if os.path.exists(wb_path):
        wb = openpyxl.load_workbook(wb_path)
    else:
        wb = openpyxl.Workbook()
        # Remove default sheet
        if "Sheet" in wb.sheetnames:
            del wb["Sheet"]

    total_added = 0
    for cfg in NEW_RETAILER_CONFIGS:
        for brand, s_key, f_key in [("Samsung", "sheet_samsung", "file_samsung"), ("LG", "sheet_lg", "file_lg")]:
            sheet_name = cfg[s_key]
            json_file = os.path.join(DATA_DIR, cfg[f_key])
            if not os.path.exists(json_file):
                print(f"  [WARN] Missing {json_file}, skipping sheet {sheet_name}")
                continue
                
            with open(json_file, "r", encoding="utf-8") as f:
                items = json.load(f)

            if sheet_name in wb.sheetnames:
                del wb[sheet_name]

            ws = wb.create_sheet(title=sheet_name)
            write_sheet(ws, items, brand, cfg["currency"])
            total_added += len(items)
            print(f"  ✔ [SHEET ADDED] {sheet_name} ({len(items)} models, Currency: {cfg['currency']})")

    # Save with retry
    saved = False
    save_path = wb_path
    version = 1
    while not saved:
        try:
            wb.save(save_path)
            saved = True
            print(f"✅ [SAVED] Successfully saved 30-sheet EU Workbook: {save_path}")
        except PermissionError:
            base, ext = os.path.splitext(wb_path)
            save_path = f"{base}_v{version + 1}{ext}"
            version += 1
            print(f"  ➔ Permission denied. Retrying with: {save_path}...")

    # Auto-mirror to History_EU
    try:
        today_folder = datetime.now().strftime("2026 %m%d")
        hist_dir = os.path.join(ROOT_DIR, "History_EU", today_folder)
        os.makedirs(hist_dir, exist_ok=True)
        shutil.copy2(save_path, os.path.join(hist_dir, os.path.basename(save_path)))
        print(f"  ➔ [HISTORY AUTO-MIRROR] Copied to {hist_dir}")
    except Exception as e_hist:
        print(f"  [WARN] History copy error: {e_hist}")

    # Auto-sync into master_product_urls.json
    try:
        master_reg_path = os.path.join(DATA_DIR, "master_product_urls.json")
        if os.path.exists(master_reg_path):
            with open(master_reg_path, "r", encoding="utf-8") as f_m:
                master = json.load(f_m)
        else:
            master = {}

        today_str = datetime.now().strftime("%Y-%m-%d")
        reg_count = 0
        for cfg in NEW_RETAILER_CONFIGS:
            for brand, f_key in [("Samsung", "file_samsung"), ("LG", "file_lg")]:
                json_file = os.path.join(DATA_DIR, cfg[f_key])
                if not os.path.exists(json_file): continue
                with open(json_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                for it in items:
                    mc = it.get("model_code")
                    url = it.get("url")
                    if mc and url and mc != "Unknown" and url.startswith("http"):
                        clean_code = re.sub(r'[^A-Za-z0-9_-]', '', mc).upper()
                        k = f"{cfg['cc']}_{cfg['retailer'].upper()}_{clean_code}"
                        master[k] = {
                            "country": cfg["cc"],
                            "retailer": cfg["retailer"],
                            "brand": brand.upper(),
                            "model_code": mc,
                            "year": it.get("year", 2026),
                            "size": it.get("size", 55),
                            "title": it.get("title", ""),
                            "url": url,
                            "last_updated": today_str
                        }
                        reg_count += 1
        with open(master_reg_path, "w", encoding="utf-8") as f_m:
            json.dump(master, f_m, ensure_ascii=False, indent=2)
        print(f"  ➔ [MASTER REGISTRY] Auto-registered/updated {reg_count} models for PL, PT, RO, SE into master_product_urls.json")
    except Exception as e_reg:
        print(f"  [WARN] Master registry update error: {e_reg}")

    # Update SQLite Price History
    try:
        sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
        from price_history import record_survey_from_excel
        record_survey_from_excel(save_path)
        print("  ➔ [SQLITE DB] Synchronized prices into price_history.db")
    except Exception as e_db:
        print(f"  [WARN] SQLite sync error: {e_db}")

if __name__ == "__main__":
    sync_new_retailers()
