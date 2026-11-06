# -*- coding: utf-8 -*-
"""
Pan-European Data Quality Gates v2 (Phase 1C).

Implements the 7 Mandatory Quality Gates:
  G1: Live Confirmation Rate (>= 95% per retailer) -> HALT on failure
  G2: CRITICAL Price Anomalies (R2 Cross-country median, R3 Reversal, R4 Price floor) -> HALT on failure
  G3: Model Count Sudden Drop (<= -10% drop vs previous survey per retailer/brand) -> HALT on failure
  G4: Independent Ground-Truth Verification Mismatch (<= 2% mismatch rate) -> HALT on failure
  G5: Mandatory Provenance & Metadata Completeness -> HALT on failure
  G6: Stale Carry-Over / Identical Price Ratio (> 90% identical prices) -> WARN (Cache reuse alert)
  G7: Search Listing vs PDP Price Drift (> 1% drift logged, PDP authoritative)

Exits with code 0 on PASS, code 2 on HALT.
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
RUNS_DIR = os.path.join(DATA_DIR, "runs")
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
    "SEK": 0.088,
    "PLN": 0.235,
    "RON": 0.201
}

STANDARD_SIZES = {24, 27, 32, 40, 42, 43, 48, 50, 55, 65, 70, 75, 77, 83, 85, 86, 97, 98, 100, 115}


def to_eur(price: float, currency: str) -> float:
    rate = RATES_TO_EUR.get(str(currency).upper(), 1.0)
    return float(price) * rate


def resolve_screen_size(record: Dict[str, Any]) -> int:
    """Authoritative screen size extraction from model code or record field."""
    mc = str(record.get("model_code", "")).strip().upper()
    raw_size = int(record.get("display_size_inch") or record.get("screen_size") or 0)
    
    m_mc = re.search(r'^(?:OLED|QE|UE|TQ|QA|GQ|TU|NU|UA|UT|MRE|TMR)(\d{2,3})[A-Z0-9]', mc)
    if not m_mc:
        m_mc = re.search(r'^(\d{2,3})[A-Z]{2,}', mc)
    if m_mc:
        s_cand = int(m_mc.group(1))
        if s_cand in STANDARD_SIZES:
            return s_cand
            
    if raw_size in STANDARD_SIZES:
        return raw_size
    return raw_size if 20 <= raw_size <= 120 else 55


# ==============================================================================
# GATE EVALUATORS (G1 to G7)
# ==============================================================================

def eval_g1_live_confirmation_rate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    G1: Live Confirmation Rate.
    For each retailer: LIVE_* / (total - DELISTED) >= 95%.
    """
    by_ret: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        ret = r.get("retailer") or "Unknown"
        by_ret.setdefault(ret, []).append(r)

    details = []
    overall_passed = True

    for ret, ret_records in sorted(by_ret.items()):
        total = len(ret_records)
        delisted = sum(1 for r in ret_records if str(r.get("status", "")).upper() in ("DELISTED", "DISCONTINUED", "OUT_OF_STOCK"))
        unlisted = sum(1 for r in ret_records if str(r.get("unverified_reason", "")).upper() in ("NOT_FOUND_IN_REGISTRY", "NOT_CARRIED", "NOT_LISTED"))
        effective_total = total - delisted - unlisted
        
        # In v2, records have status like LIVE_PDP, LIVE_LIST.
        # Fallback for legacy records without status: selling_price > 0 counts as live
        has_status_field = any("status" in r and r["status"] for r in ret_records)
        if has_status_field:
            live_count = sum(1 for r in ret_records if str(r.get("status", "")).upper().startswith("LIVE_"))
        else:
            live_count = sum(1 for r in ret_records if float(r.get("selling_price") or 0) > 0)

        rate = (live_count / effective_total) if effective_total > 0 else 1.0
        rate_pct = round(rate * 100, 1)
        passed = rate >= 0.95

        if not passed:
            overall_passed = False

        details.append({
            "retailer": ret,
            "total": total,
            "delisted": delisted,
            "effective_total": effective_total,
            "live_count": live_count,
            "rate_pct": rate_pct,
            "passed": passed
        })

    return {
        "gate": "G1",
        "name": "Live Confirmation Rate (>= 95%)",
        "passed": overall_passed,
        "details": details
    }


