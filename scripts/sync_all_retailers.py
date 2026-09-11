import sys
import os
import openpyxl
from openpyxl.styles import Font, Alignment
import re
import json
import glob
import shutil
import copy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

def find_latest_file(pattern_prefix):
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    history_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "History"))
    files = glob.glob(os.path.join(data_dir, pattern_prefix + "*.xlsx"))
    files.extend(glob.glob(os.path.join(history_dir, "*", pattern_prefix + "*.xlsx")))
    files = [f for f in files if not os.path.basename(f).startswith("~$")]
    if not files:
        return None
    files.sort()
    return files[-1]

def load_digitec_live():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    try:
        with open(os.path.join(data_dir, "raw_digitec_samsung.json"), "r", encoding="utf-8") as f:
            samsungs = json.load(f)
        with open(os.path.join(data_dir, "raw_digitec_lg.json"), "r", encoding="utf-8") as f:
            lgs = json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load Digitec live JSONs: {e}")
        samsungs, lgs = [], []
        
    s_filtered = [p for p in samsungs if p.get("size", 0) >= 22]
    l_filtered = [p for p in lgs if p.get("size", 0) >= 22]
    return s_filtered, l_filtered

def load_interdiscount_live():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    try:
        with open(os.path.join(data_dir, "raw_interdiscount_samsung.json"), "r", encoding="utf-8") as f:
            samsungs = json.load(f)
        with open(os.path.join(data_dir, "raw_interdiscount_lg.json"), "r", encoding="utf-8") as f:
            lgs = json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load Interdiscount live JSONs: {e}")
        samsungs, lgs = [], []
        
    s_filtered = [p for p in samsungs if p.get("size", 0) >= 22]
    l_filtered = [p for p in lgs if p.get("size", 0) >= 22]
    return s_filtered, l_filtered

def load_mediamarkt_live():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    samsungs = []
    lgs = []
    
    try:
        with open(os.path.join(data_dir, "raw_mediamarkt_samsung.json"), "r", encoding="utf-8") as f:
            samsungs = json.load(f)
        with open(os.path.join(data_dir, "raw_mediamarkt_lg.json"), "r", encoding="utf-8") as f:
            lgs = json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load MediaMarkt live JSONs: {e}")
        
    if len(samsungs) == 0 or len(lgs) == 0:
        print("[FALLBACK] MediaMarkt live JSONs are empty. Reading directly from today's price tracker Excel sheets...")
        from datetime import datetime
        today_mmdd = datetime.now().strftime("%m%d")
        pt_path = os.path.join(data_dir, f"price tracker_swiss_2026 {today_mmdd}_v1.xlsx")
        if not os.path.exists(pt_path):
            pt_path = os.path.join(data_dir, f"price tracker_swiss_2026 {today_mmdd}.xlsx")
            
        if os.path.exists(pt_path):
            try:
                pt_wb = openpyxl.load_workbook(pt_path, data_only=True)
                if "MediaMarkt_Samsung_Full" in pt_wb.sheetnames:
                    s_sheet = pt_wb["MediaMarkt_Samsung_Full"]
                    for r in range(2, s_sheet.max_row + 1):
                        brand = s_sheet.cell(row=r, column=1).value
                        year = s_sheet.cell(row=r, column=2).value
                        size = s_sheet.cell(row=r, column=4).value
                        code = s_sheet.cell(row=r, column=5).value
                        price = s_sheet.cell(row=r, column=6).value
                        promo = s_sheet.cell(row=r, column=10).value
                        if code and price:
                            samsungs.append({
                                "brand": "Samsung",
                                "year": year or 2025,
                                "size": int(size) if size else 55,
                                "model_code": str(code),
                                "price": float(price),
                                "promo": str(promo or "None")
                            })
                if "MediaMarkt_LG_Full" in pt_wb.sheetnames:
                    l_sheet = pt_wb["MediaMarkt_LG_Full"]
                    for r in range(2, l_sheet.max_row + 1):
                        brand = l_sheet.cell(row=r, column=1).value
                        year = l_sheet.cell(row=r, column=2).value
                        size = l_sheet.cell(row=r, column=4).value
                        code = l_sheet.cell(row=r, column=5).value
                        price = l_sheet.cell(row=r, column=6).value
                        promo = l_sheet.cell(row=r, column=10).value
                        if code and price:
                            lgs.append({
                                "brand": "LG",
                                "year": year or 2025,
                                "size": int(size) if size else 55,
                                "model_code": str(code),
                                "price": float(price),
                                "promo": str(promo or "None")
                            })
                pt_wb.close()
                print(f"[FALLBACK SUCCESS] Loaded {len(samsungs)} Samsungs and {len(lgs)} LGs from Excel backup.")
            except Exception as e_excel:
                print(f"[ERROR] Failed to load MediaMarkt from Excel fallback: {e_excel}")
                
    s_filtered = [p for p in samsungs if p.get("size", 0) >= 22]
    l_filtered = [p for p in lgs if p.get("size", 0) >= 22]
    return s_filtered, l_filtered

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

def clean_promotion_text(promo, brand, year, model_code):
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
            
    # 6. Sound Device geschenkt / Music Studio 5 HW-LS50H
    if "SOUND DEVICE GESCHENKT" in promo_upper:
        if year == 2026:
            return "Free Sound Device with 2026 TV Purchase"
            
    # 7. Aus unserer Werbung / Werbung
    if "WERBUNG" in promo_upper or "WEEKLY AD" in promo_upper:
        return "Featured in Weekly Ad (Aus unserer Werbung)"
        
    # 8. Online Only
    if "ONLINE ONLY" in promo_upper or "ONLINE-ONLY" in promo_upper:
        return "Online Only"
        
    # 9. Sale / statt CHF
    if "STATT" in promo_upper or "WAS CHF" in promo_upper or "SALE" in promo_upper:
        # let's parse discount percent if available
        pct_match = re.search(r'(\d+)\s*%', promo)
        was_match = re.search(r'(?:was|statt)\s*(?:chf)?\s*([\d’\x27\x60,.]+)', promo, re.IGNORECASE)
        
        pct = pct_match.group(1) if pct_match else None
        was_val = was_match.group(1).replace("’", "").replace("'", "").replace("`", "").strip() if was_match else None
        if was_val and (was_val.endswith(".") or was_val.endswith(",")):
            was_val = was_val[:-1]
            
        if pct and was_val:
            return f"Sale {pct}%; was CHF {was_val}"
        elif was_val:
            return f"was CHF {was_val}"
        elif pct:
            return f"Sale {pct}%"
            
    return promo

