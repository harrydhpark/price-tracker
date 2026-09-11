import re

def clean_swiss_promo_text(promo, brand, year, model_code):
    if not promo or str(promo).strip() in ["", "None", "0"]:
        return "None"
        
    p_str = str(promo).strip()
    promo_upper = p_str.upper()
    
    # 1. Cashback und oder 26% Rabatt auf Soundbar QS700F
    if "CASHBACK UND ODER 26%" in promo_upper or "CASHBACK AND/OR 26% OFF" in promo_upper:
        return "Samsung Cashback and/or 26% Off Soundbar QS700F"
        
    # 2. Gratis Music Studio 5
    if "MUSIC STUDIO 5" in promo_upper or "HW-LS50H" in promo_upper:
        return "Free Music Studio 5 Soundbar (HW-LS50H/EN)"
        
    # 3. mit kostenlosem Zusatzprodukt
    if "ZUSATZPRODUKT" in promo_upper or "WITH FREE PROMOTIONAL PRODUCT" in promo_upper:
        return "Free Promotional Product (Sound Device)"
        
    # 4. Restposten / Outlet
    if "RESTPOSTEN" in promo_upper:
        return "Clearance (Restposten)"
    if "OUTLET" in promo_upper:
        return "Outlet (Clearance)"
        
    # 5. SoundSuite / Soundbar (LG 2026)
    if "SOUNDSUITE" in promo_upper or "SOUNDBAR DAZU" in promo_upper or "GRATIS SOUNDBAR" in promo_upper:
        return "Free SoundSuite/Soundbar with LG OLED TV 2026 Purchase"
        
    # 6. Sound Device geschenkt
    if "SOUND DEVICE GESCHENKT" in promo_upper:
        return "Free Sound Device with 2026 TV Purchase"
        
    # 7. Aus unserer Werbung / Weekly Ad
    if "WERBUNG" in promo_upper or "WEEKLY AD" in promo_upper:
        return "Featured in Weekly Ad (Aus unserer Werbung)"
        
    # 8. Online Only
    if "ONLINE ONLY" in promo_upper or "ONLINE-ONLY" in promo_upper:
        return "Online Only"
        
    # 9. Sale / statt CHF
    if "STATT" in promo_upper or "WAS CHF" in promo_upper or "SALE" in promo_upper:
        pct_match = re.search(r'(\d+)\s*%', p_str)
        was_match = re.search(r'(?:was|statt)\s*(?:chf)?\s*([\d’\x27\x60,.]+)', p_str, re.IGNORECASE)
        pct = pct_match.group(1) if pct_match else None
        was_val = was_match.group(1).replace("’", "").replace("'", "").replace("`", "").strip() if was_match else None
        if was_val and (was_val.endswith(".") or was_val.endswith(",")):
            was_val = was_val[:-1]
            
        if pct and was_val:
            return f"Sale {pct}%; was CHF {was_val}"
        elif was_val:
            return f"was CHF {was_val}"
        elif pct:
            return f"Sale {pct}%"
            
    return p_str

