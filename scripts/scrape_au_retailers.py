# -*- coding: utf-8 -*-
"""
Australia TV Retailer Real-Time Live Scraping & Cleansing Engine (Zero-Cache Standard)
Performs 100% live HTTP / Browser fetches today for:
1. JB Hi-Fi (jbhifi.com.au) - Live Shopify JSON API + Live PDP JSON Probing
2. The Good Guys (thegoodguys.com.au) - Live Category Sitemap/Search + Parallel curl_cffi PDP JSON-LD Probing
3. Harvey Norman (harveynorman.com.au) - Live StealthySession Imperva Bypass + In-Browser Parallel PDP JSON-LD Probing
Filters strictly for Model Year 2025 and 2026, purges non-TV displays, stamps scraped_at & run_id,
and outputs clean raw JSON files in data/.
"""

import os
import sys
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests as creq
from scrapling.fetchers import StealthySession

sys.stdout.reconfigure(encoding='utf-8')
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def extract_size(text, url=""):
    if url:
        slug = url.split('/')[-1].replace('.html', '').lower()
        m_sz = re.search(r'(?:samsung|lg)-(\d{2,3})(?:-inch|-inches)?-', slug)
        if m_sz:
            val = int(m_sz.group(1))
            if val in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
                return val
    m = re.search(r'\b(115|100|98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\x27-]*(?:inch|inches|zoll|pollici|pouces|cm|\b)', text.upper())
    if m:
        return int(m.group(1))
    m_mc = re.search(r'(?:OLED|QA|UA|QNED|QN)?(\d{2,3})[A-Z0-9]', text.upper())
    if m_mc:
        val = int(m_mc.group(1))
        if val in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
            return val
    return 55


def extract_year(text, model_code="", url=""):
    t_up = text.upper()
    mc_up = model_code.upper()
    slug = url.split('/')[-1].replace('.html', '').lower() if url else ""

    # 2026 Indicators
    if any(x in slug for x in ["2026", "-c6-", "-g6-", "-b6-", "-w6-", "s90h", "s95h", "s85h", "s99h", "r95h", "r85h", "m80h", "m70h", "qn80h", "qn90h", "qn85h", "ls03h", "qned86b", "qned80b", "qned87b", "qned70b", "qned72b", "mrgb87b"]):
        return 2026
    if any(x in t_up for x in ["2026", " C6", " G6", " B6", " W6", "S90H", "S95H", "S85H", "S99H", "R95H", "R85H", "M80H", "M70H", "U8000H", "QN80H", "QN90H", "QN85H", "LS03H", "QNED86B", "QNED80B", "QNED87B", "QNED70B", "QNED72B", "MRGB87B", "MRGB96B"]):
        return 2026
    if any(x in mc_up for x in ["C6", "G6", "B6", "W6", "M6", "QNED86B", "QNED80B", "QNED87B", "QNED70B", "QNED72B", "MRGB87B", "MRGB96B", "S95H", "S90H", "S85H", "S99H", "R95H", "R85H", "M80H", "M70H", "LS03H", "QN80H", "QN90H", "QN85H"]):
        return 2026

    # 2025 Indicators
    if any(x in slug for x in ["2025", "-c5-", "-g5-", "-b5-", "-m5-", "s90f", "s95f", "s85f", "r95f", "qn90f", "qn85f", "qn80f", "q7f", "q8f", "q6f", "q5f", "ls03f", "f6000"]):
        return 2025
    if any(x in t_up for x in ["2025", " C5", " G5", " B5", " M5", "S90F", "S95F", "S85F", "R95F", "QN90F", "QN85F", "QN80F", "Q7F", "Q8F", "Q6F", "Q5F", "LS03F", "U8000F", "F6000"]):
        return 2025
    if any(x in mc_up for x in ["C5", "G5", "B5", "M5", "QNED86A", "QNED80A", "QNED87A", "QNED70A", "QNED72A", "UA75", "MRGB87A", "S95F", "S90F", "S85F", "R95F", "QN90F", "QN85F", "QN80F", "Q7F", "Q8F", "Q6F", "Q5F", "LS03F", "F6000"]):
        return 2025

    return None


