import json
import re
import os
import sys
from bs4 import BeautifulSoup

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

def parse_mediamarkt_html_file(filepath, brand):
    print(f"[PARSING HTML] Loading: {filepath} for {brand}")
    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath}")
        return []
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    if "### Result" in content:
        parts = content.split("### Result")
        content = parts[1].strip()
        
    if content.startswith('"') and content.endswith('"'):
        content = content[1:-1]
        
    # Standard decoding replacement
    html_content = content.replace('\\"', '"').replace('\\/', '/').replace('\\\\', '\\').replace('\\n', '\n').replace('\\t', '\t')
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # MediaMarkt product cards are normally anchor tags with class or href containing /product/
    # Or div containers. Let's look for all links matching /product/
    product_links = soup.find_all("a", href=re.compile(r'/product/'))
    
    products = []
    seen_links = set()
    
    for link_el in product_links:
        href = link_el.get("href")
        if not href or href in seen_links:
            continue
        seen_links.add(href)
        
        # Climb parent nodes to find the container card (contains price and details)
        container = link_el
        found_price_container = False
        for _ in range(8):
            if not container:
                break
            # Look for price element or text containing CHF
            price_el = container.find(attrs={"data-test": "mms-price"})
            if price_el or "CHF" in container.text:
                found_price_container = True
                break
            container = container.parent
            
        if not found_price_container or not container:
            container = link_el.parent
            
        # Title extraction
        title = link_el.text.strip()
        if not title:
            # Try aria-label or title attribute
            title = link_el.get("aria-label") or link_el.get("title") or ""
            title = title.strip()
            
        if not title or len(title) < 5 or brand.lower() not in title.lower():
            continue
            
        # Seller Check: filter out partner listings
        block_text = container.text
        if "Verkauf und Versand durch" in block_text:
            if "MediaMarkt" not in block_text:
                continue
                
        # Non-TV filter
        title_upper = title.upper()
        if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "ZUBEHÖR", "HALTERUNG"]):
            continue
        if any(x in title_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT"]):
            continue
            
        # Price extraction
        price_val = 0.0
        price_el = container.find(attrs={"data-test": "mms-price"})
        price_text = price_el.text if price_el else block_text
        
        price_match = price_regex.search(price_text)
        if not price_match:
            price_match = price_regex_alt.search(price_text)
            
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
            
        # Model Code extraction from link
        model_code = "Unknown"
        link_lower = href.lower()
        # Clean regex logic for model extraction
        # Example link: /de/product/_samsung-qe65s90fat-tv-flat-65-163-cm-uhd-4k-smart-tv-tizen-2278340.html
        model_match = re.search(r'_(samsung|lg)-([a-z0-9\-]+?)-(?:tv|fernseher|flat|display|pro|soundbar|smart|led|\d+)', link_lower)
        if model_match:
            mc = model_match.group(2).upper()
            if len(mc) >= 6:
                model_code = mc
                
        if model_code == "Unknown":
            # Fallback: parse from title words
            words = title_upper.split()
            for w in words:
                clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "")
                if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                    model_code = clean_w
                    break

        # Size extraction
        size_match = re.search(r'(\d+)\s*"', title)
        if not size_match:
            size_match = re.search(r'(\d+)\s*Zoll', title, re.IGNORECASE)
            
        if not size_match and model_code != "Unknown":
            code_nums = re.findall(r'\d+', model_code)
            if code_nums and len(code_nums[0]) in [2, 3]:
                size_val = int(code_nums[0])
            else:
                size_val = 55
        else:
            size_val = int(size_match.group(1)) if size_match else 55
        
        if size_val < 32:
            continue
                    
        # Year classification
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
                
        # Promo extraction
        promo_desc = "None"
        # Look for badges or promo texts inside card
        promo_elements = container.find_all(class_=re.compile(r'badge|promo|offer|discount|strip', re.IGNORECASE))
        if promo_elements:
            promo_texts = [pe.text.strip() for pe in promo_elements if len(pe.text.strip()) > 2]
            if promo_texts:
                promo_desc = " | ".join(promo_texts)
        else:
            # Fallback scan block
            lines = [l.strip() for l in block_text.split("\n") if any(x in l for x in ["Cashback", "Rabatt", "Aktion", "Geschenkt"])]
            valid_lines = [l for l in lines if "inkl. MwSt" not in l and len(l) > 2]
            if valid_lines:
                promo_desc = valid_lines[0]
                
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
            "title": f"{brand} " + title.replace(brand, "").strip(),
            "link": href if href.startswith("http") else "https://www.mediamarkt.ch" + href
        })
        
    # Deduplicate by model_code
    unique_products = []
    seen = set()
    for p in products:
        if p["model_code"] not in seen:
            seen.add(p["model_code"])
            unique_products.append(p)
            
    print(f"  ➔ Successfully parsed {len(unique_products)} unique products for {brand}.")
    return unique_products

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    
    samsung_raw = os.path.join(data_dir, "mediamarkt_samsung_raw.html")
    lg_raw = os.path.join(data_dir, "mediamarkt_lg_raw.html")
    
    samsungs = parse_mediamarkt_html_file(samsung_raw, "Samsung")
    lgs = parse_mediamarkt_html_file(lg_raw, "LG")
    
    with open(os.path.join(data_dir, "raw_mediamarkt_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, "raw_mediamarkt_lg.json"), "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print(f"\n[HTML PARSING MM DONE] Saved {len(samsungs)} Samsung models and {len(lgs)} LG models to clean JSON.")

if __name__ == "__main__":
    main()
