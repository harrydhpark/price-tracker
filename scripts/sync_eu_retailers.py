# -*- coding: utf-8 -*-
import sys
import os
import openpyxl
from openpyxl.styles import Font, Alignment
import re
import json
import glob
import shutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

# Source configurations
EU_SOURCES = {
    'mm-de': {'retailer': 'MediaMarkt', 'cc': 'DE', 'currency': 'EUR'},
    'mm-at': {'retailer': 'MediaMarkt', 'cc': 'AT', 'currency': 'EUR'},
    'mm-ch': {'retailer': 'MediaMarkt', 'cc': 'CH', 'currency': 'CHF'},
    'mm-es': {'retailer': 'MediaMarkt', 'cc': 'ES', 'currency': 'EUR'},
    'mm-nl': {'retailer': 'MediaMarkt', 'cc': 'NL', 'currency': 'EUR'},
    'currys': {'retailer': 'Currys', 'cc': 'UK', 'currency': 'GBP'},
    'boulanger': {'retailer': 'Boulanger', 'cc': 'FR', 'currency': 'EUR'},
    'mw-it': {'retailer': 'MediaWorld', 'cc': 'IT', 'currency': 'EUR'},
    'alza': {'retailer': 'Alza', 'cc': 'CZ', 'currency': 'CZK'},
    'mm-hu': {'retailer': 'MediaMarkt', 'cc': 'HU', 'currency': 'HUF'},
    'worten_pt': {'retailer': 'Worten', 'cc': 'PT', 'currency': 'EUR'},
    'elgiganten_se': {'retailer': 'Elgiganten', 'cc': 'SE', 'currency': 'SEK'},
    'mediaexpert_pl': {'retailer': 'MediaExpert', 'cc': 'PL', 'currency': 'PLN'},
    'emag_ro': {'retailer': 'eMAG', 'cc': 'RO', 'currency': 'RON'},
    'kotsovolos_gr': {'retailer': 'Kotsovolos', 'cc': 'GR', 'currency': 'EUR'},
}

def save_workbook_with_retry(wb, filename):
    base, ext = os.path.splitext(filename)
    version = 1
    current_filename = filename
    saved = False
    
    while not saved:
        try:
            wb.save(current_filename)
            saved = True
            print(f"  ➔ [SAVED] Successfully saved to: {current_filename}")
        except PermissionError:
            v_match = re.search(r'(_v|v)(\d+)$', base)
            if v_match:
                prefix = v_match.group(1)
                num = int(v_match.group(2)) + 1
                base_clean = base[:v_match.start()]
                current_filename = f"{base_clean}{prefix}{num}{ext}"
                base = f"{base_clean}{prefix}{num}"
            else:
                current_filename = f"{base}_v{version}{ext}"
                version += 1
            print(f"  ➔ [LOCKED] Permission denied. Retrying with: {current_filename}...")
            
    return current_filename

