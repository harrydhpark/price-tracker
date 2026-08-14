# -*- coding: utf-8 -*-
import sys
import os
import openpyxl
from openpyxl.styles import Font, Alignment
import re
import json
import glob
import shutil

sys.stdout.reconfigure(encoding='utf-8')

# Source configurations
EU_SOURCES = {
    'mm-de': {'retailer': 'MediaMarkt', 'cc': 'DE', 'currency': 'EUR'},
    'mm-at': {'retailer': 'MediaMarkt', 'cc': 'AT', 'currency': 'EUR'},
    'mm-ch': {'retailer': 'MediaMarkt', 'cc': 'CH', 'currency': 'CHF'},
    'mm-es': {'retailer': 'MediaMarkt', 'cc': 'ES', 'currency': 'EUR'},
    'mm-nl': {'retailer': 'MediaMarkt', 'cc': 'NL', 'currency': 'EUR'},
    'currys': {'retailer': 'Currys', 'cc': 'UK', 'currency': 'GBP'},
    'fnac': {'retailer': 'Fnac', 'cc': 'FR', 'currency': 'EUR'},
    'elgiganten': {'retailer': 'Elgiganten', 'cc': 'SE', 'currency': 'SEK'},
    'mw-it': {'retailer': 'MediaWorld', 'cc': 'IT', 'currency': 'EUR'},
    'unieuro': {'retailer': 'Unieuro', 'cc': 'IT', 'currency': 'EUR'},
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
            if "H" in sub:
                year_val = 2026
            elif "F" in sub:
                year_val = 2025
            elif "D" in sub or "E" in sub:
                year_val = 2024
        
        # Fallback to title keywords
        if year_val is None:
            if any(x in title_upper for x in ["S90H", "S92H", "S95H", "S85H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "QN72H", "QN82H", "M70H", "M72H", "M80H", "M82H", "R95H", "LS03H", "U8000H", "U8070H", "U8079H", "U8075H", "U8090H", "2026"]):
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
            if any(x in model_code for x in ["C6", "G6", "B6", "W6", "M6", "QNED86B", "QNED80B", "QNED87B", "QNED81B", "QNED72B", "QNED7EB", "UA77", "MRGB87B", "MRGB87", "LX7B", "LX6", "QLED7EB", "MRGB96B", "NU850", "LB700"]):
                year_val = 2026
            # 2025 Codes
            elif any(x in model_code for x in ["C5", "G5", "B5", "W5", "M5", "QNED86A", "QNED80A", "QNED87A", "QNED87", "QNED72A", "QNED7EA", "UA75", "MRGB87A", "LX7A", "LX5", "QNED70A", "NANO81A", "NANO81", "NANO80A", "QNED93A"]):
                year_val = 2025
            # 2024 Codes
            elif any(x in model_code for x in ["C4", "G4", "B4", "M4", "UA73", "LX4"]):
                year_val = 2024
        
        # Fallback to title keywords
        if year_val is None:
            if any(x in title_upper for x in ["C6", "G6", "B6", "W6", "M6", "QNED86B", "QNED80B", "QNED87B", "QNED72B", "QNED7EB", "UA77", "2026"]):
                year_val = 2026
            elif any(x in title_upper for x in ["C5", "G5", "B5", "W5", "M5", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED7EA", "UA75", "2025"]):
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
            if parsed_code_size in [42, 43, 48, 50, 55, 65, 75, 77, 83, 85, 86, 98, 100]:
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

def clean_promotion_text(promo, brand, year, model_code, currency):
    if not promo or promo == "None":
        return "None"
    
    promo_upper = promo.upper()
    
    # 1. Cashback und oder 26% Rabatt auf Soundbar QS700F
    if "CASHBACK UND ODER 26%" in promo_upper or "CASHBACK AND/OR 26% OFF" in promo_upper:
        return "Samsung Cashback and/or 26% Off Soundbar QS700F"
        
    # 2. Gratis Music Studio 5
    if "MUSIC STUDIO 5" in promo_upper:
        return "Free Music Studio 5 Soundbar (HW-LS50H/EN)"
        
    # 3. mit kostenlosem Zusatzprodukt
    if "ZUSATZPRODUKT" in promo_upper or "WITH FREE PROMOTIONAL PRODUCT" in promo_upper:
        return "Free Promotional Product (Sound Device)"
        
    # 4. Restposten / Outlet
    if "RESTPOSTEN" in promo_upper:
        return "Clearance (Restposten)"
    if "OUTLET" in promo_upper:
        return "Outlet (Clearance)"
        
    # 5. SoundSuite / Soundbar (LG 2026)
    if "SOUNDSUITE" in promo_upper or "SOUNDBAR DAZU" in promo_upper:
        if brand.upper() == "LG" and year == 2026:
            return "Free SoundSuite/Soundbar with LG OLED TV 2026 Purchase"
            
    # 6. Sound Device geschenkt
    if "SOUND DEVICE GESCHENKT" in promo_upper:
        if year == 2026:
            return "Free Sound Device with 2026 TV Purchase"
            
    # 7. Aus unserer Werbung
    if "WERBUNG" in promo_upper or "WEEKLY AD" in promo_upper:
        return "Featured in Weekly Ad (Aus unserer Werbung)"
        
    # 8. Online Only
    if "ONLINE ONLY" in promo_upper or "ONLINE-ONLY" in promo_upper:
        return "Online Only"
        
    # 9. Direct Cut & Voucher Codes (Currys / UK & EU)
    if "DIRECT CUT" in promo_upper:
        return promo
        
    # 10. Sale / statt (Discount badges)
    if any(x in promo_upper for x in ["STATT", "WAS", "SPARA", "SAVE", "RABATT", "DISCOUNT"]):
        pct_match = re.search(r'(\d+)\s*%', promo)
        was_match = re.search(r'(?:was|statt|spara|save)\s*(?:chf|eur|gbp|sek|€|£)?\s*([\d’\x27\x60,.]+)', promo, re.IGNORECASE)
        
        pct = pct_match.group(1) if pct_match else None
        was_val = was_match.group(1).replace("’", "").replace("'", "").replace("`", "").strip() if was_match else None
        if was_val and (was_val.endswith(".") or was_val.endswith(",")):
            was_val = was_val[:-1]
            
        if pct and was_val:
            return f"Sale {pct}%; was {currency} {was_val}"
        elif was_val:
            return f"was {currency} {was_val}"
        elif pct:
            return f"Sale {pct}%"
            
    return promo

def clean_numeric_price(price_str):
    if price_str is None or price_str == "":
        return 0.0
    if isinstance(price_str, (int, float)):
        val = float(price_str)
        if 0 < val < 10.0 and round(val, 3) != round(val, 2):
            val = val * 1000.0
        return val if val >= 50.0 else 0.0
        
    clean_p = str(price_str).replace("€", "").replace("£", "").replace("kr", "").replace("SEK", "").replace("EUR", "").replace("GBP", "").replace("CHF", "").strip()
    
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
        
    # Set headers if sheet is empty
    headers = [
        "Brand", "Model Year", "Display Type", "Size (Inch)", "Model Code",
        f"Price ({currency})", "Shipping", "Installment", "Cashback", "General Promotions"
    ]
    if sheet.max_row <= 1:
        sheet.append(headers)
        
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
        # Determine cashback amount if explicitly containing "Cashback"
        cashback_val = 0
        promo_text = p.get("promo", "None") or "None"
        
        # Standardize promo text
        promo_text = clean_promotion_text(promo_text, brand, p["year"], p["model_code"], currency)
        
        if any(x in promo_text.upper() for x in ["CASHBACK", "캐시백", "REEMBOLSO", "RIMBORSO"]):
            cb_match = re.search(r'(?:cashback|캐시백|reembolso|rimborso)\s*(?:von|bis\s*zu)?\s*(?:chf|eur|gbp|sek|€|£)?\s*(\d+)', promo_text, re.IGNORECASE)
            if cb_match:
                cashback_val = int(cb_match.group(1))
            else:
                cb_match2 = re.search(r'(?:chf|eur|gbp|sek|€|£)?\s*(\d+)\s*(?:chf|eur|gbp|sek|€|£)?\s*(?:cashback|캐시백|reembolso|rimborso)', promo_text, re.IGNORECASE)
                if cb_match2:
                    cashback_val = int(cb_match2.group(1))
            if cashback_val < 10: # Ignore single-digit false positives (e.g. 2% or 2 years)
                cashback_val = 0
                    
        final_price = clean_numeric_price(p["price"])
        
        sheet.append([
            p["brand"],
            p["year"],
            p["display_type"],
            p["size"],
            p["model_code"],
            final_price,
            "Free",  # Shipping
            None,    # Installment
            cashback_val,
            promo_text
        ])
        added_count += 1
        
    print(f"    ➔ Added {added_count} live {brand} rows.")
    final_filename = save_workbook_with_retry(wb, filename)
    wb.close()
    return final_filename

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    # Resolve MMDD date
    from datetime import datetime
    today_mmdd = datetime.now().strftime("%m%d") # "0708"
    
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
        else:
            print(f"[SYNC] Creating new workbook: {excel_filename}")

    # Iterate over all EU sources and brands
    for src_key, cfg in EU_SOURCES.items():
        for brand in ["samsung", "lg"]:
            products_list = []
            
            if src_key == 'mm-ch':
                swiss_file = os.path.join(data_dir, f"price tracker_swiss_2026 {today_mmdd}_v1.xlsx")
                if not os.path.exists(swiss_file):
                    swiss_files = glob.glob(os.path.join(data_dir, "price tracker_swiss_2026 *.xlsx"))
                    swiss_files = [f for f in swiss_files if not os.path.basename(f).startswith("~$")]
                    if swiss_files:
                        swiss_files.sort()
                        swiss_file = swiss_files[-1]
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
                if src_key == 'mm-at':
                    pattern = os.path.join(data_dir, f"raw_mm-at_{brand}*.json")
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
                    name = item.get("name") or item.get("title") or ""
                    raw_price = item.get("price")
                    promo = item.get("promo") or "None"
                    if not name or len(name) < 10:
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
                    p_rec = {
                        "brand": brand.upper() if brand.lower() == "samsung" else "LG",
                        "year": year,
                        "display_type": display_type,
                        "size": size,
                        "model_code": model_code,
                        "price": price,
                        "promo": promo
                    }
                    if model_code in seen_codes:
                        if price < seen_codes[model_code]["price"]:
                            seen_codes[model_code] = p_rec
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
            
    print(f"\n[EU SYNC DONE] Saved successfully to {excel_filename}")
    
    # Auto-mirror updated Excel workbook to History_EU folder
    try:
        from datetime import datetime
        today_folder = datetime.now().strftime("%Y %m%d")
        hist_dir = os.path.abspath(os.path.join(data_dir, "..", "History_EU", today_folder))
        if not os.path.exists(hist_dir):
            os.makedirs(hist_dir)
        hist_file = os.path.join(hist_dir, os.path.basename(excel_filename))
        shutil.copy2(excel_filename, hist_file)
        print(f"  ➔ [MIRRORED TO HISTORY_EU] {hist_file}")
    except Exception as e_h:
        print(f"[WARN] Failed mirroring to History_EU: {e_h}")

if __name__ == "__main__":
    main()
