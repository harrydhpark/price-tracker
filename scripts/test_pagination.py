# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from scrapling.fetchers import StealthySession
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def parse_page_apollo(html):
    idx = html.find('window.__PRELOADED_STATE__')
    if idx == -1:
        return []
    end_idx = html.find('</script>', idx)
    raw = html[idx:end_idx].split('window.__PRELOADED_STATE__ =', 1)[1].strip()
    if raw.endswith(';'):
        raw = raw[:-1]
    raw = re.sub(r':\s*undefined\b', ': null', raw)
    try:
        data = json.loads(raw)
    except Exception as e:
        print("JSON parse error:", e)
        return []
        
    apollo = data.get("apolloState", {})
    
    # Map price features by id
    prices = {}
    for k, v in apollo.items():
        if k.startswith("CofrPriceFeature:"):
            # ID is like Media:hu:1515549
            media_id = v.get("id", "")
            raw_id = media_id.split(":")[-1] if ":" in media_id else media_id
            p_obj = v.get("price", {})
            amount = p_obj.get("amount") if isinstance(p_obj, dict) else None
            promo_p = v.get("promoPrice", {})
            promo_amount = promo_p.get("amount") if isinstance(promo_p, dict) else None
            is_mp = v.get("isProductOfTypeMarketplace", False)
            seller = v.get("marketplaceSeller")
            
            prices[raw_id] = {
                "amount": amount,
                "promo_amount": promo_amount,
                "currency": v.get("currency", "HUF"),
                "is_marketplace": is_mp,
                "seller": seller
            }
            
    products = []
    for k, v in apollo.items():
        if k.startswith("GraphqlProduct:"):
            prod_id = str(v.get("id") or v.get("productId") or "")
            title = v.get("title") or v.get("name") or v.get("description") or ""
            brand = v.get("manufacturer") or v.get("brand") or ""
            pdp_url = v.get("pdpUrl") or v.get("url") or ""
            
            price_info = prices.get(prod_id, {})
            
            products.append({
                "id": prod_id,
                "title": title,
                "brand": brand,
                "url": f"https://www.mediamarkt.hu{pdp_url}" if pdp_url.startswith("/") else pdp_url,
                "price_huf": price_info.get("amount"),
                "promo_price_huf": price_info.get("promo_amount"),
                "is_marketplace": price_info.get("is_marketplace", False),
                "seller": price_info.get("seller")
            })
            
    return products

def test_pagination():
    test_urls = [
        ("LG TV Page 1", "https://www.mediamarkt.hu/hu/search.html?query=LG+TV&page=1"),
        ("LG TV Page 2", "https://www.mediamarkt.hu/hu/search.html?query=LG+TV&page=2"),
        ("Samsung TV Page 1", "https://www.mediamarkt.hu/hu/search.html?query=Samsung+TV&page=1"),
        ("Samsung TV Page 2", "https://www.mediamarkt.hu/hu/search.html?query=Samsung+TV&page=2"),
    ]
    
    with StealthySession(headless=True) as session:
        for label, url in test_urls:
            print(f"\n--- Testing {label} ({url}) ---")
            p = session.fetch(url, solve_cloudflare=True, wait=3000, timeout=35000)
            items = parse_page_apollo(str(p.html_content))
            print(f"Status: {p.status} | Extracted products: {len(items)}")
            for it in items[:3]:
                print(f"  • [{it['brand']}] {it['title'][:55]} | Price: {it['price_huf']} HUF (MP: {it['is_marketplace']})")

if __name__ == '__main__':
    test_pagination()
