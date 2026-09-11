# -*- coding: utf-8 -*-
"""
Hungary MediaMarkt (mediamarkt.hu) TV Price Tracker
Scrapes LG & Samsung TV models, prices (HUF & EUR), classifies series/year/inch,
and exports structured JSON and Excel sample reports.
"""

import sys
import os
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from scrapling.fetchers import StealthySession
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

# Default HUF to EUR exchange rate
HUF_TO_EUR_RATE = 398.0  # 1 EUR = 398 HUF

def extract_size_from_title(title_upper):
    # Match patterns like 55", 55INCH, 55 인치, 55CM (diagonal)
    # Common inch markers
    m = re.search(r'(\d{2,3})\s*(?:\"|\'\'|”|COL|INCH|\s*CM|\b)', title_upper)
    # First look for 2-3 digits followed by inch/col/cm
    m_inch = re.search(r'(\d{2,3})\s*(?:\"|\'\'|”|COL|INCH)', title_upper)
    if m_inch:
        val = int(m_inch.group(1))
        if 24 <= val <= 115:
            return val
            
    # Look for model prefix e.g. OLED55, QE65, 50QNED
    m_mod = re.search(r'(?:OLED|QE|UE|GQ|QNED|NANO|NU|UA)?(\d{2,3})(?:C\d|G\d|B\d|QN|S\d|U\d|Q\d|QNED|NANO|UA|NU)', title_upper)
    if m_mod:
        val = int(m_mod.group(1))
        if 24 <= val <= 115:
            return val

    # Fallback to general numbers 24-115
    for token in title_upper.split():
        clean = re.sub(r'[^\d]', '', token)
        if clean.isdigit():
            v = int(clean)
            if v in [24, 27, 32, 40, 42, 43, 48, 50, 55, 60, 65, 70, 75, 77, 83, 85, 86, 98, 100, 115]:
                return v
    return 0

def extract_model_code_and_series(brand, title_upper):
    brand_lower = brand.lower()
    
    if brand_lower == "lg":
        # LG Model patterns
        # 1. OLED: OLED55C51LA, OLED65G64, OLED77B5, etc.
        m_oled = re.search(r'(OLED\d{2,3}[A-Z0-9]+)', title_upper)
        if m_oled:
            mc = m_oled.group(1)
            # Series: C5, G6, B5, M4, C6, G5 etc.
            sm = re.search(r'OLED\d{2,3}([A-Z]\d)', mc)
            series = f"OLED {sm.group(1)}" if sm else "OLED"
            return mc, series, "OLED"
            
        # 2. QNED / MRGB: 43QNED7EB3C, 65QNED80A6A, 55QNED86A3A, etc.
        m_qned = re.search(r'(\d{2,3}QNED[A-Z0-9]+)', title_upper)
        if m_qned:
            mc = m_qned.group(1)
            sm = re.search(r'QNED(\d{2,3}[A-Z0-9]*)', mc)
            series = f"QNED {sm.group(1)[:4]}" if sm else "QNED"
            category = "MRGB" if "MRGB" in mc else "QNED"
            return mc, series, category
            
        # 3. NanoCell: 50NANO82A6B, etc.
        m_nano = re.search(r'(\d{2,3}NANO[A-Z0-9]+)', title_upper)
        if m_nano:
            mc = m_nano.group(1)
            return mc, "NanoCell", "NanoCell"
            
        # 4. UHD / LED: 50NU8E0B3LA, 43UA75006LA, 55UA73003LA, 32LQ63006LA
        m_uhd = re.search(r'(\d{2,3}(?:UA|NU|UQ|UR|UT|LQ|LM)[A-Z0-9]+)', title_upper)
        if m_uhd:
            mc = m_uhd.group(1)
            if "LQ" in mc or "LM" in mc:
                return mc, "FHD/HD", "FHD"
            return mc, "UHD", "UHD"
            
        return "Unknown", "LG TV", "UHD"
        
    elif brand_lower == "samsung":
        # Samsung Model patterns
        # 1. Full model code e.g. QE65QN70FAUXXH, QE55S90FAEXXH, UE43U8072FUXXH, QE98Q7FAAUXXH
        m_full = re.search(r'([QUG][EAN]\d{2,3}[A-Z0-9]+)', title_upper)
        if m_full:
            mc = m_full.group(1)
            
            # OLED: S95, S90, S85
            if "S95" in mc or "S90" in mc or "S85" in mc:
                sm = re.search(r'(S\d{2}[A-Z]?)', mc)
                series = sm.group(1) if sm else "OLED"
                return mc, f"OLED {series}", "OLED"
                
            # Neo QLED / 8K: QN900, QN800, QN95, QN90, QN85, QN80, QN70
            if "QN" in mc:
                sm = re.search(r'(QN\d{2,3}[A-Z]?)', mc)
                series = sm.group(1) if sm else "Neo QLED"
                return mc, f"Neo QLED {series}", "Neo QLED"
                
            # QLED: Q8, Q7, Q6, Q80, Q70, Q60
            if re.search(r'Q\d[A-Z0-9]', mc):
                sm = re.search(r'(Q\d{1,2}[A-Z]?)', mc)
                series = sm.group(1) if sm else "QLED"
                return mc, f"QLED {series}", "QLED"
                
            # Frame: LS03
            if "LS03" in mc:
                return mc, "The Frame", "Lifestyle"
                
            # Crystal UHD: U8000, U8072, U8090, DU8000, etc.
            if "U8" in mc or "U7" in mc or "DU" in mc or "CU" in mc:
                sm = re.search(r'([A-Z]*U\d{4}[A-Z]*)', mc)
                series = sm.group(1) if sm else "Crystal UHD"
                return mc, f"UHD {series}", "UHD"
                
            return mc, "Samsung TV", "UHD"
            
        return "Unknown", "Samsung TV", "UHD"

    return "Unknown", "Other", "Other"

