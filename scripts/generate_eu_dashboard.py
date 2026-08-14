# -*- coding: utf-8 -*-
import openpyxl
import json
import os
import re
import sys
import glob
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))
data_dir = os.path.join(root_dir, "data")
history_dir = os.path.join(root_dir, "History_EU")
template_path = os.path.join(data_dir, "eu_price_dashboard_template.html")
workspace_dashboard_path = os.path.join(data_dir, "eu_price_dashboard.html")
firebase_public_path = os.path.join(root_dir, "public_eu", "index.html")

artifact_dir = r"C:\Users\harry.park\.gemini\antigravity\brain\02947bc7-1209-42f6-ac10-ab9b6ba3e82a"
artifact_dashboard_path = os.path.join(artifact_dir, "eu_price_dashboard.html")

EU_COUNTRIES = ["UK", "DE", "FR", "ES", "IT", "NL", "AT", "CH", "CZ", "GR", "SE", "HU"]

COUNTRY_RETAILERS = {
    "DE": ["MediaMarkt"],
    "AT": ["MediaMarkt"],
    "CH": ["MediaMarkt"],
    "ES": ["MediaMarkt"],
    "NL": ["MediaMarkt"],
    "UK": ["Currys"],
    "FR": ["Fnac"],
    "CZ": ["Alza"],
    "GR": ["Public"],
    "SE": ["Elgiganten"],
    "IT": ["MediaWorld", "Unieuro"],
    "HU": ["MediaMarkt"]
}

