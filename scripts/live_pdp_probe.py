# -*- coding: utf-8 -*-
"""
High-Speed Multithreaded Master Product URL Live PDP Probe & Replenishment Engine
1. Automatically identifies today's survey workbook across Europe and Switzerland.
2. Cross-references all registered product URLs in data/master_product_urls.json.
3. Detects models missing from active search sheets.
4. Uses ThreadPoolExecutor (10 workers) with curl_cffi for blazing fast live verification.
5. Injects verified active in-stock models into today's Excel workbook with ZERO historical fallback.
"""

import os
import sys
import json
import re
import time
import glob
import urllib.request
import openpyxl
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
HISTORY_EU_DIR = os.path.join(ROOT_DIR, "History_EU")
MASTER_REGISTRY_PATH = os.path.join(DATA_DIR, "master_product_urls.json")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
}

def parse_price_number(text):
    if not text:
        return 0.0
    s = str(text).replace('€', '').replace('£', '').replace('CHF', '').replace('Kč', '').replace('Ft', '')
    s = s.replace('\xa0', '').replace('\u202f', ' ').replace(' ', '').strip()
    if not s:
        return 0.0
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    nums = re.findall(r'\d+(?:\.\d+)?', s)
    return float(nums[0]) if nums else 0.0

def get_latest_workbook(pattern):
    candidates = glob.glob(os.path.join(DATA_DIR, pattern))
    candidates = [f for f in candidates if not os.path.basename(f).startswith("~$")]
    return sorted(candidates)[-1] if candidates else None

def probe_single_candidate(cand):
    url = cand.get('url')
    b_name = cand.get('brand', '')
    size_val = cand.get('size', 55)
    m_code = cand.get('model_code', '')

    html = None
    try:
        from curl_cffi import requests as cffi_requests
        r = cffi_requests.get(url, impersonate='chrome124', timeout=5)
        if r.status_code == 200:
            html = r.text
    except Exception:
        pass

    if not html:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    html = resp.read().decode('utf-8', errors='ignore')
        except Exception:
            return cand, None

    if not html or len(html) < 2000:
        return cand, None

    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(' ', strip=True)
    text_upper = text.upper()

    out_patterns = [
        "OUT OF STOCK", "CURRENTLY UNAVAILABLE", "NO LONGER AVAILABLE", "SORRY, THIS PRODUCT IS NO LONGER",
        "PRODEJ SKONČIL", "NEDOSTUPNÉ", "UKONČEN PRODEJ", "NENÍ SKLADEM", "TĚŠÍME SE NA DALŠÍ",
        "NICHT MEHR VERFÜGBAR", "AUSVERKAUFT", "CURRENTLY OUT OF STOCK",
        "ÉPUISÉ", "INDISPONIBLE", "PRODUIT ÉPUISÉ",
        "ESGOTADO", "INDISPONÍVEL", "NON DISPONIBILE", "ESAURITO",
        "ΕΞΑΝΤΛΗΘΗΚΕ", "ΜΗ ΔΙΑΘΕΣΙΜΟ", "ΠΡΟΣΩΡΙΝΑ ΜΗ ΔΙΑΘΕΣΙΜΟ"
    ]
    if any(pat in text_upper for pat in out_patterns):
        return cand, {"status": "out_of_stock", "price": 0.0}

    pval = 0.0
    orig_pval = 0.0
    for s in soup.find_all('script', type='application/ld+json'):
        try:
            d = json.loads(s.string)
            if isinstance(d, dict):
                offers = d.get('offers')
                if isinstance(offers, dict):
                    if offers.get('availability') and any(x in str(offers.get('availability')).lower() for x in ['outofstock', 'discontinued']):
                        return cand, {"status": "out_of_stock", "price": 0.0}
                    p = offers.get('price')
                    if p: pval = float(p)
                elif isinstance(offers, list) and len(offers) > 0:
                    p = offers[0].get('price')
                    if p: pval = float(p)
            if pval > 50.0:
                break
        except Exception:
            pass

    if pval < 50.0:
        clean_text = re.sub(r'(?:Save|Was|Rabatt|Cashback|Gutschein|de remise|όφελος)\s*[:£€$\d\.\,\s]+', '', text, flags=re.I)
        m = re.findall(r'([£€$]\s*[\d\.,]+|[\d\.,\s]+(?:\s*€|\s*,-|\s*Kč|\s*Ft|\s*CHF))', clean_text)
        for cand_str in m:
            num = parse_price_number(cand_str)
            if 80.0 <= num <= 25000.0 and num not in [2024, 2025, 2026]:
                pval = num
                break

    if pval < 80.0:
        return cand, None

    if size_val >= 75 and pval < 450.0:
        return cand, None
    elif size_val >= 55 and pval < 250.0:
        return cand, None
    elif size_val >= 42 and pval < 150.0:
        return cand, None

    return cand, {
        "status": "in_stock",
        "price": pval,
        "original_price": orig_pval or pval
    }

