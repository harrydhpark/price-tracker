# -*- coding: utf-8 -*-
"""
Region and Retailer Plugin Manager
Auto-discovers and manages country/retailer configurations from config/regions/
"""

import os
import json
import glob
from typing import Dict, List, Any, Optional

CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "regions"))

def get_all_regions(include_templates: bool = False) -> Dict[str, Dict[str, Any]]:
    """Discovers and loads all region configuration JSON files."""
    regions = {}
    pattern = os.path.join(CONFIG_DIR, "*.json")
    for fp in glob.glob(pattern):
        fn = os.path.basename(fp)
        if not include_templates and "template" in fn.lower():
            continue
        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
                r_id = data.get("region_id")
                if r_id:
                    regions[r_id] = data
        except Exception as e:
            print(f"[WARN] Error loading region config {fp}: {e}")
    return regions

def get_region(region_id: str) -> Optional[Dict[str, Any]]:
    """Returns configuration for a specific region."""
    regions = get_all_regions(include_templates=True)
    return regions.get(region_id)

def get_all_countries() -> Dict[str, Dict[str, Any]]:
    """Returns a dictionary of all supported countries keyed by country code (e.g. 'DE', 'CH')."""
    countries = {}
    for r_id, r_data in get_all_regions().items():
        for c in r_data.get("countries", []):
            code = c.get("code")
            if code:
                c_copy = dict(c)
                c_copy["region_id"] = r_id
                c_copy["pairs_config"] = r_data.get("pairs_config", {})
                countries[code] = c_copy
    return countries

def get_rates_to_eur() -> Dict[str, float]:
    """Extracts currency exchange rates to EUR from active regions."""
    rates = {"EUR": 1.0}
    for c_code, c_data in get_all_countries().items():
        for ret in c_data.get("retailers", []):
            curr = ret.get("currency", "EUR").upper()
            rate = ret.get("rate_to_eur", 1.0)
            rates[curr] = float(rate)
    return rates

def get_pairs_config_for_country(country_code: str) -> Dict[str, List[Dict[str, Any]]]:
    """Returns 1:1 LG vs Samsung pairing config for a given country code."""
    countries = get_all_countries()
    c = countries.get(country_code.upper())
    if c and "pairs_config" in c:
        return c["pairs_config"]
    # Fallback to DACH default
    dach = get_region("dach")
    return dach.get("pairs_config", {}) if dach else {}

if __name__ == "__main__":
    regs = get_all_regions()
    print(f"Discovered {len(regs)} active regions: {list(regs.keys())}")
    cnts = get_all_countries()
    print(f"Total supported countries ({len(cnts)}): {list(cnts.keys())}")
    print(f"Exchange rates to EUR: {get_rates_to_eur()}")
