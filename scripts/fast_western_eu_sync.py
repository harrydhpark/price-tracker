# -*- coding: utf-8 -*-
"""
Fast Western Europe (DE, AT, ES, NL, IT) Sync from Playwright MCP Dump
"""

import os
import sys
import json
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

DISCARD_KEYWORDS = [
    'RATEN', 'RATE', 'MONAT', 'MESES', 'MES', 'FINANZIERUNG', 'FINANCIACIÓN', 'FINANZIAMENTO',
    'CUOTAS', 'CUOTA', 'TAEG', 'RATES', 'SPARE', 'REFURBISHED', 'ANGEBOTE AB', 'CASHBACK',
    'REEMBOLSO', 'RIMBORSO', 'SCONTO', 'RETOUR', 'PAKKET', 'BUNDEL', 'GUTSCHEIN', 'ABZUG',
    'VORTEIL', 'VOORDEEL', 'REMISE', 'RABAIS', 'BONUS', 'ODR', 'ÉCONOMIE', 'ECONOMIE',
    'RÉDUCTION', 'REDUCCIÓN', 'PROMO', 'DESCUENTO', 'CODE'
]

TAX_KEYWORDS = ['INCL. BTW', 'INKL. MWST', 'IVA INCL', 'IVA INCLUSA', 'TVA INCLUSE']

NON_TV_KEYWORDS = [
    "MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", 
    "BEAMER", "PROJEKTOR", "WASCHMASCHINE", "HALTERUNG", "WANDHALTERUNG", 
    "SUBWOOFER", "AIRPODS", "KOPFHÖRER", "KOPFHORER", "HEADPHONES", 
    "EARPHONES", "CASE", "LADECASE", "FERNBEDIENUNG", "KABEL", "CABLE",
    "STANDVOET", "STANDFUSS", "STANDFUß", "PEDESTAL", "BEVESTIGING", "ADAPTER",
    "VOET", "SUPPORT", "ACCESSORY", "ACCESSOIRE", "BEUGEL", "WANDBEUGEL",
    "MUURBEUGEL", "SUPPORT MURAL", "PIED", "STAFF", "STAFFA",
    "PHILIPS", "SONY", "TCL", "HISENSE", "PANASONIC", "APPLE", "XIAOMI", "PUS",
    "GALAXY S2", "SMARTPHONE", "TABLET"
]

def check_price_floor(price, size, disp):
    if price < 50.0:
        return False
    if disp == "OLED":
        if size >= 83 and price < 1800.0: return False
        if size >= 77 and price < 1300.0: return False
        if size >= 70 and price < 1100.0: return False
        if size >= 65 and price < 850.0: return False
        if size >= 55 and price < 650.0: return False
        if size in [42, 48] and price < 500.0: return False
        if price < 400.0: return False
    elif disp == "Micro RGB":
        if size >= 75 and price < 1200.0: return False
        if size >= 50 and price < 600.0: return False
        if price < 500.0: return False
    elif disp in ["QNED", "QLED"]:
        if size >= 75 and price < 600.0: return False
        if size >= 65 and price < 450.0: return False
        if size >= 50 and price < 280.0: return False
        if size >= 43 and price < 200.0: return False
        if price < 150.0: return False
    else: # UHD 4K
        if size >= 70 and price < 450.0: return False
        if size >= 55 and price < 180.0: return False
        if size >= 43 and price < 120.0: return False
        if price < 80.0: return False
    return True

def parse_price_str(raw):
    c = raw.replace('–', '00').replace('-', '00').replace('\xa0', ' ').replace('\u202f', ' ').strip()
    m = re.search(r'(?:€|£)\s*(\d+[\d\s\.,]*)|(\d+[\d\s\.,]*)\s*(?:€|£)', c)
    if not m:
        return 0.0
    num = (m.group(1) or m.group(2)).replace(' ', '').replace('.', '').replace(',', '.')
    try:
        val = float(num)
        return val if val >= 50.0 else 0.0
    except ValueError:
        return 0.0

