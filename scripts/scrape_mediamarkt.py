from scrapling.fetchers import StealthySession
from bs4 import BeautifulSoup
import json
import re
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

def _load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    if os.path.isfile(env_path):
        try:
            with open(env_path, "r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip().lstrip("\ufeff")
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()

# Get TIMEOUT_MULTIPLIER
TIMEOUT_MULTIPLIER = float(os.environ.get("TIMEOUT_MULTIPLIER", "1.0"))
if TIMEOUT_MULTIPLIER != 1.0:
    print(f"[TIMEOUT MULTIPLIER] Applying multiplier: {TIMEOUT_MULTIPLIER}")

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
        if any(x in model_code for x in ["C6", "G6", "B6", "QNED86B", "QNED80B", "QNED87B", "QNED71B", "QNED70B", "QNED72B", "QNED7EB", "UA77", "MRGB87B", "LX7B", "LX6", "27LX6TDGA", "QLED7EB", "MRGB96B"]):
            return 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED7EA", "UA75", "MRGB87A", "LX7A", "LX5", "QNED70A", "NANO81A", "NANO80A", "QNED93A"]):
            return 2025
        elif any(x in model_code for x in ["C4", "G4", "B4", "QNED80", "QNED85", "QNED86", "UA73"]):
            if "2025" in title_upper:
                return 2025
            return 2024
            
    if any(x in title_upper for x in ["C6", "G6", "B6", "QNED86B", "QNED71B", "QNED70B", "QNED72B", "QNED80B", "QNED87B", "QNED7EB", "MRGB87B", "LX7B", "LX6", "27LX6", "STANBYME 2", "MRGB96B"]):
        return 2026
    if any(x in title_upper for x in ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED87A", "QNED7EA", "QNED72A", "MRGB87A", "LX7A", "LX5", "QNED70", "NANO81", "NANO80", "QNED93"]):
        return 2025
    if any(x in title_upper for x in ["C4", "G4", "B4"]):
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
                
                # Check promo badge first
                if promo == "None":
                    badge_cand = parent.find(lambda el: el.name in ['span', 'div', 'p'] and any(kw in el.get_text().lower() for kw in ["cashback", "soundbar", "geschenk", "gratis", "rabatt", "aktion", "gutschein", "coupon"]))
                    if badge_cand:
                        cand_text = badge_cand.get_text(strip=True)
                        if len(cand_text) < 80 and not any(junk in cand_text.lower() for junk in ["warenkorb", "lieferung", "abholen", "mediamarkt"]):
                            promo = cand_text
                
                # 1. First priority: Dedicated price DOM elements
                price_el = parent.find(attrs={"data-test": re.compile(r"branded-price|product-price|price-box", re.I)})
                if not price_el:
                    price_el = parent.find(class_=lambda x: x and any(c in str(x).lower() for c in ["mms-branded-price", "brandedprice", "productprice"]))
                
                if price_el and price == "N/A":
                    p_txt = price_el.get_text(strip=True)
                    m = re.search(r'([\d\s’\x27\x60,.]*(?:[.–]|,\d{2}|\.\d{2}))', p_txt)
                    if m:
                        clean_num = re.sub(r'[.–\s’\x27\x60]', '', m.group(1)).strip()
                        if len(clean_num) > 1 and clean_num not in ["2025", "2026"]:
                            price = m.group(0).strip()
                
                # 2. Fallback: Search in parent text with promo badge text pre-stripped
                if price == "N/A":
                    text = parent.get_text()
                    # Capture promo mention before stripping if not yet set
                    if promo == "None":
                        cb_found = re.findall(r'(?:CHF\s*\d+[\d\s’\x27\x60,.]*\s*(?:Cashback|Rabatt|Gutschein|Coupon|Zusatzrabatt|Ersparnis|Geschenk|Sparen)|(?:Cashback|Rabatt|Gutschein|Coupon|Zusatzrabatt|Ersparnis|Geschenk|Sparen)\s*(?:von|bis\s*zu)?\s*CHF\s*[\d\s’\x27\x60,.]+)', text, flags=re.I)
                        if cb_found:
                            promo = cb_found[0].strip()
                            
                    # Strip discount and cashback mentions
                    clean_text = re.sub(r'CHF\s*\d+[\d\s’\x27\x60,.]*\s*(?:Cashback|Rabatt|Gutschein|Coupon|Zusatzrabatt|Ersparnis|Geschenk|Sparen)', '', text, flags=re.I)
                    clean_text = re.sub(r'(?:Cashback|Rabatt|Gutschein|Coupon|Zusatzrabatt|Ersparnis|Geschenk|Sparen)\s*(?:von|bis\s*zu)?\s*CHF\s*[\d\s’\x27\x60,.]+', '', clean_text, flags=re.I)
                    
                    price_match = re.search(r'CHF\s*([\d\s’\x27\x60,.]*(?:[.–]|,\d{2}|\.\d{2}))', clean_text)
                    if price_match:
                        p_val = re.sub(r'[.–\s’\x27\x60]', '', price_match.group(1)).strip()
                        if len(p_val) > 1 and p_val not in ["2025", "2026"]:
                            price = price_match.group(0).strip()
                        
                seller_match = re.search(r'(?:Verkauft durch|Sold by)\s+([^\n\r.]+)', parent.get_text(), re.IGNORECASE)
                if seller_match:
                    seller = seller_match.group(1).strip()
                        
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
                
            if any(x in title_upper for x in ["GALAXY S26", "SMARTPHONE", "HANDY", "MOBILE", "TAB S"]):
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
                
            # Screen size & OLED price threshold guard (reject promo voucher / discount false positives)
            if display_type == "OLED":
                if size_val >= 77 and price_val < 1500.0:
                    continue
                elif size_val >= 65 and price_val < 1000.0:
                    continue
                elif size_val >= 48 and price_val < 600.0:
                    continue
                elif size_val >= 42 and price_val < 500.0:
                    continue
            elif size_val >= 75 and price_val < 400.0:
                continue
            elif price_val < 150.0:
                continue
                
            try:
                from swiss_promo_parser import parse_swiss_promo_and_cashback
                cashback_amt, promo_desc = parse_swiss_promo_and_cashback(promo_desc, title, brand, year_val, model_code, size_val, price_val)
            except Exception:
                cashback_amt = 0
                
            products.append({
                "brand": brand,
                "year": year_val,
                "display": display_type,
                "size": size_val,
                "model_code": model_code,
                "price": price_val,
                "shipping": "Free",
                "installment": "",
                "cashback": cashback_amt,
                "promo": promo_desc,
                "title": title,
                "link": "https://www.mediamarkt.ch" + href if href.startswith("/") else href
            })
            page_added += 1
            
        print(f"  -> Added {page_added} valid TVs from page {page_num}.")
        page_num += 1
        
    return products

def scrape_mediamarkt_firecrawl_deprecated(brand):
    return []
def _legacy_mediamarkt_firecrawl(brand):
    api_key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if not api_key:
        print(f"  [FIRECRAWL] No API key found, skipping Firecrawl.")
        return []
    
    print(f"\n⚡ [FIRECRAWL LIVE] Executing real-time queries for {brand} on mediamarkt.ch...")
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        import requests as cffi_requests
    
    if brand.upper() == "SAMSUNG":
        queries = [
            "https://www.mediamarkt.ch/de/search.html?query=samsung%20oled%20s95h",
            "https://www.mediamarkt.ch/de/search.html?query=samsung%20S90&brand=SAMSUNG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=samsung%20S95&brand=SAMSUNG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=samsung%20S99&brand=SAMSUNG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=samsung%20QN80&brand=SAMSUNG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=samsung%20M70&brand=SAMSUNG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=samsung%20R85&brand=SAMSUNG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=samsung%20U8090&brand=SAMSUNG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=samsung%20the%20frame&brand=SAMSUNG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=samsung%202026&brand=SAMSUNG&marketplace=MediaMarkt"
        ]
    else:
        queries = [
            "https://www.mediamarkt.ch/de/search.html?query=65C67",
            "https://www.mediamarkt.ch/de/search.html?query=LG%20C6&brand=LG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=LG%20G6&brand=LG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=LG%20B6&brand=LG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=LG%20QNED&brand=LG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=LG%20MRGB&brand=LG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=LG%20StanbyME&brand=LG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=LG%202026&brand=LG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=LG%20C5&brand=LG&marketplace=MediaMarkt",
            "https://www.mediamarkt.ch/de/search.html?query=LG%20G5&brand=LG&marketplace=MediaMarkt"
        ]

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    all_products = []
    
    for url in queries:
        payload = {"url": url, "formats": ["markdown"], "waitFor": 3000}
        try:
            r = cffi_requests.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers, timeout=60)
            if r.status_code != 200:
                print(f"  ⚠️ [FIRECRAWL] HTTP {r.status_code} on {url}")
                continue
            md = r.json().get("data", {}).get("markdown", "")
            card_chunks = re.split(r'(?:In den Warenkorb|In den Einkaufswagen){1,2}', md)
            for card in card_chunks:
                m_link = re.search(r'\[\*\*([^\*\]]+)\*\*\]\((https?://www\.mediamarkt\.ch/[^\)]+/product/[^\)]+)\)', card)
                if not m_link:
                    continue
                title = m_link.group(1).strip()
                p_url = m_link.group(2).strip()
                u_title = title.upper()
                
                # Check non-TV
                if any(x in u_title for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HALTERUNG", "AIRPODS", "IPHONE", "GALAXY S", "SMARTPHONE", "PLAYSTATION", "BEAMER", "PROJEKTOR"]):
                    continue
                if any(x in u_title for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT"]):
                    continue
                
                # Parse price (robust matching for CHF)
                matches = re.findall(r'CHF[\s\xa0]*(\d[\d\s\xa0\u202f’\'`.,]*(?:\.\u2013|,\u2013|,\d{2}|\.\d{2}|\b))', card)
                price_val = 0.0
                for m in matches:
                    clean_p = re.sub(r'[\s\xa0\u202f’\'`\u2013-]', '', m).strip()
                    if not clean_p: continue
                    if ',' in clean_p and '.' in clean_p: clean_p = clean_p.replace('.', '').replace(',', '.')
                    elif ',' in clean_p: clean_p = clean_p.replace(',', '.')
                    elif '.' in clean_p and len(clean_p.split('.')[-1]) == 3: clean_p = clean_p.replace('.', '')
                    try:
                        v = float(clean_p)
                        if 100.0 <= v <= 35000.0 and v not in [2024, 2025, 2026]:
                            price_val = v
                            break
                    except ValueError:
                        continue
                if price_val == 0.0:
                    continue
                
                # Promo
                promo_desc = "None"
                if "Aus unserer Werbung" in card:
                    promo_desc = "Aus unserer Werbung"
                if "Sound Suite" in card:
                    promo_desc = (promo_desc + " | 25% LG Sound Suite") if promo_desc != "None" else "25% LG Sound Suite"
                
                # Size
                size_val = 55
                m_sz = re.search(r'\b(115|100|98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:inch|zoll|cm|\b)', u_title)
                if m_sz:
                    size_val = int(m_sz.group(1))
                    
                # Model code & year
                if brand.upper() == "SAMSUNG":
                    year_val = classify_samsung_year("Unknown", u_title)
                    model_code = extract_model_code_from_title(u_title, "samsung", size_val)
                    if model_code == "Unknown":
                        for s in ["S95H", "S90H", "S85H", "S99H", "QN90H", "QN85H", "QN80H", "QN70H", "M80H", "M70H", "R95H", "R85H", "U8090H", "U8000H", "LS03H", "S90F", "S95F", "S85F"]:
                            if s in u_title:
                                model_code = f"QE{size_val}{s}"
                                break
                    display_type = "LED"
                    if "OLED" in u_title: display_type = "OLED"
                    elif "QNED" in u_title: display_type = "QNED"
                    elif "NEO QLED" in u_title or "NEOQLED" in u_title: display_type = "Neo QLED"
                    elif "QLED" in u_title: display_type = "QLED"
                    elif any(x in u_title for x in ["MRGB", "R85", "R95"]): display_type = "MRGB"
                else:
                    year_val = classify_lg_year("Unknown", u_title)
                    m_code = re.search(r'\b(OLED\d{2}[A-Z0-9]+|\d{2}QNED[A-Z0-9]+|\d{2}MRGB[A-Z0-9]+|\d{2}NANO[A-Z0-9]+|\d{2}UT[A-Z0-9]+|\d{2}UR[A-Z0-9]+)\b', u_title)
                    if m_code:
                        model_code = m_code.group(1)
                    else:
                        m_slug = re.search(r'_(lg-[a-z0-9-]+)-\d+\.html', p_url)
                        if m_slug:
                            slug_upper = m_slug.group(1).upper()
                            m_sc = re.search(r'(OLED\d{2}[A-Z0-9]+|\d{2}QNED[A-Z0-9]+|\d{2}MRGB[A-Z0-9]+)', slug_upper)
                            model_code = m_sc.group(1) if m_sc else f"LG{size_val}C6"
                        else:
                            model_code = f"LG{size_val}C6"
                    display_type = "LED"
                    if "OLED" in u_title or "OLED" in model_code: display_type = "OLED"
                    elif "QNED" in u_title or "QNED" in model_code: display_type = "QNED"
                    elif "MRGB" in u_title or "MRGB" in model_code: display_type = "MRGB"
                
                if year_val not in [2025, 2026]:
                    continue
                
                try:
                    from swiss_promo_parser import parse_swiss_promo_and_cashback
                    cashback_amt, promo_desc = parse_swiss_promo_and_cashback(promo_desc, title, brand, year_val, model_code, size_val, price_val)
                except Exception:
                    cashback_amt = 0
                    
                all_products.append({
                    "brand": brand,
                    "year": year_val,
                    "display": display_type,
                    "size": size_val,
                    "model_code": model_code,
                    "price": price_val,
                    "shipping": "Free",
                    "installment": "",
                    "cashback": cashback_amt,
                    "promo": promo_desc,
                    "title": title,
                    "link": p_url
                })
        except Exception as ex:
            print(f"  ⚠️ [FIRECRAWL ERROR] on {url}: {ex}")
        time.sleep(0.5)
        
    print(f"  ✔ [FIRECRAWL] Collected {len(all_products)} raw items for {brand}.")
    return all_products

def scrape_mediamarkt_brand(brand):
    print(f"\n[MEDIAMARKT ZERO-FIRECRAWL] Starting scrape for brand: {brand}")
    products = []
    # Zero-Firecrawl: Firecrawl API calls permanently decommissioned
            
    # 2. Secondary Failover: Local StealthySession if Firecrawl returned 0 products
    if not products:
        print(f"  ➔ Failover: Executing local StealthySession for {brand}...")
        if brand.upper() == "SAMSUNG":
            search_configs = [
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20TV&brand=SAMSUNG&marketplace=MediaMarkt&modelyear=2025%20OR%202026", 10),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%202026&brand=SAMSUNG&marketplace=MediaMarkt", 5),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20OLED&brand=SAMSUNG&marketplace=MediaMarkt", 3),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20S90&brand=SAMSUNG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20S95&brand=SAMSUNG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20oled%20s95h", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20S99&brand=SAMSUNG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20QN80&brand=SAMSUNG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20M70&brand=SAMSUNG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20R85&brand=SAMSUNG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20U8090&brand=SAMSUNG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=samsung%20the%20frame&brand=SAMSUNG&marketplace=MediaMarkt", 2)
            ]
        elif brand.upper() == "LG":
            search_configs = [
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20TV&brand=LG&marketplace=MediaMarkt&modelyear=2025%20OR%202026", 10),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%202026&brand=LG&marketplace=MediaMarkt", 5),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20OLED&brand=LG&marketplace=MediaMarkt", 3),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20C6&brand=LG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20G6&brand=LG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20B6&brand=LG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20C5&brand=LG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20G5&brand=LG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20QNED&brand=LG&marketplace=MediaMarkt", 3),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20MRGB&brand=LG&marketplace=MediaMarkt", 2),
                ("https://www.mediamarkt.ch/de/search.html?query=LG%20StanbyME&brand=LG&marketplace=MediaMarkt", 2)
            ]
        else:
            search_configs = [(f"https://www.mediamarkt.ch/de/search.html?query={brand}+TV", 10)]

        try:
            with StealthySession(headless=False) as session:
                for base_url, max_pages in search_configs:
                    try:
                        res_prods = scrape_mediamarkt_query(session, base_url, max_pages, brand)
                        products.extend(res_prods)
                    except Exception as ex:
                        print(f"  ⚠️ Error or block on {base_url}: {ex}. Breaking early.")
                        break
        except Exception as e:
            print(f"  ⚠️ StealthySession initialization error: {e}")
            
    unique_products = []
    seen = set()
    for p in products:
        if p["model_code"] not in seen:
            seen.add(p["model_code"])
            unique_products.append(p)
            
    print(f"  -> Successfully collected {len(unique_products)} unique products for {brand}.")
    
    # STRICT ASSERTION GATE: ZERO STALE CACHE PERMITTED
    if len(unique_products) == 0:
        raise RuntimeError(f"❌ [CRITICAL ZERO LIVE DATA] Real-time scraping for {brand} failed (0 products). Stale cache fallback is strictly prohibited.")
        
    return unique_products