def sync_with_swiss_master_registry(retailer, brand, live_products):
    """
    Reconciles live collected Swiss products with the Pan-European Master URL Registry
    (data/master_product_urls.json) for Switzerland (CH).
    - Preserves valid registered models (loss-prevention)
    - Auto-registers newly discovered models to master_product_urls.json
    - Ensures 100% stable model retention across survey runs
    """
    from datetime import datetime
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    master_registry_path = os.path.join(data_dir, "master_product_urls.json")
    
    master_urls = {}
    if os.path.exists(master_registry_path):
        try:
            with open(master_registry_path, "r", encoding="utf-8") as f:
                master_urls = json.load(f)
        except Exception as e:
            print(f"  [WARN] Could not load master_product_urls: {e}")
            master_urls = {}
            
    today_str = datetime.now().strftime("%Y-%m-%d")
    ret_norm = str(retailer).strip()
    brand_norm = "SAMSUNG" if str(brand).upper() == "SAMSUNG" else "LG"
    
    # Map existing live products by model_code
    live_map = {}
    for p in live_products:
        mc = str(p.get("model_code", "")).strip().upper()
        if mc and mc not in ["UNKNOWN", ""]:
            if mc not in live_map or p.get("price", 999999) < live_map[mc].get("price", 999999):
                live_map[mc] = p
                
    # 1. Update Master Registry with all valid live items
    new_reg_count = 0
    for mc, p in live_map.items():
        reg_key = f"CH_{ret_norm.upper()}_{brand_norm}_{mc}"
        url = p.get("url") or p.get("link") or ""
        if reg_key in master_urls:
            # Update existing registration
            if url and url.startswith("http"):
                master_urls[reg_key]["url"] = url
            master_urls[reg_key]["last_updated"] = today_str
            if p.get("title"):
                master_urls[reg_key]["title"] = p["title"]
        else:
            if url and url.startswith("http"):
                master_urls[reg_key] = {
                    "country": "CH",
                    "retailer": ret_norm,
                    "brand": brand_norm,
                    "model_code": p.get("model_code"),
                    "year": p.get("year", 2025),
                    "size": p.get("size", 0),
                    "title": p.get("title", ""),
                    "url": url,
                    "last_updated": today_str
                }
                new_reg_count += 1
                
    # Save back to master_product_urls.json
    try:
        with open(master_registry_path, "w", encoding="utf-8") as f:
            json.dump(master_urls, f, ensure_ascii=False, indent=2)
        if new_reg_count > 0:
            print(f"  ➔ [REGISTRY SYNC] Auto-registered {new_reg_count} new {ret_norm} {brand_norm} models into master_product_urls.json")
    except Exception as e:
        print(f"  [WARN] Failed saving master_product_urls: {e}")
        
    reconciled_products = list(live_map.values())
    reconciled_products.sort(key=lambda x: (x.get("size", 0), x.get("model_code", "")))
    return reconciled_products

def sync_retailer_sheet(filename, sheetname, brand, products, global_cashback_map=None):
    if not os.path.exists(filename):
        print(f"[ERROR] {filename} not found.")
        return filename
        
    print(f"\n[SYNC] Loading {filename} -> {sheetname}...")
    wb = openpyxl.load_workbook(filename)
    sheet = wb[sheetname]
    
    # Remove old rows for this brand
    removed_count = 0
    for r in range(sheet.max_row, 1, -1):
        brand_val = sheet.cell(row=r, column=1).value
        if str(brand_val).strip().upper() == str(brand).strip().upper():
            sheet.delete_rows(r)
            removed_count += 1
            
    print(f"  ➔ Removed {removed_count} obsolete {brand} rows.")
    
    # Append new live rows
    added_count = 0
    for p in products:
        code_upper = p["model_code"].upper()
        display_type = "LED"
        if "OLED" in code_upper or "S90" in code_upper or "S95" in code_upper or "S85" in code_upper or "S99" in code_upper:
            display_type = "OLED"
        elif "QNED" in code_upper:
            display_type = "QNED"
        elif "QN" in code_upper or "Q8" in code_upper or "Q7" in code_upper:
            display_type = "QLED"
        elif "U8" in code_upper or "UA" in code_upper or "UT" in code_upper or "UR" in code_upper:
            display_type = "UHD 4K"
            
        cashback_val = p.get("cashback", 0) or 0
        promo_text = p.get("promo", "None") or "None"
        try:
            from swiss_promo_parser import parse_swiss_promo_and_cashback
            cb_parsed, promo_text = parse_swiss_promo_and_cashback(
                promo_text, p.get("title", ""), brand, p.get("year", 2025), p["model_code"], p.get("size", 55), p.get("price", 0)
            )
            if cb_parsed > 0:
                cashback_val = cb_parsed
        except Exception:
            pass
            
        sheet.append([
            p["brand"],
            p["year"],
            display_type,
            p["size"],
            p["model_code"],
            p["price"],
            "Free",
            None,
            cashback_val,
            promo_text
        ])
        added_count += 1
        
    print(f"  ➔ Added {added_count} live {brand} rows.")
    final_filename = save_workbook_with_retry(wb, filename)
    wb.close()
    return final_filename

