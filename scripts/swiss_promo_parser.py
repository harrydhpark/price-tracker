"""
Swiss Promotion and Cashback Parser Module
Uses promo_classifier under the hood to ensure consistent separation of:
- Was / Original Prices
- Cashback
- Price Promotions
- Non-Price Promotions
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from promo_classifier import classify_promotions

def clean_swiss_promo_text(promo, brand, year, model_code):
    if not promo or str(promo).strip() in ["", "None", "0"]:
        return "None"
        
    orig, cb, price_p, non_price_p = classify_promotions(
        promo_raw=promo,
        brand=brand,
        year=year,
        model_code=model_code,
        currency="CHF"
    )
    
    parts = []
    if price_p != "None":
        parts.append(price_p)
    if non_price_p != "None":
        parts.append(non_price_p)
        
    return "; ".join(parts) if parts else "None"

def parse_swiss_promo_and_cashback(promo_raw, title_raw, brand, year, model_code, size, price, original_price=0.0):
    """
    Parses raw promotion badges, descriptions, and titles to extract:
    1. cashback: Numeric CHF cashback value (e.g. 200, 500, 1000) or 0
    2. promo: Clean, standardized promotion description (Free SoundSuite, Bundle discount, etc.)
       Excludes was CHF prices and marketing labels.
    """
    orig, cb, price_p, non_price_p = classify_promotions(
        promo_raw=promo_raw,
        title_raw=title_raw,
        brand=brand,
        year=year,
        model_code=model_code,
        price=price,
        currency="CHF",
        existing_original_price=original_price
    )
    
    parts = []
    if price_p != "None":
        parts.append(price_p)
    if non_price_p != "None":
        parts.append(non_price_p)
        
    promo_text = "; ".join(parts) if parts else "None"
    return cb, promo_text

def parse_swiss_promo_details(promo_raw, title_raw, brand, year, model_code, size, price, original_price=0.0):
    """
    Returns full (orig_price, cashback_val, price_promo, non_price_promo) tuple.
    """
    return classify_promotions(
        promo_raw=promo_raw,
        title_raw=title_raw,
        brand=brand,
        year=year,
        model_code=model_code,
        price=price,
        currency="CHF",
        existing_original_price=original_price
    )