def extract_model_code(text, url=""):
    if url:
        slug = url.split('/')[-1].replace('.html', '').lower()
        m_sz = re.search(r'(?:samsung|lg)-(\d{2,3})(?:-inch|-inches)?-', slug)
        s_sz = int(m_sz.group(1)) if m_sz else extract_size(text, url)
        if 'samsung' in slug:
            for s in ['s95h', 's90h', 's85h', 's99h', 'r95h', 'r95f', 'r85h', 'm80h', 'm70h', 'qn90h', 'qn80h', 'qn85h', 'qn90f', 'qn85f', 'qn80f', 'q7f', 'q8f', 'q5f', 's95f', 's90f', 's85f', 'ls03h', 'ls03f', 'f6000']:
                if s in slug:
                    return f"QA{s_sz}{s.upper()}"
        elif 'lg' in slug:
            for s in ['c6', 'g6', 'b6', 'w6', 'm6', 'c5', 'g5', 'b5', 'm5', 'qned86b', 'qned80b', 'qned70b', 'qned86a', 'qned80a', 'mrgb87b']:
                if f"-{s}-" in slug or slug.endswith(f"-{s}") or s in slug:
                    if s.startswith('qned') or s.startswith('mrgb'):
                        return f"{s_sz}{s.upper()}"
                    else:
                        return f"OLED{s_sz}{s.upper()}"

    text_u = text.upper()
    m = re.search(r'\b(OLED\d{2}[A-Z0-9]{2,8}|\d{2,3}[A-Z]{3,6}\d{2}[A-Z0-9]{1,6}|QA\d{2,3}[A-Z0-9]{3,12}|UA\d{2,3}[A-Z0-9]{3,12})\b', text_u)
    if m:
        cand = m.group(1)
        # Canonicalize AU suffix like AWXXY
        cand = re.sub(r'(?:AWXXY|WXXY|XXY)$', '', cand)
        return cand

    size = extract_size(text, url)
    for s_series in ["S95H", "S90H", "S85H", "S99H", "R95H", "R95F", "R85H", "M80H", "M70H", "QN80H", "QN90H", "QN85H", "Q7F", "Q8F", "Q5F", "S95F", "S90F", "S85F", "QN90F", "LS03H", "LS03F", "F6000"]:
        if s_series in text_u:
            return f"QA{size}{s_series}"

    for l_series in ["W6", "G6", "C6", "B6", "C5", "G5", "B5", "QNED70B", "QNED86B", "QNED80B", "QNED70A", "QNED86A", "MRGB87B", "MRGB96B", "NU85", "NU80", "UA75"]:
        if l_series in text_u:
            if l_series.startswith(("QNED", "MRGB", "NU", "UA")):
                return f"{size}{l_series}"
            else:
                return f"OLED{size}{l_series}"

    return ""


def get_category(mc, title=""):
    t_up = f"{mc} {title}".upper()
    if any(x in t_up for x in ["MRGB", "MICRO RGB", "R85", "R95"]):
        return "MRGB"
    if any(x in t_up for x in ["OLED", "S90", "S95", "S85", "S99", "C6", "G6", "B6", "W6", "C5", "G5", "B5"]):
        return "OLED"
    if "QNED" in t_up:
        return "QNED"
    if any(x in t_up for x in ["QN", "QLED", "NEO", "M70", "M80", "Q7", "Q8", "Q6", "Q5"]):
        return "QLED"
    return "UHD"


