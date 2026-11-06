# -*- coding: utf-8 -*-
"""
Corporate Subsidiary x Product Daily ATA Matrix Generator (2026 New Models - 11월 일별 조사)
Generates:
  1. Excel Workbook: data/EU_Daily_ATA_Matrix_2026_11.xlsx (and History_EU/2026 1102/ or 1103/)
  2. Structured JSON: data/eu_daily_ata_matrix_2026_11.json (embedded into eu_price_dashboard.html)
"""
import os
import re
import sys
import glob
import json
import shutil
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding="utf-8")

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from scripts.generate_eu_dashboard import (
    extract_products_from_sheet,
    find_sheet,
    find_product,
    COUNTRY_RETAILERS,
    COUNTRY_CURRENCIES,
    CURRENCY_SYMBOLS,
)
from scripts.generate_eu_ata_matrix import (
    SUBSIDIARIES,
    MATRIX_ROWS_2026,
    match_corporate_ata_pair,
)

data_dir = os.path.join(root_dir, "data")
history_dir = os.path.join(root_dir, "History_EU")

# 11월 일자 (11/01 ~ 11/30, 총 30일)
DAYS_NOVEMBER = [f"11/{d:02d}" for d in range(1, 31)]


def find_november_survey_workbooks():
    """
    Scans data/ and History_EU/ for all November 2026 survey workbooks.
    Returns sorted dict: { '11/02': path_1102, '11/03': path_1103, '11/04': path_1104, ... }
    """
    found = {}
    # Scan History_EU first
    for entry in glob.glob(os.path.join(history_dir, "2026 11*")):
        if os.path.isdir(entry):
            m = re.search(r"2026 11(\d{2})", os.path.basename(entry))
            if m:
                day_key = f"11/{m.group(1)}"
                for wb_file in glob.glob(os.path.join(entry, "price tracker_EU_2026 11*.xlsx")):
                    found[day_key] = os.path.abspath(wb_file)

    # Scan data/ directory (overriding or supplementing with freshest workbooks)
    for wb_file in glob.glob(os.path.join(data_dir, "price tracker_EU_2026 11*.xlsx")):
        m = re.search(r"price tracker_EU_2026 11(\d{2})", os.path.basename(wb_file))
        if m:
            day_key = f"11/{m.group(1)}"
            found[day_key] = os.path.abspath(wb_file)

    return dict(sorted(found.items(), key=lambda x: x[0]))


def load_workbook_products(wb_path):
    """Loads all subsidiary products from an EU price tracker workbook."""
    if not os.path.exists(wb_path):
        return {}
    wb = openpyxl.load_workbook(wb_path, data_only=True)
    subs_products = {}
    for sub_info in SUBSIDIARIES:
        cc = sub_info["cc"]
        ret = COUNTRY_RETAILERS[cc][0]
        sam_cands = [
            f"{ret}_{cc}_SAMSUNG_Full",
            f"{ret}_{cc}_SAMSUNG",
            f"{ret}_{cc}_Samsung_Full",
            f"{ret}_Samsung_Full",
            f"{ret}_Samsung",
        ]
        lg_cands = [
            f"{ret}_{cc}_LG_Full",
            f"{ret}_{cc}_LG",
            f"{ret}_LG_Full",
            f"{ret}_LG",
        ]
        s_sheet = find_sheet(wb, sam_cands)
        l_sheet = find_sheet(wb, lg_cands)

        s_prods = extract_products_from_sheet(s_sheet) if s_sheet else []
        l_prods = extract_products_from_sheet(l_sheet) if l_sheet else []
        
        # Strict Pan-European Direct Seller Guard: exclude any 3rd-party marketplace models on CH MediaMarkt (S85H, S95H, MRGB96B)
        if cc == "CH":
            s_prods = [p for p in s_prods if not (p.get("year") == 2026 and any(k in str(p.get("model_code", "")).upper() for k in ["S85H", "S95H"]))]
            l_prods = [p for p in l_prods if not ("MRGB96" in str(p.get("model_code", "")).upper())]
        subs_products[sub_info["sub"]] = {
            "s_prods": s_prods,
            "l_prods": l_prods,
            "currency": COUNTRY_CURRENCIES.get(cc, "EUR"),
            "currency_sym": CURRENCY_SYMBOLS.get(COUNTRY_CURRENCIES.get(cc, "EUR"), "€"),
        }
    return subs_products


