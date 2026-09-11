import os, sys, json, re, time, openpyxl, shutil
from curl_cffi import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")

def passes_uk_price_guard(display, size, price):
    d_up = str(display).upper()
    p = float(price)
    
    if "OLED" in d_up:
        if size in [42, 48] and p < 650.0: return False
        elif size == 55 and p < 800.0: return False
        elif size == 65 and p < 1100.0: return False
        elif size in [77, 83] and p < 1600.0: return False
        elif size >= 83 and p < 2400.0: return False
    elif "MICRO RGB" in d_up or "MRGB" in d_up or "R85" in d_up or "R95" in d_up:
        if size >= 100 and p < 10000.0: return False
        elif size >= 86 and p < 2500.0: return False
        elif size >= 75 and p < 1800.0: return False
        elif size >= 50 and p < 800.0: return False
    elif any(x in d_up for x in ["QNED", "QLED", "NEO QLED"]):
        if size >= 75 and p < 800.0: return False
        elif size >= 65 and p < 550.0: return False
        elif size >= 50 and p < 350.0: return False
        elif size >= 43 and p < 250.0: return False
    else: # UHD 4K
        if size >= 55 and p < 200.0: return False
        elif size >= 43 and p < 150.0: return False
        
    return p >= 120.0

def parse_currys_tile(tile, brand):
    lines = [l.strip() for l in tile.get_text('\n').split('\n') if l.strip()]
    if not lines:
        return None
        
    title_line = ""
    for l in lines:
        if l.upper().startswith(brand.upper()) and len(l) > 15:
            title_line = l
            break
            
    if not title_line:
        a = tile.find('a', href=re.compile(r'/products/'))
        if a and a.get_text(strip=True):
            title_line = a.get_text(strip=True)
            
    if not title_line or brand.upper() not in title_line.upper():
        return None
        
    u_title = title_line.upper()
    if any(x in u_title for x in ["SOUNDBAR", "SOUND BAR", "BUNDLE", "MONITOR", "ODYSSEY", "ULTRAGEAR", "REMOTE", "PROJECTOR", "BEAMER", "CABLE", "REFURBISHED"]):
        return None
        
    if any(x in u_title for x in ["WALL BRACKET", "FLOOR STAND"]):
        return None
        
    if ("WALL MOUNT" in u_title or "STAND" in u_title) and not ("VERSION" in u_title or "SMART TV" in u_title or "OLED" in u_title or "QNED" in u_title or "QLED" in u_title):
        return None
        
    size_m = re.search(r'\b(115|100|98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"\'\'-]*(?:INCH|\b)', u_title)
    size = int(size_m.group(1)) if size_m else 55
    if size < 22:
        return None
        
    model_code = None
    # 1. First look for full Samsung/LG model code patterns in title
    m_cand = re.search(r'\b([A-Z0-9]{2}\d{2,3}[A-Z0-9]{3,12}|\d{2,3}[A-Z]{3,6}\d{2}[A-Z0-9]{1,6}|OLED\d{2}[A-Z0-9]{2,8}|MRE\d{2,3}[A-Z0-9]{2,6}|QE\d{2}[A-Z0-9]{2,8}|UE\d{2}[A-Z0-9]{2,12})\b', u_title)
    if m_cand and any(c.isdigit() for c in m_cand.group(1)):
        model_code = m_cand.group(1)
    else:
        dash_m = re.search(r'-\s*([A-Z0-9]{5,15})', u_title)
        if dash_m and any(c.isdigit() for c in dash_m.group(1)):
            model_code = dash_m.group(1)
        else:
            model_code = "Unknown"
        
    if model_code.upper() in ["MONTH", "CLAIM", "TRADE", "STARS", "SAMSUNG", "LG", "UNKNOWN", "TELEVISION", "OFFER", "REVIEWS", "WHITE", "BLACK", "SILVER"]:
        return None
        
    year = 2025
    if any(x in u_title for x in ['2026', ' H', 'B6', 'C6', 'G6', 'S90H', 'S95H', 'S85H', 'S99H', 'QN80H', 'QN70H', 'M70H', 'M80H', 'R85H', 'R95H', 'QNED86B', 'QNED80B', 'QNED72B', 'QNED83B', 'MRGB88B', 'MRGB96B', 'NU85', 'NU80']):
        year = 2026
    elif any(x in u_title for x in ['2025', ' F', 'B5', 'C5', 'G5', 'S90F', 'S95F', 'QN90F', 'QN80F', 'QN70F', 'Q7F', 'Q8F', 'QNED86A', 'QNED80A', 'QNED70A', 'UA75', 'LX7']):
        year = 2025
    elif any(x in u_title for x in ['2024', ' D', 'B4', 'C4', 'G4', 'S90D']):
        year = 2024
        
    if year < 2025:
        return None
        
    display = 'OLED' if 'OLED' in u_title else ('MICRO RGB' if ('MICRO RGB' in u_title or 'MRGB' in u_title or 'R85' in u_title or 'R95' in u_title) else ('QNED' if 'QNED' in u_title else ('QLED' if ('QLED' in u_title or 'NEO QLED' in u_title) else 'UHD 4K')))
    
    # 1. Primary: Extract directly from Currys price DOM elements
    selling_price = None
    val_span = tile.select_one('.price-info .sales .value, .sales .value')
    if val_span:
        try:
            c_val = val_span.get('content')
            if c_val:
                selling_price = float(c_val.replace(',', ''))
            else:
                selling_price = float(val_span.get_text(strip=True).replace('£', '').replace(',', ''))
        except Exception:
            pass
            
    # 2. Fallback: Parse from lines if DOM extraction didn't catch price
    lines = [line.strip() for line in tile.get_text('\n').splitlines() if line.strip()]
    if not selling_price:
        for i, l in enumerate(lines):
            p_match = re.match(r'^£([\d,]+(?:\.\d{2})?)$', l)
            if p_match:
                val = float(p_match.group(1).replace(',', ''))
                # Avoid monthly payment line (which is preceded by 'From' or followed by 'per month')
                is_monthly = False
                if i > 0 and lines[i-1].lower() == 'from':
                    is_monthly = True
                if i + 1 < len(lines) and 'month' in lines[i+1].lower():
                    is_monthly = True
                if not is_monthly:
                    selling_price = val
                    break

    if not selling_price or selling_price < 80.0:
        return None

    save_amount = None
    save_span = tile.select_one('.primary-save-price')
    if save_span:
        try:
            save_amount = float(save_span.get_text(strip=True).replace('£', '').replace(',', ''))
        except Exception:
            pass

    was_price = None
    was_div = tile.select_one('.price-date')
    if was_div:
        was_m = re.search(r'Was\s*£([\d,]+(?:\.\d{2})?)', was_div.get_text())
        if was_m:
            was_price = float(was_m.group(1).replace(',', ''))

    promo_lines = []
    for i, l in enumerate(lines):
        if not save_amount:
            save_m = re.match(r'^Save\s*£([\d,]+(?:\.\d{2})?)', l, re.I)
            if save_m:
                save_amount = float(save_m.group(1).replace(',', ''))
            elif l == "Save" and i + 1 < len(lines):
                save_m2 = re.match(r'^£([\d,]+(?:\.\d{2})?)$', lines[i+1])
                if save_m2:
                    save_amount = float(save_m2.group(1).replace(',', ''))
                    
        if not was_price:
            was_m = re.search(r'Was\s*£([\d,]+(?:\.\d{2})?)', l, re.I)
            if was_m:
                was_price = float(was_m.group(1).replace(',', ''))
            
        if any(x in l.lower() for x in ["trade-in", "trade in", "cashback", "soundbar", "code", "off this tv"]):
            if not l.startswith("From £") and not l.startswith("£") and not l.startswith("Was £"):
                promo_lines.append(l)

    if save_amount and (save_amount > 2500 or save_amount > selling_price * 2):
        save_amount = None
        
    orig_price = None
    if was_price and was_price > selling_price and was_price < selling_price * 3:
        orig_price = was_price
    elif save_amount:
        orig_price = round(selling_price + save_amount, 2)
        
    if not passes_uk_price_guard(display, size, selling_price):
        return None
        
    clean_promos = []
    if save_amount:
        clean_promos.append(f"Save GBP {save_amount:.2f}")
    for pl in promo_lines:
        if "+more offers" in pl or pl.startswith("+"): continue
        ti_m = re.search(r'Get £(\d+)\s*off.*?trade-in.*?(?:Use\s*([A-Z0-9]+))?', pl, re.I)
        if ti_m:
            code_str = f" (Code: {ti_m.group(2)})" if ti_m.group(2) else ""
            clean_promos.append(f"Trade-in GBP {ti_m.group(1)} off{code_str}")
            continue
        sb_m = re.search(r'(?:Free|Get)\s*([^.]+?Soundbar[^.]*)', pl, re.I)
        if sb_m:
            clean_promos.append(sb_m.group(0).strip())
            continue
        cb_m = re.search(r'£(\d+)\s*cashback', pl, re.I)
        if cb_m:
            clean_promos.append(f"GBP {cb_m.group(1)} Cashback")
            continue
        if len(pl) < 80:
            clean_promos.append(pl)
            
    promo_str = '; '.join(dict.fromkeys(clean_promos)) if clean_promos else "None"
    
    a_tag = tile.find('a', href=re.compile(r'/products/'))
    href = a_tag.get('href', '') if a_tag else ''
    if href and not href.startswith('http'):
        href = 'https://www.currys.co.uk' + href
        
    return {
        'brand': brand.capitalize(),
        'year': year,
        'display': display,
        'size': size,
        'model_code': model_code,
        'price': selling_price,
        'orig_price': orig_price,
        'shipping': 'Free',
        'cashback': 0,
        'promo': promo_str,
        'title': title_line,
        'link': href
    }

