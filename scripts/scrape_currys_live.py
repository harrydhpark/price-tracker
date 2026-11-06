import os, sys, json, re, time, shutil
from bs4 import BeautifulSoup
from scrapling.fetchers import StealthySession

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
MASTER_URLS_PATH = os.path.join(DATA_DIR, "master_product_urls.json")

from core.run_context import init_run_context, stamp

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

def extract_currys_metadata(title_line, brand, fallback_mc=None, fallback_size=None):
    u_title = title_line.upper()
    if any(x in u_title for x in ["SOUNDBAR", "SOUND BAR", "BUNDLE", "MONITOR", "ODYSSEY", "ULTRAGEAR", "REMOTE", "PROJECTOR", "BEAMER", "CABLE", "REFURBISHED"]):
        return None
    if any(x in u_title for x in ["WALL BRACKET", "FLOOR STAND"]):
        return None
    if ("WALL MOUNT" in u_title or "STAND" in u_title) and not ("VERSION" in u_title or "SMART TV" in u_title or "OLED" in u_title or "QNED" in u_title or "QLED" in u_title):
        return None

    model_code = "Unknown"
    m_cand = re.search(r'\b([A-Z0-9]{2}\d{2,3}[A-Z0-9]{3,12}|\d{2,3}[A-Z]{3,6}\d{2}[A-Z0-9]{1,6}|OLED\d{2}[A-Z0-9]{2,8}|MRE\d{2,3}[A-Z0-9]{2,6}|QE\d{2,3}[A-Z0-9]{2,8}|UE\d{2,3}[A-Z0-9]{2,12})\b', u_title)
    if m_cand and any(c.isdigit() for c in m_cand.group(1)):
        model_code = m_cand.group(1)
    else:
        dash_m = re.search(r'-\s*([A-Z0-9]{5,15})', u_title)
        if dash_m and any(c.isdigit() for c in dash_m.group(1)):
            model_code = dash_m.group(1)
        elif fallback_mc:
            model_code = str(fallback_mc).strip().upper()
        else:
            model_code = "Unknown"

    if model_code.upper() in ["MONTH", "CLAIM", "TRADE", "STARS", "SAMSUNG", "LG", "UNKNOWN", "TELEVISION", "OFFER", "REVIEWS", "WHITE", "BLACK", "SILVER"]:
        if fallback_mc and fallback_mc.upper() not in ["UNKNOWN", "SAMSUNG", "LG"]:
            model_code = fallback_mc.upper()
        else:
            return None

    size_m = re.search(r'\b(115|100|98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"\'\'-]*(?:INCH|\b)', u_title)
    if size_m:
        size = int(size_m.group(1))
    else:
        c_sz = re.search(r'(?:^|[A-Z]{1,3})(\d{2,3})(?:[A-Z]|$)', model_code)
        if c_sz and int(c_sz.group(1)) in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
            size = int(c_sz.group(1))
        elif fallback_size:
            size = int(fallback_size)
        else:
            size = 55
    if size < 22:
        return None

    year = None
    check_str = f"{u_title} {model_code.upper()}"
    if any(x in check_str for x in ['2026', ' H', 'B6', 'C6', 'G6', 'S90H', 'S95H', 'S85H', 'S99H', 'QN80H', 'QN70H', 'QN85H', 'QN90H', 'QN95H', 'QN800H', 'QN900H', 'M70H', 'M80H', 'R85H', 'R95H', 'U8000H', 'U8090H', 'U9000H', 'LS03H', 'QNED86B', 'QNED85B', 'QNED82B', 'QNED81B', 'QNED80B', 'QNED72B', 'QNED70B', 'QNED83B', 'MRGB88B', 'MRGB96B', 'MRGB86B', 'NU85', 'NU80', 'UA77', 'LX6']):
        year = 2026
    elif any(x in check_str for x in ['2025', ' F', 'B5', 'C5', 'G5', 'M5', 'S90F', 'S95F', 'S85F', 'QN90F', 'QN85F', 'QN80F', 'QN70F', 'QN95F', 'QN800F', 'QN900F', 'Q7F', 'Q8F', 'U8000F', 'U8090F', 'LS03F', 'QNED93A', 'QNED86A', 'QNED85A', 'QNED82A', 'QNED81A', 'QNED80A', 'QNED70A', 'NANO81A', 'NANO80A', 'UA75', 'UA73', 'LX7']):
        year = 2025
    elif any(x in check_str for x in ['2024', ' D', 'B4', 'C4', 'G4', 'S90D', 'S95D', 'QN90D', 'QN85D']):
        year = 2024
    else:
        # Check Samsung year letter after index 2
        if brand.upper() == "SAMSUNG" and len(model_code) > 4:
            sub = model_code[2:].upper()
            if "H" in sub: year = 2026
            elif "F" in sub: year = 2025
            elif "D" in sub: year = 2024
        elif brand.upper() == "LG":
            if re.search(r'(?:OLED\d{2}[BCGM]6|QNED\d{2}B|MRGB\d{2}B|UA77)', model_code.upper()):
                year = 2026
            elif re.search(r'(?:OLED\d{2}[BCGM]5|QNED\d{2}A|NANO\d{2}A|UA7[345])', model_code.upper()):
                year = 2025

    if not year or year < 2025:
        return None

    is_oled = bool(re.search(r'\bOLED', check_str)) and not bool(re.search(r'QNED|NANO|NU8', model_code.upper()))
    display = 'OLED' if is_oled else ('MICRO RGB' if ('MICRO RGB' in check_str or 'MRGB' in check_str or 'R85' in check_str or 'R95' in check_str) else ('QNED' if 'QNED' in check_str else ('QLED' if ('QLED' in check_str or 'NEO QLED' in check_str or 'QN' in model_code.upper()) else 'UHD 4K')))
    return model_code, size, year, display

