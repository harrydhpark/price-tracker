# -*- coding: utf-8 -*-
import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')
from scripts.scrape_alza import extract_model_code_and_info

data_dir = 'data'

def process(step_file, brand):
    with open(step_file, 'r', encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'### Result\s*\n(.*?)\n### Ran Playwright code', text, re.DOTALL)
    data = json.loads(m.group(1))
    items = data.get('allItems', [])
    processed = []
    seen = set()
    for it in items:
        title = it['title']
        title_upper = title.upper()
        price = it['price']
        url = it['url']
        size_m = re.search(r'(\d{2,3})\s*(?:[″"]|inch|cm|\b)', title)
        size_val = 55
        if size_m:
            try:
                candidate = int(size_m.group(1))
                if 22 <= candidate <= 100:
                    size_val = candidate
            except:
                pass
        if size_val < 22:
            continue
        if any(x in title_upper for x in ['MONITOR', 'ODYSSEY', 'ULTRAGEAR', 'MYVIEW', 'SOUNDBAR']):
            continue
        model_code, series_code, year_val = extract_model_code_and_info(title_upper, brand, size_val)
        if year_val and year_val < 2025:
            continue
        if model_code in seen:
            continue
        seen.add(model_code)
        was_price = it.get('was_price', 0)
        discount_pct = int(round((was_price - price) / was_price * 100)) if was_price > price else 0
        processed.append({
            'brand': brand.capitalize(),
            'year': year_val or 2025,
            'series': series_code,
            'size': size_val,
            'model_code': model_code,
            'price': price,
            'was_price': was_price,
            'discount_pct': discount_pct,
            'promo': it.get('promo', 'None'),
            'cashback': it.get('cashback', 0),
            'title': title,
            'url': url
        })
    out = os.path.join(data_dir, f'raw_alza_{brand.lower()}.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)
    print(f'✅ Saved {len(processed)} {brand} models to {out}')

process(r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\702\output.txt', 'LG')
process(r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\710\output.txt', 'Samsung')
