# -*- coding: utf-8 -*-
import openpyxl
import json
import os
import re
import sys
import glob

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))
data_dir = os.path.join(root_dir, "data")
master_registry_path = os.path.join(data_dir, "master_product_urls.json")

master_urls = {}

if os.path.exists(master_registry_path):
    try:
        with open(master_registry_path, "r", encoding="utf-8") as f:
            master_urls = json.load(f)
    except Exception as e:
        master_urls = {}

def extract_size_and_year_from_title(title, model_code=""):
    t_up = str(title).upper()
    mc_up = str(model_code).upper()
    
    # Year
    year = 2025
    if any(x in t_up for x in ["2026", " C6", " G6", " B6", "QNED86B", "QNED80B", "QNED87B", "QNED71B", "QNED70B", "QNED72B", "QNED7EB", "S90H", "S95H", "S85H", "S99H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "M80H", "M70H", "R95H", "R85H", "U8000H", "U8090H", "U8072H", "LS03H", "LS03HW"]):
        year = 2026
    elif any(x in mc_up for x in ["C6", "G6", "B6", "M6", "QNED86B", "QNED80B", "QNED87B", "QNED71B", "QNED70B", "QNED7EB", "QNED72B", "MRGB87B", "MRGB96B", "UA77", "LX7B", "LX6", "27LX6TDGA", "QLED7EB", "S95H", "S90H", "S85H", "S99H", "R95H", "R85H", "M80H", "M70H", "U8090H", "LS03H"]):
        year = 2026
    elif any(x in t_up for x in ["2025", " C5", " G5", " B5", "QNED86A", "QNED80A", "QNED87A", "QNED7EA", "QNED72A", "S90F", "S95F", "S85F", "QN90F", "QN85F", "QN80F", "Q7F", "Q8F", "Q6F", "LS03F", "U8000F", "U8090F"]):
        year = 2025
    elif any(x in mc_up for x in ["C5", "G5", "B5", "M5", "QNED86A", "QNED80A", "QNED87A", "QNED7EA", "QNED72A", "QNED70A", "UA75", "MRGB87A", "LX7A", "LX5", "QNED93A", "S95F", "S90F", "S85F", "QN90F", "QN85F", "QN80F", "Q7F", "Q8F", "Q6F", "LS03F"]):
        year = 2025

    # Size
    size = 0
    m_sz = re.search(r'\b(98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:inch|zoll|pollici|cm|\b)', t_up)
    if m_sz:
        size = int(m_sz.group(1))
    elif mc_up:
        m_mc_sz = re.search(r'(?:QE|OLED|TQ|UE|GQ|TU|QN|4K|8K)?(\d{2})[A-Z]', mc_up)
        if m_mc_sz and m_mc_sz.group(1) in ["98", "97", "86", "85", "83", "77", "75", "70", "65", "55", "50", "48", "43", "42", "40", "32", "27", "24"]:
            size = int(m_mc_sz.group(1))
            
    return year, size

def add_to_registry(country, retailer, brand, model_code, year, size, title, url):
    if not url or not str(url).startswith("http"):
        return
    if not model_code or str(model_code).strip() in ["", "Unknown", "Unknown Samsung", "Unknown LG"]:
        return
        
    c_clean = str(country).strip().upper()
    ret_clean = str(retailer).strip()
    b_clean = str(brand).strip().upper()
    mc_clean = str(model_code).strip()
    
    # Exclude 2024 or older models
    if year and str(year).isdigit() and int(year) < 2025:
        return
    if any(x in mc_clean.upper() for x in ["G4", "C4", "B4", "M4", "S90D", "S95D", "QN90D", "DU8000", "CU8000"]):
        return
        
    key = f"{c_clean}_{ret_clean}_{mc_clean}".upper()
    
    calc_year, calc_size = extract_size_and_year_from_title(title, mc_clean)
    final_year = int(year) if year and str(year).isdigit() and int(year) >= 2025 else calc_year
    final_size = int(size) if size and str(size).isdigit() and int(size) > 0 else calc_size
    
    master_urls[key] = {
        "country": c_clean,
        "retailer": ret_clean,
        "brand": b_clean,
        "model_code": mc_clean,
        "year": final_year,
        "size": final_size,
        "title": str(title or "").strip(),
        "url": str(url).strip(),
        "last_updated": "2026-08-15"
    }

print("[MASTER REGISTRY] 1. Scanning Pan-European Excel Workbooks...")
excel_files = glob.glob(os.path.join(data_dir, "price tracker_EU_*.xlsx")) + glob.glob(os.path.join(root_dir, "History_EU/**/*.xlsx"), recursive=True)
excel_files = [f for f in excel_files if not os.path.basename(f).startswith("~$")]

for excel_path in excel_files:
    try:
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            country = "EU"
            retailer = "MediaMarkt"
            brand = "SAMSUNG" if "SAMSUNG" in sheet_name.upper() else ("LG" if "LG" in sheet_name.upper() else "TV")
            
            if "HU" in sheet_name: country = "HU"; retailer = "MediaMarkt"
            elif "CZ" in sheet_name: country = "CZ"; retailer = "Alza"
            elif "GR" in sheet_name: country = "GR"; retailer = "Public"
            elif "DE" in sheet_name: country = "DE"; retailer = "MediaMarkt"
            elif "AT" in sheet_name: country = "AT"; retailer = "MediaMarkt"
            elif "CH" in sheet_name: country = "CH"; retailer = "MediaMarkt"
            elif "ES" in sheet_name: country = "ES"; retailer = "MediaMarkt"
            elif "NL" in sheet_name: country = "NL"; retailer = "MediaMarkt"
            elif "UK" in sheet_name: country = "UK"; retailer = "Currys"
            elif "FR" in sheet_name: country = "FR"; retailer = "Fnac"
            elif "IT" in sheet_name: country = "IT"; retailer = "MediaWorld"
            
            headers = [str(ws.cell(row=1, column=c).value or "").lower() for c in range(1, ws.max_column + 1)]
            
            url_col = None
            code_col = None
            year_col = None
            size_col = None
            title_col = None
            
            for idx, h in enumerate(headers):
                if any(x in h for x in ["link", "url", "pdp", "hyperlink"]): url_col = idx + 1
                if any(x in h for x in ["model code", "code", "modell", "model"]):
                    if not code_col or "code" in h: code_col = idx + 1
                if any(x in h for x in ["year", "jahr", "év"]): year_col = idx + 1
                if any(x in h for x in ["size", "zoll", "inch"]): size_col = idx + 1
                if any(x in h for x in ["title", "name", "termék", "product"]): title_col = idx + 1
                
            if not url_col:
                for test_col in [11, 12, 13]:
                    if test_col <= ws.max_column:
                        val = str(ws.cell(row=2, column=test_col).value or "")
                        if val.startswith("http"):
                            url_col = test_col
                            break
                            
            code_col = code_col or 5
            year_col = year_col or 2
            size_col = size_col or 4
            title_col = title_col or (13 if ws.max_column >= 13 else code_col)
            
            if url_col:
                for r in range(2, ws.max_row + 1):
                    c_brand = ws.cell(row=r, column=1).value or brand
                    c_year = ws.cell(row=r, column=year_col).value
                    c_size = ws.cell(row=r, column=size_col).value
                    c_code = ws.cell(row=r, column=code_col).value
                    c_url = ws.cell(row=r, column=url_col).value
                    c_title = ws.cell(row=r, column=title_col).value
                    
                    cell_obj = ws.cell(row=r, column=url_col)
                    if cell_obj.hyperlink and cell_obj.hyperlink.target:
                        c_url = cell_obj.hyperlink.target
                        
                    if c_url and c_code:
                        add_to_registry(country, retailer, str(c_brand), str(c_code), c_year, c_size, str(c_title), str(c_url))
        wb.close()
    except Exception as e:
        print(f"  [WARN] Failed parsing workbook {excel_path}: {e}")

print("[MASTER REGISTRY] 2. Scanning Swiss Workbooks & JSONs...")
swiss_excel_files = glob.glob(os.path.join(root_dir, "History/*/price tracker_swiss_*.xlsx")) + glob.glob(os.path.join(root_dir, "History/price tracker_swiss_*.xlsx")) + glob.glob(os.path.join(data_dir, "price tracker_swiss_*.xlsx"))
for se_path in swiss_excel_files:
    if os.path.basename(se_path).startswith("~$"):
        continue
    try:
        sw_wb = openpyxl.load_workbook(se_path, data_only=True)
        for s in sw_wb.sheetnames:
            ws = sw_wb[s]
            s_brand = "SAMSUNG" if "SAMSUNG" in s.upper() else "LG"
            s_ret = "MediaMarkt" if "MEDIAMARKT" in s.upper() or "MM" in s.upper() else ("Interdiscount" if "INTERDISCOUNT" in s.upper() or "ID" in s.upper() else "Digitec")
            
            # Find column positions
            code_col, url_col, year_col, size_col, title_col = 5, 12, 2, 4, 13
            for c_idx in range(1, min(ws.max_column + 1, 20)):
                val = str(ws.cell(row=1, column=c_idx).value or '').lower()
                if 'url' in val or 'link' in val or 'pdp' in val:
                    url_col = c_idx
                elif 'code' in val or 'model' in val:
                    code_col = c_idx
                elif 'year' in val:
                    year_col = c_idx
                elif 'size' in val or 'inch' in val:
                    size_col = c_idx
                elif 'title' in val or 'name' in val:
                    title_col = c_idx
                    
            for r in range(2, ws.max_row + 1):
                c_code = ws.cell(row=r, column=code_col).value
                c_url = ws.cell(row=r, column=url_col).value
                c_year = ws.cell(row=r, column=year_col).value
                c_size = ws.cell(row=r, column=size_col).value
                c_title = ws.cell(row=r, column=title_col).value
                
                cell_obj = ws.cell(row=r, column=url_col)
                if cell_obj.hyperlink and cell_obj.hyperlink.target:
                    c_url = cell_obj.hyperlink.target
                    
                if c_url and c_code:
                    add_to_registry("CH", s_ret, s_brand, str(c_code), c_year, c_size, str(c_title), str(c_url))
        sw_wb.close()
    except Exception as e:
        print(f"  [WARN] Swiss excel error {se_path}: {e}")

ch_raw_map = [
    ("raw_mediamarkt_samsung.json", "CH", "MediaMarkt", "SAMSUNG"),
    ("raw_mediamarkt_lg.json", "CH", "MediaMarkt", "LG"),
    ("raw_interdiscount_samsung.json", "CH", "Interdiscount", "SAMSUNG"),
    ("raw_interdiscount_lg.json", "CH", "Interdiscount", "LG"),
    ("raw_digitec_samsung.json", "CH", "Digitec", "SAMSUNG"),
    ("raw_digitec_lg.json", "CH", "Digitec", "LG")
]
for fname, country, ret, b in ch_raw_map:
    fpath = os.path.join(data_dir, fname)
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                items = json.load(f)
            for it in items:
                u = it.get("link") or it.get("url")
                c = it.get("model_code") or it.get("code")
                y = it.get("year", 2025)
                sz = it.get("size", 0)
                t = it.get("title", "")
                add_to_registry(country, ret, b, c, y, sz, t, u)
        except Exception as e:
            print(f"  [WARN] Error loading {fname}: {e}")

print("[MASTER REGISTRY] 3. Scanning France Raw JSONs...")

for fn in ["raw_fnac_samsung.json", "raw_fnac_lg.json"]:
    fp = os.path.join(data_dir, fn)
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                items = json.load(f)
            b = "SAMSUNG" if "samsung" in fn else "LG"
            for it in items:
                u = it.get("url") or it.get("link")
                t = it.get("title") or it.get("name") or ""
                m_match = re.search(r'(?:TQ\d{2}[A-Z0-9]+|OLED\d{2}[A-Z0-9]+|\d{2}QNED[A-Z0-9]+|TU\d{2}[A-Z0-9]+|TMR\d{2}[A-Z0-9]+)', t)
                m_code = m_match.group(0) if m_match else t
                if u:
                    add_to_registry("FR", "Fnac", b, m_code, 2025, 0, t, u)
        except Exception as e:
            print(f"  [WARN] Error loading {fn}: {e}")

print("[MASTER REGISTRY] 4. Scanning Czech Republic (Alza)...")
for fn in ["raw_alza_samsung.json", "raw_alza_lg.json"]:
    fp = os.path.join(data_dir, fn)
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                items = json.load(f)
            for it in items:
                add_to_registry("CZ", "Alza", it.get("brand", ""), it.get("model_code", ""), it.get("year", 2025), it.get("size", 0), it.get("title", ""), it.get("url", ""))
        except Exception as e:
            print(f"  [WARN] Error loading {fn}: {e}")

print("[MASTER REGISTRY] 5. Scanning Greece (Public.gr)...")
for fn in ["raw_public_gr_samsung.json", "raw_public_gr_lg.json"]:
    fp = os.path.join(data_dir, fn)
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                items = json.load(f)
            for it in items:
                add_to_registry("GR", "Public", it.get("brand", ""), it.get("model_code", ""), it.get("year", 2025), it.get("size", 0), it.get("title", ""), it.get("url", ""))
        except Exception as e:
            print(f"  [WARN] Error loading {fn}: {e}")

print("[MASTER REGISTRY] 6. Scanning Hungary (MediaMarkt HU)...")
for fn in ["mediamarkt_hu_full.json", "raw_mediamarkt_hu_deep.json"]:
    fp = os.path.join(data_dir, fn)
    if os.path.exists(fp):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for it in data:
                    add_to_registry("HU", "MediaMarkt", it.get("Brand", it.get("brand", "")), it.get("Model Code", it.get("model_code", "")), it.get("Model Year", it.get("year", 2025)), it.get("Size (inch)", it.get("size", 0)), it.get("Title", it.get("title", "")), it.get("Product Link", it.get("pdp_url", it.get("url", ""))))
            elif isinstance(data, dict):
                for b, items in data.items():
                    if isinstance(items, list):
                        for it in items:
                            add_to_registry("HU", "MediaMarkt", it.get("brand", b), it.get("model_code", ""), it.get("year", 2025), it.get("size", 0), it.get("title", ""), it.get("pdp_url", it.get("url", "")))
        except Exception as e:
            print(f"  [WARN] Error loading {fn}: {e}")

# Save Master Registry
with open(master_registry_path, "w", encoding="utf-8") as f:
    json.dump(master_urls, f, ensure_ascii=False, indent=2)

print(f"\n=======================================================")
print(f"✅ Pan-European Master Product URL Registry successfully created/updated!")
print(f"📁 Target File: {master_registry_path}")
print(f"📊 Total Registered Model URLs: {len(master_urls)}")

by_country = {}
for k, v in master_urls.items():
    c = v.get("country", "Unknown")
    by_country[c] = by_country.get(c, 0) + 1

print("\nBreakdown by Country:")
for c, cnt in sorted(by_country.items()):
    print(f"  • {c:<5}: {cnt:>4} unique models with verified URLs")
print(f"=======================================================")
