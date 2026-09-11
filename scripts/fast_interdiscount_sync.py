import json
import re
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def extract_precise_price(title, full_text, size_val=55, display_type="LED"):
    if not title:
        return 0.0
        
    # Clean title fragment (first 18 chars)
    clean_frag = title[:18]
    
    # 1. Price immediately before title
    # e.g. '2’299.95 CHF\n\nSAMSUNG QE55S99H' or '2’499.–\n2’499.00 CHF\n\nSAMSUNG'
    pat1 = r'(\d[\d’\']*(?:\.\d{2}|.–|\.95|\.00))\s*(?:CHF)?\s*\n+\s*' + re.escape(clean_frag)
    m = re.findall(pat1, full_text, re.IGNORECASE)
    if m:
        p_raw = m[0].replace('’', '').replace("'", '').replace('.–', '.00')
        try:
            pval = float(p_raw)
            if pval >= 50.0:
                # Apply OLED Guard
                if "OLED" in display_type.upper():
                    if size_val >= 83 and pval < 2000.0: pass
                    elif size_val >= 77 and pval < 1500.0: pass
                    elif size_val >= 65 and pval < 1000.0: pass
                    elif size_val >= 55 and pval < 800.0: pass
                    else: return pval
                else:
                    return pval
        except ValueError:
            pass
            
    # 2. Local search in 200 chars before title
    t_idx = full_text.find(clean_frag)
    if t_idx != -1:
        chunk_before = full_text[max(0, t_idx-200):t_idx]
        m_before = re.findall(r'(\d[\d’\']*(?:\.\d{2}|.–|\.95|\.00))\s*(?:CHF)?', chunk_before)
        if m_before:
            for cand in reversed(m_before):
                p_raw = cand.replace('’', '').replace("'", '').replace('.–', '.00')
                try:
                    pval = float(p_raw)
                    if "OLED" in display_type.upper():
                        if size_val >= 83 and pval < 2000.0: continue
                        elif size_val >= 77 and pval < 1500.0: continue
                        elif size_val >= 65 and pval < 1000.0: continue
                        elif size_val >= 55 and pval < 800.0: continue
                    if pval >= 50.0:
                        return pval
                except ValueError:
                    pass

    # 3. Fallback to all numbers in text with size-based guard
    norm = re.sub(r'\.\s*(\d{2})', r'.\1', full_text)
    clean = norm.replace("’", "").replace("'", "").replace("`", "").replace("CHF", "").replace("EUR", "").replace(" ", "").replace("\n", " ").strip()
    m_all = re.findall(r'(\d+\.\d{2})', clean) or re.findall(r'(\d+)', clean)
    nums = []
    for x in m_all:
        try:
            v = float(x)
            if "OLED" in display_type.upper():
                if size_val >= 83 and v < 2000.0: continue
                elif size_val >= 77 and v < 1500.0: continue
                elif size_val >= 65 and v < 1000.0: continue
                elif size_val >= 55 and v < 800.0: continue
            if v >= 50.0:
                nums.append(v)
        except ValueError:
            pass
    return min(nums) if nums else 0.0

