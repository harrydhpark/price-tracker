import asyncio
from playwright.async_api import async_playwright
import json
import re
import os
import sys

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

from playwright.async_api import Page
TIMEOUT_MULTIPLIER = float(os.environ.get("TIMEOUT_MULTIPLIER", "1.0"))
if TIMEOUT_MULTIPLIER != 1.0:
    print(f"[TIMEOUT MONKEY PATCH] Applying multiplier: {TIMEOUT_MULTIPLIER}")
    original_sleep = asyncio.sleep
    async def patched_sleep(delay, result=None):
        return await original_sleep(delay * TIMEOUT_MULTIPLIER, result)
    asyncio.sleep = patched_sleep

    original_wait_for_timeout = Page.wait_for_timeout
    async def patched_wait_for_timeout(self, timeout):
        return await original_wait_for_timeout(self, int(timeout * TIMEOUT_MULTIPLIER))
    Page.wait_for_timeout = patched_wait_for_timeout

    original_goto = Page.goto
    async def patched_goto(self, url, **kwargs):
        if "timeout" in kwargs:
            kwargs["timeout"] = int(kwargs["timeout"] * TIMEOUT_MULTIPLIER)
        return await original_goto(self, url, **kwargs)
    Page.goto = patched_goto

    original_wait_for_selector = Page.wait_for_selector
    async def patched_wait_for_selector(self, selector, **kwargs):
        if "timeout" in kwargs:
            kwargs["timeout"] = int(kwargs["timeout"] * TIMEOUT_MULTIPLIER)
        return await original_wait_for_selector(self, selector, **kwargs)
    Page.wait_for_selector = patched_wait_for_selector
# -----------------------------

# Regex pattern for pricing
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
            
    if any(x in title_upper for x in ["S90H", "S95H", "S85H", "S99H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN82H", "QN80H", "QN70H", "LS03H", "LS03HW", "U8000H", "U8090H", "U8070H", "M80H", "M82H", "M70H", "M72H", "R85H", "R95H", "2026"]):
        return 2026
    if any(x in title_upper for x in ["S90F", "S95F", "S85F", "QN900F", "QN800F", "QN95F", "QN90F", "QN85F", "QN82F", "QN80F", "QN70F", "LS03F", "U8000F", "U8090F", "U8070F", "M80F", "M70F", "R85F", "Q7F", "Q8F", "2025"]):
        return 2025
    if any(x in title_upper for x in ["S90D", "S95D", "S85D", "QN900D", "QN800D", "QN95D", "QN90D", "QN85D", "QN80D", "QN70D", "LS03D", "U8000D", "U8090D", "M70D"]):
        return 2024
    return None

def classify_lg_year(model_code, title_upper):
    if model_code != "Unknown":
        if any(x in model_code for x in ["C6", "G6", "B6", "QNED86B", "QNED87B", "QNED85B", "QNED83B", "QNED82B", "QNED81B", "QNED80B", "QNED71B", "QNED70B", "QNED72B", "QNED7EB", "UA77", "MRGB87B", "LX7B", "LX6", "27LX6TDGA", "QLED7EB", "MRGB96B"]):
            return 2026
        elif any(x in model_code for x in ["C5", "G5", "B5", "QNED86A", "QNED87A", "QNED85A", "QNED80A", "QNED72A", "QNED7EA", "UA75", "MRGB87A", "LX7A", "LX5", "QNED70A", "NANO81A", "NANO80A", "QNED93A"]):
            return 2025
        elif any(x in model_code for x in ["C4", "G4", "B4", "QNED80", "QNED85", "QNED86", "UA73"]):
            if "2025" in title_upper:
                return 2025
            return 2024
            
    if any(x in title_upper for x in ["C6", "G6", "B6", "QNED86B", "QNED87B", "QNED85B", "QNED83B", "QNED82B", "QNED81B", "QNED80B", "QNED71B", "QNED70B", "QNED72B", "QNED7EB", "MRGB87B", "LX7B", "LX6", "27LX6", "STANBYME 2", "MRGB96B", "2026"]):
        return 2026
    if any(x in title_upper for x in ["C5", "G5", "B5", "QNED86A", "QNED87A", "QNED85A", "QNED80A", "QNED7EA", "QNED72A", "MRGB87A", "LX7A", "LX5", "QNED70", "NANO81", "NANO80", "QNED93", "2025"]):
        return 2025
    if any(x in title_upper for x in ["C4", "G4", "B4"]):
        return 2024
    return None

