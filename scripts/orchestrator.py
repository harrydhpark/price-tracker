# -*- coding: utf-8 -*-
"""
Master Orchestrator Agent CLI for Pan-European TV Price Tracker & Promo Analyzer.
Coordinates multi-agent regional scrapers, data normalization, SQLite price history,
Data Intelligence Engine analysis, web dashboard compilation, and Firebase deployment.
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from scripts.core.region_manager import (
    get_all_regions,
    get_all_countries,
    get_region
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PYTHON_EXE = os.path.join(ROOT_DIR, "python_env", "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

def run_cmd(cmd_list: List[str], desc: str) -> bool:
    print(f"\n▶ [STEP] {desc}...")
    start = time.time()
    try:
        proc = subprocess.run(
            cmd_list,
            cwd=ROOT_DIR,
            check=True,
            text=True,
            encoding="utf-8",
            capture_output=False,
            shell=(os.name == 'nt')
        )
        elapsed = round(time.time() - start, 1)
        print(f"✔ [SUCCESS] {desc} completed in {elapsed}s.")
        return True
    except subprocess.CalledProcessError as e:
        elapsed = round(time.time() - start, 1)
        print(f"❌ [FAILED] {desc} failed (Exit Code {e.returncode}) after {elapsed}s.")
        return False
    except Exception as ex:
        print(f"❌ [ERROR] {desc} error: {ex}")
        return False

def sync_regional_data(region_id: Optional[str] = None):
    print("\n=======================================================")
    print("🔄 [ORCHESTRATOR] Running Regional Sync Pipelines")
    print("=======================================================")
    
    # 1. Western EU & DACH (DE, AT, UK, ES, IT, NL, FR)
    if not region_id or region_id in ["dach", "western_eu"]:
        run_cmd([PYTHON_EXE, "scripts/sync_eu_retailers.py"], "Sync Western EU & DACH Retailers to Excel")

    # 2. Eastern EU (CZ, GR, HU)
    if not region_id or region_id in ["eastern_eu"]:
        run_cmd([PYTHON_EXE, "scripts/sync_eastern_eu.py"], "Sync Eastern EU (CZ, GR, HU) Retailers to Excel")

    # 3. Swiss Local Survey (MediaMarkt, Interdiscount, Digitec)
    if not region_id or region_id in ["dach", "ch"]:
        run_cmd([PYTHON_EXE, "scripts/sync_all_retailers.py"], "Sync Swiss Multi-Retailer Workbook")

    # 4. Australia Survey (JB Hi-Fi, The Good Guys, Harvey Norman)
    if not region_id or region_id in ["au", "australia"]:
        run_cmd([PYTHON_EXE, "scripts/sync_au_retailers.py"], "Sync Australia Retailers to Excel")

    # 5. New EU Retailers (PL MediaExpert, PT Worten, RO Altex, SE Elgiganten)
    if not region_id or region_id in ["nordics", "eastern_eu", "western_eu", "new_eu"]:
        run_cmd([PYTHON_EXE, "scripts/sync_new_eu_retailers.py"], "Sync New EU Retailers (PL, PT, RO, SE) to Excel")

def sync_master_registry():
    print("\n=======================================================")
    print("🗄️ [ORCHESTRATOR] Synchronizing Master Product URL Registry")
    print("=======================================================")
    run_cmd([PYTHON_EXE, "scripts/build_master_url_registry.py"], "Merge New URLs into master_product_urls.json")

def run_quality_gates():
    print("\n=======================================================")
    print("🛡️ [ORCHESTRATOR] Running Data Quality Gates & Anomaly Audits")
    print("=======================================================")
    run_cmd([PYTHON_EXE, "scripts/quality_gates.py"], "Audit Quality Gates (R1-R4)")

def update_price_history():
    print("\n=======================================================")
    print("📊 [ORCHESTRATOR] Updating SQLite Price History Database")
    print("=======================================================")
    today_str = datetime.now().strftime("%m%d")
    eu_target = os.path.join(ROOT_DIR, "data", f"price tracker_EU_2026 {today_str}_v1.xlsx")
    swiss_target = os.path.join(ROOT_DIR, "data", f"price tracker_swiss_2026 {today_str}_v1.xlsx")
    au_target = os.path.join(ROOT_DIR, "data", f"price tracker_AU_2026 {today_str}_v1.xlsx")

    # If exact date not found, pick latest
    import glob
    if not os.path.exists(eu_target):
        cand = glob.glob(os.path.join(ROOT_DIR, "data", "price tracker_EU_2026 *.xlsx"))
        if cand: eu_target = sorted(cand)[-1]
    if not os.path.exists(swiss_target):
        cand = glob.glob(os.path.join(ROOT_DIR, "data", "price tracker_swiss_2026 *.xlsx"))
        if cand: swiss_target = sorted(cand)[-1]
    if not os.path.exists(au_target):
        cand = glob.glob(os.path.join(ROOT_DIR, "data", "price tracker_AU_2026 *.xlsx"))
        if cand: au_target = sorted(cand)[-1]

    cmd = [
        PYTHON_EXE, "-c",
        f"import sys; sys.path.insert(0, '.'); from scripts.price_history import record_survey_from_excel; "
        f"record_survey_from_excel(r'{eu_target}'); record_survey_from_excel(r'{swiss_target}'); record_survey_from_excel(r'{au_target}')"
    ]
    run_cmd(cmd, "Record Workbooks into price_history.db")

def run_data_intelligence(date: Optional[str] = None, country: Optional[str] = None):
    print("\n=======================================================")
    print("🧠 [ORCHESTRATOR] Running Data Intelligence Engine")
    print("=======================================================")
    cmd = [PYTHON_EXE, "scripts/data_intelligence_engine.py"]
    if date:
        cmd.extend(["--date", date])
    if country:
        cmd.extend(["--country", country])
    run_cmd(cmd, "Generate 1:1 Gap Analysis, WoW Trends & Executive Briefing")

def compile_dashboards():
    print("\n=======================================================")
    print("🖥️ [ORCHESTRATOR] Compiling Web Dashboards")
    print("=======================================================")
    run_cmd([PYTHON_EXE, "scripts/generate_eu_dashboard.py"], "Compile Pan-European Price Dashboard")
    run_cmd([PYTHON_EXE, "scripts/generate_dashboard.py"], "Compile Swiss Price Dashboard")
    run_cmd([PYTHON_EXE, "scripts/generate_au_dashboard.py"], "Compile Australia Price Dashboard")

def deploy_firebase():
    print("\n=======================================================")
    print("🚀 [ORCHESTRATOR] Deploying Dashboards to Firebase Hosting")
    print("=======================================================")
    npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
    run_cmd([npx_cmd, "firebase", "deploy", "--only", "hosting:eu-price-tracker,hosting:swiss-price-tracker,hosting:au-price-tracker"], "Deploy to Firebase Hosting")

def main():
    parser = argparse.ArgumentParser(description="Master Multi-Agent TV Price Tracker Orchestrator")
    parser.add_argument("--all", action="store_true", help="Execute across all configured regions")
    parser.add_argument("--region", type=str, default=None, help="Target region ID (dach, western_eu, eastern_eu, au)")
    parser.add_argument("--country", type=str, default=None, help="Target country code (DE, UK, FR, ES, IT, NL, AT, CH, CZ, GR, HU, AU)")
    parser.add_argument("--sync", action="store_true", help="Run regional Excel synchronization")
    parser.add_argument("--registry", action="store_true", help="Synchronize Master Product URL Registry")
    parser.add_argument("--gates", action="store_true", help="Run Quality Gates and Anomaly Audits")
    parser.add_argument("--db-sync", action="store_true", help="Record Excel workbooks into price_history.db")
    parser.add_argument("--analyze-only", action="store_true", help="Run only Data Intelligence Engine and generate reports")
    parser.add_argument("--dashboard", action="store_true", help="Compile standalone web dashboards")
    parser.add_argument("--deploy", action="store_true", help="Deploy web dashboards to Firebase Hosting")
    parser.add_argument("--full", action="store_true", help="Run full pipeline: Sync -> Registry -> Gates -> DB -> Analyze -> Dashboard -> Deploy")
    args = parser.parse_args()

    total_start = time.time()
    regions = get_all_regions()
    countries = get_all_countries()
    print("=======================================================")
    print("🌐 [MASTER ORCHESTRATOR] Pan-European TV Price Tracker")
    print(f"  • Registered Regions ({len(regions)}): {list(regions.keys())}")
    print(f"  • Active Countries ({len(countries)}): {list(countries.keys())}")
    print(f"  • Target Region Filter: {args.region or 'ALL'}")
    print("=======================================================")

    if args.analyze_only:
        run_data_intelligence(country=args.country)
        compile_dashboards()
        print(f"\n🎉 [COMPLETE] Analysis & Dashboard compilation finished in {round(time.time() - total_start, 1)}s.")
        return

    if args.full:
        sync_regional_data(args.region)
        sync_master_registry()
        run_quality_gates()
        update_price_history()
        run_data_intelligence(country=args.country)
        compile_dashboards()
        deploy_firebase()
        print(f"\n🎉 [COMPLETE] Full End-to-End Survey Pipeline completed in {round(time.time() - total_start, 1)}s.")
        return

    # Individual flags
    ran_anything = False
    if args.sync:
        sync_regional_data(args.region)
        ran_anything = True
    if args.registry:
        sync_master_registry()
        ran_anything = True
    if args.gates:
        run_quality_gates()
        ran_anything = True
    if args.db_sync:
        update_price_history()
        ran_anything = True
    if args.dashboard:
        compile_dashboards()
        ran_anything = True
    if args.deploy:
        deploy_firebase()
        ran_anything = True

    if not ran_anything:
        # Default behavior if no flags: run analysis + compile dashboards
        print("ℹ️ No specific action flag specified. Defaulting to: --analyze-only + --dashboard")
        run_data_intelligence(country=args.country)
        compile_dashboards()

    print(f"\n🎉 [ORCHESTRATOR FINISHED] Total elapsed time: {round(time.time() - total_start, 1)}s.")

if __name__ == "__main__":
    main()
