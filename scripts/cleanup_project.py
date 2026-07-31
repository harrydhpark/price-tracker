import os
import shutil
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def cleanup():
    print("=== Starting Project Cleanup ===")
    
    # 1. Delete debug HTML and TXT files
    debug_files = [
        os.path.join(ROOT, "currys_cards_debug.txt")
    ] + glob.glob(os.path.join(ROOT, "data", "debug_*.html"))
    
    deleted_count = 0
    for file_path in debug_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[DELETED] {os.path.basename(file_path)}")
                deleted_count += 1
            except Exception as e:
                print(f"[ERROR DELETING] {file_path}: {e}")
    print(f"Total debug files deleted: {deleted_count}")

    # 2. Move test scripts to scripts/archive/
    archive_dir = os.path.join(ROOT, "scripts", "archive")
    os.makedirs(archive_dir, exist_ok=True)
    
    test_scripts = [
        'debug_currys_text.py',
        'inspect_debug_text.py',
        'inspect_greece_debug.py',
        'inspect_kotsovolos_led.py',
        'inspect_public_dom.py',
        'inspect_public_search.py',
        'search_public_tags.py',
        'test_all_greece_urls.py',
        'test_currys_parser.py',
        'test_greece_sites.py',
        'test_stealthy_greece.py'
    ]
    
    moved_scripts = 0
    for script_name in test_scripts:
        src = os.path.join(ROOT, "scripts", script_name)
        dst = os.path.join(archive_dir, script_name)
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print(f"[MOVED SCRIPT] {script_name} -> scripts/archive/")
                moved_scripts += 1
            except Exception as e:
                print(f"[ERROR MOVING SCRIPT] {script_name}: {e}")
    print(f"Total test scripts moved to archive: {moved_scripts}")

    # 3. Organize past excel files in data/ into History / History_EU
    data_dir = os.path.join(ROOT, "data")
    
    # Swiss past files: Swiss_ATA_Comparison_2026_0720 ~ 0725, price tracker_swiss_2026 0720 ~ 0725
    swiss_past_files = [
        "Swiss_ATA_Comparison_2026_0720.xlsx",
        "Swiss_ATA_Comparison_2026_0722.xlsx",
        "Swiss_ATA_Comparison_2026_0724.xlsx",
        "Swiss_ATA_Comparison_2026_0725.xlsx",
        "price tracker_swiss_2026 0720_v1.xlsx",
        "price tracker_swiss_2026 0722_v1.xlsx",
        "price tracker_swiss_2026 0724_v1.xlsx",
        "price tracker_swiss_2026 0725_v1.xlsx"
    ]
    
    for f in swiss_past_files:
        src = os.path.join(data_dir, f)
        if os.path.exists(src):
            date_part = None
            if "2026_07" in f:
                parts = f.split("2026_")
                if len(parts) > 1:
                    date_part = "2026 " + parts[1][:4]
            elif "2026 07" in f:
                parts = f.split("2026 ")
                if len(parts) > 1:
                    date_part = "2026 " + parts[1][:4]
            
            if date_part:
                target_hist_dir = os.path.join(ROOT, "History", date_part)
                os.makedirs(target_hist_dir, exist_ok=True)
                dst = os.path.join(target_hist_dir, f)
                try:
                    shutil.move(src, dst)
                    print(f"[MOVED HIST] {f} -> History/{date_part}/")
                except Exception as e:
                    print(f"[ERROR MOVING HIST] {f}: {e}")

    # EU past files: price tracker_EU_2026 0708_v1.xlsx ~ 0726_v1.xlsx
    eu_past_files = [
        "price tracker_EU_2026 0708_v1.xlsx",
        "price tracker_EU_2026 0723_v1.xlsx",
        "price tracker_EU_2026 0725_v1.xlsx",
        "price tracker_EU_2026 0726_v1.xlsx"
    ]
    
    for f in eu_past_files:
        src = os.path.join(data_dir, f)
        if os.path.exists(src):
            date_part = None
            if "2026 " in f:
                parts = f.split("2026 ")
                if len(parts) > 1:
                    date_part = "2026 " + parts[1][:4]
            
            if date_part:
                target_hist_dir = os.path.join(ROOT, "History_EU", date_part)
                os.makedirs(target_hist_dir, exist_ok=True)
                dst = os.path.join(target_hist_dir, f)
                try:
                    shutil.move(src, dst)
                    print(f"[MOVED HIST EU] {f} -> History_EU/{date_part}/")
                except Exception as e:
                    print(f"[ERROR MOVING HIST EU] {f}: {e}")

    # 4. Rename EU-price-tracker to EU-price-tracker_backup
    eu_tracker_dir = os.path.join(ROOT, "EU-price-tracker")
    eu_backup_dir = os.path.join(ROOT, "EU-price-tracker_backup")
    if os.path.exists(eu_tracker_dir) and not os.path.exists(eu_backup_dir):
        try:
            os.rename(eu_tracker_dir, eu_backup_dir)
            print(f"[RENAMED] EU-price-tracker -> EU-price-tracker_backup")
        except Exception as e:
            print(f"[ERROR RENAMING] EU-price-tracker: {e}")

    print("=== Project Cleanup Finished Successfully ===")

if __name__ == "__main__":
    cleanup()
