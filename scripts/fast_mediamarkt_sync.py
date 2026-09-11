# -*- coding: utf-8 -*-
import json
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from swiss_promo_parser import parse_swiss_promo_and_cashback

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def extract_model_code_from_title(title_upper, brand, size_val):
    if brand.lower() == "samsung":
        patterns = [
            r'(QN\d{2,3}[FH])',
            r'(S\d{2}[FH])',
            r'(U\d{4}[FH])',
            r'(M\d{2}[FH])',
            r'(R\d{2}[FH])',
            r'(LS03[A-Z]{1,2})',
            r'(F\d{4})',
            r'(MR\d{2}[FH])'
        ]
        for pat in patterns:
            m = re.search(pat, title_upper)
            if m:
                matched_series = m.group(1)
                if "R85" in matched_series or "R95" in matched_series or "MR" in matched_series:
                    return f"MRE{size_val}{matched_series}"
                elif "U8" in matched_series or "M7" in matched_series or "F6" in matched_series:
                    return f"UE{size_val}{matched_series}"
                else:
                    if "LS03F" in matched_series and "PRO" in title_upper:
                        return f"QE{size_val}LS03FW"
                    return f"QE{size_val}{matched_series}"
    return "Unknown"

def classify_samsung_year(model_code, title_upper):
    if "2026" in title_upper: return 2026
    if "2025" in title_upper: return 2025
    if "2024" in title_upper: return 2024
    if model_code != "Unknown" and len(model_code) > 3:
        sub = model_code[2:]
        if "H" in sub: return 2026
        elif "F" in sub: return 2025
        elif "D" in sub or "E" in sub: return 2024
    if any(x in title_upper for x in ["S90H", "S95H", "S85H", "S99H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "LS03H", "U8000H", "U8090H", "R85H", "R95H"]): return 2026
    if any(x in title_upper for x in ["S90F", "S95F", "S85F", "QN900F", "QN800F", "QN95F", "QN90F", "QN85F", "QN80F", "QN70F", "LS03F", "U8000F", "U8090F", "Q8F", "Q7F"]): return 2025
    if any(x in title_upper for x in ["S90D", "S95D", "S85D", "QN900D", "QN800D", "QN95D", "QN90D", "QN85D", "QN80D", "QN70D", "LS03D", "U8000D", "U8090D"]): return 2024
    return 2025

def classify_lg_year(model_code, title_upper):
    if model_code != "Unknown":
        if any(x in model_code for x in ["C6", "G6", "B6", "QNED86B", "QNED80B", "QNED87B", "QNED72B", "QNED7EB", "UA77", "MRGB87B", "LX7B", "LX6", "QLED7EB", "MRGB96B"]): return 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED7EA", "UA75", "MRGB87A", "LX7A", "LX5", "QNED70A", "NANO81A", "NANO80A", "QNED93A"]): return 2025
        elif any(x in model_code for x in ["C4", "G4", "B4", "QNED80", "QNED85", "QNED86", "UA73"]):
            if "2025" in title_upper: return 2025
            return 2024
    if any(x in title_upper for x in ["C6", "G6", "B6", "QNED86B", "QNED80B", "QNED7EB", "MRGB87B", "LX7B", "LX6", "MRGB96B", "2026"]): return 2026
    if any(x in title_upper for x in ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED7EA", "MRGB87A", "LX7A", "LX5", "QNED70", "NANO81", "NANO80", "QNED93", "2025"]): return 2025
    return 2025

def parse_dump(filepath, brand):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    md = data.get("markdown", "")
    
    blocks = re.split(r'\[\*\*([^\*]+)\*\*\]\((https://www\.mediamarkt\.ch/de/product/[^\)]+)\)', md)
    if len(blocks) <= 1:
        url = data.get("metadata", {}).get("sourceURL") or data.get("metadata", {}).get("url") or ""
        if not url:
            m_u = re.search(r'https://www\.mediamarkt\.ch/de/product/[^\s\)\"]+', md)
            if m_u: url = m_u.group(0)
        m_t = re.search(r'#+\s*(SAMSUNG[^\n]+|LG[^\n]+)', md, re.I)
        if not m_t:
            m_t = re.search(r'\n(SAMSUNG\s+\d+[^\n]+|LG\s+\d+[^\n]+)', md, re.I)
        if m_t and url:
            blocks = ["", m_t.group(1).strip(), url, md]
    items = []
    
    for i in range(1, len(blocks), 3):
        title = blocks[i].strip()
        url = blocks[i+1].strip()
        body = blocks[i+2] if i+2 < len(blocks) else ""
        
        title_upper = title.upper()
        if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "ZUBEHÖR", "HALTERUNG", "WANDHALTERUNG"]):
            continue
        if any(x in title_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT"]):
            continue
            
        # Price extraction
        price_m = re.findall(r'CHF\s*([\d\s’\x27\x60,.]*(?:[.–]|,\d{2}|\.\d{2}))', body)
        price_val = 0.0
        for p in price_m:
            clean = re.sub(r'[.–\s’\x27\x60]', '', p).replace(',', '.').strip()
            try:
                val = float(clean)
                if val >= 80.0 and val not in [2024, 2025, 2026]:
                    price_val = val
                    break
            except ValueError:
                pass
                
        if price_val < 50.0:
            continue
            
        # Model code from URL slug
        model_code = "Unknown"
        slug_match = re.search(r'_(?:lg|samsung)-([a-z0-9]+)', url.lower())
        if slug_match:
            slug = slug_match.group(1).upper()
            if brand.lower() == "samsung":
                if slug.startswith(("QE", "UE", "MRE")) or (any(c.isdigit() for c in slug) and len(slug) >= 6):
                    model_code = slug
            else:
                model_code = slug
                
        if model_code == "Unknown":
            words = title_upper.split()
            for w in words:
                clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "")
                if any(c.isdigit() for c in clean_w) and len(clean_w) >= 6:
                    model_code = clean_w
                    break
                    
        # Screen size
        size_match = re.search(r'(\d+)\s*"', title)
        if not size_match:
            size_match = re.search(r'(\d+)\s*Zoll', title, re.IGNORECASE)
        size_val = int(size_match.group(1)) if size_match else 55
        if model_code != "Unknown":
            code_nums = re.findall(r'\d+', model_code)
            if code_nums and len(code_nums[0]) in [2, 3]:
                sz = int(code_nums[0])
                if sz in [42, 43, 48, 50, 55, 65, 75, 77, 83, 85, 86, 98, 100]:
                    size_val = sz
                    
        if size_val < 22:
            continue
            
        year_val = classify_samsung_year(model_code, title_upper) if brand.lower() == "samsung" else classify_lg_year(model_code, title_upper)
        if year_val not in [2025, 2026]:
            continue
            
        if model_code == "Unknown" and brand.lower() == "lg":
            if "C6" in title_upper: model_code = f"OLED{size_val}C6"
            elif "G6" in title_upper: model_code = f"OLED{size_val}G6"
            elif "B6" in title_upper: model_code = f"OLED{size_val}B6"
            elif "C5" in title_upper: model_code = f"OLED{size_val}C5"
            elif "G5" in title_upper: model_code = f"OLED{size_val}G5"
            elif "B5" in title_upper: model_code = f"OLED{size_val}B5"
            
        if model_code == "Unknown" and brand.lower() == "samsung":
            extracted = extract_model_code_from_title(title_upper, brand, size_val)
            if extracted != "Unknown":
                model_code = extracted
                
        # Display type
        display_type = "LED"
        if "OLED" in title_upper or "OLED" in model_code: display_type = "OLED"
        elif "QNED" in title_upper or "QNED" in model_code: display_type = "QNED"
        elif "NEO QLED" in title_upper or "NEOQLED" in title_upper: display_type = "Neo QLED"
        elif "QLED" in title_upper or "QLED" in model_code: display_type = "QLED"
        elif any(k in title_upper or k in model_code for k in ["MRGB", "R85", "R95", "MICRO RGB"]): display_type = "Micro RGB"
        elif any(k in model_code for k in ["U8", "UA", "UT", "NU"]): display_type = "UHD 4K"
        
        # OLED Guard
        if display_type == "OLED":
            if size_val >= 83 and price_val < 2000.0: continue
            elif size_val >= 77 and price_val < 1500.0: continue
            elif size_val >= 65 and price_val < 1000.0: continue
            elif size_val >= 55 and price_val < 800.0: continue
            elif size_val >= 42 and price_val < 500.0: continue
            
        # Promo
        promo_raw = "None"
        if any(kw in body for kw in ["Cashback", "Rabatt", "Geschenk", "Aktion", "Gutschein", "Gratis", "Soundbar"]):
            m_pr = re.findall(r'(?:Cashback|Rabatt|Geschenk|Aktion|Gutschein|Gratis|Soundbar)[^\n]+', body, re.I)
            if m_pr: promo_raw = m_pr[0].strip()[:80]
            
        cb_val, clean_promo = parse_swiss_promo_and_cashback(promo_raw, f"{title} {body}", brand, year_val, model_code, size_val, price_val)
        
        items.append({
            "brand": "Samsung" if brand.lower() == "samsung" else "LG",
            "year": year_val,
            "display": display_type,
            "size": size_val,
            "model_code": model_code,
            "price": price_val,
            "shipping": "Free",
            "installment": "",
            "cashback": cb_val,
            "promo": clean_promo,
            "title": title,
            "link": url
        })
        
    return items

def main():
    base_dir = r"C:\Users\harry.park\.gemini\antigravity\brain\b82f4db0-4973-4a68-b5f3-be3639f9b5e9\.system_generated\steps"
    
    samsung_steps = [261, 330, 332, 334, 336, 338, 340, 463, 467, 471]
    lg_steps = [342, 344, 346, 348, 350, 352]
    
    all_samsungs = []
    seen_s = {}
    for st in samsung_steps:
        fp = os.path.join(base_dir, str(st), "output.txt")
        items = parse_dump(fp, "Samsung")
        for it in items:
            mc = it["model_code"]
            if mc not in seen_s or it["price"] < seen_s[mc]["price"]:
                seen_s[mc] = it
    all_samsungs = list(seen_s.values())
    
    all_lgs = []
    seen_l = {}
    for st in lg_steps:
        fp = os.path.join(base_dir, str(st), "output.txt")
        items = parse_dump(fp, "LG")
        for it in items:
            mc = it["model_code"]
            if mc not in seen_l or it["price"] < seen_l[mc]["price"]:
                seen_l[mc] = it
    all_lgs = list(seen_l.values())
    
    print(f"[MEDIAMARKT] Extracted {len(all_samsungs)} Samsung and {len(all_lgs)} LG unique live products.")
    
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "raw_mediamarkt_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(all_samsungs, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_DIR, "raw_mediamarkt_lg.json"), "w", encoding="utf-8") as f:
        json.dump(all_lgs, f, ensure_ascii=False, indent=2)
        
    print("[MEDIAMARKT DONE] Successfully saved raw_mediamarkt_samsung.json and raw_mediamarkt_lg.json.")

if __name__ == "__main__":
    main()
