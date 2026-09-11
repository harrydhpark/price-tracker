import json
import os
import re

data_dir = r"data"
files = [
    "raw_mediamarkt_samsung.json",
    "raw_mediamarkt_lg.json",
    "raw_interdiscount_samsung.json",
    "raw_interdiscount_lg.json",
    "raw_digitec_samsung.json",
    "raw_digitec_lg.json"
]

print("=== INSPECTING RAW SWISS JSON DATA ===")
for f in files:
    path = os.path.join(data_dir, f)
    if not os.path.exists(path):
        print(f"File not found: {f}")
        continue
    with open(path, "r", encoding="utf-8") as fp:
        try:
            items = json.load(fp)
        except Exception as e:
            print(f"Error loading {f}: {e}")
            continue
            
    print(f"\n[{f}] Total items: {len(items)}")
    
    cb_keywords = ["cashback", "cash back", "gutschein", "rabatt", "aktion", "chf", "fr.", "remise", "bon", "trade-in", "voucher", "soundbar", "geschenk"]
    
    matched_items = []
    for item in items:
        title = item.get("title", "") or item.get("name", "")
        promo = item.get("promo", "") or ""
        cb = item.get("cashback", 0)
        
        all_text = f"{title} {promo} {cb}".lower()
        
        found_kws = [kw for kw in cb_keywords if kw in all_text]
        if found_kws:
            matched_items.append((item.get("model_code", "Unknown"), item.get("price", 0), promo, found_kws, title[:60]))
            
    print(f"  -> Items with promo/cashback keywords: {len(matched_items)}")
    for m, p, promo, kws, t in matched_items[:15]:
        print(f"     - {m} (CHF {p}): promo='{promo}' | matched={kws} | title='{t}'")
