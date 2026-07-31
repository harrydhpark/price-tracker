# -*- coding: utf-8 -*-
import sys
import os
import json
import urllib.request
import re

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'el-GR,el;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
}

def check_site(name, url):
    print(f"\n--- Checking {name}: {url} ---")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            print(f"[{name}] Status: {response.status}, HTML Length: {len(html)}")
            
            # Check for JSON embedded data or product tags
            if "window.__NEXT_DATA__" in html:
                print("  ➔ Found window.__NEXT_DATA__")
            if "application/ld+json" in html:
                print("  ➔ Found application/ld+json")
            if "__INITIAL_STATE__" in html:
                print("  ➔ Found __INITIAL_STATE__")
                
            # Search for TV brand mentions
            sam_count = len(re.findall(r'samsung', html, re.IGNORECASE))
            lg_count = len(re.findall(r'lg', html, re.IGNORECASE))
            print(f"  ➔ Mention counts: Samsung={sam_count}, LG={lg_count}")
            
    except Exception as e:
        print(f"[{name}] Error: {e}")

if __name__ == '__main__':
    check_site("Kotsovolos Search Samsung", "https://www.kotsovolos.gr/site/search.jsp?q=samsung+tv")
    check_site("Kotsovolos Sound Vision TVs", "https://www.kotsovolos.gr/sound-vision/televisions")
    check_site("Public Search Samsung", "https://www.public.gr/search?q=samsung+tv")
    check_site("Public TVs Category", "https://www.public.gr/cat/sound-and-vision/tvs")
