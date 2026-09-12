# -*- coding: utf-8 -*-
import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_alza import extract_model_code_and_info, update_eu_excel_tracker

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")

def process_alza_dump(step_file):
    print(f"[ALZA SYNC] Reading dump from {step_file}")
    with open(step_file, 'r', encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'### Result\s*\n(.*?)\n### Ran Playwright code', text, re.DOTALL)
    if m:
        raw_json_str = m.group(1).strip()
    else:
        s_idx = text.find('{')
        e_idx = text.rfind('}')
        raw_json_str = text[s_idx:e_idx+1]
        
    raw_data = json.loads(raw_json_str)
    brand_data = raw_data.get("data", {})
    
    all_processed = {"Samsung": [], "LG": []}
    
    for brand in ["Samsung", "LG"]:
        items = brand_data.get(brand, [])
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
                    if 22 <= candidate <= 115:
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
            
        out = os.path.join(DATA_DIR, f'raw_alza_{brand.lower()}.json')
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
        print(f'✅ Saved {len(processed)} {brand} models to {out}')
        all_processed[brand] = processed
        
    print(f"\n[ALZA EXCEL SYNC] Updating EU workbook with Alza Czech sheets...")
    update_eu_excel_tracker(all_processed["LG"], all_processed["Samsung"])
    print("[ALZA DONE] Alza Czech Republic collection and synchronization completed cleanly!")

if __name__ == '__main__':
    dump_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\harry.park\.gemini\antigravity\brain\1c8f1fcd-c6b2-4806-abbc-780188e26593\.system_generated\steps\955\output.txt"
    process_alza_dump(dump_path)