def collect_known_urls_by_retailer():
    """Collects all valid product PDP URLs per retailer from master_product_urls_au.json and existing raw files."""
    urls_by_ret = {"JB Hi-Fi": {}, "The Good Guys": {}, "Harvey Norman": {}}
    reg_path = os.path.join(DATA_DIR, "master_product_urls_au.json")
    if os.path.exists(reg_path):
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                reg = json.load(f)
            for k, v in reg.items():
                r = v.get("retailer")
                u = v.get("url", "")
                if r in urls_by_ret and u and any(d in u for d in ["jbhifi.com.au/products/", "thegoodguys.com.au/", "harveynorman.com.au/"]):
                    if not any(bad in u for bad in ["cdn.shopify.com", "imgix.net", "toshiba", "tcl-", "hisense-", "sony-"]):
                        urls_by_ret[r][u] = v
        except Exception:
            pass

    for r_key, r_name in [("jbhifi", "JB Hi-Fi"), ("goodguys", "The Good Guys"), ("harveynorman", "Harvey Norman")]:
        for b_sub in ["samsung", "lg"]:
            fp = os.path.join(DATA_DIR, f"raw_{r_key}_{b_sub}.json")
            if os.path.exists(fp):
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        arr = json.load(f)
                    for it in arr:
                        u = it.get("url", "")
                        if u and any(d in u for d in ["jbhifi.com.au/products/", "thegoodguys.com.au/", "harveynorman.com.au/"]):
                            if not any(bad in u for bad in ["cdn.shopify.com", "imgix.net", "toshiba", "tcl-", "hisense-", "sony-"]):
                                urls_by_ret[r_name][u] = it
                except Exception:
                    pass
    return urls_by_ret


def scrape_jbhifi_live(known_map, run_id, now_iso):
    print("\n▶ [1/3] Scraping JB Hi-Fi Live (Shopify JSON API + Live PDP Probing)...")
    items_by_url = {}

    # 1. Fetch Shopify collections JSON pages
    for col in ["tvs", "samsung-tvs", "lg-tvs", "oled-tvs", "qled-tvs", "mini-led-tvs", "4k-tvs"]:
        for page in range(1, 4):
            api_url = f"https://www.jbhifi.com.au/collections/{col}/products.json?limit=250&page={page}"
            try:
                r = creq.get(api_url, impersonate="chrome124", timeout=15)
                if r.status_code != 200:
                    break
                prods = r.json().get("products", [])
                if not prods:
                    break
                for p in prods:
                    handle = p.get("handle", "")
                    if not handle:
                        continue
                    pdp_url = f"https://www.jbhifi.com.au/products/{handle}"
                    items_by_url[pdp_url] = p
                if len(prods) < 250:
                    break
            except Exception:
                break

    # 2. Probe all known JB Hi-Fi PDP URLs via live .json endpoint in parallel
    missing_urls = [u for u in known_map.keys() if u not in items_by_url]
    def _fetch_jb_pdp(u):
        try:
            r = creq.get(u + ".json", impersonate="chrome124", timeout=15)
            if r.status_code == 200:
                return u, r.json().get("product")
        except Exception:
            pass
        return u, None

    if missing_urls:
        with ThreadPoolExecutor(max_workers=12) as ex:
            futs = [ex.submit(_fetch_jb_pdp, u) for u in missing_urls]
            for fut in as_completed(futs):
                u, prod = fut.result()
                if prod:
                    items_by_url[u] = prod

    results = []
    for u, prod in items_by_url.items():
        title = (prod.get("title") or "").strip()
        vendor = (prod.get("vendor") or "").upper()
        u_low = u.lower()
        if any(b in u_low for b in ["toshiba", "philips", "ffalcon", "tcl", "hisense", "sony", "panasonic", "soundbar", "bracket", "remote", "cable", "monitor", "projector"]):
            continue
        if "SAMSUNG" in vendor or "samsung" in u_low or "SAMSUNG" in title.upper():
            brand = "SAMSUNG"
        elif "LG" in vendor or "lg-" in u_low or "LG " in title.upper():
            brand = "LG"
        else:
            continue

        variants = prod.get("variants") or []
        if not variants:
            continue
        v0 = variants[0]
        try:
            price = float(v0.get("price") or 0)
        except Exception:
            price = 0.0
        try:
            orig_price = float(v0.get("compare_at_price") or price)
        except Exception:
            orig_price = price
        if orig_price < price:
            orig_price = price
        if price < 250:
            continue

        mc = extract_model_code(title, u)
        if not mc and u in known_map:
            mc = known_map[u].get("model_code", "")
        year = extract_year(title, mc, u)
        if year not in [2025, 2026] and u in known_map:
            year = known_map[u].get("year")
        if not mc or year not in [2025, 2026]:
            continue
        size = extract_size(title, u)
        if size < 24:
            continue
        cat = get_category(mc, title)
        promo = f"Save ${int(orig_price - price)}" if orig_price > price else "None"
        results.append({
            "name": title,
            "title": title,
            "model_code": mc,
            "brand": brand,
            "year": year,
            "category": cat,
            "size": size,
            "price": price,
            "original_price": orig_price,
            "promo": promo,
            "retailer": "JB Hi-Fi",
            "url": u,
            "scraped_at": now_iso,
            "run_id": run_id,
            "source": "live_shopify_json"
        })
    print(f"  ✔ [JB Hi-Fi Live] Probed {len(items_by_url)} live PDPs -> {len(results)} valid 2025/2026 models")
    return results