PAIRS_CONFIG_2025 = {
    "OLED": [
        {"lg": "G5", "sam": "S95F", "sizes": ["83", "77", "65", "55"]},
        {"lg": "C5", "sam": "S90F", "sizes": ["83", "77", "65", "55", "48", "42"]},
        {"lg": "B5", "sam": "S85F", "sizes": ["83", "77", "65", "55", "48"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED86A", "sam": "QN80F", "sizes": ["100", "86", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED86A", "sam": "QN70F", "sizes": ["100", "86", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED80A", "sam": "Q8F", "sizes": ["100", "86", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED84A", "sam": "Q7F", "sizes": ["100", "86", "85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": [
        {"lg": "UA75", "sam": "U8000F", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ]
}

PAIRS_CONFIG_2026 = {
    "OLED": [
        {"lg": "G6", "sam": "S99H", "sizes": ["83", "77", "65", "55"]},
        {"lg": "G6", "sam": "S95H", "sizes": ["83", "77", "65", "55", "48"]},
        {"lg": "C6", "sam": "S90H", "sizes": ["83", "77", "65", "55", "48", "42"]},
        {"lg": "B6", "sam": "S85H", "sizes": ["83", "77", "65", "55", "48"]}
    ],
    "MRGB": [
        {"lg": "MRGB95", "sam": "R95H", "sizes": ["100", "86", "75", "65"]},
        {"lg": "MRGB85", "sam": "R85H", "sizes": ["86", "75", "65", "55", "50"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED93", "sam": "QN80H", "sizes": ["85", "75", "65", "55"]},
        {"lg": "QNED85", "sam": "QN70H", "sizes": ["85", "75", "65", "55"]},
        {"lg": "QNED80", "sam": "Q8H", "sizes": ["85", "75", "65", "55", "50"]},
        {"lg": "QNED70", "sam": "Q7H", "sizes": ["85", "75", "65", "55"]},
        {"lg": "QNED81B", "sam": "M80H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": [
        {"lg": "NU85", "sam": "U8000H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ]
}

PAIRS_CONFIG_2026_IT = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": PAIRS_CONFIG_2026["MRGB"],
    "QNED/QLED": [
        {"lg": "QNED87B", "sam": "QN70H", "sizes": ["100", "86", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70B", "sam": "M70H", "sizes": ["86", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2026_UK = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": PAIRS_CONFIG_2026["MRGB"],
    "QNED/QLED": [
        {"lg": "QNED86B", "sam": "QN80H", "sizes": ["100", "86", "85", "75", "65", "55", "50"]},
        {"lg": "QNED86B", "sam": "QN70H", "sizes": ["86", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M70H", "sizes": ["86", "85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2025_NL = {
    "OLED": PAIRS_CONFIG_2025["OLED"],
    "QNED/QLED": [
        {"lg": "QNED86A", "sam": "QN74F", "sizes": ["85", "75", "65", "55"]},
        {"lg": "QNED70A", "sam": "Q7F", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2025["UHD 4K"]
}

PAIRS_CONFIG_2026_NL = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": PAIRS_CONFIG_2026["MRGB"],
    "QNED/QLED": [
        {"lg": "QNED86B", "sam": "QN80H", "sizes": ["100", "85", "75", "65", "55", "50"]},
        {"lg": "QNED82B", "sam": "M80H", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70B", "sam": "M70H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2025_ES = {
    "OLED": PAIRS_CONFIG_2025["OLED"],
    "QNED/QLED": [
        {"lg": "QNED93", "sam": "QN80F", "sizes": ["100", "85", "75", "65", "55"]},
        {"lg": "QNED86A", "sam": "QN70F", "sizes": ["100", "85", "75", "65", "55"]},
        {"lg": "QNED70A", "sam": "Q7F", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": [
        {"lg": "UA75", "sam": "U7025F", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ]
}

PAIRS_CONFIG_2026_CZ = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": PAIRS_CONFIG_2026["MRGB"],
    "QNED/QLED": [
        {"lg": "QNED93B", "sam": "QN80H", "sizes": ["100", "86", "85", "75", "65", "55", "50"]},
        {"lg": "QNED86B", "sam": "QN80H", "sizes": ["100", "86", "85", "75", "65", "55", "50"]},
        {"lg": "QNED85B", "sam": "QN70H", "sizes": ["86", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED80B", "sam": "M80H", "sizes": ["86", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70B", "sam": "M70H", "sizes": ["86", "85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2026_GR = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": [
        {"lg": "MRGB96B", "sam": "R95H", "sizes": ["100", "86", "75", "65"]},
        {"lg": "MRGB87B", "sam": "R85H", "sizes": ["86", "75", "65", "55"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED87B", "sam": "QN80H", "sizes": ["100", "86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED81B", "sam": "QN70H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED81B", "sam": "M80H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M70H", "sizes": ["86", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2025_DE = {
    "OLED": PAIRS_CONFIG_2025["OLED"],
    "QNED/QLED": [
        {"lg": "QNED86A", "sam": "QN80F", "sizes": ["100", "85", "75", "65", "55"]},
        {"lg": "QNED86A", "sam": "QN70F", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70A", "sam": "Q7F", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2025["UHD 4K"]
}

PAIRS_CONFIG_2026_ES = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": PAIRS_CONFIG_2026["MRGB"],
    "QNED/QLED": [
        {"lg": "QNED86B", "sam": "QN80H", "sizes": ["100", "85", "75", "65", "55", "50"]},
        {"lg": "QNED81B", "sam": "M80H", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M70H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2026_DE = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": PAIRS_CONFIG_2026["MRGB"],
    "QNED/QLED": [
        {"lg": "QNED93", "sam": "QN80H", "sizes": ["85", "75", "65", "55"]},
        {"lg": "QNED86B", "sam": "QN70H", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M80H", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M70H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2026_AT = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": [
        {"lg": "MRGB95", "sam": "R95H", "sizes": ["86", "75", "65"]},
        {"lg": "MRGB87B", "sam": "R86H", "sizes": ["86", "75", "65", "55", "50"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED93", "sam": "QN80H", "sizes": ["85", "75", "65", "55"]},
        {"lg": "QNED86B", "sam": "QN70H", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M82H", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M72H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2026_CH = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": PAIRS_CONFIG_2026["MRGB"],
    "QNED/QLED": [
        {"lg": "QNED86B", "sam": "QN80H", "sizes": ["85", "75", "65", "55", "50"]},
        {"lg": "QNED70B", "sam": "M70H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2026_FR = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": [
        {"lg": "MRGB96B", "sam": "R95H", "sizes": ["100", "86", "75", "65"]},
        {"lg": "MRGB87B", "sam": "R85H", "sizes": ["86", "75", "65", "55"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED87", "sam": "QN80H", "sizes": ["100", "86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED81B", "sam": "QN74H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED81B", "sam": "M80H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70B", "sam": "M70H", "sizes": ["86", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2025_FR = {
    "OLED": PAIRS_CONFIG_2025["OLED"],
    "QNED/QLED": [
        {"lg": "QNED87", "sam": "QN80F", "sizes": ["100", "85", "75", "65", "55"]},
        {"lg": "QNED87", "sam": "QN74F", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED84A", "sam": "Q7F", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2025["UHD 4K"]
}

PAIRS_CONFIG_2026_HU = {
    "OLED": [
        {"lg": "G6", "sam": "S99H", "sizes": ["83", "77", "65", "55"]},
        {"lg": "G6", "sam": "S95H", "sizes": ["83", "77", "65", "55", "48"]},
        {"lg": "C6", "sam": "S90H", "sizes": ["83", "77", "65", "55", "48", "42"]},
        {"lg": "B6", "sam": "S85H", "sizes": ["83", "77", "65", "55", "48"]}
    ],
    "MRGB": [
        {"lg": "MRGB95B", "sam": "R95H", "sizes": ["86", "85", "75", "65", "55"]},
        {"lg": "MRGB87B", "sam": "R85H", "sizes": ["86", "85", "75", "65", "55"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED93B/92B", "sam": "QN80H", "sizes": ["86", "85", "75", "65", "55"]},
        {"lg": "QNED87B", "sam": "QN80H", "sizes": ["100", "86", "85", "75", "65", "55", "50"]},
        {"lg": "QNED80B", "sam": "M80H", "sizes": ["86", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70B", "sam": "M74H", "sizes": ["86", "85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": [
        {"lg": "NU8E", "sam": "U8000H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ]
}

PAIRS_CONFIG_2025_HU = {
    "OLED": [
        {"lg": "G5", "sam": "S95F", "sizes": ["83", "77", "65", "55"]},
        {"lg": "C5", "sam": "S90F", "sizes": ["83", "77", "65", "55", "48", "42"]},
        {"lg": "B5", "sam": "S85F", "sizes": ["83", "77", "65", "55", "48"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED86A", "sam": "QN80F", "sizes": ["86", "85", "75", "65", "55", "50"]},
        {"lg": "QNED80A", "sam": "QN70F", "sizes": ["86", "85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED7EA", "sam": "Q7F", "sizes": ["86", "85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": [
        {"lg": "UA75", "sam": "U8072F", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "UA73", "sam": "U8000F", "sizes": ["85", "75", "65", "55", "50", "43"]}
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

def parse_direct_cut(promo, price):
    if not promo or price <= 0:
        return 0
    # 1. Percentage check first: 'Direct Cut 10%' or 'Get 10% off'
    m_pct = re.search(r'Direct Cut\s+(\d+(?:\.\d+)?)\s*%', promo, re.I)
    if not m_pct:
        m_pct = re.search(r'(?:Get|Save)\s+(\d+(?:\.\d+)?)\s*%\s*off.*?(?:code|voucher)', promo, re.I)
    if m_pct:
        try:
            pct = float(m_pct.group(1))
            return int(round(price * (pct / 100.0)))
        except ValueError:
            pass

    # 2. Fixed amount check: 'Direct Cut GBP 200' or 'Get £200 off'
    m_fixed = re.search(r'Direct Cut\s+(?:GBP|CHF|EUR|€|£)\s*([\d,]+(?:\.\d+)?)', promo, re.I)
    if not m_fixed:
        m_fixed = re.search(r'Direct Cut\s+([\d,]+(?:\.\d+)?)\s*(?:GBP|CHF|EUR|€|£)', promo, re.I)
    if not m_fixed:
        m_fixed = re.search(r'(?:Get|Save)\s+(?:GBP|CHF|EUR|€|£)?\s*([\d,]+(?:\.\d+)?)\s*off.*?(?:code|voucher)', promo, re.I)
    if m_fixed:
        try:
            return int(round(float(m_fixed.group(1).replace(',', ''))))
        except ValueError:
            pass
            
    return 0

def extract_products_from_sheet(sheet):
    products = []
    if sheet is None:
        return products
        
    for r in range(2, sheet.max_row + 1):
        brand = sheet.cell(row=r, column=1).value
        if not brand or str(brand).strip().lower() in ["brand", "marca", "marque"]:
            continue
            
        year = sheet.cell(row=r, column=2).value
        if str(year).strip().lower() in ["model year", "year", "modelyear"]:
            continue
        disp = sheet.cell(row=r, column=3).value
        size = sheet.cell(row=r, column=4).value
        code = sheet.cell(row=r, column=5).value
        price = clean_price(sheet.cell(row=r, column=6).value)
        promo = str(sheet.cell(row=r, column=10).value or "").strip()
        cashback = clean_price(sheet.cell(row=r, column=9).value)
        direct_cut = parse_direct_cut(promo, price)
        total_discount = cashback + direct_cut
        net = max(0, price - total_discount) if price > 0 else 0
        
        products.append({
            "brand": str(brand).strip(),
            "year": int(year) if year else 0,
            "display_type": str(disp).strip() if disp else "",
            "size": int(size) if size else 0,
            "model_code": str(code).strip() if code else "",
            "price": price,
            "cashback": cashback,
            "direct_cut": direct_cut,
            "net": net,
            "promo": promo
        })
    return products

def find_product(products, brand, size, series, year):
    target_size = int(size)
    matched_candidates = []
    for p in products:
        p_size = p["size"]
        # Allow 85 and 86 inch to match flexibly for flagship size pairs
        if target_size in [85, 86] and p_size in [85, 86]:
            size_match = True
        else:
            size_match = (p_size == target_size)
            
        if p["brand"].upper() != brand.upper() or not size_match or p["year"] != year:
            continue
        code = p["model_code"].upper()
        
        if "QNED" in series.upper() and "QNED" not in code:
            continue
        if "QNED" not in series.upper() and "QNED" in code:
            continue
            
        match = False
        series_upper = series.upper()
        
        if series_upper in ["G6", "G5", "C6", "C5", "B6", "B5"]:
            is_oled = p.get("display_type", "").upper() in ["OLED", "OLED EVO"] or "OLED" in code or code.startswith("OLED")
            if is_oled or re.match(r'^\d{2}(G6|G5|C6|C5|B6|B5)', code):
                match = bool(re.search(r'(?:^|\d{2})' + series_upper, code))
        elif series_upper in ["QNED93B/92B", "QNED93B", "QNED92B", "QNED93A", "QNED93", "QNED92"]:
            match = any(x in code for x in ["QNED93", "QNED92", "QNED91", "QNED90"])
        elif series_upper in ["QNED72B", "QNED72"]:
            match = "QNED72" in code
        elif series_upper in ["QNED86B"]:
            match = "QNED86" in code or (p_size in [98, 99, 100] and "QNED87" in code)
        elif series_upper in ["QNED87B", "QNED87"]:
            match = any(x in code for x in ["QNED87", "QNED86"])
        elif series_upper in ["QNED82B", "QNED82"]:
            match = "QNED82" in code
        elif series_upper in ["QNED70A", "QNED70B", "QNED70", "QNED71B", "QNED71"]:
            match = any(x in code for x in ["QNED70", "QNED71", "QNED72", "QNED7E"])
        elif series_upper in ["QNED86A", "QNED86", "QNED85B", "QNED85A", "QNED85"]:
            match = "QNED86" in code or "QNED85" in code or "QNED87" in code
        elif series_upper in ["QNED84A", "QNED84"]:
            match = "QNED84" in code or "QNED80" in code or "QNED82" in code
        elif series_upper in ["QNED80B", "QNED80A", "QNED80"]:
            match = any(x in code for x in ["QNED80", "QNED81", "QNED82", "QNED84"])
        elif series_upper in ["M74H", "M74"]:
            match = any(x in code for x in ["M74", "M70", "M72", "M73", "M75"])
        elif series_upper in ["M70H", "M70", "M72H", "M72"]:
            match = any(x in code for x in ["M70", "M72", "M73", "M74", "M75"])
        elif series_upper in ["QNED81B", "QNED81"]:
            match = "QNED81" in code or "QNED80B" in code or "QNED80" in code or "QNED82" in code or "QNED84" in code
        elif series_upper in ["M80H", "M80", "M82H", "M82"]:
            match = any(x in code for x in ["M80", "M82", "M83", "M85"])
        elif series_upper in ["QNED70"]:
            match = "QNED70" in code or "QNED72" in code or "QNED7E" in code
        elif series_upper in ["QN80F", "QN80", "QN80H"]:
            if not any(x in code for x in ["LS03", "LS01", "LS05", "FRAME", "QN90", "QN95", "QN900"]):
                match = any(x in code for x in ["QN80", "QN81", "QN82", "QN83", "QN84", "QN85", "QN88"])
        elif series_upper in ["QN74F", "QN74", "QN70F", "QN70", "QN70H"]:
            if not any(x in code for x in ["LS03", "LS01", "LS05", "FRAME"]):
                match = any(x in code for x in ["QN70", "QN71", "QN72", "QN73", "QN74", "QN75"])
        elif series_upper in ["Q8F", "Q8", "Q8H"]:
            if not any(x in code for x in ["LS03", "LS01", "LS05", "FRAME"]):
                match = bool(re.search(r'(?:^|[A-Z]{2}\d{2})(Q80|Q85|Q81|Q82|Q83|Q84|Q8F|Q8A|Q8D|Q8)(?:[^0-9]|$)', code))
        elif series_upper in ["Q7F", "Q7", "Q7H"]:
            if not any(x in code for x in ["LS03", "LS01", "LS05", "FRAME"]):
                match = bool(re.search(r'(?:^|[A-Z]{2}\d{2})(Q70|Q71|Q72|Q73|Q74|Q75|Q7F|Q7A|Q7D|Q7)(?:[^0-9]|$)', code))
        elif series_upper in ["QNED7EB", "QNED7EA", "QNED7E"]:
            match = any(x in code for x in ["QNED7E", "QNED70", "QNED71", "QNED72"])
        elif series_upper in ["NU8E", "NU85"]:
            match = any(x in code for x in ["NU8E", "NU85", "NU80", "NU75", "UA77", "UT", "UR", "UQ"])
        elif series_upper in ["UA75", "UA73"]:
            match = any(x in code for x in ["UA75", "UA73", "UA77", "UT", "UR", "UQ"])
        elif series_upper in ["U8072F", "U8072"]:
            match = any(x in code for x in ["U8072", "U8070", "8072", "U8000", "U8005", "DU8000", "CU8000"])
        elif series_upper in ["U7025F", "U7025"]:
            match = any(x in code for x in ["U7025", "7025", "TU7025"])
        elif series_upper in ["U8000F", "U8000H", "U8000"]:
            match = any(x in code for x in ["U8000", "U8005", "U8010", "U8070", "U8072", "U8075", "U8079", "U8080", "U8090", "U8092", "8072", "8092", "DU8000", "CU8000"])
        elif series_upper in ["S99H", "S99"]: match = "S99" in code
        elif series_upper in ["S95H", "S95F", "S95"]: match = "S95" in code
        elif series_upper in ["S90H", "S90F", "S90"]: match = any(x in code for x in ["S90", "S91", "S92", "S93", "S94"])
        elif series_upper in ["S85H", "S85F", "S85"]: match = any(x in code for x in ["S85", "S84", "S86", "S83", "S82", "S81", "S80"])
        elif series_upper in ["MRGB95B", "MRGB96B", "MRGB96", "MRGB95", "MRGB9"]: match = any(x in code for x in ["MRGB95", "MRGB96", "MRGB9", "MR95", "MR96"])
        elif series_upper in ["MRGB87B", "MRGB87", "MRGB85", "MRGB8"]: match = any(x in code for x in ["MRGB87", "MRGB85", "MRGB86", "MRGB8", "MR85"])
        elif series_upper in ["R95H", "R95"]: match = bool(re.search(r'(?:R95|MRE.*95|GMR.*95|TMR.*95)', code))
        elif series_upper in ["R86H", "R86", "R85H", "R85"]: match = bool(re.search(r'(?:R86|R85|MRE.*86|MRE.*85|GMR.*86|GMR.*85|TMR.*85)', code))
        
        if match:
            matched_candidates.append(p)
            
    if not matched_candidates:
        return None
        
    # Priority sorting:
    # 1. Official European/Italian OLED sub-models (e.g. G56, G66, C55, C65, B65)
    # 2. True U8000 series (U8000, U8005, U8070) over U7000 fallback
    def get_priority(item):
        code = item["model_code"].upper()
        if any(x in code for x in ["G56", "G66", "C55", "C65", "B65", "B55"]):
            return 0
        if any(x in code for x in ["U8000", "U8005", "U8010", "U8070", "U8075", "U8090"]):
            return 1
        if "U7000" in code:
            return 2
        return 3
        
    matched_candidates.sort(key=get_priority)
    return matched_candidates[0]

def find_sheet(wb, possible_names):
    for name in possible_names:
        if name in wb.sheetnames:
            return wb[name]
    return None

def build_paired_data(wb, country, year, config):
    paired = {}
    sheet_data = {}
    
    for ret in COUNTRY_RETAILERS[country]:
        ret_key = ret.lower().replace('mediamarkt', 'mm').replace('mediaworld', 'mw').replace('unieuro', 'uni')
        samsung_sheet = find_sheet(wb, [f"{ret}_{country}_SAMSUNG_Full", f"{ret}_{country}_SAMSUNG_Full (EUR)", f"{ret}_{country}_SAMSUNG_Full (GBP)", f"{ret}_{country}_Samsung", f"{ret}_{country}_SAMSUNG", f"Alza_CZ_Samsung", "Public_GR_Samsung", "MediaMarkt_HU_Samsung"])
        lg_sheet = find_sheet(wb, [f"{ret}_{country}_LG_Full", f"{ret}_{country}_LG_Full (EUR)", f"{ret}_{country}_LG_Full (GBP)", f"{ret}_{country}_LG", f"{ret}_{country}_LG", f"Alza_CZ_LG", "Public_GR_LG", "MediaMarkt_HU_LG"])
        
        sheet_data[ret_key] = {
            "SAMSUNG": extract_products_from_sheet(samsung_sheet),
            "LG": extract_products_from_sheet(lg_sheet)
        }
        
    for cat, series_list in config.items():
        paired[cat] = []
        for pair in series_list:
            lg_series = pair["lg"]
            sam_series = pair["sam"]
            
            for size in pair["sizes"]:
                pair_label_str = f"{size}\"{lg_series} vs. {size}\"{sam_series}"
                if "U8000" in sam_series:
                    pair_label_str = f"{size}\"{lg_series} vs. {size}\"U8070H"
                if ("MRGB96" in lg_series or "MRGB95" in lg_series) and str(size) in ["86", "85"]:
                    pair_label_str = f'86"{lg_series} vs. 85"R95H'
                elif ("MRGB87" in lg_series or "MRGB85" in lg_series) and str(size) in ["86", "85"]:
                    pair_label_str = f'86"{lg_series} vs. 85"{sam_series}'
                elif "QNED93" in lg_series and "QN80" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED93B/92B vs. 85"QN80H'
                elif "QNED87" in lg_series and "QN80" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED87B vs. 85"QN80H'
                elif "QNED80" in lg_series and "M80" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED80B vs. 85"M80H'
                elif "QNED70" in lg_series and ("M74" in sam_series or "M70" in sam_series) and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED70B vs. 85"M74H' if "M74" in sam_series else '86"QNED70B vs. 85"M70H'
                elif "QNED72" in lg_series and ("M70" in sam_series or "M72" in sam_series) and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED72B vs. 85"M72H'
                elif "QNED72" in lg_series and ("M80" in sam_series or "M82" in sam_series) and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED72B vs. 85"M82H'
                elif "QNED72" in lg_series and "M70" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED72B vs. 85"M70H'
                elif "QNED86" in lg_series and "QN70" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED86B vs. 85"QN70H'
                elif "QNED86" in lg_series and "QN80" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED86B vs. 85"QN80H'
                elif "QNED82" in lg_series and "M80" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED82B vs. 85"M80H'
                elif "QNED81" in lg_series and "M80" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED81B vs. 85"M80H'
                elif "QNED86" in lg_series and "QN74" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED86A vs. 85"QN74F'
                elif "QNED70" in lg_series and "Q7" in sam_series and str(size) in ["86", "85"]:
                    pair_label_str = '86"QNED70A vs. 85"Q7F'
                elif "QNED86" in lg_series and "QN80" in sam_series and str(size) in ["100"]:
                    pair_label_str = '100"QNED87B vs. 100"QN80H'
                    
                entry = {
                    "size": int(size),
                    "lg_series": f"{size}{lg_series}",
                    "sam_series": f"{size}{sam_series}",
                    "pair_label": pair_label_str
                }
                
                for ret in COUNTRY_RETAILERS[country]:
                    ret_key = ret.lower().replace('mediamarkt', 'mm').replace('mediaworld', 'mw').replace('unieuro', 'uni')
                    lg_prod = find_product(sheet_data[ret_key]["LG"], "LG", size, lg_series, year)
                    sam_prod = find_product(sheet_data[ret_key]["SAMSUNG"], "SAMSUNG", size, sam_series, year)
                    
                    entry[f"lg_code_{ret_key}"] = lg_prod["model_code"] if lg_prod else ""
                    entry[f"lg_price_{ret_key}"] = lg_prod["price"] if lg_prod else 0
                    entry[f"lg_net_{ret_key}"] = lg_prod["net"] if lg_prod else 0
                    entry[f"lg_promo_{ret_key}"] = lg_prod["promo"] if lg_prod else ""
                    entry[f"lg_model_{ret_key}"] = lg_prod["model_code"] if lg_prod else ""
                    
                    entry[f"sam_code_{ret_key}"] = sam_prod["model_code"] if sam_prod else ""
                    entry[f"sam_price_{ret_key}"] = sam_prod["price"] if sam_prod else 0
                    entry[f"sam_net_{ret_key}"] = sam_prod["net"] if sam_prod else 0
                    entry[f"sam_promo_{ret_key}"] = sam_prod["promo"] if sam_prod else ""
                    entry[f"sam_model_{ret_key}"] = sam_prod["model_code"] if sam_prod else ""
                    
                paired[cat].append(entry)
    return paired

def scan_history_data():
    historical_data = {}
    
    if not os.path.exists(history_dir):
        print(f"[WARN] History directory not found: {history_dir}")
        return historical_data
        
    date_folders = []
    for name in os.listdir(history_dir):
        path = os.path.join(history_dir, name)
        if os.path.isdir(path) and re.match(r'^\d{4}\s+\d{4}$', name):
            date_folders.append(name)
            
    date_folders.sort()
    
    for folder in date_folders:
        folder_path = os.path.join(history_dir, folder)
        excel_files = glob.glob(os.path.join(folder_path, "price tracker_EU_*.xlsx"))
        excel_files = [f for f in excel_files if not os.path.basename(f).startswith("~$")]
        if not excel_files:
            continue
            
        excel_files.sort()
        best_file = excel_files[-1]
        
        parts = folder.split()
        date_str = f"{parts[1][:2]}/{parts[1][2:]}"
        print(f"  ➔ Scanning EU history: {date_str} from {os.path.basename(best_file)}")
        
        try:
            wb = openpyxl.load_workbook(os.path.join(folder_path, best_file), data_only=True)
            for country in EU_COUNTRIES:
                if country not in historical_data:
                    historical_data[country] = {"2025": {}, "2026": {}}
                    
                for year, config in [("2025", PAIRS_CONFIG_2025), ("2026", PAIRS_CONFIG_2026)]:
                    paired_data = build_paired_data(wb, country, int(year), config)
                    
                    for cat, pairs in paired_data.items():
                        for p in pairs:
                            lg_key = p["lg_series"]
                            if lg_key not in historical_data[country][year]:
                                historical_data[country][year][lg_key] = {"history": [], "display": cat}
                            sam_key = p["sam_series"]
                            if sam_key not in historical_data[country][year]:
                                historical_data[country][year][sam_key] = {"history": [], "display": cat}
                                
                            lg_hist_entry = {"date": date_str}
                            sam_hist_entry = {"date": date_str}
                            
                            for ret in COUNTRY_RETAILERS[country]:
                                ret_key = ret.lower().replace('mediamarkt', 'mm').replace('mediaworld', 'mw').replace('unieuro', 'uni')
                                lg_hist_entry[f"{ret_key}_price"] = p.get(f"lg_price_{ret_key}", 0)
                                lg_hist_entry[f"{ret_key}_net"] = p.get(f"lg_net_{ret_key}", 0)
                                sam_hist_entry[f"{ret_key}_price"] = p.get(f"sam_price_{ret_key}", 0)
                                sam_hist_entry[f"{ret_key}_net"] = p.get(f"sam_net_{ret_key}", 0)
                                
                            historical_data[country][year][lg_key]["history"].append(lg_hist_entry)
                            historical_data[country][year][sam_key]["history"].append(sam_hist_entry)
            wb.close()
        except Exception as e:
            print(f"  ➔ [WARN] Failed to load/parse historical file {best_file}: {e}")
            
    return historical_data

def main():
    excel_files = glob.glob(os.path.join(data_dir, "price tracker_EU_*.xlsx"))
    excel_files = [f for f in excel_files if not os.path.basename(f).startswith("~$")]
    if not excel_files:
        print("[ERROR] No EU Price Tracker Excel workbook found.")
        return
        
    excel_files.sort()
    
    # Auto pre-archive Excel files to History_EU directory if not archived yet
    os.makedirs(history_dir, exist_ok=True)
    import shutil
    for fpath in excel_files:
        fname = os.path.basename(fpath)
        match = re.search(r'(\d{4}\s+\d{4})', fname)
        if match:
            folder_name = match.group(1)
            target_folder = os.path.join(history_dir, folder_name)
            os.makedirs(target_folder, exist_ok=True)
            target_dest = os.path.join(target_folder, fname)
            if not os.path.exists(target_dest):
                shutil.copy2(fpath, target_dest)
                print(f"  ➔ [PRE-ARCHIVE] Copied {fname} to {target_folder}")

    latest_excel = excel_files[-1]
    print(f"[PARSING EXCEL] Loading latest report: {latest_excel}...")
    
    wb = openpyxl.load_workbook(latest_excel, data_only=True)
    price_data = {}
    
    for country in EU_COUNTRIES:
        if country == "IT":
            cfg_2026 = PAIRS_CONFIG_2026_IT
        elif country == "UK":
            cfg_2026 = PAIRS_CONFIG_2026_UK
        elif country == "NL":
            cfg_2026 = PAIRS_CONFIG_2026_NL
        elif country == "ES":
            cfg_2026 = PAIRS_CONFIG_2026_ES
        elif country == "DE":
            cfg_2026 = PAIRS_CONFIG_2026_DE
        elif country == "AT":
            cfg_2026 = PAIRS_CONFIG_2026_AT
        elif country == "CH":
            cfg_2026 = PAIRS_CONFIG_2026_CH
        elif country == "CZ":
            cfg_2026 = PAIRS_CONFIG_2026_CZ
        elif country == "GR":
            cfg_2026 = PAIRS_CONFIG_2026_GR
        elif country == "FR":
            cfg_2026 = PAIRS_CONFIG_2026_FR
        elif country == "HU":
            cfg_2026 = PAIRS_CONFIG_2026_HU
        else:
            cfg_2026 = PAIRS_CONFIG_2026
            
        if country == "NL":
            cfg_2025 = PAIRS_CONFIG_2025_NL
        elif country == "ES":
            cfg_2025 = PAIRS_CONFIG_2025_ES
        elif country == "DE":
            cfg_2025 = PAIRS_CONFIG_2025_DE
        elif country == "FR":
            cfg_2025 = PAIRS_CONFIG_2025_FR
        elif country == "HU":
            cfg_2025 = PAIRS_CONFIG_2025_HU
        else:
            cfg_2025 = PAIRS_CONFIG_2025
            
        price_data[country] = {
            "2025": build_paired_data(wb, country, 2025, cfg_2025),
            "2026": build_paired_data(wb, country, 2026, cfg_2026)
        }
    wb.close()
    
    print("[PARSING HISTORY] Scanning all historical survey folders...")
    history_data = scan_history_data()
    price_data["history"] = history_data
    
    if not os.path.exists(template_path):
        print(f"[ERROR] HTML base template not found: {template_path}")
        return
        
    print(f"[COMPILING DASHBOARD] Injecting JSON data and survey dates into template...")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    json_str = json.dumps(price_data, indent=2)
    injection_block = f"const priceData = {json_str};"
    
    survey_date = datetime.now().strftime("%Y년 %m월 %d일")
    survey_date_dot = datetime.now().strftime("%Y.%m.%d")
    
    compiled_html = html_content.replace("// {{INSERT_PRICE_DATA}}", injection_block)
    compiled_html = compiled_html.replace("{{SURVEY_DATE}}", survey_date)
    compiled_html = compiled_html.replace("{{SURVEY_DATE_DOT}}", survey_date_dot)
    
    with open(workspace_dashboard_path, "w", encoding="utf-8") as f:
        f.write(compiled_html)
    print(f"  ➔ [SAVED] Compiled HTML saved to Workspace: {workspace_dashboard_path}")
    
    os.makedirs(artifact_dir, exist_ok=True)
    with open(artifact_dashboard_path, "w", encoding="utf-8") as f:
        f.write(compiled_html)
    print(f"  ➔ [SAVED] Compiled HTML saved to Artifact: {artifact_dashboard_path}")
    
    os.makedirs(os.path.dirname(firebase_public_path), exist_ok=True)
    with open(firebase_public_path, "w", encoding="utf-8") as f:
        f.write(compiled_html)
    print(f"  ➔ [SAVED] Compiled HTML saved to Firebase Public: {firebase_public_path}")
    
    # Save to latest History_EU folder if exists
    if os.path.exists(history_dir):
        folders = [os.path.join(history_dir, d) for d in os.listdir(history_dir) if os.path.isdir(os.path.join(history_dir, d)) and re.match(r'^\d{4}\s+\d{4}$', d)]
        if folders:
            folders.sort()
            latest_hist_folder = folders[-1]
            latest_hist_html = os.path.join(latest_hist_folder, "eu_price_dashboard.html")
            with open(latest_hist_html, "w", encoding="utf-8") as f:
                f.write(compiled_html)
            print(f"  ➔ [SAVED] Compiled HTML saved to History_EU: {latest_hist_html}")
    
    print("\n[DASHBOARD COMPILATION COMPLETED SUCCESSFULLY]")

if __name__ == "__main__":
    main()
