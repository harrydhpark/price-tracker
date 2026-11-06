# -*- coding: utf-8 -*-
"""
MediaExpert Poland (mediaexpert.pl) Scraper & Normalizer
Extracts Samsung & LG TV products from Poland, enforcing strict 2025/2026 model year classification,
extracting Polish PLN prices, promo codes, and writing clean JSON datasets.
"""

import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

NON_TV_KEYWORDS = [
    "SOUNDBAR", "SOUND BAR", "UCHWYT", "WIESZAK", "KABEL", "PILOT",
    "MONITOR", "ODYSSEY", "ULTRAGEAR", "ZESTAW", "PROJEKTOR", "TURYS"
]

def parse_mediaexpert_product(raw_item, brand):
    title = raw_item.get("title", "").strip()
    u_title = title.upper()
    url = raw_item.get("url", "").strip()
    price = float(raw_item.get("price", 0.0))
    orig_price = float(raw_item.get("original_price", price))
    promo = raw_item.get("promo", "None")

    if any(k in u_title for k in NON_TV_KEYWORDS):
        return None
    # Fix regex bug if price was glued with date/code: e.g. 3009261999 -> 1999
    if price > 500000.0:
        p_str = str(int(price))
        p_cand = float(p_str[-4:])
        if p_cand >= 500:
            price = p_cand
    if price < 500.0:
        return None

    # 1. Screen size
    size = 0
    m_sz = re.search(r'(\d{2,3})[\s"”\'-]*(?:CALI|CAL|\"|”|\b)', u_title)
    if m_sz:
        c_sz = int(m_sz.group(1))
        if c_sz in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
            size = c_sz
    if not size or size < 22:
        return None

    # 2. Model Code Extraction
    model_code = "Unknown"
    if brand.upper() == "SAMSUNG":
        # Check standard prefixes
        m_mc = re.search(r'\b((?:QE|UE|GQ|TQ|MRE)\d{2,3}[A-Z0-9]+)\b', u_title)
        if m_mc:
            model_code = m_mc.group(1)
        else:
            patterns = [
                r'\b(QN\d{2,3}[FH])\b', r'\b(S\d{2}[FH])\b', r'\b(U\d{4}[FH])\b',
                r'\b(M\d{2}[FH])\b', r'\b(R\d{2}[FH])\b', r'\b(LS03[A-Z]{1,2})\b',
                r'\b(Q\d[FH]\d?)\b'
            ]
            for pat in patterns:
                m = re.search(pat, u_title)
                if m:
                    ser = m.group(1)
                    if ser.startswith('S') or ser.startswith('QN') or ser.startswith('LS') or ser.startswith('Q'):
                        model_code = f"QE{size}{ser}"
                    elif ser.startswith('U') or ser.startswith('M'):
                        model_code = f"UE{size}{ser}"
                    elif ser.startswith('R'):
                        model_code = f"MRE{size}{ser}"
                    break
    else: # LG
        m_oled = re.search(r'\b(OLED\d{2,3}[A-Z0-9]*)\b', u_title)
        if m_oled:
            model_code = m_oled.group(1)
        else:
            m_lg = re.search(r'\b(\d{2,3}(?:QNED|MRGB|NU|NANO|LX|LB|QLED|C[456]|G[456]|B[456])\w*)\b', u_title)
            if m_lg:
                model_code = m_lg.group(1)

    # 3. Model Year Classification (Strict 2025/2026)
    year = None
    if brand.upper() == "SAMSUNG":
        if any(x in model_code for x in ["S90D", "S95D", "QN90D", "Q60D", "DU7", "DU8"]):
            return None
        if len(model_code) > 3 and "H" in model_code[2:]:
            year = 2026
        elif len(model_code) > 3 and "F" in model_code[2:]:
            year = 2025
        elif "2026" in u_title:
            year = 2026
        elif "2025" in u_title:
            year = 2025
    else: # LG
        if any(x in model_code for x in ["C4", "G4", "B4", "M4"]):
            return None
        if any(x in model_code for x in ["C6", "G6", "B6", "W6", "M6", "QNED87B", "QNED86B", "QNED83B", "QNED81B", "QNED72B", "QNED7EB", "QNED8EB", "NU850", "NU800", "MRGB", "27LX6"]):
            year = 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "W5", "M5", "QNED86A", "QNED80A", "QNED93A", "QNED92A", "UA75", "UA77", "NANO81A", "NANO80A"]):
            year = 2025
        elif "2026" in u_title:
            year = 2026
        elif "2025" in u_title:
            year = 2025

    if year not in [2025, 2026]:
        return None

    # 4. Display Type Classification
    display_type = "LED"
    c_up = model_code.upper()
    if brand.upper() == "SAMSUNG":
        if "OLED" in u_title or any(x in c_up for x in ["S90", "S92", "S95", "S85", "S99", "S83"]):
            display_type = "OLED"
        elif "MICRO RGB" in u_title or "R86" in c_up or "R95" in c_up or "R85" in c_up:
            display_type = "Micro RGB"
        elif "NEO QLED" in u_title or "QD-MINI LED" in u_title or "QN" in c_up:
            display_type = "Neo QLED"
        elif "MINILED" in u_title or "MINI LED" in u_title or any(x in c_up for x in ["M74", "M86", "M80"]):
            display_type = "Mini LED"
        elif "QLED" in u_title or "Q7" in c_up or "Q8" in c_up or "Q6" in c_up or "LS03" in c_up:
            display_type = "QLED"
        elif "U8092" in c_up or "U8072" in c_up or "LED 4K" in u_title or "CRYSTAL UHD" in u_title:
            display_type = "UHD 4K"
    else: # LG
        if "QNED" in c_up or "QNED" in u_title:
            display_type = "QNED"
        elif "MRGB" in c_up or "MINI RGB" in u_title or "MICRO RGB" in u_title:
            display_type = "Micro RGB"
        elif any(x in c_up for x in ["NU900", "NU800", "NU850", "NU85", "UA75", "UA77"]):
            display_type = "UHD 4K"
        elif "NANO" in c_up or "NANOCELL" in u_title:
            display_type = "NanoCell"
        elif "27LX6" in c_up or "STANBYME" in u_title:
            display_type = "Lifestyle"
        elif "OLED" in u_title or "OLED" in c_up or re.search(r"\bOLED\w*[BCGWM][456]\b", c_up):
            display_type = "OLED evo" if ("EVO" in u_title or any(x in c_up for x in ["G6", "G5", "C6", "C5"])) else "OLED"

    # 5. Price Guard Thresholds in PLN
    if "OLED" in display_type.upper():
        if size in [42, 48] and price < 2500.0: return None
        if size == 55 and price < 3000.0: return None
        if size == 65 and price < 4200.0: return None
        if size >= 77 and price < 6000.0: return None
    elif "MICRO RGB" in display_type.upper():
        if size <= 50 and price < 2500.0: return None
        if size in [55, 65] and price < 3500.0: return None
        if size >= 75 and price < 5000.0: return None
    elif any(x in display_type.upper() for x in ["QNED", "QLED", "NEO QLED", "MINI LED"]):
        if size <= 43 and price < 1000.0: return None
        if size in [50, 55] and price < 1400.0: return None
        if size >= 65 and price < 2000.0: return None
        if size >= 75 and price < 2800.0: return None
    elif display_type == "UHD 4K":
        if size <= 43 and price < 700.0: return None
        if size >= 55 and price < 1000.0: return None
    elif display_type == "Lifestyle":
        if price < 1200.0: return None

    return {
        "brand": "Samsung" if brand.upper() == "SAMSUNG" else "LG",
        "year": year,
        "display": display_type,
        "display_type": display_type,
        "size": size,
        "model_code": model_code,
        "price": price,
        "original_price": orig_price,
        "shipping": "Free",
        "cashback": 0.0,
        "promo": promo,
        "title": title,
        "url": url,
        "link": url
    }

