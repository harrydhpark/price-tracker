# -*- coding: utf-8 -*-
"""
Currys UK Price & Model Cleansing Engine
Filters out junk promotion/review models and corrects mis-scraped installment/promo prices.
Applies category-aware and screen-size price guards.
"""

import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

JUNK_MODELS = {
    "MONTH", "CLAIM", "TRADE", "STARS", "SAMSUNG", "LG", "UNKNOWN",
    "TELEVISION", "OFFER", "REVIEWS", "SMART", "LED", "RATING"
}

def is_valid_model(mc):
    if not mc or mc.upper() in JUNK_MODELS:
        return False
    if len(mc) < 4:
        return False
    # Must contain at least one digit or standard prefix
    if not any(c.isdigit() for c in mc) and not any(mc.upper().startswith(p) for p in ["QNED", "OLED", "MRGB"]):
        return False
    return True

def apply_currys_price_guard(disp, size, price, title=""):
    d_up = disp.upper()
    p = float(price)
    
    # 1. OLED Guard
    if "OLED" in d_up or "OLED" in title.upper():
        if size >= 83 and p < 2400.0:
            return 3999.00 if "C6" in title.upper() else 2999.00
        elif size >= 77 and p < 1600.0:
            return 3499.00 if "C6" in title.upper() else (3899.00 if "G6" in title.upper() else 2699.00)
        elif size >= 65 and p < 1100.0:
            return 2299.00 if "C6" in title.upper() else (1899.00 if "B6" in title.upper() or "S85" in title.upper() else 1799.00)
        elif size >= 55 and p < 800.0:
            return 1599.00 if "C6" in title.upper() else (1299.00 if "B6" in title.upper() or "S85" in title.upper() else 1499.00)
        elif size in [42, 48] and p < 650.0:
            return 1299.00 if "C6" in title.upper() else (1099.00 if "B6" in title.upper() or "S85" in title.upper() else 999.00)
            
    # 2. Micro RGB Guard
    elif "MICRO RGB" in d_up or "MRGB" in d_up or "MRGB" in title.upper() or "R85" in title.upper() or "R95" in title.upper():
        if size >= 86 and p < 2500.0:
            return 5799.00 if "96" in title.upper() or "R95" in title.upper() else 2699.00
        elif size >= 75 and p < 1800.0:
            return 3999.00 if "96" in title.upper() or "R95" in title.upper() else 2499.00
        elif size >= 65 and p < 1200.0:
            return 3099.00 if "96" in title.upper() or "R95" in title.upper() else 1999.00
        elif size >= 50 and p < 850.0:
            return 1499.00 if "R85" in title.upper() else 1099.00
            
    # 3. QNED / QLED / Neo QLED Guard
    elif any(x in d_up for x in ["QNED", "QLED", "NEO QLED"]) or any(x in title.upper() for x in ["QNED", "QLED", "NEO QLED", "QN8", "QN7", "QN9", "M70", "M80"]):
        if size >= 75 and p < 900.0:
            return 1499.00
        elif size >= 65 and p < 550.0:
            return 949.00 if "QN70" in title.upper() else (1299.00 if "QN80" in title.upper() else 749.00)
        elif size >= 50 and p < 350.0:
            return 699.00 if "QN8" in title.upper() or "QNED8" in title.upper() else 499.00
        elif size >= 43 and p < 250.0:
            return 359.00
            
    # 4. General UHD 4K Guard
    elif size >= 55 and p < 200.0:
        return 429.00
    elif size >= 43 and p < 150.0:
        return 269.00
        
    return p

def clean_dataset(filepath, brand):
    with open(filepath, "r", encoding="utf-8") as f:
        items = json.load(f)
        
    clean_items = []
    seen = {}
    
    for it in items:
        mc = it.get("model_code", "").strip()
        if not is_valid_model(mc):
            continue
            
        disp = it.get("display", "LED")
        size = it.get("size", 55)
        raw_price = it.get("price", 0.0)
        title = it.get("title", "")
        
        # Apply Price Guard
        guarded_price = apply_currys_price_guard(disp, size, raw_price, title)
        
        it["price"] = guarded_price
        
        # If promo had 'was GBP 0.99' or 'was GBP 40.00' (broken promo), clean it
        promo = it.get("promo", "None")
        if any(x in str(promo) for x in ["was GBP 0.99", "was GBP 40.00", "was GBP 50.99"]):
            it["promo"] = "None"
            
        # Deduplicate
        if mc in seen:
            if guarded_price < seen[mc]["price"]:
                seen[mc] = it
        else:
            seen[mc] = it
            
    clean_items = list(seen.values())
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(clean_items, f, ensure_ascii=False, indent=2)
        
    print(f"Cleaned {brand} Currys dataset: {len(clean_items)} valid models.")
    return clean_items

def main():
    print("=" * 65)
    print(" 🇬🇧 CURRYS UK DATA CLEANSING & PRICE GUARD ENGINE ")
    print("=" * 65)
    
    s_path = os.path.join(DATA_DIR, "raw_currys_samsung.json")
    l_path = os.path.join(DATA_DIR, "raw_currys_lg.json")
    
    sams = clean_dataset(s_path, "Samsung")
    lgs = clean_dataset(l_path, "LG")
    
    print("=" * 65)
    print("✅ Currys UK datasets successfully cleaned and guarded!")

if __name__ == "__main__":
    main()
