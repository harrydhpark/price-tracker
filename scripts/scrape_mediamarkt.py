from scrapling.fetchers import StealthySession
from bs4 import BeautifulSoup
import json
import re
import os
import sys

# Get TIMEOUT_MULTIPLIER
TIMEOUT_MULTIPLIER = float(os.environ.get("TIMEOUT_MULTIPLIER", "1.0"))
if TIMEOUT_MULTIPLIER != 1.0:
    print(f"[TIMEOUT MULTIPLIER] Applying multiplier: {TIMEOUT_MULTIPLIER}")

sys.stdout.reconfigure(encoding='utf-8')

# Regex pattern for pricing
price_regex = re.compile(r'(\d[\d\s’\x27\x60,.]*[,.]\d{2})')

def extract_model_code_from_title(title_upper, brand, size_val):
    if brand.lower() == "samsung":
        patterns = [
            r'(QN\d{2,3}[FH])',    # QN900H, QN90F 등
            r'(S\d{2}[FH])',       # S95F, S90H, S85F 등
            r'(U\d{4}[FH])',       # U8000F, U8090H, U8000H 등
            r'(M\d{2}[FH])',       # M70H 등
            r'(R\d{2}[FH])',       # R85H, R95H 등
            r'(LS03[A-Z]{1,2})',   # LS03HE, LS03F 등
            r'(F\d{4})',           # F6000 등
            r'(MR\d{2}[FH])'       # MR95F 등
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
    if "2026" in title_upper:
        return 2026
    if "2025" in title_upper:
        return 2025
    if "2024" in title_upper:
        return 2024
        
    mc = model_code
    if mc == "Unknown":
        mc = extract_model_code_from_title(title_upper, "samsung", 55)
        
    if mc != "Unknown":
        if len(mc) > 3:
            sub = mc[2:]
            if "H" in sub:
                return 2026
            elif "F" in sub:
                return 2025
            elif "D" in sub or "E" in sub:
                return 2024
            
    if any(x in title_upper for x in ["S90H", "S95H", "S85H", "S99H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "LS03H", "U8000H", "U8090H", "R85H", "R95H", "M70H"]):
        return 2026
    if any(x in title_upper for x in ["S90F", "S95F", "S85F", "QN900F", "QN800F", "QN95F", "QN90F", "QN85F", "QN80F", "QN70F", "LS03F", "U8000F", "U8090F", "Q7F", "Q8F"]):
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


def scrape_mediamarkt_query(session, base_url, max_pages, brand):
    products = []
    page_num = 1
    
    # Regex pattern for pricing
    price_regex = re.compile(r'(\d[\d\s’\x27\x60,.]*[,.]\d{2})')
    
    while page_num <= max_pages:
        url = f"{base_url}&page={page_num}"
        print(f"  -> [PAGE {page_num}] Navigating to: {url}")
        try:
            p = session.fetch(
                url,
                solve_cloudflare=True,
                wait=int(3000 * TIMEOUT_MULTIPLIER),
                timeout=int(60000 * TIMEOUT_MULTIPLIER)
            )
            
            html = str(p.html_content)
            if not html or p.status != 200:
                print(f"  -> Empty response or bad status {p.status}")
                break
                
            if "Verification Required" in html:
                print(f"  -> Cloudflare block detected on page {page_num}")
                break
                
        except Exception as e:
            print(f"  -> Navigation failed for page {page_num}: {e}")
            break
            
        print(f"  -> Parsing page {page_num}...")
        
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)
        raw_items = []
        seen_titles = set()
        
        for link in links:
            href = link['href']
            if '/product/' not in href:
                continue
                
            # Extract real product title from headings or aria-label, avoiding image ALT text
            title = ""
            parent_node = link.parent
            for _ in range(5):
                if not parent_node:
                    break
                h_node = parent_node.find(['h2', 'h3', 'p', 'span'], class_=lambda c: c and any(x in str(c).lower() for x in ['title', 'name', 'heading']))
                if h_node:
                    title = h_node.get_text(strip=True)
                    break
                parent_node = parent_node.parent

            if not title or len(title) < 10 or 'Das Display zeigt' in title or 'Fernseher zeigt' in title:
                title = link.get('aria-label', '').strip() or link.get_text(strip=True)

            if not title or len(title) < 10 or 'Das Display zeigt' in title or 'Fernseher zeigt' in title:
                continue

            if title in seen_titles:
                continue
            seen_titles.add(title)
            
            price = "N/A"
            promo = "None"
            seller = "MediaMarkt"
            
            parent = link.parent
            for depth in range(8):
                if not parent:
                    break
                text = parent.get_text()
                
                price_match = re.search(r'CHF\s*([\d\s’\x27\x60,.]*(?:[.–]|,\d{2}|\.\d{2}))', text)
                if price_match and price == "N/A":
                    p_val = re.sub(r'[.–\s’\x27\x60]', '', price_match.group(1)).strip()
                    if len(p_val) > 1 and p_val not in ["2025", "2026"]:
                        price = price_match.group(0).strip()
                        
                seller_match = re.search(r'(?:Verkauft durch|Sold by)\s+([^\n\r.]+)', text, re.IGNORECASE)
                if seller_match:
                    seller = seller_match.group(1).strip()
                    
                if any(kw in text for kw in ["Cashback", "Rabatt", "Geschenk", "Aktion"]):
                    promo_el = parent.find(class_=lambda x: x and any(kw in x for kw in ["badge", "promo", "Aktion", "benefit"]))
                    if promo_el and promo == "None":
                        promo = promo_el.get_text(strip=True)
                        
                parent = parent.parent
                
            raw_items.append({
                "title": title,
                "href": href,
                "price": price,
                "promo": promo,
                "seller": seller
            })
            
        print(f"  -> Extracted {len(raw_items)} raw items on page {page_num}.")
        if len(raw_items) == 0:
            print("  -> No items extracted on this page, exiting pagination loop.")
            break
            
        page_added = 0
        for item in raw_items:
            title = item["title"]
            price_str = item["price"]
            promo_desc = item["promo"]
            seller = item["seller"]
            href = item["href"]
            
            title_upper = title.upper()
            
            if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "ZUBEHÖR", "HALTERUNG"]):
                continue
            if any(x in title_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT"]):
                continue
                
            seller_upper = seller.upper()
            if "MEDIAMARKT" not in seller_upper or "PARTNER" in seller_upper:
                continue
                
            price_val = 0.0
            if price_str != "N/A":
                clean_p = price_str.replace("CHF", "").strip()
                price_match = re.search(r'([\d\s’\x27\x60,.]+)', clean_p)
                if price_match:
                    p_str = price_match.group(1).replace("\u2019", "").replace("'", "").replace("`", "").replace(" ", "").replace(",", ".").strip()
                    if p_str.endswith(".") or p_str.endswith(","):
                        p_str = p_str[:-1]
                    try:
                        price_val = float(p_str)
                    except ValueError:
                        price_val = 0.0
                        
            if price_val == 0.0:
                continue
                
            model_code = "Unknown"
            url_slug_match = re.search(r'_(?:lg|samsung)-([a-z0-9]+)', href.lower())
            if url_slug_match:
                slug_code = url_slug_match.group(1).upper()
                if brand.lower() == "samsung":
                    if slug_code.startswith(("QE", "UE", "MRE")) or (any(char.isdigit() for char in slug_code) and len(slug_code) >= 6):
                        model_code = slug_code
                else:
                    model_code = slug_code
            
            if model_code == "Unknown":
                words = title_upper.split()
                for w in words:
                    clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "")
                    if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                        model_code = clean_w
                        break
                    
            size_match = re.search(r'(\d+)\s*\"', title)
            if not size_match:
                size_match = re.search(r'(\d+)\s*Zoll', title, re.IGNORECASE)
                
            size_val = int(size_match.group(1)) if size_match else 55
            
            # Always prioritize model code size digits if valid 2-digit screen size exists
            if model_code != "Unknown":
                code_nums = re.findall(r'\d+', model_code)
                if code_nums and len(code_nums[0]) in [2, 3]:
                    parsed_code_size = int(code_nums[0])
                    if parsed_code_size in [42, 43, 48, 50, 55, 65, 75, 77, 83, 85, 86, 98, 100]:
                        size_val = parsed_code_size
                
            if size_val < 22:
                continue
                
            if brand.lower() == "samsung":
                year_val = classify_samsung_year(model_code, title_upper)
            else:
                year_val = classify_lg_year(model_code, title_upper)
                
            if year_val not in [2025, 2026]:
                continue
                
            if model_code == "Unknown" and brand.lower() == "lg":
                if "C6" in title_upper:
                    model_code = f"OLED{size_val}C6"
                elif "G6" in title_upper:
                    model_code = f"OLED{size_val}G6"
                elif "B6" in title_upper:
                    model_code = f"OLED{size_val}B6"
                elif "C5" in title_upper:
                    model_code = f"OLED{size_val}C5"
                elif "G5" in title_upper:
                    model_code = f"OLED{size_val}G5"
                elif "B5" in title_upper:
                    model_code = f"OLED{size_val}B5"
                    
            if model_code == "Unknown" and brand.lower() == "samsung":
                extracted = extract_model_code_from_title(title_upper, brand, size_val)
                if extracted != "Unknown":
                    model_code = extracted
                else:
                    if "U8090H" in title_upper:
                        model_code = f"UE{size_val}U8090H"
                    elif "M70H" in title_upper:
                        model_code = f"UE{size_val}M70H"
                    elif "QN80H" in title_upper:
                        model_code = f"QE{size_val}QN80H"
                    elif "S99H" in title_upper:
                        model_code = f"QE{size_val}S99H"
                    elif "S90H" in title_upper:
                        model_code = f"QE{size_val}S90H"
                    elif "R85H" in title_upper:
                        model_code = f"MRE{size_val}R85H"
                    elif "R95H" in title_upper:
                        model_code = f"MRE{size_val}R95H"
                    elif "LS03HE" in title_upper:
                        model_code = f"QE{size_val}LS03HE"
                    elif "U8000F" in title_upper:
                        model_code = f"UE{size_val}U8000F"
                    elif "Q7F" in title_upper:
                        model_code = f"QE{size_val}Q7F"
                    elif "Q8F" in title_upper:
                        model_code = f"QE{size_val}Q8F"
                    elif "S90F" in title_upper:
                        model_code = f"QE{size_val}S90F"
                    elif "FRAME PRO" in title_upper:
                        model_code = f"QE{size_val}LS03FW"
                    elif "FRAME" in title_upper:
                        if year_val == 2025:
                            model_code = f"QE{size_val}LS03F"
                        else:
                            model_code = f"QE{size_val}LS03HE"
                    elif "F6000" in title_upper:
                        model_code = f"UE{size_val}F6000"
                    elif "MR95F" in title_upper:
                        model_code = f"MRE{size_val}MR95F"
                    else:
                        model_code = f"QE{size_val}UNKWN{year_val}"
                    
            display_type = "LED"
            if "OLED" in title_upper:
                display_type = "OLED"
            elif "QNED" in title_upper:
                display_type = "QNED"
            elif "NEO QLED" in title_upper or "NEOQLED" in title_upper:
                display_type = "Neo QLED"
            elif "QLED" in title_upper:
                display_type = "QLED"
            elif any(x in title_upper or x in model_code.upper() for x in ["MRGB", "R85", "R95", "MICRO RGB", "MICRRGB"]):
                display_type = "MRGB"
                
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
                "link": "https://www.mediamarkt.ch" + href if href.startswith("/") else href
            })
            page_added += 1
            
        print(f"  -> Added {page_added} valid TVs from page {page_num}.")
        page_num += 1
        
    return products

