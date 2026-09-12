# -*- coding: utf-8 -*-
import openpyxl
import json
import os
import re
import sys
import glob
import shutil
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.insert(0, root_dir)
data_dir = os.path.join(root_dir, "data")
history_dir = os.path.join(root_dir, "History_EU")
template_path = os.path.join(data_dir, "eu_price_dashboard_template.html")
workspace_dashboard_path = os.path.join(data_dir, "eu_price_dashboard.html")
firebase_public_path = os.path.join(root_dir, "public_eu", "index.html")

# Dynamic artifact directory if provided by environment
artifact_dir = os.environ.get("ANTIGRAVITY_ARTIFACT_DIR")
artifact_dashboard_path = os.path.join(artifact_dir, "eu_price_dashboard.html") if artifact_dir else None

EU_COUNTRIES = ["UK", "DE", "FR", "ES", "IT", "NL", "AT", "CH", "CZ", "GR", "HU"]

COUNTRY_RETAILERS = {
    "UK": ["Currys"],
    "DE": ["MediaMarkt"],
    "FR": ["Fnac"],
    "ES": ["MediaMarkt"],
    "IT": ["MediaWorld"],
    "NL": ["MediaMarkt"],
    "AT": ["MediaMarkt"],
    "CH": ["MediaMarkt"],
    "CZ": ["Alza"],
    "GR": ["Public"],
    "HU": ["MediaMarkt"]
}

COUNTRY_CURRENCIES = {
    "UK": "GBP", "DE": "EUR", "FR": "EUR", "ES": "EUR", "IT": "EUR", "NL": "EUR", "AT": "EUR", "CH": "CHF", "CZ": "CZK", "GR": "EUR", "HU": "HUF"
}

CURRENCY_SYMBOLS = {
    "EUR": "€", "GBP": "£", "CHF": "CHF ", "CZK": "Kč ", "HUF": "Ft "
}

