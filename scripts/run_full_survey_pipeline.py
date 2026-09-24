# -*- coding: utf-8 -*-
"""
Master Automated Weekly TV Price Survey Pipeline Runner
Executes the full end-to-end price survey across 12 countries (Europe 11 + Australia 1):
1. Live Web Scraping (Western EU, UK, CZ, GR, HU, CH, AU)
2. Live Master Product URL PDP Probing
3. Master Product URL Registry Auto-Synchronization
4. Excel Workbook Synchronization & History Archiving
5. Data Quality Gates (R1-R4) & Price Anomaly Audit
6. SQLite Price History Time-Series Update
7. AI Data Intelligence Engine (1:1 Lineup Gaps, WoW Trends, Executive Briefing)
8. Multi-Region Web Dashboard Compilation (EU, Swiss, Australia)
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

def run_step(cmd_list: List[str], desc: str, timeout: Optional[int] = 1800, allow_failure: bool = False) -> bool:
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
            if not allow_failure:
                return False
            print(f"⚠️ [WARNING] Step failed but allow_failure=True. Continuing pipeline...")
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
    print(f" 🚀 PAN-EUROPEAN & AUSTRALIAN TV PRICE TRACKER - FULL SURVEY PIPELINE")
    print(f" 📅 Start Time: {now.strftime('%Y-%m-%d %H:%M:%S')} (KST, UTC+09:00)")
    print(f" 📂 Log File  : {log_path}")
    print(f" ⚙️ Python Env: {PYTHON_EXE}")
    print(f" 🛠️ Mode      : {'SKIP SCRAPE (Sync/Compile Only)' if skip_scrape else ('STEALTH-FAST (Firecrawl & Master Probe)' if stealth_fast else 'FULL (Scrape -> Sync -> Deploy)')}")
    print("*" * 75)

    step_status = {}

    try:
        # ==============================================================================
        # 1. LIVE WEB SCRAPING & MASTER PROBE
        # ==============================================================================
        if not skip_scrape:
            print("\n[PHASE 1] LIVE WEB SCRAPING ACROSS ALL 12 COUNTRIES")

            # 1.1 Western EU (DE, AT, ES, NL, IT, UK) Stealthy Scraper
            if not stealth_fast:
                step_status["scrape_western_eu"] = run_step(
                    [PYTHON_EXE, "scripts/scrape_western_eu.py"],
                    "Scrape Western European Retailers (DE, AT, ES, NL, IT, UK)",
                    timeout=300,
                    allow_failure=True
                )
            else:
                print("⚡ [--stealth-fast active] Skipping local Western EU Scrapling scraper; delegating to Firecrawl Stealth & Master PDP Probe.")

            # 1.2 Western EU Targeted Series Search (Firecrawl Stealth)
            step_status["scrape_western_eu_targeted"] = run_step(
                [PYTHON_EXE, "scripts/scrape_western_eu_targeted.py"],
                "Scrape Targeted Series Search for Western EU & France (Fnac/Darty)",
                allow_failure=allow_partial
            )

            # 1.3 UK Currys Precision Scraper
            step_status["scrape_currys"] = run_step(
                [PYTHON_EXE, "scripts/scrape_currys_live.py"],
                "Scrape UK Currys Precision TV Catalog",
                allow_failure=allow_partial
            )

            # 1.4 Czech Republic Alza
            step_status["scrape_alza"] = run_step(
                [PYTHON_EXE, "scripts/scrape_alza.py"],
                "Scrape Czech Republic (Alza.cz) 12-Page Catalog",
                allow_failure=allow_partial
            )

            # 1.5 Greece Public.gr Multi-Query Scraper
            step_status["scrape_public_gr"] = run_step(
                [PYTHON_EXE, "scripts/scrape_public_gr.py"],
                "Scrape Greece (Public.gr) 59-Query Catalog",
                timeout=360,
                allow_failure=allow_partial
            )

            # 1.6 Hungary MediaMarkt Scraper
            hu_cmd = [PYTHON_EXE, "scripts/scrape_and_sync_hungary.py"]
            if stealth_fast:
                hu_cmd.append("--fast")
            step_status["scrape_hungary"] = run_step(
                hu_cmd,
                "Scrape Hungary (MediaMarkt HU) Catalog",
                timeout=180,
                allow_failure=allow_partial
            )

            # 1.7 Swiss Multi-Retailer (MediaMarkt, Interdiscount, Digitec)
            mm_ch_cmd = [PYTHON_EXE, "scripts/scrape_mediamarkt.py"]
            id_ch_cmd = [PYTHON_EXE, "scripts/scrape_interdiscount.py"]
            dg_ch_cmd = [PYTHON_EXE, "scripts/scrape_digitec.py"]
            if stealth_fast:
                mm_ch_cmd.append("--fast")
                id_ch_cmd.append("--fast")
                dg_ch_cmd.append("--fast")

            step_status["scrape_mediamarkt_ch"] = run_step(
                mm_ch_cmd,
                "Scrape Switzerland MediaMarkt CH",
                timeout=180,
                allow_failure=allow_partial
            )
            step_status["scrape_interdiscount_ch"] = run_step(
                id_ch_cmd,
                "Scrape Switzerland Interdiscount CH",
                timeout=180,
                allow_failure=allow_partial
            )
            step_status["scrape_digitec_ch"] = run_step(
                dg_ch_cmd,
                "Scrape Switzerland Digitec CH",
                timeout=180,
                allow_failure=allow_partial
            )

            # 1.8 Australia Big 3 (JB Hi-Fi, The Good Guys, Harvey Norman)
            step_status["scrape_australia"] = run_step(
                [PYTHON_EXE, "scripts/scrape_au_retailers.py"],
                "Scrape Australia Big 3 Retailers",
                timeout=240,
                allow_failure=allow_partial
            )

            # 1.9 Direct Live PDP Probing for Master URL Continuity
            step_status["pdp_probe"] = run_step(
                [PYTHON_EXE, "scripts/live_pdp_probe.py"],
                "Direct Live PDP Probing for Master Product URLs",
                allow_failure=True
            )

            # 1.10 Master Registry Auto-Sync
            step_status["registry_sync"] = run_step(
                [PYTHON_EXE, "scripts/build_master_url_registry.py"],
                "Auto-Sync Master Product URL Registry",
                allow_failure=False
            )
        else:
            print("\n[PHASE 1] Skipped (--skip-scrape enabled). Proceeding to Workbook Synchronization.")

        # ==============================================================================
        # 2. EXCEL WORKBOOK SYNCHRONIZATION & ARCHIVING
        # ==============================================================================
        print("\n[PHASE 2] EXCEL WORKBOOK SYNCHRONIZATION & HISTORY BACKUP")

        # 2.1 Swiss Multi-Retailer Workbook (MediaMarkt, Interdiscount, Digitec)
        step_status["sync_swiss"] = run_step(
            [PYTHON_EXE, "scripts/sync_all_retailers.py"],
            "Synchronize Swiss Multi-Retailer Workbook & History",
            allow_failure=False
        )

        # 2.2 Western EU & DACH Workbook (DE, AT, UK, ES, IT, NL, FR, CH)
        step_status["sync_western_eu"] = run_step(
            [PYTHON_EXE, "scripts/sync_eu_retailers.py"],
            "Synchronize Western EU & DACH Retailers to Pan-European Workbook",
            allow_failure=False
        )

        # 2.3 Eastern EU Sync (CZ Alza, GR Public, HU MediaMarkt)
        step_status["sync_eastern_eu"] = run_step(
            [PYTHON_EXE, "scripts/sync_eastern_eu.py"],
            "Synchronize Eastern EU Retailers (CZ, GR, HU) to Pan-European Workbook",
            allow_failure=False
        )

        # 2.4 Australia Workbook (JB Hi-Fi, The Good Guys, Harvey Norman)
        step_status["sync_australia"] = run_step(
            [PYTHON_EXE, "scripts/sync_au_retailers.py"],
            "Synchronize Australia Workbook & History",
            allow_failure=False
        )

        # 2.5 New EU Retailers Sync (PL MediaExpert, PT Worten, RO Altex, SE Elgiganten)
        step_status["sync_new_eu"] = run_step(
            [PYTHON_EXE, "scripts/sync_new_eu_retailers.py"],
            "Synchronize New EU Retailers (PL, PT, RO, SE) to Pan-European Workbook",
            allow_failure=False
        )

        # ==============================================================================
        # 3. QUALITY GATES & TIME-SERIES DB
        # ==============================================================================
        print("\n[PHASE 3] QUALITY GATES AUDIT & TIME-SERIES DB RECORDING")

        # 3.1 Quality Gates Audit (R1-R4)
        step_status["quality_gates"] = run_step(
            [PYTHON_EXE, "scripts/quality_gates.py"],
            "Audit Data Quality Gates (Zero Critical Anomalies Gate)",
            allow_failure=False
        )

        # 3.2 Ingest Workbooks into SQLite price_history.db
        step_status["price_history"] = run_step(
            [PYTHON_EXE, "scripts/orchestrator.py", "--db-sync"],
            "Record All Survey Workbooks into price_history.db",
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
            "Compile Pan-European 11-Country TV Price Dashboard",
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

    except Exception as e:
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
    parser.add_argument("--allow-partial", action="store_true", default=True, help="Tolerate minor scraping failures without terminating pipeline")
    parser.add_argument("--full-scrapling", action="store_true", help="Force legacy local Scrapling on Turnstile (Warning: may hang)")
    parser.add_argument("--stealth-fast", action="store_true", default=True, help="Bypass local Turnstile loops by using Firecrawl Stealth and Master PDP Probing")
    args = parser.parse_args()

    is_stealth = not args.full_scrapling
    success = execute_full_survey(skip_scrape=args.skip_scrape, allow_partial=args.allow_partial, stealth_fast=is_stealth)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
