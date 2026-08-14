# -*- coding: utf-8 -*-
import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/sample_mm_hu_search.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'window\.__PRELOADED_STATE__\s*=\s*({.+?});\s*</script>', html, re.DOTALL)
if m:
    raw = m.group(1)
    data = json.loads(raw)
    print("Parsed JSON successfully!")
    with open("scripts/preloaded_state.json", "w", encoding="utf-8") as pf:
        json.dump(data, pf, ensure_ascii=False, indent=2)
    print("Saved scripts/preloaded_state.json")
    
    # Check for products
    def find_products(obj, path=""):
        if isinstance(obj, dict):
            if "products" in obj and isinstance(obj["products"], (list, dict)):
                print(f"Found 'products' at {path}. Count: {len(obj['products'])}")
            if "items" in obj and isinstance(obj["items"], (list, dict)):
                print(f"Found 'items' at {path}. Count: {len(obj['items'])}")
            for k, v in obj.items():
                find_products(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, elem in enumerate(obj[:3]):
                find_products(elem, f"{path}[{i}]")
                
    find_products(data)