def parse_currys_tile(tile, brand, page_url=""):
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
        
    meta = extract_currys_metadata(title_line, brand)
    if not meta:
        return None
    model_code, size, year, display = meta
    
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
            
    lines = [line.strip() for line in tile.get_text('\n').splitlines() if line.strip()]
    if not selling_price:
        for i, l in enumerate(lines):
            p_match = re.match(r'^£([\d,]+(?:\.\d{2})?)$', l)
            if p_match:
                val = float(p_match.group(1).replace(',', ''))
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
        
    rec = {
        'brand': 'Samsung' if brand.upper() == 'SAMSUNG' else 'LG',
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
        'link': href or page_url
    }
    return stamp(rec, engine="scrapling_stealthy", source_type="list", http_status=200, source_url=href or page_url)

def parse_currys_pdp(html, url, brand, fallback_mc=None, fallback_size=None):
    if not html or len(html) < 10000:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    
    # 1. Check JSON-LD availability & price fallback
    ld_price = None
    for s in soup.find_all('script', type='application/ld+json'):
        if not s.string:
            continue
        try:
            d = json.loads(s.string)
            items = d if isinstance(d, list) else [d]
            for it in items:
                if isinstance(it, dict) and it.get('@type') == 'Product':
                    offers = it.get('offers')
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    if isinstance(offers, dict):
                        avail = str(offers.get('availability', '')).lower()
                        if 'outofstock' in avail or 'discontinued' in avail:
                            return None
                        if offers.get('price'):
                            ld_price = float(str(offers['price']).replace(',', ''))
        except Exception:
            pass

    # Check explicit out-of-stock / unavailable message on PDP
    oos_el = soup.select_one('.out-of-stock, .unavailable-msg')
    if oos_el and any(x in oos_el.get_text().lower() for x in ['out of stock', 'no longer available']):
        return None
    body_txt = soup.get_text(' ', strip=True)
    if "Sorry, this product is no longer available" in body_txt or "Out of stock for home delivery" in body_txt:
        return None

    h1 = soup.select_one('h1.product-name, h1')
    if not h1:
        return None
    title_line = h1.get_text(' ', strip=True)
    if brand.upper() not in title_line.upper():
        return None

    meta = extract_currys_metadata(title_line, brand, fallback_mc=fallback_mc, fallback_size=fallback_size)
    if not meta:
        return None
    model_code, size, year, display = meta

    selling_price = None
    val_span = soup.select_one('.pdp-price .sales .value, .price-info .sales .value, .sales .value')
    if val_span:
        try:
            c_val = val_span.get('content')
            if c_val:
                selling_price = float(str(c_val).replace(',', ''))
            else:
                selling_price = float(val_span.get_text(strip=True).replace('£', '').replace(',', ''))
        except Exception:
            pass
    if not selling_price and ld_price:
        selling_price = ld_price

    if not selling_price or selling_price < 80.0:
        return None

    save_amount = None
    save_span = soup.select_one('.primary-save-price')
    if save_span:
        try:
            save_amount = float(re.sub(r'[^\d.]', '', save_span.get_text(strip=True).replace(',', '')))
        except Exception:
            pass

    was_price = None
    was_div = soup.select_one('.price-date, .was-price')
    if was_div:
        was_m = re.search(r'Was\s*£([\d,]+(?:\.\d{2})?)', was_div.get_text())
        if was_m:
            was_price = float(was_m.group(1).replace(',', ''))

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
    promo_str = '; '.join(dict.fromkeys(clean_promos)) if clean_promos else "None"

    rec = {
        'brand': 'Samsung' if brand.upper() == 'SAMSUNG' else 'LG',
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
        'link': url
    }
    return stamp(rec, engine="scrapling_stealthy", source_type="pdp", http_status=200, source_url=url)

