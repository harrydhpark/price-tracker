# -*- coding: utf-8 -*-
import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/preloaded_state_fixed.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

apollo = d.get("apolloState", {})
print(f"Total apolloState keys: {len(apollo)}")

products = []
for k, v in apollo.items():
    if k.startswith("GraphqlProduct:"):
        # This is a product entry
        prod_id = v.get("id") or v.get("productId")
        title = v.get("title") or v.get("name") or v.get("description")
        brand = v.get("manufacturer") or v.get("brand")
        url = v.get("url") or v.get("pdpUrl")
        
        # Look for price in CofrPriceFeature
        price_val = None
        for pk, pv in apollo.items():
            if pk.startswith("CofrPriceFeature:") and f":{v.get('id')}" in pk or f":{prod_id}" in pk:
                # price object
                price_obj = pv.get("price", {})
                if isinstance(price_obj, dict):
                    # could be formattedPrice or amount or value
                    price_val = price_obj.get("amount") or price_obj.get("value") or price_obj.get("formattedPrice") or price_obj.get("currentPrice")
                    
        products.append({
            "id": prod_id,
            "title": title,
            "brand": brand,
            "url": url,
            "raw_product": v
        })

print(f"Found {len(products)} GraphqlProduct entries")
for i, p in enumerate(products[:10]):
    print(f"[{i+1}] ID: {p['id']} | Brand: {p['brand']} | Title: {str(p['title'])[:60]}")

