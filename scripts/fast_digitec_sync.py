# -*- coding: utf-8 -*-
import json
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from swiss_promo_parser import parse_swiss_promo_and_cashback

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def classify_samsung_year(model_code, title_upper):
    if model_code != "Unknown":
        if len(model_code) > 3:
            sub = model_code[2:]
            if "H" in sub: return 2026
            elif "F" in sub: return 2025
            elif "D" in sub or "E" in sub: return 2024
    if any(x in title_upper for x in ["S90H", "S95H", "S85H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "LS03H", "U8000H", "U8090H", "R85H", "R95H"]): return 2026
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

def parse_digitec_price(card_text):
    m = re.findall(r'CHF\s*([\d\s’\x27\x60,.]*(?:[.–]|,\d{2}|\.\d{2}))', card_text)
    if not m:
        m = re.findall(r'CHF\s*(\d[\d’\x27\x60]*)', card_text)
    for cand in m:
        clean = re.sub(r'[.–\s’\x27\x60]', '', str(cand)).replace(',', '.').strip()
        try:
            val = float(clean)
            if val >= 50.0 and val not in [2024, 2025, 2026]:
                return val
        except ValueError:
            pass
    return 0.0

def clean_and_parse(items, brand):
    products = []
    seen = {}
    
    for item in items:
        title = item.get("title") or ""
        href = item.get("href") or ""
        text = item.get("text") or ""
        
        if not title or len(title) < 5:
            continue
            
        title_upper = title.upper()
        if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "ZUBEHÖR", "HALTERUNG", "WANDHALTERUNG"]):
            continue
        if any(x in title_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT"]):
            continue
            
        words = title_upper.split()
        model_code = "Unknown"
        for w in words:
            clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "").replace("[", "").replace("]", "")
            if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                if brand.lower() == "samsung" and any(clean_w.startswith(p) for p in ["QE", "UE", "GQ", "TQ", "MRE"]):
                    model_code = clean_w
                    break
                elif brand.lower() == "lg" and (clean_w.startswith("OLED") or any(p in clean_w for p in ["QNED", "NANO", "MRGB", "LX", "UA", "NU"])):
                    model_code = clean_w
                    break
                elif model_code == "Unknown":
                    model_code = clean_w
                    
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
            
        display_type = "LED"
        if "OLED" in title_upper or "OLED" in model_code: display_type = "OLED"
        elif "QNED" in title_upper or "QNED" in model_code: display_type = "QNED"
        elif "NEO QLED" in title_upper or "NEOQLED" in title_upper: display_type = "Neo QLED"
        elif "QLED" in title_upper or "QLED" in model_code: display_type = "QLED"
        elif any(k in title_upper or k in model_code for k in ["MRGB", "R85", "R95", "MICRO RGB"]): display_type = "Micro RGB"
        elif any(k in model_code for k in ["U8", "UA", "UT", "NU"]): display_type = "UHD 4K"
        
        price_val = parse_digitec_price(text)
        if price_val < 50.0:
            continue
            
        if display_type == "OLED":
            if size_val >= 83 and price_val < 2000.0: continue
            elif size_val >= 77 and price_val < 1500.0: continue
            elif size_val >= 65 and price_val < 1000.0: continue
            elif size_val >= 55 and price_val < 800.0: continue
            elif size_val >= 42 and price_val < 500.0: continue
            
        promo_raw = "None"
        if any(kw in text for kw in ["Cashback", "Rabatt", "Geschenk", "Aktion", "Gutschein", "Gratis", "Soundbar"]):
            m_pr = re.findall(r'(?:Cashback|Rabatt|Geschenk|Aktion|Gutschein|Gratis|Soundbar)[^\n]+', text, re.I)
            if m_pr: promo_raw = m_pr[0].strip()[:80]
            
        cb_val, clean_promo = parse_swiss_promo_and_cashback(promo_raw, f"{title} {text}", brand, year_val, model_code, size_val, price_val)
        
        rec = {
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
            "link": "https://www.digitec.ch" + href if href.startswith("/") else href
        }
        
        if model_code in seen:
            if price_val < seen[model_code]["price"]:
                seen[model_code] = rec
        else:
            seen[model_code] = rec
            
    return list(seen.values())

def main():
    if len(sys.argv) < 2:
        print("Usage: python fast_digitec_sync.py <dump_path>")
        sys.exit(1)
        
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith("### Result"):
        content = content[len("### Result"):].strip()
    idx = content.find("### Ran Playwright code")
    if idx != -1:
        content = content[:idx].strip()
        
    raw_data = json.loads(content)
    if "data" in raw_data and isinstance(raw_data["data"], dict):
        s_raw = raw_data["data"].get("samsung", [])
        l_raw = raw_data["data"].get("lg", [])
    else:
        s_raw = raw_data.get("samsung", [])
        l_raw = raw_data.get("lg", [])
    
    samsungs = clean_and_parse(s_raw, "Samsung")
    lgs = clean_and_parse(l_raw, "LG")
    
    print(f"[DIGITEC] Cleaned {len(samsungs)} Samsung and {len(lgs)} LG live items.")
    os.makedirs(DATA_DIR, exist_ok=True)
    
    with open(os.path.join(DATA_DIR, "raw_digitec_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(os.path.join(DATA_DIR, "raw_digitec_lg.json"), "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print("[DIGITEC SUCCESS] Saved raw_digitec_samsung.json and raw_digitec_lg.json successfully.")

if __name__ == "__main__":
    main()