def main():
    init_run_context()
    start_time = time.time()
    print("=" * 65)
    print(" 🇬🇧 CURRYS UK ZERO-FIRECRAWL LIVE SURVEY (LISTINGS + MASTER PDPs) ")
    print("=" * 65)

    # Build URL list: 11 Samsung listing pages + 11 LG listing pages + all UK master PDP URLs
    samsung_list_urls = [f"https://www.currys.co.uk/tv-and-audio/televisions/tvs/samsung?start={s}&sz=20" for s in range(0, 220, 20)]
    lg_list_urls = [f"https://www.currys.co.uk/tv-and-audio/televisions/tvs/lg?start={s}&sz=20" for s in range(0, 220, 20)]

    uk_master_items = []
    if os.path.exists(MASTER_URLS_PATH):
        with open(MASTER_URLS_PATH, "r", encoding="utf-8") as f:
            master = json.load(f)
        for k, v in master.items():
            if v.get("country") == "UK" and v.get("url"):
                uk_master_items.append(v)

    all_urls = list(dict.fromkeys(samsung_list_urls + lg_list_urls + [v["url"] for v in uk_master_items]))
    print(f"  ➔ Preparing in-browser batch fetch for {len(all_urls)} Currys URLs ({len(samsung_list_urls)+len(lg_list_urls)} listing pages + {len(uk_master_items)} registered PDPs)...")

    fetched_map = {}

    def batch_fetch_action(page):
        js = """
        async (urls) => {
            const out = {};
            const batchSize = 8;
            for (let i = 0; i < urls.length; i += batchSize) {
                const batch = urls.slice(i, i + batchSize);
                await Promise.all(batch.map(async (u) => {
                    try {
                        const r = await fetch(u, {credentials: 'include'});
                        const txt = await r.text();
                        out[u] = {status: r.status, html: txt};
                    } catch (e) {
                        out[u] = {status: 0, html: '', err: String(e)};
                    }
                }));
            }
            return out;
        }
        """
        res = page.evaluate(js, all_urls)
        fetched_map.update(res)

    with StealthySession(headless=False, solve_cloudflare=True, timeout=90000) as session:
        session.fetch(
            "https://www.currys.co.uk/tv-and-audio/televisions/tvs/samsung",
            solve_cloudflare=True,
            wait=2000,
            page_action=batch_fetch_action
        )

    print(f"  ✔ Fetched {len(fetched_map)} URLs in {time.time()-start_time:.1f}s!")

    live_samsung = {}
    live_lg = {}

    # 1. Parse listing pages
    for brand, url_list, target_dict in [("Samsung", samsung_list_urls, live_samsung), ("LG", lg_list_urls, live_lg)]:
        for u in url_list:
            info = fetched_map.get(u, {})
            if info.get("status") != 200 or not info.get("html"):
                continue
            soup = BeautifulSoup(info["html"], "html.parser")
            tiles = soup.find_all('div', class_=lambda c: c and 'product-tile' in c and 'pt-md-0' in c)
            for t in tiles:
                rec = parse_currys_tile(t, brand, page_url=u)
                if rec:
                    mc = rec["model_code"]
                    if mc not in target_dict or rec["price"] < target_dict[mc]["price"]:
                        target_dict[mc] = rec

    print(f"  ➔ From listing pages: Samsung={len(live_samsung)}, LG={len(live_lg)}")

    # 2. Parse registered PDP pages (PDP overrides listing price for exact SKU accuracy!)
    pdp_added_s = 0
    pdp_added_l = 0
    for item in uk_master_items:
        u = item["url"]
        b = item.get("brand", "Samsung")
        mc_hint = item.get("model_code")
        sz_hint = item.get("size")
        info = fetched_map.get(u, {})
        if info.get("status") != 200 or not info.get("html"):
            continue
        rec = parse_currys_pdp(info["html"], u, b, fallback_mc=mc_hint, fallback_size=sz_hint)
        if rec:
            mc = rec["model_code"]
            if b.upper() == "SAMSUNG":
                if mc not in live_samsung:
                    pdp_added_s += 1
                live_samsung[mc] = rec
            else:
                if mc not in live_lg:
                    pdp_added_l += 1
                live_lg[mc] = rec

    print(f"  ➔ After live PDP verification: Samsung={len(live_samsung)} (+{pdp_added_s} from PDP), LG={len(live_lg)} (+{pdp_added_l} from PDP)")

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

    print("\n[CURRYS LIVE SURVEY COMPLETED SUCCESSFULLY]")

    try:
        from scrape_logger import emit_summary
        elapsed = round(time.time() - start_time, 2)
        emit_summary(country="UK", retailer="Currys", brand="SAMSUNG", total_extracted=len(final_s), final_deduplicated=len(final_s), execution_time_sec=elapsed)
        emit_summary(country="UK", retailer="Currys", brand="LG", total_extracted=len(final_l), final_deduplicated=len(final_l), execution_time_sec=elapsed)
    except Exception:
        pass

if __name__ == "__main__":
    main()