def parse_card_prices(card_text):
    lines = [l.strip() for l in card_text.split('\n') if l.strip()]
    
    orig_price = 0.0
    selling_price = 0.0
    
    # 1. Check for UVP / original price line
    for l in lines:
        if any(x in l.upper() for x in ['UVP', 'WAS', 'PREZZO CONSIGLIATO', 'ADVIESPRIJS']):
            p = parse_price_str(l)
            if p >= 100.0:
                orig_price = p
                break

    # 2. Look for tax line to anchor selling price
    for i, l in enumerate(lines):
        if any(tk in l.upper() for tk in TAX_KEYWORDS):
            prices_found = []
            for prev_idx in range(i - 1, max(-1, i - 8), -1):
                prev_line = lines[prev_idx]
                if any(dk in prev_line.upper() for dk in DISCARD_KEYWORDS):
                    continue
                p = parse_price_str(prev_line)
                if p >= 100.0 and p not in prices_found:
                    prices_found.append(p)
            if prices_found:
                selling_price = prices_found[0]
                if len(prices_found) > 1 and orig_price == 0.0:
                    orig_price = max(prices_found)
                break
                
    # 3. Fallback: clean lines from bottom up
    if not selling_price:
        clean_lines = []
        for l in lines:
            if any(dk in l.upper() for dk in DISCARD_KEYWORDS):
                continue
            if any(uk in l.upper() for uk in ['UVP', 'WAS', 'PREZZO CONSIGLIATO', 'ADVIESPRIJS']):
                continue
            clean_lines.append(l)
        for l in reversed(clean_lines):
            p = parse_price_str(l)
            if p >= 100.0:
                selling_price = p
                break
                
    return selling_price, orig_price or selling_price

def extract_promo(card_text):
    upper = card_text.upper()
    m_pct = re.search(r'(-\d+%)', card_text)
    pct_str = m_pct.group(1) if m_pct else ""
    
    if "VUELTA AL COLE" in upper:
        return f"Vuelta al cole ({pct_str})" if pct_str else "Vuelta al cole"
    elif "BUNDELVOORDEEL" in upper:
        return "Bundelvoordeel"
    elif "RETOUR" in upper:
        m_cb = re.search(r'(?:€|£)?\s*(\d+)\s*retour', card_text, re.IGNORECASE)
        return f"Cashback €{m_cb.group(1)}" if m_cb else "Cashback"
    elif pct_str:
        return f"Discount {pct_str}"
    return "None"

