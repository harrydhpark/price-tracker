# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('public_eu/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('const priceData = ')
end = text.find(';\n', start)
data = json.loads(text[start + len('const priceData = '):end])
w37 = data.get('weekly_changes', {}).get('W37', {})

items = w37.get('items', [])
print(f"Total W37 items: {len(items)}")

by_c = {}
for it in items:
    c = it.get('country', 'Unknown')
    by_c.setdefault(c, []).append(it)

for c, c_items in sorted(by_c.items()):
    ret = c_items[0].get('retailer') if c_items else ''
    drops = [x for x in c_items if 'PRICE_DROP' in x.get('tags', [])]
    hikes = [x for x in c_items if 'PRICE_HIKE' in x.get('tags', [])]
    promos = [x for x in c_items if any('PROMO' in t or 'CASHBACK' in t for t in x.get('tags', []))]
    news = [x for x in c_items if 'NEW_MODEL' in x.get('tags', [])]
    delisted = [x for x in c_items if 'DELISTED' in x.get('tags', [])]
    
    print(f"\n=======================================================")
    print(f"🌍 국가: {c} | 유통: {ret} (총 {len(c_items)}건 변동)")
    print(f"  - 인하: {len(drops)}건 | 인상: {len(hikes)}건 | 프로모션 변경: {len(promos)}건 | 신규 진입: {len(news)}건 | 단종/품절: {len(delisted)}건")
    print(f"=======================================================")
    
    if drops:
        print("  🔻 [가격 인하 모델]")
        for d in drops:
            b = d.get('brand')
            mc = d.get('model_code')
            sz = d.get('size')
            disp = d.get('display')
            curr = d.get('currency')
            pp = d.get('prev_price')
            cp = d.get('curr_price')
            diff = d.get('price_diff')
            pct = d.get('price_diff_pct')
            pr = d.get('curr_promo')
            print(f"    • [{b}] {mc} ({sz}\" {disp}): {curr} {pp:,.0f} ➔ {curr} {cp:,.0f} ({diff:+,.0f}, {pct:+.1f}%) | {pr}")
            
    if hikes:
        print("  🔺 [가격 인상 모델]")
        for h in hikes:
            b = h.get('brand')
            mc = h.get('model_code')
            sz = h.get('size')
            disp = h.get('display')
            curr = h.get('currency')
            pp = h.get('prev_price')
            cp = h.get('curr_price')
            diff = h.get('price_diff')
            pct = h.get('price_diff_pct')
            print(f"    • [{b}] {mc} ({sz}\" {disp}): {curr} {pp:,.0f} ➔ {curr} {cp:,.0f} ({diff:+,.0f}, {pct:+.1f}%)")
            
    if promos:
        print("  🎁 [프로모션 변동 모델]")
        for p in promos[:8]:
            b = p.get('brand')
            mc = p.get('model_code')
            sz = p.get('size')
            old_pr = p.get('prev_promo')
            new_pr = p.get('curr_promo')
            print(f"    • [{b}] {mc} ({sz}\"): {old_pr} ➔ {new_pr}")
        if len(promos) > 8:
            print(f"    ... 외 {len(promos) - 8}개 모델")

    if news:
        print("  ✨ [신규 출시/추적 모델]")
        for n in news:
            b = n.get('brand')
            mc = n.get('model_code')
            sz = n.get('size')
            disp = n.get('display')
            curr = n.get('currency')
            cp = n.get('curr_price')
            print(f"    • [{b}] {mc} ({sz}\" {disp}): {curr} {cp:,.0f}")
