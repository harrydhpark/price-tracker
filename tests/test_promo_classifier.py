import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from promo_classifier import classify_promotions, extract_was_price, extract_numeric_cashback

class TestPromoClassifier(unittest.TestCase):

    def test_was_price_extraction(self):
        # 'was 300 euro'
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="was 300 euro",
            price=249.0,
            currency="EUR"
        )
        self.assertEqual(orig, 300.0)
        self.assertEqual(cb, 0)
        self.assertEqual(price_p, "None")
        self.assertEqual(non_price_p, "None")

        # 'Was £1,099.00'
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Sale 15%; was £1,099.00",
            price=899.0,
            currency="GBP"
        )
        self.assertEqual(orig, 1099.0)
        self.assertEqual(price_p, "None")
        self.assertEqual(non_price_p, "None")

        # 'statt CHF 1'499'
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="statt CHF 1'499",
            price=1199.0,
            currency="CHF"
        )
        self.assertEqual(orig, 1499.0)
        self.assertEqual(price_p, "None")
        self.assertEqual(non_price_p, "None")

    def test_marketing_badges_purging(self):
        # Badges that are NOT customer promotions must return None
        for badge in ["Aus unserer Werbung", "Featured in Weekly Ad (Aus unserer Werbung)", "Online Only", "Clearance (Restposten)", "Outlet (Clearance)", "Free Delivery"]:
            orig, cb, price_p, non_price_p = classify_promotions(promo_raw=badge, price=500.0)
            self.assertEqual(price_p, "None", f"Badge {badge} leaked to price_p")
            self.assertEqual(non_price_p, "None", f"Badge {badge} leaked to non_price_p")

    def test_pure_discount_rate_purging(self):
        # Pure discount percentages without campaign names
        for d in ["Discount -15%", "Discount -20%", "Sale 30%", "-25%"]:
            orig, cb, price_p, non_price_p = classify_promotions(promo_raw=d, price=500.0)
            self.assertEqual(price_p, "None", f"Rate {d} leaked to price_p")
            self.assertEqual(non_price_p, "None", f"Rate {d} leaked to non_price_p")

    def test_trade_in_and_cashback_price_promotions(self):
        # Trade-in
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Trade-in GBP 100 off",
            currency="GBP",
            price=799.0
        )
        self.assertEqual(price_p, "Trade-in Discount: £100 Off")
        self.assertEqual(non_price_p, "None")

        # Combo: Save + Trade-in
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Save GBP 100.00; Trade-in GBP 150 off",
            currency="GBP",
            price=999.0
        )
        self.assertEqual(price_p, "Trade-in Discount: £150 Off")
        self.assertEqual(non_price_p, "None")

        # Public Greece επιστροφή
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="15% Public επιστροφή",
            currency="EUR",
            price=600.0
        )
        self.assertEqual(price_p, "Loyalty Reward: 15% Store Credit (Public)")

        # Alza Days
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Alza Days Discount Campaign",
            currency="CZK",
            price=15000.0
        )
        self.assertEqual(price_p, "Coupon Discount: Alza Days Special Rebate")

        # Vuelta al cole
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Vuelta al cole (-10%)",
            currency="EUR",
            price=1200.0
        )
        self.assertEqual(price_p, "Instant Rebate: -10% (Back to School Promo)")

    def test_non_price_promotions(self):
        # Currys Soundbar gift
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Free LG US20A Soundbar worth £129 with this TV",
            brand="LG",
            currency="GBP",
            price=999.0
        )
        self.assertEqual(non_price_p, "Free Gift: LG Soundbar (US20A, £129 value)")

        # Currys bundle 30% off soundbars
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Get 30% off selected soundbars when bought with any Samsung TV",
            brand="Samsung",
            currency="GBP",
            price=1499.0
        )
        self.assertEqual(non_price_p, "Bundle Offer: 30% Off Selected Soundbar with TV")

        # Swiss SoundSuite
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Free SoundSuite/Soundbar with LG OLED TV 2026 Purchase",
            brand="LG",
            year=2026,
            model_code="OLED65C6",
            currency="CHF",
            price=2499.0
        )
        self.assertEqual(non_price_p, "Free Gift: SoundSuite/Soundbar with LG OLED TV")

        # Greek Soundbar special bundle
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Soundbar LG στα 119€",
            brand="LG",
            currency="EUR",
            price=799.0
        )
        self.assertEqual(non_price_p, "Bundle Offer: LG Soundbar at €119")

        # Frame Bezel gift
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Δώρο Frame στο Καλάθι",
            brand="Samsung",
            model_code="QE65LS03F",
            currency="EUR",
            price=1299.0
        )
        self.assertEqual(non_price_p, "Free Gift: The Frame Custom Bezel")

        # Warranty extension
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Δώρο Επέκταση Εγγύησης",
            brand="LG",
            currency="EUR",
            price=1099.0
        )
        self.assertEqual(non_price_p, "Extended Warranty: Free Extended Guarantee")

    def test_combined_price_and_non_price_promotions(self):
        # Swiss Combo: Cashback CHF 500 + Free SoundSuite
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Cashback CHF 500; Free SoundSuite/Soundbar with LG OLED TV 2026 Purchase",
            brand="LG",
            year=2026,
            model_code="OLED65C6",
            currency="CHF",
            price=2899.0
        )
        self.assertEqual(cb, 500)
        self.assertEqual(price_p, "Cashback: CHF 500")
        self.assertEqual(non_price_p, "Free Gift: SoundSuite/Soundbar with LG OLED TV")

        # Swiss Combo: Cashback and/or 26% Rabatt auf Soundbar QS700F
        orig, cb, price_p, non_price_p = classify_promotions(
            promo_raw="Cashback und oder 26% Rabatt auf Soundbar QS700F",
            title_raw="Cashback 300 CHF",
            brand="Samsung",
            year=2026,
            model_code="QE65S90H",
            currency="CHF",
            price=2199.0
        )
        self.assertEqual(cb, 300)
        self.assertEqual(price_p, "Cashback: CHF 300")
        self.assertEqual(non_price_p, "Bundle Offer: 26% Off Soundbar QS700F")

if __name__ == "__main__":
    unittest.main()