async def scrape_digitec_brand(brand):
    print(f"\n[DIGITEC] Starting scrape for brand: {brand}")
    
    if brand.lower() == "samsung":
        url = "https://www.digitec.ch/de/s1/producttype/tv-4?filter=bra%3D422%2C5778%3D2025%7C2026%2Coff%3DInStock&take=150"
    else:
        url = "https://www.digitec.ch/de/s1/producttype/tv-4?filter=bra%3D284%2C5778%3D2025%7C2026%2Coff%3DInStock&take=150"
        
    profile_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".chrome_profile_digi"))
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
        
    products = []
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"  -> Navigating to: {url}")
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"  -> [ERROR] Navigation failed: {e}")
            await context.close()
            return []
            
        print("  -> Scrolling page to load all products...")
        for i in range(15):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
        # Check and click "Mehr anzeigen" if visible to load additional pages
        try:
            show_more = page.locator("a:has-text('Mehr anzeigen')").first
            if await show_more.is_visible():
                print("  -> Found 'Mehr anzeigen' button, clicking it...")
                await show_more.scroll_into_view_if_needed()
                await show_more.click()
                await page.wait_for_timeout(4000)
                # Scroll again
                for i in range(5):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)
        except Exception as e:
            print(f"  -> [INFO] No 'Mehr anzeigen' button or click failed: {e}")
            
        print("  -> Parsing product details...")
        raw_items = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href*="/product/"]'));
                const results = [];
                const seen = new Set();
                
                links.forEach(link => {
                    const title = link.getAttribute('aria-label') || "";
                    if (!title || title.length < 10) return;
                    
                    const href = link.getAttribute('href') || "";
                    
                    if (!seen.has(title)) {
                        seen.add(title);
                        
                        let price = "N/A";
                        let promo = "None";
                        let seller = "Digitec";
                        
                        let parent = link.parentElement;
                        for (let depth = 0; depth < 8; depth++) {
                            if (!parent) break;
                            const text = parent.textContent || "";
                            
                            const priceRegex = /CHF\\s*([\\d\\s’'\\x27\\x60,.]*(?:[.–]|,\\d{2}|\\.\\d{2}))/;
                            const match = text.match(priceRegex);
                            if (match && price === "N/A") {
                                const pVal = match[1].replace(/[.–\\s’'\\x27\\x60]/g, "").trim();
                                if (pVal.length > 1 && pVal !== "2025" && pVal !== "2026") {
                                    price = match[0].trim();
                                }
                            }
                            
                            if (text.includes("Aktion") || text.includes("Cashback") || text.includes("Rabatt") || text.includes("Neu")) {
                                const badgeEl = parent.querySelector('[class*="badge"], [class*="Badge"], [class*="promo"], span[class*="Styled"]');
                                if (badgeEl && promo === "None") {
                                    promo = badgeEl.textContent.trim();
                                }
                            }
                            
                            const sellerMatch = text.match(/(?:Offer by|Angebot von|Verkauf und Versand durch)\\s+([^\\n\\r]+)/i);
                            if (sellerMatch) {
                                seller = sellerMatch[1].trim();
                            }
                            
                            parent = parent.parentElement;
                        }
                        
                        results.push({
                            title,
                            href,
                            price,
                            promo,
                            seller
                        });
                    }
                });
                return results;
            }
        """)
        
        print(f"  -> Extracted {len(raw_items)} raw items. Filtering...")
        await context.close()
        return process_digitec_raw_items(raw_items, brand)

def process_digitec_raw_items(raw_items, brand):
    products = []
    brand_lower = brand.lower()
    for item in raw_items:
        title = item["title"]
        price_str = item["price"]
        promo_desc = item["promo"]
        seller = item["seller"]
        href = item["href"]
        
        title_upper = title.upper()
        
        if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "ZUBEHÖR", "HALTERUNG", "WANDHALTERUNG"]):
            continue
        if any(x in title_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT"]):
            continue
            
        seller_upper = seller.upper()
        if "DIGITEC" not in seller_upper and "GALAXUS" not in seller_upper and "MEDIA" not in seller_upper and seller != "Digitec":
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
            
        words = title_upper.split()
        model_code = "Unknown"
        for w in words:
            clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "")
            if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                model_code = clean_w
                break
                
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
            
        if size_val < 22:
            continue
            
        if brand_lower == "samsung":
            year_val = classify_samsung_year(model_code, title_upper)
        else:
            year_val = classify_lg_year(model_code, title_upper)
            
        if year_val not in [2025, 2026]:
            continue
            
        if model_code == "Unknown" and brand_lower == "lg":
            if "C6" in title_upper: model_code = f"OLED{size_val}C6"
            elif "G6" in title_upper: model_code = f"OLED{size_val}G6"
            elif "B6" in title_upper: model_code = f"OLED{size_val}B6"
            elif "C5" in title_upper: model_code = f"OLED{size_val}C5"
            elif "G5" in title_upper: model_code = f"OLED{size_val}G5"
            elif "B5" in title_upper: model_code = f"OLED{size_val}B5"
            elif "QNED86" in title_upper: model_code = f"{size_val}QNED86A"
            elif "QNED80" in title_upper: model_code = f"{size_val}QNED80A"
        elif model_code == "Unknown" and brand_lower == "samsung":
            if "S95H" in title_upper: model_code = f"QE{size_val}S95H"
            elif "S90H" in title_upper: model_code = f"QE{size_val}S90H"
            elif "S90F" in title_upper: model_code = f"QE{size_val}S90F"
            elif "QN90F" in title_upper: model_code = f"QE{size_val}QN90F"
            elif "Q8F" in title_upper: model_code = f"QE{size_val}Q8F"
                
        display_type = "LED"
        if "OLED" in title_upper: display_type = "OLED"
        elif "QNED" in title_upper: display_type = "QNED"
        elif "NEO QLED" in title_upper or "NEOQLED" in title_upper: display_type = "Neo QLED"
        elif "QLED" in title_upper: display_type = "QLED"
            
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
            "link": "https://www.digitec.ch" + href if href.startswith("/") else href
        })
        
    unique_products = []
    seen = set()
    for p in products:
        if p["model_code"] not in seen:
            seen.add(p["model_code"])
            unique_products.append(p)
            
    print(f"  -> Successfully collected {len(unique_products)} unique products for {brand}.")
    return unique_products

def scrape_digitec_firecrawl_deprecated(brand):
    return []
def _legacy_digitec_firecrawl(brand):
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        print("  ⚠️ [DIGITEC FIRECRAWL] FIRECRAWL_API_KEY missing in environment.")
        return []
    import requests
    from bs4 import BeautifulSoup
    
    brand_lower = brand.lower()
    print(f"\n[DIGITEC FIRECRAWL] Starting live scrape for brand: {brand}")
    bra_id = "422" if brand_lower == "samsung" else "284"
    url = f"https://www.digitec.ch/de/s1/producttype/tv-4?filter=bra%3D{bra_id}%2C5778%3D2025%7C2026%2Coff%3DInStock&take=150"
    payload = {"url": url, "formats": ["html"], "waitFor": 3000}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    try:
        r = requests.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers, timeout=60)
        if r.status_code != 200:
            print(f"  ⚠️ Digitec Firecrawl status {r.status_code}")
            return []
        html = r.json().get("data", {}).get("html", "")
        if not html:
            return []
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=lambda h: h and "/product/" in h)
        raw_items = []
        seen_hrefs = set()
        for l in links:
            title = l.get("aria-label") or ""
            href = l.get("href") or ""
            if not title or len(title) < 10 or href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            parent = l.find_parent("article") or l.find_parent("div")
            price_str = "N/A"
            promo = "None"
            seller = "Digitec"
            if parent:
                txt = parent.get_text()
                p_m = re.search(r'CHF\s*([\d\s’\x27\x60,.]*(?:[.–]|,\d{2}|\.\d{2}|\b))', txt) or re.search(r'([\d\s’\x27\x60,.]*(?:[.–]|,\d{2}|\.\d{2}|\b))\s*CHF', txt)
                if p_m:
                    price_str = p_m.group(0).strip()
                if any(k in txt for k in ["Aktion", "Cashback", "Rabatt", "Neu"]):
                    promo = "Promo"
                s_m = re.search(r'(?:Offer by|Angebot von|Verkauf und Versand durch)\s+([^\n\r]+)', txt, re.IGNORECASE)
                if s_m:
                    seller = s_m.group(1).strip()
            raw_items.append({"title": title, "href": href, "price": price_str, "promo": promo, "seller": seller})
            
        print(f"  ✔ [DIGITEC FIRECRAWL] Extracted {len(raw_items)} raw link items.")
        return process_digitec_raw_items(raw_items, brand)
    except Exception as e:
        print(f"  ⚠️ [DIGITEC FIRECRAWL ERROR] {e}")
        return []

async def main():
    import time
    import argparse
    start_time = time.time()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", "--stealth-fast", action="store_true", dest="fast", help="Use real-time Firecrawl scraping")
    args, _ = parser.parse_known_args()
    
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    s_path = os.path.join(data_dir, "raw_digitec_samsung.json")
    l_path = os.path.join(data_dir, "raw_digitec_lg.json")
    
    is_fast = args.fast or os.environ.get("STEALTH_FAST") == "1"
    samsungs = []
    lgs = []
    
    print("🚀 [ZERO-FIRECRAWL] Executing 100% local persistent Playwright scraper for Digitec CH...")
    try:
        samsungs = await scrape_digitec_brand("Samsung")
        lgs = await scrape_digitec_brand("LG")
    except Exception as e:
        print(f"❌ [PLAYWRIGHT ERROR] {e}")
        samsungs, lgs = [], []
            
    # STRICT ASSERTION GATE: ZERO STALE CACHE PERMITTED
    if len(samsungs) == 0 or len(lgs) == 0:
        raise RuntimeError("❌ [CRITICAL ZERO LIVE DATA] Digitec live scraping returned 0 models. Stale cache fallback is strictly prohibited.")
        
    with open(s_path, "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(l_path, "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print(f"\n[DIGITEC DONE] Successfully saved {len(samsungs)} Samsung models and {len(lgs)} LG models directly from live web.")
    
    try:
        from scrape_logger import emit_summary
        elapsed = round(time.time() - start_time, 2)
        emit_summary(country="CH", retailer="Digitec", brand="SAMSUNG", total_extracted=len(samsungs), final_deduplicated=len(samsungs), execution_time_sec=elapsed)
        emit_summary(country="CH", retailer="Digitec", brand="LG", total_extracted=len(lgs), final_deduplicated=len(lgs), execution_time_sec=elapsed)
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main())

