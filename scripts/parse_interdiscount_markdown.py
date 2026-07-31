import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

price_regex = re.compile(r'(\d[\d\s’\x27\x60,.]*[,.]\d{2})')

def classify_samsung_year(model_code, title_upper):
    if model_code != "Unknown":
        if len(model_code) > 3:
            sub = model_code[2:]
            if "H" in sub:
                return 2026
            elif "F" in sub:
                return 2025
            elif "D" in sub or "E" in sub:
                return 2024
            
    if any(x in title_upper for x in ["S90H", "S95H", "S85H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "LS03H", "U8000H", "U8090H"]):
        return 2026
    if any(x in title_upper for x in ["S90F", "S95F", "S85F", "QN900F", "QN800F", "QN95F", "QN90F", "QN85F", "QN80F", "QN70F", "LS03F", "U8000F", "U8090F"]):
        return 2025
    if any(x in title_upper for x in ["S90D", "S95D", "S85D", "QN900D", "QN800D", "QN95D", "QN90D", "QN85D", "QN80D", "QN70D", "LS03D", "U8000D", "U8090D"]):
        return 2024
    return None

def classify_lg_year(model_code, title_upper):
    if model_code != "Unknown":
        if any(x in model_code for x in ["C6", "G6", "B6", "QNED86B", "QNED80B", "QNED87B", "QNED72B", "QNED7EB", "UA77"]):
            return 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED7EA", "UA75"]):
            return 2025
        elif any(x in model_code for x in ["C4", "G4", "B4", "QNED80", "QNED85", "QNED86", "UA73"]):
            return 2024
            
    if "C6" in title_upper or "G6" in title_upper or "B6" in title_upper or "QNED86B" in title_upper or "QNED80B" in title_upper or "QNED7EB" in title_upper:
        return 2026
    if "C5" in title_upper or "G5" in title_upper or "B5" in title_upper or "QNED86A" in title_upper or "QNED80A" in title_upper or "QNED7EA" in title_upper:
        return 2025
    if "C4" in title_upper or "G4" in title_upper or "B4" in title_upper:
        return 2024
    return None

def parse_interdiscount_raw(filepath, brand):
    print(f"[PARSING ID] Loading: {filepath} for {brand}")
    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath}")
        return []
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    json_match = re.search(r'(\[\s*\{.*\}\s*\])', content, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
        except Exception as e:
            print(f"[ERROR] JSON parsing failed: {e}")
            return []
    else:
        print("[WARN] JSON block not found in raw file")
        return []
        
    products = []
    brand_upper = brand.upper()
    
    for item in data:
        title = item.get("name")
        href = item.get("href")
        price_str = item.get("price")
        promo_desc = item.get("promo") or "None"
        
        if not title or not href or not price_str:
            continue
            
        title_upper = title.upper()
        
        # 1. Purge non-TVs
        if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "ZUBEHÖR", "HALTERUNG"]):
            continue
        if any(x in title_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT"]):
            continue
            
        # 2. Parse Price
        price_match = price_regex.search(price_str)
        price_val = 0.0
        if price_match:
            p_str = price_match.group(1).replace("\u2019", "").replace("'", "").replace("`", "").replace(" ", "").replace(",", ".").strip()
            try:
                price_val = float(p_str)
            except ValueError:
                price_val = 0.0
        else:
            # Fallback
            clean_p = price_str.replace("CHF", "").strip()
            price_match_alt = re.search(r'([\d\s’\x27\x60,.]+)', clean_p)
            if price_match_alt:
                p_str = price_match_alt.group(1).replace("\u2019", "").replace("'", "").replace("`", "").replace(" ", "").replace(",", ".").strip()
                if p_str.endswith(".") or p_str.endswith(","):
                    p_str = p_str[:-1]
                try:
                    price_val = float(p_str)
                except ValueError:
                    price_val = 0.0
                    
        if price_val == 0.0:
            continue
            
        # 3. Model Code
        words = title_upper.split()
        model_code = "Unknown"
        for w in words:
            clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "")
            if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                model_code = clean_w
                break
                
        # 4. Size
        size_match = re.search(r'(\d+)\s*"', title)
        if not size_match:
            size_match = re.search(r'(\d+)\s*Zoll', title, re.IGNORECASE)
        if not size_match and model_code != "Unknown":
            code_nums = re.findall(r'\d+', model_code)
            if code_nums and len(code_nums[0]) == 2:
                size_val = int(code_nums[0])
            else:
                size_val = 55
        else:
            size_val = int(size_match.group(1)) if size_match else 55
            
        if size_val < 32:
            continue
            
        # 5. Year
        if brand.lower() == "samsung":
            year_val = classify_samsung_year(model_code, title_upper)
        else:
            year_val = classify_lg_year(model_code, title_upper)
            
        if year_val not in [2025, 2026]:
            continue
            
        # LG Special C6 mapping
        if model_code == "Unknown" and brand.lower() == "lg":
            if "C6" in title_upper:
                model_code = f"OLED{size_val}C6"
            elif "G6" in title_upper:
                model_code = f"OLED{size_val}G6"
            elif "B6" in title_upper:
                model_code = f"OLED{size_val}B6"
                
        display_type = "LED"
        if "OLED" in title_upper:
            display_type = "OLED"
        elif "QNED" in title_upper:
            display_type = "QNED"
        elif "NEO QLED" in title_upper or "NEOQLED" in title_upper:
            display_type = "Neo QLED"
        elif "QLED" in title_upper:
            display_type = "QLED"
            
        products.append({
            "brand": brand,
            "year": year_val,
            "display": display_type,
            "size": size_val,
            "model_code": model_code,
            "price": price_val,
            "shipping": "Free",
            "installment": "",
            "cashback": 0,
            "promo": promo_desc,
            "title": title,
            "link": "https://www.interdiscount.ch" + href if href.startswith("/") else href
        })
        
    # Deduplicate
    unique_products = []
    seen = set()
    for p in products:
        if p["model_code"] not in seen:
            seen.add(p["model_code"])
            unique_products.append(p)
            
    print(f"  ➔ Parsed {len(unique_products)} unique products for {brand}.")
    return unique_products

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    
    samsung_raw = os.path.join(data_dir, "interdiscount_samsung_raw.json")
    lg_raw = os.path.join(data_dir, "interdiscount_lg_raw.json")
    
    samsungs = parse_interdiscount_raw(samsung_raw, "Samsung")
    lgs = parse_interdiscount_raw(lg_raw, "LG")
    
    with open(os.path.join(data_dir, "raw_interdiscount_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, "raw_interdiscount_lg.json"), "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print(f"\n[PARSING ID DONE] Saved {len(samsungs)} Samsung models and {len(lgs)} LG models to clean JSON.")

if __name__ == "__main__":
    main()
