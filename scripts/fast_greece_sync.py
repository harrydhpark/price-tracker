# -*- coding: utf-8 -*-
import sys
import os
import json
import re
import subprocess

sys.stdout.reconfigure(encoding='utf-8')

def sync_mcp_output(mcp_output_path):
    print(f"[FAST SYNC] Processing MCP output file: {mcp_output_path}")
    with open(mcp_output_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    json_str = ""
    for line in lines:
        line_s = line.strip()
        if line_s.startswith('"{\\"kotsovolos_samsung') or line_s.startswith('"{') or line_s.startswith('{'):
            json_str = line_s
            break
            
    if json_str.startswith('"') and json_str.endswith('"'):
        json_str = json.loads(json_str) # Unquote inner JSON string
        
    data = json.loads(json_str)
    
    k_sam = data.get("kotsovolos_samsung", [])
    k_lg = data.get("kotsovolos_lg", [])
    p_sam = data.get("public_samsung", [])
    p_lg = data.get("public_lg", [])
    
    print(f"\n==========================================")
    print(f"🇬🇷 Extracted Product Counts:")
    print(f"  ➔ Kotsovolos Samsung: {len(k_sam)} items")
    print(f"  ➔ Kotsovolos LG: {len(k_lg)} items")
    print(f"  ➔ Public Samsung: {len(p_sam)} items")
    print(f"  ➔ Public LG: {len(p_lg)} items")
    print(f"==========================================\n")
    
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    with open(os.path.join(data_dir, "raw_kotsovolos_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(k_sam, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(data_dir, "raw_kotsovolos_lg.json"), "w", encoding="utf-8") as f:
        json.dump(k_lg, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(data_dir, "raw_public_samsung.json"), "w", encoding="utf-8") as f:
        json.dump(p_sam, f, ensure_ascii=False, indent=2)
        
    with open(os.path.join(data_dir, "raw_public_lg.json"), "w", encoding="utf-8") as f:
        json.dump(p_lg, f, ensure_ascii=False, indent=2)

    # Run sync to Excel
    print("➔ Running sync_greece_retailers.py...")
    res1 = subprocess.run([sys.executable, "scripts/sync_greece_retailers.py"], capture_output=True, text=True, encoding='utf-8')
    print(res1.stdout)
    
    # Run generate dashboard
    print("➔ Running generate_greece_dashboard.py...")
    res2 = subprocess.run([sys.executable, "scripts/generate_greece_dashboard.py"], capture_output=True, text=True, encoding='utf-8')
    print(res2.stdout)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sync_mcp_output(sys.argv[1])
    else:
        mcp_path = r"C:\Users\harry.park\.gemini\antigravity\brain\9f486970-3247-4b17-8056-f2d1733fce4d\.system_generated\steps\185\output.txt"
        sync_mcp_output(mcp_path)