def classify_model_year(brand, model_code, title_upper):
    # Year classification
    if "2026" in title_upper:
        return 2026
    if "2025" in title_upper:
        return 2025
    if "2024" in title_upper:
        return 2024
        
    brand_lower = brand.lower()
    if brand_lower == "lg":
        if any(x in model_code for x in ["C6", "G6", "B6", "M6", "QNED86B", "QNED80B", "QNED87B", "QNED7EB", "QNED72B", "NU8E", "MRGB87B", "UA77"]):
            return 2026
        if any(x in model_code for x in ["C5", "G5", "B5", "M5", "QNED86A", "QNED80A", "QNED87A", "QNED7EA", "QNED72A", "NANO82A", "NANO81A", "UA75", "UA73", "MRGB87A"]):
            return 2025
        if any(x in model_code for x in ["C4", "G4", "B4", "M4", "QNED85", "QNED80", "QNED86", "UA70", "UR", "UQ"]):
            return 2024
    elif brand_lower == "samsung":
        # Samsung 2026: H suffix e.g. QN90H, S90H, U8000H, Q70H
        # Samsung 2025: F suffix e.g. QN90F, S90F, U8072F, Q7FA
        # Samsung 2024: D suffix e.g. QN90D, S90D, DU8000
        if re.search(r'[A-Z0-9]+[H][A-Z0-9]*', model_code):
            return 2026
        if re.search(r'[A-Z0-9]+[F][A-Z0-9]*', model_code):
            return 2025
        if re.search(r'[A-Z0-9]+[D][A-Z0-9]*', model_code):
            return 2024

    return 2025  # Default reasonable assumption for current market

def parse_mediamarkt_hu_html(html):
    idx = html.find('window.__PRELOADED_STATE__')
    if idx == -1:
        return []
    end_idx = html.find('</script>', idx)
    raw = html[idx:end_idx].split('window.__PRELOADED_STATE__ =', 1)[1].strip()
    if raw.endswith(';'):
        raw = raw[:-1]
    raw = re.sub(r':\s*undefined\b', ': null', raw)
    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"JSON parse error: {e}")
        return []
        
    apollo = data.get("apolloState", {})
    
    # Map price features
    prices = {}
    for k, v in apollo.items():
        if k.startswith("CofrPriceFeature:"):
            media_id = v.get("id", "")
            raw_id = media_id.split(":")[-1] if ":" in media_id else media_id
            p_obj = v.get("price", {})
            amount = p_obj.get("amount") if isinstance(p_obj, dict) else None
            promo_p = v.get("promoPrice", {})
            promo_amount = promo_p.get("amount") if isinstance(promo_p, dict) else None
            is_mp = v.get("isProductOfTypeMarketplace", False)
            seller = v.get("marketplaceSeller")
            
            prices[raw_id] = {
                "amount": amount,
                "promo_amount": promo_amount,
                "currency": v.get("currency", "HUF"),
                "is_marketplace": is_mp,
                "seller": seller
            }
            
    products = []
    for k, v in apollo.items():
        if k.startswith("GraphqlProduct:"):
            prod_id = str(v.get("id") or v.get("productId") or "")
            title = v.get("title") or v.get("name") or v.get("description") or ""
            brand = v.get("manufacturer") or v.get("brand") or ""
            pdp_url = v.get("pdpUrl") or v.get("url") or ""
            
            price_info = prices.get(prod_id, {})
            
            products.append({
                "product_id": prod_id,
                "title": title,
                "brand": brand,
                "pdp_url": f"https://www.mediamarkt.hu{pdp_url}" if pdp_url.startswith("/") else pdp_url,
                "price_huf": price_info.get("amount"),
                "promo_price_huf": price_info.get("promo_amount"),
                "is_marketplace": price_info.get("is_marketplace", False),
                "seller": price_info.get("seller") or "MediaMarkt"
            })
            
    return products

