import glob
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from promo_classifier import classify_promotions

def verify():
    promos = set()
    for f in glob.glob('data/raw_*.json'):
        try:
            data = json.load(open(f, encoding='utf-8'))
            items = data if isinstance(data, list) else data.get('products', data.get('items', []))
            for it in items:
                if isinstance(it, dict):
                    p = it.get('promo') or it.get('promotion') or it.get('General Promotions')
                    if p and str(p).strip() not in ['', 'None', '0']:
                        promos.add(str(p).strip())
        except Exception:
            pass

    print(f"Testing {len(promos)} unique promo strings...")
    
    clean_count = 0
    orig_count = 0
    cb_count = 0
    price_p_count = 0
    non_price_p_count = 0

    for p in sorted(promos):
        orig, cb, price_p, non_price_p = classify_promotions(p, price=1000.0)
        if orig > 0: orig_count += 1
        if cb > 0: cb_count += 1
        if price_p != "None": price_p_count += 1
        if non_price_p != "None": non_price_p_count += 1
        if orig > 0 or cb > 0 or price_p != "None" or non_price_p != "None":
            clean_count += 1

        sys.stdout.buffer.write(f"[{p}] -> Orig: {orig} | CB: {cb} | Price: {price_p} | NonPrice: {non_price_p}\n".encode('utf-8', errors='replace'))

    print(f"\nSummary:")
    print(f"Total Unique: {len(promos)}")
    print(f"With Was/Original Price: {orig_count}")
    print(f"With Cashback: {cb_count}")
    print(f"With Price Promo: {price_p_count}")
    print(f"With Non-Price Promo: {non_price_p_count}")

if __name__ == "__main__":
    verify()
