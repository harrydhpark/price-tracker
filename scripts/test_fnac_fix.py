# -*- coding: utf-8 -*-
import json, re, os, glob, sys

sys.stdout.reconfigure(encoding='utf-8')

def clean_fnac_text(text):
    text = text.replace('\u202f', ' ').replace('\u00a0', ' ').replace('\u2009', ' ').replace('\u200b', '')
    return text

def parse_fnac_cards_fixed(md_text, brand):
    md_text = clean_fnac_text(md_text)
    items = []
    pattern = r'\[(TV (?:' + brand + r')[^\]]+)\]\((https://www\.fnac\.com/[^/]+/a\d+/[^\)]+)\)'
    splits = list(re.finditer(pattern, md_text, re.IGNORECASE))
    
    for i, m in enumerate(splits):
        title = m.group(1).strip()
        url = m.group(2).strip()
        start = m.start()
        end = splits[i+1].start() if i+1 < len(splits) else len(md_text)
        chunk = md_text[start:end]
        
        if 'Reconditionné' in chunk or 'Occasion' in chunk:
            continue
            
        size_m = re.search(r'(\d{2,3})\s*(?:\"|cm|pouces)', title)
        size_val = int(size_m.group(1)) if size_m else 55
        if size_val > 100:
            size_val = int(round(size_val / 2.54))
            
        clean_chunk = re.sub(r'Dès\s+[\d\s,.]+\s*€\s*/\s*mois.*?(?=\n\n|\Z)', '', chunk, flags=re.I|re.DOTALL)
        clean_chunk = re.sub(r'Montant total dû\s*:\s*[\d\s,.]+\s*€', '', clean_chunk, flags=re.I)
        clean_chunk = re.sub(r'Bon Plan\s*-\s*[\d\s,.]+\s*€', '', clean_chunk, flags=re.I)
        clean_chunk = re.sub(r'[\d\s,.]+\s*€\s*de\s*(?:remise|réduction|d\'économie)', '', clean_chunk, flags=re.I)
        
        strong_prices = re.findall(r'\*\*([\d\s]+(?:,\d{2})?)\s*€\*\*', clean_chunk)
        before_was_prices = re.findall(r'([\d\s]+(?:,\d{2})?)\s*€\s*~~', clean_chunk)
        all_prices = re.findall(r'([\d\s]+(?:,\d{2})?)\s*€', clean_chunk)
        
        candidates = strong_prices + before_was_prices + all_prices
        clean_prices = []
        for p in candidates:
            cp = p.replace(' ', '').replace(',', '.')
            try:
                val = float(cp)
                # Size guards
                if size_val >= 70 and val < 600:
                    continue
                if size_val >= 55 and val < 450:
                    continue
                if size_val >= 48 and val < 350:
                    continue
                if val >= 150.0:
                    clean_prices.append(val)
            except ValueError:
                pass
                
        if not clean_prices:
            continue
            
        selling_price = clean_prices[0]
        
        was_m = re.search(r'~~([\d\s]+(?:,\d{2})?)\s*€~~', clean_chunk)
        promo = 'None'
        if was_m:
            was_val = was_m.group(1).replace(' ', '').replace(',', '.')
            try:
                was_num = float(was_val)
                if was_num > selling_price:
                    pct = int(round((was_num - selling_price) / was_num * 100))
                    promo = f'Sale {pct}%; was EUR {was_num:.2f}'
            except ValueError:
                pass
                
        items.append({
            'name': title,
            'title': title,
            'url': url,
            'price': selling_price,
            'promo': promo
        })
    return items

def load_step_md(step_num):
    p = f'C:/Users/harry.park/.gemini/antigravity/brain/b3c2e62f-fde9-42ac-b9e3-e3e459e36f9b/.system_generated/steps/{step_num}/output.txt'
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            d = json.load(f)
        return d.get('markdown', '')
    return ''

s_md = '\n'.join([load_step_md(s) for s in [129, 131, 133, 217, 219, 221, 223, 225]])
s_items = parse_fnac_cards_fixed(s_md, 'Samsung')
lg_md = '\n'.join([load_step_md(s) for s in [99, 135, 137, 227, 229, 231, 233, 235]])
lg_items = parse_fnac_cards_fixed(lg_md, 'LG')

print('Parsed Samsung items:', len(s_items))
for it in s_items:
    for target in ['S95H', 'S99H', 'QN74']:
        if target in it['name']:
            print(f"  Samsung: {it['name']} --> {it['price']} €")

print('Parsed LG items:', len(lg_items))
for it in lg_items:
    for target in ['OLED55B6', 'OLED65B6', 'QNED81B']:
        if target in it['name']:
            print(f"  LG: {it['name']} --> {it['price']} €")