def load_live_raw_products():
    """Fallback: Loads products directly from live raw_*.json if available today."""
    raw_products = {}
    for sub_info in SUBSIDIARIES:
        cc = sub_info["cc"]
        ret = COUNTRY_RETAILERS[cc][0]
        sub = sub_info["sub"]

        # Map to raw json filenames
        if cc == "UK":
            s_file = "raw_currys_samsung.json"
            l_file = "raw_currys_lg.json"
        elif cc == "FR":
            s_file = "raw_boulanger_samsung.json"
            l_file = "raw_boulanger_lg.json"
        elif cc == "CH":
            s_file = "raw_mediamarkt_samsung.json"
            l_file = "raw_mediamarkt_lg.json"
        elif cc == "CZ":
            s_file = "raw_alza_samsung.json"
            l_file = "raw_alza_lg.json"
        elif cc == "HU":
            s_file = "raw_mm-hu_samsung.json"
            l_file = "raw_mm-hu_lg.json"
        elif cc == "PT":
            s_file = "raw_worten_pt_samsung.json"
            l_file = "raw_worten_pt_lg.json"
        elif cc == "SE":
            s_file = "raw_elgiganten_se_samsung.json"
            l_file = "raw_elgiganten_se_lg.json"
        elif cc == "PL":
            s_file = "raw_mediaexpert_pl_samsung.json"
            l_file = "raw_mediaexpert_pl_lg.json"
        elif cc == "RO":
            s_file = "raw_emag_ro_samsung.json"
            l_file = "raw_emag_ro_lg.json"
        elif cc == "GR":
            s_file = "raw_kotsovolos_gr_samsung.json"
            l_file = "raw_kotsovolos_gr_lg.json"
        elif cc == "IT":
            s_file = "raw_mw-it_samsung.json"
            l_file = "raw_mw-it_lg.json"
        else:
            s_file = f"raw_mm-{cc.lower()}_samsung.json"
            l_file = f"raw_mm-{cc.lower()}_lg.json"

        s_path = os.path.join(data_dir, s_file)
        l_path = os.path.join(data_dir, l_file)

        s_prods, l_prods = [], []
        if os.path.exists(s_path):
            try:
                with open(s_path, "r", encoding="utf-8") as f:
                    s_prods = json.load(f)
            except Exception:
                pass
        if os.path.exists(l_path):
            try:
                with open(l_path, "r", encoding="utf-8") as f:
                    l_prods = json.load(f)
            except Exception:
                pass

        if s_prods or l_prods:
            raw_products[sub] = {
                "s_prods": s_prods,
                "l_prods": l_prods,
                "currency": COUNTRY_CURRENCIES.get(cc, "EUR"),
                "currency_sym": CURRENCY_SYMBOLS.get(COUNTRY_CURRENCIES.get(cc, "EUR"), "€"),
            }
    return raw_products