def extract_model_and_meta(card_text, brand):
    upper = card_text.upper()
    
    # Strict brand verification
    if brand.upper() not in upper:
        return None, 0, 0, ""
        
    # Exclude non-TVs
    if any(x in upper for x in NON_TV_KEYWORDS):
        return None, 0, 0, ""
        
    # Size
    size_m = re.search(r'\b(98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:ZOLL|INCH|POUCES|POLLICI|CM|\b)', upper)
    size = int(size_m.group(1)) if size_m else 55
    
    # Model code
    model_code = "Unknown"
    code_m = re.search(r'\b([A-Z0-9]{2}\d{2}[A-Z0-9]{3,10}|\d{2}[A-Z]{3,6}\d{2}[A-Z0-9]{2,6}|OLED\d{2}[A-Z0-9]{2,6}|MRE\d{2}[A-Z0-9]{2,6})\b', upper)
    if code_m:
        model_code = code_m.group(1)
        
    if brand.upper() == "SAMSUNG":
        if model_code == "Unknown" or len(model_code) < 5 or model_code.startswith("PUS"):
            m_series = re.search(r'\b(S9\d[FH]|QN\d{2,3}[FH]|M\d{2}[FH]|R\d{2}[FH]|U\d{4}[FH]|LS03[FH]|Q\d[FH])\b', upper)
            if m_series:
                series = m_series.group(1)
                prefix = "QE" if series.startswith(("S", "QN", "Q")) else ("UE" if series.startswith(("M", "U")) else "MRE")
                model_code = f"{prefix}{size}{series}"
            else:
                return None, 0, 0, ""
    elif brand.upper() == "LG":
        if model_code == "Unknown" or not any(x in model_code for x in ["QNED", "OLED", "MRGB", "NANO", "LX", "NU", "UA", "UT", "UR", "UQ", "LB", "STANBYME"]):
            if "STANBYME" in upper or "27LX6" in upper:
                model_code = "27LX6TDGA"
                size = 27
            elif "QNED86B" in upper: model_code = f"{size}QNED86B"
            elif "QNED81B" in upper: model_code = f"{size}QNED81B"
            elif "QNED80B" in upper: model_code = f"{size}QNED80B"
            elif "QNED72B" in upper: model_code = f"{size}QNED72B"
            elif "QNED71B" in upper: model_code = f"{size}QNED71B"
            elif "QNED70B" in upper: model_code = f"{size}QNED70B"
            elif "QNED86A" in upper: model_code = f"{size}QNED86A"
            elif "QNED80A" in upper: model_code = f"{size}QNED80A"
            elif "QNED72A" in upper: model_code = f"{size}QNED72A"
            elif "QNED70A" in upper: model_code = f"{size}QNED70A"
            elif "MRGB87B" in upper: model_code = f"{size}MRGB87B"
            elif "MRGB96B" in upper: model_code = f"{size}MRGB96B"
            elif "MRGB87A" in upper: model_code = f"{size}MRGB87A"
            else:
                return None, 0, 0, ""
            
    # Year
    year = 2025
    if any(x in upper for x in ["2026", "B6", "C6", "G6", "R85H", "R95H", "S90H", "S92H", "S95H", "S99H", "QN82H", "M72H", "M82H", "R86H", "U8070H", "QNED86B", "QNED81B", "QNED80B", "QNED87B", "QNED72B", "QNED71B", "QNED70B", "27LX6", "STANBYME 2", "U8090H", "M70H"]):
        year = 2026
    elif any(x in upper for x in ["2025", "B5", "C5", "G5", "S90F", "S92F", "S95F", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED70A"]):
        year = 2025
    elif any(x in upper for x in ["2024", "B4", "C4", "G4", "S90D"]):
        year = 2024
        
    # Strict Display Type Disambiguation
    if "MRGB" in upper or "MICRO RGB" in upper or "R85" in upper or "R95" in upper:
        display = "Micro RGB"
    elif "QNED" in upper:
        display = "QNED"
    elif "OLED" in upper:
        display = "OLED"
    elif "QLED" in upper or "NEO QLED" in upper or any(k in upper for k in ["LS03", "QN8", "QN9", "QN7"]):
        display = "QLED"
    else:
        display = "UHD 4K"
        
    return model_code, size, year, display

def process_dump_content(content, default_country=None):
    if content.startswith("### Result"):
        content = content[len("### Result"):].strip()
    idx = content.find("### Ran Playwright code")
    if idx != -1:
        content = content[:idx].strip()
        
    raw_data = json.loads(content)
    if "country" in raw_data:
        country_key = raw_data["country"]
        brands_data = raw_data.get("data", {})
        all_data = {country_key: brands_data}
    elif default_country:
        brands_data = raw_data.get("data", raw_data)
        all_data = {default_country: brands_data}
    elif "data" in raw_data and isinstance(raw_data["data"], dict) and any(k in raw_data["data"] for k in ["samsung", "lg"]):
        all_data = {"single": raw_data["data"]}
    else:
        all_data = raw_data.get("data", {})
        if not all_data and any(k in raw_data for k in ["samsung", "lg"]):
            all_data = {"single": raw_data}
            
    for country_key, brands_data in all_data.items():
        samsungs_raw = brands_data.get("samsung", [])
        lgs_raw = brands_data.get("lg", [])
        
        samsungs = []
        seen_s = {}
        for item in samsungs_raw:
            card_text = item.get("cardText", "") or item.get("text", "")
            href = item.get("href", "")
            sp, op = parse_card_prices(card_text)
            if sp < 80.0:
                continue
            m_code, size, year, disp = extract_model_and_meta(card_text, "Samsung")
            if not m_code or m_code == "Unknown" or size < 22 or year not in [2025, 2026]:
                continue
            if not check_price_floor(sp, size, disp):
                continue
                
            # Find best title line
            lines = [l.strip() for l in card_text.split('\n') if l.strip()]
            title = ""
            for l in lines:
                if "SAMSUNG" in l.upper() and len(l) > 15:
                    title = l
                    break
            if not title:
                title = lines[0][:80]
                
            rec = {
                "brand": "Samsung",
                "year": year,
                "display": disp,
                "size": size,
                "model_code": m_code,
                "price": sp,
                "orig_price": op,
                "shipping": "Free",
                "cashback": 0,
                "promo": extract_promo(card_text),
                "title": title,
                "link": href
            }
            if m_code not in seen_s or sp < seen_s[m_code]["price"]:
                seen_s[m_code] = rec
        samsungs = list(seen_s.values())
        
        lgs = []
        seen_l = {}
        for item in lgs_raw:
            card_text = item.get("cardText", "") or item.get("text", "")
            href = item.get("href", "")
            sp, op = parse_card_prices(card_text)
            if sp < 80.0:
                continue
            m_code, size, year, disp = extract_model_and_meta(card_text, "LG")
            if not m_code or m_code == "Unknown" or size < 22 or year not in [2025, 2026]:
                continue
            if not check_price_floor(sp, size, disp):
                continue
                
            # Find best title line
            lines = [l.strip() for l in card_text.split('\n') if l.strip()]
            title = ""
            for l in lines:
                if "LG" in l.upper() and len(l) > 15:
                    title = l
                    break
            if not title:
                title = lines[0][:80]
                
            rec = {
                "brand": "LG",
                "year": year,
                "display": disp,
                "size": size,
                "model_code": m_code,
                "price": sp,
                "orig_price": op,
                "shipping": "Free",
                "cashback": 0,
                "promo": extract_promo(card_text),
                "title": title,
                "link": href
            }
            if m_code not in seen_l or sp < seen_l[m_code]["price"]:
                seen_l[m_code] = rec
        lgs = list(seen_l.values())
        
        print(f"[{country_key}] Parsed {len(samsungs)} Samsung and {len(lgs)} LG live products.")
        
        s_file = os.path.join(DATA_DIR, f"raw_{country_key}_samsung.json")
        l_file = os.path.join(DATA_DIR, f"raw_{country_key}_lg.json")
        
        if samsungs:
            with open(s_file, "w", encoding="utf-8") as f:
                json.dump(samsungs, f, ensure_ascii=False, indent=2)
            print(f"  -> Wrote {len(samsungs)} to {s_file}")
        if lgs:
            with open(l_file, "w", encoding="utf-8") as f:
                json.dump(lgs, f, ensure_ascii=False, indent=2)
            print(f"  -> Wrote {len(lgs)} to {l_file}")

def sync_all_western_dumps():
    dumps = [
        (r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\2074\output.txt", "mm-de"),
        (r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\2056\output.txt", "mm-at"),
        (r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\2010\output.txt", "mm-es"),
        (r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\scratch\nl_merged.json", "mm-nl"),
        (r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\2048\output.txt", "mw-it"),
    ]
    for p, c_name in dumps:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if '"country":' not in content:
                content = content.replace('"data":', f'"country": "{c_name}", "data":')
            process_dump_content(content, default_country=c_name)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            process_dump_content(f.read())
    else:
        sync_all_western_dumps()

