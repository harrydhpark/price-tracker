import os
import sys
import json
import re
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

import price_history as ph

# Exchange rate multipliers to EUR
RATES_TO_EUR = {
    "EUR": 1.0,
    "CHF": 1.05,
    "GBP": 1.18,
    "CZK": 0.040,
    "HUF": 0.0025,
    "AUD": 0.60,
    "SEK": 0.088
}

def to_eur(price: float, currency: str) -> float:
    rate = RATES_TO_EUR.get(str(currency).upper(), 1.0)
    return float(price) * rate

def run_quality_gates(records: List[Dict[str, Any]], survey_date: str = None) -> List[Dict[str, Any]]:
    """Runs data quality gates (R1-R4) on a dataset of TV price survey records.
    Returns a list of detected anomalies.
    """
    if not records:
        return []

    if not survey_date:
        survey_date = datetime.now().strftime("%Y-%m-%d")

    anomalies = []
    con = ph.get_connection()
    cur = con.cursor()

    # Pre-group for R2 (cross-country median)
    by_model: Dict[str, List[tuple]] = {}
    for r in records:
        mc = r.get("model_code", "").strip()
        p = float(r.get("selling_price") or 0.0)
        curr = str(r.get("currency", "EUR")).upper()
        if mc and mc.upper() not in ["UNKNOWN", "UNKNOWN SAMSUNG", "UNKNOWN LG"] and p > 0:
            by_model.setdefault(mc, []).append((r, to_eur(p, curr)))

    # Evaluate R2 (Cross-Country Outlier: >= 2x median across >= 2 countries)
    for mc, list_recs in by_model.items():
        countries = set(item[0].get("country", "") for item in list_recs)
        if len(countries) >= 2:
            eur_prices = sorted([item[1] for item in list_recs])
            n = len(eur_prices)
            med = (eur_prices[n // 2] if n % 2 != 0 else (eur_prices[n // 2 - 1] + eur_prices[n // 2]) / 2.0)
            if med > 0:
                for r, eur_p in list_recs:
                    if eur_p >= 2.0 * med:
                        curr = r.get("currency", "EUR")
                        raw_p = float(r.get("selling_price", 0.0))
                        max_local = round((med * 2.0) / RATES_TO_EUR.get(curr, 1.0), 1)
                        anomalies.append({
                            "rule": "R2",
                            "severity": "CRITICAL",
                            "country": r.get("country", ""),
                            "retailer": r.get("retailer", ""),
                            "model_code": mc,
                            "observed": raw_p,
                            "expected_range": f"< {max_local} {curr} (Median: {med:.1f} EUR)",
                            "message": f"EUR-converted price ({eur_p:.1f} EUR) is >= 2.0x cross-country median ({med:.1f} EUR)"
                        })

    # Evaluate R1, R3, R4 per record
    for r in records:
        country = str(r.get("country", "")).upper()
        retailer = str(r.get("retailer", ""))
        model_code = str(r.get("model_code", "")).strip()
        price = float(r.get("selling_price") or 0.0)
        currency = str(r.get("currency", "EUR")).upper()
        # Authoritative screen size resolution
        STANDARD_SIZES = {24, 27, 32, 40, 42, 43, 48, 50, 55, 65, 70, 75, 77, 83, 85, 86, 97, 98, 100}
        raw_size = int(r.get("display_size_inch") or 0)
        size = 0
        
        # 1. Authoritative model code prefix check: e.g. TQ32..., QE55..., OLED65..., UE24..., 55QNED...
        mc_up = model_code.upper()
        m_mc = re.search(r'^(?:OLED|QE|UE|TQ|QA|GQ|TU|NU|UA|UT|MRE|TMR)(\d{2})[A-Z0-9]', mc_up)
        if not m_mc:
            m_mc = re.search(r'^(\d{2})[A-Z]{2,}', mc_up)
        if m_mc:
            s_cand = int(m_mc.group(1))
            if s_cand in STANDARD_SIZES:
                size = s_cand
                
        # 2. Fallback to recorded size if valid
        if size == 0 and raw_size in STANDARD_SIZES:
            size = raw_size
        elif size == 0:
            size = raw_size if 20 <= raw_size <= 100 else 55
        curr_promo = str(r.get("promo_text") or "")
        eur_price = to_eur(price, currency)

        # Rule 4: Category and screen-size price floors (CRITICAL)
        panel_up = (r.get("panel_type") or "").upper()
        mc_up = model_code.upper()
        is_mrgb = any(x in panel_up or x in mc_up for x in ["MRGB", "MICRO RGB", "R85", "R95"])
        is_qned = not is_mrgb and any(x in panel_up or x in mc_up for x in ["QNED", "QLED", "NEO QLED", "QN8", "QN9", "QN7", "LS03"])
        is_oled = not is_mrgb and not is_qned and ("OLED" in panel_up or "OLED" in mc_up or any(s in mc_up for s in ["S90", "S95", "S99", "S85"]))

        floor_violated = False
        floor_eur = 50.0
        cat_name = "TV"

        if is_oled:
            cat_name = "OLED"
            if size >= 83: floor_eur = 1800.0
            elif size >= 77: floor_eur = 1300.0
            elif size >= 70: floor_eur = 1100.0
            elif size >= 65: floor_eur = 850.0
            elif size >= 55: floor_eur = 650.0
            elif size in [42, 48]: floor_eur = 500.0
            else: floor_eur = 400.0
        elif is_mrgb:
            cat_name = "Micro RGB"
            if size >= 75: floor_eur = 1200.0
            elif size >= 50: floor_eur = 600.0
            else: floor_eur = 500.0
        elif is_qned:
            cat_name = "QNED/QLED"
            if size >= 75: floor_eur = 600.0
            elif size >= 65: floor_eur = 450.0
            elif size >= 50: floor_eur = 280.0
            elif size >= 43: floor_eur = 200.0
            else: floor_eur = 150.0
        else: # UHD 4K / Entry LED
            cat_name = "UHD 4K"
            if size >= 70: floor_eur = 450.0
            elif size >= 55: floor_eur = 180.0
            elif size >= 43: floor_eur = 120.0
            else: floor_eur = 80.0

        # Absolute minimum floor
        if eur_price < 50.0 and price > 0:
            floor_violated = True
            floor_eur = 50.0
            cat_name = "Absolute Floor"
        elif eur_price < floor_eur:
            floor_violated = True

        if floor_violated:
            min_local = round(floor_eur / RATES_TO_EUR.get(currency, 1.0), 1)
            anomalies.append({
                "rule": "R4",
                "severity": "CRITICAL",
                "country": country,
                "retailer": retailer,
                "model_code": model_code,
                "observed": price,
                "expected_range": f">= {min_local} {currency} ({cat_name} floor: EUR {floor_eur:.0f})",
                "message": f"{size}\" {cat_name} price ({price} {currency} = {eur_price:.1f} EUR) violates minimum floor of EUR {floor_eur:.0f}"
            })

        # Rule 1: ±30% Spike/Drop Guard (WARN)
        if price > 0:
            cur.execute("""
                SELECT selling_price, promo_text, date
                FROM daily_prices
                WHERE country = ? AND retailer = ? AND model_code = ? AND date < ?
                ORDER BY date DESC
                LIMIT 1
            """, (country, retailer, model_code, survey_date))
            prev = cur.fetchone()
            if prev and prev["selling_price"] and prev["selling_price"] > 0:
                prev_price = float(prev["selling_price"])
                prev_promo = str(prev["promo_text"] or "")
                diff_pct = (price - prev_price) / prev_price
                if abs(diff_pct) >= 0.30:
                    # Promo text exemption: if promo changed along with price, exempt
                    if curr_promo != prev_promo or curr_promo.strip().upper() not in ["NONE", ""]:
                        pass
                    elif r.get("original_price") and float(r.get("original_price")) > price:
                        pass
                    else:
                        anomalies.append({
                            "rule": "R1",
                            "severity": "WARN",
                            "country": country,
                            "retailer": retailer,
                            "model_code": model_code,
                            "observed": price,
                            "expected_range": f"{prev_price * 0.7:.1f} ~ {prev_price * 1.3:.1f} {currency}",
                            "message": f"Price shifted by {diff_pct * 100:+.1f}% vs previous survey ({prev['date']} price: {prev_price} {currency}) without promo change"
                        })

        # Rule 3: Consecutive 0/null price alert (WARN)
        if price <= 0:
            cur.execute("""
                SELECT selling_price, date
                FROM daily_prices
                WHERE country = ? AND retailer = ? AND model_code = ? AND date < ?
                ORDER BY date DESC
                LIMIT 1
            """, (country, retailer, model_code, survey_date))
            prev = cur.fetchone()
            if prev and (prev["selling_price"] is None or float(prev["selling_price"]) <= 0):
                anomalies.append({
                    "rule": "R3",
                    "severity": "WARN",
                    "country": country,
                    "retailer": retailer,
                    "model_code": model_code,
                    "observed": price,
                    "expected_range": "> 0",
                    "message": f"Model has 0/null price in 2 consecutive surveys ({prev['date']} and {survey_date})"
                })

    con.close()
    return anomalies

def evaluate_and_enforce_gate(records: List[Dict[str, Any]], survey_date: str = None) -> bool:
    """Evaluates quality gates, generates anomaly report JSON, prints summary table,
    and returns True if gate passes, or exits/returns False if gate fails.
    """
    if not survey_date:
        survey_date = datetime.now().strftime("%Y-%m-%d")
    date_clean = survey_date.replace("-", "")

    anomalies = run_quality_gates(records, survey_date)
    
    # Save anomaly report JSON
    report_file = os.path.join(DATA_DIR, f"anomaly_report_{date_clean}.json")
    report_data = {
        "survey_date": survey_date,
        "total_records_audited": len(records),
        "total_anomalies": len(anomalies),
        "critical_count": sum(1 for a in anomalies if a["severity"] == "CRITICAL"),
        "warn_count": sum(1 for a in anomalies if a["severity"] == "WARN"),
        "anomalies": anomalies
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    # Print summary table
    print("\n" + "=" * 70)
    print(f" 🛡️ DATA QUALITY GATES & ANOMALY AUDIT REPORT ({survey_date})")
    print("=" * 70)
    print(f"Total Records Audited: {len(records):,}")
    print(f"Total Anomalies Flagged: {len(anomalies)} (CRITICAL: {report_data['critical_count']}, WARN: {report_data['warn_count']})")
    print(f"Saved Detailed Report : {report_file}\n")

    if anomalies:
        print(f"{'RULE':4s} | {'SEVERITY':8s} | {'COUNTRY':4s} | {'RETAILER':12s} | {'MODEL CODE':16s} | {'OBSERVED':10s} | {'MESSAGE'}")
        print("-" * 70)
        for a in anomalies[:25]: # Print first 25
            obs_str = f"{a['observed']}"
            print(f"{a['rule']:4s} | {a['severity']:8s} | {a['country']:4s} | {a['retailer'][:12]:12s} | {a['model_code'][:16]:16s} | {obs_str:10s} | {a['message']}")
        if len(anomalies) > 25:
            print(f"... and {len(anomalies) - 25} more anomalies (see report JSON).")
        print("-" * 70)

    # Enforcement check
    critical_count = report_data["critical_count"]
    total_records = len(records)
    ratio = len(anomalies) / total_records if total_records > 0 else 0.0
    block_threshold = float(os.environ.get("ANOMALY_BLOCK_THRESHOLD", "0.05"))

    if critical_count > 0:
        print("\n" + "!" * 70)
        print(f"[QUALITY GATE FAILED] Found {critical_count} CRITICAL anomalies!")
        print("Violation of strict price floor (R4) or cross-country outlier (R2).")
        print("Aborting pipeline deployment to protect production dashboard integrity.")
        print("!" * 70)
        return False

    if ratio > block_threshold:
        print("\n" + "!" * 70)
        print(f"[QUALITY GATE FAILED] Anomaly ratio {ratio*100:.2f}% exceeds threshold {block_threshold*100:.2f}%!")
        print("Aborting pipeline deployment due to abnormal data volatility.")
        print("!" * 70)
        return False

    print(f"\n✅ [QUALITY GATE PASSED] 0 CRITICAL violations. Anomaly ratio {ratio*100:.2f}% is within {block_threshold*100:.2f}% threshold.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Price Anomaly Detection & Data Quality Gates")
    parser.add_argument("--excel", type=str, default=None, help="Path to survey Excel workbook to audit")
    parser.add_argument("--date", type=str, default=None, help="Survey date (YYYY-MM-DD)")
    args = parser.parse_args()

    survey_date = args.date or datetime.now().strftime("%Y-%m-%d")
    records = []

    if args.excel and os.path.exists(args.excel):
        records = ph.parse_survey_workbook(args.excel)
    else:
        # Load from price_history.db for the given date
        con = ph.get_connection()
        cur = con.cursor()
        rows = cur.execute("SELECT * FROM daily_prices WHERE date = ?", (survey_date,)).fetchall()
        con.close()
        records = [dict(r) for r in rows]

    if not records:
        # Look for today's files in data/
        today_mmdd = datetime.now().strftime("%m%d")
        candidates = [
            os.path.join(DATA_DIR, f"price tracker_swiss_2026 {today_mmdd}_v1.xlsx"),
            os.path.join(DATA_DIR, f"price tracker_swiss_2026 {today_mmdd}.xlsx"),
            os.path.join(DATA_DIR, f"price tracker_EU_2026 {today_mmdd}_v1.xlsx")
        ]
        for c in candidates:
            if os.path.exists(c):
                records.extend(ph.parse_survey_workbook(c))

    if not records:
        print(f"[INFO] No records found for date {survey_date} to audit.")
        sys.exit(0)

    passed = evaluate_and_enforce_gate(records, survey_date)
    if not passed:
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
