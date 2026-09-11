# -*- coding: utf-8 -*-
import json, re, sys, os

sys.stdout.reconfigure(encoding='utf-8')

with open('data/eu_price_dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('const priceData = ')
if idx != -1:
    end_idx = text.find(';</script>', idx)
    if end_idx == -1: end_idx = text.find(';\n', idx)
    json_str = text[idx + len('const priceData = '):end_idx]
    data = json.loads(json_str)
    
    print("=== UK 2026 PAIRS IN DASHBOARD ===")
    uk_2026 = data.get('UK', {}).get('2026', {})
    print(f"UK 2026 categories: {list(uk_2026.keys()) if isinstance(uk_2026, dict) else len(uk_2026)}")
    if isinstance(uk_2026, dict):
        for cat, pairs in uk_2026.items():
            print(f" -- Category: {cat} ({len(pairs)} pairs) --")
            for p in pairs:
                print(f"    {p.get('size')}in {p.get('pair_label')} -> LG: £{p.get('lg_price_currys')} ({p.get('lg_code_currys')}) vs SAM: £{p.get('sam_price_currys')} ({p.get('sam_code_currys')})")

    print("\n=== UK 2025 PAIRS IN DASHBOARD ===")
    uk_2025 = data.get('UK', {}).get('2025', [])
    print(f"UK 2025 pairs: {len(uk_2025)}")
    for p in uk_2025[:5]:
        print(f"  {p.get('size')}in {p.get('pair_label')} -> LG: £{p.get('lg_price_currys')} ({p.get('lg_code_currys')}) vs SAM: £{p.get('sam_price_currys')} ({p.get('sam_code_currys')})")

    print("\n=== UK W37 WEEKLY CHANGES IN DASHBOARD ===")
    wc = data.get('weekly_changes', {})
    w37 = wc.get('W37', {})
    items = w37.get('items', []) if isinstance(w37, dict) else w37
    uk_changes = [c for c in items if c.get('country') == 'UK']
    print(f"UK W37 changes count: {len(uk_changes)}")
    for c in uk_changes[:15]:
        print(f"  {c.get('brand')} {c.get('model')} ({c.get('size')}in): Old £{c.get('old_price')} -> New £{c.get('new_price')} [{c.get('change_type')}]")

else:
    print("Could not find const priceData")