def replenish_workbook(target_wb_path, master_registry):
    print(f"\n[REPLENISH] Auditing target workbook: {target_wb_path}", flush=True)
    wb = openpyxl.load_workbook(target_wb_path)

    total_added = 0
    total_checked = 0
    total_oos = 0

    sheet_retailer_map = {
        'Currys_UK_SAMSUNG_Full': ('UK', 'Currys', 'SAMSUNG'),
        'Currys_UK_LG_Full': ('UK', 'Currys', 'LG'),
        'MediaMarkt_DE_SAMSUNG_Full': ('DE', 'MediaMarkt', 'SAMSUNG'),
        'MediaMarkt_DE_LG_Full': ('DE', 'MediaMarkt', 'LG'),
        'MediaMarkt_AT_SAMSUNG_Full': ('AT', 'MediaMarkt', 'SAMSUNG'),
        'MediaMarkt_AT_LG_Full': ('AT', 'MediaMarkt', 'LG'),
        'MediaMarkt_ES_SAMSUNG_Full': ('ES', 'MediaMarkt', 'SAMSUNG'),
        'MediaMarkt_ES_LG_Full': ('ES', 'MediaMarkt', 'LG'),
        'MediaMarkt_NL_SAMSUNG_Full': ('NL', 'MediaMarkt', 'SAMSUNG'),
        'MediaMarkt_NL_LG_Full': ('NL', 'MediaMarkt', 'LG'),
        'MediaWorld_IT_SAMSUNG_Full': ('IT', 'MediaWorld', 'SAMSUNG'),
        'MediaWorld_IT_LG_Full': ('IT', 'MediaWorld', 'LG'),
        'Fnac_FR_SAMSUNG_Full': ('FR', 'Fnac', 'SAMSUNG'),
        'Fnac_FR_LG_Full': ('FR', 'Fnac', 'LG'),
        'Alza_CZ_Samsung': ('CZ', 'Alza', 'SAMSUNG'),
        'Alza_CZ_LG': ('CZ', 'Alza', 'LG'),
        'Public_GR_Samsung': ('GR', 'Public', 'SAMSUNG'),
        'Public_GR_LG': ('GR', 'Public', 'LG'),
        'MediaMarkt_HU_Samsung': ('HU', 'MediaMarkt', 'SAMSUNG'),
        'MediaMarkt_HU_LG': ('HU', 'MediaMarkt', 'LG'),
        'MediaMarkt_Samsung_Full': ('CH', 'MediaMarkt', 'SAMSUNG'),
        'MediaMarkt_LG_Full': ('CH', 'MediaMarkt', 'LG'),
        'Interdiscount_Samsung_Full': ('CH', 'Interdiscount', 'SAMSUNG'),
        'Interdiscount_LG_Full': ('CH', 'Interdiscount', 'LG'),
        'Digitec_Samsung_Full': ('CH', 'Digitec', 'SAMSUNG'),
        'Digitec_LG_Full': ('CH', 'Digitec', 'LG'),
        'MediaMarkt_CH_SAMSUNG_Full': ('CH', 'MediaMarkt', 'SAMSUNG'),
        'MediaMarkt_CH_LG_Full': ('CH', 'MediaMarkt', 'LG')
    }

    for s_name, (c_code, r_name, b_name) in sheet_retailer_map.items():
        if s_name not in wb.sheetnames:
            continue
        ws = wb[s_name]

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue

        header = [str(c).lower().strip() if c else '' for c in rows[0]]
        code_col = 4
        for idx, h in enumerate(header):
            if any(k in h for k in ['model code', 'model_code', 'code']):
                code_col = idx
                break

        existing_codes = set()
        for r in rows[1:]:
            if r and len(r) > code_col and r[code_col]:
                existing_codes.add(str(r[code_col]).strip().upper())

        candidates = []
        for k, entry in master_registry.items():
            if not isinstance(entry, dict):
                continue
            if (str(entry.get('country', '')).upper() == c_code and
                str(entry.get('retailer', '')).lower() == r_name.lower() and
                str(entry.get('brand', '')).lower() == b_name.lower()):
                m_code = str(entry.get('model_code', '')).strip().upper()
                if m_code and m_code not in existing_codes and entry.get('url'):
                    candidates.append(entry)

        if not candidates:
            continue

        print(f"  [{s_name}] Probing {len(candidates)} missing candidates with 10 threads...", flush=True)

        sheet_added = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(probe_single_candidate, c) for c in candidates]
            for f in as_completed(futures):
                total_checked += 1
                try:
                    cand, probe = f.result()
                    if not probe:
                        continue
                    if probe.get('status') == 'out_of_stock':
                        total_oos += 1
                        continue
                    if probe.get('status') == 'in_stock' and probe.get('price', 0) > 0:
                        p = probe['price']
                        op = probe.get('original_price', p)
                        size_val = cand.get('size', 55)
                        m_code = cand.get('model_code')
                        ws.append([
                            b_name.capitalize(),
                            cand.get('year', 2025),
                            cand.get('display_type', 'LED'),
                            size_val,
                            m_code,
                            p,
                            op,
                            cand.get('series', 'Unknown'),
                            0,
                            'Replenished Live In-Stock',
                            cand.get('url'),
                            cand.get('title', f"{b_name} {m_code} TV")
                        ])
                        existing_codes.add(m_code)
                        sheet_added += 1
                        total_added += 1
                except Exception:
                    pass

        if sheet_added > 0:
            print(f"    ✔ Successfully replenished {sheet_added} active in-stock models into {s_name}!", flush=True)

    wb.save(target_wb_path)
    wb.close()
    print(f"\n[SUMMARY] Checked {total_checked} candidate URLs: {total_oos} out-of-stock/delisted (excluded), {total_added} in-stock models replenished.", flush=True)