def scrape_mediamarkt_brand(brand):
    print(f"\n[MEDIAMARKT] Starting scrape for brand: {brand}")
    if brand.upper() == "SAMSUNG":
        search_configs = [
            ("https://www.mediamarkt.ch/de/search.html?query=samsung%20TV&brand=SAMSUNG&marketplace=MediaMarkt&modelyear=2025%20OR%202026", 10),
            ("https://www.mediamarkt.ch/de/search.html?query=samsung%20OLED&brand=SAMSUNG&marketplace=MediaMarkt", 3),
            ("https://www.mediamarkt.ch/de/search.html?query=samsung%20S90&brand=SAMSUNG&marketplace=MediaMarkt", 2),
            ("https://www.mediamarkt.ch/de/search.html?query=samsung%20S95&brand=SAMSUNG&marketplace=MediaMarkt", 2),
            ("https://www.mediamarkt.ch/de/search.html?query=samsung%20S99&brand=SAMSUNG&marketplace=MediaMarkt", 2)
        ]
    elif brand.upper() == "LG":
        search_configs = [
            ("https://www.mediamarkt.ch/de/search.html?query=LG%20TV&brand=LG&marketplace=MediaMarkt&modelyear=2025%20OR%202026", 10),
            ("https://www.mediamarkt.ch/de/search.html?query=LG%20OLED&brand=LG&marketplace=MediaMarkt", 3),
            ("https://www.mediamarkt.ch/de/search.html?query=LG%20C6&brand=LG&marketplace=MediaMarkt", 2),
            ("https://www.mediamarkt.ch/de/search.html?query=LG%20G6&brand=LG&marketplace=MediaMarkt", 2),
            ("https://www.mediamarkt.ch/de/search.html?query=LG%20C5&brand=LG&marketplace=MediaMarkt", 2),
            ("https://www.mediamarkt.ch/de/search.html?query=LG%20G5&brand=LG&marketplace=MediaMarkt", 2)
        ]
    else:
        search_configs = [
            (f"https://www.mediamarkt.ch/de/search.html?query={brand}+TV", 10)
        ]
        
    products = []
    
    with StealthySession(headless=True) as session:
        for base_url, max_pages in search_configs:
            print(f"\n➔ [SEARCH QUERY] Executing: {base_url} (Max pages: {max_pages})")
            products.extend(scrape_mediamarkt_query(session, base_url, max_pages, brand))
            
    unique_products = []
    seen = set()
    for p in products:
        if p["model_code"] not in seen:
            seen.add(p["model_code"])
            unique_products.append(p)
            
    print(f"  -> Successfully collected {len(unique_products)} unique products for {brand}.")
    return unique_products

def main():
    samsungs = scrape_mediamarkt_brand("Samsung")
    lgs = scrape_mediamarkt_brand("LG")
    
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    
    with open(os.path.join(data_dir, "raw_mediamarkt_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, "raw_mediamarkt_lg.json"), "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print(f"\n[MEDIAMARKT DONE] Saved {len(samsungs)} Samsung models and {len(lgs)} LG models.")

if __name__ == "__main__":
    main()