def clean_series_code(series_key, year):
    # Strip generation suffixes like G57/G67 -> G5/G6, S905 -> S90F / S90H
    # Extract size prefix
    size_match = re.match(r'^(\d+)', series_key)
    if not size_match:
        return series_key
    size = size_match.group(0)
    family = series_key[len(size):].strip()
    
    # LG clean up
    if family.startswith("G5") or family.startswith("G6") or family.startswith("C5") or family.startswith("C6") or family.startswith("B5") or family.startswith("B6"):
        # e.g., G57 -> G5, B69 -> B6
        family = family[0] + family[1]
    # Samsung clean up
    elif family.startswith("S90") or family.startswith("S85") or family.startswith("QN70"):
        # e.g., S905 -> S90F or S90H depending on year
        suffix = "H" if year == 2026 else "F"
        if family.startswith("S90"):
            family = f"S90{suffix}"
        elif family.startswith("S85"):
            family = f"S85{suffix}"
        elif family.startswith("QN70"):
            family = f"QN70{suffix}"
            
    return f"{size}{family}"

def find_matching_product(series_key, year, brand, products):
    # series_key is already cleaned
    size_match = re.match(r'^(\d+)', series_key)
    if not size_match:
        return None
    size = int(size_match.group(1))
    family = series_key[len(size_match.group(0)):].strip().upper()
    
    # Strip trailing letter if needed for generic match, but keep year boundaries
    if family.endswith("H") or family.endswith("F"):
        family_base = family[:-1]
    else:
        family_base = family
        
    matched = []
    for p in products:
        size_ok = (p["size"] == size) or (size in [85, 86] and p["size"] in [85, 86])
        if not size_ok or p["brand"].upper() != brand.upper():
            continue
        if p.get("year") != year:
            continue
            
        code = p["model_code"].upper()
        display = p.get("display", "").upper()
        
        # OLED vs QNED crossover protection
        if "QNED" in family and "QNED" not in code:
            continue
        if "QNED" not in family and "QNED" in code:
            continue
            
        is_match = False
        
        # OLED series verification
        if family in ["G5", "G6", "C5", "C6", "B5", "B6"]:
            # Ensure it is actually an OLED model
            if "OLED" not in display and "OLED" not in code:
                continue
                
        if family == "G5":
            is_match = "G5" in code
        elif family == "G6":
            is_match = "G6" in code
        elif family == "C5":
            is_match = "C5" in code
        elif family == "C6":
            is_match = "C6" in code
        elif family == "B5":
            is_match = "B5" in code
        elif family == "B6":
            is_match = "B6" in code
        elif family == "QNED90":
            is_match = "QNED90" in code
        elif family == "QNED85":
            is_match = "QNED85" in code or "QNED86" in code
        elif family in ["QNED80", "QNED71"]:
            if size <= 65:
                is_match = any(k in code for k in ["QNED80", "QNED71", "QNED72", "QNED70", "QNED7E"])
            else:
                is_match = "QNED80" in code or "QNED71" in code
        elif family == "QNED70":
            is_match = "QNED70" in code or "QNED72" in code or "QNED7E" in code
        elif family == "QNED86A":
            is_match = "QNED86" in code or "QNED85" in code
        elif family == "QNED86B":
            is_match = "QNED86" in code
        elif family == "QNED80A":
            is_match = "QNED80" in code
        elif family == "QNED80B":
            is_match = "QNED80" in code or "QNED7E" in code or "QNED72" in code
        elif family == "UA75":
            is_match = "UA75" in code or "UA73" in code
        elif family == "UA77" or family == "NU85":
            is_match = any(k in code for k in ["NU85", "NU80", "NU800", "UA77", "UT", "UR", "UQ", "LH", "LM"])
        elif family == "S99H":
            is_match = "S99H" in code or "S99" in code
        elif family == "S95F":
            is_match = "S95F" in code or ("S95" in code and "D" not in code and "H" not in code)
        elif family == "S95H":
            is_match = "S95H" in code
        elif family == "S90F":
            is_match = "S90F" in code or ("S90" in code and "D" not in code and "H" not in code)
        elif family == "S90H":
            is_match = "S90H" in code
        elif family == "S85F":
            is_match = "S85F" in code or ("S85" in code and "D" not in code and "H" not in code)
        elif family == "S85H":
            is_match = "S85H" in code
        elif family == "R95H":
            is_match = "R95" in code or "MRE95" in code
        elif family == "R85H":
            is_match = "R85" in code or "MRE85" in code
        elif family == "MRGB95":
            is_match = "MRGB9" in code or "MR95" in code or "MRGB95" in code
        elif family == "MRGB85":
            is_match = "MRGB8" in code or "MR85" in code or "MRGB87" in code or "MRGB85" in code
        elif family == "QNED93" or family == "QNED93A":
            is_match = "QNED93" in code
        elif family == "QN80F":
            is_match = "QN80F" in code or ("QN80" in code and "D" not in code and "H" not in code)
        elif family == "QN80H":
            is_match = "QN80" in code
        elif family == "QN70F":
            is_match = "QN70F" in code or ("QN70" in code and "D" not in code and "H" not in code)
        elif family == "QN70H":
            is_match = "QN70" in code
        elif family == "M80H":
            is_match = "M80" in code
        elif family == "M70H":
            is_match = "M70" in code
        elif family in ["Q8", "Q8F", "Q8H"]:
            is_match = "Q8" in code
        elif family in ["Q7", "Q7F", "Q7H"]:
            is_match = "Q7" in code
        elif family in ["U8000", "U8000F", "U8000H", "U8090", "U8090H", "U8070", "U8070H"]:
            is_match = any(k in code for k in ["U8000", "U8090", "U8070", "U80"])
            
        if is_match:
            matched.append(p)
            
    if not matched:
        return None
    if len(matched) == 1:
        return matched[0]

    if family in ["QNED80", "QNED71"]:
        def qned_priority(p):
            c = p["model_code"].upper()
            if "QNED71" in c: return 1
            if "QNED72" in c: return 2
            if "QNED80" in c: return 3
            if "QNED70" in c: return 4
            if "QNED7E" in c: return 5
            return 6
        matched.sort(key=qned_priority)
    elif family == "QNED70":
        def qned70_priority(p):
            c = p["model_code"].upper()
            if "QNED70" in c: return 1
            if "QNED72" in c: return 2
            if "QNED7E" in c: return 3
            return 4
        matched.sort(key=qned70_priority)

    return matched[0]