def build_daily_ata_dataset():
    """Builds the November 2026 daily ATA matrix dataset dynamically scanning all survey days."""
    wb_map = find_november_survey_workbooks()
    print(f"[DAILY ATA] Discovered November survey workbooks: {list(wb_map.keys())}")

    day_products_map = {}
    active_days = []

    # Baseline: use the earliest available workbook for baseline (typically 11/02)
    earliest_day = list(wb_map.keys())[0] if wb_map else "11/02"
    base_wb_path = wb_map.get(earliest_day)
    if not base_wb_path or not os.path.exists(base_wb_path):
        base_wb_path = os.path.join(data_dir, "price tracker_EU_2026 1102_v1.xlsx")

    print(f"[DAILY ATA] Loading baseline from ({earliest_day}): {base_wb_path}")
    base_prods = load_workbook_products(base_wb_path)

    # 11/01 is carried over from earliest survey baseline
    day_products_map["11/01"] = base_prods
    active_days.append("11/01")

    # Load all discovered workbooks
    for day_key, wb_path in wb_map.items():
        print(f"[DAILY ATA] Loading {day_key} survey workbook: {wb_path}")
        prods = load_workbook_products(wb_path)
        day_products_map[day_key] = prods
        if day_key not in active_days:
            active_days.append(day_key)

    active_days = sorted(list(set(active_days)))
    print(f"[DAILY ATA] Active Survey Days configured: {active_days}")

    structured_rows = []
    for r_def in MATRIX_ROWS_2026:
        cat = r_def["cat"]
        inch = r_def["inch"]
        lg_series = r_def["lg_series"]
        sam_label = r_def["sam_label"]
        lg_guide = r_def["lg_guide"]

        row_item = {
            "cat": cat,
            "inch": inch,
            "lg_series": lg_series,
            "sam_label": sam_label,
            "lg_guide": lg_guide,
            "subsidiaries": {},
        }

        for sub_info in SUBSIDIARIES:
            sub = sub_info["sub"]
            cc = sub_info["cc"]

            sub_daily_data = {}
            for day in DAYS_NOVEMBER:
                if day in day_products_map:
                    sub_store = day_products_map[day].get(sub, {})
                    l_prods = sub_store.get("l_prods", [])
                    s_prods = sub_store.get("s_prods", [])
                    curr = sub_store.get("currency", "EUR")
                    curr_sym = sub_store.get("currency_sym", "€")

                    res = match_corporate_ata_pair(l_prods, s_prods, cc, inch, lg_series, sam_label)
                    res["currency"] = curr
                    res["currency_sym"] = curr_sym
                    res["date"] = day
                    if res.get("lg_price"):
                        res["lg_price"] = int(round(float(res["lg_price"])))
                    if res.get("sam_price"):
                        res["sam_price"] = int(round(float(res["sam_price"])))
                    if res.get("lg_net"):
                        res["lg_net"] = int(round(float(res["lg_net"])))
                    if res.get("sam_net"):
                        res["sam_net"] = int(round(float(res["sam_net"])))
                    if res.get("ata") is not None:
                        res["ata"] = int(round(float(res["ata"])))
                    if res.get("ata_raw") is not None:
                        res["ata_raw"] = int(round(float(res["ata_raw"])))
                    if res.get("ata_net") is not None:
                        res["ata_net"] = int(round(float(res["ata_net"])))
                    sub_daily_data[day] = res
                else:
                    sub_daily_data[day] = None

            row_item["subsidiaries"][sub] = sub_daily_data

        structured_rows.append(row_item)

    dataset = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "month": "2026-11",
        "title": "2026년 11월 유럽 법인/지점별 일별 ATA 비교 매트릭스",
        "days": DAYS_NOVEMBER,
        "active_days": active_days,
        "subsidiaries": SUBSIDIARIES,
        "rows": structured_rows,
    }
    return dataset