def parse_product_name(title, brand):
    title_upper = title.upper()
    model_code = "Unknown"
    
    # 1. Size
    size_val = 55
    size_match = re.search(r'(\d+)\s*"', title)
    if not size_match:
        size_match = re.search(r'(\d+)\s*Zoll', title, re.IGNORECASE)
    if not size_match:
        size_match = re.search(r'(\d+)\s*inch', title, re.IGNORECASE)
    if not size_match:
        size_match = re.search(r'(\d+)\s*cm', title, re.IGNORECASE)
        if size_match:
            cm = int(size_match.group(1))
            cm_map = {108: 43, 121: 48, 126: 50, 139: 55, 164: 65, 189: 75, 195: 77, 210: 83, 216: 85, 218: 86, 248: 98}
            size_val = cm_map.get(cm, int(cm / 2.54))
    if size_match and not size_val:
        size_val = int(size_match.group(1))
        
    # 2. Model Code
    if brand.upper() == "LG":
        # LG OLED Patterns
        m_oled = re.search(r'\b(OLED\d{2}[A-Z0-9]+)\b', title_upper)
        if m_oled:
            model_code = m_oled.group(1)
        else:
            # LG QNED / UHD
            m_lg = re.search(r'\b(\d{2}[A-Z]{2,4}\d{2,4}[A-Z0-9]*)\b', title_upper)
            if m_lg:
                model_code = m_lg.group(1)
            else:
                words = title_upper.split()
                for w in words:
                    clean_w = re.sub(r'[^\w-]', '', w)
                    if any(junk in clean_w for junk in ["LEDLG", "OLEDLG", "TV", "CINEMA", "SMART"]):
                        continue
                    if any(char.isdigit() for char in clean_w) and len(clean_w) >= 5:
                        model_code = clean_w
                        break
    else: # SAMSUNG
        words = title_upper.split()
        for w in words:
            clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace('"', '').strip()
            if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                if any(clean_w.startswith(pre) for pre in ["GQ", "TQ", "QE", "UE", "GU", "MRE"]):
                    model_code = clean_w
                    break
        if model_code == "Unknown":
            patterns = [
                r'\b(QN\d{2,3}[FH])\b',
                r'\b(S\d{2,3}[FH])\b',
                r'\b(U\d{3,4}[FH])\b',
                r'\b(M\d{2,3}[FH])\b',
                r'\b(R\d{2,3}[FH])\b',
                r'\b(LS03[A-Z]{1,2})\b',
                r'\b(F\d{4})\b',
                r'\b(MR\d{2,3}[FH])\b'
            ]
            for pat in patterns:
                m = re.search(pat, title_upper)
                if m:
                    series = m.group(1)
                    if series.startswith('S') or series.startswith('QN') or series.startswith('LS'):
                        model_code = f"QE{size_val}{series}"
                    elif series.startswith('U') or series.startswith('M') or series.startswith('F'):
                        model_code = f"UE{size_val}{series}"
                    elif series.startswith('R') or series.startswith('MR'):
                        model_code = f"MRE{size_val}{series}"
                    break
        if model_code == "Unknown":
            for w in words:
                clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace('"', '').strip()
                if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                    model_code = clean_w
                    break
                    
    # Priority for size in model code
    if model_code != "Unknown":
        code_nums = re.findall(r'\d+', model_code)
        if code_nums and len(code_nums[0]) in [2, 3]:
            parsed_code_size = int(code_nums[0])
            if parsed_code_size in [27, 42, 43, 48, 50, 55, 65, 75, 77, 83, 85, 86, 98, 100]:
                size_val = parsed_code_size
                
    # 3. Year
    year_val = None
    if brand.upper() == "SAMSUNG":
        if model_code != "Unknown" and len(model_code) > 3:
            sub = model_code[2:]
            if "H" in sub:
                year_val = 2026
            elif "F" in sub:
                year_val = 2025
            elif "D" in sub or "E" in sub:
                year_val = 2024
        if not year_val:
            if "2026" in title_upper or any(x in title_upper for x in ["S90H", "S95H", "S85H", "S99H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "LS03H", "U8000H", "U8090H", "M70H", "R85H", "R95H"]):
                year_val = 2026
            elif "2025" in title_upper or any(x in title_upper for x in ["S90F", "S95F", "S85F", "QN900F", "QN800F", "QN95F", "QN90F", "QN85F", "QN80F", "QN70F", "LS03F", "U8000F", "U8090F", "M70F", "R85F"]):
                year_val = 2025
    elif brand.upper() == "LG":
        # LG Model Year
        lg_2026_codes = ["C6", "G6", "B6", "QNED86B", "QNED80B", "QNED87B", "QNED71B", "QNED70B", "QNED72B", "QNED7EB", "UA77", "MRGB87B", "LX7B", "LX6", "27LX6TDGA", "QLED7EB", "MRGB96B"]
        lg_2025_codes = ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED7EA", "UA75", "MRGB87A", "LX7A", "LX5", "QNED70A", "NANO81A", "NANO80A", "QNED93A"]
        if any(c in model_code.upper() for c in lg_2026_codes) or any(x in title_upper for x in ["2026", "C6", "G6", "B6", "QNED86B", "QNED80B", "QNED87B", "QNED71B", "QNED70B", "QNED72B", "QNED7EB", "MRGB87B", "LX7B", "LX6", "27LX6", "STANBYME 2", "MRGB96B"]):
            year_val = 2026
        elif any(c in model_code.upper() for c in lg_2025_codes) or any(x in title_upper for x in ["2025", "C5", "G5", "B5", "QNED86A", "QNED80A", "QNED87A", "QNED7EA", "QNED72A", "MRGB87A", "LX7A", "LX5", "QNED70", "NANO81", "NANO80", "QNED93"]):
            year_val = 2025
        elif any(c in model_code.upper() for c in ["C4", "G4", "B4", "QNED80T", "UT80", "UA73"]) or any(x in title_upper for x in ["2024", "C4", "G4", "B4"]):
            year_val = 2024
            
    # 4. Display Type
    display_type = "LED"
    code_upper = model_code.upper()
    if brand.upper() == "SAMSUNG":
        if "MRE" in code_upper or "MR" in code_upper or "MICRO RGB" in title_upper:
            display_type = "Micro RGB"
        elif any(x in code_upper for x in ["S90", "S95", "S99", "S85", "S92", "S94", "S9"]):
            display_type = "OLED"
        elif any(x in code_upper for x in ["QN9", "QN8", "QN7", "QN90", "QN95", "QN85", "QN80", "QN70"]):
            display_type = "Neo QLED"
        elif any(x in code_upper for x in ["LS03", "LS01", "LS05", "FRAME"]):
            display_type = "Lifestyle"
        elif any(x in code_upper for x in ["Q6", "Q7", "Q8", "Q9", "QE"]):
            display_type = "QLED"
        elif any(x in code_upper for x in ["U8", "UA", "UT", "UR", "UQ", "UX"]):
            display_type = "UHD 4K"
    elif brand.upper() == "LG":
        if "MRGB" in code_upper or "MRGB" in title_upper:
            display_type = "Micro RGB"
        elif "QNED" in code_upper or "QNED" in title_upper:
            display_type = "QNED"
        elif "OLED" in code_upper or "OLED" in title_upper or re.search(r'OLED\d{2}', code_upper):
            display_type = "OLED evo" if ("EVO" in title_upper or any(x in code_upper for x in ["G5", "G6", "C5", "C6", "M5", "M6"])) else "OLED"
        elif "NANO" in code_upper or "NANO" in title_upper:
            display_type = "NanoCell"
        elif any(x in code_upper for x in ["NU900", "NU90", "NU85", "NU80", "NU800", "NU850", "LB650", "LB", "UA75", "UA73", "UA77"]):
            display_type = "UHD 4K"
        elif "LX" in code_upper or "STANBYME" in code_upper:
            display_type = "Lifestyle"

    return model_code, size_val, year_val, display_type

def clean_and_parse(items, brand):
    products = []
    seen = {}
    
    for item in items:
        title = item.get("title") or item.get("name") or ""
        href = item.get("href") or ""
        text_raw = item.get("text") or item.get("cardText") or ""
        promo_desc = item.get("promo") or "None"
        
        if not title or len(title) < 5:
            continue
            
        title_upper = title.upper()
        if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "WASCHMASCHINE", "TROCKNER", "ZUBEHÖR", "HALTERUNG", "WANDHALTERUNG", "SUBWOOFER", "SPEAKER"]):
            continue
        if any(x in title_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT", "DEMO", "OCCASION"]):
            continue
            
        model_code, size_val, year_val, display_type = parse_product_name(title, brand)
        if size_val < 22 or year_val not in [2025, 2026]:
            continue
            
        price_val = extract_precise_price(title, text_raw, size_val, display_type)
        if price_val < 50.0:
            continue
            
        cb_val = 0
        try:
            from swiss_promo_parser import parse_swiss_promo_and_cashback
            cb_val, promo_desc = parse_swiss_promo_and_cashback(
                promo_desc, f"{title} {text_raw}", brand, year_val, model_code, size_val, price_val
            )
        except Exception:
            pass
            
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
            "promo": promo_desc,
            "title": title,
            "link": "https://www.interdiscount.ch" + href if href.startswith("/") else href
        }
        
        if model_code in seen:
            if price_val < seen[model_code]["price"]:
                seen[model_code] = rec
        else:
            seen[model_code] = rec
            
    return list(seen.values())

def load_json_result(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    if content.startswith("### Result"):
        content = content[len("### Result"):].strip()
    idx = content.find("### Ran Playwright code")
    if idx != -1:
        content = content[:idx].strip()
    return json.loads(content)

def main():
    if len(sys.argv) < 2:
        print("Usage: python fast_interdiscount_sync.py <output_txt_path>")
        sys.exit(1)
        
    output_path = sys.argv[1]
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    
    raw_data = load_json_result(output_path)
    if "data" in raw_data and isinstance(raw_data["data"], dict):
        samsung_items = raw_data["data"].get("samsung", [])
        lg_items = raw_data["data"].get("lg", [])
    else:
        samsung_items = raw_data.get("samsung", [])
        lg_items = raw_data.get("lg", [])
    
    samsungs = clean_and_parse(samsung_items, "Samsung")
    lgs = clean_and_parse(lg_items, "LG")
    
    print(f"Parsed {len(samsungs)} Samsung products for Interdiscount.")
    print(f"Parsed {len(lgs)} LG products for Interdiscount.")
    
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "raw_interdiscount_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, "raw_interdiscount_lg.json"), "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print("[SUCCESS] Interdiscount sync completed successfully with 1:1 precise price extraction!")

if __name__ == "__main__":
    main()
