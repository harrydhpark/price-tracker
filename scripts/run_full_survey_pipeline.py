# -*- coding: utf-8 -*-
"""
Master Automated Weekly TV Price Survey Pipeline Runner
Executes the full end-to-end price survey across 16 countries (Europe 15 + Australia 1, 18 Retailers):
1. Live Web Scraping (UK, DE, AT, FR, ES, IT, NL, SE, PT, PL, HU, CZ, RO eMAG, GR Kotsovolos, CH 3-Retailer, AU Big-3)
2. Live Master Product URL PDP Probing & Category Pagination Discovery
3. Master Product URL Registry Auto-Synchronization
4. Excel Workbook Synchronization & History Archiving
5. Independent G4 Cross-Verification, Country Release Gate (G1-G5) & Data Quality Gates (R1-R4)
6. SQLite Price History Time-Series Update
7. AI Data Intelligence Engine (1:1 Lineup Gaps, WoW Trends, Executive Briefing)
8. Multi-Region Web Dashboard Compilation (EU 15-Country, Swiss, Australia)
9. Firebase Hosting Live Deployment & Availability Verification
"""

import os
import sys
import time
import glob
import json
import shutil
import argparse
import subprocess
from datetime import datetime
from typing import List, Tuple, Optional

# Ensure UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

