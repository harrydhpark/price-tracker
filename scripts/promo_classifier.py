"""

Promotion Classifier and Standardizer for European TV Price Tracking

Categorizes promotional texts into:

1. Original Price (Was / Strikethrough / Statt price extraction)

2. Cashback (Numeric integer amount)

3. Price Promotion (Direct discounts, trade-in, instant coupon codes, store loyalty credit)

4. Non-Price Promotion (Free gift soundbars, bundle discounts, custom bezels, extended warranty, subscriptions)



Also filters out non-promotional retailer/marketing badges:

- Aus unserer Werbung (Weekly ad)

- Online Only

- Clearance / Restposten / Outlet

- Free Delivery (already tracked in Shipping column)

"""



import re

import unicodedata



# Non-promotional marketing tags to completely filter out

NON_PROMO_BADGES = [

    r'AUS UNSERER WERBUNG',

    r'WEEKLY AD',

    r'ONLINE[\s-]?ONLY',

    r'RESTPOSTEN',

    r'OUTLET',

    r'CLEARANCE',

    r'BESTSELLER',

    r'FREE DELIVERY',

    r'GRATIS VERSAND',

    r'LIVRAISON GRATUITE',

    r'ENVIO GRATIS',

    r'SPEDIZIONE GRATUITA',

    r'DOPRAVA ZDARMA',

    r'INGYENES SZÁLLÍTÁS',

    r'INGYENES SZALLITAS',

    r'ON ADORE.*',

    r'TECHNOLOGIE MINI LED.*',

    r'MOTION XCELERATOR.*',

    r'TOP FAVORITE',

    r'SUPER PRET',

    r'CRAZY DAYS',

]



def clean_raw_text(text):

    if not text or str(text).strip() in ["", "None", "0", "null", "undefined"]:

        return ""

    # Normalize unicode spaces (Narrow no-break space, non-breaking space)

    t = str(text).replace("\u202f", " ").replace("\u00a0", " ").replace("\u2009", " ").replace("\u200b", " ")

    return t.strip()



def normalize_diacritics(text):

    if not text:

        return ""

    nfd = unicodedata.normalize('NFD', text)

    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')



def extract_was_price(text, currency="EUR"):

    """

    Extracts original/was/strikethrough price from expressions like:

    - 'was 300 euro', 'Was £1,099', 'was CHF 1'499', 'statt 1.299 €'

    Returns float value or None.

    """

    if not text:

        return None

        

    t = clean_raw_text(text)

    

    # Match patterns like:

    # "was 300 euro", "was €1,299", "was £1,099.00", "statt CHF 1'499", "statt € 899", "spara 300 kr"

    patterns = [

        r'(?:was|statt|spara)\s*(?:chf|eur|gbp|sek|czk|huf|€|£)?\s*([\d’\x27\x60,.]+)(?:\s*(?:chf|eur|gbp|sek|czk|huf|euro|euros|€|£))?',

        r'(?:chf|eur|gbp|sek|czk|huf|€|£)\s*([\d’\x27\x60,.]+)\s*(?:was|statt)',

    ]

    

    for pat in patterns:

        m = re.search(pat, t, re.IGNORECASE)

        if m:

            val_str = m.group(1).replace("’", "").replace("'", "").replace("`", "").strip()

            if not val_str:

                continue

            if val_str.endswith(".") or val_str.endswith(","):

                val_str = val_str[:-1]

                

            # European format vs UK format

            if "," in val_str and "." in val_str:

                if val_str.find(".") < val_str.find(","):

                    # 1.299,00

                    val_str = val_str.replace(".", "").replace(",", ".")

                else:

                    # 1,299.00

                    val_str = val_str.replace(",", "")

            elif "." in val_str and re.match(r'^\d{1,3}\.\d{3}$', val_str):

                val_str = val_str.replace(".", "")

            elif "," in val_str and re.match(r'^\d{1,3},\d{3}$', val_str):

                val_str = val_str.replace(",", "")

            elif "," in val_str:

                val_str = val_str.replace(",", ".")

                

            try:

                val = float(val_str)

                # Ignore small numbers or years like 2025, 2026 if price is suspiciously tiny

                if 50.0 <= val <= 30000.0:

                    return val

            except ValueError:

                pass

                

    return None



