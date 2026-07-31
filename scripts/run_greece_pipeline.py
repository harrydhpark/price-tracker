# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import glob
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

def run_script(script_name):
    print(f"\n==========================================")
    print(f"🚀 Running: {script_name}")
    print(f"==========================================")
    cmd = [sys.executable, os.path.join("scripts", script_name)]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    print(res.stdout)
    if res.stderr and "Error" in res.stderr:
        print("⚠️ Stderr:", res.stderr)
    return res.returncode

def main():
    print("--------------------------------------------------")
    print("🇬🇷 Starting Greece Price Tracker & Dashboard Pipeline")
    print("--------------------------------------------------")
    
    # 1. Scrape Kotsovolos & Public
    run_script("scrape_kotsovolos.py")
    run_script("scrape_public.py")
    
    # 2. Sync to Excel
    run_script("sync_greece_retailers.py")
    
    # 3. Generate Dashboard HTML
    run_script("generate_greece_dashboard.py")
    
    print("\n--------------------------------------------------")
    print("✅ Greece Price Tracker Pipeline Completed Successfully!")
    print("--------------------------------------------------")

if __name__ == '__main__':
    main()
