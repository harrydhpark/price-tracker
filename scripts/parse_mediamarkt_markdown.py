import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Price regex pattern
price_regex = re.compile(r'CHF\s*([\d\s’\x27\x60,.]*[,.]\d{2})')
price_regex_alt = re.compile(r'CHF\s*(\d+)')

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

def parse_mediamarkt_file(filepath, brand):
    print(f"[PARSING] MediaMarkt raw file: {filepath} for {brand}")
    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath}")
        return []
        
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        markdown = data.get("markdown", "")
        
    # Remove image markdown references
    markdown = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', markdown)
    
    # Matches products links
    # [Title](Link)
    pattern = rf'\[{brand}\s+([^\]]+)\]\(([^)]+)\)'
    matches = list(re.finditer(pattern, markdown, re.IGNORECASE))
    
    products = []
    for idx, match in enumerate(matches):
        full_title = f"{brand} " + match.group(1)
        link = match.group(2)
        
        start_pos = match.end()
        end_pos = matches[idx+1].start() if idx+1 < len(matches) else len(markdown)
        block = markdown[start_pos:end_pos]
        
        # 1. Direct Seller Check: skip if contains "Verkauf und Versand durch [Partner]"
        if "Verkauf und Versand durch" in block:
            # Check if seller is NOT MediaMarkt
            # Usually direct seller has no "Verkauf und Versand durch" line, or it says "Verkauft durch MediaMarkt"
            if "MediaMarkt" not in block:
                continue
                
        # 2. Exclude monitors, washers, second hand
        title_upper = full_title.upper()
        if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "ZUBEHÖR", "HALTERUNG"]):
            continue
        if any(x in title_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT"]):
            continue
            
        # 3. Parse Price
        price_val = 0.0
        price_match = price_regex.search(block)
        if not price_match:
            price_match = price_regex_alt.search(block)
            
        if price_match:
            p_str = price_match.group(1).replace("\u2019", "").replace("'", "").replace("`", "").replace(" ", "").replace(",", ".").replace(".–", "").strip()
            if p_str.endswith(".") or p_str.endswith(","):
                p_str = p_str[:-1]
            try:
                price_val = float(p_str)
            except ValueError:
                price_val = 0.0
                
        if price_val == 0.0:
            continue
            
        # 4. Extract size
        size_match = re.search(r'(\d+)\s*"', full_title)
        if not size_match:
            size_match = re.search(r'(\d+)\s*Zoll', full_title, re.IGNORECASE)
        size_val = int(size_match.group(1)) if size_match else 55
        
        if size_val < 32:
            continue
            
        # 5. Extract model code from title or link
        model_code = "Unknown"
        # First try to parse from detailed link
        # e.g., ..._samsung-qe75q8faau-tv... -> qe75q8faau
        link_lower = link.lower()
        model_match = re.search(r'_(samsung|lg)-([a-z0-9\-]+)-\d+\.html', link_lower)
        if model_match:
            mc = model_match.group(2).upper()
            # Clean up extra words from URL slug using regex
            clean_match = re.search(r'(QE\d{2}[A-Z0-9]+|UE\d{2}[A-Z0-9]+|GQ\d{2}[A-Z0-9]+|MRE\d{2}[A-Z0-9]+|OLED\d{2}[A-Z0-9]+|QNED\d{2}[A-Z0-9]+|UA\d{2}[A-Z0-9]+|LM\d{2}[A-Z0-9]+|UR\d{2}[A-Z0-9]+|UT\d{2}[A-Z0-9]+)', mc)
            if clean_match:
                model_code = clean_match.group(1)
            elif len(mc) >= 6:
                parts = mc.split('-')
                if len(parts[0]) >= 6:
                    model_code = parts[0]
                else:
                    model_code = mc
                
        if model_code == "Unknown":
            # Fallback: parse from title words
            words = title_upper.split()
            for w in words:
                clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "")
                if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                    model_code = clean_w
                    break
                    
        # 6. Determine year
        if brand.lower() == "samsung":
            year_val = classify_samsung_year(model_code, title_upper)
        else:
            year_val = classify_lg_year(model_code, title_upper)
            
        if year_val not in [2025, 2026]:
            continue
            
        # LG C6 special mapping
        if model_code == "Unknown" and brand.lower() == "lg":
            if "C6" in title_upper:
                model_code = f"OLED{size_val}C6"
            elif "G6" in title_upper:
                model_code = f"OLED{size_val}G6"
            elif "B6" in title_upper:
                model_code = f"OLED{size_val}B6"
                
        # 7. Promo check
        promo_desc = "None"
        if "Cashback" in block or "Rabatt" in block or "Aktion" in block:
            # Basic parsing of promo text in block
            promo_lines = [line.strip() for line in block.split("\n") if any(x in line for x in ["Cashback", "Rabatt", "Aktion", "inkl. MwSt"])]
            if promo_lines:
                # Find line that is not just "inkl. MwSt"
                for pl in promo_lines:
                    if "inkl. MwSt" not in pl and len(pl) > 2:
                        promo_desc = pl
                        break
                        
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
            "title": full_title,
            "link": link if link.startswith("http") else "https://www.mediamarkt.ch" + link
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
    
    samsung_raw = os.path.join(data_dir, "mediamarkt_samsung_raw.json")
    lg_raw = os.path.join(data_dir, "mediamarkt_lg_raw.json")
    
    samsungs = parse_mediamarkt_file(samsung_raw, "Samsung")
    lgs = parse_mediamarkt_file(lg_raw, "LG")
    
    with open(os.path.join(data_dir, "raw_mediamarkt_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, "raw_mediamarkt_lg.json"), "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print(f"\n[PARSING MM DONE] Saved {len(samsungs)} Samsung models and {len(lgs)} LG models to clean JSON.")

if __name__ == "__main__":
    main()
