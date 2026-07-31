# -*- coding: utf-8 -*-
import sys
import os
import json
import re
from scrapling.fetchers import StealthySession
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

TIMEOUT_MULTIPLIER = float(os.environ.get("TIMEOUT_MULTIPLIER", "1.0"))

urls = [
    ("Kotsovolos_Samsung", "https://www.kotsovolos.gr/sound-vision/televisions?manufacturer=samsung"),
    ("Kotsovolos_LG", "https://www.kotsovolos.gr/sound-vision/televisions?manufacturer=lg"),
    ("Public_Samsung", "https://www.public.gr/cat/sound-and-vision/tvs?m=samsung"),
    ("Public_LG", "https://www.public.gr/cat/sound-and-vision/tvs?m=lg"),
]

def test_fetch():
    print("[START] Testing Scrapling StealthySession for Greece retailers...")
    with StealthySession(headless=True) as session:
        for tag, url in urls:
            print(f"\nFetching {tag}: {url}")
            try:
                # Do NOT pass network_idle=True
                res = session.fetch(url, wait=int(3000 * TIMEOUT_MULTIPLIER))
                html = res.status_code if hasattr(res, 'status_code') else "OK"
                body = res.body if hasattr(res, 'body') else str(res)
                if isinstance(body, bytes):
                    body = body.decode('utf-8', errors='ignore')
                    
                print(f"➔ Status: {html}, Body Length: {len(body)}")
                if "Verification Required" in body or "Cloudflare" in body and "Access denied" in body:
                    print("  ⚠️ Blocked by Cloudflare")
                else:
                    soup = BeautifulSoup(body, 'html.parser')
                    # Look for Next.js data or product cards
                    next_data = soup.find('script', id='__NEXT_DATA__')
                    ld_json = soup.find_all('script', type='application/ld+json')
                    cards = soup.select('.product, [class*="product"], [data-testid*="product"]')
                    print(f"  ➔ Success! NEXT_DATA: {bool(next_data)}, ld+json: {len(ld_json)}, CSS Product Cards: {len(cards)}")
                    
                    # Save HTML snippet for analysis
                    filename = f"data/debug_{tag.lower()}.html"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(body)
                    print(f"  ➔ Saved debug file: {filename}")
            except Exception as e:
                print(f"  ❌ Error fetching {tag}: {e}")

if __name__ == '__main__':
    test_fetch()