def scrape_brand_live(brand):
    print(f"\n==================================================")
    print(f" 🇬🇧 SCRAPING LIVE CURRYS UK: {brand.upper()} ")
    print(f"==================================================")
    slug = brand.lower()
    seen = {}
    
    # Traverse pages: 0, 20, 40, ... up to 200 (10 pages)
    for start in range(0, 220, 20):
        url = f"https://www.currys.co.uk/tv-and-audio/televisions/tvs/{slug}?start={start}&sz=20"
        print(f"  ➔ Fetching page (start={start})...", end=" ")
        try:
            r = requests.get(url, impersonate="chrome124", timeout=15)
            if r.status_code != 200:
                print(f"Status {r.status_code}, stopping.")
                break
                
            soup = BeautifulSoup(r.text, 'html.parser')
            tiles = soup.find_all('div', class_=lambda c: c and 'product-tile' in c and 'pt-md-0' in c)
            if not tiles:
                print("0 tiles found, end of listings.")
                break
                
            page_added = 0
            for t in tiles:
                rec = parse_currys_tile(t, brand)
                if rec:
                    mc = rec["model_code"]
                    if mc not in seen or rec["price"] < seen[mc]["price"]:
                        seen[mc] = rec
                        page_added += 1
            print(f"Found {len(tiles)} tiles | Extracted {page_added} valid models (Running total: {len(seen)})")
            time.sleep(1.0)
        except Exception as e:
            print(f"Error: {e}")
            break
            
    print(f"✅ Total unique live {brand} models extracted: {len(seen)}")
    return seen