def main():
    print("=" * 70, flush=True)
    print(" 🌐 HIGH-SPEED MULTITHREADED MASTER PDP PROBE & REPLENISHER ", flush=True)
    print("=" * 70, flush=True)

    if not os.path.exists(MASTER_REGISTRY_PATH):
        print(f"[ERROR] Master Registry not found at: {MASTER_REGISTRY_PATH}", flush=True)
        return

    with open(MASTER_REGISTRY_PATH, 'r', encoding='utf-8') as f:
        master_registry = json.load(f)
    print(f"Loaded {len(master_registry)} total registered master URLs.", flush=True)

    today_mmdd = datetime.now().strftime("%m%d")
    today_folder = datetime.now().strftime("%Y %m%d")

    # 1. Replenish European Workbook
    eu_wb = os.path.join(DATA_DIR, f"price tracker_EU_2026 {today_mmdd}_v1.xlsx")
    if not os.path.exists(eu_wb):
        eu_wb = get_latest_workbook("price tracker_EU_2026 *.xlsx")

    if eu_wb and os.path.exists(eu_wb):
        replenish_workbook(eu_wb, master_registry)
        hist_folder = os.path.join(HISTORY_EU_DIR, today_folder)
        os.makedirs(hist_folder, exist_ok=True)
        import shutil
        shutil.copy2(eu_wb, os.path.join(hist_folder, os.path.basename(eu_wb)))
        print(f"[MIRROR] Mirrored replenished EU workbook to: {hist_folder}", flush=True)

    # 2. Replenish Swiss Workbook
    ch_wb = os.path.join(DATA_DIR, f"price tracker_swiss_2026 {today_mmdd}_v1.xlsx")
    if not os.path.exists(ch_wb):
        ch_wb = get_latest_workbook("price tracker_swiss_2026 *.xlsx")

    if ch_wb and os.path.exists(ch_wb):
        replenish_workbook(ch_wb, master_registry)
        ch_hist_folder = os.path.join(ROOT_DIR, "History", today_folder)
        os.makedirs(ch_hist_folder, exist_ok=True)
        import shutil
        shutil.copy2(ch_wb, os.path.join(ch_hist_folder, os.path.basename(ch_wb)))
        print(f"[MIRROR] Mirrored replenished Swiss workbook to: {ch_hist_folder}", flush=True)

    print("\n[COMPLETE] High-speed master replenishment cycle finished cleanly!", flush=True)

if __name__ == '__main__':
    main()