def main():
    import time
    import argparse
    start_time = time.time()
    
    print("🚀 [ZERO-FIRECRAWL] MediaMarkt CH: Executing In-Browser 2-Stage DOMParser batch (0 Firecrawl credits)...")
    from scrape_western_eu_targeted import run_targeted_western_eu
    run_targeted_western_eu(countries="CH")
    
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    s_path = os.path.join(data_dir, "raw_mediamarkt_samsung.json")
    l_path = os.path.join(data_dir, "raw_mediamarkt_lg.json")
    
    samsungs = json.load(open(s_path, encoding="utf-8")) if os.path.exists(s_path) else []
    lgs = json.load(open(l_path, encoding="utf-8")) if os.path.exists(l_path) else []
    
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    
    s_path = os.path.join(data_dir, "raw_mediamarkt_samsung.json")
    l_path = os.path.join(data_dir, "raw_mediamarkt_lg.json")
    
    # STRICT ZERO CACHE: Ensure non-empty live dataset
    if len(samsungs) == 0 or len(lgs) == 0:
        raise RuntimeError("❌ [CRITICAL ZERO LIVE DATA] MediaMarkt CH live scraping returned zero models. Aborting without stale cache fallback.")
        
    with open(s_path, "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(l_path, "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print(f"\n[MEDIAMARKT DONE] Successfully saved {len(samsungs)} Samsung models and {len(lgs)} LG models directly from live web.")
    
    try:
        from scrape_logger import emit_summary
        elapsed = round(time.time() - start_time, 2)
        emit_summary(country="CH", retailer="MediaMarkt", brand="SAMSUNG", total_extracted=len(samsungs), final_deduplicated=len(samsungs), execution_time_sec=elapsed)
        emit_summary(country="CH", retailer="MediaMarkt", brand="LG", total_extracted=len(lgs), final_deduplicated=len(lgs), execution_time_sec=elapsed)
    except Exception:
        pass
    
    try:
        from scrape_logger import emit_summary
        elapsed = round(time.time() - start_time, 2)
        emit_summary(country="CH", retailer="MediaMarkt", brand="SAMSUNG", total_extracted=len(samsungs), final_deduplicated=len(samsungs), execution_time_sec=elapsed)
        emit_summary(country="CH", retailer="MediaMarkt", brand="LG", total_extracted=len(lgs), final_deduplicated=len(lgs), execution_time_sec=elapsed)
    except Exception:
        pass

if __name__ == "__main__":
    main()
