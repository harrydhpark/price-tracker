# -*- coding: utf-8 -*-
import sys, re
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('currys_cards_debug.txt', 'r', encoding='utf-16le') as f:
    text = f.read()

def parse_currys_promo(t, name):
    # Remove soundbar lines to prevent false positive matching on TV offers
    t_no_sb = '\n'.join([line for line in t.split('\n') if not re.search(r'soundbar|soundbars', line, re.I)])
    
    # 1. Soundbar attach offer
    sb_offer = None
    if re.search(r'soundbars?.*50%', t, re.I) or re.search(r'50%.*soundbars?', t, re.I):
        sb_offer = "Up to 50% Off Soundbar w/ TV"
        
    # 2. TV Coupon Code / Direct Cut
    direct_cut_str = None
    code_off_m = re.search(r'Get\s*(?:£|짙|GBP)?\s*([\d,]+(?:\.\d{2})?)\s*off(?: marked price)?.*?(?:code|enter code)\s*([A-Z0-9]{3,15})', t_no_sb, re.I | re.DOTALL)
    code_pct_m = re.search(r'Get\s*(\d+)\s*%\s*off(?: marked price)?.*?(?:code|enter code)\s*([A-Z0-9]{3,15})', t_no_sb, re.I | re.DOTALL)
    
    if code_off_m:
        direct_cut_str = f"Direct Cut GBP {code_off_m.group(1)} (Code: {code_off_m.group(2)})"
    elif code_pct_m:
        direct_cut_str = f"Direct Cut {code_pct_m.group(1)}% (Code: {code_pct_m.group(2)})"
    else:
        code_m = re.search(r'(?:use|enter|with)\s*code\s*:?\s*([A-Z0-9]{3,15})', t_no_sb, re.I)
        if code_m:
            direct_cut_str = f"Voucher Code: {code_m.group(1)}"
            
    # 3. TV Price Drop (Was / Save)
    save_amt = re.search(r'Save £([\d,]+(?:\.\d{2})?)', t_no_sb)
    was_amt = re.search(r'Was £([\d,]+(?:\.\d{2})?)', t_no_sb)
    price_drop_str = None
    if was_amt and save_amt and not direct_cut_str:
        price_drop_str = f"Save GBP {save_amt.group(1)}; was GBP {was_amt.group(1)}"
    elif was_amt and not direct_cut_str:
        price_drop_str = f"was GBP {was_amt.group(1)}"
        
    # 4. TV Cashback
    cb_m = re.search(r'(?:Claim|Get|Up to)?\s*£(\d+)\s*cashback', t_no_sb, re.I)
    cb_str = None
    if cb_m and int(cb_m.group(1)) >= 10:
        cb_str = f"GBP {cb_m.group(1)} Cashback"
        
    promo_parts = [direct_cut_str, cb_str, price_drop_str, sb_offer]
    return '; '.join(filter(None, promo_parts)) or "None"

blocks = text.split('--- ITEM CARD ---')
for i, block in enumerate(blocks[1:6], 1):
    lines = block.strip().split('\n')
    name = lines[0] if lines else ''
    res = parse_currys_promo(block, name)
    print(f"CARD #{i}: {name[:60]}")
    print(f"  --> Promo: {res}\n")
