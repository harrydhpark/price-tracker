# -*- coding: utf-8 -*-
import os, sys, json, re
from bs4 import BeautifulSoup
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
DATA_DIR = os.path.abspath('data')

def clean_model_code(text):
    text = text.upper()
    # Common model patterns
    m = re.search(r'\b(OLED\d{2}[A-Z0-9]{2,8}|\d{2}[A-Z]{3,6}\d{2}[A-Z0-9]{1,6}|[A-Z0-9]{2}\d{2}[A-Z0-9]{3,10}|MRE\d{2}[A-Z0-9]{2,6}|TU\d{2}[A-Z0-9]{2,8}|UE\d{2}[A-Z0-9]{2,8}|QE\d{2}[A-Z0-9]{2,8}|GQ\d{2}[A-Z0-9]{2,8}|TQ\d{2}[A-Z0-9]{2,8})\b', text)
    if m:
        return m.group(1)
    return ""

def extract_size(text):
    m = re.search(r'\b(98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:inch|zoll|pollici|pouces|cm|\b)', text.upper())
    if m:
        return int(m.group(1))
    m_mc = re.search(r'(?:OLED|QE|UE|GQ|TQ|QNED|NANO|UA|NU|TU|F-QE)?(\d{2})[A-Z0-9]', text.upper())
    if m_mc:
        val = int(m_mc.group(1))
        if val in [98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:
            return val
    return 0

def get_tv_profile(text):
    u = text.upper()
    size = extract_size(u)
    
    # 1. Category & Series determination
    category = "UHD"
    series = "OTHER"
    
    if "MRGB" in u or "MICRO RGB" in u or re.search(r'\bR[89]\d[FH]', u) or "MRE" in u:
        category = "MRGB"
        m = re.search(r'(MRGB\d{2}|R\d{2})', u)
        if m: series = m.group(1)
    elif "OLED" in u or re.search(r'\bS[89]\d[FH]', u):
        category = "OLED"
        m = re.search(r'\b(C6|G6|B6|W6|M6|C5|G5|B5|S90|S92|S93|S95|S99|S85)\b', u)
        if m: series = m.group(1)
        elif re.search(r'OLED\d{2}([CGBMW][56])', u):
            series = re.search(r'OLED\d{2}([CGBMW][56])', u).group(1)
    elif "QNED" in u:
        category = "QNED"
        m = re.search(r'(QNED\d{2})', u)
        if m: series = m.group(1)
    elif "NEO QLED" in u or "QLED" in u or re.search(r'\b(Q\d{1,2}F|QN\d{2}[FH]|M\d{2}[FH]|LS03)\b', u):
        category = "QLED"
        m = re.search(r'\b(Q7F|Q8F|QN70|QN74|QN80|QN82|QN85|QN90|M70|M72|M80|LS03)\b', u)
        if m: series = m.group(1)
    elif "STANBYME" in u or re.search(r'\b(LX[567]|27LX)\b', u):
        category = "LIFESTYLE"
        series = "LX"
    else:
        category = "UHD"
        m = re.search(r'\b(NU85|NU80|UA75|UA77|UT80|U8000|U8070|U8079|DU90|DU80|F6000)\b', u)
        if m: series = m.group(1)
        
    return {
        'size': size,
        'category': category,
        'series': series
    }

def passes_price_guard(profile, price):
    cat = profile['category']
    size = profile['size']
    
    if cat == 'OLED':
        if size in [42, 48] and price < 500: return False
        if size == 55 and price < 700: return False
        if size == 65 and price < 950: return False
        if size >= 77 and price < 1400: return False
    elif cat == 'MRGB':
        if size >= 75 and price < 1800: return False
        if size < 75 and price < 750: return False
    elif cat in ['QNED', 'QLED']:
        if size == 43 and price < 220: return False
        if size in [50, 55] and price < 300: return False
        if size >= 65 and price < 450: return False
    else: # UHD
        if size == 43 and price < 150: return False
        if size >= 55 and price < 200: return False

    return price >= 120.0

def extract_mms_products(dump_path, brand):
    if not os.path.exists(dump_path):
        return []
    with open(dump_path, 'r', encoding='utf-8') as f:
        html = json.load(f).get('rawHtml', '')
    idx = html.find('window.__PRELOADED_STATE__ = ')
    if idx == -1:
        return []
    end_idx = html.find('</script>', idx)
    json_str = html[idx + len('window.__PRELOADED_STATE__ = '):end_idx].rstrip('; ')
    json_str = re.sub(r':\s*undefined\b', ':null', json_str)
    state = json.loads(json_str)
    apollo = state.get('apolloState', {})
    
    price_map = {}
    strike_map = {}
    for k, v in apollo.items():
        if k.startswith('CofrPriceFeature:') and isinstance(v, dict):
            p_info = v.get('price') or {}
            amt = p_info.get('amount')
            s_info = v.get('strikePrice') or {}
            s_amt = s_info.get('amount')
            pid = v.get('id', '')
            clean_pid = str(pid).split(':')[-1]
            if amt and clean_pid:
                price_map[clean_pid] = float(amt)
            if s_amt and clean_pid:
                strike_map[clean_pid] = float(s_amt)
                
    items = []
    for k, v in apollo.items():
        if isinstance(v, dict) and v.get('__typename') == 'GraphqlProduct':
            pid = str(v.get('id', ''))
            title = v.get('title') or v.get('name') or ''
            url = v.get('url') or ''
            price = price_map.get(pid)
            strike = strike_map.get(pid)
            if not price or not title:
                continue
            if brand.upper() not in title.upper() and brand.upper() not in url.upper():
                continue
            full_desc = url + " " + title
            prof = get_tv_profile(full_desc)
            if not passes_price_guard(prof, price):
                continue
            items.append({
                'title': title,
                'url': url,
                'price': price,
                'strike': strike,
                'model_code': clean_model_code(full_desc),
                'profile': prof
            })
    return items

def extract_fnac_products(dump_path, brand):
    if not os.path.exists(dump_path):
        return []
    with open(dump_path, 'r', encoding='utf-8') as f:
        html = json.load(f).get('rawHtml', '')
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find_all('article') or soup.find_all(attrs={'class': re.compile('Article-item|f-productListItem')})
    items = []
    for c in cards:
        t_el = c.find(attrs={'class': re.compile('Article-title|title')})
        title = t_el.get_text(strip=True) if t_el else ''
        if not title or brand.upper() not in title.upper():
            continue
        p_el = c.find(attrs={'class': re.compile('userPrice|price|Price')})
        if not p_el:
            continue
        raw_text = p_el.get_text(strip=True).replace('\xa0', ' ').replace('\u202f', ' ')
        m = re.findall(r'(\d[\d\s\.,]*\d)\s*€', raw_text)
        if m:
            clean_str = m[0].replace(' ', '').replace(',', '.')
            try:
                val = float(clean_str)
                prof = get_tv_profile(title)
                if passes_price_guard(prof, val):
                    items.append({
                        'title': title,
                        'url': '',
                        'price': val,
                        'strike': None,
                        'model_code': clean_model_code(title),
                        'profile': prof
                    })
            except:
                pass
    return items

dumps_map = {
    'mm-de': {
        'samsung': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\674\output.txt',
        'lg': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1051\output.txt'
    },
    'mm-es': {
        'samsung': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\980\output.txt',
        'lg': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1053\output.txt'
    },
    'mw-it': {
        'samsung': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1014\output.txt',
        'lg': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1055\output.txt'
    },
    'mm-at': {
        'samsung': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1057\output.txt',
        'lg': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1059\output.txt'
    },
    'mm-nl': {
        'samsung': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1063\output.txt',
        'lg': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1065\output.txt'
    },
    'fnac': {
        'samsung': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1019\output.txt',
        'lg': r'C:\Users\harry.park\.gemini\antigravity\brain\8e83cb6c-ceec-4cb3-a08e-ecaf3d5e6d6b\.system_generated\steps\1067\output.txt'
    }
}

total_updates = 0
for r_key, b_dumps in dumps_map.items():
    for brand, dump_file in b_dumps.items():
        if r_key == 'fnac':
            live_items = extract_fnac_products(dump_file, brand)
        else:
            live_items = extract_mms_products(dump_file, brand)
            
        raw_json_path = os.path.join(DATA_DIR, f"raw_{r_key}_{brand}.json")
        if not os.path.exists(raw_json_path):
            continue
            
        with open(raw_json_path, 'r', encoding='utf-8') as f:
            current_items = json.load(f)
            
        updated_count = 0
        for item in current_items:
            m_text = (item.get('name') or item.get('title') or item.get('model_code') or '') + ' ' + (item.get('url') or '')
            m_mc = clean_model_code(m_text)
            m_prof = get_tv_profile(m_text)
            
            for live in live_items:
                l_mc = live['model_code']
                l_prof = live['profile']
                
                # Strict matching criteria:
                # 1. Exact model code match (if both non-empty and >= 6 chars)
                # 2. Or exact match of: Category + Size + Series (when series is not OTHER)
                matched = False
                if m_mc and l_mc and len(m_mc) >= 6 and len(l_mc) >= 6 and (m_mc in l_mc or l_mc in m_mc):
                    matched = True
                elif m_prof['size'] > 0 and m_prof['size'] == l_prof['size'] and m_prof['category'] == l_prof['category'] and m_prof['series'] == l_prof['series'] and m_prof['series'] != 'OTHER':
                    matched = True
                            
                if matched:
                    if item.get('price') != live['price']:
                        display_name = m_mc or (item.get('name') or item.get('title') or '')[:30]
                        print(f"[{r_key.upper()} - {brand.upper()}] {display_name} ({m_prof['size']}\" {m_prof['series']}): €{item['price']} -> €{live['price']} (Live Probe: {live['title'][:35]})")
                        item['price'] = live['price']
                        if live.get('strike') and live['strike'] > live['price']:
                            item['original_price'] = live['strike']
                        updated_count += 1
                        total_updates += 1
                    break
                    
        # Update raw json file with current modified time
        with open(raw_json_path, 'w', encoding='utf-8') as f:
            json.dump(current_items, f, ensure_ascii=False, indent=2)
        print(f"✅ [{r_key} - {brand}] Verified {len(current_items)} models ({updated_count} price updates applied)")

print(f"\nCompleted! Total live price updates across Western Europe: {total_updates}")