PAIRS_CONFIG_2025 = {
    "OLED": [
        {"lg": "G5", "sam": "S95F", "sizes": ["83", "77", "65", "55"]},
        {"lg": "C5", "sam": "S90F", "sizes": ["83", "77", "65", "55", "48", "42"]},
        {"lg": "B5", "sam": "S85F", "sizes": ["83", "77", "65", "55", "48"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED86A", "sam": "QN80F", "sizes": ["100", "86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED86A", "sam": "QN70F", "sizes": ["100", "86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED80A", "sam": "Q8F", "sizes": ["100", "86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED84A", "sam": "Q7F", "sizes": ["100", "86", "75", "65", "55", "50", "43"]}
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
        {"lg": "QNED87B", "sam": "QN70H", "sizes": ["100", "86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70B", "sam": "M70H", "sizes": ["86", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": PAIRS_CONFIG_2026["UHD 4K"]
}

PAIRS_CONFIG_2026_UK = {
    "OLED": PAIRS_CONFIG_2026["OLED"],
    "MRGB": [
        {"lg": "MRGB96", "sam": "R95H", "sizes": ["100", "86", "75", "65"]},
        {"lg": "MRGB88", "sam": "R85H", "sizes": ["86", "75", "65", "55", "50"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED86B", "sam": "QN80H", "sizes": ["100", "86", "75", "65", "55", "50"]},
        {"lg": "QNED86B", "sam": "QN70H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M70H", "sizes": ["86", "75", "65", "55", "50", "43"]}
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
        {"lg": "QNED93B", "sam": "QN80H", "sizes": ["100", "86", "75", "65", "55", "50"]},
        {"lg": "QNED86B", "sam": "QN80H", "sizes": ["100", "86", "75", "65", "55", "50"]},
        {"lg": "QNED85B", "sam": "QN70H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED80B", "sam": "M80H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70B", "sam": "M70H", "sizes": ["86", "75", "65", "55", "50", "43"]}
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
    "MRGB": [
        {"lg": "MRGB96B", "sam": "R95H", "sizes": ["100", "86", "75", "65"]},
        {"lg": "MRGB86B", "sam": "R85H", "sizes": ["86", "75", "65", "55", "50"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED93", "sam": "QN80H", "sizes": ["85", "75", "65", "55"]},
        {"lg": "QNED86B", "sam": "QN70H", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M80H", "sizes": ["85", "75", "65", "55", "50", "43"]},
        {"lg": "QNED72B", "sam": "M70H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ],
    "UHD 4K": [
        {"lg": "NU800", "sam": "U8000H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ]
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
    "OLED": [
        {"lg": "G6", "sam": "S99H", "sizes": ["83", "77", "65", "55"]},
        {"lg": "G6", "sam": "S95H", "sizes": ["83", "77", "65", "55", "48"]},
        {"lg": "C6", "sam": "S90H", "sizes": ["83", "77", "65", "55", "48", "42"]},
        {"lg": "B6", "sam": "S85H", "sizes": ["83", "77", "65", "55", "48"]}
    ],
    "MRGB": [
        {"lg": "MRGB87B", "sam": "R85H", "sizes": ["86", "75", "65", "55", "50"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED86B", "sam": "QN80H", "sizes": ["100", "86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED71B", "sam": "M70H", "sizes": ["65", "55", "50", "43"]},
        {"lg": "QNED70B", "sam": "M70H", "sizes": ["85", "75"]}
    ],
    "UHD 4K": [
        {"lg": "NU85", "sam": "U8000H", "sizes": ["85", "75", "65", "55", "50", "43"]}
    ]
}

PAIRS_CONFIG_2025_CH = {
    "OLED": [
        {"lg": "G5", "sam": "S95F", "sizes": ["83", "77", "65", "55"]},
        {"lg": "C5", "sam": "S90F", "sizes": ["83", "77", "65", "55", "48", "42"]},
        {"lg": "B5", "sam": "S85F", "sizes": ["83", "77", "65", "55"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED86A", "sam": "QN80F", "sizes": ["85", "75", "65", "55"]},
        {"lg": "QNED86A", "sam": "QN70F", "sizes": ["75"]},
        {"lg": "QNED80A", "sam": "Q8F", "sizes": ["85", "75", "65", "55"]},
        {"lg": "QNED80A", "sam": "Q7F", "sizes": ["85"]}
    ],
    "UHD 4K": [
        {"lg": "UA75", "sam": "U8000F", "sizes": ["75", "65", "55", "43"]}
    ]
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
        {"lg": "MRGB95B", "sam": "R95H", "sizes": ["86", "75", "65", "55"]},
        {"lg": "MRGB87B", "sam": "R85H", "sizes": ["86", "75", "65", "55"]}
    ],
    "QNED/QLED": [
        {"lg": "QNED93B/92B", "sam": "QN80H", "sizes": ["86", "75", "65", "55"]},
        {"lg": "QNED87B", "sam": "QN80H", "sizes": ["100", "86", "75", "65", "55", "50"]},
        {"lg": "QNED80B", "sam": "M80H", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED70B", "sam": "M74H", "sizes": ["86", "75", "65", "55", "50", "43"]}
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
        {"lg": "QNED86A", "sam": "QN80F", "sizes": ["86", "75", "65", "55", "50"]},
        {"lg": "QNED80A", "sam": "QN70F", "sizes": ["86", "75", "65", "55", "50", "43"]},
        {"lg": "QNED7EA", "sam": "Q7F", "sizes": ["86", "75", "65", "55", "50", "43"]}
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
    if sheet is None or sheet.max_row < 2:
        return products
        
    # Dynamic header detection
    headers = {}
    for c in range(1, min(sheet.max_column + 1, 20)):
        val = sheet.cell(row=1, column=c).value
        if val:
            headers[str(val).strip().lower()] = c

    def get_col(candidates, default_col):
        for cand in candidates:
            for h_text, col_idx in headers.items():
                if cand == h_text or cand in h_text:
                    return col_idx
        return default_col

    c_brand = get_col(["brand", "marca", "marque"], 1)
    c_year = get_col(["model year", "modelyear", "year"], 2)
    c_disp = get_col(["display type", "display", "series"], 3)
    c_size = get_col(["size (inch)", "size", "inch"], 4)
    c_code = get_col(["model code", "code", "model"], 5)
    
    # Selling price column
    c_price = 6
    for h_text, col_idx in headers.items():
        if ("selling price" in h_text or "price" in h_text) and not any(x in h_text for x in ["was", "original", "discount", "link"]):
            c_price = col_idx
            break
            
    # Cashback column
    c_cashback = None
    for h_text, col_idx in headers.items():
        if "cashback" in h_text:
            c_cashback = col_idx
            break
    if c_cashback is None:
        c_cashback = 9
        
    # Promotion column
    c_promo = None
    for h_text, col_idx in headers.items():
        if any(x in h_text for x in ["promotion", "promo"]) and "cashback" not in h_text:
            c_promo = col_idx
            break
    if c_promo is None:
        c_promo = 10
        
    for r in range(2, sheet.max_row + 1):
        brand = sheet.cell(row=r, column=c_brand).value
        if not brand or str(brand).strip().lower() in ["brand", "marca", "marque"]:
            continue
            
        year = sheet.cell(row=r, column=c_year).value
        if str(year).strip().lower() in ["model year", "year", "modelyear"]:
            continue
        disp = sheet.cell(row=r, column=c_disp).value
        size = sheet.cell(row=r, column=c_size).value
        code = sheet.cell(row=r, column=c_code).value
        price = clean_price(sheet.cell(row=r, column=c_price).value)
        promo = str(sheet.cell(row=r, column=c_promo).value or "").strip()
        cashback = clean_price(sheet.cell(row=r, column=c_cashback).value)
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
        
        # Cross-validation: Check if model code explicitly contains a conflicting screen size
        # e.g. target_size=55 but code is QE100QN80H -> extracted code size is 100 != 55 -> reject
        m_code_sz = re.search(r'(?:^|[A-Z]{1,3})(\d{2,3})(?:[A-Z]|$)', code)
        if m_code_sz:
            c_sz = int(m_code_sz.group(1))
            if c_sz in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
                if target_size in [85, 86] and c_sz in [85, 86]:
                    pass # Valid flagship pair match
                elif c_sz != target_size:
                    continue # Reject conflicting model size
        
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
        elif series_upper in ["QNED71B", "QNED71"]:
            match = "QNED71" in code
        elif series_upper in ["QNED70A", "QNED70B", "QNED70"]:
            match = any(x in code for x in ["QNED70", "QNED72", "QNED7E"])
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
        elif series_upper in ["NU800", "NU800B", "NU80", "NU8E", "NU85"]:
            match = any(x in code for x in ["NU800", "NU80", "NU8E", "NU85", "NU75", "UA77", "UT", "UR", "UQ"])
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
        elif series_upper in ["MRGB95B", "MRGB96B", "MRGB96", "MRGB95", "MRGB9"]: match = any(x in code for x in ["MRGB96", "MRGB95", "MRGB9", "MR95", "MR96"])
        elif series_upper in ["MRGB87B", "MRGB87", "MRGB88B", "MRGB88", "MRGB86B", "MRGB86", "MRGB85", "MRGB8"]: match = any(x in code for x in ["MRGB88", "MRGB87", "MRGB86", "MRGB85", "MRGB8", "MR85"])
        elif series_upper in ["R95H", "R95"]: match = bool(re.search(r'(?:R95|MR95)', code))
        elif series_upper in ["R86H", "R86", "R85H", "R85"]: match = bool(re.search(r'(?:R86|R85)', code)) and not bool(re.search(r'(?:R95|MR95)', code))
        
        if match:
            matched_candidates.append(p)
            
    if not matched_candidates:
        return None
        
    # Priority sorting:
    # 1. Official European/Italian OLED sub-models (e.g. G56, G66, C55, C65, B65)
    # 2. True U8000 series (U8000, U8005, U8070) over U7000 fallback
    # 3. Prefer model codes matching target size exactly
    def get_priority(item):
        code = item["model_code"].upper()
        prio = 0
        m_c_sz = re.search(r'(?:^|[A-Z]{1,3})(\d{2,3})(?:[A-Z]|$)', code)
        if m_c_sz:
            c_sz = int(m_c_sz.group(1))
            if target_size in [85, 86] and c_sz in [85, 86]:
                pass
            elif c_sz != target_size:
                prio += 10
        if any(x in code for x in ["G56", "G66", "C55", "C65", "B65", "B55"]):
            return prio + 0
        if any(x in code for x in ["U8000", "U8005", "U8010", "U8070", "U8075", "U8090"]):
            return prio + 1
        if "U7000" in code:
            return prio + 2
        return prio + 3
        
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
        seen_pair_labels = set()
        for pair in series_list:
            lg_series = pair["lg"]
            sam_series = pair["sam"]
            
            for size in pair["sizes"]:
                sam_sz_lbl = "85" if str(size) in ["86", "85"] and any(x in sam_series for x in ["R85", "R86", "R95", "QN", "Q", "M7", "M8", "U8"]) else str(size)
                lg_sz_lbl = "86" if str(size) in ["86", "85"] and ("MRGB" in lg_series or "QNED" in lg_series) else str(size)

                pair_label_str = f"{lg_sz_lbl}\"{lg_series} vs. {sam_sz_lbl}\"{sam_series}"
                if "U8000" in sam_series:
                    pair_label_str = f"{lg_sz_lbl}\"{lg_series} vs. {sam_sz_lbl}\"U8070H"
                if ("MRGB96" in lg_series or "MRGB95" in lg_series) and str(size) in ["86", "85"]:
                    pair_label_str = f'86"{lg_series} vs. 85"R95H'
                elif ("MRGB88" in lg_series or "MRGB87" in lg_series or "MRGB86" in lg_series or "MRGB85" in lg_series) and str(size) in ["86", "85"]:
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
                    
                if pair_label_str in seen_pair_labels:
                    continue
                seen_pair_labels.add(pair_label_str)
                
                entry = {
                    "size": int(size),
                    "lg_series": f"{lg_sz_lbl}{lg_series}",
                    "sam_series": f"{sam_sz_lbl}{sam_series}",
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

def get_country_pair_configs(country):
    if country == "IT": cfg_2026 = PAIRS_CONFIG_2026_IT
    elif country == "UK": cfg_2026 = PAIRS_CONFIG_2026_UK
    elif country == "NL": cfg_2026 = PAIRS_CONFIG_2026_NL
    elif country == "ES": cfg_2026 = PAIRS_CONFIG_2026_ES
    elif country == "DE": cfg_2026 = PAIRS_CONFIG_2026_DE
    elif country == "AT": cfg_2026 = PAIRS_CONFIG_2026_AT
    elif country == "CH": cfg_2026 = PAIRS_CONFIG_2026_CH
    elif country == "CZ": cfg_2026 = PAIRS_CONFIG_2026_CZ
    elif country == "GR": cfg_2026 = PAIRS_CONFIG_2026_GR
    elif country == "FR": cfg_2026 = PAIRS_CONFIG_2026_FR
    elif country == "HU": cfg_2026 = PAIRS_CONFIG_2026_HU
    else: cfg_2026 = PAIRS_CONFIG_2026

    if country == "NL": cfg_2025 = PAIRS_CONFIG_2025_NL
    elif country == "ES": cfg_2025 = PAIRS_CONFIG_2025_ES
    elif country == "DE": cfg_2025 = PAIRS_CONFIG_2025_DE
    elif country == "FR": cfg_2025 = PAIRS_CONFIG_2025_FR
    elif country == "HU": cfg_2025 = PAIRS_CONFIG_2025_HU
    elif country == "CH": cfg_2025 = PAIRS_CONFIG_2025_CH
    else: cfg_2025 = PAIRS_CONFIG_2025

    return cfg_2025, cfg_2026

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
                
                cfg_2025, cfg_2026 = get_country_pair_configs(country)
                for year, config in [("2025", cfg_2025), ("2026", cfg_2026)]:
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
            
    # Prune series that have no recorded prices across all dates to optimize dashboard size
    pruned_data = {}
    for country, c_data in historical_data.items():
        pruned_data[country] = {}
        for yr, yr_data in c_data.items():
            pruned_data[country][yr] = {}
            for s_key, s_entry in yr_data.items():
                has_nonzero = False
                for h in s_entry.get("history", []):
                    for k, v in h.items():
                        if k != "date" and isinstance(v, (int, float)) and v > 0:
                            has_nonzero = True
                            break
                    if has_nonzero:
                        break
                if has_nonzero:
                    pruned_data[country][yr][s_key] = s_entry
                    
    return pruned_data

def check_is_benchmark(country, brand, year, size, model_code, title):
    cfg_2025, cfg_2026 = get_country_pair_configs(country)
    cfg = cfg_2026 if year == 2026 else cfg_2025
    b_up = str(brand).upper()
    mc_up = str(model_code).upper()
    t_up = str(title).upper()
    
    for cat, pair_list in cfg.items():
        for pair in pair_list:
            if str(size) in [str(s) for s in pair.get("sizes", [])]:
                target_series = pair["lg"] if b_up == "LG" else pair["sam"]
                if target_series.upper() in mc_up or target_series.upper() in t_up:
                    return True
    return False

def load_workbook_catalog(wb_path):
    if not os.path.exists(wb_path):
        return {}
    wb = openpyxl.load_workbook(wb_path, data_only=True)
    catalog = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        
        country = 'DE'
        retailer = 'MediaMarkt'
        brand = 'SAMSUNG' if 'SAMSUNG' in sheet_name.upper() else ('LG' if 'LG' in sheet_name.upper() else 'TV')
        
        if 'HU' in sheet_name: country = 'HU'; retailer = 'MediaMarkt'
        elif 'CZ' in sheet_name: country = 'CZ'; retailer = 'Alza'
        elif 'GR' in sheet_name: country = 'GR'; retailer = 'Public'
        elif 'DE' in sheet_name: country = 'DE'; retailer = 'MediaMarkt'
        elif 'AT' in sheet_name: country = 'AT'; retailer = 'MediaMarkt'
        elif 'CH' in sheet_name: country = 'CH'; retailer = 'MediaMarkt'
        elif 'ES' in sheet_name: country = 'ES'; retailer = 'MediaMarkt'
        elif 'NL' in sheet_name: country = 'NL'; retailer = 'MediaMarkt'
        elif 'UK' in sheet_name: country = 'UK'; retailer = 'Currys'
        elif 'FR' in sheet_name: country = 'FR'; retailer = 'Fnac'
        elif 'IT' in sheet_name: country = 'IT'; retailer = 'MediaWorld'
        
        if country not in EU_COUNTRIES:
            continue
            
        headers = [str(ws.cell(row=1, column=c).value or '').lower() for c in range(1, ws.max_column + 1)]
        
        code_col, year_col, size_col, price_col, cb_col, promo_col, title_col, disp_col = 5, 2, 4, 6, 9, 10, 13, 3
        for idx, h in enumerate(headers):
            if any(x in h for x in ['model code', 'code', 'modell']) and not ('was' in h or 'strike' in h):
                code_col = idx + 1
            elif any(x in h for x in ['year', 'jahr', 'ev']): year_col = idx + 1
            elif any(x in h for x in ['display', 'panel', 'type', 'kijelzo']): disp_col = idx + 1
            elif any(x in h for x in ['size', 'zoll', 'inch']): size_col = idx + 1
            elif any(x in h for x in ['selling price', 'price']) and not ('was' in h or 'strike' in h or 'original' in h or 'eur' in h and 'huf' in ''.join(headers)):
                price_col = idx + 1
            elif any(x in h for x in ['cashback', 'cb']): cb_col = idx + 1
            elif any(x in h for x in ['promotion', 'promo', 'general']): promo_col = idx + 1
            elif any(x in h for x in ['title', 'name', 'product', 'termek']): title_col = idx + 1
            
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
                
            curr = COUNTRY_CURRENCIES.get(country, 'EUR')
            sym = CURRENCY_SYMBOLS.get(curr, '€')
            
            key = f'{country}_{retailer}_{c_brand}_{c_code}'.upper()
            catalog[key] = {
                'country': country,
                'retailer': retailer,
                'brand': 'LG' if 'LG' in str(c_brand).upper() else 'SAMSUNG',
                'year': int(c_year) if c_year and str(c_year).isdigit() else 2025,
                'display': str(c_disp or 'LED').strip(),
                'size': int(c_size) if c_size and str(c_size).isdigit() else 55,
                'model_code': c_code,
                'currency': curr,
                'currency_sym': sym,
                'price': price_val,
                'cashback': cb_val,
                'net_price': max(0.0, price_val - cb_val),
                'promo': str(c_promo).strip(),
                'title': str(c_title or c_code).strip()
            }
    wb.close()
    return catalog

def compute_weekly_changes():
    print("[PARSING WEEKLY CHANGES] Analyzing week-over-week changes (W31, W32, W33, W34)...")
    w30_path = os.path.join(history_dir, "2026 0726", "price tracker_EU_2026 0726_v1.xlsx")
    w31_path = os.path.join(history_dir, "2026 0728", "price tracker_EU_2026 0728_v1.xlsx")
    w32_path = os.path.join(history_dir, "2026 0806", "price tracker_EU_2026 0806_v1.xlsx")
    
    w33_path = os.path.join(history_dir, "2026 0814", "price tracker_EU_2026 0814_v1_temp.xlsx")
    if not os.path.exists(w33_path):
        w33_path = os.path.join(history_dir, "2026 0814", "price tracker_EU_2026 0814_v1.xlsx")
    if not os.path.exists(w33_path):
        w33_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_EU_2026 0814*.xlsx")))
        if w33_cands: w33_path = w33_cands[-1]

    w34_path = os.path.join(history_dir, "2026 0817", "price tracker_EU_2026 0817_v1.xlsx")
    if not os.path.exists(w34_path):
        w34_path = os.path.join(data_dir, "price tracker_EU_2026 0817_v1.xlsx")
    if not os.path.exists(w34_path):
        w34_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_EU_2026 0817*.xlsx")))
        if w34_cands: w34_path = w34_cands[-1]

    w35_path = os.path.join(history_dir, "2026 0828", "price tracker_EU_2026 0828_v1.xlsx")
    if not os.path.exists(w35_path):
        w35_path = os.path.join(data_dir, "price tracker_EU_2026 0828_v1.xlsx")
    if not os.path.exists(w35_path):
        w35_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_EU_2026 0828*.xlsx")))
        if w35_cands: w35_path = w35_cands[-1]

    w36_path = os.path.join(history_dir, "2026 0903", "price tracker_EU_2026 0903_v1.xlsx")
    if not os.path.exists(w36_path):
        w36_path = os.path.join(history_dir, "2026 0901", "price tracker_EU_2026 0901_v1.xlsx")
    if not os.path.exists(w36_path):
        w36_path = os.path.join(data_dir, "price tracker_EU_2026 0903_v1.xlsx")
    if not os.path.exists(w36_path):
        w36_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_EU_2026 0903*.xlsx")))
        if w36_cands: w36_path = w36_cands[-1]

    w37_path = os.path.join(history_dir, "2026 0907", "price tracker_EU_2026 0907_v1.xlsx")
    if not os.path.exists(w37_path):
        w37_path = os.path.join(data_dir, "price tracker_EU_2026 0907_v1.xlsx")
    if not os.path.exists(w37_path):
        w37_cands = sorted(glob.glob(os.path.join(data_dir, "price tracker_EU_2026 0907*.xlsx")))
        if w37_cands: w37_path = w37_cands[-1]
    
    cat_w30 = load_workbook_catalog(w30_path)
    cat_w31 = load_workbook_catalog(w31_path)
    cat_w32 = load_workbook_catalog(w32_path)
    cat_w33 = load_workbook_catalog(w33_path)
    cat_w34 = load_workbook_catalog(w34_path)
    cat_w35 = load_workbook_catalog(w35_path)
    cat_w36 = load_workbook_catalog(w36_path)
    cat_w37 = load_workbook_catalog(w37_path)
    
    transitions = [
        ("W37", "W37(09.07) vs W36(09.03)", "2026.09.07", "2026.09.03", cat_w36, cat_w37),
        ("W36", "W36(09.03) vs W35(08.28)", "2026.09.03", "2026.08.28", cat_w35, cat_w36),
        ("W35", "W35(08.28) vs W34(08.17)", "2026.08.28", "2026.08.17", cat_w34, cat_w35),
        ("W34", "W34(08.17) vs W33(08.14)", "2026.08.17", "2026.08.14", cat_w33, cat_w34),
        ("W33", "W33(08.14) vs W32(08.06)", "2026.08.14", "2026.08.06", cat_w32, cat_w33),
        ("W32", "W32(08.06) vs W31(07.28)", "2026.08.06", "2026.07.28", cat_w31, cat_w32),
        ("W31", "W31(07.28) vs W30(07.26)", "2026.07.28", "2026.07.26", cat_w30, cat_w31)
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
        
        country_stats = {c: {"drops": 0, "hikes": 0, "promos": 0, "news": 0, "delisted": 0} for c in EU_COUNTRIES}
        
        for key, curr_item in curr_cat.items():
            if curr_item.get("year") != 2026:
                continue
                
            country = curr_item["country"]
            brand = curr_item["brand"]
            retailer = curr_item["retailer"]
            year = curr_item["year"]
            size = curr_item["size"]
            model_code = curr_item["model_code"]
            display = curr_item["display"]
            title = curr_item["title"]
            currency = curr_item["currency"]
            currency_sym = curr_item["currency_sym"]
            
            is_bm = check_is_benchmark(country, brand, year, size, model_code, title)
            
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
                    if country in country_stats: country_stats[country]["drops"] += 1
                elif p_diff > 0.5:
                    tags.append("PRICE_HIKE")
                    price_hikes += 1
                    hike_pcts.append(abs(p_diff_pct))
                    if country in country_stats: country_stats[country]["hikes"] += 1
                    
                promo_changed = False
                if promo_curr != promo_prev:
                    promo_changed = True
                    if promo_prev in ["None", "", "-"] and promo_curr not in ["None", "", "-"]:
                        tags.append("PROMO_NEW")
                    elif promo_prev not in ["None", "", "-"] and promo_curr in ["None", "", "-"]:
                        tags.append("PROMO_ENDED")
                    else:
                        tags.append("PROMO_CHANGED")
                        
                if cb_curr != cb_prev:
                    promo_changed = True
                    tags.append("CASHBACK_CHANGED")
                    
                if promo_changed:
                    promo_changes += 1
                    if country in country_stats: country_stats[country]["promos"] += 1
                    
                if tags:
                    items.append({
                        "key": key,
                        "country": country,
                        "retailer": retailer,
                        "brand": brand,
                        "year": year,
                        "display": display,
                        "size": size,
                        "model_code": model_code,
                        "title": title,
                        "currency": currency,
                        "currency_sym": currency_sym,
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
                if country in country_stats: country_stats[country]["news"] += 1
                items.append({
                    "key": key,
                    "country": country,
                    "retailer": retailer,
                    "brand": brand,
                    "year": year,
                    "display": display,
                    "size": size,
                    "model_code": model_code,
                    "title": title,
                    "currency": currency,
                    "currency_sym": currency_sym,
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
                country = prev_item["country"]
                brand = prev_item["brand"]
                retailer = prev_item["retailer"]
                year = prev_item["year"]
                size = prev_item["size"]
                model_code = prev_item["model_code"]
                display = prev_item["display"]
                title = prev_item["title"]
                currency = prev_item["currency"]
                currency_sym = prev_item["currency_sym"]
                
                is_bm = check_is_benchmark(country, brand, year, size, model_code, title)
                
                delisted_models += 1
                if country in country_stats: country_stats[country]["delisted"] += 1
                items.append({
                    "key": key,
                    "country": country,
                    "retailer": retailer,
                    "brand": brand,
                    "year": year,
                    "display": display,
                    "size": size,
                    "model_code": model_code,
                    "title": title,
                    "currency": currency,
                    "currency_sym": currency_sym,
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
            "country_stats": country_stats,
            "items": items
        }
        print(f"  ➔ [WEEKLY CHANGES] {week_key}: {len(items)} change items (Drops: {price_drops}, Hikes: {price_hikes}, Promos: {promo_changes}, New: {new_models})")
        
    return weekly_changes_data

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
        cfg_2025, cfg_2026 = get_country_pair_configs(country)
        price_data[country] = {
            "2025": build_paired_data(wb, country, 2025, cfg_2025),
            "2026": build_paired_data(wb, country, 2026, cfg_2026)
        }
    wb.close()
    
    print("[PARSING HISTORY] Scanning all historical survey folders...")
    history_data = scan_history_data()
    price_data["history"] = history_data
    
    weekly_changes_data = compute_weekly_changes()
    price_data["weekly_changes"] = weekly_changes_data
    
    if not os.path.exists(template_path):
        print(f"[ERROR] HTML base template not found: {template_path}")
        return
        
    print(f"[COMPILING DASHBOARD] Running DataIntelligenceEngine and preparing executive data...")
    exec_summary_json = "{}"
    try:
        from scripts.data_intelligence_engine import DataIntelligenceEngine
        now_dt = datetime.now()
        intel_engine = DataIntelligenceEngine(target_date=now_dt.strftime("%Y-%m-%d"))
        md_report_path = intel_engine.generate_executive_briefing_report()
        exec_json_path = intel_engine.export_dashboard_summary_json()
        with open(exec_json_path, "r", encoding="utf-8") as f_ex:
            exec_summary_json = f_ex.read()
        print(f"  ➔ [INTEL] Executive briefing report and structured JSON generated.")
        
        # Mirror report to public_eu/reports/
        public_reports_dir = os.path.join(root_dir, "public_eu", "reports")
        os.makedirs(public_reports_dir, exist_ok=True)
        shutil.copy2(md_report_path, os.path.join(public_reports_dir, os.path.basename(md_report_path)))
    except Exception as e_intel:
        print(f"  ➔ [WARN] Could not run DataIntelligenceEngine: {e_intel}")

    print(f"[COMPILING DASHBOARD] Injecting JSON data and survey dates into template...")
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    json_str = json.dumps(price_data, separators=(',', ':'), ensure_ascii=False)
    injection_block = f"const priceData = {json_str};\n        const executiveSummaryData = {exec_summary_json};"
    
    now_dt = datetime.now()
    week_no = now_dt.isocalendar()[1]
    survey_date = now_dt.strftime(f"%Y년 %m월 %d일 (W{week_no})")
    survey_date_dot = now_dt.strftime(f"%Y.%m.%d(W{week_no})")
    
    compiled_html = html_content.replace("// {{INSERT_PRICE_DATA}}", injection_block)
    compiled_html = compiled_html.replace("{{SURVEY_DATE}}", survey_date)
    compiled_html = compiled_html.replace("{{SURVEY_DATE_DOT}}", survey_date_dot)
    
    with open(workspace_dashboard_path, "w", encoding="utf-8") as f:
        f.write(compiled_html)
    print(f"  ➔ [SAVED] Compiled HTML saved to Workspace: {workspace_dashboard_path}")
    
    if artifact_dashboard_path:
        try:
            os.makedirs(os.path.dirname(artifact_dashboard_path), exist_ok=True)
            with open(artifact_dashboard_path, "w", encoding="utf-8") as f:
                f.write(compiled_html)
            print(f"  ➔ [SAVED] Compiled HTML saved to Artifact: {artifact_dashboard_path}")
        except Exception as e_art:
            print(f"  ➔ [WARN] Could not write to artifact: {e_art}")
    
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