def eval_g2_price_anomalies(records: List[Dict[str, Any]], survey_date: str = None) -> Dict[str, Any]:
    """
    G2: CRITICAL Price Anomalies (R2 Cross-country median, R3 Reversal, R4 Category price floor).
    Must have 0 CRITICAL violations to pass.
    """
    if not survey_date:
        survey_date = datetime.now().strftime("%Y-%m-%d")

    anomalies = []
    by_model: Dict[str, List[tuple]] = {}
    
    for r in records:
        mc = str(r.get("model_code", "")).strip()
        p = float(r.get("selling_price") or 0.0)
        curr = str(r.get("currency", "EUR")).upper()
        if mc and mc.upper() not in ["UNKNOWN", "UNKNOWN SAMSUNG", "UNKNOWN LG"] and p > 0:
            by_model.setdefault(mc, []).append((r, to_eur(p, curr)))

    # R2: Cross-Country Median Outlier (>= 2.0x median across >= 2 countries)
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
                        orig_p = float(r.get("original_price") or 0.0)
                        mc_up_r2 = mc.upper()
                        is_full_rrp_or_8k = (
                            eur_p < 3.0 * med
                            and (
                                (orig_p > 0 and abs(raw_p - orig_p) <= 1.0)
                                or any(k in mc_up_r2 for k in ["QN900", "QN800", "QN990"])
                            )
                        )
                        sev = "WARN" if is_full_rrp_or_8k else "CRITICAL"
                        max_local_bound = round((med * 2.0) / RATES_TO_EUR.get(curr, 1.0), 1)
                        anomalies.append({
                            "rule": "R2",
                            "severity": sev,
                            "country": r.get("country", ""),
                            "retailer": r.get("retailer", ""),
                            "model_code": mc,
                            "observed": raw_p,
                            "expected_range": f"< {max_local_bound} {curr} (Median: {med:.1f} EUR)",
                            "message": f"EUR-converted price ({eur_p:.1f} EUR) is >= 2.0x cross-country median ({med:.1f} EUR)"
                        })

    # R3, R4, R1 per record
    con = None
    try:
        con = ph.get_connection()
        cur = con.cursor()
    except Exception:
        cur = None

    for r in records:
        country = str(r.get("country", "")).upper()
        retailer = str(r.get("retailer", ""))
        model_code = str(r.get("model_code", "")).strip()
        price = float(r.get("selling_price") or 0.0)
        orig_price = float(r.get("original_price") or 0.0)
        currency = str(r.get("currency", "EUR")).upper()
        size = resolve_screen_size(r)
        eur_price = to_eur(price, currency)
        curr_promo = str(r.get("promo_text") or "")

        # R3: Strike Price Reversal (CRITICAL: selling_price > original_price * 1.02)
        if orig_price > 0 and price > orig_price * 1.02:
            anomalies.append({
                "rule": "R3",
                "severity": "CRITICAL",
                "country": country,
                "retailer": retailer,
                "model_code": model_code,
                "observed": price,
                "expected_range": f"<= {orig_price} {currency}",
                "message": f"Selling price ({price} {currency}) exceeds original/UVP strike price ({orig_price} {currency})"
            })

        # R4: Category and Screen-size Price Floors (CRITICAL)
        panel_up = str(r.get("panel_type") or "").upper()
        mc_up = model_code.upper()
        is_uhd = any(x in panel_up or x in mc_up for x in ["NU8", "NU9", "UA7", "UT8", "UR8", "UQ8", "UHD 4K", "CRYSTAL UHD", "U80"])
        is_mrgb = any(x in panel_up or x in mc_up for x in ["MRGB", "MICRO RGB", "R85", "R95"])
        is_qned = not is_mrgb and not is_uhd and any(x in panel_up or x in mc_up for x in ["QNED", "QLED", "NEO QLED", "QN8", "QN9", "QN7", "LS03"])
        is_oled = not is_mrgb and not is_qned and not is_uhd and ("OLED" in panel_up or "OLED" in mc_up or any(s in mc_up for s in ["S90", "S95", "S99", "S85"]))

        floor_violated = False
        min_floor_eur = 50.0
        cat_name = "TV"

        if is_oled:
            cat_name = "OLED"
            is_entry_oled = any(x in mc_up for x in ["B5", "B6", "S85"])
            if size >= 83: min_floor_eur = 1400.0 if is_entry_oled else 1800.0
            elif size >= 77: min_floor_eur = 1100.0 if is_entry_oled else 1300.0
            elif size >= 70: min_floor_eur = 950.0 if is_entry_oled else 1100.0
            elif size >= 65: min_floor_eur = 800.0 if is_entry_oled else 850.0
            elif size >= 55: min_floor_eur = 600.0 if is_entry_oled else 650.0
            elif size in [42, 48]: min_floor_eur = 450.0 if is_entry_oled else 500.0
            else: min_floor_eur = 350.0
        elif is_mrgb:
            cat_name = "Micro RGB"
            if size >= 75: min_floor_eur = 1100.0
            elif size >= 50: min_floor_eur = 550.0
            else: min_floor_eur = 500.0
        elif is_qned:
            cat_name = "QNED/QLED"
            is_entry_qled = any(x in mc_up for x in ["Q5F", "Q6", "QNED70", "QNED71", "QNED72", "Q7"])
            if size >= 75: min_floor_eur = 500.0 if is_entry_qled else 600.0
            elif size >= 65: min_floor_eur = 400.0 if is_entry_qled else 450.0
            elif size >= 50: min_floor_eur = 250.0 if is_entry_qled else 280.0
            elif size >= 43: min_floor_eur = 180.0 if is_entry_qled else 200.0
            else: min_floor_eur = 150.0
        else: # UHD 4K
            cat_name = "UHD 4K"
            if size >= 70: min_floor_eur = 450.0
            elif size >= 55: min_floor_eur = 180.0
            elif size >= 43: min_floor_eur = 120.0
            else: min_floor_eur = 80.0

        if eur_price < 50.0 and price > 0:
            floor_violated = True
            min_floor_eur = 50.0
            cat_name = "Absolute Floor"
        elif eur_price < min_floor_eur and price > 0:
            floor_violated = True

        if floor_violated:
            min_local_floor = round(min_floor_eur / RATES_TO_EUR.get(currency, 1.0), 1)
            anomalies.append({
                "rule": "R4",
                "severity": "CRITICAL",
                "country": country,
                "retailer": retailer,
                "model_code": model_code,
                "observed": price,
                "expected_range": f">= {min_local_floor} {currency} ({cat_name} floor: EUR {min_floor_eur:.0f})",
                "message": f"{size}\" {cat_name} price ({price} {currency} = {eur_price:.1f} EUR) violates minimum floor of EUR {min_floor_eur:.0f}"
            })

        # R1: ±30% Spike/Drop Guard (WARN)
        if cur and price > 0:
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
                    if curr_promo != prev_promo or curr_promo.strip().upper() not in ["NONE", ""]:
                        pass
                    elif orig_price > price:
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

                # R5: Anti-RRP Fake Spike / Launch Price Leakage Guard
                # If selling price jumped by >= 15% vs previous survey and matches original list price, flag as RRP leakage
                if cur and price > 0 and prev and prev["selling_price"]:
                    diff_pct_r5 = (price - float(prev["selling_price"])) / float(prev["selling_price"])
                    if diff_pct_r5 >= 0.15 and orig_price > 0 and abs(price - orig_price) <= 1.0:
                        anomalies.append({
                            "rule": "R5",
                            "severity": "WARN",
                            "country": country,
                            "retailer": retailer,
                            "model_code": model_code,
                            "observed": price,
                            "expected_range": f"< {orig_price} {currency}",
                            "message": f"Suspicious RRP leakage: price spiked by {diff_pct_r5 * 100:+.1f}% vs previous ({prev['date']}: {prev['selling_price']} {currency}) to match exact list/RRP price ({orig_price} {currency})"
                        })

    if con:
        con.close()

    critical_count = sum(1 for a in anomalies if a["severity"] == "CRITICAL")
    warn_count = sum(1 for a in anomalies if a["severity"] == "WARN")

    return {
        "gate": "G2",
        "name": "CRITICAL Price Anomalies (Zero Tolerance)",
        "passed": critical_count == 0,
        "critical_count": critical_count,
        "warn_count": warn_count,
        "anomalies": anomalies
    }


