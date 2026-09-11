# -*- coding: utf-8 -*-
"""
Parser Regression Test Suite (P2-5)
Tests domain-specific rules:
1. LG 2026 B6 guard: 65NU850B6LA, 55QNED81B6C, 65QNED72B6B do not misclassify as OLED B6.
2. Samsung Micro RGB: MRE85R95H vs R85 overmatching prevention (series is R95, size is 85).
3. European thousand period (.) and decimal comma (,) parsing: 1.199,00 € -> 1199.0.
4. French Narrow No-Break Space: 1\u202f999 € -> 1999.0.
5. Installment & discount badge text stripping: '100€ de remise 1 299 €' -> 1299.0.
6. Model year extraction & filtering: 2024 models (S90D, C4) excluded from 2025/2026 scope.
"""

import unittest
import re
import sys
import os

# Set stdout encoding
sys.stdout.reconfigure(encoding='utf-8')


# ---------------------------------------------------------------------------
# Canonical Domain Parsers & Classifiers under test
# ---------------------------------------------------------------------------

def parse_european_price(price_str):
    """
    Parses European prices with thousand periods and decimal commas,
    handling symbols like €, £, CHF, spaces, and non-breaking spaces.
    E.g. '1.199,00 €' -> 1199.0, '1.799,-' -> 1799.0, '559 ,00€' -> 559.0
    """
    if not price_str:
        return 0.0
    
    p = str(price_str).replace('€', '').replace('£', '').replace('CHF', '').replace('\xa0', ' ').replace('\u202f', ' ').strip()
    p = re.sub(r'[,.]-$', '', p)
    
    # 1. 1.199,00 or 1.199,50
    if re.search(r'\d{1,3}\.\d{3},\d{2}', p):
        p = p.replace('.', '').replace(',', '.')
    # 2. 1.199 without decimals (e.g. 1.199 €)
    elif re.search(r'^\d{1,3}\.\d{3}$', p.strip()):
        p = p.replace('.', '')
    # 3. 1,199.00
    elif re.search(r'\d{1,3},\d{3}\.\d{2}', p):
        p = p.replace(',', '')
    # 4. Comma as decimal separator: 559,00 or 559,0
    elif re.search(r'\d+,\d{1,2}$', p):
        p = p.replace(' ', '').replace(',', '.')
    # 5. Space as thousand separator: 1 199 or 1 199.00
    elif re.search(r'\d{1,3}\s+\d{3}', p):
        p = p.replace(' ', '').replace(',', '.')
    
    m = re.findall(r'(\d+(?:\.\d{1,2})?)', p)
    if m:
        try:
            val = float(m[0])
            return val if val >= 50.0 else 0.0
        except ValueError:
            pass
    return 0.0


def parse_french_price_with_stripping(text):
    """
    Parses French prices with narrow no-break space (\u202f) or non-breaking space (\xa0),
    and strips monthly installment ('Dès 45 € / mois') and discount badges ('100€ de remise').
    """
    if not text:
        return 0.0
    
    # Normalize Unicode spaces
    t = str(text).replace('\u202f', ' ').replace('\xa0', ' ').replace('\u2009', ' ')
    
    # Pre-strip discount mentions ('100€ de remise', '50€ de réduction', 'Bon Plan -200 €')
    t = re.sub(r'\d+€\s*(?:de\s*remise|d[\'\u2019]économie|de\s*réduction)', '', t, flags=re.IGNORECASE)
    t = re.sub(r'bon\s*plan\s*-\s*\d+\s*€', '', t, flags=re.IGNORECASE)
    
    # Pre-strip installment text ('Dès 45 € / mois', 'From £35 a month')
    t = re.sub(r'dès\s*[\d\s,.]+\s*€\s*\/\s*mois', '', t, flags=re.IGNORECASE)
    t = re.sub(r'from\s*£?[\d\s,.]+\s*a\s*month', '', t, flags=re.IGNORECASE)
    
    # Match French currency amounts: e.g. '1 299 €' or '999 €' or '2 199,00 €'
    m_eur = re.findall(r'([\d\s]+(?:[.,]\d{2})?)\s*€', t)
    vals = []
    if m_eur:
        for raw in m_eur:
            cleaned = raw.strip().replace(' ', '').replace(',', '.')
            try:
                v = float(cleaned)
                if v >= 50.0:
                    vals.append(v)
            except ValueError:
                pass
    else:
        # Fallback to general numeric parser
        return parse_european_price(t)
        
    return min(vals) if vals else 0.0