def extract_numeric_cashback(text, currency="EUR", price=0.0):

    """

    Extracts numeric cashback amount across all 15 European languages:

    - DE/AT/CH: Cashback, Rückvergütung, Geld zurück

    - UK: Cashback, Claim back

    - FR: ODR, Offre de remboursement, Remboursement différé

    - ES/PT: Reembolso, Devolución

    - IT: Rimborso, Cashback

    - NL: Retour, Geld terug, Terugbetaling

    - PL: Zwrot, Kasa wraca, Odbierz zwrot

    - SE: Återbäring, Aterbaring, Återbetalning

    - CZ: Cashback, Peníze zpět

    - HU: Visszatérítés, Visszaterites

    - RO: Cashback, Restituire

    - GR: Επιστροφή, Epistrofi

    """

    if not text:

        return 0

        

    t = clean_raw_text(text)

    curr_pats = r'(?:chf|eur|gbp|sek|czk|huf|pln|ron|kr|€|£|zł|lei)?'

    cb_keywords = r'(?:cashback|cash\s*back|claim\s*(?:up\s*to\s*)?[£€]?\d+\s*back|reembolso|rimborso|retour|terug|rückvergütung|ruckvergutung|geld\s*zurück|remise\s*différée|remboursement|odr|zwrot|kasa\s*wraca|återbäring|aterbaring|återbetalning|visszatérítés|visszaterites|επιστροφή|epistrofi|restituire|penize\s*zpet)'

    

    # 1. Number before cashback: "100€ Cashback", "500 zł zwrotu", "1000 kr återbäring", "CHF 1000.- Cashback"

    m = re.search(curr_pats + r'\s*(\d{2,5})\s*' + curr_pats + r'\s*(?:\.-|.–|[\.,\-])?\s*' + cb_keywords, t, re.IGNORECASE)

    if m:

        val = int(m.group(1))

        if val not in [2024, 2025, 2026] and (price == 0 or val <= 0.85 * price or val <= 5000):

            return val

            

    # 2. Number after cashback: "Cashback: €100", "Cashback: CHF 1000", "Kasa wraca: 500 zł", "ODR 150€"

    m2 = re.search(cb_keywords + r'[:\s-]*(?:von|bis\s*zu|sichern|de|na\s*konto)?\s*' + curr_pats + r'\s*(\d{2,5})', t, re.IGNORECASE)

    if m2:

        val = int(m2.group(1))

        if val not in [2024, 2025, 2026] and (price == 0 or val <= 0.85 * price or val <= 5000):

            return val



    # 3. Direct Cashback with negative discount: "Direct Cashback | - CHF 500" or "- CHF 500.- Rabatt"

    m3 = re.search(r'direct\s*cashback[^\d]*-\s*' + curr_pats + r'\s*(\d{2,5})', t, re.IGNORECASE)

    if m3:

        val = int(m3.group(1))

        if val not in [2024, 2025, 2026] and (price == 0 or val <= 0.85 * price or val <= 5000):

            return val

            

    return 0



