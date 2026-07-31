import asyncio
from playwright.async_api import async_playwright
import json
import re
import urllib.parse
import os
import sys
import math

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

# 정규식 패턴 정의
price_regex = re.compile(r'(\d[\d\s’\x27\x60,.]*[,.]\d{2})')

def classify_samsung_year(model_code, title_upper):
    if model_code != "Unknown":
        if "H" in model_code[2:]:
            return 2026
        elif "F" in model_code[2:]:
            return 2025
        elif "D" in model_code[2:] or "E" in model_code[2:]:
            return 2024
        elif "C" in model_code[2:]:
            return 2023
        elif "B" in model_code[2:]:
            return 2022
        elif "A" in model_code[2:]:
            return 2021
            
    if any(x in title_upper for x in ["S90H", "S95H", "S85H", "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "LS03H", "U8000H", "U8090H", "M70H", "R85H"]):
        return 2026
    if any(x in title_upper for x in ["S90F", "S95F", "S85F", "QN900F", "QN800F", "QN95F", "QN90F", "QN85F", "QN80F", "QN70F", "LS03F", "U8000F", "U8090F", "M70F", "R85F"]):
        return 2025
    if any(x in title_upper for x in ["S90D", "S95D", "S85D", "QN900D", "QN800D", "QN95D", "QN90D", "QN85D", "QN80D", "QN70D", "LS03D", "U8000D", "U8090D", "M70D"]):
        return 2024
    if any(x in title_upper for x in ["S90C", "S95C", "QN900C", "QN800C", "QN95C", "QN90C", "QN85C", "QN80C", "QN70C", "LS03C"]):
        return 2023
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


async def check_and_wait_for_captcha(page):
    for i in range(45): # Max 90 seconds
        content = await page.content()
        title = await page.title()
        
        is_captcha = ("Verification Required" in content or "blocked" in content or 
                      "captcha" in content or "captcha-delivery" in content or
                      "잠시만 기다리십시오" in title or "보안 확인" in title or "잠시만 기다리십시오" in content)
                      
        if is_captcha:
            if i % 5 == 0:
                print("\n[CAPTCHA ALERT] Cloudflare 보안 캡차가 감지되었습니다!")
                print("➔ Attempting automated Turnstile bypass...")
            
            # Find Turnstile Frame
            cf_frames = [f for f in page.frames if "challenges.cloudflare.com" in f.url]
            if cf_frames:
                cf_frame = cf_frames[0]
                try:
                    await asyncio.sleep(5) # Wait for Turnstile widget to load completely
                    iframe_element = await cf_frame.frame_element()
                    if iframe_element:
                        rect = await iframe_element.bounding_box()
                        if rect:
                            click_x = rect['x'] + 30
                            click_y = rect['y'] + 32
                            print(f"➔ Found Turnstile iframe, clicking coordinate: ({click_x}, {click_y})")
                            await page.mouse.move(click_x, click_y)
                            await page.mouse.down()
                            await asyncio.sleep(0.1)
                            await page.mouse.up()
                            await asyncio.sleep(5) # Wait for page reaction
                except Exception as e:
                    print(f"➔ Automated bypass attempt failed: {e}")
            else:
                await asyncio.sleep(2)
        else:
            if i > 0:
                print("➔ [SUCCESS] 캡차가 성공적으로 해결되었습니다. 스크래핑을 계속합니다.")
            return True
    print("\n[ERROR] 캡차 해결 대기 시간이 초과되어 스크래핑을 일시 중단합니다.")
    return False

async def scrape_brand_tv(brand):
    print(f"\n[INTERDISCOUNT] Starting scrape for brand: {brand}")
    brand_upper = brand.upper()
    products = []
    
    profile_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".chrome_profile"))
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
        
    async with async_playwright() as p:
        # persistent_context + chrome channel + slow_mo 사용
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
        
        # 1단계: 메인 홈페이지로 접속하여 쿠키 세션 수립
        print("  -> Initial navigation to homepage for cookies...")
        try:
            await page.goto("https://www.interdiscount.ch/de", timeout=50000)
            await check_and_wait_for_captcha(page)
            await page.wait_for_timeout(3000)
            
            # 쿠키 승인
            cookie_btn = await page.wait_for_selector("button#uc-btn-accept-banner, #uc-accept-all-button", timeout=5000)
            if cookie_btn:
                await cookie_btn.click()
                print("  -> Accepted cookie banner.")
                await page.wait_for_timeout(1000)
        except Exception as e:
            print(f"  -> Homepage navigation / cookie accept warning: {e}")
            
        # 페이지 1~5 순회하며 수집 (SKILL.md 카테고리 URL 및 5페이지 제한 루프)
        for page_idx in range(1, 6):
            if brand_upper == "SAMSUNG":
                url = f"https://www.interdiscount.ch/de/fernseher--c111000?brand=SAMSUNG&page={page_idx}"
            else:
                url = f"https://www.interdiscount.ch/de/fernseher--c111000?brand=LG&page={page_idx}"
            print(f"  -> Navigating to page {page_idx}: {url}")
            try:
                await page.goto(url, timeout=50000)
                await check_and_wait_for_captcha(page)
                await page.wait_for_timeout(4000)
                await page.wait_for_selector('article', timeout=15000)
            except Exception as e:
                print(f"  -> [WARN] Failed to load page {page_idx}: {e}")
                continue
                    
            # SKILL.md 목록 추출 스크립트 실행
            html_articles = await page.evaluate("""
                async () => {
                    await new Promise(r => setTimeout(r, 2500)); // 렌더링 대기 필수
                    const recent = Array.from(document.querySelectorAll('h2'))
                        .find(h => /Zuletzt angesehene/.test(h.textContent));
                    const arts = Array.from(document.querySelectorAll('main article'));
                    const listing = recent
                        ? arts.filter(a => a.compareDocumentPosition(recent) & Node.DOCUMENT_POSITION_FOLLOWING)
                        : arts;
                    return listing.map(a => {
                        const link = a.querySelector('a[href*="/product/"]');
                        return {
                            name: link ? link.getAttribute('aria-label') : null,
                            href: link ? link.getAttribute('href') : null,
                            price: a.querySelector('.sr-only') ? a.querySelector('.sr-only').textContent : null,
                            promo: a.querySelector('.font-semibold.line-clamp-1') ? a.querySelector('.font-semibold.line-clamp-1').textContent : null
                        };
                    });
                }
            """)
            
            print(f"  -> Page {page_idx}: Extracted {len(html_articles)} articles.")
            
            for art in html_articles:
                title = art["name"]
                href = art["href"]
                price_str = art["price"]
                promo_desc = art["promo"] or "None"
                
                if not title or not href or not price_str:
                    continue
                    
                title_upper = title.upper()
                
                # 모니터/세탁기 등 제외
                if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "BEAMER", "PROJEKTOR", "WASCHMASCHINE", "TROCKNER", "ZUBEHÖR", "HALTERUNG", "WANDHALTERUNG"]):
                    continue
                # 중고 제외
                if any(x in title_upper for x in ["GEBRAUCHT", "REFURBISHED", "DEMO", "OCCASION"]):
                    continue
                    
                # 가격
                price_match = price_regex.search(price_str)
                price_val = 0.0
                if price_match:
                    p_str = price_match.group(1).replace("\u2019", "").replace("'", "").replace("`", "").replace(" ", "").replace(",", ".").strip()
                    try:
                        price_val = float(p_str)
                    except ValueError:
                        price_val = 0.0
                else:
                    # 다른 형식의 가격 매칭 시도
                    price_match_alt = price_regex.search(price_str.replace("CHF", "").strip())
                    if price_match_alt:
                        p_str = price_match_alt.group(1).replace("\u2019", "").replace("'", "").replace("`", "").replace(" ", "").replace(",", ".").strip()
                        try:
                            price_val = float(p_str)
                        except ValueError:
                            price_val = 0.0
                            
                if price_val == 0.0:
                    continue
                    
                # 모델 코드 분석
                words = title_upper.split()
                model_code = "Unknown"
                for w in words:
                    clean_w = w.replace("(", "").replace(")", "").replace(",", "").replace("\"", "")
                    if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                        model_code = clean_w
                        break
                        
                # 사이즈 추출
                size_match = re.search(r'(\d+)\s*"', title)
                if not size_match:
                    size_match = re.search(r'(\d+)\s*Zoll', title, re.IGNORECASE)
                if not size_match:
                    size_match = re.search(r'(\d+)-Zoll', title, re.IGNORECASE)
                if not size_match and model_code != "Unknown":
                    code_nums = re.findall(r'\d+', model_code)
                    if code_nums and len(code_nums[0]) in [2, 3]:
                        size_val = int(code_nums[0])
                    else:
                        size_val = 55
                else:
                    size_val = int(size_match.group(1)) if size_match else 55
                    
                # 모델 연도 판별
                if brand_upper == "SAMSUNG":
                    year_val = classify_samsung_year(model_code, title_upper)
                else:
                    year_val = classify_lg_year(model_code, title_upper)
                    
                if year_val not in [2025, 2026]:
                    continue
                    
                # C6 같은 특수 모델코드 처리
                if model_code == "Unknown" and brand_upper == "LG":
                    if "C6" in title_upper:
                        model_code = f"OLED{size_val}C6"
                    elif "G6" in title_upper:
                        model_code = f"OLED{size_val}G6"
                    elif "B6" in title_upper:
                        model_code = f"OLED{size_val}B6"
                    
                # Display Type 분석
                display_type = "LED"
                if "OLED" in title_upper:
                    display_type = "OLED"
                elif "QNED" in title_upper:
                    display_type = "QNED"
                elif "NEO QLED" in title_upper:
                    display_type = "Neo QLED"
                elif "QLED" in title_upper:
                    display_type = "QLED"
                elif "CRYSTAL" in title_upper:
                    display_type = "Crystal UHD"
                    
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
                    "link": "https://www.interdiscount.ch" + href if href.startswith("/") else href
                })
                
        await context.close()
        
    unique_products = []
    seen_codes = set()
    for p in products:
        if p["model_code"] not in seen_codes:
            seen_codes.add(p["model_code"])
            unique_products.append(p)
            
    return unique_products

async def main():
    sys.stdout.reconfigure(encoding='utf-8')
    samsungs = await scrape_brand_tv("Samsung")
    lgs = await scrape_brand_tv("LG")
    
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "raw_interdiscount_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(samsungs, f, ensure_ascii=False, indent=2)
    with open(os.path.join(data_dir, "raw_interdiscount_lg.json"), "w", encoding="utf-8") as f:
        json.dump(lgs, f, ensure_ascii=False, indent=2)
        
    print(f"\n[INTERDISCOUNT DONE] Saved {len(samsungs)} Samsung models and {len(lgs)} LG models.")

if __name__ == "__main__":
    asyncio.run(main())