def classify_lg_product(model_code, title=""):
    """
    Classifies an LG TV model into (display_type, series_name).
    Strictly adheres to the LG 2026 B6 Guard:
    Budget / mid-range models like 65NU850B6LA, 55QNED81B6C, 65QNED72B6B contain 'B6'
    in their model suffix, but MUST NOT be classified as OLED or OLED B6.
    """
    mc_up = str(model_code).strip().upper()
    t_up = str(title).strip().upper()
    combined = f"{mc_up} {t_up}"
    
    # 1. Non-OLED display type checks take precedence over suffix matching
    if any(k in mc_up for k in ["QNED", "NANO", "NU", "UA", "UT"]) or any(k in t_up for k in ["QNED", "NANOCELL", "MINI LED"]):
        if "QNED" in mc_up or "QNED" in t_up:
            display_type = "QNED"
            m_qned = re.search(r'QNED(\d{2}[AB]?)', mc_up) or re.search(r'QNED(\d{2}[AB]?)', t_up)
            series = f"QNED{m_qned.group(1)}" if m_qned else "QNED"
        elif any(k in mc_up for k in ["NU", "UA", "UT"]) or "UHD" in t_up:
            display_type = "UHD 4K"
            m_nu = re.search(r'\b(NU\d{2,3}|UA\d{2}|UT\d{2})', mc_up) or re.search(r'\b(NU\d{2,3}|UA\d{2}|UT\d{2})', t_up)
            series = m_nu.group(1) if m_nu else "UHD 4K"
        else:
            display_type = "LED"
            series = "LED"
        return display_type, series
    
    # 2. Strict OLED classification
    is_oled = "OLED" in mc_up or "OLED" in t_up
    if is_oled:
        # Match OLED flagship series (e.g. OLED65B6, OLED55C6, OLED77G6, OLED65B5)
        m_mc = re.search(r'OLED\d{2}([BCGMW][456])', mc_up)
        if m_mc:
            return "OLED", f"OLED {m_mc.group(1)}"
        m_t = re.search(r'\b(?:OLED\s*(?:EVO\s*)?)?([BCGMW][456])\b', t_up)
        if m_t:
            return "OLED", f"OLED {m_t.group(1)}"
        return "OLED", "OLED"
    
    return "LED", "Unknown"


def classify_samsung_mrgb(model_code, title=""):
    """
    Classifies Samsung Micro RGB models.
    Guards against MRE85R95H being misclassified as series 'R85' due to '85' size prefix.
    Returns: (is_mrgb, screen_size, series)
    """
    mc_up = str(model_code).strip().upper()
    t_up = str(title).strip().upper()
    combined = f"{mc_up} {t_up}"
    
    is_mrgb = any(k in combined for k in ["MICRO RGB", "MICRO-RGB", "MRGB", "MRE", "TMR"])
    if not is_mrgb:
        return False, 0, "Unknown"
    
    # Extract size: e.g. MRE85... or TMR75... or 85"
    m_sz = re.search(r'(?:MRE|TMR)(\d{2})', mc_up)
    if not m_sz:
        m_sz = re.search(r'\b(100|86|85|75|65|55|50)[\s"”\'-]*(?:INCH|ZOLL|CM|\b)', t_up)
    size = int(m_sz.group(1)) if m_sz else 0
    
    # Extract series: R95H / R85H / R86H / R95 / R85
    # Strict matching: R95 must be matched before R85 to prevent overmatching on 85 size
    m_ser = re.search(r'(?:MRE\d{2}|TMR\d{2})?(R95[A-Z]?|R86[A-Z]?|R85[A-Z]?)\b', mc_up)
    if not m_ser:
        m_ser = re.search(r'\b(R95[A-Z]?|R86[A-Z]?|R85[A-Z]?)\b', t_up)
    
    series = m_ser.group(1) if m_ser else "Unknown"
    return is_mrgb, size, series