def extract_numeric_direct_cut(text, currency="EUR", price=0.0):

    """

    Extracts instant cart discounts, coupon codes, and direct price cuts across Europe:

    - UK: Save GBP 200, £100 off with code

    - DE/AT/CH: Direktabzug 200€, Sofortrabatt 150€, Gutschein 100€

    - FR: Remise immédiate de 100€, 150€ de remise

    - IT: Sconto subito a carrello di 100€, Sconto a carrello

    - ES/PT: Descuento directo, Desconto direto, Cupão APP

    - NL: Directe korting, Kassakorting

    - PL: Rabat w koszyku, Rabat z kodem, Zniżka

    - GR: Κέρδος 250 €, Άμεση έκπτωση

    - RO: Reducere directă, Card cadou eMAG

    """

    if not text:

        return 0

        

    t = clean_raw_text(text)

    

    patterns = [

        r'Save\s*(?:GBP|£)\s*(\d+)',

        r'(\d+)\s*(?:GBP|£)?\s*off\s*with\s*code',

        r'-\s*(?:CHF|EUR|€)?\s*(\d+)(?:\.-|.–|[\.,\-])?\s*(?:Rabatt|Direktabzug|Sofortrabatt)',

        r'(?:CHF|EUR|€)?\s*(\d+)(?:\.-|.–|[\.,\-])?\s*(?:Rabatt|Direktabzug|Sofortrabatt)',

        r'(?:Direktabzug|Sofortrabatt|Gutschein)[:\s-]*(?:von|bis\s*zu)?\s*(?:CHF|EUR|€)?\s*(\d+)',

        r'Remise\s*immédiate[:\s-]*(?:de)?\s*(?:EUR|€)?\s*(\d+)',

        r'(\d+)\s*€\s*de\s*remise\s*(?:immédiate)?',

        r'Sconto\s*(?:subito\s*)?(?:a\s*carrello)?[:\s-]*(?:di)?\s*(?:EUR|€)?\s*(\d+)',

        r'(\d+)\s*€\s*di\s*sconto\s*(?:a\s*carrello|subito)?',

        r'(?:Descuento|Desconto)\s*direto[:\s-]*(?:de)?\s*(?:EUR|€)?\s*(\d+)',

        r'Cupão[:\s-]*(?:de)?\s*(?:EUR|€)?\s*(\d+)',

        r'Directe\s*korting[:\s-]*(?:van)?\s*(?:EUR|€)?\s*(\d+)',

        r'Kassakorting[:\s-]*(\d+)',

        r'(?:Rabat|Zniżka)[:\s-]*(\d+)\s*(?:zł|pln)',

        r'(\d+)\s*(?:zł|pln)\s*rabatu',

        r'Κέρδος\s*(\d+)\s*€',

        r'Άμεση\s*έκπτωση\s*(\d+)',

        r'Reducere\s*directă[:\s-]*(?:de)?\s*(\d+)',

        r'Card\s*cadou[:\s-]*(\d+)',

        r'Direktrabatt[:\s-]*(\d+)\s*(?:kr|sek)?',

    ]

    

    for pat in patterns:

        m = re.search(pat, t, re.IGNORECASE)

        if m:

            val = int(m.group(1))

            if val not in [2024, 2025, 2026] and (price == 0 or val <= 0.85 * price or val <= 5000):

                return val

                

    return 0