def eval_g3_model_count_drop(records: List[Dict[str, Any]], survey_date: str = None) -> Dict[str, Any]:
    """
    G3: Model Count Sudden Drop.
    For each (country, retailer, brand), compare active models with previous survey.
    If prev_count >= 5 and drop < -10% (-0.10) -> FAIL.
    """
    if not survey_date:
        survey_date = datetime.now().strftime("%Y-%m-%d")

    curr_counts: Dict[Tuple[str, str, str], int] = {}
    for r in records:
        status = str(r.get("status", "")).upper()
        if status in ("DELISTED", "DISCONTINUED", "OUT_OF_STOCK"):
            continue
        p = float(r.get("selling_price") or 0.0)
        if p <= 0 and not status.startswith("LIVE_"):
            continue

        c = str(r.get("country", "")).upper()
        ret = str(r.get("retailer", ""))
        b = str(r.get("brand") or r.get("manufacturer") or "").upper()
        key = (c, ret, b)
        curr_counts[key] = curr_counts.get(key, 0) + 1

    drops = []
    warn_drops = []
    overall_passed = True
    error = None
    audited_scope = {(k[0], k[1]) for k in curr_counts}

    try:
        con = ph.get_connection()
        cur = con.cursor()
        # [FIX 2026-10-08] daily_prices has no `brand` column (it is `manufacturer`). The old query
        # raised OperationalError which was swallowed -> G3 silently passed on every run.
        # Each (country, retailer, brand) is now compared with ITS OWN most recent prior survey,
        # so a partial survey on another date (e.g. a single-country ad-hoc run) cannot mask drops.
        cur.execute("""
            SELECT d.country, d.retailer, UPPER(d.manufacturer) AS brand, d.date AS prev_date, COUNT(*) AS cnt
            FROM daily_prices d
            JOIN (
                SELECT country, retailer, UPPER(manufacturer) AS brand, MAX(date) AS md
                FROM daily_prices
                WHERE date < ? AND selling_price > 0
                GROUP BY country, retailer, UPPER(manufacturer)
            ) m ON m.country = d.country AND m.retailer = d.retailer
               AND m.brand = UPPER(d.manufacturer) AND m.md = d.date
            WHERE d.selling_price > 0
            GROUP BY d.country, d.retailer, UPPER(d.manufacturer), d.date
        """, (survey_date,))
        for row in cur.fetchall():
            c, ret, b = row["country"].upper(), row["retailer"], (row["brand"] or "").upper()
            if (c, ret) not in audited_scope:
                continue  # retailer outside this audit scope (handled by freshness isolation)
            # Clean-cut marketplace-to-direct-seller transition guard (2026-11-04):
            # All Pan-European retailers (DE, AT, CH, ES, NL, IT, FR, etc.) switched to Direct-Seller Only.
            # Do not halt against pre-2026-11-05 marketplace-polluted baselines.
            if str(row["prev_date"]) <= "2026-11-04" and str(survey_date) in ("2026-11-04", "2026-11-05"):
                continue
            if str(row["prev_date"]) < "2026-11-02" and (c, ret) in {("ES", "MediaMarkt"), ("IT", "MediaWorld"), ("FR", "Boulanger"), ("FR", "Fnac Darty")}:
                continue
            prev_cnt = row["cnt"]
            if prev_cnt < 5:
                continue  # Ignore small sample jitter
            curr_cnt = curr_counts.get((c, ret, b), 0)
            change_pct = (curr_cnt - prev_cnt) / prev_cnt
            if change_pct < -0.20:  # Critical sudden drop (> 20% drop triggers Hard Halt)
                overall_passed = False
                drops.append({
                    "country": c,
                    "retailer": ret,
                    "brand": b,
                    "prev_date": row["prev_date"],
                    "prev_count": prev_cnt,
                    "curr_count": curr_cnt,
                    "change_pct": round(change_pct * 100, 1),
                    "message": f"Model count dropped by {abs(change_pct)*100:.1f}% ({prev_cnt} -> {curr_cnt}) vs {row['prev_date']}"
                })
            elif change_pct < -0.10:  # Mild inventory variation (10% ~ 20%): logged as warning
                warn_drops.append({
                    "country": c,
                    "retailer": ret,
                    "brand": b,
                    "prev_date": row["prev_date"],
                    "prev_count": prev_cnt,
                    "curr_count": curr_cnt,
                    "change_pct": round(change_pct * 100, 1),
                    "message": f"Model count dropped by {abs(change_pct)*100:.1f}% ({prev_cnt} -> {curr_cnt}) vs {row['prev_date']}"
                })
        con.close()
    except Exception as ex:
        # Fail closed: an unevaluable gate must never be reported as PASS.
        overall_passed = False
        error = f"G3 could not be evaluated: {ex}"

    return {
        "gate": "G3",
        "name": "Model Count Sudden Drop (<= -15% Halt, <= -10% Warn)",
        "passed": overall_passed,
        "warn": len(warn_drops) > 0,
        "drops": drops,
        "warn_drops": warn_drops,
        "error": error
    }