def extract_model_year(brand, model_code, title=""):
    """
    Extracts release model year for Samsung / LG TVs.
    Samsung: D=2024, F=2025, H=2026
    LG: 4=2024, 5/A=2025, 6/B=2026
    Returns: year (int) or None
    """
    brand_up = str(brand).strip().upper()
    mc_up = str(model_code).strip().upper()
    t_up = str(title).strip().upper()
    
    if brand_up == "SAMSUNG":
        if "2026" in t_up: return 2026
        if "2025" in t_up: return 2025
        if "2024" in t_up: return 2024
        
        # Check generation letter after prefix (index >= 2)
        if len(mc_up) > 3:
            sub = mc_up[2:]
            if "H" in sub: return 2026
            elif "F" in sub: return 2025
            elif "D" in sub or "E" in sub: return 2024
            
        # Series names in title
        if any(x in t_up for x in ["S90H", "S95H", "S85H", "S99H", "QN90H", "QN85H", "QN80H", "QN70H", "M80H", "M70H", "R95H", "R85H", "LS03H", "U8000H", "U8090H"]):
            return 2026
        if any(x in t_up for x in ["S90F", "S95F", "S85F", "QN95F", "QN90F", "QN85F", "QN80F", "QN70F", "Q8F", "Q7F", "Q6F", "LS03F", "U8000F", "U8090F"]):
            return 2025
        if any(x in t_up for x in ["S90D", "S95D", "S85D", "QN95D", "QN90D", "QN85D", "QN80D", "LS03D", "U8000D"]):
            return 2024
            
    elif brand_up == "LG":
        # Check explicit year tags
        if "2026" in t_up: return 2026
        if "2025" in t_up: return 2025
        if "2024" in t_up: return 2024
        
        # Model code checks
        if any(x in mc_up for x in ["C6", "G6", "B6", "M6", "W6", "QNED86B", "QNED80B", "QNED87B", "QNED72B", "QNED71B", "QNED70B", "QNED7EB", "UA77", "MRGB87B", "MRGB96B", "LX7B", "LX6", "27LX6TDGA", "NU850B", "NU85"]):
            return 2026
        if any(x in mc_up for x in ["C5", "G5", "B5", "M5", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED70A", "QNED7EA", "UA75", "MRGB87A", "LX7A", "LX5", "QNED93A"]):
            return 2025
        if any(x in mc_up for x in ["C4", "G4", "B4", "M4", "QNED80T", "QNED85T", "QNED86T", "UA73"]):
            return 2024
            
        # Title checks
        if any(x in t_up for x in ["C6", "G6", "B6", "QNED86B", "QNED80B", "QNED70B", "MRGB87B", "MRGB96B"]):
            return 2026
        if any(x in t_up for x in ["C5", "G5", "B5", "QNED86A", "QNED80A", "QNED70A"]):
            return 2025
        if any(x in t_up for x in ["C4", "G4", "B4"]):
            return 2024
            
    return None


def is_target_survey_model(brand, model_code, title=""):
    """Returns True if the model belongs to target survey years 2025 or 2026."""
    year = extract_model_year(brand, model_code, title)
    return year in [2025, 2026]


# ---------------------------------------------------------------------------
# Unit Test Suite
# ---------------------------------------------------------------------------

class TestParserRegression(unittest.TestCase):

    # -----------------------------------------------------------------------
    # Rule 1: LG 2026 B6 Guard
    # -----------------------------------------------------------------------
    def test_lg_2026_b6_guard_non_oled_models(self):
        """UHD 4K & QNED models with B6 suffixes must NOT be classified as OLED B6."""
        test_cases = [
            ("65NU850B6LA", "LG 65NU850B6LA 4K UHD Smart TV 2026", "UHD 4K"),
            ("55QNED81B6C", "LG 55QNED81B6C QNED Evo Smart TV 2026", "QNED"),
            ("65QNED72B6B", "LG 65QNED72B6B QNED 4K TV 2026", "QNED"),
            ("85QNED72B6A", "LG 85QNED72B6A QNED 4K TV 2025", "QNED"),
            ("55UA77006LB", "LG 55UA77006LB 4K LED TV 2026", "UHD 4K"),
        ]
        
        for model_code, title, expected_disp in test_cases:
            with self.subTest(model_code=model_code):
                disp_type, series = classify_lg_product(model_code, title)
                self.assertNotEqual(disp_type, "OLED", f"{model_code} must not be classified as OLED")
                self.assertNotIn("OLED B6", series, f"{model_code} must not be classified as series OLED B6")
                self.assertEqual(disp_type, expected_disp, f"{model_code} display type mismatch")

    def test_lg_genuine_oled_b6_classification(self):
        """Genuine OLED B6 models MUST be correctly identified as OLED and OLED B6."""
        genuine_cases = [
            ("OLED65B6PLA", "LG OLED65B6PLA 4K OLED TV"),
            ("OLED55B6", "LG OLED evo B6 55 Zoll 4K"),
            ("OLED77B6", "LG OLED77B6 4K Smart TV"),
        ]
        for model_code, title in genuine_cases:
            with self.subTest(model_code=model_code):
                disp_type, series = classify_lg_product(model_code, title)
                self.assertEqual(disp_type, "OLED")
                self.assertEqual(series, "OLED B6")

    # -----------------------------------------------------------------------
    # Rule 2: Samsung Micro RGB Overmatching Guard (MRE85R95H vs R85)
    # -----------------------------------------------------------------------
    def test_samsung_micro_rgb_r95_vs_r85(self):
        """MRE85R95H must be classified as 85-inch R95 series, not R85 series."""
        # 85" R95 flagship
        is_m, sz, ser = classify_samsung_mrgb("MRE85R95H", "Samsung Micro RGB MRE85R95H 2026")
        self.assertTrue(is_m)
        self.assertEqual(sz, 85, "Screen size should be 85")
        self.assertEqual(ser, "R95H", "Series must be R95H, not R85H!")
        
        # 85" R95 with French TMR code
        is_m, sz, ser = classify_samsung_mrgb("TMR85R95H", "TV LED Samsung Micro RGB TMR85R95H 216 cm 2026")
        self.assertTrue(is_m)
        self.assertEqual(sz, 85)
        self.assertEqual(ser, "R95H")

        # 65" R85 model
        is_m, sz, ser = classify_samsung_mrgb("MRE65R85H", "Samsung Micro RGB MRE65R85H 2026")
        self.assertTrue(is_m)
        self.assertEqual(sz, 65)
        self.assertEqual(ser, "R85H")

    # -----------------------------------------------------------------------
    # Rule 3: European Thousand Period and Decimal Comma Parsing
    # -----------------------------------------------------------------------
    def test_european_price_parsing(self):
        """European formatted price strings must parse to exact floats."""
        cases = [
            ("1.199,00 €", 1199.0),
            ("1.799,-", 1799.0),
            ("559 ,00€", 559.0),
            ("2.499,50 €", 2499.5),
            ("1.199 €", 1199.0),
            ("3.499,00 €", 3499.0),
            ("699,00 €", 699.0),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                parsed = parse_european_price(raw)
                self.assertAlmostEqual(parsed, expected, places=2)

    # -----------------------------------------------------------------------
    # Rule 4: France Narrow No-Break Space (\u202f & \xa0)
    # -----------------------------------------------------------------------
    def test_french_narrow_no_break_space(self):
        """Narrow No-Break Space (\u202f) and non-breaking space (\xa0) must not split prices."""
        cases = [
            ("1\u202f999 €", 1999.0),
            ("1\u00a0299 €", 1299.0),
            ("3\u202f499 €", 3499.0),
            ("999 €", 999.0),
            ("2\u202f199,00 €", 2199.0),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                parsed = parse_french_price_with_stripping(raw)
                self.assertAlmostEqual(parsed, expected, places=2)

    # -----------------------------------------------------------------------
    # Rule 5: Installment & Discount Badge Stripping
    # -----------------------------------------------------------------------
    def test_installment_and_discount_badge_stripping(self):
        """Promotional badges and installment amounts must be stripped before price parsing."""
        cases = [
            ("100€ de remise 1 299 €", 1299.0),
            ("50€ de réduction 899 €", 899.0),
            ("Dès 45 € / mois 1 499 €", 1499.0),
            ("Bon Plan -200 € 2 199 €", 2199.0),
            ("100€ d'économie 1 799 €", 1799.0),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                parsed = parse_french_price_with_stripping(raw)
                self.assertAlmostEqual(parsed, expected, places=2)

    # -----------------------------------------------------------------------
    # Rule 6: Model Year Extraction & Filtering
    # -----------------------------------------------------------------------
    def test_model_year_extraction_and_filtering(self):
        """Pre-2025 models must be rejected; 2025/2026 models must be accepted."""
        # Older models (2024) -> Must be rejected
        older_models = [
            ("SAMSUNG", "QE65S90D", "Samsung OLED 65S90D 2024"),
            ("SAMSUNG", "QE75QN90D", "Samsung Neo QLED 75QN90D 2024"),
            ("LG", "OLED55C4", "LG OLED evo 55C4 2024"),
            ("LG", "OLED65G4", "LG OLED evo 65G4 2024"),
            ("LG", "65QNED80T", "LG 65QNED80T 4K TV 2024"),
        ]
        for brand, mc, title in older_models:
            with self.subTest(brand=brand, model_code=mc):
                year = extract_model_year(brand, mc, title)
                self.assertEqual(year, 2024)
                self.assertFalse(is_target_survey_model(brand, mc, title), f"{mc} (2024) should be excluded")

        # Target models (2025 / 2026) -> Must be accepted
        target_models = [
            ("SAMSUNG", "QE65S90F", "Samsung OLED 65S90F 2025", 2025),
            ("SAMSUNG", "QE65S90H", "Samsung OLED 65S90H 2026", 2026),
            ("SAMSUNG", "MRE85R95H", "Samsung Micro RGB 85R95H 2026", 2026),
            ("LG", "OLED55C5", "LG OLED evo 55C5 2025", 2025),
            ("LG", "OLED65C6", "LG OLED evo 65C6 2026", 2026),
            ("LG", "65NU850B6LA", "LG 65NU850B6LA 4K UHD 2026", 2026),
            ("LG", "55QNED81B6C", "LG 55QNED81B6C QNED TV 2026", 2026),
        ]
        for brand, mc, title, expected_year in target_models:
            with self.subTest(brand=brand, model_code=mc):
                year = extract_model_year(brand, mc, title)
                self.assertEqual(year, expected_year)
                self.assertTrue(is_target_survey_model(brand, mc, title), f"{mc} ({expected_year}) should be included")


if __name__ == '__main__':
    unittest.main()