def classify_year(brand, model_code, title_upper):
    year_val = None  # Default value is always None
    
    # Samsung rules
    if brand.upper() == "SAMSUNG":
        if model_code != "Unknown" and len(model_code) > 3:
            sub = model_code[2:]
            if "FUXX" in sub:
                year_val = 2025
            elif "H" in sub:
                year_val = 2026
            elif "F" in sub:
                year_val = 2025
            elif "D" in sub or "E" in sub:
                year_val = 2024
        
        # Fallback to title keywords
        if year_val is None:
            if any(x in title_upper for x in ["S90H", "S92H", "S95H", "S85H", "S99H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "QN72H", "QN82H", "M70H", "M72H", "M80H", "M82H", "R95H", "R85H", "R86H", "LS03H", "U8000H", "U8070H", "U8079H", "U8075H", "U8090H", "2026"]):
                year_val = 2026
            elif any(x in title_upper for x in ["S90F", "S92F", "S95F", "S85F", "QN900F", "QN800F", "QN95F", "QN90F", "QN85F", "QN80F", "QN70F", "QN72F", "QN82F", "M70F", "M72F", "M80F", "M82F", "R95F", "LS03F", "U8000F", "U8070F", "U8079F", "U8075F", "U8090F", "2025"]):
                year_val = 2025
            elif any(x in title_upper for x in ["S90D", "S95D", "S85D", "QN900D", "QN800D", "QN95D", "QN90D", "QN85D", "QN80D", "QN70D", "LS03D", "U8000D", "U8090D", "2024"]):
                year_val = 2024

    # LG rules
    elif brand.upper() == "LG":
        # Check model code first
        if model_code != "Unknown":
            # 2026 Codes
            if any(x in model_code for x in ["C6", "G6", "B6", "W6", "M6", "QNED86B", "QNED85B", "QNED84B", "QNED83B", "QNED82B", "QNED81B", "QNED80B", "QNED87B", "QNED8EB", "QNED8MB", "QNED93B", "QNED91B", "QNED72B", "QNED71B", "QNED70B", "QNED7EB", "NANO82B", "NANO81B", "NANO80B", "UA77", "MRGB87B", "MRGB87", "MRGB86B", "MRGB86", "MRGB96B", "MRGB96", "LX7B", "LX6", "27LX6TDGA", "27LX6", "STANBYME 2", "STANBYME", "QLED7EB", "NU850", "NU800", "NU8E0", "NU80", "NU8", "LB700", "LB70", "LB650", "LB65"]):
                year_val = 2026
            # 2025 Codes
            elif any(x in model_code for x in ["C5", "G5", "B5", "W5", "M5", "QNED86A", "QNED86", "QNED85A", "QNED85", "QNED84A", "QNED84", "QNED83A", "QNED83", "QNED82A", "QNED82", "QNED81A", "QNED81", "QNED80A", "QNED80", "QNED87A", "QNED87", "QNED75A", "QNED75", "QNED72A", "QNED7EA", "UA75", "UA74", "MRGB87A", "LX7A", "LX5", "QNED70A", "NANO82A", "NANO81A", "NANO81", "NANO80A", "NANO80", "QNED93A", "QNED93", "QNED91A", "QNED91", "QNED99"]):
                year_val = 2025
            # 2024 Codes
            elif any(x in model_code for x in ["C4", "G4", "B4", "M4", "UA73", "LX4"]):
                year_val = 2024
        
        # Fallback to title keywords
        if year_val is None:
            if any(x in title_upper for x in ["C6", "G6", "B6", "W6", "M6", "QNED86B", "QNED85B", "QNED84B", "QNED83B", "QNED82B", "QNED81B", "QNED80B", "QNED87B", "QNED8EB", "QNED8MB", "QNED72B", "QNED71B", "QNED70B", "QNED7EB", "UA77", "MRGB87B", "MRGB86B", "MRGB96B", "MRGB96", "27LX6TDGA", "27LX6", "STANBYME 2", "STANBYME", "NU800", "NU850", "NU8E0", "NU80", "LB700", "LB70", "LB650", "LB65", "2026"]):
                year_val = 2026
            elif any(x in title_upper for x in ["C5", "G5", "B5", "W5", "M5", "QNED86A", "QNED86", "QNED85A", "QNED85", "QNED84A", "QNED84", "QNED83A", "QNED83", "QNED82A", "QNED82", "QNED81A", "QNED81", "QNED80A", "QNED80", "QNED87A", "QNED75A", "QNED75", "QNED72A", "QNED70A", "QNED7EA", "UA75", "UA74", "NANO82A", "NANO81A", "NANO80A", "NANO80", "QNED93A", "QNED93", "QNED91A", "QNED91", "QNED99", "2025"]):
                year_val = 2025
            elif any(x in title_upper for x in ["C4", "G4", "B4", "M4", "2024"]):
                year_val = 2024
                
        if model_code != "Unknown" and "UA73" in model_code and "2025" in title_upper:
            year_val = 2025
            
    return year_val

def parse_product_name(title, brand):
    title_upper = title.upper()
    model_code = "Unknown"
    
    # 1. Size (Zoll / " / Inch / cm)
    size_val = 55  # Default fallback
    size_match = re.search(r'(\d+)\s*"', title)
    if not size_match:
        size_match = re.search(r'(\d+)\s*Zoll', title, re.IGNORECASE)
    if not size_match:
        size_match = re.search(r'(\d+)\s*inch', title, re.IGNORECASE)
    if not size_match:
        size_match = re.search(r'(\d{2,3})\s*(?:cm|pouces)', title, re.IGNORECASE)
        if size_match:
            cm_val = int(size_match.group(1))
            if cm_val > 100:
                size_val = int(round(cm_val / 2.54))
            elif cm_val >= 22:
                size_val = cm_val
            size_match = True
            
    if isinstance(size_match, re.Match):
        size_val = int(size_match.group(1))
    
    # 2. Model Code
    if brand.upper() == "LG":
        oled_match = re.search(r'\b(OLED\d{2,3}[A-Z]{1,3}\d{0,2}[A-Z]*)\b', title_upper)
        if oled_match:
            model_code = oled_match.group(1)
        else:
            oled_short = re.search(r'\b(\d{2,3})([BCGMW][456]\d?[A-Z]{2,3})\b', title_upper)
            if oled_short and "OLED" in title_upper:
                model_code = f"OLED{oled_short.group(1)}{oled_short.group(2)}"
            else:
                lg_code_match = re.search(r'\b(\d{2,3}(?:QNED|NANO|MRGB|LX|NU|UA|UT|UR|UQ|LB|QLED)\w*)\b', title_upper)
                if lg_code_match:
                    model_code = lg_code_match.group(1)
                else:
                    words = title_upper.split()
                    for w in words:
                        clean_w = re.sub(r'[^\w-]', '', w)
                        if any(junk in clean_w for junk in ["LEDLG", "OLEDLG", "TV", "CINEMA"]):
                            continue
                        if any(char.isdigit() for char in clean_w) and len(clean_w) >= 5:
                            model_code = clean_w
                            break
        # Smart fallback for LG series when model_code is Unknown or generic
        if model_code == "Unknown" or not any(x in model_code for x in ["QNED", "OLED", "MRGB", "NANO", "LX", "NU", "UA", "UT", "UR", "UQ", "LB", "QLED"]):
            if "27LX6" in title_upper or "STANBYME 2" in title_upper or "STANBYME" in title_upper:
                model_code = "27LX6TDGA"
                size_val = 27
            elif "QNED86B" in title_upper or "QNED86" in title_upper:
                model_code = f"{size_val}QNED86B"
            elif "QNED81B" in title_upper or "QNED81" in title_upper:
                model_code = f"{size_val}QNED81B"
            elif "QNED80B" in title_upper or "QNED80" in title_upper:
                model_code = f"{size_val}QNED80B"
            elif "QNED72B" in title_upper or "QNED72" in title_upper:
                model_code = f"{size_val}QNED72B"
            elif "QNED71B" in title_upper or "QNED71" in title_upper:
                model_code = f"{size_val}QNED71B"
            elif "QNED70B" in title_upper or "QNED70" in title_upper:
                model_code = f"{size_val}QNED70B"
            elif "MRGB87B" in title_upper or "MRGB87" in title_upper:
                model_code = f"{size_val}MRGB87B"
            elif "MRGB96B" in title_upper or "MRGB96" in title_upper:
                model_code = f"{size_val}MRGB96B"
    else: # SAMSUNG or others
        words = title_upper.split()
        for w in words:
            clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace('"', '').strip()
            if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                if any(clean_w.startswith(pre) for pre in ["GQ", "TQ", "QE", "UE", "GU", "MRE"]):
                    model_code = clean_w
                    break
        if model_code == "Unknown":
            patterns = [
                r'\b(QN\d{2,3}[FH])\b',
                r'\b(S\d{2,3}[FH])\b',
                r'\b(U\d{3,4}[FH])\b',
                r'\b(M\d{2,3}[FH])\b',
                r'\b(R\d{2,3}[FH])\b',
                r'\b(LS03[A-Z]{1,2})\b',
                r'\b(F\d{4})\b',
                r'\b(MR\d{2,3}[FH])\b'
            ]
            for pat in patterns:
                m = re.search(pat, title_upper)
                if m:
                    series = m.group(1)
                    if series.startswith('S') or series.startswith('QN') or series.startswith('LS'):
                        model_code = f"QE{size_val}{series}"
                    elif series.startswith('U') or series.startswith('M') or series.startswith('F'):
                        model_code = f"UE{size_val}{series}"
                    elif series.startswith('R') or series.startswith('MR'):
                        model_code = f"MRE{size_val}{series}"
                    break
        if model_code == "Unknown":
            for w in words:
                clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace('"', '').strip()
                if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                    model_code = clean_w
                    break
        
    # Always prioritize model code size digits if valid 2-digit screen size exists (e.g. TQ65S92H -> 65)
    if model_code != "Unknown":
        code_nums = re.findall(r'\d+', model_code)
        if code_nums and len(code_nums[0]) in [2, 3]:
            parsed_code_size = int(code_nums[0])
            if parsed_code_size in [24, 27, 32, 40, 42, 43, 48, 50, 55, 65, 70, 75, 77, 83, 85, 86, 97, 98, 100, 115]:
                size_val = parsed_code_size
            
    # 3. Year
    year_val = classify_year(brand, model_code, title_upper)
    
    # 4. Display Type
    display_type = "LED"
    code_upper = model_code.upper()
    if brand.upper() == "SAMSUNG":
        if "OLED" in code_upper or any(x in code_upper for x in ["S90", "S91", "S92", "S93", "S94", "S95", "S99", "S85", "S83", "S84", "S86", "S89"]) or bool(re.search(r'S(?:9[0-9]|8[0-9])', code_upper)):
            display_type = "OLED"
        elif "MRE" in code_upper or "MRGB" in code_upper:
            display_type = "Micro RGB"
        elif "QN" in code_upper:
            display_type = "Neo QLED"
        elif any(x in code_upper for x in ["M70", "M72", "M74", "M80", "M82", "M84"]) or "MINI LED" in title_upper:
            display_type = "Mini LED"
        elif "Q" in code_upper or "LS" in code_upper:
            display_type = "QLED"
        elif any(x in code_upper for x in ["U8", "UA", "UT", "UR", "UQ", "UX"]):
            display_type = "UHD 4K"
    elif brand.upper() == "LG":
        if "MRGB" in code_upper or "MRGB" in title_upper:
            display_type = "Micro RGB"
        elif "QNED" in code_upper or "QNED" in title_upper:
            display_type = "QNED"
        elif "OLED" in code_upper or "OLED" in title_upper or re.search(r'OLED\d{2}', code_upper):
            display_type = "OLED evo" if ("EVO" in title_upper or any(x in code_upper for x in ["G5", "G6", "C5", "C6", "M5", "M6"])) else "OLED"
        elif "NANO" in code_upper or "NANO" in title_upper:
            display_type = "NanoCell"
        elif any(x in code_upper for x in ["NU900", "NU90", "NU85", "NU80", "NU800", "NU850", "LB650", "LB", "UA75", "UA73", "UA77", "UT", "UR", "UQ", "LQ"]):
            display_type = "UHD 4K"
        elif "LX" in code_upper or "STANBYME" in code_upper:
            display_type = "Lifestyle"

    return model_code, size_val, year_val, display_type

from promo_classifier import classify_promotions

def clean_promotion_text(promo, brand, year, model_code, currency):
    if not promo or str(promo).strip() in ["", "None", "0"]:
        return "None"
    orig, cb, price_p, non_price_p = classify_promotions(
        promo_raw=promo,
        brand=brand,
        year=year,
        model_code=model_code,
        currency=currency
    )
    parts = []
    if price_p != "None":
        parts.append(price_p)
    if non_price_p != "None":
        parts.append(non_price_p)
    return "; ".join(parts) if parts else "None"

def clean_numeric_price(price_str):
    if price_str is None or price_str == "":
        return 0.0
    if isinstance(price_str, (int, float)):
        val = float(price_str)
        if 0 < val < 10.0 and round(val, 3) != round(val, 2):
            val = val * 1000.0
        return val if val >= 50.0 else 0.0
        
    clean_p = str(price_str).replace("€", "").replace("£", "").replace("kr", "").replace("SEK", "").replace("EUR", "").replace("GBP", "").replace("CHF", "").replace("CZK", "").replace("Kč", "").replace("HUF", "").replace("Ft", "").replace("PLN", "").replace("zł", "").strip()
    
    # European format check: "1.799", "2.499", "1.499"
    if re.match(r'^\d{1,3}\.\d{3}$', clean_p):
        clean_p = clean_p.replace(".", "")
    elif re.match(r'^\d{1,3},\d{3}$', clean_p):
        clean_p = clean_p.replace(",", "")
    elif "," in clean_p and "." in clean_p:
        if clean_p.find(".") < clean_p.find(","):
            clean_p = clean_p.replace(".", "").replace(",", ".")
        else:
            clean_p = clean_p.replace(",", "")
    elif "," in clean_p:
        parts = clean_p.split(",")
        if len(parts[-1]) == 2:
            clean_p = clean_p.replace(",", ".")
        else:
            clean_p = clean_p.replace(",", "")
            
    clean_p = re.sub(r'[^\d.]', '', clean_p)
    try:
        val = float(clean_p) if clean_p else 0.0
        if 0 < val < 10.0:
            val = val * 1000.0
        return val if val >= 50.0 else 0.0
    except ValueError:
        return 0.0

def sync_retailer_sheet(filename, sheetname, brand, products, currency):
    if not os.path.exists(filename):
        wb = openpyxl.Workbook()
        # Remove default sheet
        default_sheet = wb.active
        wb.remove(default_sheet)
    else:
        wb = openpyxl.load_workbook(filename)
        
    print(f"  ➔ Syncing to sheet: {sheetname} ({currency})...")
    
    # Get or create sheet
    if sheetname in wb.sheetnames:
        sheet = wb[sheetname]
    else:
        sheet = wb.create_sheet(sheetname)
        
    # Set or update headers (12-column standard)
    headers = [
        "Brand", "Model Year", "Display Type", "Size (Inch)", "Model Code",
        f"Price ({currency})", f"Original Price ({currency})", "Shipping", "Installment",
        "Cashback", "Price Promotion", "Non-Price Promotion"
    ]
    # Unconditionally enforce standard 12-column headers on every sync
    for col_idx, h in enumerate(headers, 1):
        sheet.cell(row=1, column=col_idx, value=h)
        
    # Delete old rows for this brand
    removed_count = 0
    for r in range(sheet.max_row, 1, -1):
        brand_val = sheet.cell(row=r, column=1).value
        if str(brand_val).upper() == str(brand).upper():
            sheet.delete_rows(r)
            removed_count += 1
    if removed_count > 0:
        print(f"    ➔ Removed {removed_count} obsolete {brand} rows.")
        
    # Append new rows
    added_count = 0
    for p in products:
        final_price = clean_numeric_price(p["price"])
        raw_orig_p = clean_numeric_price(p.get("original_price") or p.get("orig_price") or p.get("was_price") or p.get("uvp", 0.0))
        
        orig_price, cb_val, price_promo, non_price_promo = classify_promotions(
            promo_raw=p.get("promo", "None"),
            title_raw=p.get("title", ""),
            brand=p["brand"],
            year=p["year"],
            model_code=p["model_code"],
            price=final_price,
            currency=currency,
            existing_original_price=raw_orig_p
        )
        
        # Determine cashback amount if explicitly provided and not found by classifier
        if cb_val == 0 and p.get("cashback") and isinstance(p["cashback"], (int, float)) and p["cashback"] > 0:
            cb_val = int(round(p["cashback"]))
            curr_sym = "£" if currency == "GBP" else ("CHF " if currency == "CHF" else "€")
            if price_promo == "None":
                price_promo = f"Cashback: {curr_sym}{cb_val}"
            elif f"{cb_val}" not in price_promo:
                price_promo = f"Cashback: {curr_sym}{cb_val}; {price_promo}"
                
        sheet.append([
            p["brand"],
            p["year"],
            p["display_type"],
            p["size"],
            p["model_code"],
            final_price,
            orig_price if orig_price > 0 else None,
            "Free",  # Shipping
            None,    # Installment
            cb_val,
            price_promo,
            non_price_promo
        ])
        added_count += 1
        
    print(f"    ➔ Added {added_count} live {brand} rows.")
    final_filename = save_workbook_with_retry(wb, filename)
    wb.close()
    return final_filename

def purge_unrefreshed_sheets(filename, keep_sheets):
    """Remove every sheet that was not rewritten in this run. Returns list of removed sheet names."""
    if not os.path.exists(filename):
        return []
    wb = openpyxl.load_workbook(filename)
    removed = [n for n in wb.sheetnames if n not in keep_sheets]
    if len(removed) == len(wb.sheetnames):
        wb.close()
        raise RuntimeError("Refusing to purge: no sheet was refreshed in this run.")
    for n in removed:
        wb.remove(wb[n])
    if removed:
        wb.save(filename)
        print(f"  🧹 [STALE-SHEET ISOLATION] Removed {len(removed)} carried-over sheets: {removed}")
    wb.close()
    return removed


def write_sync_manifest(data_dir, excel_filename, refreshed_sheets, purged):
    from datetime import datetime as _dt
    m_d = re.search(r'(\d{4})\s+(\d{4})', os.path.basename(excel_filename))
    tag = f"{m_d.group(1)}{m_d.group(2)}" if m_d else _dt.now().strftime('%Y%m%d')
    run_dir = os.path.join(data_dir, "runs", f"eu_{tag}")
    os.makedirs(run_dir, exist_ok=True)
    countries = sorted({s.split("_")[1] for s in refreshed_sheets if s.count("_") >= 2})
    manifest = {
        "workbook": os.path.basename(excel_filename),
        "generated_at": _dt.now().isoformat(timespec="seconds"),
        "refreshed_sheets": sorted(refreshed_sheets),
        "refreshed_countries": countries,
        "purged_sheets": purged,
    }
    with open(os.path.join(run_dir, "sync_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    # Resolve MMDD date
    from datetime import datetime
    target_date = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        target_date = sys.argv[1]
    elif "--date" in sys.argv:
        idx = sys.argv.index("--date")
        if idx + 1 < len(sys.argv):
            target_date = sys.argv[idx + 1]
            
    today_mmdd = target_date if target_date else datetime.now().strftime("%m%d")
    
    excel_filename = os.path.join(data_dir, f"price tracker_EU_2026 {today_mmdd}_v1.xlsx")
    
    # Check if there is an existing file for today to append/modify
    latest_files = glob.glob(os.path.join(data_dir, f"price tracker_EU_2026 {today_mmdd}*.xlsx"))
    latest_files = [f for f in latest_files if not os.path.basename(f).startswith("~$")]
    if latest_files:
        latest_files.sort()
        excel_filename = latest_files[-1]
        print(f"[SYNC] Found existing workbook: {excel_filename}")
    else:
        # Check if there is a previous date workbook to clone
        prev_files = glob.glob(os.path.join(data_dir, "price tracker_EU_2026 *.xlsx"))
        prev_files = [f for f in prev_files if not os.path.basename(f).startswith("~$")]
        if prev_files:
            prev_files.sort()
            prev_file = prev_files[-1]
            print(f"[SYNC] Cloning latest workbook: {prev_file} -> {excel_filename}")
            shutil.copyfile(prev_file, excel_filename)
    # Mandatory Pre-flight Live Assertion Gate
    print("=" * 65)
    print(f" 🛡️ MANDATORY PRE-FLIGHT LIVE ASSERTION GATE (Survey Date: {today_mmdd})")
    print("=" * 65)
    today_date_str = datetime.now().strftime("%Y-%m-%d")
    # Raw files must have been written ON the survey date (target date if given, else today).
    expected_date_str = f"{datetime.now().year}-{today_mmdd[:2]}-{today_mmdd[2:]}"
    stale_files = []
    checked_count = 0
    for s_key in EU_SOURCES:
        if s_key == 'mm-ch':
            continue
        for b in ["samsung", "lg"]:
            r_path = os.path.join(data_dir, f"raw_{s_key}_{b}.json")
            if not os.path.exists(r_path):
                g_cands = glob.glob(os.path.join(data_dir, f"raw_{s_key}_{b}*.json"))
                if g_cands:
                    r_path = g_cands[0]
            if os.path.exists(r_path):
                mtime = datetime.fromtimestamp(os.path.getmtime(r_path)).strftime("%Y-%m-%d")
                fsize = os.path.getsize(r_path)
                checked_count += 1
                if fsize < 100:
                    stale_files.append((os.path.basename(r_path), "EMPTY FILE (<100B)"))
                elif mtime not in (expected_date_str, today_date_str):
                    stale_files.append((os.path.basename(r_path), f"{mtime} (expected {expected_date_str} or {today_date_str})"))
            else:
                stale_files.append((f"raw_{s_key}_{b}.json", "MISSING"))
                
    if stale_files:
        print(f"❌ [ASSERTION FAILURE] Found {len(stale_files)} invalid or missing raw datasets:")
        for fname, f_date in stale_files:
            print(f"   • {fname}: Status {f_date}")
        raise RuntimeError(f"PRE-FLIGHT ASSERTION FAILED: {len(stale_files)} files require valid live datasets.")
    print(f"✅ All {checked_count} raw EU datasets verified fresh for today ({today_date_str})!\n")

    # Iterate over all EU sources and brands
    refreshed_sheets = set()
    for src_key, cfg in EU_SOURCES.items():
        for brand in ["samsung", "lg"]:
            products_list = []
            
            if src_key == 'mm-ch':
                swiss_file = os.path.join(data_dir, f"price tracker_swiss_2026 {today_mmdd}_v1.xlsx")
                # [2026-10-08] No fallback to an older Swiss workbook (that injected stale CH prices).
                if not os.path.exists(swiss_file):
                    print(f"  ⏸️ [CH] No Swiss workbook for {today_mmdd}; CH sheets not refreshed (kept on last release).")
                if os.path.exists(swiss_file):
                    try:
                        wb_s = openpyxl.load_workbook(swiss_file, data_only=True)
                        s_name = "MediaMarkt_Samsung_Full" if brand.lower() == "samsung" else "MediaMarkt_LG_Full"
                        if s_name in wb_s.sheetnames:
                            ws_s = wb_s[s_name]
                            for r in range(2, ws_s.max_row + 1):
                                b_v = ws_s.cell(row=r, column=1).value
                                yr_v = ws_s.cell(row=r, column=2).value
                                disp_v = ws_s.cell(row=r, column=3).value
                                sz_v = ws_s.cell(row=r, column=4).value
                                code_v = ws_s.cell(row=r, column=5).value
                                pr_v = ws_s.cell(row=r, column=6).value
                                cb_v = ws_s.cell(row=r, column=9).value or 0
                                promo_v = ws_s.cell(row=r, column=10).value or "None"
                                if code_v and pr_v and str(code_v).upper() != "UNKNOWN":
                                    products_list.append({
                                        "brand": str(b_v).strip() if b_v else brand.upper(),
                                        "year": int(yr_v) if yr_v else 2025,
                                        "display_type": str(disp_v).strip() if disp_v else "LED",
                                        "size": int(sz_v) if sz_v else 55,
                                        "model_code": str(code_v).strip(),
                                        "price": float(pr_v),
                                        "promo": str(promo_v),
                                        "cashback": int(cb_v) if cb_v else 0
                                    })
                        wb_s.close()
                    except Exception as e_s:
                        print(f"[WARN] Failed loading Swiss Excel for mm-ch: {e_s}")
            else:
                direct_file = os.path.join(data_dir, f"raw_{src_key}_{brand}.json")
                if os.path.exists(direct_file):
                    json_files = [direct_file]
                else:
                    pattern = os.path.join(data_dir, f"raw_{src_key}_{brand}*.json")
                    json_files = glob.glob(pattern)
                
                scraped_items = []
                for jf in json_files:
                    try:
                        with open(jf, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, dict) and "items" in data:
                                scraped_items.extend(data["items"])
                            elif isinstance(data, list):
                                scraped_items.extend(data)
                    except Exception as e:
                        print(f"[WARN] Failed to load JSON {jf}: {e}")
                        
                if not scraped_items:
                    continue
                    
                seen_codes = {}
                for item in scraped_items:
                    if not isinstance(item, dict):
                        continue
                    if item.get("model_code") and item.get("year") in [2025, 2026] and item.get("size", 0) >= 22:
                        model_code = item["model_code"]
                        year = item["year"]
                        size = item["size"]
                        # Cross-verify size from model code if model code explicitly contains standard screen size
                        m_c_sz = re.search(r'(?:^|[A-Z]{1,3})(\d{2,3})(?:[A-Z]|$)', model_code.upper())
                        if m_c_sz:
                            parsed_sz = int(m_c_sz.group(1))
                            if parsed_sz in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27]:
                                if not (size in [85, 86] and parsed_sz in [85, 86]):
                                    size = parsed_sz
                        display_type = item.get("display") or item.get("display_type") or "LED"
                        mc_up = model_code.upper()
                        if brand.lower() == "lg":
                            if any(k in mc_up for k in ["NU800", "NU850", "NU8E0", "NU80", "NU85", "UA75", "UA77", "UT", "UR", "UQ", "LQ", "LB"]):
                                display_type = "UHD 4K"
                            elif "QNED" in mc_up:
                                display_type = "QNED"
                            elif "MRGB" in mc_up:
                                display_type = "Micro RGB"
                            elif "NANO" in mc_up:
                                display_type = "NanoCell"
                        elif brand.lower() == "samsung":
                            if any(k in mc_up for k in ["U80", "U85", "U8", "U900", "UA", "UT", "UR", "UQ"]):
                                display_type = "UHD 4K"
                            elif any(k in mc_up for k in ["MRGB", "MRE", "TMR", "R85H", "R95H", "MR95"]):
                                display_type = "Micro RGB"
                        price = clean_numeric_price(item.get("price"))
                        promo = item.get("promo") or item.get("promotions") or "None"
                    else:
                        name = item.get("name") or item.get("title") or ""
                        raw_price = item.get("price")
                        promo = item.get("promo") or "None"
                        if not name:
                            continue
                        name_upper = name.upper()
                        if any(x in name_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "ZUBEHÖR", "HALTERUNG", "WALLMOUNT", "CORNICE", "GALAXY BUDS"]):
                            continue
                        if any(x in name_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT", "REACONDICIONADO", "RICONDIZIONATO"]):
                            continue
                        model_code, size, year, display_type = parse_product_name(name, brand)
                        if size < 22 or year not in [2025, 2026]:
                            continue
                        price = clean_numeric_price(raw_price)
                        
                    if price <= 0.0:
                        continue
                    cashback = clean_numeric_price(item.get("cashback", 0))
                    orig_p = clean_numeric_price(item.get("original_price") or item.get("orig_price") or item.get("was_price") or item.get("uvp", 0.0))
                    p_rec = {
                        "brand": brand.upper() if brand.lower() == "samsung" else "LG",
                        "year": year,
                        "display_type": display_type,
                        "size": size,
                        "model_code": model_code,
                        "price": price,
                        "original_price": orig_p,
                        "promo": promo,
                        "cashback": cashback,
                        "title": item.get("title") or item.get("name", "")
                    }
                    if model_code in seen_codes:
                        if price < seen_codes[model_code]["price"]:
                            seen_codes[model_code] = p_rec
                        elif seen_codes[model_code].get("cashback", 0) == 0 and cashback > 0:
                            seen_codes[model_code]["cashback"] = cashback
                            if seen_codes[model_code].get("promo") in ["None", ""]:
                                seen_codes[model_code]["promo"] = promo
                            if not seen_codes[model_code].get("original_price") and orig_p > 0:
                                seen_codes[model_code]["original_price"] = orig_p
                    else:
                        seen_codes[model_code] = p_rec
                products_list = list(seen_codes.values())
                
            if not products_list:
                continue
                
            products_list.sort(key=lambda x: (x["size"], x["model_code"]))
            sheetname = f"{cfg['retailer']}_{cfg['cc']}_{brand.upper() if brand.lower() == 'samsung' else 'LG'}_Full"
            excel_filename = sync_retailer_sheet(
                excel_filename, sheetname,
                "Samsung" if brand.lower() == "samsung" else "LG",
                products_list, cfg["currency"]
            )
            refreshed_sheets.add(sheetname)

    # [2026-10-08] Stale-sheet isolation: the workbook is cloned from the previous survey, so every
    # sheet NOT rewritten in this run (GR/HU/PL/PT/RO/SE/CZ, or a source whose raw file was empty)
    # used to be carried over and recorded into price_history.db AS TODAY'S PRICES.
    # Those sheets are now removed; their countries keep their last released survey (release manifest).
    purged = purge_unrefreshed_sheets(excel_filename, refreshed_sheets)
    write_sync_manifest(data_dir, excel_filename, refreshed_sheets, purged)

    # Auto-synchronize master_product_urls.json with all active EU models
    try:
        from datetime import datetime
        master_registry_path = os.path.join(data_dir, "master_product_urls.json")
        if os.path.exists(master_registry_path):
            with open(master_registry_path, "r", encoding="utf-8") as f_m:
                master_urls = json.load(f_m)
            today_str = datetime.now().strftime("%Y-%m-%d")
            reg_added = 0
            
            for src_key, cfg in EU_SOURCES.items():
                for brand in ["samsung", "lg"]:
                    raw_file = os.path.join(data_dir, f"raw_{src_key}_{brand}.json")
                    if os.path.exists(raw_file):
                        try:
                            with open(raw_file, "r", encoding="utf-8") as f_r:
                                raw_items = json.load(f_r)
                            if isinstance(raw_items, dict) and "items" in raw_items:
                                raw_items = raw_items["items"]
                            for it in raw_items:
                                mc = it.get("model_code")
                                url = it.get("link") or it.get("url") or ""
                                if mc and mc != "Unknown" and url.startswith("http"):
                                    # Pan-European Blacklisted 3rd-Party Marketplace Guard
                                    u_lower = url.lower()
                                    if "mediamarkt" in u_lower or "mediaworld" in u_lower:
                                        m_pid = re.search(r'-(\d{8,10})\.html', url)
                                        if m_pid and (len(m_pid.group(1)) >= 9 or m_pid.group(1).startswith(('14', '15', '16', '17', '18'))):
                                            continue
                                    if "offertype=marketplace" in u_lower:
                                        continue
                                    if "worten.pt" in u_lower and "seller=" in u_lower and "worten" not in u_lower.split("seller=")[1].split("&")[0]:
                                        continue
                                    if "emag.ro" in u_lower and ("/partener-" in u_lower or "seller_id=" in u_lower):
                                        continue
                                    key = f"{cfg['cc']}_{cfg['retailer'].upper()}_{mc}"
                                    if key not in master_urls:
                                        master_urls[key] = {
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
                                        reg_added += 1
                                    else:
                                        master_urls[key]["url"] = url
                                        master_urls[key]["last_updated"] = today_str
                        except Exception:
                            pass
            with open(master_registry_path, "w", encoding="utf-8") as f_m:
                json.dump(master_urls, f_m, ensure_ascii=False, indent=2)
            if reg_added > 0:
                print(f"  ➔ [MASTER REGISTRY AUTO-SYNC] Auto-registered {reg_added} new EU models into master_product_urls.json")
    except Exception as e_reg:
        print(f"[WARN] Failed auto-syncing master_product_urls.json: {e_reg}")

    print(f"\n[EU SYNC DONE] Saved successfully to {excel_filename}")
    
    # [2026-10-08] DB recording and History_EU mirroring were done here BEFORE any quality gate ran,
    # so failed/partial surveys became "history". Both now happen only in
    # scripts/release_by_country.py, per country, after the gates pass.
    print("  ⏭️ DB write / History_EU mirror deferred -> run: "
          f"python scripts/release_by_country.py --excel \"{excel_filename}\" --apply")

    try:
        from scrape_logger import emit_summary
        emit_summary(
            country="EU",
            retailer="Pan_EU_Retailers",
            brand="ALL",
            total_extracted=0,
            final_deduplicated=0,
            execution_time_sec=0.0
        )
    except Exception:
        pass

if __name__ == "__main__":
    main()