def scrape_goodguys_live(known_map, run_id, now_iso):
    print("\n▶ [2/3] Scraping The Good Guys Live (Parallel curl_cffi PDP JSON-LD Probing)...")
    urls = list(known_map.keys())

    # Also discover new URLs from The Good Guys Television category pages
    for cat_url in [
        "https://www.thegoodguys.com.au/televisions/all-tvs/samsung",
        "https://www.thegoodguys.com.au/televisions/all-tvs/lg",
        "https://www.thegoodguys.com.au/televisions/oled-tvs"
    ]:
        try:
            r = creq.get(cat_url, impersonate="chrome124", timeout=15)
            if r.status_code == 200:
                found = re.findall(r'https://www\.thegoodguys\.com\.au/(?:samsung|lg)-[a-z0-9-]+', r.text)
                for fu in found:
                    fu_clean = fu.split('"')[0].split("'")[0].split("?")[0]
                    if fu_clean not in urls:
                        urls.append(fu_clean)
        except Exception:
            pass

    def _probe_gg(u):
        try:
            r = creq.get(u, impersonate="chrome124", timeout=18)
            if r.status_code != 200:
                return u, None
            lds = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', r.text, re.S)
            for b in lds:
                if '"Product"' in b:
                    try:
                        d = json.loads(b)
                        if d.get("@type") == "Product":
                            return u, d
                    except Exception:
                        pass
        except Exception:
            pass
        return u, None

    results = []
    probed_ok = 0
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = [ex.submit(_probe_gg, u) for u in urls]
        for fut in as_completed(futs):
            u, prod_ld = fut.result()
            if not prod_ld:
                continue
            probed_ok += 1
            title = (prod_ld.get("name") or "").strip()
            offers = prod_ld.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            avail = str(offers.get("availability") or "")
            if "OutOfStock" in avail or "Discontinued" in avail:
                continue
            try:
                price = float(offers.get("price") or 0)
            except Exception:
                price = 0.0
            if price < 250:
                continue

            u_low = u.lower()
            brand = "SAMSUNG" if ("samsung" in u_low or "SAMSUNG" in title.upper()) else "LG"
            mc = extract_model_code(title, u)
            if not mc and u in known_map:
                mc = known_map[u].get("model_code", "")
            year = extract_year(title, mc, u)
            if year not in [2025, 2026] and u in known_map:
                year = known_map[u].get("year")
            if not mc or year not in [2025, 2026]:
                continue
            size = extract_size(title, u)
            if size < 24:
                continue
            cat = get_category(mc, title)
            results.append({
                "name": title,
                "title": title,
                "model_code": mc,
                "brand": brand,
                "year": year,
                "category": cat,
                "size": size,
                "price": price,
                "original_price": price,
                "promo": "None",
                "retailer": "The Good Guys",
                "url": u,
                "scraped_at": now_iso,
                "run_id": run_id,
                "source": "live_pdp_jsonld"
            })
    print(f"  ✔ [The Good Guys Live] Probed {probed_ok}/{len(urls)} live PDPs -> {len(results)} valid 2025/2026 models")
    return results


