# -*- coding: utf-8 -*-
import json
import sys
import re
from scrapling.fetchers import StealthyFetcher

sys.stdout.reconfigure(encoding='utf-8')

fetcher = StealthyFetcher()

queries = [
    ("Samsung Micro RGB", "https://www.mediamarkt.hu/hu/search.html?query=Samsung+Micro+RGB"),
    ("Samsung R95H R85H", "https://www.mediamarkt.hu/hu/search.html?query=R95H+R85H"),
    ("Samsung MRE", "https://www.mediamarkt.hu/hu/search.html?query=MRE85+MRE75+MRE65+MRE55"),
    ("LG MRGB", "https://www.mediamarkt.hu/hu/search.html?query=MRGB87B+MRGB96B"),
    ("Cashback Promo", "https://www.mediamarkt.hu/hu/search.html?query=cashback"),
    ("Penzvisszafizetes", "https://www.mediamarkt.hu/hu/search.html?query=p%C3%A9nzvisszafizet%C3%A9s")
]

print("=== Checking mediamarkt.hu searches ===")
for label, url in queries:
    print(f"\n[QUERY] {label}: {url}")
    try:
        res = fetcher.fetch(url, solve_cloudflare=True, wait=2500, timeout=35000)
        html = str(res.html_content)
        print(f"  Status: {res.status}, Length: {len(html)}")
        
        idx = html.find("window.__PRELOADED_STATE__")
        if idx != -1:
            end_idx = html.find("</script>", idx)
            raw = html[idx:end_idx].split("window.__PRELOADED_STATE__ =", 1)[1].strip()
            if raw.endswith(";"): raw = raw[:-1]
            raw = re.sub(r':\s*undefined\b', ': null', raw)
            data = json.loads(raw)
            apollo = data.get("apolloState", {})
            
            # Products
            products = [v for k, v in apollo.items() if k.startswith("GraphqlProduct:")]
            print(f"  Found {len(products)} GraphqlProduct items")
            for p in products:
                title = p.get("title", "")
                mfr = p.get("manufacturer", "")
                p_id = p.get("id", "")
                
                # Price
                p_feat = p.get("cofrPriceFeature", {})
                price_id = p_feat.get("id", "") if isinstance(p_feat, dict) else ""
                price_obj = apollo.get(price_id, {}) if price_id else {}
                p_val = price_obj.get("price", {})
                amount = p_val.get("amount") if isinstance(p_val, dict) else None
                
                # Availability / Online Status
                avail_ref = p.get("cofrAvailabilityFeature", {})
                avail_id = avail_ref.get("id", "") if isinstance(avail_ref, dict) else ""
                avail_obj = apollo.get(avail_id, {}) if avail_id else {}
                is_online = avail_obj.get("isOnlineAvailable")
                
                # Badges / Promotions
                badges = []
                for b_ref in (p.get("badges") or []):
                    b_id = b_ref.get("id") if isinstance(b_ref, dict) else None
                    if b_id and b_id in apollo:
                        b_text = apollo[b_id].get("text") or apollo[b_id].get("label") or ""
                        badges.append(b_text)
                        
                print(f"   • [{mfr}] {title} | Price: {amount} Ft | Online: {is_online} | Badges: {badges}")
                
            # Promotions / Cashback banners in apolloState
            promos = [v for k, v in apollo.items() if "promo" in k.lower() or "badge" in k.lower() or "cashback" in k.lower()]
            if promos:
                print(f"  Found {len(promos)} promo/badge/cashback objects in page state:")
                for pr in promos[:5]:
                    print("     Promo obj:", {k: v for k, v in pr.items() if isinstance(v, (str, int, float, bool))})
    except Exception as e:
        print("  Error:", e)

