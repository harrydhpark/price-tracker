# -*- coding: utf-8 -*-
import sys
import os
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

with open('scripts/sample_mm_hu_search.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('window.__PRELOADED_STATE__')
if idx != -1:
    end_idx = html.find('</script>', idx)
    script_str = html[idx:end_idx].strip()
    raw = script_str.split('window.__PRELOADED_STATE__ =', 1)[1].strip()
    if raw.endswith(';'):
        raw = raw[:-1]
    
    # Replace JS undefined with null
    raw = re.sub(r':\s*undefined\b', ': null', raw)
    try:
        data = json.loads(raw)
        print("Successfully parsed window.__PRELOADED_STATE__ JSON!")
        
        # Look for search / product results
        with open("scripts/preloaded_state_fixed.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        store = data.get("reduxInitialStore", {})
        print("Store keys:", list(store.keys()))
        
        # Check products in catalog / search
        for k in ["products", "search", "catalog", "category", "entities"]:
            if k in store:
                print(f"Store has key: {k}")
                
        # Deep search for items
        def print_keys(d, depth=0):
            if depth > 3: return
            if isinstance(d, dict):
                for k, v in d.items():
                    print("  " * depth + f"- {k} ({type(v).__name__})")
                    print_keys(v, depth + 1)
        
        print_keys(store, 0)
        
    except Exception as e:
        print("JSON parse error:", e)