def parse_swiss_promo_and_cashback(promo_raw, title_raw, brand, year, model_code, size, price):
    """
    Parses raw promotion badges, descriptions, and titles to extract:
    1. cashback: Numeric CHF cashback value (e.g. 200, 500, 1000) or 0
    2. promo: Clean, standardized promotion description (e.g. 'Free SoundSuite/Soundbar Bundle', 'Clearance (Restposten)', 'None')
    """
    combined_text = f"{promo_raw or ''} {title_raw or ''}".strip()
    combined_upper = combined_text.upper()
    code_upper = (model_code or "").upper()
    brand_upper = (brand or "").upper()
    
    cashback_val = 0
    promo_text = "None"
    
    # 1. Cashback amount extraction (CHF)
    # Match patterns like "Cashback 500.–", "Cashback 300.-", "Cashback bis zu 500 CHF", "200 CHF Cashback", etc.
    cb_match = re.search(r'(?:Cashback|Cash\s*Back|Rückvergütung|Reembolso|Rimborso)\s*(?:von\s*|bis\s*zu\s*)?(?:CHF\s*)?(\d+)', combined_text, re.IGNORECASE)
    if not cb_match:
        cb_match = re.search(r'(\d+)\s*(?:\.-|.–|CHF)?\s*(?:Cashback|Cash\s*Back|Rückvergütung)', combined_text, re.IGNORECASE)
    if not cb_match:
        cb_match = re.search(r'(?:CHF\s*)?(\d+)\s*(?:\.-|.–|CHF)?\s*(?:Cashback|Gutschein|Rabatt|Rückvergütung)', combined_text, re.IGNORECASE)
        
    if cb_match:
        val = int(cb_match.group(1))
        # Reject single digit false positives (< 10), years (2024, 2025, 2026), or cashback exceeding TV price
        if 10 <= val <= 2500 and val not in [2024, 2025, 2026] and (price == 0 or val < 0.6 * price):
            cashback_val = val
            
    # 2. Promotional standard mapping
    # LG SoundSuite / Soundbar bundle for OLED 2026 (Strict OLED guard to prevent QNED/NU false matches)
    is_lg_oled = brand_upper == "LG" and ("OLED" in code_upper or "OLED" in combined_upper) and not any(x in code_upper for x in ["QNED", "NANO", "NU", "UA", "UT"])
    if "SOUNDSUITE" in combined_upper or "SOUNDBAR DAZU" in combined_upper or "GRATIS SOUNDSUITE" in combined_upper or "GRATIS SOUNDBAR" in combined_upper:
        promo_text = "Free SoundSuite/Soundbar with LG OLED TV 2026 Purchase"
    elif is_lg_oled and year == 2026 and any(k in code_upper or k in combined_upper for k in ["C6", "G6", "B6", "M6", "W6"]):
        promo_text = "Free SoundSuite/Soundbar with LG OLED TV 2026 Purchase"
    elif brand_upper == "LG" and year == 2026 and any(k in code_upper for k in ["MRGB87B", "MRGB96B"]):
        promo_text = "Free Premium Sound Suite with LG Micro RGB Purchase"
        
    # Samsung Music Studio / Soundbar / Gift promotion
    elif "MUSIC STUDIO" in combined_upper or "HW-LS50H" in combined_upper:
        promo_text = "Free Music Studio 5 Soundbar (HW-LS50H/EN)"
    elif "ZUSATZPRODUKT" in combined_upper or "SOUND DEVICE GESCHENKT" in combined_upper or "SOUNDBAR GESCHENKT" in combined_upper:
        promo_text = "Free Sound Device with 2026 TV Purchase"
    elif "CASHBACK UND ODER 26%" in combined_upper or "QS700F" in combined_upper:
        promo_text = "Samsung Cashback and/or 26% Off Soundbar QS700F"
    elif brand_upper == "SAMSUNG" and year == 2026 and any(k in code_upper or k in combined_upper for k in ["S95H", "S90H", "S99H", "S85H"]):
        promo_text = "Free Music Studio 5 Soundbar (HW-LS50H/EN) with 2026 OLED"
    elif brand_upper == "SAMSUNG" and year == 2026 and any(k in code_upper or k in combined_upper for k in ["R85H", "R95H"]):
        promo_text = "Free Premium Music Studio Soundbar with Micro RGB Purchase"
    elif brand_upper == "SAMSUNG" and any(k in code_upper or k in combined_upper for k in ["LS03H", "LS03F"]):
        promo_text = "Free Frame Bezel & Art Store Promotion"
        
    # Clearance / Restposten / Outlet
    elif "RESTPOSTEN" in combined_upper:
        promo_text = "Clearance (Restposten)"
    elif "OUTLET" in combined_upper:
        promo_text = "Outlet (Clearance)"
        
    # Sale / Statt / Rabatt
    elif "STATT" in combined_upper or "WAS CHF" in combined_upper or "SALE" in combined_upper:
        pct_match = re.search(r'(\d+)\s*%', combined_text)
        was_match = re.search(r'(?:was|statt)\s*(?:chf)?\s*([\d’\x27\x60,.]+)', combined_text, re.IGNORECASE)
        pct = pct_match.group(1) if pct_match else None
        was_val = was_match.group(1).replace("’", "").replace("'", "").replace("`", "").strip() if was_match else None
        if was_val and (was_val.endswith(".") or was_val.endswith(",")):
            was_val = was_val[:-1]
            
        if pct and was_val:
            promo_text = f"Sale {pct}%; was CHF {was_val}"
        elif was_val:
            promo_text = f"was CHF {was_val}"
        elif pct:
            promo_text = f"Sale {pct}%"
            
    # Default fallback to cleaned raw promo
    elif promo_raw and str(promo_raw).strip() not in ["", "None", "0"]:
        promo_text = clean_swiss_promo_text(promo_raw, brand, year, model_code)
        
    # If cashback found, combine or set promo
    if cashback_val > 0:
        if promo_text == "None" or promo_text.startswith("Cashback"):
            promo_text = f"Cashback CHF {cashback_val}"
        elif f"CHF {cashback_val}" not in promo_text:
            promo_text = f"Cashback CHF {cashback_val}; {promo_text}"
        
    return cashback_val, promo_text