def scrape_brand_tv(session, brand, max_pages=8):
    print(f"\n=======================================================")
    print(f"🔍 [SCRAPING] Starting {brand} TV Collection (Max {max_pages} pages)")
    print(f"=======================================================")
    
    brand_query = "LG+TV" if brand.upper() == "LG" else "Samsung+TV"
    collected = []
    seen_ids = set()
    
    for page in range(1, max_pages + 1):
        url = f"https://www.mediamarkt.hu/hu/search.html?query={brand_query}&page={page}"
        print(f"  ➔ [Page {page}] Fetching: {url}")
        
        try:
            res = session.fetch(url, solve_cloudflare=True, wait=3000, timeout=40000)
            if res.status != 200:
                print(f"  ⚠️ Non-200 status {res.status} on page {page}")
                break
                
            items = parse_mediamarkt_hu_html(str(res.html_content))
            if not items:
                print(f"  ➔ No products extracted on page {page}, stopping pagination.")
                break
                
            new_count = 0
            for it in items:
                pid = it["product_id"]
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    collected.append(it)
                    new_count += 1
                    
            print(f"  ➔ Page {page}: Found {len(items)} items (+{new_count} new unique). Total: {len(collected)}")
            
        except Exception as e:
            print(f"  ❌ Error fetching page {page}: {e}")
            break
            
    return collected