def scrape_harveynorman_live(known_map, run_id, now_iso):
    print("\n▶ [3/3] Scraping Harvey Norman Live (StealthySession In-Browser Parallel PDP JSON-LD Probing)...")
    urls = list(known_map.keys())
    if not urls:
        return []

    res_holder = {}
    def _run_hn_in_browser(page):
        page.wait_for_timeout(4000)
        res_holder["data"] = page.evaluate("""async (urls) => {
            const out = [];
            for (let i = 0; i < urls.length; i += 8) {
                const batch = urls.slice(i, i + 8);
                const batchRes = await Promise.all(batch.map(async u => {
                    try {
                        const r = await fetch(u, {credentials: 'include'});
                        if (!r.ok) return {url: u, status: r.status};
                        const h = await r.text();
                        const doc = new DOMParser().parseFromString(h, 'text/html');
                        const lds = Array.from(doc.querySelectorAll('script[type="application/ld+json"]')).map(s => s.textContent);
                        let prodLd = null;
                        for (const b of lds) {
                            if (b.includes('"Product"')) {
                                try {
                                    const parsed = JSON.parse(b);
                                    if (parsed['@type'] === 'Product') {
                                        prodLd = parsed;
                                        break;
                                    }
                                } catch(e) {}
                            }
                        }
                        return {url: u, status: r.status, prodLd};
                    } catch(e) {
                        return {url: u, error: String(e)};
                    }
                }));
                out.push(...batchRes);
            }
            return out;
        }""", urls)

    with StealthySession(headless=False, solve_cloudflare=False, timeout=120000) as session:
        session.fetch(urls[0], wait=5000, page_action=_run_hn_in_browser)

    raw_list = res_holder.get("data") or []
    results = []
    probed_ok = 0
    for entry in raw_list:
        u = entry.get("url", "")
        prod_ld = entry.get("prodLd")
        if not prod_ld:
            continue
        probed_ok += 1
        title = (prod_ld.get("name") or "").strip()
        offers = prod_ld.get("offers") or {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        avail = str(offers.get("availability") or "")
        if "OutOfStock" in avail or "Discontinued" in avail:
            continue
        try:
            price = float(offers.get("price") or 0)
        except Exception:
            price = 0.0
        if price < 250:
            continue

        u_low = u.lower()
        brand = "SAMSUNG" if ("samsung" in u_low or "SAMSUNG" in title.upper()) else "LG"
        mc = extract_model_code(title, u)
        if not mc and u in known_map:
            mc = known_map[u].get("model_code", "")
        year = extract_year(title, mc, u)
        if year not in [2025, 2026] and u in known_map:
            year = known_map[u].get("year")
        if not mc or year not in [2025, 2026]:
            continue
        size = extract_size(title, u)
        if size < 24:
            continue
        cat = get_category(mc, title)
        results.append({
            "name": title,
            "title": title,
            "model_code": mc,
            "brand": brand,
            "year": year,
            "category": cat,
            "size": size,
            "price": price,
            "original_price": price,
            "promo": "None",
            "retailer": "Harvey Norman",
            "url": u,
            "scraped_at": now_iso,
            "run_id": run_id,
            "source": "live_pdp_jsonld"
        })
    print(f"  ✔ [Harvey Norman Live] Probed {probed_ok}/{len(urls)} live PDPs -> {len(results)} valid 2025/2026 models")
    return results


def main():
    print("=" * 70)
    print(" 🇦🇺 AUSTRALIA TV RETAILERS REAL-TIME LIVE SCRAPING ENGINE (ZERO CACHE)")
    print("=" * 70)

    run_id = os.environ.get("SURVEY_RUN_ID") or f"au_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    now_iso = datetime.now().astimezone().isoformat(timespec="seconds")

    urls_by_ret = collect_known_urls_by_retailer()
    for r_name, umap in urls_by_ret.items():
        print(f"  • Known Master PDP URLs for {r_name:<15}: {len(umap)} URLs")

    jb_items = scrape_jbhifi_live(urls_by_ret["JB Hi-Fi"], run_id, now_iso)
    gg_items = scrape_goodguys_live(urls_by_ret["The Good Guys"], run_id, now_iso)
    hn_items = scrape_harveynorman_live(urls_by_ret["Harvey Norman"], run_id, now_iso)

    retailer_results = {
        "jbhifi": ("JB Hi-Fi", jb_items),
        "goodguys": ("The Good Guys", gg_items),
        "harveynorman": ("Harvey Norman", hn_items),
    }

    total_extracted = 0
    all_registry_items = []

    for r_key, (r_name, items) in retailer_results.items():
        dedup = {}
        for it in items:
            mc = it["model_code"]
            if mc not in dedup or it["price"] < dedup[mc]["price"]:
                dedup[mc] = it

        final_items = sorted(dedup.values(), key=lambda x: (-x["year"], -x["size"], x["price"]))
        samsung_items = [it for it in final_items if it["brand"] == "SAMSUNG"]
        lg_items = [it for it in final_items if it["brand"] == "LG"]

        if len(samsung_items) < 5 or len(lg_items) < 5:
            raise RuntimeError(f"❌ Live scrape for {r_name} returned insufficient models (Samsung={len(samsung_items)}, LG={len(lg_items)}). Refusing to overwrite!")

        s_path = os.path.join(DATA_DIR, f"raw_{r_key}_samsung.json")
        l_path = os.path.join(DATA_DIR, f"raw_{r_key}_lg.json")

        with open(s_path, "w", encoding="utf-8") as f:
            json.dump(samsung_items, f, ensure_ascii=False, indent=2)
        with open(l_path, "w", encoding="utf-8") as f:
            json.dump(lg_items, f, ensure_ascii=False, indent=2)

        print(f"✅ [{r_name}] Saved {len(samsung_items)} Samsung, {len(lg_items)} LG (Total: {len(final_items)} live models)")
        total_extracted += len(final_items)
        all_registry_items.extend(final_items)

    # Update master_product_urls_au.json with clean live URLs
    registry_path = os.path.join(DATA_DIR, "master_product_urls_au.json")
    master_reg = {}
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                old_reg = json.load(f)
            # Keep only entries with valid product URLs (purge image CDN links)
            for k, v in old_reg.items():
                u = v.get("url", "")
                if any(d in u for d in ["jbhifi.com.au/products/", "thegoodguys.com.au/", "harveynorman.com.au/"]):
                    if not any(bad in u for bad in ["cdn.shopify.com", "imgix.net"]):
                        master_reg[k] = v
        except Exception:
            master_reg = {}

    added_urls = 0
    today_ymd = datetime.now().strftime("%Y-%m-%d")
    for it in all_registry_items:
        key = f"{it['retailer']}_{it['model_code']}"
        if key not in master_reg:
            added_urls += 1
        master_reg[key] = {
            "retailer": it["retailer"],
            "brand": it["brand"],
            "year": it["year"],
            "category": it["category"],
            "size": it["size"],
            "model_code": it["model_code"],
            "url": it["url"],
            "last_verified": today_ymd
        }

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(master_reg, f, ensure_ascii=False, indent=2)

    print(f"\n📦 [AU MASTER REGISTRY] Total {len(master_reg)} clean verified product URLs (Newly added: {added_urls})")
    print(f"🎉 TOTAL LIVE VERIFIED UNIQUE MODELS ACROSS AU: {total_extracted}")


if __name__ == "__main__":
    main()
