# -*- coding: utf-8 -*-
import os
import sys
import re
import json
import glob

sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
SCRATCH_DIR = os.path.join(ROOT_DIR, "scratch_eu")
if not os.path.exists(SCRATCH_DIR):
    os.makedirs(SCRATCH_DIR)

def parse_currys_markdown(md_text, brand):
    items = []
    # Split by product blocks
    # Currys product headers: [**SAMSUNG ...**](https://www.currys.co.uk/products/...)
    cards = re.split(r'(?=\[\*\*(?:SAMSUNG|LG)[^\*]+\*\*\]\(https://www\.currys\.co\.uk/products/)', md_text)
    for card in cards:
        if not card.strip():
            continue
        title_m = re.search(r'\[\*\*([^\*]+)\*\*\]\(https://www\.currys\.co\.uk/products/[^\)]+\)', card)
        if not title_m:
            continue
        title = title_m.group(1).strip()
        
        # Price extraction: £999.97 or £1,099.00
        # Usually: [£999.97\\n\\nSave £99.03\\n\\nWas £1,099.00
        price_m = re.search(r'£([\d,]+(?:\.\d{2})?)', card)
        if not price_m:
            continue
        price_val = float(price_m.group(1).replace(',', ''))
        if price_val < 50.0:
            continue
            
        # Promo parsing
        t_no_sb = '\n'.join([line for line in card.split('\n') if not re.search(r'soundbar|soundbars', line, re.I)])
        
        sb_offer = "Up to 50% Off Soundbar w/ TV" if re.search(r'50%.*soundbars?|soundbars?.*50%', card, re.I) else None
        
        code_off_m = re.search(r'Get\s*(?:£|GBP)?\s*([\d,]+(?:\.\d{2})?)\s*off(?: marked price)?.*?(?:code|enter code)\s*([A-Z0-9]{3,15})', t_no_sb, re.I | re.DOTALL)
        code_pct_m = re.search(r'Get\s*(\d+)\s*%\s*off(?: marked price)?.*?(?:code|enter code)\s*([A-Z0-9]{3,15})', t_no_sb, re.I | re.DOTALL)
        
        direct_cut_str = None
        if code_off_m:
            direct_cut_str = f"Direct Cut GBP {code_off_m.group(1)} (Code: {code_off_m.group(2)})"
        elif code_pct_m:
            direct_cut_str = f"Direct Cut {code_pct_m.group(1)}% (Code: {code_pct_m.group(2)})"
            
        save_amt = re.search(r'Save £([\d,]+(?:\.\d{2})?)', t_no_sb)
        was_amt = re.search(r'Was £([\d,]+(?:\.\d{2})?)', t_no_sb)
        price_drop_str = None
        if was_amt and save_amt and not direct_cut_str:
            price_drop_str = f"Save GBP {save_amt.group(1)}; was GBP {was_amt.group(1)}"
        elif was_amt and not direct_cut_str:
            price_drop_str = f"was GBP {was_amt.group(1)}"
            
        cb_m = re.search(r'(?:Claim|Get|Up to)?\s*£(\d+)\s*cashback', t_no_sb, re.I)
        cb_str = f"GBP {cb_m.group(1)} Cashback" if (cb_m and int(cb_m.group(1)) >= 10) else None
        
        promo_parts = [direct_cut_str, cb_str, price_drop_str, sb_offer]
        promo = '; '.join(filter(None, promo_parts)) or "None"
        
        items.append({
            "name": title,
            "title": title,
            "price": price_val,
            "promo": promo
        })
    return items

def clean_fnac_text(text):
    return text.replace('\u202f', ' ').replace('\u00a0', ' ').replace('\u2009', ' ').replace('\u200b', '')

def parse_fnac_markdown(md_text, brand):
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
            
        # Strip installment text: 'Dès ... / mois', 'TAEG', 'Montant total dû'
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

def parse_mediamarkt_eu_markdown(md_text, brand, cc):
    items = []
    # MediaMarkt product link: [SAMSUNG ...](https://www.mediamarkt.../product/...) or [LG ...](...)
    cards = re.split(r'(?=\[(?:SAMSUNG|LG)[^\]]+\]\(https://www\.mediamarkt\.[a-z]+/|\[(?:SAMSUNG|LG)[^\]]+\]\(https://www\.mediaworld\.it/)', md_text)
    for card in cards:
        if not card.strip():
            continue
        title_m = re.search(r'\[((?:SAMSUNG|LG|OLED)[^\]]+)\]\((?:https://www\.mediamarkt\.[a-z]+/|https://www\.mediaworld\.it/)[^\)]+\)', card)
        if not title_m:
            continue
        title = title_m.group(1).strip()
        if len(title) < 8 or any(x in title.upper() for x in ["SOUNDBAR", "HIFI", "BEAMER", "ZUBEHÖR"]):
            continue
            
        # Price: 549,– € or 1099,00€ or 1.399,– €
        prices = re.findall(r'(\d[\d\s’\x27\x60,.]*)\s*(?:,–\s*€|,\d{2}\s*€|€)', card)
        clean_prices = []
        for p in prices:
            clean_p = p.replace('.', '').replace(' ', '').replace('\xa0', '').replace(',', '.')
            try:
                val = float(clean_p)
                if val >= 100.0:
                    clean_prices.append(val)
            except ValueError:
                pass
                
        if not clean_prices:
            continue
            
        selling_price = clean_prices[-1]
        
        promo_parts = []
        cb_m = re.search(r'(\d+)\s*€\s*Cashback', card, re.I)
        if cb_m:
            promo_parts.append(f"{cb_m.group(1)}€ Cashback")
            
        club_m = re.search(r'-([\d,]+)\s*€\s*Rabatt freischalten', card, re.I)
        if club_m:
            promo_parts.append(f"Club Coupon -{club_m.group(1)}€")
            
        pct_m = re.search(r'-(\d+)%', card)
        if pct_m and len(clean_prices) > 1:
            was_p = clean_prices[0]
            if was_p > selling_price:
                promo_parts.append(f"Sale {pct_m.group(1)}%; was EUR {was_p:.2f}")
                
        promo = '; '.join(promo_parts) if promo_parts else "None"
        
        items.append({
            "name": title,
            "title": title,
            "price": selling_price,
            "promo": promo
        })
    return items

def process_file(filepath, src, brand):
    with open(filepath, 'r', encoding='utf-8') as fp:
        content = fp.read()
    if src == 'currys':
        return parse_currys_markdown(content, brand)
    elif src == 'fnac':
        return parse_fnac_markdown(content, brand)
    elif src.startswith('mm-') or src.startswith('mw-'):
        return parse_mediamarkt_eu_markdown(content, brand, src.split('-')[-1])
    return []

if __name__ == '__main__':
    # Test or parse single file
    if len(sys.argv) >= 4:
        fpath, src, brand = sys.argv[1], sys.argv[2], sys.argv[3]
        res = process_file(fpath, src, brand)
        print(f"Extracted {len(res)} items from {fpath}")
        out_f = os.path.join(DATA_DIR, f"raw_{src}_{brand}.json")
        with open(out_f, 'w', encoding='utf-8') as of:
            json.dump(res, of, ensure_ascii=False, indent=2)
        print(f"Saved to {out_f}")
