# -*- coding: utf-8 -*-
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('data/mediamarkt_hu_full.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

sec_items = [it for it in items if it.get('Brand', '').upper() == 'SAMSUNG' or it.get('brand', '').upper() == 'SAMSUNG']
print(f"Total Samsung items in DB: {len(sec_items)}")

def classify_samsung_year_accurate(model_code, title_upper):
    mc = model_code.upper()
    
    # 1. Clean country suffix like XXH, XXC, XXN, XXU, XXE, etc.
    mc_clean = re.sub(r'(?:XXH|XXC|XXN|XXU|XXE|XAU|XEN)$', '', mc)
    
    # 2. Check series + year letter pattern
    # Patterns: S90H, S95H, S85H, S90F, S95F, S85F
    # QN900H, QN90H, QN80H, QN70H, QN900F, QN90F, QN80F, QN70F
    # Q8FA, Q7FA, Q6FA, Q80F, Q70F, Q70H
    # LS03HW, LS03FW, LS03H, LS03F
    # M80H, M70H, R95H, R85H
    # U8072H, U8072F, U8000H, U8000F, U7022F
    
    # 2026 Series patterns
    if any(x in mc_clean for x in [
        "S95H", "S90H", "S85H", "S99H",
        "QN900H", "QN800H", "QN95H", "QN90H", "QN85H", "QN80H", "QN70H", "QN72H", "QN82H",
        "M80H", "M70H", "M82H", "M72H", "R95H", "R85H", "R86H",
        "LS03H", "LS03HW",
        "U8000H", "U8072H", "U8070H", "U8090H", "U8005H", "U8500H",
        "Q70H", "Q80H", "Q60H"
    ]):
        return 2026
        
    # 2025 Series patterns
    if any(x in mc_clean for x in [
        "S95F", "S90F", "S85F", "S91F", "S92F",
        "QN990F", "QN900F", "QN800F", "QN95F", "QN90F", "QN85F", "QN80F", "QN70F", "QN72F", "QN74F", "QN82F",
        "Q8F", "Q7F", "Q6F", "Q8FA", "Q7FA", "Q6FA", "Q80F", "Q70F", "Q60F",
        "LS03F", "LS03FW",
        "U8000F", "U8072F", "U8070F", "U8090F", "U8005F", "U7022F", "U7020F", "U7025F", "U7000F",
        "H5002F"
    ]):
        return 2025

    # 2024 Series patterns
    if any(x in mc_clean for x in [
        "S95D", "S90D", "S85D", "QN900D", "QN90D", "QN85D", "QN80D", "QN70D", "Q60D", "LS03D", "DU8000", "DU7000", "CU8000"
    ]):
        return 2024
        
    # Check general match
    m_yr = re.search(r'(?:S\d{2}|QN\d{2,3}|Q\d{1,2}|M\d{2}|R\d{2}|LS\d{2}|U\d{4}|H\d{4})([HFD])', mc_clean)
    if m_yr:
        letter = m_yr.group(1)
        if letter == 'H': return 2026
        if letter == 'F': return 2025
        if letter == 'D': return 2024
        
    if "2026" in title_upper: return 2026
    if "2025" in title_upper: return 2025
    if "2024" in title_upper: return 2024
    
    return 2025

counts = {2026: 0, 2025: 0, 2024: 0}
for it in sec_items:
    mc = it.get('Model Code') or it.get('model_code') or ''
    t = (it.get('Title') or it.get('title') or '').upper()
    yr = classify_samsung_year_accurate(mc, t)
    counts[yr] = counts.get(yr, 0) + 1
    if counts[yr] <= 5 or yr == 2026:
        print(f"[{yr}] Model: {mc:<20} | Title: {t[:60]}")

print("\nSummary Breakdown:", counts)
