# -*- coding: utf-8 -*-
import os
import sys
import re
import json
import time
from datetime import datetime
import requests

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT_DIR)

def _load_env_file():
    env_path = os.path.join(ROOT_DIR, ".env")
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
        except Exception as e:
            print("Error reading .env:", e)

_load_env_file()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

print("[*] FIRECRAWL_API_KEY loaded:", bool(FIRECRAWL_API_KEY))

FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v1/scrape"
HEADERS = {
    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}

NON_TV_KEYWORDS = [
    "ODYSSEY", "MONITOR", "SOUNDBAR", "WALLMOUNT", "WANDHALTERUNG",
    "GALAXY", "PHONE", "SMARTPHONE", "TABLET", "CASE", "COVER", "HÜLLE",
    "REMOTE", "FERNBEDIENUNG", "KABEL", "CABLE", "BEAMER", "PROJECTOR"
]

def clean_price_val(raw_str):
    if not raw_str:
        return 0.0
    s = str(raw_str).replace("€", "").replace("£", "").replace("CHF", "").replace("Ft", "").replace("Kč", "").replace("CZK", "").replace("HUF", "").strip()
    s = s.replace("\u202f", " ").replace("\u00a0", " ")
    if re.match(r'^\d{1,3}\.\d{3}$', s):
        s = s.replace(".", "")
    elif re.match(r'^\d{1,3},\d{3}$', s):
        s = s.replace(",", "")
    elif "," in s and "." in s:
        if s.find(".") < s.find(","):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts[-1]) == 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    cleaned = re.sub(r'[^\d.]', '', s)
    try:
        val = float(cleaned)
        if 0 < val < 10.0:
            val *= 1000.0
        return val
    except:
        return 0.0

def parse_size_from_text(text):
    m = re.search(r'\b(115|100|98|86|85|77|75|65|55|50|48|43|42)\b', text)
    if m:
        return int(m.group(1))
    m2 = re.search(r'(\d{2,3})[\s-]*(?:inch|zoll|pollici|pouces|\")', text, re.I)
    if m2:
        return int(m2.group(1))
    return 0

def parse_model_code_from_text(text, brand):
    b_up = brand.upper()
    t_up = text.upper()
    if b_up == "LG":
        m = re.search(r'\b(\d{2,3}MRGB\w+)\b', t_up)
        if m:
            return m.group(1)
        m2 = re.search(r'\b(MRGB\w+)\b', t_up)
        if m2:
            return m2.group(1)
    else: # SAMSUNG
        m = re.search(r'\b((?:MRE|QE|UE|RE|TMR)?\d{2,3}R[89][56]\w*)\b', t_up)
        if m:
            return m.group(1)
        m2 = re.search(r'\b(R[89][56]H?\w*)\b', t_up)
        if m2:
            return m2.group(1)
    return "Unknown"

def scrape_url_via_firecrawl(url):
    payload = {"url": url, "formats": ["markdown"], "proxy": "stealth"}
    for attempt in range(3):
        try:
            r = requests.post(FIRECRAWL_ENDPOINT, json=payload, headers=HEADERS, timeout=50)
            if r.status_code == 200:
                data = r.json().get("data", {})
                return data.get("markdown", ""), 200
            elif r.status_code == 429:
                time.sleep(10)
            else:
                time.sleep(2)
        except Exception as e:
            time.sleep(2)
    return "", 0

