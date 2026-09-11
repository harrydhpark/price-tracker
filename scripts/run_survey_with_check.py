import os
import sys
import json
import re
import glob
import shutil
import argparse
import subprocess
from datetime import datetime, timedelta
import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

# Root path of the project
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
HISTORY_DIR = os.path.join(ROOT_DIR, "History")

def get_yesterday_info():
    """Finds the latest history folder in History directory that is older than today,
    and returns its date string (MMDD) and the path to its price tracker file."""
    folders = []
    if not os.path.exists(HISTORY_DIR):
        print(f"[ERROR] History directory not found at: {HISTORY_DIR}")
        return None, None
        
    for name in os.listdir(HISTORY_DIR):
        path = os.path.join(HISTORY_DIR, name)
        if os.path.isdir(path) and re.match(r'^\d{4}\s+\d{4}$', name):
            folders.append(name)
            
    folders.sort()
    
    # Exclude today's folder if it already exists
    today_folder_prefix = datetime.now().strftime("%Y %m%d")
    valid_folders = [f for f in folders if f != today_folder_prefix]
    
    if not valid_folders:
        print("[WARN] No historical folders found. Using yesterday's date relative to today.")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%m%d")
        return yesterday_str, None
        
    latest_folder = valid_folders[-1]
    mmdd = latest_folder.split()[1] # "0709"
    
    # Find price tracker in this folder
    folder_path = os.path.join(HISTORY_DIR, latest_folder)
    pt_files = glob.glob(os.path.join(folder_path, "price tracker_swiss_*.xlsx"))
    pt_files = [f for f in pt_files if not os.path.basename(f).startswith("~$")]
    if pt_files:
        pt_files.sort()
        return mmdd, pt_files[-1]
        
    return mmdd, None

def get_yesterday_sheet_counts(pt_file):
    """Loads yesterday's counts from the archived price tracker excel sheet."""
    counts = {}
    if not pt_file or not os.path.exists(pt_file):
        print(f"[WARN] Archived price tracker file not found: {pt_file}")
        return counts
        
    try:
        wb = openpyxl.load_workbook(pt_file, read_only=True)
        for sname in wb.sheetnames:
            if sname.endswith("_Full"):
                # Subtract 1 header row
                counts[sname] = max(0, wb[sname].max_row - 1)
        wb.close()
    except Exception as e:
        print(f"[ERROR] Failed to load yesterday's sheet counts from {pt_file}: {e}")
        
    return counts

def get_today_json_counts():
    """Reads today's counts from raw JSON files in the data directory."""
    counts = {
        "MediaMarkt_Samsung_Full": 0,
        "MediaMarkt_LG_Full": 0,
        "Interdiscount_Samsung_Full": 0,
        "Interdiscount_LG_Full": 0,
        "Digitec_Samsung_Full": 0,
        "Digitec_LG_Full": 0
    }
    
    mapping = {
        "MediaMarkt_Samsung_Full": "raw_mediamarkt_samsung.json",
        "MediaMarkt_LG_Full": "raw_mediamarkt_lg.json",
        "Interdiscount_Samsung_Full": "raw_interdiscount_samsung.json",
        "Interdiscount_LG_Full": "raw_interdiscount_lg.json",
        "Digitec_Samsung_Full": "raw_digitec_samsung.json",
        "Digitec_LG_Full": "raw_digitec_lg.json"
    }
    
    for sheet, fname in mapping.items():
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    counts[sheet] = len(data)
            except Exception as e:
                print(f"[WARN] Failed to read {fname}: {e}")
                
    return counts

