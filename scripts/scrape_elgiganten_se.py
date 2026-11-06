# -*- coding: utf-8 -*-
"""
Elgiganten Sweden (elgiganten.se) Scraper & Normalizer
Standardizes Samsung & LG TV products for Sweden, enforcing 2025/2026 year rules,
filtering out gaming monitors/laptops, and formatting SEK prices.
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
    "ODYSSEY", "GAMING", "DATORSKÄRM", "GAMINGSKÄRM", "BILD SKÄRM", "BILDSKÄRM",
    "MONITOR", "GALAXY BOOK", "LAPTOP", "COPILOT", "OUTLET PRIS", "ANVÄNT SKICK",
    "BRA SKICK", "SOUNDBAR", "SOUND BAR", "VÄGGFÄSTE", "FÄSTE", "STAND", "KABEL",
    "FJÄRRKONTROLL", "PROJEKTOR", "BEAMER"
]

def parse_elgiganten_product(raw_item, brand):
    title = raw_item.get("title", "").strip()
    u_title = title.upper()
    url = raw_item.get("url", "").strip()
    raw_snippet = raw_item.get("rawSnippet", "")
    promo = raw_item.get("promo", "None")

    if any(k in u_title for k in NON_TV_KEYWORDS):
        return None
    if "/outlet/" in url or "/datorer-kontor/" in url or "/datorskarm/" in url:
        return None

    # 1. Screen size
    size = 0
    m_sz = re.search(r'(\d{2,3})[\s"”\'-]*(?:TUM|INCH|\"|”|\b)', u_title)
    if m_sz:
        c_sz = int(m_sz.group(1))
        if c_sz in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
            size = c_sz
    if not size or size < 22:
        return None

    # 2. Price extraction from lines in rawSnippet
    lines = [l.strip() for l in raw_snippet.split('\n') if l.strip()]
    price = 0.0
    for l in lines:
        m_p = re.match(r'^(\d[\d\s]*\d)\s*\.-$', l)
        if m_p:
            p_cand = float(m_p.group(1).replace(' ', ''))
            if p_cand >= 1000.0 and p_cand < 500000.0:
                price = p_cand
                break
    if not price:
        # Fallback to item price if valid
        raw_p = raw_item.get("price", 0)
        if raw_p and raw_p < 200000:
            price = float(raw_p)
            
    if price < 1500.0:
        return None

    # 3. Original price extraction
    orig_price = price
    for l in lines:
        m_op = re.search(r'Tidigare pris\s*(\d[\d\s]*\d)\s*\.-', l, re.I)
        if m_op:
            orig_price = float(m_op.group(1).replace(' ', ''))
            break
            
    # 4. Model Code Extraction
    model_code = "Unknown"
    if brand.upper() == "SAMSUNG":
        patterns = [
            r'\b(QN\d{2,3}[FH])\b',
            r'\b(S\d{2}[FH])\b',
            r'\b(U\d{4}[FH])\b',
            r'\b(M\d{2}[FH])\b',
            r'\b(R\d{2}[FH])\b',
            r'\b(LS03[A-Z]{1,2})\b',
            r'\b(Q\d[FH]\d?)\b',
            r'\b(H\d{4}[FH])\b'
        ]
        for pat in patterns:
            m = re.search(pat, u_title)
            if m:
                ser = m.group(1)
                if ser.startswith('S') or ser.startswith('QN') or ser.startswith('LS') or ser.startswith('Q'):
                    model_code = f"QE{size}{ser}"
                elif ser.startswith('U') or ser.startswith('M') or ser.startswith('H'):
                    model_code = f"TQ{size}{ser}" if ser.startswith('U7025') else f"UE{size}{ser}"
                elif ser.startswith('R'):
                    model_code = f"MRE{size}{ser}"
                break
    else: # LG
        m_oled = re.search(r'\b(OLED\d{2,3}[A-Z0-9]+)\b', u_title)
        if m_oled:
            model_code = m_oled.group(1)
        else:
            m_lg = re.search(r'\b(\d{2,3}(?:QNED|MRGB|NU|NANO|LX|LB|QLED)[A-Z0-9]+)\b', u_title)
            if m_lg:
                model_code = m_lg.group(1)
            else:
                m_oled_ser = re.search(r'\b([CGBMW][56][A-Z0-9]*)\b', u_title)
                if m_oled_ser and ('OLED' in u_title or 'EVO' in u_title):
                    model_code = f"OLED{size}{m_oled_ser.group(1)}"
                else:
                    m_qned = re.search(r'\bQNED\s*(\d{2,3}[A-Z]?)\b', u_title)
                    if m_qned:
                        model_code = f"{size}QNED{m_qned.group(1)}"
                    else:
                        m_mrgb = re.search(r'\bMRGB\s*(\d{2,3}[A-Z]?)\b', u_title)
                        if m_mrgb:
                            model_code = f"{size}MRGB{m_mrgb.group(1)}"
                        else:
                            m_nano = re.search(r'\bNANO\s*(\d{2,3}[A-Z]?)\b', u_title)
                            if m_nano:
                                model_code = f"{size}NANO{m_nano.group(1)}"
                            else:
                                m_ua = re.search(r'\bUA\s*(\d{2,3}[A-Z]?)\b', u_title)
                                if m_ua:
                                    model_code = f"{size}UA{m_ua.group(1)}"
                                else:
                                    m_nu = re.search(r'\bNU\s*(\d{3,4}[A-Z]?)\b', u_title)
                                    if m_nu:
                                        model_code = f"{size}NU{m_nu.group(1)}"
                                    elif "STANBYME" in u_title or "27LX6" in u_title:
                                        model_code = "27LX6TDGA"

    # Exclude 58-inch U7025H per user rule
    if size == 58 and "U7025" in model_code.upper():
        return None

    # 5. Model Year Classification (Strict 2025/2026)
    year = None
    if brand.upper() == "SAMSUNG":
        if "2026" in u_title or any(x in model_code for x in ["H", "2026"]):
            year = 2026
        elif "2025" in u_title or any(x in model_code for x in ["F", "2025"]):
            year = 2025
    else: # LG
        if any(x in model_code for x in ["C6", "G6", "B6", "W6", "M6", "QNED87B", "QNED86B", "QNED83B", "QNED81B", "QNED72B", "QNED8EB", "NU850", "NU800", "MRGB", "27LX6"]) or "2026" in u_title:
            year = 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "W5", "M5", "QNED86A", "QNED85", "QNED80", "QNED93A", "QNED92A", "NANO82", "UA75"]) or "2025" in u_title:
            year = 2025

    if year not in [2025, 2026]:
        return None

    # 6. Display Type Classification (Strict B6 Guard)
    display_type = "LED"
    c_up = model_code.upper()
    if brand.upper() == "SAMSUNG":
        if "OLED" in u_title or any(x in c_up for x in ["S90", "S95", "S85", "S91"]):
            display_type = "OLED"
        elif "MICRO RGB" in u_title or any(x in c_up for x in ["R95", "R85", "R86", "R87"]):
            display_type = "Micro RGB"
        elif "NEO QLED" in u_title or "QN" in c_up:
            display_type = "Neo QLED"
        elif "MINI LED" in u_title or "MINILED" in u_title or any(x in c_up for x in ["M72", "M84", "M70", "M80"]):
            display_type = "Mini LED"
        elif "QLED" in u_title or "Q7" in c_up or "Q8" in c_up or "LS03" in c_up:
            display_type = "QLED"
        elif "CRYSTAL UHD" in u_title or "U7025" in c_up or "U8095" in c_up or "4K" in u_title:
            display_type = "UHD 4K"
    else: # LG
        if "MRGB" in u_title or "MRGB" in c_up or "MICRO RGB" in u_title or "MINI RGB" in u_title:
            display_type = "Micro RGB"
        elif "QNED" in u_title or "QNED" in c_up:
            display_type = "QNED"
        elif "NU850" in c_up or "NU800" in c_up or "NANOUHD" in u_title or "UA75" in c_up:
            display_type = "UHD 4K"
        elif "NANO" in u_title or "NANOCELL" in u_title:
            display_type = "NanoCell"
        elif "27LX6" in c_up or "STANBYME" in u_title:
            display_type = "Lifestyle"
        elif "OLED" in u_title or "OLED" in c_up or re.search(r"\bOLED\w*[BCGWM][456]\b", c_up):
            display_type = "OLED evo" if ("EVO" in u_title or any(x in c_up for x in ["G6", "G5", "C6", "C5"])) else "OLED"

    # 7. SEK Price Guards
    if "OLED" in display_type.upper():
        if size in [42, 48] and price < 7000.0: return None
        if size == 55 and price < 9000.0: return None
        if size == 65 and price < 12000.0: return None
        if size >= 77 and price < 18000.0: return None
    elif any(x in display_type.upper() for x in ["QNED", "QLED", "NEO QLED", "MINI LED"]):
        if size <= 43 and price < 2500.0: return None
        if size in [50, 55] and price < 3500.0: return None
        if size >= 65 and price < 5000.0: return None
        if size >= 75 and price < 7000.0: return None
    elif display_type == "UHD 4K":
        if size <= 43 and price < 1800.0: return None
        if size >= 55 and price < 2500.0: return None

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

def process_elgiganten_data(data_obj):
    cleaned = {"Samsung": [], "LG": []}
    for brand in ["Samsung", "LG"]:
        raw_list = data_obj.get(brand, [])
        seen_codes = {}
        for it in raw_list:
            prod = parse_elgiganten_product(it, brand)
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

    all_raw = {"Samsung": [], "LG": []}
    step_files = [
        r"C:\Users\harry.park\.gemini\antigravity\brain\f5be8497-b2c8-406d-b69f-5f9e4ce904e9\.system_generated\steps\715\output.txt",
        r"C:\Users\harry.park\.gemini\antigravity\brain\f5be8497-b2c8-406d-b69f-5f9e4ce904e9\.system_generated\steps\719\output.txt",
        r"C:\Users\harry.park\.gemini\antigravity\brain\f5be8497-b2c8-406d-b69f-5f9e4ce904e9\.system_generated\steps\723\output.txt",
        r"C:\Users\harry.park\.gemini\antigravity\brain\f5be8497-b2c8-406d-b69f-5f9e4ce904e9\.system_generated\steps\254\output.txt"
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
                    if "data" in obj:
                        d = obj["data"]
                        if isinstance(d, dict):
                            all_raw["Samsung"].extend(d.get("Samsung", []))
                            all_raw["LG"].extend(d.get("LG", []))
                        elif isinstance(d, list):
                            for it in d:
                                b = it.get("brand", "Samsung")
                                all_raw[b].append(it)
                except Exception:
                    pass
            else:
                for line in text.split('\n'):
                    line = line.strip()
                    if line.startswith('{"Samsung":'):
                        try:
                            obj = json.loads(line)
                            all_raw["Samsung"].extend(obj.get("Samsung", []))
                            all_raw["LG"].extend(obj.get("LG", []))
                        except Exception:
                            pass
                        break

    if not all_raw["Samsung"] and not all_raw["LG"]:
        print("[ERROR] No raw Elgiganten data available.")
        sys.exit(1)

    cleaned = process_elgiganten_data(all_raw)

    out_s = os.path.join(DATA_DIR, "raw_elgiganten_se_samsung.json")
    out_l = os.path.join(DATA_DIR, "raw_elgiganten_se_lg.json")

    with open(out_s, "w", encoding="utf-8") as f:
        json.dump(cleaned["Samsung"], f, ensure_ascii=False, indent=2)
    with open(out_l, "w", encoding="utf-8") as f:
        json.dump(cleaned["LG"], f, ensure_ascii=False, indent=2)

    print(f"✅ [ELGIGANTEN SE] Successfully processed {len(cleaned['Samsung'])} Samsung and {len(cleaned['LG'])} LG models!")
    print(f"  ➔ Saved to {out_s}")
    print(f"  ➔ Saved to {out_l}")

if __name__ == "__main__":
    main()