def main():
    print("================================================================================")
    print(" RESCRAPING & PROBING MICRO RGB (LG MRGB & SAMSUNG R85H/R95H) ALL RETAILERS")
    print("================================================================================")
    
    TARGET_SEARCHES = [
        # Spain (ES)
        ("ES", "MediaMarkt", "Samsung", "https://www.mediamarkt.es/es/search.html?query=Samsung+R85H"),
        ("ES", "MediaMarkt", "Samsung", "https://www.mediamarkt.es/es/search.html?query=Samsung+R95H"),
        ("ES", "MediaMarkt", "Samsung", "https://www.mediamarkt.es/es/search.html?query=Samsung+R85"),
        ("ES", "MediaMarkt", "LG", "https://www.mediamarkt.es/es/search.html?query=LG+MRGB"),
        
        # Germany (DE)
        ("DE", "MediaMarkt", "LG", "https://www.mediamarkt.de/de/search.html?query=LG+MRGB"),
        ("DE", "MediaMarkt", "LG", "https://www.mediamarkt.de/de/search.html?query=MRGB86B"),
        ("DE", "MediaMarkt", "Samsung", "https://www.mediamarkt.de/de/search.html?query=Samsung+R85H"),
        ("DE", "MediaMarkt", "Samsung", "https://www.mediamarkt.de/de/search.html?query=Samsung+R95H"),
        
        # France (FR) Fnac
        ("FR", "Fnac", "Samsung", "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0&Search=tv+samsung+r85h"),
        ("FR", "Fnac", "Samsung", "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0&Search=tv+samsung+r95h"),
        ("FR", "Fnac", "LG", "https://www.fnac.com/SearchResult/ResultList.aspx?SCat=0&Search=tv+lg+mrgb"),
        
        # Hungary (HU)
        ("HU", "MediaMarkt", "LG", "https://www.mediamarkt.hu/hu/search.html?query=LG+MRGB"),
        ("HU", "MediaMarkt", "LG", "https://www.mediamarkt.hu/hu/search.html?query=MRGB87B"),
        ("HU", "MediaMarkt", "Samsung", "https://www.mediamarkt.hu/hu/search.html?query=Samsung+R85H"),
        
        # Austria (AT)
        ("AT", "MediaMarkt", "Samsung", "https://www.mediamarkt.at/de/search.html?query=Samsung+R85H"),
        ("AT", "MediaMarkt", "Samsung", "https://www.mediamarkt.at/de/search.html?query=Samsung+R86H"),
        ("AT", "MediaMarkt", "LG", "https://www.mediamarkt.at/de/search.html?query=LG+MRGB"),
        
        # Greece (Public)
        ("GR", "Public", "LG", "https://www.public.gr/search?q=lg+mrgb"),
        ("GR", "Public", "Samsung", "https://www.public.gr/search?q=samsung+r85h"),
        ("GR", "Public", "Samsung", "https://www.public.gr/search?q=samsung+r95h"),
        
        # Italy (MediaWorld)
        ("IT", "MediaWorld", "Samsung", "https://www.mediaworld.it/it/search.html?query=Samsung+R85H"),
        ("IT", "MediaWorld", "Samsung", "https://www.mediaworld.it/it/search.html?query=Samsung+R95H"),
        ("IT", "MediaWorld", "LG", "https://www.mediaworld.it/it/search.html?query=LG+MRGB"),
        
        # Netherlands (MediaMarkt NL)
        ("NL", "MediaMarkt", "Samsung", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+R85H"),
        ("NL", "MediaMarkt", "Samsung", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+R95H"),
        ("NL", "MediaMarkt", "LG", "https://www.mediamarkt.nl/nl/search.html?query=LG+MRGB")
    ]
    
    print(f"[*] Executing {len(TARGET_SEARCHES)} targeted live searches via Firecrawl...")
    search_results = []
    for cc, ret, brand, url in TARGET_SEARCHES:
        print(f"  --> Searching {cc} {ret} {brand}: {url}")
        md, status = scrape_url_via_firecrawl(url)
        if status == 200 and md:
            matches = re.findall(r'\[\*\*([^\*\]]+)\*\*\]\((https?://[^\)]+/product/[^\)]+)\)(.*?)(?=\[\*\*|\Z)', md, re.DOTALL | re.IGNORECASE)
            if not matches:
                matches = re.findall(r'\[([^\*\]]+)\]\((https?://www\.fnac\.com/[^\)]+/[^\)]+)\)(.*?)(?=\n\[|\Z)', md, re.DOTALL | re.IGNORECASE)
            print(f"      Found {len(matches)} product links in search results")
            for title, p_url, chunk in matches:
                u_t = title.upper()
                if any(x in u_t for x in NON_TV_KEYWORDS):
                    continue
                if brand.upper() not in u_t and not any(k in u_t for k in ["MRGB", "R85", "R95", "R86", "R96"]):
                    continue
                sz = parse_size_from_text(title)
                code = parse_model_code_from_text(title, brand)
                p_matches = re.findall(r'(?:€|EUR|£|CHF|Ft|Kč)\s*([\d\.\s,]+)|([\d\.\s,]+)\s*(?:€|EUR|£|CHF|Ft|Kč)', chunk)
                p_val = 0.0
                for pm in p_matches:
                    p_val = clean_price_val(pm[0] or pm[1])
                    if p_val >= 400.0:
                        break
                if p_val >= 400.0 and sz >= 48:
                    search_results.append({
                        "country": cc,
                        "retailer": ret,
                        "brand": brand,
                        "size": sz,
                        "model_code": code,
                        "title": title.strip(),
                        "url": p_url.strip(),
                        "price": p_val,
                        "year": 2026,
                        "display_type": "Micro RGB",
                        "promo": "None",
                        "cashback": 0.0
                    })
        time.sleep(0.5)
        
    print(f"[+] Total newly discovered MRGB items from search: {len(search_results)}")
    for item in search_results:
        print(f"    {item['country']} {item['brand']} {item['size']}\" {item['model_code']}: {item['price']} ({item['url']})")
        
    with open("data/raw_mrgb_rescraped.json", "w", encoding="utf-8") as f:
        json.dump(search_results, f, ensure_ascii=False, indent=2)
        
    print("[*] Completed targeted search phase.")

if __name__ == "__main__":
    main()