def get_stale_raw_targets():
    """Checks which retailer raw datasets are missing or not updated today."""
    today_date_str = datetime.now().strftime("%Y-%m-%d")
    mapping = {
        "mediamarkt": ["raw_mediamarkt_samsung.json", "raw_mediamarkt_lg.json"],
        "interdiscount": ["raw_interdiscount_samsung.json", "raw_interdiscount_lg.json"],
        "digitec": ["raw_digitec_samsung.json", "raw_digitec_lg.json"]
    }
    stale = {"mediamarkt": False, "interdiscount": False, "digitec": False}
    for ret, files in mapping.items():
        for fname in files:
            p = os.path.join(DATA_DIR, fname)
            if not os.path.exists(p):
                stale[ret] = True
            else:
                mtime = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d")
                if mtime != today_date_str:
                    stale[ret] = True
    return stale

def run_scraper(script_name):
    """Runs a single scraper script with a timeout multiplier.
    Returns: (success: bool, returncode: int, stderr_tail: str)
    """
    env = os.environ.copy()
    env["TIMEOUT_MULTIPLIER"] = "1.5"
    
    script_path = os.path.join(ROOT_DIR, "scripts", script_name)
    print(f"\n[LAUNCH] Launching scraper with TIMEOUT_MULTIPLIER=1.5: {script_name}...")
    
    try:
        res = subprocess.run(
            [sys.executable, script_path],
            env=env,
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.stdout:
            print(res.stdout)
        if res.returncode != 0:
            stderr_tail = "\n".join((res.stderr or "").strip().splitlines()[-20:])
            print(f"[ERROR] Scraper {script_name} exited with error code {res.returncode}")
            if stderr_tail:
                print(f"[STDERR TAIL]\n{stderr_tail}")
            return False, res.returncode, stderr_tail
        return True, 0, ""
    except Exception as e:
        err_msg = str(e)
        print(f"[ERROR] Failed to execute scraper {script_name}: {err_msg}")
        return False, -1, err_msg

def run_pipeline_step(step_name, cmd_args):
    """Executes a pipeline step script and validates its exit code.
    Aborts immediately on non-zero exit code.
    """
    print("\n" + "="*50)
    print(f" RUNNING: {step_name.upper()}")
    print("="*50)
    res = subprocess.run(
        cmd_args,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if res.stdout:
        print(res.stdout)
    if res.returncode != 0:
        stderr_tail = "\n".join((res.stderr or "").strip().splitlines()[-20:])
        print("\n" + "!"*60)
        print(f"[FATAL STEP FAILURE] Stage: '{step_name}' failed with exit code {res.returncode}")
        if stderr_tail:
            print(f"[STDERR TAIL (last 20 lines)]:\n{stderr_tail}")
        print("!"*60)
        print(f"[HALT] Pipeline aborted before subsequent stages (Dashboard/Deploy).")
        sys.exit(res.returncode if res.returncode != 0 else 1)
    return res

def main():
    parser = argparse.ArgumentParser(description="Automated Survey Verification & Execution Wrapper")
    parser.add_argument("--allow-partial", action="store_true", help="Allow pipeline to proceed using previous survey data if some retailers fail")
    args = parser.parse_args()

    print("="*60)
    print(" AUTOMATED SURVEY VERIFICATION & RERUN wrapper")
    print("="*60)
    if args.allow_partial:
        print("[MODE] --allow-partial enabled: Partial retailer failures will be tolerated.")
    
    # Retailer scraper status tracker
    scraper_status = {
        "mediamarkt": True,
        "interdiscount": True,
        "digitec": True
    }
    scraper_errors = {}
    
    # 0. Check for stale/missing datasets and run initial live scrape if needed
    stale_targets = get_stale_raw_targets()
    stale_any = any(stale_targets.values())
    if stale_any:
        print("\n[INITIAL LIVE SCRAPE] Found stale or missing raw datasets for today.")
        print("➔ Initiating live web scraping pass before count verification...")
        if stale_targets["mediamarkt"]:
            print("  • MediaMarkt: Launching scrape_mediamarkt.py...")
            ok, code, err = run_scraper("scrape_mediamarkt.py")
            scraper_status["mediamarkt"] = ok
            if not ok:
                scraper_errors["mediamarkt"] = (code, err)
        if stale_targets["interdiscount"]:
            print("  • Interdiscount: Launching scrape_interdiscount.py...")
            ok, code, err = run_scraper("scrape_interdiscount.py")
            scraper_status["interdiscount"] = ok
            if not ok:
                scraper_errors["interdiscount"] = (code, err)
        if stale_targets["digitec"]:
            print("  • Digitec: Launching scrape_digitec.py...")
            ok, code, err = run_scraper("scrape_digitec.py")
            scraper_status["digitec"] = ok
            if not ok:
                scraper_errors["digitec"] = (code, err)
        print("\n[INITIAL LIVE SCRAPE DONE] Proceeding to baseline comparison...\n")
    
    # 1. Get yesterday's info and counts
    yesterday_mmdd, yesterday_pt = get_yesterday_info()
    print(f"[BASELINE] Resolved baseline survey date: 2026 {yesterday_mmdd}")
    print(f"[BASELINE] Yesterday's price tracker path: {yesterday_pt}")
    
    yesterday_counts = get_yesterday_sheet_counts(yesterday_pt)
    print(f"[BASELINE COUNTS] {yesterday_counts}")
    
    # Fallback default baseline if yesterday_pt is missing (updated to current golden counts)
    default_baseline = {
        "MediaMarkt_Samsung_Full": 69,
        "MediaMarkt_LG_Full": 57,
        "Interdiscount_Samsung_Full": 73,
        "Interdiscount_LG_Full": 38,
        "Digitec_Samsung_Full": 98,
        "Digitec_LG_Full": 123
    }
    
    for k, v in default_baseline.items():
        if k not in yesterday_counts or yesterday_counts[k] == 0:
            yesterday_counts[k] = v
            print(f"  -> Using default baseline for {k}: {v}")
            
    # 2. Get today's initial counts
    today_counts = get_today_json_counts()
    print(f"[TODAY COUNTS] {today_counts}")
    
    # 3. Compare and trigger rerun
    rerun_targets = {
        "mediamarkt": False,
        "interdiscount": False,
        "digitec": False
    }
    
    comparison_results = {}
    needs_rerun = False
    
    diff_threshold = float(os.environ.get("SURVEY_DIFF_THRESHOLD", "0.10"))
    print(f"[CONFIG] Active survey discrepancy threshold: {diff_threshold*100:.1f}%")

    for sheet, y_count in yesterday_counts.items():
        if sheet not in today_counts:
            print(f"[WARN] Sheet '{sheet}' not found in today_counts mapping. Skipping baseline comparison.")
            continue
        t_count = today_counts.get(sheet, 0)
        diff_pct = 0.0
        if y_count > 0:
            diff_pct = abs(t_count - y_count) / y_count
            
        diff_formatted = f"{(t_count - y_count):+d} ({diff_pct*100:.2f}%)"
        print(f"Sheet '{sheet}': Yesterday={y_count} | Today={t_count} | Diff={diff_formatted}")
        
        comparison_results[sheet] = {
            "yesterday": y_count,
            "today": t_count,
            "diff_pct": diff_pct,
            "action": "OK"
        }
        
        if diff_pct >= diff_threshold:
            needs_rerun = True
            comparison_results[sheet]["action"] = "NEEDS RERUN"
            
            # Map sheet to scraper script prefix
            if "MediaMarkt" in sheet:
                rerun_targets["mediamarkt"] = True
            elif "Interdiscount" in sheet:
                rerun_targets["interdiscount"] = True
            elif "Digitec" in sheet:
                rerun_targets["digitec"] = True
                
    if not needs_rerun:
        print(f"\n[SUCCESS] No brands or retailers differ by {diff_threshold*100:.1f}% or more compared to yesterday. Skipping reruns.")
    else:
        print(f"\n[WARNING] Found survey count discrepancies of {diff_threshold*100:.1f}% or more. Triggering automated reruns...")
        
        # We try up to 3 times to get better counts
        for attempt in range(1, 4):
            print(f"\n--- RERUN ATTEMPT {attempt}/3 ---")
            
            any_rerun_in_this_attempt = False
            
            # Check which scrapers to run
            if rerun_targets["mediamarkt"]:
                print("➔ Rerunning MediaMarkt scraper...")
                ok, code, err = run_scraper("scrape_mediamarkt.py")
                scraper_status["mediamarkt"] = ok
                if not ok:
                    scraper_errors["mediamarkt"] = (code, err)
                else:
                    scraper_errors.pop("mediamarkt", None)
                any_rerun_in_this_attempt = True
                
            if rerun_targets["interdiscount"]:
                print("➔ Rerunning Interdiscount scraper...")
                ok, code, err = run_scraper("scrape_interdiscount.py")
                scraper_status["interdiscount"] = ok
                if not ok:
                    scraper_errors["interdiscount"] = (code, err)
                else:
                    scraper_errors.pop("interdiscount", None)
                any_rerun_in_this_attempt = True
                
            if rerun_targets["digitec"]:
                print("➔ Rerunning Digitec scraper...")
                ok, code, err = run_scraper("scrape_digitec.py")
                scraper_status["digitec"] = ok
                if not ok:
                    scraper_errors["digitec"] = (code, err)
                else:
                    scraper_errors.pop("digitec", None)
                any_rerun_in_this_attempt = True
                
            if not any_rerun_in_this_attempt:
                break
                
            # Reload counts after rerun
            today_counts = get_today_json_counts()
            print(f"[RELOADED COUNTS] {today_counts}")
            
            # Reset rerun targets for next iteration
            rerun_targets = {
                "mediamarkt": False,
                "interdiscount": False,
                "digitec": False
            }
            
            needs_rerun_still = False
            for sheet, y_count in yesterday_counts.items():
                if sheet not in today_counts:
                    continue
                t_count = today_counts.get(sheet, 0)
                diff_pct = abs(t_count - y_count) / y_count if y_count > 0 else 0
                
                comparison_results[sheet]["today"] = t_count
                comparison_results[sheet]["diff_pct"] = diff_pct
                
                if diff_pct >= diff_threshold:
                    needs_rerun_still = True
                    comparison_results[sheet]["action"] = "STILL DISCREPANT"
                    
                    if "MediaMarkt" in sheet:
                        rerun_targets["mediamarkt"] = True
                    elif "Interdiscount" in sheet:
                        rerun_targets["interdiscount"] = True
                    elif "Digitec" in sheet:
                        rerun_targets["digitec"] = True
                else:
                    comparison_results[sheet]["action"] = "RESOLVED"
                    
            if not needs_rerun_still:
                print(f"\n[RESOLVED] All discrepancies resolved under the {diff_threshold*100:.1f}% threshold after retries.")
                break
            else:
                print(f"\n[WARN] Discrepancies still exist after attempt {attempt}. Retrying...")
                
    # Check scraper execution status before proceeding to sync and export
    failed_retailers = [ret for ret, ok in scraper_status.items() if not ok]
    if failed_retailers:
        print("\n" + "!"*60)
        print(f"[ERROR] Scraper execution failed for: {', '.join([r.upper() for r in failed_retailers])}")
        for ret in failed_retailers:
            code, err = scraper_errors.get(ret, (-1, "Unknown error"))
            print(f"  • {ret.upper()}: Exit code {code}")
            if err:
                print(f"    Stderr (last 20 lines):\n{err}")
        print("!"*60)
        
        if not args.allow_partial:
            print("\n[FATAL] One or more scrapers failed and --allow-partial is not enabled.")
            print("[FATAL] Aborting pipeline to prevent processing or deploying incomplete/corrupted data.")
            sys.exit(1)
        else:
            print("\n[WARN] --allow-partial is enabled. Proceeding with remaining retailers.")
            print(f"[WARN] Failed retailer data will be retained from previous survey with '[이전주 데이터]' badge.")

    # 4. Proceed to final pipeline execution (Sync, Registry Update, History Archiving, Dashboard, Deploy)
    sync_path = os.path.join(ROOT_DIR, "scripts", "sync_all_retailers.py")
    run_pipeline_step("Final Sync & Excel Compilation", [sys.executable, sync_path])
    
    # 4.1 Update Master URL Registry
    registry_path = os.path.join(ROOT_DIR, "scripts", "build_master_url_registry.py")
    run_pipeline_step("Master URL Registry Update", [sys.executable, registry_path])
    
    # 4.2 Quality Gates & Anomaly Audit
    gate_path = os.path.join(ROOT_DIR, "scripts", "quality_gates.py")
    run_pipeline_step("Data Quality Gates & Price Anomaly Audit", [sys.executable, gate_path])
    
    # Resolve MMDD date string for files
    today_mmdd = datetime.now().strftime("%m%d")
    today_folder_name = datetime.now().strftime("%Y %m%d") # "2026 0710"
    
    # 5. History Archiving
    print("\n" + "="*50)
    print(" ARCHIVING FILES TO HISTORY")
    print("="*50)
    today_history_dir = os.path.join(HISTORY_DIR, today_folder_name)
    os.makedirs(today_history_dir, exist_ok=True)
    
    # Source files in data/
    pt_source = os.path.join(DATA_DIR, f"price tracker_swiss_2026 {today_mmdd}_v1.xlsx")
    if not os.path.exists(pt_source):
        pt_source = os.path.join(DATA_DIR, f"price tracker_swiss_2026 {today_mmdd}.xlsx")
        
    ata_source = os.path.join(DATA_DIR, f"Swiss_ATA_Comparison_2026_{today_mmdd}.xlsx")
    if not os.path.exists(ata_source):
        ata_source = os.path.join(DATA_DIR, f"Swiss_ATA_Comparison_2026_{today_mmdd}_v1.xlsx")
        
    # Copy files
    if os.path.exists(pt_source):
        shutil.copy2(pt_source, today_history_dir)
        print(f"Copied: {pt_source} -> {today_history_dir}")
    if os.path.exists(ata_source):
        shutil.copy2(ata_source, today_history_dir)
        print(f"Copied: {ata_source} -> {today_history_dir}")
        
    # 6. Rebuild HTML Dashboard
    dash_path = os.path.join(ROOT_DIR, "scripts", "generate_dashboard.py")
    run_pipeline_step("Dashboard Generation", [sys.executable, dash_path])
    
    # Copy compiled HTML to History folder
    html_source = os.path.join(DATA_DIR, "swiss_price_dashboard.html")
    if os.path.exists(html_source):
        shutil.copy2(html_source, today_history_dir)
        print(f"Copied: {html_source} -> {today_history_dir}")
        
    # 7. Firebase Hosting Deploy
    print("\n" + "="*50)
    print(" DEPLOYING TO FIREBASE HOSTING")
    print("="*50)
    try:
        deploy_res = subprocess.run(
            ["firebase", "deploy", "--only", "hosting:swiss-price-tracker"],
            cwd=ROOT_DIR,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if deploy_res.stdout:
            print(deploy_res.stdout)
        if deploy_res.returncode == 0:
            print("[SUCCESS] Deployed successfully to https://swiss-price-tracker-lge.web.app")
        else:
            stderr_tail = "\n".join((deploy_res.stderr or "").strip().splitlines()[-20:])
            print(f"[ERROR] Firebase deployment failed with exit code {deploy_res.returncode}")
            if stderr_tail:
                print(f"[STDERR TAIL]\n{stderr_tail}")
            sys.exit(deploy_res.returncode if deploy_res.returncode != 0 else 1)
    except FileNotFoundError:
        print("[ERROR] Firebase CLI ('firebase') not found on system PATH. Deployment aborted.")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected exception during Firebase deployment: {e}")
        sys.exit(1)
        
    print("\n" + "="*50)
    print(" PROCESS COMPLETED SUCCESSFULLY")
    print("="*50)

if __name__ == "__main__":
    main()