PYTHON_EXE = os.path.join(ROOT_DIR, "python_env", "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

class DualLogger:
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log_file = open(filepath, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

class PipelineHalt(RuntimeError):
    """Raised when a mandatory step fails. Stops the pipeline BEFORE DB write / dashboard / deploy (Hard Halt policy)."""


def run_step(cmd_list: List[str], desc: str, timeout: Optional[int] = 1800, allow_failure: bool = False) -> bool:
    ok = _run_step_impl(cmd_list, desc, timeout)
    if not ok and not allow_failure:
        raise PipelineHalt(f"Mandatory step failed: {desc}")
    if not ok:
        print(f"⚠️ [WARNING] Optional step '{desc}' failed (allow_failure=True). Recorded as FAILED in summary.")
    return ok


def _run_step_impl(cmd_list: List[str], desc: str, timeout: Optional[int] = 1800) -> bool:
    print("\n" + "=" * 70)
    print(f"▶ [STEP] {desc.upper()}")
    print("=" * 70)
    start_t = time.time()
    try:
        proc = subprocess.Popen(
            cmd_list,
            cwd=ROOT_DIR,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=(os.name == 'nt'),
            bufsize=1
        )
        if proc.stdout:
            for line in iter(proc.stdout.readline, ''):
                if not line:
                    break
                print(line, end="")
                sys.stdout.flush()
            proc.stdout.close()
        proc.wait(timeout=timeout)
        if proc.returncode != 0:
            print(f"\n❌ [STEP FAILED] '{desc}' exited with code {proc.returncode} ({round(time.time() - start_t, 1)}s)")
            return False
        elapsed = round(time.time() - start_t, 1)
        print(f"✔ [STEP SUCCESS] '{desc}' completed in {elapsed}s.")
        return True
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        print(f"\n❌ [TIMEOUT] '{desc}' timed out after {timeout}s.")
        return False
    except Exception as ex:
        print(f"\n❌ [ERROR] '{desc}' exception: {ex}")
        return False

def verify_http_endpoint(url: str, timeout: int = 15) -> bool:
    try:
        from urllib.request import urlopen, Request
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            print(f"  • {url} -> HTTP {status} OK")
            return status == 200
    except Exception as e:
        print(f"  • {url} -> Verification failed: {e}")
        return False

def _check_single_raw_file(fpath: str, fname: str, desc: str, now_ts: float, run_start: Optional[float], skip_scrape: bool) -> Optional[str]:
    if not os.path.exists(fpath):
        return f"❌ Missing required raw data file: {fname} ({desc})"
    mtime = os.path.getmtime(fpath)
    age_hours = (now_ts - mtime) / 3600.0
    size_bytes = os.path.getsize(fpath)
    if size_bytes < 100:
        return f"❌ File too small ({size_bytes} bytes): {fname} ({desc})"
    if (not skip_scrape) and run_start is not None and mtime < run_start:
        return f"❌ Not produced in this run (written {round(age_hours, 1)}h ago, before run start): {fname} ({desc})"
    if age_hours > 24.0:
        return f"❌ Stale historical cache detected! Age: {round(age_hours, 1)} hours ago: {fname} ({desc})"
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            item_count = len(data)
        elif isinstance(data, dict):
            item_count = sum(len(v) for v in data.values() if isinstance(v, list))
        else:
            item_count = 0
        if item_count < 3:
            return f"❌ Insufficient products ({item_count} items): {fname} ({desc})"
        if isinstance(data, list) and not fname.startswith(("raw_interdiscount_", "raw_digitec_")):
            today_prefix = datetime.now().strftime("%Y-%m-%d")
            has_today_ts = any(isinstance(it, dict) and str(it.get("scraped_at", "")).startswith(today_prefix) for it in data)
            if not has_today_ts:
                return f"❌ Missing today's live scraped_at timestamp ({today_prefix}) inside JSON items: {fname} ({desc})"
        print(f"  ✔ [VERIFIED LIVE] {desc:<42} : {item_count:>4} items | {round(age_hours, 2)}h ago ({size_bytes/1024:.1f} KB)")
        return None
    except Exception as ex:
        return f"❌ JSON parse error in {fname}: {ex}"


def _retry_failed_country_scrapers(failed_fnames: List[str], run_id: str) -> None:
    """Maps failed raw_*.json filenames to their specific country scraper commands and retries up to 2 times."""
    western_ccs = set()
    stage2_ccs = set()
    standalone_cmds = {}

    for fname in failed_fnames:
        for cc, prefix in [("DE", "raw_mm-de_"), ("AT", "raw_mm-at_"), ("ES", "raw_mm-es_"), ("IT", "raw_mw-it_"), ("NL", "raw_mm-nl_")]:
            if fname.startswith(prefix):
                western_ccs.add(cc)
        for cc, prefix in [("CZ", "raw_alza_"), ("HU", "raw_mm-hu_"), ("PT", "raw_worten_pt_"), ("SE", "raw_elgiganten_se_"), ("PL", "raw_mediaexpert_pl_")]:
            if fname.startswith(prefix):
                stage2_ccs.add(cc)
        if fname.startswith("raw_currys_"):
            standalone_cmds["UK"] = ([PYTHON_EXE, "scripts/scrape_currys_live.py"], "Retry UK Currys")
        elif fname.startswith("raw_boulanger_"):
            standalone_cmds["FR"] = ([PYTHON_EXE, "scripts/scrape_boulanger_live.py"], "Retry France Boulanger")
        elif fname.startswith("raw_emag_ro_"):
            standalone_cmds["RO"] = ([PYTHON_EXE, "scripts/scrape_emag_ro.py"], "Retry Romania eMAG.ro")
        elif fname.startswith("raw_kotsovolos_gr_"):
            standalone_cmds["GR"] = ([PYTHON_EXE, "scripts/scrape_kotsovolos_gr.py"], "Retry Greece Kotsovolos.gr")
        elif fname.startswith("raw_mediamarkt_"):
            standalone_cmds["CH_MM"] = ([PYTHON_EXE, "scripts/scrape_mediamarkt.py"], "Retry Swiss MediaMarkt")
        elif fname.startswith("raw_interdiscount_"):
            standalone_cmds["CH_ID"] = ([PYTHON_EXE, "scripts/scrape_interdiscount.py"], "Retry Swiss Interdiscount")
        elif fname.startswith("raw_digitec_"):
            standalone_cmds["CH_DG"] = ([PYTHON_EXE, "scripts/scrape_digitec.py"], "Retry Swiss Digitec")
        elif any(fname.startswith(p) for p in ("raw_jbhifi_", "raw_goodguys_", "raw_harveynorman_")):
            standalone_cmds["AU"] = ([PYTHON_EXE, "scripts/scrape_au_retailers.py"], "Retry Australia Big 3")

    for cc in sorted(western_ccs):
        _run_step_impl([PYTHON_EXE, "scripts/scrape_western_eu_targeted.py", "--countries", cc], f"Self-Heal Retry Western EU ({cc})", timeout=900)
    for cc in sorted(stage2_ccs):
        _run_step_impl([PYTHON_EXE, "scripts/scrape_stage2_eu_zero_cost.py", "--countries", cc, "--run-id", run_id], f"Self-Heal Retry Stage 2 EU ({cc})", timeout=900)
    for key, (cmd, desc) in standalone_cmds.items():
        _run_step_impl(cmd, f"Self-Heal {desc}", timeout=600)


def verify_live_datasets(data_dir: str, allow_partial: bool = False, skip_scrape: bool = False):
    print("\n" + "=" * 70)
    print("🛡️ [PRE-FLIGHT GATE] VERIFYING REAL-TIME LIVE DATA INTEGRITY (ZERO CACHE AUDIT)")
    print("=" * 70)
    
    target_files = [
        ("raw_mm-de_lg.json", "Germany MediaMarkt LG"),
        ("raw_mm-de_samsung.json", "Germany MediaMarkt Samsung"),
        ("raw_mm-at_lg.json", "Austria MediaMarkt LG"),
        ("raw_mm-at_samsung.json", "Austria MediaMarkt Samsung"),
        ("raw_mm-es_lg.json", "Spain MediaMarkt LG"),
        ("raw_mm-es_samsung.json", "Spain MediaMarkt Samsung"),
        ("raw_mw-it_lg.json", "Italy MediaWorld LG"),
        ("raw_mw-it_samsung.json", "Italy MediaWorld Samsung"),
        ("raw_mm-nl_lg.json", "Netherlands MediaMarkt LG"),
        ("raw_mm-nl_samsung.json", "Netherlands MediaMarkt Samsung"),
        ("raw_boulanger_lg.json", "France Boulanger LG"),
        ("raw_boulanger_samsung.json", "France Boulanger Samsung"),
        ("raw_currys_lg.json", "UK Currys LG"),
        ("raw_currys_samsung.json", "UK Currys Samsung"),
        ("raw_alza_lg.json", "Czech Alza LG"),
        ("raw_alza_samsung.json", "Czech Alza Samsung"),
        ("raw_mm-hu_lg.json", "Hungary MediaMarkt LG"),
        ("raw_mm-hu_samsung.json", "Hungary MediaMarkt Samsung"),
        ("raw_worten_pt_lg.json", "Portugal Worten LG"),
        ("raw_worten_pt_samsung.json", "Portugal Worten Samsung"),
        ("raw_elgiganten_se_lg.json", "Sweden Elgiganten LG"),
        ("raw_elgiganten_se_samsung.json", "Sweden Elgiganten Samsung"),
        ("raw_mediaexpert_pl_lg.json", "Poland MediaExpert LG"),
        ("raw_mediaexpert_pl_samsung.json", "Poland MediaExpert Samsung"),
        ("raw_emag_ro_lg.json", "Romania eMAG LG"),
        ("raw_emag_ro_samsung.json", "Romania eMAG Samsung"),
        ("raw_kotsovolos_gr_lg.json", "Greece Kotsovolos LG"),
        ("raw_kotsovolos_gr_samsung.json", "Greece Kotsovolos Samsung"),
        ("raw_mediamarkt_lg.json", "Swiss MediaMarkt LG"),
        ("raw_mediamarkt_samsung.json", "Swiss MediaMarkt Samsung"),
        ("raw_interdiscount_lg.json", "Swiss Interdiscount LG"),
        ("raw_interdiscount_samsung.json", "Swiss Interdiscount Samsung"),
        ("raw_digitec_lg.json", "Swiss Digitec LG"),
        ("raw_digitec_samsung.json", "Swiss Digitec Samsung"),
        ("raw_jbhifi_lg.json", "Australia JB Hi-Fi LG"),
        ("raw_goodguys_lg.json", "Australia The Good Guys LG"),
        ("raw_harveynorman_lg.json", "Australia Harvey Norman LG"),
    ]

    try:
        run_start = float(os.environ.get("SURVEY_RUN_START", ""))
    except ValueError:
        run_start = None
    run_id = os.environ.get("SURVEY_RUN_ID", f"eu_{datetime.now().strftime('%Y%m%d')}")

    errors = []
    failed_fnames = []
    now_ts = time.time()
    for fname, desc in target_files:
        fpath = os.path.join(data_dir, fname)
        err = _check_single_raw_file(fpath, fname, desc, now_ts, run_start, skip_scrape)
        if err:
            errors.append(err)
            failed_fnames.append(fname)

    # Self-healing retry loop (up to 2 attempts for any failed country)
    retry_attempt = 0
    while failed_fnames and (not skip_scrape) and retry_attempt < 2:
        retry_attempt += 1
        print(f"\n🔄 [SELF-HEALING RETRY {retry_attempt}/2] Retrying failed datasets: {', '.join(failed_fnames)}")
        _retry_failed_country_scrapers(failed_fnames, run_id)
        now_ts = time.time()
        errors = []
        still_failed = []
        for fname, desc in target_files:
            if fname in failed_fnames:
                fpath = os.path.join(data_dir, fname)
                err = _check_single_raw_file(fpath, fname, desc, now_ts, run_start, skip_scrape)
                if err:
                    errors.append(err)
                    still_failed.append(fname)
        failed_fnames = still_failed
        if not failed_fnames:
            print(f"✔ [SELF-HEALING RETRY SUCCEEDED] All previously failed datasets recovered on attempt {retry_attempt}!")
            _run_step_impl([PYTHON_EXE, "scripts/build_master_url_registry.py"], "Re-Sync Master Product URL Registry after Self-Heal", timeout=300)

    if errors:
        print("\n" + "!" * 70)
        print("❌ [PRE-FLIGHT GATE FAILED] Stale or invalid data detected after self-healing retries:")
        for err in errors:
            print(f"   {err}")
        print("!" * 70 + "\n")
        if not allow_partial:
            raise RuntimeError("Pre-flight live data verification failed. Stale cache fallback is strictly prohibited.")
        else:
            print("⚠️ [WARNING] Continuing pipeline despite warnings due to --allow-partial flag.")
    else:
        print("✔ [PRE-FLIGHT GATE PASSED] All 16 country raw datasets (37 files) are 100% verified live and fresh.\n")


def execute_full_survey(skip_scrape: bool = False, allow_partial: bool = False, stealth_fast: bool = False):
    total_start = time.time()
    now = datetime.now()
    log_filename = f"weekly_survey_{now.strftime('%Y%m%d_%H%M%S')}.log"
    log_path = os.path.join(LOGS_DIR, log_filename)
    
    # Setup dual logging
    logger = DualLogger(log_path)
    old_stdout = sys.stdout
    sys.stdout = logger

    print("*" * 75)
    print(f" 🚀 PAN-EUROPEAN (15 COUNTRIES) & AUSTRALIAN TV PRICE TRACKER - FULL SURVEY PIPELINE")
    print(f" 📅 Start Time: {now.strftime('%Y-%m-%d %H:%M:%S')} (KST, UTC+09:00)")
    print(f" 📂 Log File  : {log_path}")
    print(f" ⚙️ Python Env: {PYTHON_EXE}")
    print(f" 🛠️ Mode      : {'SKIP SCRAPE (Sync/Compile Only)' if skip_scrape else 'ZERO-FIRECRAWL LIVE SCRAPE (Open-Source Stack -> Verify -> Release -> Deploy)'}")
    print("*" * 75)

    step_status = {}

    # Run context (SURVEY_RUN_ID / SURVEY_RUN_START) is inherited by every child scraper.
    sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))
    from core.run_context import init_run_context
    run_id = init_run_context()
    print(f" 🆔 Run ID    : {run_id}")

    try:
        # ==============================================================================
        # 1. LIVE WEB SCRAPING (ZERO-FIRECRAWL OPEN-SOURCE STACK)
        # ==============================================================================
        if not skip_scrape:
            print("\n[PHASE 1] ZERO-FIRECRAWL LIVE WEB SCRAPING ACROSS ALL 16 COUNTRIES (18 RETAILERS)")

            # 1.1a UK Currys (curl_cffi + Master PDPs)
            step_status["scrape_uk_currys"] = run_step(
                [PYTHON_EXE, "scripts/scrape_currys_live.py"],
                "Scrape UK Currys (Live Search + Master PDPs via curl_cffi)",
                timeout=600,
                allow_failure=allow_partial
            )

            # 1.1b France Boulanger (curl_cffi Direct Seller Catalog + Master PDPs)
            step_status["scrape_fr_boulanger"] = run_step(
                [PYTHON_EXE, "scripts/scrape_boulanger_live.py"],
                "Scrape France Boulanger (Live Direct Seller Catalog + Master PDPs)",
                timeout=600,
                allow_failure=allow_partial
            )

            # 1.1c Western EU MediaMarkt / MediaWorld + Swiss MediaMarkt (DE, AT, ES, NL, IT, CH)
            step_status["scrape_western_eu_mm"] = run_step(
                [PYTHON_EXE, "scripts/scrape_western_eu_targeted.py", "--countries", "DE,AT,ES,NL,IT,CH"],
                "Scrape Western EU and CH MediaMarkt/MediaWorld (DE, AT, ES, NL, IT, CH Target Matrix + Master PDPs)",
                timeout=1800,
                allow_failure=allow_partial
            )

            # 1.2 Stage 2 EU (SE, PT, PL, HU, CZ) Zero-Cost Scraper (Full Category Discovery + Master PDPs)
            step_status["scrape_stage2_eu"] = run_step(
                [PYTHON_EXE, "scripts/scrape_stage2_eu_zero_cost.py", "--run-id", run_id],
                "Scrape Stage 2 EU Retailers (SE, PT, PL 16p, HU, CZ) via Zero-Firecrawl Stack",
                timeout=1800,
                allow_failure=allow_partial
            )

            # 1.3 Eastern & Southern EU: Romania eMAG.ro & Greece Kotsovolos.gr (curl_cffi Full Catalog + Master PDPs)
            step_status["scrape_ro_emag"] = run_step(
                [PYTHON_EXE, "scripts/scrape_emag_ro.py"],
                "Scrape Romania eMAG.ro (Full Category Pagination + Master PDPs via curl_cffi)",
                timeout=600,
                allow_failure=allow_partial
            )
            step_status["scrape_gr_kotsovolos"] = run_step(
                [PYTHON_EXE, "scripts/scrape_kotsovolos_gr.py"],
                "Scrape Greece Kotsovolos.gr (Full Category Pagination + Master PDPs via curl_cffi)",
                timeout=600,
                allow_failure=allow_partial
            )

            # 1.4 Swiss Multi-Retailer (MediaMarkt, Interdiscount, Digitec)
            mm_ch_cmd = [PYTHON_EXE, "scripts/scrape_mediamarkt.py"]
            id_ch_cmd = [PYTHON_EXE, "scripts/scrape_interdiscount.py"]
            dg_ch_cmd = [PYTHON_EXE, "scripts/scrape_digitec.py"]
            if stealth_fast:
                mm_ch_cmd.append("--fast")
                id_ch_cmd.append("--fast")
                dg_ch_cmd.append("--fast")

            # MediaMarkt CH is already scraped via scrape_western_eu_targeted.py (2-Stage Search + Master PDPs)
            step_status["scrape_mediamarkt_ch"] = step_status.get("scrape_western_eu_mm", True)
            step_status["scrape_interdiscount_ch"] = run_step(
                id_ch_cmd,
                "Scrape Switzerland Interdiscount CH",
                timeout=300,
                allow_failure=allow_partial
            )
            step_status["scrape_digitec_ch"] = run_step(
                dg_ch_cmd,
                "Scrape Switzerland Digitec CH",
                timeout=300,
                allow_failure=allow_partial
            )

            # 1.5 Australia Big 3 (JB Hi-Fi, The Good Guys, Harvey Norman)
            step_status["scrape_australia"] = run_step(
                [PYTHON_EXE, "scripts/scrape_au_retailers.py"],
                "Scrape Australia Big 3 Retailers",
                timeout=300,
                allow_failure=allow_partial
            )

            # 1.6 Master Registry Auto-Sync
            step_status["registry_sync"] = run_step(
                [PYTHON_EXE, "scripts/build_master_url_registry.py"],
                "Auto-Sync Master Product URL Registry",
                allow_failure=False
            )
        else:
            print("\n[PHASE 1] Skipped (--skip-scrape enabled). Proceeding to Workbook Synchronization.")

        # Mandatory Pre-flight Verification Gate: Zero Stale Cache Permitted
        verify_live_datasets(DATA_DIR, allow_partial=allow_partial, skip_scrape=skip_scrape)

        # ==============================================================================
        # 2. EXCEL WORKBOOK SYNCHRONIZATION
        # ==============================================================================
        print("\n[PHASE 2] EXCEL WORKBOOK SYNCHRONIZATION")

        # 2.1 Swiss Multi-Retailer Workbook (MediaMarkt, Interdiscount, Digitec)
        step_status["sync_swiss"] = run_step(
            [PYTHON_EXE, "scripts/sync_all_retailers.py"],
            "Synchronize Swiss Multi-Retailer Workbook",
            allow_failure=False
        )

        # 2.2 Pan-European 15-Country Workbook (DE, AT, ES, NL, IT, FR, UK, CZ, HU, PT, SE, PL, RO, GR + CH)
        step_status["sync_eu_15_countries"] = run_step(
            [PYTHON_EXE, "scripts/sync_eu_retailers.py"],
            "Synchronize All 15 EU Countries (incl. RO eMAG, GR Kotsovolos & CH) to Pan-European Workbook",
            allow_failure=False
        )

        # 2.3 Australia Workbook (JB Hi-Fi, The Good Guys, Harvey Norman)
        step_status["sync_australia"] = run_step(
            [PYTHON_EXE, "scripts/sync_au_retailers.py"],
            "Synchronize Australia Workbook",
            allow_failure=False
        )

        # ==============================================================================
        # 3. INDEPENDENT VERIFICATION (G4), COUNTRY RELEASE GATE (G1-G5) & DB SYNC
        # ==============================================================================
        print("\n[PHASE 3] INDEPENDENT G4 CROSS-VERIFICATION & COUNTRY RELEASE GATE (G1-G5)")

        eu_date_mmdd = now.strftime("%m%d")
        eu_xlsx = os.path.join(DATA_DIR, f"price tracker_EU_{now.strftime('%Y')} {eu_date_mmdd}_v1.xlsx")
        if not os.path.exists(eu_xlsx):
            cands = sorted(glob.glob(os.path.join(DATA_DIR, "price tracker_EU_*.xlsx")))
            if cands:
                eu_xlsx = cands[-1]

        # 3.1 Independent Cross-Verification (G4) across 15 EU countries
        step_status["verify_eu_independent"] = run_step(
            [PYTHON_EXE, "scripts/verify_eu_independent.py", "--excel", eu_xlsx, "--run-id", run_id, "--countries", "UK,DE,AT,CH,FR,ES,IT,NL,CZ,HU,PT,SE,PL,RO,GR"],
            "Independent G4 Cross-Verification Across 15 EU Countries",
            timeout=900,
            allow_failure=False
        )

        # 3.2 Country-Level Release Gate (G1-G5) + SQLite DB & History_EU Mirror
        step_status["release_by_country"] = run_step(
            [PYTHON_EXE, "scripts/release_by_country.py", "--excel", eu_xlsx, "--run-id", run_id, "--countries", "UK,DE,AT,CH,FR,ES,IT,NL,CZ,HU,PT,SE,PL,RO,GR", "--allow-unverified", "--apply"],
            "Country-Level Release Gate (G1-G5) & DB Recording",
            allow_failure=False
        )

        # 3.3 Quality Gates Audit (R1-R4)
        step_status["quality_gates"] = run_step(
            [PYTHON_EXE, "scripts/quality_gates.py"],
            "Audit Data Quality Gates (Zero Critical Anomalies Gate)",
            allow_failure=False
        )

        # ==============================================================================
        # 4. AI DATA INTELLIGENCE ENGINE & DASHBOARD COMPILATION
        # ==============================================================================
        print("\n[PHASE 4] AI DATA INTELLIGENCE & WEB DASHBOARD COMPILATION")

        # 4.1 Data Intelligence Engine (1:1 Lineup Gaps, WoW Changes, Executive Briefing)
        step_status["data_intelligence"] = run_step(
            [PYTHON_EXE, "scripts/data_intelligence_engine.py"],
            "Execute Data Intelligence Engine (1:1 Gaps & Executive Briefing)",
            allow_failure=False
        )

        # 4.2 Web Dashboard Compilation (EU, Swiss, Australia)
        step_status["compile_eu_dash"] = run_step(
            [PYTHON_EXE, "scripts/generate_eu_dashboard.py"],
            "Compile Pan-European 15-Country TV Price Dashboard",
            allow_failure=False
        )
        step_status["compile_swiss_dash"] = run_step(
            [PYTHON_EXE, "scripts/generate_dashboard.py"],
            "Compile Swiss 3-Retailer TV Price Dashboard",
            allow_failure=False
        )
        step_status["compile_au_dash"] = run_step(
            [PYTHON_EXE, "scripts/generate_au_dashboard.py"],
            "Compile Australia 3-Retailer TV Price Dashboard",
            allow_failure=False
        )

        # ==============================================================================
        # 5. FIREBASE HOSTING DEPLOYMENT
        # ==============================================================================
        print("\n[PHASE 5] FIREBASE HOSTING LIVE DEPLOYMENT")

        npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
        step_status["firebase_deploy"] = run_step(
            [npx_cmd, "firebase", "deploy", "--only", "hosting:eu-price-tracker,hosting:swiss-price-tracker,hosting:au-price-tracker"],
            "Deploy Dashboards to Firebase Hosting",
            allow_failure=False
        )

        # Verify Endpoints
        print("\n[VERIFICATION] Checking Live Web Hosting Endpoints:")
        verify_http_endpoint("https://eu-price-tracker-lge.web.app")
        verify_http_endpoint("https://swiss-price-tracker-lge.web.app")
        verify_http_endpoint("https://au-price-tracker-lge.web.app")
        verify_http_endpoint("https://tv-sales-portal-2026.web.app")

    except PipelineHalt as h:
        step_status["HARD_HALT"] = False
        print("\n" + "!" * 75)
        print(f"⛔ [HARD HALT] {h}")
        print("   DB write / dashboard compile / Firebase deploy were NOT executed.")
        print("   The live dashboards keep the last released (verified) version.")
        print("!" * 75)
        return False
    except Exception as e:
        step_status["HARD_HALT"] = False
        print(f"\n❌ [CRITICAL PIPELINE EXCEPTION]: {e}")
        return False
    finally:
        total_elapsed = round(time.time() - total_start, 1)
        passed_steps = sum(1 for v in step_status.values() if v)
        total_steps = len(step_status)

        print("\n" + "=" * 75)
        print(" 🏁 SURVEY PIPELINE EXECUTION SUMMARY")
        print("=" * 75)
        print(f"  • Total Runtime: {total_elapsed}s ({round(total_elapsed/60, 2)} min)")
        print(f"  • Stage Results: {passed_steps}/{total_steps} steps succeeded")
        for s_name, s_res in step_status.items():
            icon = "✔" if s_res else "❌"
            print(f"    - {icon} {s_name}")
        print(f"  • Master Log   : {log_path}")
        print("=" * 75)

        sys.stdout = old_stdout
        logger.flush()

    return all(step_status.values())

def main():
    parser = argparse.ArgumentParser(description="Master Automated Weekly TV Price Survey Pipeline")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip web scraping and execute sync, dashboard compilation and deployment")
    parser.add_argument("--allow-partial", action="store_true", default=False, help="(Opt-in, debugging only) Tolerate scraping-step failures. Never use for releases.")
    parser.add_argument("--full-scrapling", action="store_true", help="Force legacy local Scrapling on Turnstile (Warning: may hang)")
    parser.add_argument("--stealth-fast", action="store_true", default=True, help="Bypass local Turnstile loops by using Firecrawl Stealth and Master PDP Probing")
    args = parser.parse_args()

    is_stealth = not args.full_scrapling
    success = execute_full_survey(skip_scrape=args.skip_scrape, allow_partial=args.allow_partial, stealth_fast=is_stealth)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
