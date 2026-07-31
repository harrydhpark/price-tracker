import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

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
        if any(x in model_code for x in ["C6", "G6", "B6", "QNED86B", "QNED80B", "QNED87B", "QNED72B", "QNED7EB", "UA77", "MRGB87B", "LX7B", "LX6", "QLED7EB", "MRGB96B"]):
            return 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED7EA", "UA75", "MRGB87A", "LX7A", "LX5", "QNED70A", "NANO81A", "NANO80A", "QNED93A"]):
            return 2025
        elif any(x in model_code for x in ["C4", "G4", "B4", "QNED80", "QNED85", "QNED86", "UA73"]):
            if "2025" in title_upper:
                return 2025
            return 2024
            
    if "C6" in title_upper or "G6" in title_upper or "B6" in title_upper or "QNED86B" in title_upper or "QNED80B" in title_upper or "QNED7EB" in title_upper or "MRGB87B" in title_upper or "LX7B" in title_upper or "LX6" in title_upper or "MRGB96B" in title_upper:
        return 2026
    if "C5" in title_upper or "G5" in title_upper or "B5" in title_upper or "QNED86A" in title_upper or "QNED80A" in title_upper or "QNED7EA" in title_upper or "MRGB87A" in title_upper or "LX7A" in title_upper or "LX5" in title_upper or "QNED70" in title_upper or "NANO81" in title_upper or "NANO80" in title_upper or "QNED93" in title_upper:
        return 2025
    if "C4" in title_upper or "G4" in title_upper or "B4" in title_upper:
        return 2024
    return None

def derive_samsung_2026_code(title_upper, size_val):
    # Derived code rule:
    # U8090H -> UE{s}U8090H
    # U8000H -> UE{s}U8000H
    # M70H -> UE{s}M70H
    # R85H -> MRE{s}R85H
    # LS03HE -> QE{s}LS03HE
    # Others like OLED, QNED, Neo QLED -> QE{s}{Family}
    
    families = ["U8090H", "U8000H", "M70H", "R85H", "LS03HE", "S90H", "S95H", "S99H", "QN80H", "QN85H", "QN90H", "QN95H", "QN800H", "QN900H"]
    found_family = None
    for f in families:
        if f in title_upper:
            found_family = f
            break
            
    if not found_family:
        # Try to find any word ending with H
        words = title_upper.split()
        for w in words:
            w_clean = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "")
            if w_clean.endswith("H") and len(w_clean) >= 4 and any(char.isdigit() for char in w_clean):
                found_family = w_clean
                break
                
    if not found_family:
        return "Unknown"
        
    if found_family in ["U8090H", "U8000H", "M70H"]:
        return f"UE{size_val}{found_family}"
    elif found_family == "R85H":
        return f"MRE{size_val}{found_family}"
    else:
        return f"QE{size_val}{found_family}"

def parse_markdown_content(markdown, brand, fixed_year=None):
    # Remove image markdown references
    markdown = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', markdown)
    
    # Matches product links: [Title](Link)
    # MediaMarkt title in markdown is e.g. [SAMSUNG 55" QLED Q8F ...](link)
    pattern = rf'\[{brand}\s+([^\]]+)\]\(([^)]+)\)'
    matches = list(re.finditer(pattern, markdown, re.IGNORECASE))
    
    products = []
    for idx, match in enumerate(matches):
        full_title = f"{brand} " + match.group(1)
        link = match.group(2)
        
        start_pos = match.end()
        end_pos = matches[idx+1].start() if idx+1 < len(matches) else len(markdown)
        block = markdown[start_pos:end_pos]
        
        # 1. Direct Seller Check
        if "Verkauf und Versand durch" in block:
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
        
        if size_val < 22:
            continue
            
        # 5. Extract model code from title or link
        model_code = "Unknown"
        link_lower = link.lower()
        model_match = re.search(r'_(samsung|lg)-([a-z0-9\-]+)-\d+\.html', link_lower)
        if model_match:
            mc = model_match.group(2).upper()
            clean_match = re.search(r'(\d+)?(QE\d{2}[A-Z0-9]+|UE\d{2}[A-Z0-9]+|GQ\d{2}[A-Z0-9]+|MRE\d{2}[A-Z0-9]+|OLED\d{2}[A-Z0-9]+|QNED\d{2}[A-Z0-9]+|UA\d{2}[A-Z0-9]+|LM\d{2}[A-Z0-9]+|UR\d{2}[A-Z0-9]+|UT\d{2}[A-Z0-9]+)', mc)
            if clean_match:
                model_code = clean_match.group(0)
            elif len(mc) >= 6:
                parts = mc.split('-')
                if len(parts[0]) >= 6:
                    model_code = parts[0]
                else:
                    model_code = mc
                    
        if model_code == "Unknown":
            # parse from title words
            words = title_upper.split()
            for w in words:
                clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "")
                if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                    model_code = clean_w
                    break
                    
        # Determine year
        if brand.lower() == "samsung":
            year_val = classify_samsung_year(model_code, title_upper)
        else:
            year_val = classify_lg_year(model_code, title_upper)
            
        if year_val is None and fixed_year is not None:
            year_val = fixed_year
            
        if year_val not in [2025, 2026]:
            continue
            
        # Samsung 2026 model code derivation rules (Critical)
        if brand.lower() == "samsung" and year_val == 2026:
            derived_mc = derive_samsung_2026_code(title_upper, size_val)
            if derived_mc != "Unknown":
                model_code = derived_mc
                
        # LG model code mapping if Unknown
        if model_code == "Unknown" and brand.lower() == "lg":
            if "C6" in title_upper:
                model_code = f"OLED{size_val}C67LA"
            elif "G6" in title_upper:
                model_code = f"OLED{size_val}G67LA"
            elif "B6" in title_upper:
                model_code = f"OLED{size_val}B67LA"
            elif "C5" in title_upper:
                model_code = f"OLED{size_val}C57LA"
            elif "G5" in title_upper:
                model_code = f"OLED{size_val}G57LW"
            elif "B5" in title_upper:
                model_code = f"OLED{size_val}B59LA"
                
        # 6. Promo check
        promo_desc = "None"
        if "Cashback" in block or "Rabatt" in block or "Aktion" in block:
            promo_lines = [line.strip() for line in block.split("\n") if any(x in line for x in ["Cashback", "Rabatt", "Aktion", "inkl. MwSt"])]
            if promo_lines:
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
    return products