def get_display_type(series_str, year):
    series_str = series_str.upper()
    if any(x in series_str for x in ["G5", "C5", "B5", "G6", "C6", "B6", "S99", "S95", "S90", "S85", "S91", "S92", "S93", "S94", "S83", "S84", "S86", "S89"]):
        return "OLED"
    if "QNED" in series_str or any(x in series_str for x in ["QNED90", "QNED85", "QNED80", "QNED70", "QNED86", "QNED93"]):
        return "QNED"
    if any(x in series_str for x in ["MRGB", "R95", "R85"]):
        return "MRGB"
    if any(x in series_str for x in ["QN80", "QN70", "M80", "M70", "Q8", "Q7"]):
        return "QLED"
    if any(x in series_str for x in ["UA75", "UA77", "NU900", "NU90", "NU85", "NU80", "NU800", "NU850", "LB650", "LB", "U8000"]):
        return "UHD 4K"
    return "UHD 4K"

def sync_ata_sheet(filename, sheetname, year, msh_products, id_products, digi_products):
    if not os.path.exists(filename):
        print(f"[ERROR] {filename} not found.")
        return filename
        
    print(f"\n[SYNC ATA] Loading {filename} -> {sheetname}...")
    wb = openpyxl.load_workbook(filename)
    sheet = wb[sheetname]
    
    # Hide grid lines
    sheet.views.sheetView[0].showGridLines = False
    
    # Fonts
    bold_samsung = Font(name="Calibri", size=11, bold=True, color="002060")
    reg_samsung = Font(name="Calibri", size=11, bold=False, color="002060")
    
    # Define VLOOKUP Summary start dynamically based on row contents
    summary_start = None
    for r in range(4, 300):
        val_b = sheet.cell(row=r, column=2).value
        if val_b == "Series" and r > 10:
            summary_start = r
            break
            
    if summary_start is None:
        summary_start = 86 if year == 2025 else 132
        
    # Find last data row in the upper matrix by scanning upwards from summary_start - 1
    last_row = summary_start - 1
    while last_row > 4:
        val_b = sheet.cell(row=last_row, column=2).value
        if val_b and str(val_b).strip():
            break
        last_row -= 1
        
    print(f"  ➔ [DYNAMIC OFFSET] Detected summary_start: {summary_start} | last_row: {last_row}")
        
    # Set Display column header
    sheet.cell(row=3, column=1).value = "Display"
    sheet.cell(row=3, column=1).font = Font(name="Calibri", size=11, bold=True)
    
    # 1. Row 4 to last_row: Populate detailed model data in upper matrix
    for r in range(4, last_row + 1):
        series_val = sheet.cell(row=r, column=2).value
        if not series_val:
            # Clear all data cells for blank/spacer rows
            sheet.cell(row=r, column=1).value = ""
            for col in [3, 4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16]:
                sheet.cell(row=r, column=col).value = ""
            sheet.cell(row=r, column=7).value = ""
            sheet.cell(row=r, column=12).value = ""
            sheet.cell(row=r, column=17).value = ""
            continue
            
        raw_series = str(series_val).strip()
        clean_series = clean_series_code(raw_series, year)
        sheet.cell(row=r, column=2).value = clean_series
        
        # A열 Display Type 기입
        disp_type = get_display_type(clean_series, year)
        sheet.cell(row=r, column=1).value = disp_type
        
        # Brand detection
        is_lg = any(s in clean_series for s in ["G5", "C5", "B5", "QNED86A", "QNED80A", "UA75", "G6", "C6", "B6", "QNED86B", "QNED80B", "UA77", "QNED90", "QNED85", "QNED80", "QNED70", "NU85", "MRGB87", "MRGB85", "MRGB8", "MRGB9", "QNED93"])
        brand = "LG" if is_lg else "Samsung"
        
        # Determine denominator row for LG ATA formula (OLED G series rows)
        size_match = re.match(r'^(\d+)', clean_series)
        denom_row = 7  # Default
        if size_match:
            sz = int(size_match.group(1))
            if sz in [83, 85, 86, 100]:
                denom_row = 4
            elif sz in [75, 77]:
                denom_row = 5
            elif sz in [65]:
                denom_row = 6
            else:
                denom_row = 7
                
                # 1. Find matches
        msh_match = find_matching_product(clean_series, year, brand, msh_products)
        id_match = find_matching_product(clean_series, year, brand, id_products)
        digi_match = find_matching_product(clean_series, year, brand, digi_products)
        
        # 2. Extract raw cashback values
        msh_cb = 0
        if msh_match:
            msh_cb = msh_match.get("cashback", 0) or 0
            if msh_cb == 0:
                promo = msh_match.get("promo", "None") or "None"
                cb_m = re.search(r'(?:cashback|캐시백|rückvergütung)\s*(?:von\s*|bis\s*zu\s*)?(?:chf)?\s*(\d+)', promo, re.IGNORECASE)
                if not cb_m:
                    cb_m = re.search(r'(\d+)\s*(?:\.-|.–|chf)?\s*(?:cashback|캐시백|rückvergütung)', promo, re.IGNORECASE)
                if cb_m: msh_cb = int(cb_m.group(1))
                
        id_cb = 0
        if id_match:
            id_cb = id_match.get("cashback", 0) or 0
            if id_cb == 0:
                promo = id_match.get("promo", "None") or "None"
                cb_m = re.search(r'(?:cashback|캐시백|rückvergütung)\s*(?:von\s*|bis\s*zu\s*)?(?:chf)?\s*(\d+)', promo, re.IGNORECASE)
                if not cb_m:
                    cb_m = re.search(r'(\d+)\s*(?:\.-|.–|chf)?\s*(?:cashback|캐시백|rückvergütung)', promo, re.IGNORECASE)
                if cb_m: id_cb = int(cb_m.group(1))
                
        digi_cb = 0
        if digi_match:
            digi_cb = digi_match.get("cashback", 0) or 0
            if digi_cb == 0:
                promo = digi_match.get("promo", "None") or "None"
                cb_m = re.search(r'(?:cashback|캐시백|rückvergütung)\s*(?:von\s*|bis\s*zu\s*)?(?:chf)?\s*(\d+)', promo, re.IGNORECASE)
                if not cb_m:
                    cb_m = re.search(r'(\d+)\s*(?:\.-|.–|chf)?\s*(?:cashback|캐시백|rückvergütung)', promo, re.IGNORECASE)
                if cb_m: digi_cb = int(cb_m.group(1))
                
        # 3. No cashback inheritance allowed per user request (Only exact values)
            
        # 4. Write MSH
        if msh_match:
            sheet.cell(row=r, column=3).value = msh_match["model_code"]
            sheet.cell(row=r, column=5).value = msh_match["price"]
            sheet.cell(row=r, column=6).value = msh_cb
        else:
            sheet.cell(row=r, column=3).value = ""
            sheet.cell(row=r, column=5).value = ""
            sheet.cell(row=r, column=6).value = ""
        sheet.cell(row=r, column=4).value = f'=IF(E{r}="","",E{r}-F{r})'
        
        # 5. Write Interdiscount
        if id_match:
            sheet.cell(row=r, column=8).value = id_match["model_code"]
            sheet.cell(row=r, column=10).value = id_match["price"]
            sheet.cell(row=r, column=11).value = id_cb
        else:
            sheet.cell(row=r, column=8).value = ""
            sheet.cell(row=r, column=10).value = ""
            sheet.cell(row=r, column=11).value = ""
        sheet.cell(row=r, column=9).value = f'=IF(J{r}="","",J{r}-K{r})'
        
        # 6. Write Digitec
        if digi_match:
            sheet.cell(row=r, column=13).value = digi_match["model_code"]
            sheet.cell(row=r, column=15).value = digi_match["price"]
            sheet.cell(row=r, column=16).value = digi_cb
        else:
            sheet.cell(row=r, column=13).value = ""
            sheet.cell(row=r, column=15).value = ""
            sheet.cell(row=r, column=16).value = ""
        sheet.cell(row=r, column=14).value = f'=IF(O{r}="","",O{r}-P{r})'
        
        # Apply styling & formatting rules
        if brand == "Samsung":
            sheet.cell(row=r, column=1).font = bold_samsung
            sheet.cell(row=r, column=2).font = bold_samsung
            for col in [3, 8, 13]:
                sheet.cell(row=r, column=col).font = reg_samsung
            for col in [7, 12, 17]:
                sheet.cell(row=r, column=col).value = ""
        else:
            lg_bold = Font(name="Calibri", size=11, bold=True)
            sheet.cell(row=r, column=1).font = lg_bold
            sheet.cell(row=r, column=2).font = lg_bold
            
            sheet.cell(row=r, column=7).value = f'=IFERROR(D{r}/D{denom_row},"")'
            sheet.cell(row=r, column=12).value = f'=IFERROR(I{r}/I{denom_row},"")'
            sheet.cell(row=r, column=17).value = f'=IFERROR(N{r}/N{denom_row},"")'
            
            for col in [7, 12, 17]:
                sheet.cell(row=r, column=col).number_format = "0%"

    # 2. Write VLOOKUP Summary Table from scratch
    if year == 2025:
        summary_series = [
            "55G5", "55C5", "55B5", "55QNED86A", "55QNED80A", "55UA75",
            "",
            "65G5", "65C5", "65B5", "65QNED86A", "65QNED80A", "65UA75",
            "",
            "77G5", "77C5", "77B5", "75QNED86A", "75QNED80A", "75UA75",
            "",
            "55S95F", "55S90F", "55S85F", "55QN70F", "55Q8F", "55Q7F", "55U8000F",
            "",
            "65S95F", "65S90F", "65S85F", "65QN70F", "65Q8F", "65Q7F", "65U8000F",
            "",
            "77S95F", "77S90F", "77S85F", "75QN70F", "75Q8F", "75Q7F", "75U8000F"
        ]
    else:
        summary_series = [
            "55G6", "55C6", "55B6", "55QNED85", "55QNED80", "55NU85",
            "",
            "65G6", "65C6", "65B6", "65QNED85", "65QNED80", "65NU85",
            "",
            "77G6", "77C6", "77B6", "75QNED85", "75QNED80", "75NU85",
            "",
            "55S99H", "55S95H", "55S90H", "55S85H", "55QN70H", "55Q8H", "55Q7H", "55U8000H",
            "",
            "65S99H", "65S95H", "65S90H", "65S85H", "65QN70H", "65Q8H", "65Q7H", "65U8000H",
            "",
            "77S99H", "77S95H", "77S90H", "77S85H", "75QN70H", "75Q8H", "75Q7H", "75U8000H"
        ]
        
    # Write VLOOKUP Summary Header Row
    sheet.cell(row=summary_start, column=1).value = "Display"
    sheet.cell(row=summary_start, column=1).font = Font(name="Calibri", size=11, bold=True)
    sheet.cell(row=summary_start, column=2).value = "Series"
    sheet.cell(row=summary_start, column=2).font = Font(name="Calibri", size=11, bold=True)
    sheet.cell(row=summary_start, column=3).value = "VLOOKUP Summary"
    sheet.cell(row=summary_start, column=3).font = Font(name="Calibri", size=11, bold=True)
    sheet.cell(row=summary_start, column=3).alignment = Alignment(horizontal="center")
    
    try:
        sheet.merge_cells(start_row=summary_start, start_column=3, end_row=summary_start, end_column=17)
    except Exception as e:
        print(f"  ➔ [INFO] Merge cells on Row {summary_start} skipped: {e}")
        
    # Fill summary rows
    for i, s_code in enumerate(summary_series):
        r = summary_start + 1 + i
        sheet.cell(row=r, column=2).value = s_code
        
        if not s_code:
            # Empty spacer row
            sheet.cell(row=r, column=1).value = ""
            for col in range(3, 18):
                sheet.cell(row=r, column=col).value = ""
            continue
            
        clean_s = clean_series_code(s_code, year)
        sheet.cell(row=r, column=2).value = clean_s
        
        # Display type
        disp_type = get_display_type(clean_s, year)
        sheet.cell(row=r, column=1).value = disp_type
        
        # Brand detection
        is_lg = any(s in clean_s for s in ["G5", "C5", "B5", "QNED86A", "QNED80A", "UA75", "G6", "C6", "B6", "QNED86B", "QNED80B", "UA77", "QNED90", "QNED85", "QNED80", "QNED70", "NU85", "MRGB85", "MRGB8", "MRGB9", "QNED93"])
        brand = "LG" if is_lg else "Samsung"
        
        # Determine lookup key (for 2026 Q8H / Q7H mapped to R95H / R85H)
        lookup_key = f"$B{r}"
        if year == 2026:
            if clean_s == "55Q8H": lookup_key = '"55R95H"'
            elif clean_s == "65Q8H": lookup_key = '"65R95H"'
            elif clean_s == "75Q8H": lookup_key = '"75R95H"'
            elif clean_s == "55Q7H": lookup_key = '"55R85H"'
            elif clean_s == "65Q7H": lookup_key = '"65R85H"'
            elif clean_s == "75Q7H": lookup_key = '"75R85H"'
            
        # Determine denominator row in summary table for LG ATA
        size_match = re.match(r'^(\d+)', clean_s)
        denom_row = summary_start + 1  # Default to 55G6 / 55G5
        if size_match:
            sz = int(size_match.group(1))
            if sz in [83, 85, 86, 100]:
                denom_row = summary_start + 1 + 14
            elif sz in [75, 77]:
                denom_row = summary_start + 1 + 14
            elif sz in [65]:
                denom_row = summary_start + 1 + 7
            else:
                denom_row = summary_start + 1 + 0
                
        # Write VLOOKUP formulas for columns 3 to 17
        # MSH
        sheet.cell(row=r, column=3).value = f'=IF(VLOOKUP({lookup_key},$B$4:$Q${last_row},2,FALSE)=0,"",VLOOKUP({lookup_key},$B$4:$Q${last_row},2,FALSE))'
        sheet.cell(row=r, column=4).value = f'=IF(E{r}="","",E{r}-F{r})'
        sheet.cell(row=r, column=5).value = f'=IF(ISNA(VLOOKUP({lookup_key},$B$4:$Q${last_row},4,FALSE)),"",VLOOKUP({lookup_key},$B$4:$Q${last_row},4,FALSE))'
        sheet.cell(row=r, column=6).value = f'=IF(ISNA(VLOOKUP({lookup_key},$B$4:$Q${last_row},5,FALSE)),"",VLOOKUP({lookup_key},$B$4:$Q${last_row},5,FALSE))'
        
        # ID
        sheet.cell(row=r, column=8).value = f'=IF(VLOOKUP({lookup_key},$B$4:$Q${last_row},7,FALSE)=0,"",VLOOKUP({lookup_key},$B$4:$Q${last_row},7,FALSE))'
        sheet.cell(row=r, column=9).value = f'=IF(J{r}="","",J{r}-K{r})'
        sheet.cell(row=r, column=10).value = f'=IF(ISNA(VLOOKUP({lookup_key},$B$4:$Q${last_row},9,FALSE)),"",VLOOKUP({lookup_key},$B$4:$Q${last_row},9,FALSE))'
        sheet.cell(row=r, column=11).value = f'=IF(ISNA(VLOOKUP({lookup_key},$B$4:$Q${last_row},10,FALSE)),"",VLOOKUP({lookup_key},$B$4:$Q${last_row},10,FALSE))'
        
        # Digitec
        sheet.cell(row=r, column=13).value = f'=IF(VLOOKUP({lookup_key},$B$4:$Q${last_row},12,FALSE)=0,"",VLOOKUP({lookup_key},$B$4:$Q${last_row},12,FALSE))'
        sheet.cell(row=r, column=14).value = f'=IF(O{r}="","",O{r}-P{r})'
        sheet.cell(row=r, column=15).value = f'=IF(ISNA(VLOOKUP({lookup_key},$B$4:$Q${last_row},14,FALSE)),"",VLOOKUP({lookup_key},$B$4:$Q${last_row},14,FALSE))'
        sheet.cell(row=r, column=16).value = f'=IF(ISNA(VLOOKUP({lookup_key},$B$4:$Q${last_row},15,FALSE)),"",VLOOKUP({lookup_key},$B$4:$Q${last_row},15,FALSE))'
        
        # Styles and Brand specifics
        if brand == "Samsung":
            sheet.cell(row=r, column=1).font = bold_samsung
            sheet.cell(row=r, column=2).font = bold_samsung
            for col in [3, 8, 13]:
                sheet.cell(row=r, column=col).font = reg_samsung
            for col in [7, 12, 17]:
                sheet.cell(row=r, column=col).value = ""
        else:
            lg_bold = Font(name="Calibri", size=11, bold=True)
            sheet.cell(row=r, column=1).font = lg_bold
            sheet.cell(row=r, column=2).font = lg_bold
            
            sheet.cell(row=r, column=7).value = f'=IFERROR(D{r}/D{denom_row},"")'
            sheet.cell(row=r, column=12).value = f'=IFERROR(I{r}/I{denom_row},"")'
            sheet.cell(row=r, column=17).value = f'=IFERROR(N{r}/N{denom_row},"")'
            
            for col in [7, 12, 17]:
                sheet.cell(row=r, column=col).number_format = "0%"
                
    final_filename = save_workbook_with_retry(wb, filename)
    wb.close()
    return final_filename