def create_daily_ata_excel(dataset, output_path):
    """
    Creates the November Daily ATA Excel Workbook.
    Each of the 15 European subsidiaries has its own dedicated sheet.
    Layout: 94 Columns:
      Cols A-D (4): Category, Inch, LG Model, Samsung Model
      Cols E-AH (30): ATA Index (11/01 ~ 11/30) with Excel ROUND Formulas & Guide 105 Norm
      Cols AI-BL (30): LG Selling Price (11/01 ~ 11/30)
      Cols BM-CP (30): Samsung Selling Price (11/01 ~ 11/30)
    """
    wb = openpyxl.Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)

    font_title = Font(name="Segoe UI", size=14, bold=True, color="1F2937")
    font_sec_hdr = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    font_col_hdr = Font(name="Segoe UI", size=9, bold=True, color="374151")
    font_meta = Font(name="Segoe UI", size=9, bold=True, color="111827")
    font_val = Font(name="Segoe UI", size=9, color="111827")
    font_empty = Font(name="Segoe UI", size=9, color="9CA3AF")

    fill_block_meta = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
    fill_block_ata = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")     # Navy
    fill_block_lg = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")      # Deep Red / Burgundy
    fill_block_sam = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")    # Deep Teal / Emerald

    fill_subhdr_ata = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")   # Light Blue
    fill_subhdr_lg = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")    # Light Red
    fill_subhdr_sam = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")   # Light Green

    border_thin = Border(
        left=Side(style="thin", color="E5E7EB"),
        right=Side(style="thin", color="E5E7EB"),
        top=Side(style="thin", color="E5E7EB"),
        bottom=Side(style="thin", color="E5E7EB")
    )
    border_major_right = Border(
        left=Side(style="thin", color="E5E7EB"),
        right=Side(style="medium", color="4B5563"),
        top=Side(style="thin", color="E5E7EB"),
        bottom=Side(style="thin", color="E5E7EB")
    )

    days = dataset["days"]  # 30 days
    num_days = len(days)

    for sub_info in SUBSIDIARIES:
        sub = sub_info["sub"]
        cc = sub_info["cc"]
        banner = sub_info["banner"]
        country_ko = sub_info["country_ko"]
        curr_sym = CURRENCY_SYMBOLS.get(COUNTRY_CURRENCIES.get(cc, "EUR"), "€")

        sheet_title = f"{sub}_{cc}" if len(sub) <= 4 else f"{sub[:6]}_{cc}"
        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].showGridLines = True

        # Row 1: Title
        ws.merge_cells("A1:CP1")
        c1 = ws["A1"]
        c1.value = f"2026년 11월 일별 ATA 비교 매트릭스 - [{sub}] {country_ko} ({banner}) [통화: {curr_sym}]"
        c1.font = font_title
        c1.alignment = Alignment(vertical="center", indent=1)
        ws.row_dimensions[1].height = 36

        # Row 3 & 4: Headers
        # Major Blocks:
        # A3:D3 -> 메타정보
        ws.merge_cells("A3:D3")
        c_meta_hdr = ws["A3"]
        c_meta_hdr.value = "기본 비교 라인업 (2026 New Models)"
        c_meta_hdr.font = font_sec_hdr
        c_meta_hdr.fill = PatternFill(start_color="4B5563", end_color="4B5563", fill_type="solid")
        c_meta_hdr.alignment = Alignment(horizontal="center", vertical="center")

        # Cols E to AH (30 cols) -> ATA
        col_ata_start = 5
        col_ata_end = col_ata_start + num_days - 1
        ws.merge_cells(start_row=3, start_column=col_ata_start, end_row=3, end_column=col_ata_end)
        c_ata_hdr = ws.cell(row=3, column=col_ata_start)
        c_ata_hdr.value = "1. ATA 지수 (LG 실판매가 / SEC 실판매가 * 100) [Guide 105 라인업은 100 기준 정규화]"
        c_ata_hdr.font = font_sec_hdr
        c_ata_hdr.fill = fill_block_ata
        c_ata_hdr.alignment = Alignment(horizontal="center", vertical="center")

        # Cols AI to BL (30 cols) -> LG Price
        col_lg_start = col_ata_end + 1
        col_lg_end = col_lg_start + num_days - 1
        ws.merge_cells(start_row=3, start_column=col_lg_start, end_row=3, end_column=col_lg_end)
        c_lg_hdr = ws.cell(row=3, column=col_lg_start)
        c_lg_hdr.value = f"2. LG 실판매가 (Net Selling Price) [{curr_sym}]"
        c_lg_hdr.font = font_sec_hdr
        c_lg_hdr.fill = fill_block_lg
        c_lg_hdr.alignment = Alignment(horizontal="center", vertical="center")

        # Cols BM to CP (30 cols) -> Samsung Price
        col_sam_start = col_lg_end + 1
        col_sam_end = col_sam_start + num_days - 1
        ws.merge_cells(start_row=3, start_column=col_sam_start, end_row=3, end_column=col_sam_end)
        c_sam_hdr = ws.cell(row=3, column=col_sam_start)
        c_sam_hdr.value = f"3. Samsung 실판매가 (Net Selling Price) [{curr_sym}]"
        c_sam_hdr.font = font_sec_hdr
        c_sam_hdr.fill = fill_block_sam
        c_sam_hdr.alignment = Alignment(horizontal="center", vertical="center")

        ws.row_dimensions[3].height = 26

        # Row 4: Sub Headers
        meta_headers = ["Category", "LG Model (Series)", "Samsung Model (Series)", "Inch"]
        for c_idx, h_text in enumerate(meta_headers, start=1):
            cell = ws.cell(row=4, column=c_idx, value=h_text)
            cell.font = font_col_hdr
            cell.fill = fill_block_meta
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_thin

        for i, day in enumerate(days):
            # ATA days
            c_ata = ws.cell(row=4, column=col_ata_start + i, value=day)
            c_ata.font = font_col_hdr
            c_ata.fill = fill_subhdr_ata
            c_ata.alignment = Alignment(horizontal="center", vertical="center")
            c_ata.border = border_major_right if (i == num_days - 1) else border_thin

            # LG days
            c_lg = ws.cell(row=4, column=col_lg_start + i, value=day)
            c_lg.font = font_col_hdr
            c_lg.fill = fill_subhdr_lg
            c_lg.alignment = Alignment(horizontal="center", vertical="center")
            c_lg.border = border_major_right if (i == num_days - 1) else border_thin

            # Samsung days
            c_sam = ws.cell(row=4, column=col_sam_start + i, value=day)
            c_sam.font = font_col_hdr
            c_sam.fill = fill_subhdr_sam
            c_sam.alignment = Alignment(horizontal="center", vertical="center")
            c_sam.border = border_major_right if (i == num_days - 1) else border_thin

        ws.row_dimensions[4].height = 22

        # Data Rows (Row 5 to 52, 48 rows)
        for r_idx, r_def in enumerate(dataset["rows"], start=5):
            cat = r_def["cat"]
            inch = r_def["inch"]
            lg_series = r_def["lg_series"]
            sam_label = r_def["sam_label"]
            lg_guide = r_def["lg_guide"]

            sub_dict = r_def["subsidiaries"].get(sub, {})

            # Representative models from day 11/02 or 11/03
            rep_lg_code = ""
            rep_sam_code = ""
            for d in ["11/02", "11/03", "11/01"]:
                if sub_dict.get(d):
                    if sub_dict[d].get("lg_code"):
                        rep_lg_code = sub_dict[d]["lg_code"]
                    if sub_dict[d].get("sam_code"):
                        rep_sam_code = sub_dict[d]["sam_code"]
                    if rep_lg_code and rep_sam_code:
                        break

            lg_repr = f"{rep_lg_code} ({lg_series})" if rep_lg_code else lg_series
            sam_repr = f"{rep_sam_code} ({sam_label})" if rep_sam_code else sam_label

            ws.cell(row=r_idx, column=1, value=cat).alignment = Alignment(horizontal="center", vertical="center")
            ws.cell(row=r_idx, column=2, value=lg_repr).alignment = Alignment(horizontal="left", vertical="center", indent=1)
            ws.cell(row=r_idx, column=3, value=sam_repr).alignment = Alignment(horizontal="left", vertical="center", indent=1)
            ws.cell(row=r_idx, column=4, value=f"{inch}\"").alignment = Alignment(horizontal="center", vertical="center")

            for c_i in range(1, 5):
                c_cell = ws.cell(row=r_idx, column=c_i)
                c_cell.font = font_meta
                c_cell.border = border_major_right if (c_i == 4) else border_thin

            # Populate Days (ATA, LG, SEC)
            is_guide_105 = (lg_series in ["QNED82B", "QNED80B", "QNED70B"])

            for d_i, day in enumerate(days):
                col_ata = col_ata_start + d_i
                col_lg = col_lg_start + d_i
                col_sam = col_sam_start + d_i

                day_rec = sub_dict.get(day)
                lg_p = day_rec.get("lg_net") or day_rec.get("lg_price") or 0 if day_rec else 0
                sam_p = day_rec.get("sam_net") or day_rec.get("sam_price") or 0 if day_rec else 0

                # 1. LG Price Cell
                c_lg_cell = ws.cell(row=r_idx, column=col_lg)
                if lg_p > 0:
                    c_lg_cell.value = lg_p
                    c_lg_cell.number_format = "#,##0"
                    c_lg_cell.font = font_val
                else:
                    c_lg_cell.value = "-"
                    c_lg_cell.font = font_empty
                c_lg_cell.alignment = Alignment(horizontal="right", vertical="center")
                c_lg_cell.border = border_major_right if (d_i == num_days - 1) else border_thin

                # 2. Samsung Price Cell
                c_sam_cell = ws.cell(row=r_idx, column=col_sam)
                if sam_p > 0:
                    c_sam_cell.value = sam_p
                    c_sam_cell.number_format = "#,##0"
                    c_sam_cell.font = font_val
                else:
                    c_sam_cell.value = "-"
                    c_sam_cell.font = font_empty
                c_sam_cell.alignment = Alignment(horizontal="right", vertical="center")
                c_sam_cell.border = border_major_right if (d_i == num_days - 1) else border_thin

                # 3. ATA Formula Cell
                col_lg_let = get_column_letter(col_lg)
                col_sam_let = get_column_letter(col_sam)

                c_ata_cell = ws.cell(row=r_idx, column=col_ata)
                if lg_p > 0 and sam_p > 0:
                    if is_guide_105:
                        c_ata_cell.value = f'=IFERROR(ROUND((({col_lg_let}{r_idx}/{col_sam_let}{r_idx})*100)/1.05,0),"-")'
                    else:
                        c_ata_cell.value = f'=IFERROR(ROUND(({col_lg_let}{r_idx}/{col_sam_let}{r_idx})*100,0),"-")'
                    c_ata_cell.font = Font(name="Segoe UI", size=9, bold=True, color="111827")
                else:
                    c_ata_cell.value = "-"
                    c_ata_cell.font = font_empty

                c_ata_cell.alignment = Alignment(horizontal="center", vertical="center")
                c_ata_cell.border = border_major_right if (d_i == num_days - 1) else border_thin

            ws.row_dimensions[r_idx].height = 20

        # Conditional formatting for ATA columns
        ata_range = f"E5:{get_column_letter(col_ata_end)}52"
        fill_green = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
        font_green = Font(color="166534", bold=True)
        fill_red = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        font_red = Font(color="991B1B", bold=True)

        ws.conditional_formatting.add(
            ata_range,
            CellIsRule(operator="greaterThanOrEqual", formula=["100"], stopIfTrue=False, fill=fill_green, font=font_green)
        )
        ws.conditional_formatting.add(
            ata_range,
            CellIsRule(operator="lessThan", formula=["100"], stopIfTrue=False, fill=fill_red, font=font_red)
        )

        # Freeze panes at E5
        ws.freeze_panes = "E5"

        # Column widths
        ws.column_dimensions["A"].width = 11
        ws.column_dimensions["B"].width = 25
        ws.column_dimensions["C"].width = 25
        ws.column_dimensions["D"].width = 8
        for col_idx in range(col_ata_start, col_sam_end + 1):
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = 9

    wb.save(output_path)
    print(f"✔ [DAILY ATA] Saved November Daily ATA Matrix Excel -> {output_path}")