def parse_all_pages():
    scratch_dir = r"C:\Users\harry.park\.gemini\antigravity\brain\518a5474-5d4f-493a-979e-846df933cf38\scratch"
    data_dir = r"d:\TV 유럽영업\15. AX Task\2026 AX 실행과제\Price Tracker\data"
    
    samsungs = []
    lgs = []
    
    # 1. Samsung 2026 Pages
    for p in range(1, 6):
        fn = f"mm_samsung_2026_page{p}.txt"
        fp = os.path.join(scratch_dir, fn)
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    markdown = data.get("markdown", "")
                    items = parse_markdown_content(markdown, "Samsung", fixed_year=2026)
                    samsungs.extend(items)
                    print(f"  Parsed {len(items)} Samsung 2026 items from {fn}")
                except Exception as e:
                    print(f"  [ERROR] Parsing {fn} failed: {e}")
                    
    # 2. Samsung 2025 Pages
    for p in range(1, 6):
        fn = f"mm_samsung_2025_page{p}.txt"
        fp = os.path.join(scratch_dir, fn)
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    markdown = data.get("markdown", "")
                    items = parse_markdown_content(markdown, "Samsung", fixed_year=2025)
                    samsungs.extend(items)
                    print(f"  Parsed {len(items)} Samsung 2025 items from {fn}")
                except Exception as e:
                    print(f"  [ERROR] Parsing {fn} failed: {e}")
                    
    # 3. LG 2026 Pages
    for p in range(1, 6):
        fn = f"mm_lg_2026_page{p}.txt"
        fp = os.path.join(scratch_dir, fn)
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    markdown = data.get("markdown", "")
                    items = parse_markdown_content(markdown, "LG", fixed_year=2026)
                    lgs.extend(items)
                    print(f"  Parsed {len(items)} LG 2026 items from {fn}")
                except Exception as e:
                    print(f"  [ERROR] Parsing {fn} failed: {e}")
                    
    # 4. LG 2025 Pages
    for p in range(1, 6):
        fn = f"mm_lg_2025_page{p}.txt"
        fp = os.path.join(scratch_dir, fn)
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    markdown = data.get("markdown", "")
                    items = parse_markdown_content(markdown, "LG", fixed_year=2025)
                    lgs.extend(items)
                    print(f"  Parsed {len(items)} LG 2025 items from {fn}")
                except Exception as e:
                    print(f"  [ERROR] Parsing {fn} failed: {e}")
                    
    # Deduplicate by model_code
    unique_samsung = []
    seen_sam = set()
    for p in samsungs:
        if p["model_code"] not in seen_sam:
            seen_sam.add(p["model_code"])
            unique_samsung.append(p)
            
    unique_lg = []
    seen_lg = set()
    for p in lgs:
        if p["model_code"] not in seen_lg:
            seen_lg.add(p["model_code"])
            unique_lg.append(p)
            
    print(f"\n[DEDUPLICATE RESULTS]")
    print(f"  ➔ Samsung: {len(samsungs)} -> {len(unique_samsung)} unique")
    print(f"  ➔ LG: {len(lgs)} -> {len(unique_lg)} unique")
    
    # Save clean JSON files
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "raw_mediamarkt_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(unique_samsung, f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, "raw_mediamarkt_lg.json"), "w", encoding="utf-8") as f:
        json.dump(unique_lg, f, ensure_ascii=False, indent=2)
        
    print(f"[SUCCESS] MediaMarkt all pages parsed successfully!")

if __name__ == "__main__":
    parse_all_pages()