def classify_promotions(promo_raw, title_raw="", brand="", year=2026, model_code="", price=0.0, currency="EUR", existing_original_price=0.0):

    """

    Master classifier:

    Takes raw promotional text and product metadata, returns:

    (original_price, cashback_int, price_promotion_str, non_price_promotion_str)

    """

    combined_raw = f"{promo_raw or ''} {title_raw or ''}".strip()

    clean_p = clean_raw_text(promo_raw)

    clean_combined = clean_raw_text(combined_raw)

    

    upper_promo = normalize_diacritics(clean_p.upper())

    upper_comb = normalize_diacritics(clean_combined.upper())

    code_upper = normalize_diacritics(str(model_code or "").upper())

    brand_upper = normalize_diacritics(str(brand or "").upper())

    

    # 1. Original Price Extraction

    extracted_orig = extract_was_price(clean_p, currency=currency)

    final_orig_price = existing_original_price if existing_original_price and existing_original_price > 0 else 0.0

    if extracted_orig and extracted_orig > price:

        if final_orig_price == 0.0 or extracted_orig > final_orig_price:

            final_orig_price = extracted_orig



    # 2. Cashback & Direct Cut Extraction

    cashback_val = extract_numeric_cashback(clean_combined, currency=currency, price=price)

    direct_cut_val = extract_numeric_direct_cut(clean_combined, currency=currency, price=price)

    if cashback_val > 0 and direct_cut_val > 0 and cashback_val == direct_cut_val:
        total_deduction = cashback_val
    else:
        total_deduction = cashback_val + direct_cut_val



    # 3. Non-promotional Marketing Badges Purge

    # Check if the promo string is purely a marketing label

    is_pure_badge = False

    for badge_pat in NON_PROMO_BADGES:

        if re.search(r'^' + badge_pat + r'$', upper_promo.strip()):

            is_pure_badge = True

            break

            

    # Check for pure 'Sale X%' or 'Discount -X%' with no other campaign/gift info

    is_pure_discount_rate = bool(re.match(r'^(?:SALE|DISCOUNT|RABATT)?\s*[-]?\d{1,2}\s*%$', upper_promo.strip()))

    

    # Check for pure was price string: e.g. "was 300 euro", "was GBP 1,099.00", "was CHF 1499"

    is_pure_was_price = bool(re.match(r'^(?:SALE\s*\d+%\s*;\s*)?(?:WAS|STATT|SPARA)\s*(?:CHF|EUR|GBP|SEK|CZK|HUF|€|£)?\s*[\d’\x27\x60,.]+(?:\s*(?:EURO|EUROS|CHF|EUR|GBP|€|£))?$', upper_promo.strip()))



    price_promos = []

    non_price_promos = []



    # ----------------------------------------------------

    # A. PRICE PROMOTIONS (Cashback, Trade-in, Instant Rebate, Coupon, Loyalty Credit)

    # ----------------------------------------------------

    # Resolve Currency Symbol for Promotions

    if "GBP" in upper_comb or "£" in clean_p or currency == "GBP":

        curr_symbol = "£"

    elif "CHF" in upper_comb or currency == "CHF":

        curr_symbol = "CHF "

    elif "PLN" in upper_comb or currency == "PLN" or "ZŁ" in upper_comb:

        curr_symbol = "zł"

    elif "SEK" in upper_comb or currency == "SEK":

        curr_symbol = "kr"

    elif "CZK" in upper_comb or currency == "CZK":

        curr_symbol = "Kč"

    elif "HUF" in upper_comb or currency == "HUF":

        curr_symbol = "Ft"

    elif "RON" in upper_comb or currency == "RON":

        curr_symbol = "lei"

    else:

        curr_symbol = "€"



    # A1. Cashback

    if cashback_val > 0:

        price_promos.append(f"Cashback: {curr_symbol}{cashback_val}")



    # A1-2. Direct Cut / Instant Cart Discount

    if direct_cut_val > 0:

        price_promos.append(f"Direct Cut: {curr_symbol}{direct_cut_val}")



    # A2. Trade-in Discounts

    # e.g. "Trade-in GBP 100 off", "Trade in 150 off", "Trade-in 250 off"

    trade_in_match = re.search(r'Trade[\s-]?in\s*(?:GBP|EUR|CHF|€|£)?\s*(\d+)\s*off', clean_p, re.IGNORECASE)

    if trade_in_match:

        if "GBP" in upper_promo or "£" in clean_p:

            curr_sym = "£"

        elif "CHF" in upper_promo:

            curr_sym = "CHF "

        elif currency == "GBP":

            curr_sym = "£"

        elif currency == "CHF":

            curr_sym = "CHF "

        else:

            curr_sym = "€"

        price_promos.append(f"Trade-in Discount: {curr_sym}{trade_in_match.group(1)} Off")



    # A3. Loyalty Rewards / Store Credit

    # e.g. "15% Public επιστροφή"

    if "ΕΠΙΣΤΡΟΦ" in upper_comb or "EPISTROFI" in upper_comb:

        pct_m = re.search(r'(\d+)\s*%', clean_p)

        pct_str = f"{pct_m.group(1)}%" if pct_m else "15%"

        price_promos.append(f"Loyalty Reward: {pct_str} Store Credit (Public)")



    # A4. Instant Rebate / Coupon Code Campaigns

    if "ALZA DAYS" in upper_comb:

        price_promos.append("Coupon Discount: Alza Days Special Rebate")

    elif "VUELTA AL COLE" in upper_comb:

        pct_m = re.search(r'(\d+)\s*%', clean_p)

        if pct_m:

            price_promos.append(f"Instant Rebate: -{pct_m.group(1)}% (Back to School Promo)")

        else:

            price_promos.append("Instant Rebate: Back to School Promo")

    elif "BON PLAN" in upper_comb and "REMISE" in upper_comb:

        rem_m = re.search(r'(\d+)\s*€?\s*(?:de\s*remise)', clean_p, re.IGNORECASE)

        if rem_m:

            price_promos.append(f"Instant Rebate: -€{rem_m.group(1)} Immediate Discount")

        else:

            price_promos.append("Instant Rebate: Special Immediate Discount")

    elif "DIRECT CUT" in upper_promo:

        price_promos.append(clean_p)



    # ----------------------------------------------------

    # B. NON-PRICE PROMOTIONS (Soundbars, Bundles, Bezels, Extended Warranty, Subscriptions)

    # ----------------------------------------------------

    # B1. Bundle Discounts (TV + Soundbar combo discount)

    # e.g. "Get 30% off selected soundbars when bought with any Samsung TV"

    # e.g. "TV + Soundbar = 30% Rabatt"

    # e.g. "Cashback und oder 26% Rabatt auf Soundbar QS700F"

    # e.g. "Soundbar LG στα 119€"

    if "GET 30% OFF SELECTED SOUNDBARS" in upper_comb or ("TV + SOUNDBAR" in upper_comb and "30%" in upper_comb):

        non_price_promos.append("Bundle Offer: 30% Off Selected Soundbar with TV")

    elif "26% RABATT AUF SOUNDBAR QS700F" in upper_comb or "QS700F" in upper_comb:

        non_price_promos.append("Bundle Offer: 26% Off Soundbar QS700F")

    elif re.search(r'SOUNDBAR\s*(?:LG|SAMSUNG)?\s*ΣΤΑ\s*(\d+)\s*€', upper_comb):

        sb_m = re.search(r'SOUNDBAR\s*(?:LG|SAMSUNG)?\s*ΣΤΑ\s*(\d+)\s*€', upper_comb)

        brand_tag = "LG" if "LG" in upper_comb else "Samsung"

        non_price_promos.append(f"Bundle Offer: {brand_tag} Soundbar at €{sb_m.group(1)}")

    elif "BUNDELVOORDEEL" in upper_promo:

        non_price_promos.append("Bundle Offer: Audio Accessory Discount")



    # B2. Free Gift: Soundbars & Audio Devices

    # e.g. "Free LG US20A Soundbar worth £129 with this TV"

    # e.g. "Free LG US60TR Soundbar worth £399 with this TV"

    # e.g. "Free SoundSuite/Soundbar with LG OLED TV 2026 Purchase"

    # e.g. "Free Music Studio 5 Soundbar (HW-LS50H/EN) with 2026 OLED"

    # e.g. "Δώρο Samsung Soundbar"

    if "FREE LG US20A SOUNDBAR" in upper_comb or "US20A" in upper_comb:

        non_price_promos.append("Free Gift: LG Soundbar (US20A, £129 value)")

    elif "FREE LG US60TR SOUNDBAR" in upper_comb or "US60TR" in upper_comb:

        non_price_promos.append("Free Gift: LG Soundbar (US60TR, £399 value)")

    elif "SOUNDSUITE" in upper_comb or "SOUNDBAR DAZU" in upper_comb or "GRATIS SOUNDBAR" in upper_comb:

        non_price_promos.append("Free Gift: SoundSuite/Soundbar with LG OLED TV")

    elif "MUSIC STUDIO" in upper_comb or "HW-LS50H" in upper_comb:

        non_price_promos.append("Free Gift: Music Studio 5 Soundbar (HW-LS50H/EN)")

    elif "ΔΩΡΟ SAMSUNG SOUNDBAR" in upper_comb or "DORO SAMSUNG SOUNDBAR" in upper_comb:

        non_price_promos.append("Free Gift: Samsung Soundbar")

    elif "SOUND DEVICE GESCHENKT" in upper_comb or "ZUSATZPRODUKT" in upper_comb or "FREE SOUND DEVICE" in upper_comb:

        non_price_promos.append("Free Gift: Free Sound Device with TV Purchase")

    elif brand_upper == "LG" and year == 2026 and any(k in code_upper for k in ["MRGB87B", "MRGB96B"]):

        non_price_promos.append("Free Gift: Premium Sound Suite with LG Micro RGB")

    elif brand_upper == "SAMSUNG" and year == 2026 and any(k in code_upper for k in ["R85H", "R95H"]):

        non_price_promos.append("Free Gift: Premium Music Studio Soundbar with Micro RGB")



    # B3. Free Gift: Custom Bezel & Frames

    # e.g. "Δώρο Frame στο Καλάθι", "Free Frame Bezel & Art Store Promotion"

    if "ΔΩΡΟ FRAME" in upper_comb or "FRAME BEZEL" in upper_comb or ("LS03" in code_upper and "BEZEL" in upper_comb):

        non_price_promos.append("Free Gift: The Frame Custom Bezel")



    # B4. Extended Warranty

    # e.g. "Δώρο Επέκταση Εγγύησης", "5 Years Warranty"

    if "ΕΠΕΚΤΑΣΗ ΕΓΓΥΗΣΗΣ" in upper_comb or "EPEKTASI EGGYISIS" in upper_comb or "EXTENDED WARRANTY" in upper_comb:

        non_price_promos.append("Extended Warranty: Free Extended Guarantee")



    # B5. Subscriptions / Content

    if "ART STORE" in upper_comb:

        if not any("FRAME" in p for p in non_price_promos):

            non_price_promos.append("Free Subscription: Art Store Service")

    if "STREAMING CONTENT" in upper_comb or "STREAMING" in upper_comb:

        non_price_promos.append("Free Content: Streaming Package Included")



    # ----------------------------------------------------

    # Final cleanup & Fallback resolution

    # ----------------------------------------------------

    # If the raw promo string was pure marketing/clearance badge or pure was price, suppress fallback

    if is_pure_badge or is_pure_was_price or is_pure_discount_rate:

        pass

    else:

        # If no standard promo matched, check if there's residual text not yet captured

        if not price_promos and not non_price_promos and clean_p:

            # Strip was/statt prices and pure discount badges from residual text

            residual = re.sub(r'(?:was|statt|spara)\s*(?:chf|eur|gbp|sek|czk|huf|€|£)?\s*[\d’\x27\x60,.]+(?:\s*(?:euro|euros|€|£))?', '', clean_p, flags=re.IGNORECASE).strip()

            residual = re.sub(r'Sale\s*\d+%\s*;?', '', residual, flags=re.IGNORECASE).strip()

            residual = re.sub(r'Discount\s*-\d+%\s*;?', '', residual, flags=re.IGNORECASE).strip()

            residual = residual.strip(" ;,-")

            

            # Check against marketing badges again

            if residual and not any(re.search(b, residual.upper()) for b in NON_PROMO_BADGES):

                # If it looks like a discount or promotion, assign appropriately

                if any(x in residual.upper() for x in ["CASHBACK", "REEMBOLSO", "RIMBORSO", "REBATE"]):

                    price_promos.append(residual)

                elif any(x in residual.upper() for x in ["GIFT", "SOUNDBAR", "GRATIS", "FREE", "WARRANTY", "BUNDLE"]):

                    non_price_promos.append(residual)



    price_promo_str = "; ".join(dict.fromkeys(price_promos)) if price_promos else "None"

    non_price_promo_str = "; ".join(dict.fromkeys(non_price_promos)) if non_price_promos else "None"



    return final_orig_price, total_deduction, price_promo_str, non_price_promo_str