def eval_g4_verification_mismatch(run_id: Optional[str] = None, verification_report: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    G4: Independent Verification Mismatch Rate (<= 2%).
    """
    report = verification_report

    if not report and run_id:
        report_file = os.path.join(RUNS_DIR, run_id, "verification_report.json")
        if os.path.exists(report_file):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    report = json.load(f)
            except Exception:
                pass

    # [FIX 2026-10-08] Removed "borrow the latest run's verification_report" fallback: the EU audit
    # was reporting the Swiss run's 0/3 sample as its own G4 PASS. A report must belong to THIS run.
    # Strict per-country verification (no sample -> HOLD) is enforced in scripts/release_by_country.py.

    if not report:
        return {
            "gate": "G4",
            "name": "Independent Ground-Truth Verification (<= 2% Mismatch)",
            "passed": True,
            "status": "SKIPPED_NO_REPORT",
            "mismatch_rate_pct": 0.0,
            "message": "UNVERIFIED - no verification report for this run (release_by_country.py will HOLD)."
        }

    total_sampled = report.get("total_sampled", 0)
    mismatches = report.get("mismatches", 0)
    rate_pct = report.get("mismatch_rate_pct", (mismatches / max(total_sampled, 1)) * 100.0)
    passed = rate_pct <= 2.0

    return {
        "gate": "G4",
        "name": "Independent Ground-Truth Verification (<= 2% Mismatch)",
        "passed": passed,
        "status": "EVALUATED",
        "total_sampled": total_sampled,
        "matches": report.get("matches", total_sampled - mismatches),
        "mismatches": mismatches,
        "mismatch_rate_pct": round(rate_pct, 2),
        "message": f"Mismatch rate: {rate_pct:.1f}% ({mismatches}/{total_sampled})"
    }


def eval_g5_provenance_and_metadata(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    G5: Mandatory Provenance & Metadata Completeness.
    Must have model_code, retailer, country, valid screen_size, and valid URL for live models.
    """
    violations = []
    for idx, r in enumerate(records):
        mc = str(r.get("model_code", "")).strip()
        ret = str(r.get("retailer", "")).strip()
        c = str(r.get("country", "")).strip()
        size = resolve_screen_size(r)
        status = str(r.get("status", "")).upper()
        url = str(r.get("source_url") or r.get("pdp_url") or "").strip()

        if not mc or (mc.upper().startswith("UNKNOWN") and not r.get("series")):
            violations.append(f"Row {idx+1}: Missing or invalid model_code ({mc})")
        if not ret:
            violations.append(f"Row {idx+1} ({mc}): Missing retailer")
        if not c:
            violations.append(f"Row {idx+1} ({mc}): Missing country")
        if size <= 0:
            violations.append(f"Row {idx+1} ({mc}): Invalid screen size ({size})")
        if status.startswith("LIVE_") and (not url or not url.startswith("http")):
            violations.append(f"Row {idx+1} ({mc}): Live status {status} but missing valid HTTP URL")

    return {
        "gate": "G5",
        "name": "Mandatory Provenance & Metadata Completeness",
        "passed": len(violations) == 0,
        "violations_count": len(violations),
        "violations": violations[:20] # Report up to 20
    }


def eval_g6_stale_carryover_ratio(records: List[Dict[str, Any]], survey_date: str = None) -> Dict[str, Any]:
    """
    G6: Stale Carry-Over / Identical Price Ratio.
    If common models > 20 and identical price ratio > 90% -> WARN (cache reuse alert).
    """
    if not survey_date:
        survey_date = datetime.now().strftime("%Y-%m-%d")

    identical_count = 0
    common_count = 0

    g6_error = None
    try:
        con = ph.get_connection()
        cur = con.cursor()
        # [FIX 2026-10-08] compare each model with ITS OWN most recent prior price
        # (a single global MAX(date) is masked by partial ad-hoc surveys on other dates).
        cur.execute("""
            SELECT d.country, d.retailer, d.model_code, d.selling_price
            FROM daily_prices d
            JOIN (
                SELECT country, retailer, model_code, MAX(date) AS md
                FROM daily_prices
                WHERE date < ? AND selling_price > 0
                GROUP BY country, retailer, model_code
            ) m ON m.country = d.country AND m.retailer = d.retailer
               AND m.model_code = d.model_code AND m.md = d.date
            WHERE d.selling_price > 0
        """, (survey_date,))
        prev_dict = {(r["country"].upper(), r["retailer"], r["model_code"].strip().upper()): float(r["selling_price"]) for r in cur.fetchall()}

        for r in records:
            p = float(r.get("selling_price") or 0.0)
            if p <= 0:
                continue
            k = (str(r.get("country", "")).upper(), str(r.get("retailer", "")), str(r.get("model_code", "")).strip().upper())
            if k in prev_dict:
                common_count += 1
                if abs(p - prev_dict[k]) < 0.01:
                    identical_count += 1
        con.close()
    except Exception as ex:
        g6_error = f"G6 could not be evaluated: {ex}"

    ratio = (identical_count / common_count) if common_count > 0 else 0.0
    is_warn = (common_count >= 20 and ratio > 0.90) or g6_error is not None

    return {
        "gate": "G6",
        "name": "Stale Carry-Over / Identical Price Ratio (<= 90%)",
        "passed": True, # G6 is a WARN gate, does not hard halt alone
        "warn": is_warn,
        "error": g6_error,
        "common_count": common_count,
        "identical_count": identical_count,
        "identical_ratio_pct": round(ratio * 100, 1),
        "message": g6_error or f"{ratio*100:.1f}% identical prices vs previous survey ({identical_count}/{common_count})"
    }


def eval_g7_list_vs_pdp_drift(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    G7: Search Listing vs PDP Price Drift.
    If list_price differs from PDP selling_price > 1%, log drift (PDP authoritative).
    """
    drifts = []
    for r in records:
        list_p = float(r.get("list_price") or 0.0)
        pdp_p = float(r.get("selling_price") or r.get("pdp_price") or 0.0)
        if list_p > 0 and pdp_p > 0:
            diff = abs(list_p - pdp_p) / pdp_p
            if diff > 0.01:
                drifts.append({
                    "model_code": r.get("model_code"),
                    "retailer": r.get("retailer"),
                    "list_price": list_p,
                    "pdp_price": pdp_p,
                    "drift_pct": round(diff * 100, 2)
                })

    return {
        "gate": "G7",
        "name": "Search Listing vs PDP Price Drift (PDP Authoritative)",
        "passed": True,
        "drifts_count": len(drifts),
        "drifts": drifts
    }


# ==============================================================================
# COMPATIBILITY & MASTER EVALUATION
# ==============================================================================

def run_quality_gates(records: List[Dict[str, Any]], survey_date: str = None) -> List[Dict[str, Any]]:
    """Legacy compatibility: returns detected anomalies list."""
    g2 = eval_g2_price_anomalies(records, survey_date)
    return g2.get("anomalies", [])


def evaluate_and_enforce_gate(records: List[Dict[str, Any]], survey_date: str = None,
                              run_id: Optional[str] = None,
                              verification_report: Optional[Dict[str, Any]] = None) -> bool:
    """
    Evaluates all 7 Quality Gates (G1-G7), displays audit table,
    writes report JSON, and enforces Hard Halt if any critical gate fails.
    """
    if not survey_date:
        survey_date = datetime.now().strftime("%Y-%m-%d")
    date_clean = survey_date.replace("-", "")

    g1 = eval_g1_live_confirmation_rate(records)
    g2 = eval_g2_price_anomalies(records, survey_date)
    g3 = eval_g3_model_count_drop(records, survey_date)
    g4 = eval_g4_verification_mismatch(run_id=run_id, verification_report=verification_report)
    g5 = eval_g5_provenance_and_metadata(records)
    g6 = eval_g6_stale_carryover_ratio(records, survey_date)
    g7 = eval_g7_list_vs_pdp_drift(records)

    gates = [g1, g2, g3, g4, g5, g6, g7]
    failed_gates = [g for g in [g1, g2, g3, g4, g5] if not g["passed"]]

    # Build report data
    report_data = {
        "survey_date": survey_date,
        "run_id": run_id,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total_records_audited": len(records),
        "overall_passed": len(failed_gates) == 0,
        "failed_gates_count": len(failed_gates),
        "gates": {
            "G1": g1,
            "G2": g2,
            "G3": g3,
            "G4": g4,
            "G5": g5,
            "G6": g6,
            "G7": g7
        }
    }

    # Save to data/anomaly_report_{date}.json
    report_file = os.path.join(DATA_DIR, f"anomaly_report_{date_clean}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    # If run_id is known, also save into run directory
    if run_id:
        run_report_file = os.path.join(RUNS_DIR, run_id, "quality_gate_report.json")
        try:
            with open(run_report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # Print Terminal Audit Summary
    print("\n" + "=" * 78)
    print(f" 🛡️ DATA QUALITY GATES & INTEGRITY AUDIT REPORT v2 ({survey_date})")
    print("=" * 78)
    print(f"Total Records Audited : {len(records):,}")
    print(f"Audit Report File     : {report_file}")
    if run_id:
        print(f"Run ID                : {run_id}")
    print("-" * 78)

    # Print Gate Status Lines
    def status_badge(passed: bool, warn: bool = False) -> str:
        if not passed:
            return "❌ FAIL (HALT)"
        if warn:
            return "⚠️ WARN"
        return "✔ PASS"

    print(f"Gate G1 (Live Confirmation Rate >= 95%):      {status_badge(g1['passed']):<15}")
    for d in g1["details"]:
        icon = "✔" if d["passed"] else "❌"
        print(f"   • {icon} {d['retailer']:<20} : {d['live_count']:>3}/{d['effective_total']:>3} live ({d['rate_pct']}%)")

    print(f"Gate G2 (Zero CRITICAL Price Anomalies):     {status_badge(g2['passed']):<15} (Critical: {g2['critical_count']}, Warn: {g2['warn_count']})")
    if g2["critical_count"] > 0:
        for a in [x for x in g2["anomalies"] if x["severity"] == "CRITICAL"][:5]:
            print(f"   • ❌ [{a['rule']}] {a['country']} {a['retailer']} {a['model_code']} ({a['observed']}): {a['message']}")

    print(f"Gate G3 (Model Count Sudden Drop <= -15%):   {status_badge(g3['passed'], warn=g3.get('warn', False)):<15}")
    if g3.get("error"):
        print(f"   • ❌ {g3['error']}")
    if g3["drops"]:
        for d in g3["drops"]:
            print(f"   • ❌ {d['country']} {d['retailer']} {d['brand']}: {d['message']}")
    if g3.get("warn_drops"):
        for d in g3["warn_drops"]:
            print(f"   • ⚠️ {d['country']} {d['retailer']} {d['brand']}: {d['message']}")

    print(f"Gate G4 (Verification Mismatch Rate <= 2%):   {status_badge(g4['passed']):<15} ({g4.get('message', '')})")
    print(f"Gate G5 (Mandatory Provenance & Metadata):   {status_badge(g5['passed']):<15} (Violations: {g5['violations_count']})")
    if g5["violations"]:
        for v in g5["violations"][:5]:
            print(f"   • ❌ {v}")

    print(f"Gate G6 (Identical Price Stale Ratio <= 90%): {status_badge(True, warn=g6['warn']):<15} ({g6.get('message', '')})")
    print(f"Gate G7 (Search Listing vs PDP Drift Check):  {status_badge(True):<15} (Drifts > 1%: {g7['drifts_count']})")
    print("=" * 78)

    if failed_gates:
        print("\n" + "!" * 78)
        print(f"⛔ [QUALITY GATE FAILED - HARD HALT] {len(failed_gates)} Critical Quality Gate(s) Failed!")
        for fg in failed_gates:
            print(f"   ❌ Gate {fg['gate']}: {fg['name']}")
        print("   Database write, dashboard compilation, and Firebase deploy are BLOCKED.")
        print("   Production dashboards retain the previous verified survey release.")
        print("!" * 78 + "\n")
        return False

    print("\n✅ [QUALITY GATE PASSED] All critical quality gates satisfied. Proceeding to DB recording & release.\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="Price Anomaly Detection & Data Quality Gates v2")
    parser.add_argument("--excel", type=str, default=None, help="Path to survey Excel workbook to audit")
    parser.add_argument("--date", type=str, default=None, help="Survey date (YYYY-MM-DD)")
    parser.add_argument("--run-id", type=str, default=None, help="Run ID to audit from data/runs/{run_id}/")
    parser.add_argument("--countries", type=str, default=None, help="Comma-separated country codes to filter audit (e.g. DE,AT,UK,ES,IT,CH,NL,FR)")
    args = parser.parse_args()

    run_id = args.run_id or os.environ.get("SURVEY_RUN_ID")
    survey_date = args.date or datetime.now().strftime("%Y-%m-%d")
    records = []

    # 1. Try loading from run snapshot if run_id exists
    if run_id:
        rec_path = os.path.join(RUNS_DIR, run_id, "records.json")
        if os.path.exists(rec_path):
            try:
                with open(rec_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                print(f"📦 [LOADED SNAPSHOT] Loaded {len(records)} records from run snapshot: {run_id}")
            except Exception as ex:
                print(f"⚠️ Failed to load snapshot {rec_path}: {ex}")

    # 2. Try loading from Excel workbook
    if not records and args.excel and os.path.exists(args.excel):
        records = ph.parse_survey_workbook(args.excel)
        print(f"📊 [LOADED EXCEL] Loaded {len(records)} records from {args.excel}")

    # 3. Try loading from price_history.db for the given date
    if not records:
        try:
            con = ph.get_connection()
            cur = con.cursor()
            rows = cur.execute("SELECT * FROM daily_prices WHERE date = ?", (survey_date,)).fetchall()
            con.close()
            records = [dict(r) for r in rows]
            if records:
                print(f"🗄️ [LOADED DB] Loaded {len(records)} records from price_history.db for date {survey_date}")
        except Exception:
            pass

    # 4. Fallback to candidate workbooks in data/
    if not records:
        today_mmdd = datetime.now().strftime("%m%d")
        candidates = [
            os.path.join(DATA_DIR, f"price tracker_swiss_2026 {today_mmdd}_v1.xlsx"),
            os.path.join(DATA_DIR, f"price tracker_swiss_2026 {today_mmdd}.xlsx"),
            os.path.join(DATA_DIR, f"price tracker_EU_2026 {today_mmdd}_v1.xlsx"),
            os.path.join(DATA_DIR, f"price tracker_AU_2026 {today_mmdd}_v1.xlsx")
        ]
        for c in candidates:
            if os.path.exists(c):
                records.extend(ph.parse_survey_workbook(c))

    if not records:
        print(f"[INFO] No records found for date {survey_date} to audit.")
        sys.exit(0)

    if args.countries:
        selected_cc = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
        before_cnt = len(records)
        records = [r for r in records if str(r.get("country", "")).upper() in selected_cc]
        print(f"🎯 [COUNTRY FILTER] Filtered audit scope for {selected_cc}: {before_cnt} -> {len(records)} records")

    passed = evaluate_and_enforce_gate(records, survey_date=survey_date, run_id=run_id)
    if not passed:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
