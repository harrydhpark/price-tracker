import os
import json
import re
import asyncio
from playwright.async_api import async_playwright

DATA_DIR = os.path.abspath('data')

def parse_price_str(price_str):
    if not price_str:
        return None
    cleaned = re.sub(r'[^\d,\.]', '', price_str.strip())
    if not cleaned:
        return None
    # Handle European comma/dot
    if ',' in cleaned and '.' in cleaned:
        if cleaned.rfind(',') > cleaned.rfind('.'):
            # 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # 1,234.56
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        val = float(cleaned)
        return val
    except:
        return None

async def inspect_url(page, item):
    url = item.get('url')
    country = item.get('country')
    retailer = item.get('retailer')
    model_code = item.get('model_code')
    brand = item.get('brand')
    year = item.get('year')
    size = item.get('size', 55)

    res = {
        'master_key': item.get('master_key'),
        'country': country,
        'retailer': retailer,
        'brand': brand,
        'model_code': model_code,
        'year': year,
        'size': size,
        'url': url,
        'status': 'unknown',
        'reason': '',
        'price': None,
        'page_title': ''
    }

    try:
        response = await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        status_code = response.status if response else 0
        current_url = page.url

        if status_code in [404, 410]:
            res['status'] = 'discontinued_404'
            res['reason'] = f'HTTP {status_code}'
            return res

        # Check redirect away from product
        if 'alza.cz' in current_url and '/d' not in current_url:
            res['status'] = 'discontinued_redirect'
            res['reason'] = 'Redirected to category/homepage'
            return res

        page_title = await page.title()
        res['page_title'] = page_title
        content = await page.content()
        body_text = await page.evaluate("() => document.body.innerText")

        # Retailer-specific OOS / Discontinued detection
        r_lower = retailer.lower()
        if 'alza' in r_lower:
            if 'prodej skončil' in body_text.lower() or 'nedostupné' in body_text.lower() or 'těmto produktům již odzvonilo' in body_text.lower():
                res['status'] = 'discontinued_oos'
                res['reason'] = 'Prodej skončil / Nedostupné'
                return res
            # Try get price
            price_el = await page.query_selector('.price-box__price, .price_primary, .bigPrice, [data-price-amount]')
            if price_el:
                p_text = await price_el.inner_text()
                p_val = parse_price_str(p_text)
                if p_val and p_val > 1000:
                    res['price'] = p_val
                    res['status'] = 'active'
                    return res

        elif 'currys' in r_lower:
            if 'out of stock' in body_text.lower() or 'no longer available' in body_text.lower() or 'we couldn\'t find that page' in body_text.lower():
                res['status'] = 'discontinued_oos'
                res['reason'] = 'Out of stock / No longer available'
                return res
            price_el = await page.query_selector('.current-price, .product-price, [data-price]')
            if price_el:
                p_text = await price_el.inner_text()
                p_val = parse_price_str(p_text)
                if p_val:
                    res['price'] = p_val
                    res['status'] = 'active'
                    return res

        elif 'public' in r_lower:
            if 'μη διαθέσιμο' in body_text.lower() or 'εξαντλήθηκε' in body_text.lower() or '404' in page_title:
                res['status'] = 'discontinued_oos'
                res['reason'] = 'Μη διαθέσιμο / Εξαντλήθηκε'
                return res
            price_el = await page.query_selector('.product-price, .current-price, .price')
            if price_el:
                p_text = await price_el.inner_text()
                p_val = parse_price_str(p_text)
                if p_val:
                    res['price'] = p_val
                    res['status'] = 'active'
                    return res

        elif 'digitec' in r_lower:
            if 'nicht mehr lieferbar' in body_text.lower() or 'ausverkauft' in body_text.lower() or 'aktuell nicht lieferbar' in body_text.lower():
                res['status'] = 'discontinued_oos'
                res['reason'] = 'Nicht mehr lieferbar / Ausverkauft'
                return res
            # Check price
            price_el = await page.query_selector('strong[class*="price_"], [data-test="product-price"]')
            if price_el:
                p_text = await price_el.inner_text()
                p_val = parse_price_str(p_text)
                if p_val:
                    res['price'] = p_val
                    res['status'] = 'active'
                    return res

        elif 'mediamarkt' in r_lower or 'mediaworld' in r_lower:
            if 'nicht mehr verfügbar' in body_text.lower() or 'ausverkauft' in body_text.lower() or 'esaurito' in body_text.lower() or 'agotado' in body_text.lower() or 'niet leverbaar' in body_text.lower() or 'nem rendelhető' in body_text.lower():
                res['status'] = 'discontinued_oos'
                res['reason'] = 'Nicht mehr verfügbar / Ausverkauft'
                return res
            price_el = await page.query_selector('[data-test="branded-price-whole-value"], .price, [class*="Price"]')
            if price_el:
                p_text = await price_el.inner_text()
                p_val = parse_price_str(p_text)
                if p_val:
                    res['price'] = p_val
                    res['status'] = 'active'
                    return res

        elif 'fnac' in r_lower:
            if 'épuisé' in body_text.lower() or 'indisponible' in body_text.lower() or 'n\'est plus disponible' in body_text.lower():
                res['status'] = 'discontinued_oos'
                res['reason'] = 'Épuisé / Indisponible'
                return res
            price_el = await page.query_selector('.userPrice, .f-price, [data-automation-id="product-price"]')
            if price_el:
                p_text = await price_el.inner_text()
                p_val = parse_price_str(p_text)
                if p_val:
                    res['price'] = p_val
                    res['status'] = 'active'
                    return res

        # Default fallback check
        res['status'] = 'unclassified'
        res['reason'] = f'Title: {page_title[:40]}'

    except Exception as e:
        res['status'] = 'error'
        res['reason'] = str(e)[:100]

    return res

async def test_batch():
    with open('data/master_urls_missing_713.json', 'r', encoding='utf-8') as f:
        missing = json.load(f)

    # Pick 2 samples from top 5 retailers
    sample_indices = [0, 1, 151, 152, 282, 283, 374, 375, 452, 453]
    samples = [missing[i] for i in sample_indices if i < len(missing)]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        for it in samples:
            r = await inspect_url(page, it)
            print(f"[{r['retailer']}] {r['model_code']} -> Status: {r['status']}, Price: {r['price']}, Reason: {r['reason']}")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_batch())