def main():
    print("=" * 65)
    print(" 🇬🇧 CURRYS UK LIVE PRICE SURVEY & PIPELINE SYNCHRONIZER ")
    print("=" * 65)
    
    # 1. Scrape live from Currys UK
    live_samsung = scrape_brand_live("Samsung")
    live_lg = scrape_brand_live("LG")
    
    # 2. Reconcile with verified catalog continuity baseline (09/01)
    # If any non-promoted models from catalog were not captured on search pages, supplement them with verified baseline
    wb_01_path = os.path.join(ROOT_DIR, "History_EU", "2026 0901", "price tracker_EU_2026 0901_v1.xlsx")
    if os.path.exists(wb_01_path):
        wb_01 = openpyxl.load_workbook(wb_01_path, data_only=True)
        for brand, s_name, live_dict in [("Samsung", "Currys_UK_SAMSUNG_Full", live_samsung), ("LG", "Currys_UK_LG_Full", live_lg)]:
            ws = wb_01[s_name]
            added_from_base = 0
            for r in range(2, ws.max_row + 1):
                vals = [ws.cell(r, c).value for c in range(1, 11)]
                mc = str(vals[4]).strip() if vals[4] else ""
                if mc and mc not in live_dict and mc.upper() != "UNKNOWN":
                    # Strictly probe Currys live to get current price and availability (Zero Historical Price Injection)
                    probe_url = f"https://www.currys.co.uk/search?q={brand}%20{mc}"
                    try:
                        pr = requests.get(probe_url, impersonate="chrome124", timeout=10)
                        if pr.status_code == 200:
                            psoup = BeautifulSoup(pr.text, 'html.parser')
                            ptiles = psoup.find_all('div', class_=lambda c: c and 'product-tile' in c and 'pt-md-0' in c)
                            for pt in ptiles:
                                prec = parse_currys_tile(pt, brand)
                                if prec and (prec["model_code"] == mc or mc in prec["model_code"]):
                                    live_dict[mc] = prec
                                    added_from_base += 1
                                    break
                        time.sleep(0.3)
                    except Exception:
                        pass
            print(f"Catalog continuity for {brand}: {added_from_base} unlisted models verified and added live (Total: {len(live_dict)})")

    # 3. Save clean JSON datasets
    final_s = sorted(list(live_samsung.values()), key=lambda x: (x["year"], x["size"], x["price"]), reverse=True)
    final_l = sorted(list(live_lg.values()), key=lambda x: (x["year"], x["size"], x["price"]), reverse=True)
    
    out_s = os.path.join(DATA_DIR, "raw_currys_samsung.json")
    with open(out_s, "w", encoding="utf-8") as f:
        json.dump(final_s, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Saved {len(final_s)} models to {out_s}")
    
    out_l = os.path.join(DATA_DIR, "raw_currys_lg.json")
    with open(out_l, "w", encoding="utf-8") as f:
        json.dump(final_l, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(final_l)} models to {out_l}")
    
    # 4. Sync to 0907 Workbook
    wb_07_path = os.path.join(DATA_DIR, "price tracker_EU_2026 0907_v1.xlsx")
    if os.path.exists(wb_07_path):
        wb_07 = openpyxl.load_workbook(wb_07_path)
        for brand, sheetname, dataset in [("Samsung", "Currys_UK_SAMSUNG_Full", final_s), ("LG", "Currys_UK_LG_Full", final_l)]:
            if sheetname not in wb_07.sheetnames:
                ws = wb_07.create_sheet(sheetname)
            else:
                ws = wb_07[sheetname]
                
            headers = [
                "Brand", "Model Year", "Display Type", "Size (Inch)", "Model Code",
                "Price (GBP)", "Shipping", "Installment", "Cashback", "General Promotions"
            ]
            while ws.max_row > 1:
                ws.delete_rows(ws.max_row)
            if ws.max_row == 0:
                ws.append(headers)
            else:
                for c, h in enumerate(headers, 1):
                    ws.cell(1, c).value = h
                    
            for it in dataset:
                ws.append([
                    it["brand"], it["year"], it["display"], it["size"], it["model_code"],
                    it["price"], it["shipping"], None, it["cashback"], it["promo"]
                ])
            print(f"  ➔ Updated {sheetname} in 0907 workbook: {len(dataset)} rows written.")
            
        wb_07.save(wb_07_path)
        print(f"✅ Saved updated workbook to {wb_07_path}")
        
        # Mirror to History_EU 0907
        hist_dir = os.path.join(ROOT_DIR, "History_EU", "2026 0907")
        os.makedirs(hist_dir, exist_ok=True)
        hist_file = os.path.join(hist_dir, "price tracker_EU_2026 0907_v1.xlsx")
        shutil.copyfile(wb_07_path, hist_file)
        print(f"✅ Mirrored to {hist_file}")
        
    print("\n[CURRYS LIVE SURVEY COMPLETED SUCCESSFULLY]")

if __name__ == "__main__":
    main()