def main():
    print("=" * 70)
    print(" 📆 GENERATING NOVEMBER 2026 DAILY ATA MATRIX (15 SUBSIDIARIES x 30 DAYS)")
    print("=" * 70)

    dataset = build_daily_ata_dataset()

    # Save JSON
    json_path = os.path.join(data_dir, "eu_daily_ata_matrix_2026_11.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"✔ [DAILY ATA] Saved structured JSON -> {json_path}")

    # Save Excel in data/
    xlsx_path = os.path.join(data_dir, "EU_Daily_ATA_Matrix_2026_11.xlsx")
    create_daily_ata_excel(dataset, xlsx_path)

    # Save backup in History_EU for latest survey dates
    latest_active = dataset["active_days"][-1] if dataset.get("active_days") else "11/04"
    latest_h_folder = f"2026 {latest_active.replace('/', '')}"
    target_dirs = [latest_h_folder, "2026 1104", "2026 1103", "2026 1102"]
    seen_dirs = set()
    for h_name in target_dirs:
        if h_name in seen_dirs:
            continue
        seen_dirs.add(h_name)
        h_dir = os.path.join(history_dir, h_name)
        if os.path.exists(h_dir):
            h_xlsx = os.path.join(h_dir, "EU_Daily_ATA_Matrix_2026_11.xlsx")
            shutil.copy2(xlsx_path, h_xlsx)
            print(f"✔ [DAILY ATA] Backed up to History_EU/{h_name}/EU_Daily_ATA_Matrix_2026_11.xlsx")

    print("\n🎉 [DAILY ATA MATRIX] November 2026 Daily ATA Generation Complete!")


if __name__ == "__main__":
    main()