def load_products_from_excel(excel_path):
    print(f"[LOAD EXCEL SOURCE] Reading: {excel_path}")
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    msh_s = []
    msh_l = []
    id_s = []
    id_l = []
    digi_s = []
    digi_l = []
    
    def parse_sheet(sheet, brand):
        products = []
        for r in range(2, sheet.max_row + 1):
            brand_val = sheet.cell(row=r, column=1).value
            year = sheet.cell(row=r, column=2).value
            display = sheet.cell(row=r, column=3).value
            size = sheet.cell(row=r, column=4).value
            code = sheet.cell(row=r, column=5).value
            price = sheet.cell(row=r, column=6).value
            cashback = sheet.cell(row=r, column=9).value  # Column 9 is Cashback (CHF)
            promo = sheet.cell(row=r, column=10).value  # Column 10 is General Promotions
            cb_val = int(cashback) if (cashback is not None and str(cashback).strip() not in ["", "None"]) else 0
            if cb_val == 0 and promo and str(promo).strip() not in ["", "None", "0"]:
                try:
                    from swiss_promo_parser import parse_swiss_promo_and_cashback
                    cb_p, _ = parse_swiss_promo_and_cashback(
                        str(promo), "", brand_val or brand, int(year) if year else 2025, str(code), int(size) if size else 55, float(price)
                    )
                    if cb_p > 0:
                        cb_val = cb_p
                except Exception:
                    pass
            if code and price:
                products.append({
                    "brand": brand_val or brand,
                    "year": int(year) if year else 2025,
                    "display": display or "LED",
                    "size": int(size) if size else 55,
                    "model_code": str(code),
                    "price": float(price),
                    "cashback": cb_val,
                    "promo": str(promo or "None")
                })
        return products

    if "MediaMarkt_Samsung_Full" in wb.sheetnames:
        msh_s = parse_sheet(wb["MediaMarkt_Samsung_Full"], "Samsung")
    if "MediaMarkt_LG_Full" in wb.sheetnames:
        msh_l = parse_sheet(wb["MediaMarkt_LG_Full"], "LG")
    if "Interdiscount_Samsung_Full" in wb.sheetnames:
        id_s = parse_sheet(wb["Interdiscount_Samsung_Full"], "Samsung")
    if "Interdiscount_LG_Full" in wb.sheetnames:
        id_l = parse_sheet(wb["Interdiscount_LG_Full"], "LG")
    if "Digitec_Samsung_Full" in wb.sheetnames:
        digi_s = parse_sheet(wb["Digitec_Samsung_Full"], "Samsung")
    if "Digitec_LG_Full" in wb.sheetnames:
        digi_l = parse_sheet(wb["Digitec_LG_Full"], "LG")
        
    wb.close()
    return msh_s, msh_l, id_s, id_l, digi_s, digi_l

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel-source", help="Path to price tracker Excel file to load all retailer data from directly")
    args = parser.parse_args()

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    
    # Load raw scraped datasets
    if args.excel_source:
        print(f"[EXCEL SOURCE MODE] Loading data directly from: {args.excel_source}")
        msh_s, msh_l, id_s, id_l, digi_s, digi_l = load_products_from_excel(args.excel_source)
    else:
        # Mandatory Pre-flight Live Assertion Gate for Swiss Retailers
        print("=" * 65)
        print(" 🛡️ MANDATORY PRE-FLIGHT LIVE ASSERTION GATE (Swiss 3 Retailers)")
        print("=" * 65)
        from datetime import datetime
        today_date_str = datetime.now().strftime("%Y-%m-%d")
        swiss_raws = [
            "raw_digitec_samsung.json", "raw_digitec_lg.json",
            "raw_interdiscount_samsung.json", "raw_interdiscount_lg.json",
            "raw_mediamarkt_samsung.json", "raw_mediamarkt_lg.json"
        ]
        stale_files = []
        for rf in swiss_raws:
            p = os.path.join(data_dir, rf)
            if os.path.exists(p):
                mtime = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")
                if mtime != today_date_str:
                    stale_files.append((rf, mtime))
            else:
                stale_files.append((rf, "MISSING"))
        if stale_files:
            print(f"❌ [ASSERTION FAILURE] Found {len(stale_files)} stale or missing Swiss raw datasets:")
            for fname, f_date in stale_files:
                print(f"   • {fname}: Last modified {f_date} (Expected today: {today_date_str})")
            raise RuntimeError(f"PRE-FLIGHT ASSERTION FAILED: {len(stale_files)} Swiss files require real-time live scraping for today ({today_date_str}).")
        print(f"✅ All {len(swiss_raws)} Swiss raw datasets verified fresh for today ({today_date_str})!\n")

        digi_s, digi_l = load_digitec_live()
        id_s, id_l = load_interdiscount_live()
        msh_s, msh_l = load_mediamarkt_live()
    
    print(f"\n[DATA SUMMARY]")
    print(f"  Digitec: Samsung={len(digi_s)} | LG={len(digi_l)}")
    print(f"  Interdiscount: Samsung={len(id_s)} | LG={len(id_l)}")
    print(f"  MediaMarkt: Samsung={len(msh_s)} | LG={len(msh_l)}")
    
    # Dynamic Date Logic based on current execution context (2026-07-05)
    from datetime import datetime, timedelta
    today_dt = datetime.now()
    
    # Check if we should override or use today
    today_mmdd = today_dt.strftime("%m%d")  # "0705"
    yesterday_mmdd = (today_dt - timedelta(days=1)).strftime("%m%d") # "0704"
    
    print(f"[DATE RESOLUTION] Today MMDD: {today_mmdd} | Yesterday MMDD: {yesterday_mmdd}")
    
    if args.excel_source:
        source_dir = os.path.dirname(os.path.abspath(args.excel_source))
        source_name = os.path.basename(args.excel_source)
        # Find date pattern from source_name, e.g. "price tracker_swiss_2026 0709_v1.xlsx" -> "0709"
        date_match = re.search(r'2026\s+(\d{4})', source_name)
        if date_match:
            mmdd = date_match.group(1)
        else:
            mmdd = today_mmdd
            
        today_pt = args.excel_source
        # Look for Swiss_ATA_Comparison_2026_MMDD_v*.xlsx first
        latest_pattern = os.path.join(source_dir, f"Swiss_ATA_Comparison_2026_{mmdd}*.xlsx")
        files = glob.glob(latest_pattern)
        files = [f for f in files if not os.path.basename(f).startswith("~$")]
        if files:
            files.sort()
            today_ata = files[-1]
            print(f"[TARGET ATA COMP] Resolved target comparison file: {today_ata}")
        else:
            today_ata = os.path.join(source_dir, f"Swiss_ATA_Comparison_2026_{mmdd}.xlsx")
            # Fallback to general template or clone it
            latest_ata = find_latest_file("Swiss_ATA_Comparison")
            if latest_ata:
                print(f"[CLONING TEMPLATE] {latest_ata} -> {today_ata}")
                shutil.copyfile(latest_ata, today_ata)
    else:
        # Find latest files to clone
        latest_pt = find_latest_file(f"price tracker_swiss_2026 {yesterday_mmdd}") or find_latest_file("price tracker_swiss")
        latest_ata = find_latest_file(f"Swiss_ATA_Comparison_2026_{yesterday_mmdd}") or find_latest_file(f"Swiss_ATA_Comparison_2026 {yesterday_mmdd}") or find_latest_file("Swiss_ATA_Comparison")
        
        today_pt = os.path.join(data_dir, f"price tracker_swiss_2026 {today_mmdd}_v1.xlsx")
        today_ata = os.path.join(data_dir, f"Swiss_ATA_Comparison_2026_{today_mmdd}.xlsx")
        
        if latest_pt and not os.path.exists(today_pt):
            print(f"\n[CLONING] {latest_pt} -> {today_pt}")
            shutil.copyfile(latest_pt, today_pt)
        if latest_ata and not os.path.exists(today_ata):
            print(f"\n[CLONING] {latest_ata} -> {today_ata}")
            shutil.copyfile(latest_ata, today_ata)
        
    # Build global cashback mapping - disabled per user request
    global_cashback_map = {}

    # Reconcile with Swiss Master URL Registry (Loss-Prevention & Auto-Registration)
    print("\n[MASTER REGISTRY RECONCILIATION & AUTO-REGISTRATION]")
    msh_s = sync_with_swiss_master_registry("MediaMarkt", "Samsung", msh_s)
    msh_l = sync_with_swiss_master_registry("MediaMarkt", "LG", msh_l)
    id_s = sync_with_swiss_master_registry("Interdiscount", "Samsung", id_s)
    id_l = sync_with_swiss_master_registry("Interdiscount", "LG", id_l)
    digi_s = sync_with_swiss_master_registry("Digitec", "Samsung", digi_s)
    digi_l = sync_with_swiss_master_registry("Digitec", "LG", digi_l)

    # 1. Update Price Tracker
    if os.path.exists(today_pt):
        if len(msh_s) > 0:
            today_pt = sync_retailer_sheet(today_pt, "MediaMarkt_Samsung_Full", "Samsung", msh_s, global_cashback_map)
        if len(msh_l) > 0:
            today_pt = sync_retailer_sheet(today_pt, "MediaMarkt_LG_Full", "LG", msh_l, global_cashback_map)
        today_pt = sync_retailer_sheet(today_pt, "Interdiscount_Samsung_Full", "Samsung", id_s, global_cashback_map)
        today_pt = sync_retailer_sheet(today_pt, "Interdiscount_LG_Full", "LG", id_l, global_cashback_map)
        today_pt = sync_retailer_sheet(today_pt, "Digitec_Samsung_Full", "Samsung", digi_s, global_cashback_map)
        today_pt = sync_retailer_sheet(today_pt, "Digitec_LG_Full", "LG", digi_l, global_cashback_map)
    else:
        print("[ERROR] Today's price tracker workbook does not exist.")
        
    # 2. Update TV Price Comparison (if exists)
    if not args.excel_source:
        comp_file = find_latest_file("TV_Price_Comparison") or os.path.join(data_dir, "TV_Price_Comparison_v5.xlsx")
        if os.path.exists(comp_file):
            if len(msh_s) > 0:
                comp_file = sync_retailer_sheet(comp_file, "MediaMarkt_Samsung_Full", "Samsung", msh_s, global_cashback_map)
            if len(msh_l) > 0:
                comp_file = sync_retailer_sheet(comp_file, "MediaMarkt_LG_Full", "LG", msh_l, global_cashback_map)
            comp_file = sync_retailer_sheet(comp_file, "Interdiscount_Samsung_Full", "Samsung", id_s, global_cashback_map)
            comp_file = sync_retailer_sheet(comp_file, "Interdiscount_LG_Full", "LG", id_l, global_cashback_map)
            comp_file = sync_retailer_sheet(comp_file, "Digitec_Samsung_Full", "Samsung", digi_s, global_cashback_map)
            comp_file = sync_retailer_sheet(comp_file, "Digitec_LG_Full", "LG", digi_l, global_cashback_map)
        
    # 3. Update Swiss ATA Comparison
    # Also resolve ATA files list dynamically
    ata_files = [today_ata]
    if not args.excel_source:
        ata_files.append(os.path.join(data_dir, f"Swiss_ATA_Comparison_2026_{today_mmdd}_v1.xlsx"))
        
    for af in ata_files:
        if os.path.exists(af):
            print(f"\n[SYNC COMPARISON] Processing: {af}")
            af_saved = sync_ata_sheet(af, "Swiss_2025", 2025, msh_s + msh_l, id_s + id_l, digi_s + digi_l)
            af_saved = sync_ata_sheet(af_saved, "Swiss_2026", 2026, msh_s + msh_l, id_s + id_l, digi_s + digi_l)
        else:
            print(f"[INFO] Path not found for sync: {af}")
        
    print("\n[ALL SYNCS DONE SUCCESSFULLY]")

    # 4. Record daily prices to price_history.db and emit structured log
    try:
        from price_history import record_survey_from_excel
        record_survey_from_excel(today_pt, country="CH")
    except Exception as e_db:
        print(f"[WARN] Failed recording Swiss survey to price_history.db: {e_db}")

    try:
        from scrape_logger import emit_summary
        total_items = len(msh_s + msh_l + id_s + id_l + digi_s + digi_l)
        emit_summary(
            country="CH",
            retailer="Swiss_3_Retailers",
            brand="ALL",
            total_extracted=total_items,
            final_deduplicated=total_items,
            execution_time_sec=0.0
        )
    except Exception:
        pass

if __name__ == "__main__":
    main()
