# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('public_eu/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx = html.find('const priceData = ')
if idx != -1:
    end_idx = html.find('};\n', idx)
    json_str = html[idx + len('const priceData = '):end_idx + 1]
    data = json.loads(json_str)
    
    print('Countries in priceData:', [c for c in data.keys() if c != 'history'])
    if 'HU' in data:
        hu_2026 = data['HU'].get('2026', {})
        hu_2025 = data['HU'].get('2025', {})
        print('\n=== HU 2026 Categories ===')
        for cat, pairs in hu_2026.items():
            print(f'Category [{cat}]: {len(pairs)} pairs')
            for p in pairs:
                lg_code = p.get('lg_code_mm') or 'None'
                lg_p = p.get('lg_price_mm') or 0
                sam_code = p.get('sam_code_mm') or 'None'
                sam_p = p.get('sam_price_mm') or 0
                if lg_p > 0 or sam_p > 0:
                    print(f"  • {p['pair_label']}: LG={lg_code} ({lg_p:,} Ft) vs SEC={sam_code} ({sam_p:,} Ft)")
                
        print('\n=== HU 2025 Categories ===')
        for cat, pairs in hu_2025.items():
            print(f'Category [{cat}]: {len(pairs)} pairs')
            for p in pairs:
                lg_code = p.get('lg_code_mm') or 'None'
                lg_p = p.get('lg_price_mm') or 0
                sam_code = p.get('sam_code_mm') or 'None'
                sam_p = p.get('sam_price_mm') or 0
                if lg_p > 0 or sam_p > 0:
                    print(f"  • {p['pair_label']}: LG={lg_code} ({lg_p:,} Ft) vs SEC={sam_code} ({sam_p:,} Ft)")