def process_and_clean_data(raw_items, brand):
    cleaned = []
    
    for item in raw_items:
        title = item["title"]
        title_upper = title.upper()
        
        # Filter out accessories, monitors, soundbars
        if any(x in title_upper for x in ["MONITOR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "SOUNDBAR", "HIFI", "FALI TARTÓ", "TÁVIRÁNYÍTÓ", "KIEGÉSZÍTŐ", "BRACKET"]):
            continue
            
        # Filter out marketplace partner sellers if requested (or keep but flag)
        # Here we include all MediaMarkt direct or marketplace items
        price_huf = item["price_huf"] or item["promo_price_huf"]
        if not price_huf or price_huf <= 0:
            continue
            
        inch = extract_size_from_title(title_upper)
        model_code, series, category = extract_model_code_and_series(brand, title_upper)
        year = classify_model_year(brand, model_code, title_upper)
        
        price_eur = round(price_huf / HUF_TO_EUR_RATE, 2)
        
        cleaned.append({
            "retailer": "MediaMarkt",
            "country": "Hungary",
            "country_code": "HU",
            "brand": brand,
            "category": category,
            "series": series,
            "model_code": model_code,
            "inch": inch,
            "year": year,
            "price_huf": int(price_huf),
            "price_eur": price_eur,
            "is_marketplace": item["is_marketplace"],
            "seller": item["seller"],
            "title": title,
            "pdp_url": item["pdp_url"],
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    return cleaned

def create_excel_report(all_products, output_excel_path):
    wb = openpyxl.Workbook()
    
    # Sheet 1: Raw Data
    ws_raw = wb.active
    ws_raw.title = "Hungary_MediaMarkt_Prices"
    
    headers = [
        "No", "Country", "Retailer", "Brand", "Category", "Series", 
        "Model Code", "Inch", "Year", "Price (HUF)", "Price (EUR)", 
        "Seller Type", "Seller Name", "Product Title", "PDP URL", "Survey Date"
    ]
    
    header_fill = PatternFill(start_color="051C2C", end_color="051C2C", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=10)
    bold_font = Font(name="Segoe UI", size=10, bold=True)
    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    
    ws_raw.append(headers)
    for col_idx, h in enumerate(headers, 1):
        cell = ws_raw.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    for idx, p in enumerate(all_products, 1):
        row = [
            idx,
            p["country"],
            p["retailer"],
            p["brand"],
            p["category"],
            p["series"],
            p["model_code"],
            p["inch"],
            p["year"],
            p["price_huf"],
            p["price_eur"],
            "Marketplace" if p["is_marketplace"] else "Direct (MediaMarkt)",
            p["seller"],
            p["title"],
            p["pdp_url"],
            p["collected_at"]
        ]
        ws_raw.append(row)
        curr_row = idx + 1
        
        for c_idx in range(1, len(row) + 1):
            cell = ws_raw.cell(row=curr_row, column=c_idx)
            cell.font = data_font
            cell.border = border_thin
            if c_idx in [1, 2, 3, 4, 5, 8, 9, 12]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c_idx == 10:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = '#,##0 "Ft"'
            elif c_idx == 11:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = '€#,##0.00'
                
    # Sheet 2: LG vs Samsung Direct Comparison (Matching by Inch & Segment)
    ws_comp = wb.create_sheet(title="LG_vs_Samsung_ATA")
    comp_headers = [
        "Inch", "Segment / Tech", "LG Model", "LG Price (HUF)", "LG Price (EUR)",
        "Samsung Model", "Samsung Price (HUF)", "Samsung Price (EUR)",
        "Price Gap (EUR)", "ATA Ratio (LG / SEC * 100)"
    ]
    ws_comp.append(comp_headers)
    for col_idx, h in enumerate(comp_headers, 1):
        cell = ws_comp.cell(row=1, column=col_idx)
        cell.fill = PatternFill(start_color="00538C", end_color="00538C", fill_type="solid")
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    # Auto adjust column widths
    for sheet in [ws_raw, ws_comp]:
        sheet.row_dimensions[1].height = 26
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)
            
    wb.save(output_excel_path)
    print(f"\n📊 [EXCEL CREATED] Successfully created Excel report: {output_excel_path}")

def generate_ata_summary_report(cleaned_lg, cleaned_sec):
    print("\n" + "="*80)
    print("🇭🇺 HUNGARY MEDIAMARKT TV PRICE TRACKER SAMPLE REPORT")
    print(f"Survey Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Base Rate: 1 EUR = {HUF_TO_EUR_RATE} HUF")
    print("="*80)
    
    print(f"\n[1] Overall Product Counts:")
    print(f"  • LG Total TV Models Collected: {len(cleaned_lg)}")
    print(f"  • Samsung Total TV Models Collected: {len(cleaned_sec)}")
    print(f"  • Grand Total: {len(cleaned_lg) + len(cleaned_sec)} models")
    
    # Breakdown by Category
    df_lg = pd.DataFrame(cleaned_lg)
    df_sec = pd.DataFrame(cleaned_sec)
    
    print(f"\n[2] Lineup Breakdown by Category:")
    if not df_lg.empty:
        print("  LG Lineup:")
        print(df_lg["category"].value_counts().to_string(header=False))
    if not df_sec.empty:
        print("  Samsung Lineup:")
        print(df_sec["category"].value_counts().to_string(header=False))
        
    print(f"\n[3] Key Representative Models Price Comparison (Sample Highlights):")
    print(f"{'Brand':<8} | {'Inch':<4} | {'Series/Category':<15} | {'Model Code':<18} | {'Price (HUF)':<14} | {'Price (EUR)':<12}")
    print("-" * 80)
    
    sample_picks = []
    # Pick sample models from LG & Samsung
    for df, b_name in [(df_lg, "LG"), (df_sec, "Samsung")]:
        if not df.empty:
            for cat in ["OLED", "QNED", "Neo QLED", "QLED", "UHD"]:
                sub = df[df["category"] == cat]
                if not sub.empty:
                    for _, row in sub.head(2).iterrows():
                        sample_picks.append(row)
                        
    for r in sample_picks[:12]:
        p_huf_str = f"{r['price_huf']:,} Ft"
        p_eur_str = f"€{r['price_eur']:,.1f}"
        print(f"{r['brand']:<8} | {r['inch']:<4} | {r['category']:<15} | {r['model_code']:<18} | {p_huf_str:<14} | {p_eur_str:<12}")

    print("="*80)

def main():
    with StealthySession(headless=True) as session:
        raw_lg = scrape_brand_tv(session, "LG", max_pages=6)
        raw_sec = scrape_brand_tv(session, "Samsung", max_pages=6)
        
    cleaned_lg = process_and_clean_data(raw_lg, "LG")
    cleaned_sec = process_and_clean_data(raw_sec, "Samsung")
    all_cleaned = cleaned_lg + cleaned_sec
    
    # Save structured JSON
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)
    
    json_path = os.path.join(data_dir, "mediamarkt_hu_sample.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_cleaned, f, ensure_ascii=False, indent=2)
    print(f"\n💾 [JSON SAVED] Saved structured JSON to: {json_path}")
    
    # Save Excel report
    excel_path = os.path.join(data_dir, "Hungary_MediaMarkt_TV_Price_Sample.xlsx")
    create_excel_report(all_cleaned, excel_path)
    
    # Generate ATA Summary Report
    generate_ata_summary_report(cleaned_lg, cleaned_sec)

if __name__ == "__main__":
    main()
