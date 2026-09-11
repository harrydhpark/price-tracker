# -*- coding: utf-8 -*-
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

# 1. EU Dashboard
with open('public_eu/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('const priceData = ')
end = text.find(';\n', start)
data = json.loads(text[start + len('const priceData = '):end])
w37_eu = data.get('weekly_changes', {}).get('W37', {})

print("=================================================================")
print("🇪🇺 Pan-European 11 Countries W37 Changes Breakdown")
print("=================================================================")
print("Summary:", json.dumps(w37_eu.get('summary'), indent=2))

by_country = {}
for it in w37_eu.get('items', []):
    c = it.get('country', 'Unknown')
    r = it.get('retailer', 'Unknown')
    by_country.setdefault(f"{c} ({r})", []).append(it)

for cr, items in sorted(by_country.items()):
    drops = [x for x in items if 'PRICE_DROP' in x.get('tags', [])]
    hikes = [x for x in items if 'PRICE_HIKE' in x.get('tags', [])]
    promos = [x for x in items if any('PROMO' in t or 'CASHBACK' in t for t in x.get('tags', []))]
    news = [x for x in items if 'NEW_MODEL' in x.get('tags', [])]
    print(f"\n### {cr}: 총 {len(items)}건 변동 (인하: {len(drops)}, 인상: {len(hikes)}, 프로모션: {len(promos)}, 신규: {len(news)})")
    for x in (drops + hikes)[:4]:
        b = x.get('brand')
        mc = x.get('model_code')
        sz = x.get('size')
        curr = x.get('currency')
        pp = x.get('prev_price')
        cp = x.get('curr_price')
        diff = x.get('price_diff')
        tag = '인하' if 'PRICE_DROP' in x.get('tags', []) else '인상'
        print(f"  • [{b}] {mc} ({sz}\"): {curr} {pp:,.0f} ➔ {curr} {cp:,.0f} ({diff:+,.0f}) [{tag}]")

# 2. Swiss Dashboard
with open('public/index.html', 'r', encoding='utf-8') as f:
    s_text = f.read()

start_s = s_text.find('const priceData = ')
end_s = s_text.find(';\n', start_s)
s_data = json.loads(s_text[start_s + len('const priceData = '):end_s])
w37_s = s_data.get('weekly_changes', {}).get('W37', {})

print("\n\n=================================================================")
print("🇨🇭 Switzerland 3 Retailers W37 Changes Breakdown")
print("=================================================================")
print("Summary:", json.dumps(w37_s.get('summary'), indent=2))

by_ret = {}
for it in w37_s.get('items', []):
    r = it.get('retailer', 'Unknown')
    by_ret.setdefault(r, []).append(it)

for ret, items in sorted(by_ret.items()):
    drops = [x for x in items if 'PRICE_DROP' in x.get('tags', [])]
    hikes = [x for x in items if 'PRICE_HIKE' in x.get('tags', [])]
    promos = [x for x in items if any('PROMO' in t or 'CASHBACK' in t for t in x.get('tags', []))]
    news = [x for x in items if 'NEW_MODEL' in x.get('tags', [])]
    print(f"\n### {ret}: 총 {len(items)}건 변동 (인하: {len(drops)}, 인상: {len(hikes)}, 프로모션: {len(promos)}, 신규: {len(news)})")
    for x in (drops + hikes)[:4]:
        b = x.get('brand')
        mc = x.get('model_code')
        sz = x.get('size')
        pp = x.get('prev_price')
        cp = x.get('curr_price')
        diff = x.get('price_diff')
        tag = '인하' if 'PRICE_DROP' in x.get('tags', []) else '인상'
        print(f"  • [{b}] {mc} ({sz}\"): CHF {pp:,.0f} ➔ CHF {cp:,.0f} ({diff:+,.0f}) [{tag}]")
