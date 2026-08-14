# -*- coding: utf-8 -*-
import json, re, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('public_eu/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'const priceData\s*=\s*(\{.*?\});', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    fr_2026 = data.get('FR', {}).get('2026', {})
    print('=== France 2026 MRGB ===')
    for row in fr_2026.get('MRGB', []):
        print(f"{row['pair_label']}: LG={row.get('lg_price_fnac')}€ ({row.get('lg_code_fnac')}) vs SAM={row.get('sam_price_fnac')}€ ({row.get('sam_code_fnac')})")