def process_mediaexpert_data(data_obj):
    cleaned = {"Samsung": [], "LG": []}
    for brand in ["Samsung", "LG"]:
        raw_list = data_obj.get(brand, [])
        seen_codes = {}
        for it in raw_list:
            prod = parse_mediaexpert_product(it, brand)
            if prod:
                mc = prod["model_code"]
                if mc not in seen_codes or prod["price"] < seen_codes[mc]["price"]:
                    seen_codes[mc] = prod
        cleaned[brand] = sorted(list(seen_codes.values()), key=lambda x: (x["year"], x["size"], x["price"]), reverse=True)
    return cleaned

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump-file", help="Path to raw dumped JSON file")
    args = parser.parse_args()

    all_data = {"Samsung": [], "LG": []}
    step_files = [
        r"C:\Users\harry.park\.gemini\antigravity\brain\f5be8497-b2c8-406d-b69f-5f9e4ce904e9\.system_generated\steps\847\output.txt",
        r"C:\Users\harry.park\.gemini\antigravity\brain\f5be8497-b2c8-406d-b69f-5f9e4ce904e9\.system_generated\steps\278\output.txt"
    ]
    if args.dump_file and os.path.exists(args.dump_file):
        step_files.insert(0, args.dump_file)

    for fp in step_files:
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                text = f.read()
            idx = text.find('### Result\n')
            if idx != -1:
                res_str = text[idx + len('### Result\n'):].split('### Ran Playwright code')[0].strip()
                try:
                    obj = json.loads(res_str)
                    d = obj.get("data", {})
                    all_data["Samsung"].extend(d.get("Samsung", []))
                    all_data["LG"].extend(d.get("LG", []))
                except Exception: pass
            else:
                for line in text.split('\n'):
                    line = line.strip()
                    if line.startswith('{"Samsung":'):
                        try:
                            obj = json.loads(line)
                            all_data["Samsung"].extend(obj.get("Samsung", []))
                            all_data["LG"].extend(obj.get("LG", []))
                        except Exception: pass
                        break

    if not all_data["Samsung"] and not all_data["LG"]:
        print("[ERROR] No raw MediaExpert data available.")
        sys.exit(1)

    cleaned = process_mediaexpert_data(all_data)

    out_s = os.path.join(DATA_DIR, "raw_mediaexpert_pl_samsung.json")
    out_l = os.path.join(DATA_DIR, "raw_mediaexpert_pl_lg.json")

    with open(out_s, "w", encoding="utf-8") as f:
        json.dump(cleaned["Samsung"], f, ensure_ascii=False, indent=2)
    with open(out_l, "w", encoding="utf-8") as f:
        json.dump(cleaned["LG"], f, ensure_ascii=False, indent=2)

    print(f"✅ [MEDIAEXPERT PL] Successfully processed {len(cleaned['Samsung'])} Samsung and {len(cleaned['LG'])} LG models!")
    print(f"  ➔ Saved to {out_s}")
    print(f"  ➔ Saved to {out_l}")

if __name__ == "__main__":
    main()
