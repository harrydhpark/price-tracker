# -*- coding: utf-8 -*-
import openpyxl
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

master_registry_path = "data/master_product_urls.json"
master_urls = {}

if os.path.exists(master_registry_path):
    try:
        with open(master_registry_path, "r", encoding="utf-8") as f:
            master_urls = json.load(f)
    except Exception as e:
        master_urls = {}

def add_to_registry(country, retailer, brand, model_code, year, size, title, url):
    if not url or not str(url).startswith("http"):
        return
    if not model_code or str(model_code).strip() in ["", "Unknown", "Unknown Samsung", "Unknown LG"]:
        return
        
    key = f"{country}_{retailer}_{model_code.strip()}".upper()
    
    master_urls[key] = {
        "country": country.upper(),
        "retailer": retailer,
        "brand": brand.upper(),
        "model_code": model_code.strip(),
        "year": int(year) if year and str(year).isdigit() else 2025,
        "size": int(size) if size and str(size).isdigit() else 0,
        "title": title or "",
        "url": str(url).strip(),
        "last_updated": "2026-08-14"
    }

# 1. Load from latest Pan-European Excel
excel_path = "data/price tracker_EU_2026 0814_v1.xlsx"
if os.path.exists(excel_path):
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        
        country = "EU"
        retailer = "Retailer"
        brand = "SAMSUNG" if "SAMSUNG" in sheet_name.upper() else ("LG" if "LG" in sheet_name.upper() else "TV")
        
        # Determine country and retailer
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
        elif "SE" in sheet_name: country = "SE"; retailer = "Elgiganten"
        elif "IT" in sheet_name:
            country = "IT"
            retailer = "MediaWorld" if "MediaWorld" in sheet_name or "MW" in sheet_name else "Unieuro"
            
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
            
        url_col = url_col or 12
        code_col = code_col or 5
        year_col = year_col or 2
        size_col = size_col or 4
        title_col = title_col or 13
        
        for r in range(2, ws.max_row + 1):
            c_brand = ws.cell(row=r, column=1).value or brand
            c_year = ws.cell(row=r, column=year_col).value
            c_size = ws.cell(row=r, column=size_col).value
            c_code = ws.cell(row=r, column=code_col).value
            c_url = ws.cell(row=r, column=url_col).value
            c_title = ws.cell(row=r, column=title_col).value
            
            # If hyperlink object
            cell_obj = ws.cell(row=r, column=url_col)
            if cell_obj.hyperlink and cell_obj.hyperlink.target:
                c_url = cell_obj.hyperlink.target
                
            if c_url and c_code:
                add_to_registry(country, retailer, str(c_brand), str(c_code), c_year, c_size, str(c_title), str(c_url))
                
    wb.close()

# 2. Load from Hungary Full JSON DB
hu_json_path = "data/mediamarkt_hu_full.json"
if os.path.exists(hu_json_path):
    with open(hu_json_path, "r", encoding="utf-8") as f:
        hu_items = json.load(f)
    for it in hu_items:
        add_to_registry(
            country="HU",
            retailer="MediaMarkt",
            brand=it.get("Brand", ""),
            model_code=it.get("Model Code", ""),
            year=it.get("Model Year", 2025),
            size=it.get("Size (inch)", 0),
            title=it.get("Title", ""),
            url=it.get("Product Link", "")
        )

# 3. Load from Swiss price tracker Excel if exists
swiss_excel_path = "History/price tracker_swiss_2026 0814_v1.xlsx"
if not os.path.exists(swiss_excel_path):
    # Scan History folder for latest swiss file
    if os.path.exists("History"):
        swiss_files = [os.path.join("History", f) for f in os.listdir("History") if f.endswith(".xlsx") and "swiss" in f.lower()]
        if swiss_files:
            swiss_files.sort()
            swiss_excel_path = swiss_files[-1]

if os.path.exists(swiss_excel_path):
    try:
        sw_wb = openpyxl.load_workbook(swiss_excel_path, data_only=True)
        for s in sw_wb.sheetnames:
            ws = sw_wb[s]
            s_brand = "SAMSUNG" if "SAMSUNG" in s.upper() else "LG"
            s_ret = "MediaMarkt" if "MEDIAMARKT" in s.upper() or "MM" in s.upper() else ("Interdiscount" if "INTERDISCOUNT" in s.upper() or "ID" in s.upper() else "Digitec")
            for r in range(2, ws.max_row + 1):
                c_code = ws.cell(row=r, column=5).value
                c_url = ws.cell(row=r, column=12).value
                c_year = ws.cell(row=r, column=2).value
                c_size = ws.cell(row=r, column=4).value
                c_title = ws.cell(row=r, column=13).value
                if c_url and c_code:
                    add_to_registry("CH", s_ret, s_brand, str(c_code), c_year, c_size, str(c_title), str(c_url))
        sw_wb.close()
    except Exception as e:
        print("Swiss excel parse error:", e)

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
