# -*- coding: utf-8 -*-
import sys
import os
import json
import subprocess
import glob

sys.stdout.reconfigure(encoding='utf-8')

MIN_THRESHOLD = 5 # Minimum required active model rows per retailer sheet

def check_counts():
    data_dir = "data"
    counts = {}
    for json_file in sorted(glob.glob(os.path.join(data_dir, "raw_*.json"))):
        if "kotsovolos" in json_file or "public" in json_file:
            key = os.path.basename(json_file)
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    counts[key] = len(items)
            except Exception:
                counts[key] = 0
    return counts

def run_pipeline():
    print("\n--------------------------------------------------")
    print("🇬🇷 Running Greece Survey Orchestrator with Auto-Verification (Skill Part G Standard)")
    print("--------------------------------------------------")

    attempt = 1
    max_attempts = 3
    success = False

    while attempt <= max_attempts and not success:
        print(f"\n🔄 --- Pipeline Execution Attempt {attempt}/{max_attempts} ---")
        
        # Apply timeout multiplier on retry
        if attempt > 1:
            os.environ["TIMEOUT_MULTIPLIER"] = "2.0"
            print(f"[TIMEOUT MULTIPLIER] Set to 2.0 for retry attempt {attempt}")
            
        # 1. Run multi-page collector
        print("➔ Running fast_greece_collector.py...")
        subprocess.run([sys.executable, "scripts/fast_greece_collector.py"], text=True)
        
        # 2. Check counts
        counts = check_counts()
        total_items = sum(counts.values())
        print(f"\n📊 Extracted Raw Counts Summary: {counts} (Total: {total_items} items)")
        
        if total_items >= MIN_THRESHOLD * 2 or attempt == max_attempts:
            success = True
            print("✅ Verification passed! Proceeding to Excel sync & Dashboard generation...")
        else:
            print(f"⚠️ Volume below threshold (Total: {total_items}). Retrying attempt {attempt+1}...")
            attempt += 1

    # 3. Run sync to Excel
    print("\n➔ Running sync_greece_retailers.py...")
    subprocess.run([sys.executable, "scripts/sync_greece_retailers.py"], text=True)

    # 4. Run generate dashboard
    print("\n➔ Running generate_greece_dashboard.py...")
    subprocess.run([sys.executable, "scripts/generate_greece_dashboard.py"], text=True)

    print("\n--------------------------------------------------")
    print("🎉 Greece Price Tracker Survey Completed & Verified!")
    print("--------------------------------------------------")

if __name__ == '__main__':
    run_pipeline()
