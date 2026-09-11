# -*- coding: utf-8 -*-
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'public_eu/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'const rawWeeklyChanges = (\[.*?\]);', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    w37 = [x for x in data if x.get('week') == 'W37']
    print(f'Total W37 change records across EU: {len(w37)}')
    
    by_ret = {}
    for it in w37:
        r = it.get('retailer', 'Unknown')
        by_ret.setdefault(r, []).append(it)
        
    for ret, items in sorted(by_ret.items()):
        drops = [x for x in items if x.get('changeType') == 'drop']
        hikes = [x for x in items if x.get('changeType') == 'hike']
        promos = [x for x in items if x.get('changeType') == 'promo']
        news = [x for x in items if x.get('changeType') == 'new']
        print(f"\n### {ret} (Total Changes: {len(items)})")
        print(f"- 인하(Drops): {len(drops)}건 | 인상(Hikes): {len(hikes)}건 | 프로모션(Promos): {len(promos)}건 | 신규(New): {len(news)}건")
        
        sample_changes = (drops + hikes)[:5]
        if sample_changes:
            print("  [주요 가격 변동 모델]")
            for x in sample_changes:
                old_p = x.get('oldPrice', 0)
                new_p = x.get('newPrice', 0)
                diff = x.get('diff', 0)
                curr = x.get('currency', 'EUR')
                brand = x.get('brand', '')
                model = x.get('model', '')
                size = x.get('size', '')
                ctype = '인하' if x.get('changeType') == 'drop' else '인상'
                print(f"  • [{brand}] {model} ({size}\"): {curr} {old_p:,.0f} ➔ {curr} {new_p:,.0f} ({diff:+,.0f}) [{ctype}]")

# Swiss Dashboard W37 changes
print("\n" + "="*50)
print("🇨🇭 Switzerland Retailers (W37 Changes)")
print("="*50)
with open(r'public/index.html', 'r', encoding='utf-8') as f:
    s_html = f.read()

m_s = re.search(r'const rawWeeklyChanges = (\[.*?\]);', s_html, re.DOTALL)
if m_s:
    s_data = json.loads(m_s.group(1))
    s_w37 = [x for x in s_data if x.get('week') == 'W37']
    print(f'Total W37 change records in Switzerland: {len(s_w37)}')
    
    s_by_ret = {}
    for it in s_w37:
        r = it.get('retailer', 'Unknown')
        s_by_ret.setdefault(r, []).append(it)
        
    for ret, items in sorted(s_by_ret.items()):
        drops = [x for x in items if x.get('changeType') == 'drop']
        hikes = [x for x in items if x.get('changeType') == 'hike']
        promos = [x for x in items if x.get('changeType') == 'promo']
        news = [x for x in items if x.get('changeType') == 'new']
        print(f"\n### {ret} (Total Changes: {len(items)})")
        print(f"- 인하(Drops): {len(drops)}건 | 인상(Hikes): {len(hikes)}건 | 프로모션(Promos): {len(promos)}건 | 신규(New): {len(news)}건")
        
        sample_changes = (drops + hikes)[:5]
        if sample_changes:
            print("  [주요 가격 변동 모델]")
            for x in sample_changes:
                old_p = x.get('oldPrice', 0)
                new_p = x.get('newPrice', 0)
                diff = x.get('diff', 0)
                curr = x.get('currency', 'CHF')
                brand = x.get('brand', '')
                model = x.get('model', '')
                size = x.get('size', '')
                ctype = '인하' if x.get('changeType') == 'drop' else '인상'
                print(f"  • [{brand}] {model} ({size}\"): {curr} {old_p:,.0f} ➔ {curr} {new_p:,.0f} ({diff:+,.0f}) [{ctype}]")
