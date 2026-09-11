import asyncio
from playwright.async_api import async_playwright
import json
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

# --- TIMEOUT MONKEY PATCH ---
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
            
    if any(x in title_upper for x in ["S90H", "S95H", "S85H", "S99H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "LS03H", "U8000H", "U8090H", "M70H", "R85H", "R95H"]):
        return 2026
    if any(x in title_upper for x in ["S90F", "S95F", "S85F", "QN900F", "QN800F", "QN95F", "QN90F", "QN85F", "QN80F", "QN70F", "LS03F", "U8000F", "U8090F", "M70F", "R85F", "Q7F", "Q8F"]):
        return 2025
    if any(x in title_upper for x in ["S90D", "S95D", "S85D", "QN900D", "QN800D", "QN95D", "QN90D", "QN85D", "QN80D", "QN70D", "LS03D", "U8000D", "U8090D", "M70D"]):
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
            
    if any(x in title_upper for x in ["C6", "G6", "B6", "QNED86B", "QNED80B", "QNED87B", "QNED71B", "QNED70B", "QNED72B", "QNED7EB", "MRGB87B", "LX7B", "LX6", "27LX6", "STANBYME 2", "MRGB96B"]):
        return 2026
    if any(x in title_upper for x in ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED87A", "QNED7EA", "QNED72A", "MRGB87A", "LX7A", "LX5", "QNED70", "NANO81", "NANO80", "QNED93"]):
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
        
        print(f"  -> Raw items count: {len(raw_items)}")
        for item in raw_items:
            title = item["title"]
            price_str = item["price"]
            promo_desc = item["promo"]
            seller = item["seller"]
            href = item["href"]
            
            title_upper = title.upper()
            
            print(f"DEBUG item: {title[:40]} | Price: {price_str} | Seller: {seller}")
            
            if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "ZUBEHÖR", "HALTERUNG"]):
                print("    -> Skipped: Monitor/Acc")
                continue
            if any(x in title_upper for x in ["RETURNED", "REFURBISHED", "USED", "GEBRAUCHT"]):
                print("    -> Skipped: Used/Refurbished")
                continue
                
            seller_upper = seller.upper()
            if "DIGITEC" not in seller_upper and "GALAXUS" not in seller_upper:
                print(f"    -> Skipped: Non-direct seller ({seller})")
                continue
                
            price_val = 0.0
            if price_str != "N/A":
                clean_p = price_str.replace("CHF", "").strip()
                # Match digit sequences ignoring quotes and spaces, allowing dot/comma
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
                print(f"    -> Skipped: Price is 0 or parsing failed ({price_str})")
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
                print(f"    -> Skipped: Size < 22 ({size_val})")
                continue
                
            if brand.lower() == "samsung":
                year_val = classify_samsung_year(model_code, title_upper)
            else:
                year_val = classify_lg_year(model_code, title_upper)
                
            if year_val not in [2025, 2026]:
                print(f"    -> Skipped: Year mismatch ({year_val}) for model {model_code}")
                continue
                
            if model_code == "Unknown" and brand.lower() == "lg":
                if "C6" in title_upper:
                    model_code = f"OLED{size_val}C6"
                elif "G6" in title_upper:
                    model_code = f"OLED{size_val}G6"
                elif "B6" in title_upper:
                    model_code = f"OLED{size_val}B6"
                    
            display_type = "LED"
            if "OLED" in title_upper:
                display_type = "OLED"
            elif "QNED" in title_upper:
                display_type = "QNED"
            elif "NEO QLED" in title_upper or "NEOQLED" in title_upper:
                display_type = "Neo QLED"
            elif "QLED" in title_upper:
                display_type = "QLED"
                
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
            
        await context.close()
        
    unique_products = []
    seen = set()
    for p in products:
        if p["model_code"] not in seen:
            seen.add(p["model_code"])
            unique_products.append(p)
            
    print(f"  -> Successfully collected {len(unique_products)} unique products for {brand}.")
    return unique_products

async def main():
    import time
    start_time = time.time()
    samsungs = await scrape_digitec_brand("Samsung")
    lgs = await scrape_digitec_brand("LG")
    
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    
    with open(os.path.join(data_dir, "raw_digitec_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, "raw_digitec_lg.json"), "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print(f"\n[DIGITEC DONE] Saved {len(samsungs)} Samsung models and {len(lgs)} LG models.")
    
    try:
        from scrape_logger import emit_summary
        elapsed = round(time.time() - start_time, 2)
        emit_summary(country="CH", retailer="Digitec", brand="SAMSUNG", total_extracted=len(samsungs), final_deduplicated=len(samsungs), execution_time_sec=elapsed)
        emit_summary(country="CH", retailer="Digitec", brand="LG", total_extracted=len(lgs), final_deduplicated=len(lgs), execution_time_sec=elapsed)
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main())
