# -*- coding: utf-8 -*-



"""



Targeted Series Search & Inch-Expansion Scraper for Western Europe (Phase 1):



Countries:



- NL: MediaMarkt Netherlands (mediamarkt.nl)



- DE: MediaMarkt Germany (mediamarkt.de)



- ES: MediaMarkt Spain (mediamarkt.es)



- IT: MediaWorld Italy (mediaworld.it)



- FR: Fnac France (fnac.com)







Uses Firecrawl Stealth proxy API to execute targeted series searches,



recovering missing flagship OLED, MRGB, QNED/QLED, and UHD 4K models across all screen sizes.



Writes data/raw_{retailer}_{brand}.json from THIS RUN's results only (no carry-over, no lower-only rule).



"""







import os



import sys



import json



import re



import time



from datetime import datetime



from concurrent.futures import ThreadPoolExecutor



from curl_cffi import requests







sys.path.append(os.path.dirname(os.path.abspath(__file__)))



sys.stdout.reconfigure(encoding='utf-8')







ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))



DATA_DIR = os.path.join(ROOT_DIR, "data")



os.makedirs(DATA_DIR, exist_ok=True)



def _load_env_file():



    """Load key-value pairs from .env into os.environ if present."""



    env_path = os.path.join(ROOT_DIR, ".env")



    if os.path.isfile(env_path):



        try:



            with open(env_path, "r", encoding="utf-8-sig") as f:



                for line in f:



                    line = line.strip()



                    if line and not line.startswith("#") and "=" in line:



                        k, v = line.split("=", 1)



                        k = k.strip().lstrip("\ufeff")



                        v = v.strip().strip("'\"")



                        if k and k not in os.environ:



                            os.environ[k] = v



        except Exception:



            pass







_load_env_file()



FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "").strip()



FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v1/scrape"



MASTER_REGISTRY_PATH = os.path.join(DATA_DIR, "master_product_urls.json")







def update_master_registry(items, cc, retailer):



    if not os.path.exists(MASTER_REGISTRY_PATH):



        return



    master = None



    for attempt in range(5):



        try:



            with open(MASTER_REGISTRY_PATH, "r", encoding="utf-8") as f:



                master = json.load(f)



            break



        except Exception:



            time.sleep(0.5)



    if master is None:



        return



    added = 0



    for it in items:



        mc = it.get("model_code")



        url = it.get("url")



        if mc and url and mc != "Unknown":

            # Pan-European Blacklisted 3rd-Party Marketplace Guard

            u_lower = url.lower()

            if "mediamarkt" in u_lower or "mediaworld" in u_lower:

                m_pid = re.search(r'-(\d{8,10})\.html', url)

                if m_pid and (len(m_pid.group(1)) >= 9 or m_pid.group(1).startswith(('14', '15', '16', '17', '18'))):

                    continue

            if "offertype=marketplace" in u_lower:

                continue

            if "worten.pt" in u_lower and "seller=" in u_lower and "worten" not in u_lower.split("seller=")[1].split("&")[0]:

                continue

            if "emag.ro" in u_lower and ("/partener-" in u_lower or "seller_id=" in u_lower):

                continue



            clean_code = re.sub(r'[^A-Za-z0-9_-]', '', mc).upper()



            key = f"{cc}_{retailer.upper()}_{clean_code}"



            master[key] = {



                "country": cc,



                "retailer": retailer,



                "brand": it.get("brand", "").upper(),



                "model_code": mc,



                "year": it.get("year", 2026),



                "size": it.get("size", 55),



                "title": it.get("title", ""),



                "url": url,



                "last_updated": "2026-09-15"



            }



            added += 1



    if added > 0:



        tmp_path = MASTER_REGISTRY_PATH + f".tmp_{os.getpid()}"



        try:



            with open(tmp_path, "w", encoding="utf-8") as f:



                json.dump(master, f, ensure_ascii=False, indent=2)



            os.replace(tmp_path, MASTER_REGISTRY_PATH)



            print(f"  [MASTER REGISTRY] Registered/Updated {added} models for {cc} {retailer} into Master Registry!")



        except Exception:



            if os.path.exists(tmp_path):



                try:



                    os.remove(tmp_path)



                except Exception:



                    pass







# ==============================================================================



# Non-TV & Purge Filters



# ==============================================================================



NON_TV_KEYWORDS = [



    "SOUNDBAR", "SOUND BAR", "BARRE DE SON", "BARRA DE SONIDO", "BUNDLE",



    "MONITOR", "MONITEUR", "ODYSSEY", "ULTRAGEAR", "MYVIEW", "REMOTE", "TELECOMANDO",



    "FERNBEDIENUNG", "TELECOMMANDE", "PROJECTOR", "PROJEKTOR", "PROJECTEUR", "PROIETTORE",



    "BEAMER", "CABLE", "SUPPORT", "HALTERUNG", "WANDHALTERUNG", "STAENDER", "STAND",



    "CASQUE", "HEADPHONE", "KOPFHÖRER", "CUFFIE", "AURICULARES", "EARBUDS",



    "FRIDGE", "FREEZER", "REFRIGERATOR", "KÜHLSCHRANK", "FRIGORIFERO", "FRIGORIFICO",



    "WASHING MACHINE", "WASCHMASCHINE", "LAVATRICE", "LAVADORA", "DRYER", "TROCKNER",



    "ASCIUGATRICE", "SECADORA", "DISHWASHER", "GESCHIRRSPÜLER", "LAVASTOVIGLIE", "LAVAVAJILLAS",



    "OVEN", "BACKOFEN", "FORNO", "HORNO", "MICROWAVE", "MIKROWELLE", "MICROONDE", "MICROONDAS",



    "HOOVER", "VACUUM", "STAUBSAUGER", "ASPIRAPOLVERE", "ASPIRADORA", "TABLET", "GALAXY PHONE",



    "GALAXY", "DUAL SIM", "SMARTPHONE", "HANDY", "CELLULARE", "WATCH", "SMARTWATCH", "ZUBEHÖR", "ACCESSOIRE", "ACCESSORIO",



    "ACCESORIO", "KLIMAANLAGE", "CONDIZIONATORE", "AIRE ACONDICIONADO", "CLIMATISEUR"



]







TV_INDICATORS = [



    " TV", "SMART TV", "TELEVISION", "TÉLÉVISEUR", "TELEVISORE", "TELEVISOR",



    "OLED", "QNED", "NEO QLED", "THE FRAME", "THE SERIF", "STANBYME", "MINI LED", "4K", "UHD"



]







# ==============================================================================



# Price & Screen Size Guards



# ==============================================================================



def clean_numeric_price(val):



    if not val:



        return 0.0



    p = str(val).replace('€', '').replace('£', '').replace('CHF', '').replace('\xa0', '').replace('\u202f', ' ').strip()



    if re.match(r'^\d{1,3}\.\d{3}(?:,\d{2})?$', p):



        p = p.replace('.', '').replace(',', '.')



    elif re.match(r'^\d{1,3},\d{3}(?:\.\d{2})?$', p):



        p = p.replace(',', '')



    elif ',' in p:



        p = p.replace(',', '.')



    m = re.findall(r'(\d+(?:\.\d{2})?)', p)



    if m:



        try:



            v = float(m[0])



            return v if v >= 50.0 else 0.0



        except ValueError:



            pass



    return 0.0







def passes_price_guard(disp, size, price):



    if price < 80.0:



        return False



    d = disp.upper()



    # OLED



    if "OLED" in d:



        if size <= 48 and price < 500.0:



            return False



        if size == 55 and price < 700.0:



            return False



        if size == 65 and price < 950.0:



            return False



        if size >= 77 and price < 1400.0:



            return False



        if size >= 83 and price < 2000.0:



            return False



    # Micro RGB



    elif "MICRO RGB" in d or "MRGB" in d:



        if size <= 65 and price < 600.0:



            return False



        if size >= 75 and price < 1500.0:



            return False



        if size >= 98 and price < 8000.0:



            return False



    # QNED / QLED / Neo QLED



    elif any(x in d for x in ["QNED", "QLED", "NEO QLED", "MINI LED"]):



        if size <= 43 and price < 200.0:



            return False



        if size in [50, 55] and price < 280.0:



            return False



        if size >= 65 and price < 450.0:



            return False



        if size >= 75 and price < 700.0:



            return False



    # UHD 4K



    elif "UHD" in d or "LED" in d or "4K" in d:



        if size <= 43 and price < 120.0:



            return False



        if size >= 55 and price < 180.0:



            return False



    return True







# ==============================================================================



# Smart Parser for MediaMarkt / MediaWorld Markdown Dumps



# ==============================================================================



def parse_mediamarkt_markdown(md_text, brand):



    items = []



    card_chunks = re.split(r'(?:Añadir al carrito|In den Warenkorb|Aggiungi al carrello|Voeg toe aan winkelmandje|Kosárba\s*){1,2}', md_text)



    for card in card_chunks:



        m_link = re.search(r'\[\*\*([^\*\]]+)\*\*\]\((https?://www\.(?:mediamarkt|mediaworld)\.[a-z]{2}/[^\)]+/product/[^\)]+)\)', card, re.I)



        if not m_link:



            continue



        title = m_link.group(1).strip()



        url = m_link.group(2).strip()



        u_title = title.upper()



        



        # 1. Check brand



        if brand.upper() not in u_title and not any(k in u_title for k in ['OLED', 'QNED', 'S90', 'S95', 'C6', 'G6', 'B6']):



            continue



            



        # 2. Non-TV purge



        if any(x in u_title for x in NON_TV_KEYWORDS):



            continue



            



        # 3. Direct seller check (reject marketplace 9-digit -17/-18... IDs, /marketplace/ URLs and refurbished items)



        if re.search(r'-1[78]\d{7}\.html', url) or '/marketplace/' in url.lower() or 'REACONDICIONADO' in u_title:



            continue



            



        # 4. Cashback extraction (from full card including header badges)



        cashback = 0



        cb_m = re.search(r'(?:cashback|retour|terug|reembolso|rimborso)[:\s-]*(?:de|sichern|von|bis\s*zu)?\s*(?:CHF|€|EUR)?\s*(\d{2,4})', card, re.I)
        if not cb_m:
            cb_m = re.search(r'(?:CHF|€|EUR)?\s*(\d{2,4})\s*(?:CHF|€|EUR)?\s*(?:\.-|.–|[\.,\-])?\s*(?:cashback|retour|terug|reembolso|rimborso)', card, re.I)
        if not cb_m:
            cb_m = re.search(r'direct\s*cashback[^\d]*-\s*(?:CHF|€|EUR)?\s*(\d{2,4})', card, re.I)



        if cb_m:



            val = int(cb_m.group(1))



            if 10 <= val <= 3000 and val not in [2024, 2025, 2026]:



                cashback = val



                



        # 5. Price extraction (strip cashback, financing, shipping from price area after title)



        c_clean = re.sub(r'(?:cashback|retour|terug|reembolso|rimborso)\s*[:\-]?\s*(?:€|EUR)?\s*\d+\s*(?:€|EUR)?', '', card, flags=re.I)



        c_clean = re.sub(r'\d+\s*(?:€|EUR)?\s*(?:cashback|retour|terug|reembolso|rimborso)', '', c_clean, flags=re.I)



        after_title = c_clean[c_clean.find(url):]



        price_area = re.split(



            r'Otros vendedores|En \d+ cuotas|cuotas|financiado|plazos|\+\s*\d+[\.,]\d+|único|mensual|TIN|TAE|Entrega|Envío|Lieferung|Raten|Bezahle in|Vergleichspreis',



            after_title, flags=re.I



        )[0]



        



        has_discount = bool(re.search(r'-\d+%', price_area))



        p_matches = re.findall(r'(?:€|EUR|CHF|Ft)\s*([\d\.\s\xa0\u202f’\']+(?:,\d{2}|,–|-)?)|([\d\.\s\xa0\u202f’\']+(?:,\d{2}|,–|-)?)\s*(?:€|EUR|CHF|Ft)', price_area)



        found_prices = []



        for pm in p_matches:



            raw_p = (pm[0] or pm[1]).strip().replace(' ', '').replace('\xa0', '').replace('\u202f', '').replace('’', '').replace("'", '').replace('–', '').replace('-', '')



            if ',' in raw_p and '.' in raw_p:



                raw_p = raw_p.replace('.', '').replace(',', '.')



            elif '.' in raw_p and len(raw_p.split('.')[-1]) == 3:



                raw_p = raw_p.replace('.', '')



            elif ',' in raw_p:



                raw_p = raw_p.replace(',', '.')



            try:



                val = float(raw_p)



                if val >= 80.0 and (not found_prices or abs(found_prices[-1] - val) > 1):



                    found_prices.append(val)



            except ValueError:



                continue



                



        if not found_prices:



            continue



            



        if len(found_prices) >= 2 and (has_discount or found_prices[0] > found_prices[1]):



            orig_price = found_prices[0]



            price = found_prices[1]



        else:



            price = found_prices[0]



            orig_price = None



            



        if price < 80.0:



            continue



            



        promos = []



        if cashback > 0:



            if 'reembolso' in card.lower():



                promos.append(f"Reembolso €{cashback}")



            else:



                promos.append(f"Cashback: €{cashback}")



        if 'streaming' in card.lower():



            promos.append("Inkl. Streaming Content")



        if 'sound device' in card.lower() or 'zusatzprodukt' in card.lower():



            promos.append("Free Sound Device")



        if has_discount:



            pct_m = re.search(r'(-\d+%)', price_area)



            if pct_m:



                promos.append(f"Discount {pct_m.group(1)}")



        promo = "; ".join(promos) if promos else "None"



        



        # 6. Extract Size, Model Code, Year, Display Type



        rec = build_clean_record(brand, title, url, price, cashback, promo, orig_price=orig_price)



        if rec:



            items.append(rec)



            



    return items







# ==============================================================================



# Smart Parser for Fnac Markdown Dumps



# ==============================================================================



def parse_fnac_markdown(md_text, brand):



    items = []



    pattern = re.compile(



        r'\[(?:\*\*)?((?:TV\s+|SAMSUNG|LG)[^\]\*\n]+)(?:\*\*)?\]\((https?://(?:www\.)?fnac\.com/[^\)]+/a\d+/[^\)]*)\)(.*?)(?=\n!?\[(?:\*\*)?(?:TV\s+|SAMSUNG|LG)|\Z)',



        re.DOTALL | re.IGNORECASE



    )



    for m in pattern.finditer(md_text):



        title = m.group(1).strip()



        url = m.group(2).strip()



        chunk = m.group(3)



        u_title = title.upper()



        if brand.upper() not in u_title and not any(k in u_title for k in ['OLED', 'QNED', 'S90', 'S95', 'C6', 'G6', 'B6']):



            continue



        if any(x in u_title for x in NON_TV_KEYWORDS):



            continue



            



        t_chunk = chunk.replace('\u202f', ' ').replace('\xa0', ' ').replace('\u2009', ' ')



        t_chunk = re.sub(r'\b\d+\s*€\s*(?:remboursés?|remise|réduction|d\'économie)[^\n]*', '', t_chunk, flags=re.IGNORECASE)



        t_chunk = re.sub(r'dès\s*[\d\s,.]+\s*€\s*\/\s*mois', '', t_chunk, flags=re.IGNORECASE)



        p_matches = re.findall(r'(\d+[\d\s]*[,\.]\d{2}|\d+[\d\s]*)\s*€', t_chunk)



        price = 0.0



        cleaned_prices = []



        for raw in p_matches:



            cleaned = raw.strip().replace(' ', '').replace(',', '.')



            try:



                v = float(cleaned)



                if v >= 100.0:



                    cleaned_prices.append(v)



            except:



                pass



        if cleaned_prices:



            price = cleaned_prices[-1]



            



        if price < 80.0:



            continue



            



        m_sz = re.search(r'Taille de l\'écran \(pouces\)\s*\*\*(\d{2,3})\s*"\*\*', chunk)



        if m_sz:



            title += f" {m_sz.group(1)}\""



            



        rec = build_clean_record(brand, title, url, price, 0, "None")



        if rec:



            items.append(rec)



    return items







# ==============================================================================



# Universal Product Clean Record Builder



# ==============================================================================



def build_clean_record(brand, title, url, price, cashback, promo, orig_price=None):



    u_title = title.upper()



    



    # 1. Screen Size



    size = 0



    # Inch pattern



    m_inch = re.search(r'\b(115|100|98|97|86|85|83|77|75|70|65|55|50|48|43|42|40|32|27|24)[\s"”\'-]*(?:INCH|ZOLL|POUCES|POLLICI|\"|\b)', u_title)



    if m_inch:



        size = int(m_inch.group(1))



    if not size:



        m_cm = re.search(r'\b(\d{2,3})\s*CM\b', u_title)



        if m_cm:



            cm_val = int(m_cm.group(1))



            if cm_val > 100:



                size = int(round(cm_val / 2.54))



            elif cm_val >= 22:



                size = cm_val



                



    # 2. Model Code



    model_code = "Unknown"



    if brand.upper() == "LG":



        # Check specific series prefixes first (QNED, NANO, UHD NU/UA, etc.)



        m_lg = re.search(r'\b(\d{2,3}(?:QNED|NANO|MRGB|LX|NU|UA|UT|UR|UQ|LB|QLED)\w*)\b', u_title)



        if m_lg:



            model_code = m_lg.group(1)



        else:



            # LG OLED (OLEDxxC6, xxC6, OLEDxxG6, xxG6, OLEDxxB6, xxB6)



            m_oled = re.search(r'\b(OLED\d{2,3}[A-Z0-9]*|(?:[4-9]\d|1[0-1]\d)[CGB][56][A-Z0-9]*)\b', u_title)



            if m_oled:



                model_code = m_oled.group(1)



        # Smart fallback for series



        if model_code == "Unknown":



            for w in u_title.split():



                cw = re.sub(r'[^\w-]', '', w)



                if any(char.isdigit() for char in cw) and len(cw) >= 5 and not any(j in cw for j in ["TV", "OLEDLG", "LEDLG"]):



                    model_code = cw



                    break



    else: # Samsung



        for w in u_title.split():



            cw = re.sub(r'[^\w-]', '', w)



            if any(cw.startswith(p) for p in ["GQ", "TQ", "QE", "UE", "GU", "MRE", "TU", "TMR"]):



                model_code = cw



                break



        if model_code == "Unknown":



            patterns = [



                r'\b(TMR\d{2}[A-Z0-9]+)\b', r'\b(TU\d{2}[A-Z0-9]+)\b',



                r'\b(QN\d{2,3}[FH])\b', r'\b(S\d{2,3}[FH])\b', r'\b(U\d{3,4}[FH])\b',



                r'\b(M\d{2,3}[FH])\b', r'\b(R\d{2,3}[FH])\b', r'\b(LS03[A-Z]{1,2})\b',



                r'\b(MR\d{2,3}[FH])\b'



            ]



            for pat in patterns:



                m_pat = re.search(pat, u_title)



                if m_pat:



                    ser = m_pat.group(1)



                    if ser.startswith('TMR') or ser.startswith('TU'):



                        model_code = ser



                    elif ser.startswith('S') or ser.startswith('QN') or ser.startswith('LS'):



                        model_code = f"QE{size or 55}{ser}"



                    elif ser.startswith('U') or ser.startswith('M'):



                        model_code = f"UE{size or 55}{ser}"



                    elif ser.startswith('R') or ser.startswith('MR'):



                        model_code = f"MRE{size or 55}{ser}"



                    break



                    



    # Re-verify size from model code if explicit



    if model_code != "Unknown":



        c_nums = re.findall(r'\d+', model_code)



        if c_nums and len(c_nums[0]) in [2, 3]:



            parsed_sz = int(c_nums[0])



            if parsed_sz in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27]:



                size = parsed_sz



                



    if not model_code or model_code == "Unknown":



        return None



        



    if not size:



        size = 55



    if size < 22:



        return None



        



    # 3. Model Year Classification (Strict 2025/2026 only)



    year = None



    if brand.upper() == "SAMSUNG":



        if re.search(r'[A-Z0-9]{2}\d{2}[A-Z0-9]*D\b', model_code) or any(x in model_code for x in ["S90D", "S95D", "QN90D", "Q60D", "Q70D", "Q80D", "DU7", "DU8"]):



            return None # Reject 2024



        if "FUXX" in model_code:



            year = 2025



        elif len(model_code) > 3 and "H" in model_code[2:]:



            year = 2026



        elif len(model_code) > 3 and "F" in model_code[2:]:



            year = 2025



        elif "2026" in u_title:



            year = 2026



        elif "2025" in u_title:



            year = 2025



    elif brand.upper() == "LG":



        if any(x in model_code for x in ["C4", "G4", "B4", "M4", "UA73", "UT8", "LQ6"]):



            return None # Reject 2024



        if any(x in model_code for x in ["C6", "G6", "B6", "W6", "M6", "QNED86B", "QNED81B", "QNED80B", "QNED87B", "QNED72B", "QNED71B", "QNED70B", "MRGB87B", "MRGB96B", "27LX6", "NU850", "NU85", "NU800", "NU80"]):



            year = 2026



        elif any(x in model_code for x in ["C5", "G5", "B5", "W5", "M5", "QNED86A", "QNED80A", "QNED87A", "QNED72A", "QNED70A", "NANO81A", "QNED93A", "QNED84A", "UA75"]):



            year = 2025



        elif "2026" in u_title:



            year = 2026



        elif "2025" in u_title:



            year = 2025



            



    if year not in [2025, 2026]:



        return None



        



    # 4. Display Type



    display_type = "LED"



    c_up = model_code.upper()



    if brand.upper() == "SAMSUNG":



        if "OLED" in c_up or any(x in c_up for x in ["S90", "S91", "S92", "S93", "S94", "S95", "S99", "S85", "S83"]):



            display_type = "OLED"



        elif "MRE" in c_up or "MRGB" in c_up or "TMR" in c_up:



            display_type = "Micro RGB"



        elif "QN" in c_up:



            display_type = "Neo QLED"



        elif any(x in c_up for x in ["M70", "M72", "M74", "M80", "M82", "M84"]) or "MINI LED" in u_title:



            display_type = "Mini LED"



        elif "Q" in c_up or "LS" in c_up:



            display_type = "QLED"



        elif any(x in c_up for x in ["U8", "UA", "UT", "UR", "UQ"]):



            display_type = "UHD 4K"



    elif brand.upper() == "LG":



        if "MRGB" in c_up or "MRGB" in u_title:



            display_type = "Micro RGB"



        elif "QNED" in c_up or "QNED" in u_title:



            display_type = "QNED"



        elif any(x in c_up for x in ["NU90", "NU85", "NU80", "NU800", "NU850", "UA75", "UA77", "UT", "UR", "UQ", "LQ", "LB"]):



            display_type = "UHD 4K"



        elif "NANO" in c_up:



            display_type = "NanoCell"



        elif "OLED" in c_up or "OLED" in u_title or re.search(r'\b(?:OLED)?(?:[4-9]\d)[BCG][456]\b', c_up):



            display_type = "OLED evo" if ("EVO" in u_title or any(x in c_up for x in ["G5", "G6", "C5", "C6"])) else "OLED"



        elif "LX" in c_up or "STANBYME" in c_up:



            display_type = "Lifestyle"



            



    # 5. Price Guard Verification



    if not passes_price_guard(display_type, size, price):



        return None



        



    return {



        "brand": "Samsung" if brand.upper() == "SAMSUNG" else "LG",



        "year": year,



        "display": display_type,



        "display_type": display_type,



        "size": size,



        "model_code": model_code,



        "price": price,



        "orig_price": orig_price if orig_price else price,



        "shipping": "Free",



        "cashback": cashback,



        "promo": promo,



        "title": title,



        "url": url,



        "link": url



    }







# ==============================================================================



# Zero-Firecrawl 2-Stage In-Browser DOMParser Batch Executor (StealthySession)



# ==============================================================================



def parse_dom_whole_dec(whole_str, dec_str):



    if not whole_str:



        return 0.0



    w_digits = re.sub(r'[^\d]', '', str(whole_str))



    if not w_digits:



        return 0.0



    d_digits = re.sub(r'[^\d]', '', str(dec_str or ''))



    val = float(w_digits) + (float(d_digits[:2]) / 100.0 if d_digits else 0.0)



    return val if val >= 50.0 else 0.0







def parse_json_ld_product(lds_list):



    ld_info = {"price": 0.0, "avail": "", "mpn": "", "name": "", "brand": ""}



    for raw in (lds_list or []):



        if not raw or "Product" not in raw:



            continue



        try:



            data = json.loads(raw)



        except Exception:



            continue



        objs = data if isinstance(data, list) else [data]



        for obj in objs:



            if not isinstance(obj, dict):



                continue



            if obj.get("@type") == "Product" or "Product" in str(obj.get("@type", "")):



                if not ld_info["name"]:



                    ld_info["name"] = str(obj.get("name") or "")



                if not ld_info["mpn"]:



                    ld_info["mpn"] = str(obj.get("mpn") or obj.get("model") or obj.get("sku") or "")



                b = obj.get("brand")



                if isinstance(b, dict):



                    ld_info["brand"] = str(b.get("name") or "")



                elif isinstance(b, str):



                    ld_info["brand"] = b



                offers = obj.get("offers")



                if isinstance(offers, list):



                    offers = offers[0] if offers else {}



                if isinstance(offers, dict):



                    if "offers" in offers and isinstance(offers["offers"], dict):



                        offers = offers["offers"]



                    p = clean_numeric_price(offers.get("price") or offers.get("lowPrice"))



                    if p >= 50.0:



                        ld_info["price"] = p



                    avail = str(offers.get("availability") or "")



                    if avail:



                        ld_info["avail"] = avail



    return ld_info







def extract_cashback_and_promo(badges_list, price, orig_price):



    cashback = 0



    direct_cut = 0



    promos = []



    badge_text = " | ".join(badges_list or [])



    cb_keywords = r'(?:cashback|cash\s*back|claim\s*back|reembolso|rimborso|retour|terug|rückvergütung|ruckvergutung|remise\s*différée|remboursement|odr|zwrot|kasa\s*wraca|återbäring|aterbaring|visszatérítés|visszaterites|επιστροφή|epistrofi|restituire)'



    curr_pats = r'(?:chf|eur|gbp|sek|czk|huf|pln|ron|kr|€|£|zł|lei)?'



    cb_m = re.search(cb_keywords + r'[:\s-]*(?:von|bis\s*zu|sichern|de|na\s*konto)?\s*' + curr_pats + r'\s*(\d{2,4})', badge_text, re.I)
    if not cb_m:
        cb_m = re.search(curr_pats + r'\s*(\d{2,4})\s*' + curr_pats + r'\s*(?:\.-|.–|[\.,\-])?\s*' + cb_keywords, badge_text, re.I)
    if not cb_m:
        cb_m = re.search(r'direct\s*cashback[^\d]*-\s*' + curr_pats + r'\s*(\d{2,4})', badge_text, re.I)



    if cb_m:



        val = int(cb_m.group(1))



        if val in (1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1600, 1700, 1800):



            val -= 1000



        if 10 <= val <= 3000 and val not in [2024, 2025, 2026]:



            cashback = val



            curr_sym = "CHF " if "chf" in badge_text.lower() else "€"
            if 'reembolso' in badge_text.lower():
                promos.append(f"Reembolso: {curr_sym}{cashback}")
            elif 'rimborso' in badge_text.lower():
                promos.append(f"Rimborso: {curr_sym}{cashback}")
            else:
                promos.append(f"Cashback: {curr_sym}{cashback}")



    # Direct Cut / Instant discount patterns

    dc_pats = [



        r'Save\s*(?:GBP|£)\s*(\d+)',
        r'-\s*(?:CHF|EUR|€)?\s*(\d+)(?:\.-|.–|[\.,\-])?\s*(?:Rabatt|Direktabzug|Sofortrabatt)',
        r'(?:CHF|EUR|€)?\s*(\d+)(?:\.-|.–|[\.,\-])?\s*(?:Rabatt|Direktabzug|Sofortrabatt)',
        r'(?:Direktabzug|Sofortrabatt|Rabatt|Gutschein)[:\s-]*(?:von|bis\s*zu)?\s*(?:CHF|EUR|€)?\s*(\d+)',



        r'(?:Direktabzug|Sofortrabatt|Gutschein)[:\s-]*(?:von|bis\s*zu)?\s*(?:CHF|EUR|€)?\s*(\d+)',



        r'Remise\s*immédiate[:\s-]*(?:de)?\s*(?:EUR|€)?\s*(\d+)',



        r'Sconto\s*(?:subito\s*)?(?:a\s*carrello)?[:\s-]*(?:di)?\s*(?:EUR|€)?\s*(\d+)',



        r'(?:Descuento|Desconto)\s*direto[:\s-]*(?:de)?\s*(?:EUR|€)?\s*(\d+)',



        r'Directe\s*korting[:\s-]*(?:van)?\s*(?:EUR|€)?\s*(\d+)',



        r'(?:Rabat|Zniżka)[:\s-]*(\d+)\s*(?:zł|pln)',



        r'Κέρδος\s*(\d+)\s*€',



        r'Card\s*cadou[:\s-]*(\d+)',



    ]



    for p in dc_pats:



        dm = re.search(p, badge_text, re.I)



        if dm:



            d_val = int(dm.group(1))



            if 10 <= d_val <= 3000 and d_val not in [2024, 2025, 2026]:



                direct_cut = d_val



                curr_sym = "CHF " if "chf" in badge_text.lower() else "€"
                if cashback != direct_cut:
                    promos.append(f"Direct Cut: {curr_sym}{direct_cut}")



                break



    if cashback > 0 and direct_cut > 0 and cashback == direct_cut:
        total_deduction = cashback
    else:
        total_deduction = cashback + direct_cut



    if orig_price and orig_price > price + 1.0:



        pct = int(round((1.0 - price / orig_price) * 100))



        if 1 <= pct <= 75:



            promos.append(f"Discount -{pct}%")



    return total_deduction, ("; ".join(promos) if promos else "None")







def scrape_mediamarkt_country_stealthy(cc, retailer, country_queries, master_data):



    from scrapling.fetchers import StealthySession



    search_urls = []



    seen_s = set()



    for _, _, brand, q_label, u in country_queries:



        for pg in (1, 2):



            sep = "&" if "?" in u else "?"



            full_u = f"{u}{sep}page={pg}" if "page=" not in u else u



            if full_u not in seen_s:



                seen_s.add(full_u)



                search_urls.append(full_u)







    # Load Master Registry URLs for this country



    master_by_url = {}



    master_pdp_urls = []



    for k, v in master_data.items():



        if v.get("country") == cc and v.get("url"):



            u = v["url"].split("?")[0]



            u_low = u.lower()



            if "mediamarkt." not in u_low and "mediaworld." not in u_low:



                continue



            if "/marketplace/" in u_low:



                continue



            if "/marketplace/" in u_low:



                continue



            if cc not in ("IT", "CH") and re.search(r'-1[78]\d{7}\.html', u):



                continue



            # Prefer keeping entry with longer/more specific model_code if duplicate URL exists



            if u not in master_by_url or len(str(v.get("model_code", ""))) > len(str(master_by_url[u].get("model_code", ""))):



                master_by_url[u] = v



            if u not in master_pdp_urls:



                master_pdp_urls.append(u)







    # Interleave Samsung and LG master URLs so neither brand sits entirely at the tail



    sam_urls = [u for u in master_pdp_urls if str(master_by_url[u].get("brand", "")).upper() == "SAMSUNG"]



    lg_urls = [u for u in master_pdp_urls if str(master_by_url[u].get("brand", "")).upper() != "SAMSUNG"]



    interleaved_master = []



    for i in range(max(len(sam_urls), len(lg_urls))):



        if i < len(sam_urls):



            interleaved_master.append(sam_urls[i])



        if i < len(lg_urls):



            interleaved_master.append(lg_urls[i])



    master_pdp_urls = interleaved_master







    print(f"\n  🚀 [{cc} - {retailer}] Starting Zero-Firecrawl 2-Stage In-Browser Batch:")



    print(f"     Search URLs: {len(search_urls)} | Registered Master PDPs: {len(master_pdp_urls)}", flush=True)







    payload = {



        "searchUrls": search_urls,



        "masterPdpUrls": master_pdp_urls,



        "allow9Digit": (cc in ("IT", "CH")),



    }



    res_holder = {}







    def two_stage_action(page):



        js = """



        async (payload) => {



            const parser = new DOMParser();



            const searchUrls = payload.searchUrls || [];



            const masterPdpUrls = payload.masterPdpUrls || [];



            const masterSet = new Set(masterPdpUrls);



            const allow9Digit = !!payload.allow9Digit;



            const discoveredPdps = new Set(masterPdpUrls);



            const searchCards = {};



            const sleep = (ms) => new Promise(r => setTimeout(r, ms));







            async function fetchHtml(u, ms) {



                for (let attempt = 0; attempt < 2; attempt++) {



                    const ctrl = new AbortController();



                    let timer = null;



                    const timeoutPromise = new Promise(resolve => {



                        timer = setTimeout(() => {



                            try { ctrl.abort(); } catch (e) {}



                            resolve({status: 0, html: '', err: 'timeout'});



                        }, ms);



                    });



                    const workPromise = (async () => {



                        try {



                            const r = await fetch(u, {credentials: 'include', signal: ctrl.signal});



                            if (r.status === 200) {



                                const html = await r.text();



                                return {status: 200, html: html};



                            }



                            return {status: r.status, html: ''};



                        } catch (e) {



                            return {status: 0, html: '', err: String(e)};



                        }



                    })();



                    const res = await Promise.race([workPromise, timeoutPromise]);



                    if (timer) clearTimeout(timer);



                    if (res.status === 200 || res.status === 404 || res.status === 410 || res.err === 'timeout') {



                        return res;



                    }



                    if (attempt === 0) await sleep(350);



                    else return res;



                }



                return {status: 0, html: ''};



            }







            // Stage A: Fetch search pages in parallel batches



            const batchA = 8;



            for (let i = 0; i < searchUrls.length; i += batchA) {



                const slice = searchUrls.slice(i, i + batchA);



                await Promise.all(slice.map(async (u) => {



                    const res = await fetchHtml(u, 8500);



                    if (res.status !== 200 || !res.html) return;



                    const doc = parser.parseFromString(res.html, 'text/html');



                    doc.querySelectorAll('article').forEach(art => {



                        const a = art.querySelector('a[href*="/product/"]');



                        if (!a) return;



                        let href = a.getAttribute('href') || '';



                        if (href.startsWith('/')) href = location.origin + href;



                        href = href.split('?')[0];



                        if (!href.includes('/product/')) return;



                        if (href.toLowerCase().includes('/marketplace/')) return;



                        if (!allow9Digit && /-1[78]\\d{7}\\.html/.test(href)) return;

                        if (href.toLowerCase().includes('/marketplace/')) return;



                        discoveredPdps.add(href);



                        const titleEl = art.querySelector('[data-test="product-title"]') || art.querySelector('h2') || art.querySelector('h3');



                        const wholeEl = art.querySelector('[data-test="branded-price-whole-value"]');



                        const decEl = art.querySelector('[data-test="branded-price-decimal-value"]');



                        const rrpEl = art.querySelector('[data-test="mms-strike-price-type-rrp"], [data-test*="strike-price"]');



                        const rawBadges = Array.from(art.querySelectorAll('[data-test*="badge"], [data-test*="promotion"], [class*="badge"], [class*="Badge"], [class*="pill"]')).map(e => e.textContent.trim()).filter(Boolean);
                        const discountLines = (art.innerText || '').split(/\\r?\\n/).map(l => l.trim()).filter(l => /(?:cashback|rabatt|direktabzug|sofortrabatt)/i.test(l) && l.length < 50);
                        const badges = Array.from(new Set([...rawBadges, ...discountLines])).slice(0, 8);



                        searchCards[href] = {



                            url: href,



                            title: titleEl ? titleEl.textContent.trim() : a.textContent.trim(),



                            whole: wholeEl ? wholeEl.textContent.trim() : '',



                            dec: decEl ? decEl.textContent.trim() : '',



                            rrp: rrpEl ? rrpEl.textContent.trim() : '',



                            badges: badges



                        };



                    });



                }));



                await sleep(120);



            }







            // Stage B: Fetch PDP URLs (skip URLs already priced on a live Stage A search card if they are in masterSet or have valid title)



            const allPdps = Array.from(discoveredPdps);



            const pdpResults = {};



            const statusCounts = {};



            const toFetch = [];



            for (const u of allPdps) {



                const sc = searchCards[u];



                const hasLiveCardPrice = sc && sc.whole && parseInt(sc.whole.replace(/[^0-9]/g, '') || '0', 10) >= 80;



                if (hasLiveCardPrice && (masterSet.has(u) || (sc.title && sc.title.length >= 12))) {



                    pdpResults[u] = {status: 206, fromSearchCard: true};



                    statusCounts[206] = (statusCounts[206] || 0) + 1;



                } else {



                    toFetch.push(u);



                }



            }







            const batchB = 10;



            for (let i = 0; i < toFetch.length; i += batchB) {



                const slice = toFetch.slice(i, i + batchB);



                await Promise.all(slice.map(async (u) => {



                    const res = await fetchHtml(u, 6500);



                    statusCounts[res.status] = (statusCounts[res.status] || 0) + 1;



                    if (res.status !== 200 || !res.html) {



                        pdpResults[u] = {status: res.status, err: res.err || ''};



                        return;



                    }



                    const doc = parser.parseFromString(res.html, 'text/html');



                    const titleEl = doc.querySelector('[data-test="product-title"]') || doc.querySelector('h1');



                    const pBox = doc.querySelector('[data-test="mms-product-price"]') || doc;



                    const wholeEl = pBox.querySelector('[data-test="branded-price-whole-value"]');



                    const decEl = pBox.querySelector('[data-test="branded-price-decimal-value"]');



                    const rrpEl = pBox.querySelector('[data-test="mms-strike-price-type-rrp"], [data-test*="strike-price"]');



                    const lds = Array.from(doc.querySelectorAll('script[type="application/ld+json"]')).map(s => s.textContent);



                    const rawBadges = Array.from(doc.querySelectorAll('[data-test*="badge"], [data-test*="promotion"], [class*="badge"], [class*="Badge"], [class*="pill"]')).map(e => e.textContent.trim()).filter(Boolean);
                    const discountLines = (doc.body ? doc.body.innerText || '' : '').split(/\\r?\\n/).map(l => l.trim()).filter(l => /(?:cashback|rabatt|direktabzug|sofortrabatt)/i.test(l) && l.length < 50);
                    const badges = Array.from(new Set([...rawBadges, ...discountLines])).slice(0, 8);



                    pdpResults[u] = {



                        status: 200,



                        title: titleEl ? titleEl.textContent.trim() : '',



                        whole: wholeEl ? wholeEl.textContent.trim() : '',



                        dec: decEl ? decEl.textContent.trim() : '',



                        rrp: rrpEl ? rrpEl.textContent.trim() : '',



                        lds: lds,



                        badges: badges



                    };



                }));



                await sleep(160);



            }



            return {



                searchCardsCount: Object.keys(searchCards).length,



                totalPdps: allPdps.length,



                statusCounts: statusCounts,



                searchCards: searchCards,



                pdpResults: pdpResults



            };



        }



        """



        res = page.evaluate(js, payload)



        if isinstance(res, dict):



            res_holder.update(res)







    t_c = time.time()



    entry_url = search_urls[0]



    with StealthySession(headless=False, solve_cloudflare=True, timeout=120000) as session:



        session.fetch(



            entry_url,



            solve_cloudflare=True,



            wait=2500,



            page_action=two_stage_action



        )







    pdp_results = res_holder.get("pdpResults", {})



    search_cards = res_holder.get("searchCards", {})



    status_counts = res_holder.get("statusCounts", {})



    print(f"     [{cc}] In-browser batch done in {time.time() - t_c:.1f}s | searchCards={len(search_cards)} | totalPdps={len(pdp_results)} | statuses={status_counts}", flush=True)







    def finalize_with_master_meta(rec, m_meta, brand_str, title, u, price, cashback, promo, orig_p):



        mc_m = str(m_meta.get("model_code") or "").strip()



        # Guard against the old 100" QN80H mis-registered as QE55QN80H



        if mc_m.upper() == "QE55QN80H" and ("100" in title or "100" in u or price >= 2500):



            mc_m = "QE100QN80H"



        if not rec and mc_m and mc_m.upper() != "UNKNOWN":



            b_clean = "Samsung" if "SAMSUNG" in brand_str.upper() else "LG"



            sz = int(m_meta.get("size") or 0)



            if not sz:



                c_nums = re.findall(r'\d+', mc_m)



                if c_nums and int(c_nums[0]) in [115, 100, 98, 97, 86, 85, 83, 77, 75, 70, 65, 55, 50, 48, 43, 42, 40, 32, 27, 24]:



                    sz = int(c_nums[0])



            if not sz:



                sz = 55



            yr = m_meta.get("year")



            if yr not in (2025, 2026):



                yr = 2026 if any(x in mc_m.upper() for x in ("H", "B6", "C6", "G6", "86B", "80B", "72B", "71B", "70B", "NU8")) else 2025



            disp = m_meta.get("display_type") or m_meta.get("display") or "LED"



            if passes_price_guard(disp, sz, price):



                rec = {



                    "brand": b_clean,



                    "year": yr,



                    "display": disp,



                    "display_type": disp,



                    "size": sz,



                    "model_code": mc_m,



                    "price": price,



                    "orig_price": orig_p if orig_p else price,



                    "shipping": "Free",



                    "cashback": cashback,



                    "promo": promo,



                    "title": title or m_meta.get("title") or f"{b_clean} {mc_m}",



                    "url": u,



                    "link": u



                }



        elif rec and mc_m and mc_m.upper() != "UNKNOWN":



            # Keep the canonical model_code from master registry so historical continuity is preserved



            rec["model_code"] = mc_m



            if mc_m == "QE100QN80H":



                rec["size"] = 100



        return rec







    by_brand = {"Samsung": [], "LG": []}



    for u, pdata in pdp_results.items():



        status = pdata.get("status", 0)



        scard = search_cards.get(u, {})



        m_meta = master_by_url.get(u, {})







        if status != 200:



            if not scard:



                continue



            dom_p = parse_dom_whole_dec(scard.get("whole"), scard.get("dec"))



            if dom_p < 80.0:



                continue



            rrp_p = clean_numeric_price(scard.get("rrp"))



            orig_p = rrp_p if rrp_p > dom_p else dom_p



            title = scard.get("title") or m_meta.get("title") or ""



            if m_meta.get("model_code") and m_meta["model_code"].upper() not in title.upper():



                title = f"{title} {m_meta['model_code']}".strip()



            raw_b = (m_meta.get("brand") or "").upper()



            if "SAMSUNG" in raw_b or "SAMSUNG" in title.upper():



                brand_guess = "SAMSUNG"



            elif "LG" in raw_b or "LG" in title.upper() or any(k in title.upper() for k in ("OLED", "QNED", "NANO")):



                brand_guess = "LG"



            else:



                continue



            cashback, promo = extract_cashback_and_promo(scard.get("badges"), dom_p, orig_p)



            rec = build_clean_record(brand_guess, title, u, dom_p, cashback, promo, orig_price=orig_p)



            rec = finalize_with_master_meta(rec, m_meta, brand_guess, title, u, dom_p, cashback, promo, orig_p)



            if rec:



                if cc not in ("IT", "CH") and (bool(re.search(r'-1[78]\d{7}\.html', u)) or "/marketplace/" in u.lower()):



                    continue



                rec["_source_type"] = "list"



                rec["_is_9digit"] = False



                by_brand[rec["brand"]].append(rec)



            continue







        ld_info = parse_json_ld_product(pdata.get("lds"))



        avail_low = ld_info["avail"].lower()



        if any(x in avail_low for x in ("outofstock", "discontinued", "soldout")):



            continue







        dom_p = parse_dom_whole_dec(pdata.get("whole"), pdata.get("dec"))



        price = dom_p if dom_p >= 80.0 else ld_info["price"]



        if price < 80.0 and scard:



            price = parse_dom_whole_dec(scard.get("whole"), scard.get("dec"))



        if price < 80.0:



            continue







        rrp_p = clean_numeric_price(pdata.get("rrp") or scard.get("rrp"))



        orig_p = rrp_p if rrp_p > price else price







        title_parts = [pdata.get("title") or "", ld_info.get("name") or "", scard.get("title") or "", m_meta.get("title") or ""]



        title = next((t for t in title_parts if t), "")



        if ld_info.get("mpn") and ld_info["mpn"].upper() not in title.upper():



            title = f"{title} {ld_info['mpn']}".strip()



        if m_meta.get("model_code") and m_meta["model_code"].upper() not in title.upper():



            title = f"{title} {m_meta['model_code']}".strip()







        u_title = title.upper()



        if any(x in u_title for x in NON_TV_KEYWORDS):



            continue



        if "REACONDICIONADO" in u_title or "RICONDIZIONATO" in u_title or "REFURBISHED" in u_title:



            continue







        raw_brand = (ld_info.get("brand") or m_meta.get("brand") or "").upper()



        if "SAMSUNG" in raw_brand:



            brand_str = "SAMSUNG"



        elif "LG" in raw_brand:



            brand_str = "LG"



        else:



            brand_str = ""



        if brand_str not in ("SAMSUNG", "LG"):



            if "SAMSUNG" in u_title or any(k in u_title for k in ("NEO QLED", "S90", "S95", "S85", "QN8", "QN9")):



                brand_str = "SAMSUNG"



            elif "LG" in u_title or any(k in u_title for k in ("OLED", "QNED", "C6", "G6", "B6", "C5", "G5")):



                brand_str = "LG"



        if brand_str not in ("SAMSUNG", "LG"):



            continue







        badges = (pdata.get("badges") or []) + (scard.get("badges") or [])



        cashback, promo = extract_cashback_and_promo(badges, price, orig_p)



        rec = build_clean_record(brand_str, title, u, price, cashback, promo, orig_price=orig_p)



        if not rec and m_meta.get("model_code"):



            fallback_title = f"{brand_str} {m_meta.get('size', 55)}\" {m_meta.get('model_code')} {m_meta.get('year', 2026)} TV {title}"



            rec = build_clean_record(brand_str, fallback_title, u, price, cashback, promo, orig_price=orig_p)



        rec = finalize_with_master_meta(rec, m_meta, brand_str, title, u, price, cashback, promo, orig_price=orig_p) if False else finalize_with_master_meta(rec, m_meta, brand_str, title, u, price, cashback, promo, orig_p)



        if rec:



            if cc not in ("IT", "CH") and (bool(re.search(r'-1[78]\d{7}\.html', u)) or "/marketplace/" in u.lower()):



                continue



            rec["_source_type"] = "pdp"



            rec["_is_9digit"] = False



            by_brand[rec["brand"]].append(rec)







    # Sort so 7-digit direct seller URLs and PDP sources come first



    for b_key in ("Samsung", "LG"):



        by_brand[b_key].sort(key=lambda x: (1 if x.get("_is_9digit") else 0, 0 if x.get("_source_type") == "pdp" else 1))







    print(f"     [{cc}] Extracted valid in-stock TVs -> Samsung: {len(by_brand['Samsung'])}, LG: {len(by_brand['LG'])}", flush=True)



    return by_brand











def run_targeted_western_eu(countries=None, workers=3, queries=None):



    print("================================================================================")



    print(" 🇪🇺 STARTING STAGE 1: ZERO-FIRECRAWL WESTERN EU IN-BROWSER STEALTHY SURVEY ")



    print(" Core Countries: NL (MediaMarkt), DE (MediaMarkt), AT (MediaMarkt), ES (MediaMarkt), IT (MediaWorld)")



    print("================================================================================")



    



    TARGET_MATRIX = [



        # 1. Netherlands (MediaMarkt NL)



        ("NL", "MediaMarkt", "Samsung", "OLED", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+OLED"),



        ("NL", "MediaMarkt", "Samsung", "Neo QLED", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+Neo+QLED"),



        ("NL", "MediaMarkt", "Samsung", "Mini LED", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+Mini+LED"),



        ("NL", "MediaMarkt", "Samsung", "U80", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+U80"),



        ("NL", "MediaMarkt", "Samsung", "Micro RGB", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+Micro+RGB"),



        ("NL", "MediaMarkt", "Samsung", "2026", "https://www.mediamarkt.nl/nl/search.html?query=Samsung+2026"),



        ("NL", "MediaMarkt", "LG", "OLED", "https://www.mediamarkt.nl/nl/search.html?query=LG+OLED"),



        ("NL", "MediaMarkt", "LG", "C6", "https://www.mediamarkt.nl/nl/search.html?query=LG+C6"),



        ("NL", "MediaMarkt", "LG", "QNED", "https://www.mediamarkt.nl/nl/search.html?query=LG+QNED"),



        ("NL", "MediaMarkt", "LG", "NU8", "https://www.mediamarkt.nl/nl/search.html?query=LG+NU8"),



        ("NL", "MediaMarkt", "LG", "MRGB", "https://www.mediamarkt.nl/nl/search.html?query=LG+MRGB"),



        ("NL", "MediaMarkt", "LG", "2026", "https://www.mediamarkt.nl/nl/search.html?query=LG+2026"),



        



        # 2. Germany (MediaMarkt DE)



        ("DE", "MediaMarkt", "Samsung", "OLED", "https://www.mediamarkt.de/de/search.html?query=Samsung+OLED"),



        ("DE", "MediaMarkt", "Samsung", "S85H", "https://www.mediamarkt.de/de/search.html?query=SAMSUNG%20S85H&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "Samsung", "S90H", "https://www.mediamarkt.de/de/search.html?query=SAMSUNG%20S90H&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "Samsung", "S95H", "https://www.mediamarkt.de/de/search.html?query=SAMSUNG%20S95H&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "Samsung", "S99H", "https://www.mediamarkt.de/de/search.html?query=SAMSUNG%20S99H&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "Samsung", "Neo QLED", "https://www.mediamarkt.de/de/search.html?query=Samsung+Neo+QLED"),



        ("DE", "MediaMarkt", "Samsung", "QN80", "https://www.mediamarkt.de/de/search.html?query=Samsung%20QN80&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "Samsung", "Mini LED", "https://www.mediamarkt.de/de/search.html?query=Samsung+Mini+LED"),



        ("DE", "MediaMarkt", "Samsung", "U80", "https://www.mediamarkt.de/de/search.html?query=Samsung+U80"),



        ("DE", "MediaMarkt", "Samsung", "Micro RGB", "https://www.mediamarkt.de/de/search.html?query=Samsung+Micro+RGB"),



        ("DE", "MediaMarkt", "Samsung", "The Frame", "https://www.mediamarkt.de/de/search.html?query=Samsung+The+Frame&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "Samsung", "2026", "https://www.mediamarkt.de/de/search.html?query=Samsung+2026"),



        ("DE", "MediaMarkt", "LG", "OLED", "https://www.mediamarkt.de/de/search.html?query=LG+OLED"),



        ("DE", "MediaMarkt", "LG", "B6", "https://www.mediamarkt.de/de/search.html?query=LG%20OLED%20B6&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "LG", "C6", "https://www.mediamarkt.de/de/search.html?query=LG+C6"),



        ("DE", "MediaMarkt", "LG", "G6", "https://www.mediamarkt.de/de/search.html?query=LG%20OLED%20G6&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "LG", "B5", "https://www.mediamarkt.de/de/search.html?query=LG%20B5&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "LG", "C5", "https://www.mediamarkt.de/de/search.html?query=LG%20C5&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "LG", "G5", "https://www.mediamarkt.de/de/search.html?query=LG%20G5&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "LG", "QNED", "https://www.mediamarkt.de/de/search.html?query=LG+QNED"),



        ("DE", "MediaMarkt", "LG", "NU80", "https://www.mediamarkt.de/de/search.html?query=lg%20nu80"),



        ("DE", "MediaMarkt", "LG", "MRGB", "https://www.mediamarkt.de/de/search.html?query=LG+MRGB"),



        ("DE", "MediaMarkt", "LG", "MRGB8", "https://www.mediamarkt.de/de/search.html?query=LG%20MRGB8&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "LG", "Mini_RGB", "https://www.mediamarkt.de/de/search.html?query=LG%20Mini%20RGB&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "LG", "StanbyME", "https://www.mediamarkt.de/de/search.html?query=LG%20StanbyME&marketplace=MediaMarkt"),



        ("DE", "MediaMarkt", "LG", "2026", "https://www.mediamarkt.de/de/search.html?query=LG+2026"),







        # 2b. Austria (MediaMarkt AT)



        ("AT", "MediaMarkt", "Samsung", "OLED", "https://www.mediamarkt.at/de/search.html?query=Samsung+OLED"),



        ("AT", "MediaMarkt", "Samsung", "Neo QLED", "https://www.mediamarkt.at/de/search.html?query=Samsung+Neo+QLED"),



        ("AT", "MediaMarkt", "Samsung", "Mini LED", "https://www.mediamarkt.at/de/search.html?query=Samsung+Mini+LED"),



        ("AT", "MediaMarkt", "Samsung", "U80", "https://www.mediamarkt.at/de/search.html?query=Samsung+U80"),



        ("AT", "MediaMarkt", "Samsung", "Micro RGB", "https://www.mediamarkt.at/de/search.html?query=Samsung+Micro+RGB"),



        ("AT", "MediaMarkt", "Samsung", "2026", "https://www.mediamarkt.at/de/search.html?query=Samsung+2026"),



        ("AT", "MediaMarkt", "LG", "OLED", "https://www.mediamarkt.at/de/search.html?query=LG+OLED"),



        ("AT", "MediaMarkt", "LG", "C6", "https://www.mediamarkt.at/de/search.html?query=LG+C6"),



        ("AT", "MediaMarkt", "LG", "QNED", "https://www.mediamarkt.at/de/search.html?query=LG+QNED"),



        ("AT", "MediaMarkt", "LG", "NU8", "https://www.mediamarkt.at/de/search.html?query=LG+NU8"),



        ("AT", "MediaMarkt", "LG", "MRGB", "https://www.mediamarkt.at/de/search.html?query=LG+MRGB"),



        ("AT", "MediaMarkt", "LG", "2026", "https://www.mediamarkt.at/de/search.html?query=LG+2026"),



        



        # 3. Spain (MediaMarkt ES)



        ("ES", "MediaMarkt", "Samsung", "OLED", "https://www.mediamarkt.es/es/search.html?query=Samsung+OLED&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "S83H", "https://www.mediamarkt.es/es/search.html?query=s83h&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "77S83H", "https://www.mediamarkt.es/es/search.html?query=77S83h&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "S90H", "https://www.mediamarkt.es/es/search.html?query=samsung+s90h&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "S95H", "https://www.mediamarkt.es/es/search.html?query=samsung+s95h&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "Neo QLED", "https://www.mediamarkt.es/es/search.html?query=Samsung+Neo+QLED&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "Mini LED", "https://www.mediamarkt.es/es/search.html?query=Samsung+Mini+LED&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "M73H", "https://www.mediamarkt.es/es/search.html?query=SAMSUNG%20M73h&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "M80H", "https://www.mediamarkt.es/es/search.html?query=SAMSUNG%20M80h&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "U80", "https://www.mediamarkt.es/es/search.html?query=Samsung+U80&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "Micro RGB", "https://www.mediamarkt.es/es/search.html?query=Samsung+Micro+RGB&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "R85H", "https://www.mediamarkt.es/es/search.html?query=SAMSUNG%20R85h&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "R95H", "https://www.mediamarkt.es/es/search.html?query=SAMSUNG%20R95h&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "Samsung", "2026", "https://www.mediamarkt.es/es/search.html?query=Samsung+2026&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "OLED", "https://www.mediamarkt.es/es/search.html?query=LG+OLED&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "B6", "https://www.mediamarkt.es/es/search.html?query=LG+OLED+B6&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "C6", "https://www.mediamarkt.es/es/search.html?query=LG+C6&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "42C6", "https://www.mediamarkt.es/es/search.html?query=42C6&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "G6", "https://www.mediamarkt.es/es/search.html?query=LG+OLED+G6&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "QNED", "https://www.mediamarkt.es/es/search.html?query=LG+QNED&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "QNED72B", "https://www.mediamarkt.es/es/search.html?query=LG%20QNED72B&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "QNED81B", "https://www.mediamarkt.es/es/search.html?query=LG%20QNED81B&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "QNED85B", "https://www.mediamarkt.es/es/search.html?query=LG%20QNED85B&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "NU8", "https://www.mediamarkt.es/es/search.html?query=LG+NU8&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "MRGB", "https://www.mediamarkt.es/es/search.html?query=LG+MRGB&marketplace=MediaMarkt"),



        ("ES", "MediaMarkt", "LG", "2026", "https://www.mediamarkt.es/es/search.html?query=LG+2026&marketplace=MediaMarkt"),



        



        # 4. Italy (MediaWorld IT)



        ("IT", "MediaWorld", "Samsung", "OLED", "https://www.mediaworld.it/it/search.html?query=Samsung+OLED&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "Samsung", "S95", "https://www.mediaworld.it/it/search.html?query=Samsung+S95&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "Samsung", "S90", "https://www.mediaworld.it/it/search.html?query=Samsung+S90&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "Samsung", "S85", "https://www.mediaworld.it/it/search.html?query=Samsung+S85&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "Samsung", "S99", "https://www.mediaworld.it/it/search.html?query=Samsung+S99&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "Samsung", "Neo QLED", "https://www.mediaworld.it/it/search.html?query=Samsung+Neo+QLED&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "Samsung", "Mini LED", "https://www.mediaworld.it/it/search.html?query=Samsung+Mini+LED&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "Samsung", "U80", "https://www.mediaworld.it/it/search.html?query=Samsung+U80&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "Samsung", "Micro RGB", "https://www.mediaworld.it/it/search.html?query=Samsung+Micro+RGB&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "Samsung", "2026", "https://www.mediaworld.it/it/search.html?query=Samsung+2026&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "LG", "OLED", "https://www.mediaworld.it/it/search.html?query=LG+OLED&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "LG", "C6", "https://www.mediaworld.it/it/search.html?query=LG+C6&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "LG", "QNED", "https://www.mediaworld.it/it/search.html?query=LG+QNED&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "LG", "NU8", "https://www.mediaworld.it/it/search.html?query=LG+NU8&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "LG", "NU850", "https://www.mediaworld.it/it/search.html?query=LG+NU850&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "LG", "MRGB", "https://www.mediaworld.it/it/search.html?query=LG+MRGB&marketplace=MediaWorld"),



        ("IT", "MediaWorld", "LG", "2026", "https://www.mediaworld.it/it/search.html?query=LG+2026&marketplace=MediaWorld"),







        # 5. Switzerland (MediaMarkt CH)



        ("CH", "MediaMarkt", "Samsung", "TV", "https://www.mediamarkt.ch/de/search.html?query=samsung%20TV&brand=SAMSUNG&marketplace=MediaMarkt&modelyear=2025%20OR%202026"),



        ("CH", "MediaMarkt", "Samsung", "2026", "https://www.mediamarkt.ch/de/search.html?query=samsung%202026&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "Samsung", "OLED", "https://www.mediamarkt.ch/de/search.html?query=samsung%20OLED&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "Samsung", "S90", "https://www.mediamarkt.ch/de/search.html?query=samsung%20S90&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "Samsung", "S95", "https://www.mediamarkt.ch/de/search.html?query=samsung%20S95&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "Samsung", "S85", "https://www.mediamarkt.ch/de/search.html?query=samsung%20S85&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "Samsung", "QN80", "https://www.mediamarkt.ch/de/search.html?query=samsung%20QN80&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "Samsung", "M70", "https://www.mediamarkt.ch/de/search.html?query=samsung%20M70&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "Samsung", "R85", "https://www.mediamarkt.ch/de/search.html?query=samsung%20R85&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "Samsung", "U8090", "https://www.mediamarkt.ch/de/search.html?query=samsung%20U8090&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "Samsung", "Frame", "https://www.mediamarkt.ch/de/search.html?query=samsung%20the%20frame&brand=SAMSUNG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "LG", "TV", "https://www.mediamarkt.ch/de/search.html?query=LG%20TV&brand=LG&marketplace=MediaMarkt&modelyear=2025%20OR%202026"),



        ("CH", "MediaMarkt", "LG", "2026", "https://www.mediamarkt.ch/de/search.html?query=LG%202026&brand=LG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "LG", "OLED", "https://www.mediamarkt.ch/de/search.html?query=LG%20OLED&brand=LG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "LG", "B6", "https://www.mediamarkt.ch/de/search.html?query=LG%20OLED%20B6&brand=LG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "LG", "C6", "https://www.mediamarkt.ch/de/search.html?query=LG%20C6&brand=LG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "LG", "G6", "https://www.mediamarkt.ch/de/search.html?query=LG%20OLED%20G6&brand=LG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "LG", "QNED", "https://www.mediamarkt.ch/de/search.html?query=LG%20QNED&brand=LG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "LG", "MRGB", "https://www.mediamarkt.ch/de/search.html?query=LG%20MRGB&brand=LG&marketplace=MediaMarkt"),



        ("CH", "MediaMarkt", "LG", "StanbyME", "https://www.mediamarkt.ch/de/search.html?query=LG%20StanbyME&brand=LG&marketplace=MediaMarkt"),



    ]



    



    if countries:



        if isinstance(countries, str):



            country_list = [c.strip().upper() for c in countries.split(",") if c.strip()]



        else:



            country_list = [c.upper() for c in countries]



        TARGET_MATRIX = [item for item in TARGET_MATRIX if item[0] in country_list]



        print(f"  [FILTER] Filtered queries for countries {country_list}: {len(TARGET_MATRIX)} queries to execute.")



    else:



        country_list = ["DE", "AT", "ES", "NL", "IT"]







    master_data = {}



    if os.path.exists(MASTER_REGISTRY_PATH):



        with open(MASTER_REGISTRY_PATH, "r", encoding="utf-8") as f:



            master_data = json.load(f)







    from core.run_context import stamp







    file_map = {



        ("NL", "Samsung"): "raw_mm-nl_samsung.json",



        ("NL", "LG"): "raw_mm-nl_lg.json",



        ("DE", "Samsung"): "raw_mm-de_samsung.json",



        ("DE", "LG"): "raw_mm-de_lg.json",



        ("AT", "Samsung"): "raw_mm-at_samsung.json",



        ("AT", "LG"): "raw_mm-at_lg.json",



        ("ES", "Samsung"): "raw_mm-es_samsung.json",



        ("ES", "LG"): "raw_mm-es_lg.json",



        ("IT", "Samsung"): "raw_mw-it_samsung.json",



        ("IT", "LG"): "raw_mw-it_lg.json",



        ("CH", "Samsung"): "raw_mediamarkt_samsung.json",



        ("CH", "LG"): "raw_mediamarkt_lg.json",



    }







    t0 = time.time()



    by_cc = {}



    for item in TARGET_MATRIX:



        cc = item[0]



        by_cc.setdefault(cc, []).append(item)







    for cc, cc_queries in by_cc.items():



        retailer = cc_queries[0][1]



        by_brand = scrape_mediamarkt_country_stealthy(cc, retailer, cc_queries, master_data)



        for b_key in ("Samsung", "LG"):



            items = by_brand.get(b_key, [])



            if items:



                update_master_registry(items, cc, retailer)



            fname = file_map.get((cc, b_key))



            if not fname:



                continue



            fpath = os.path.join(DATA_DIR, fname)



            model_dict = {}



            seen_this_query_batch = set()



            for item in items:



                src_type = item.pop("_source_type", "pdp")



                item.pop("_is_9digit", None)



                stamp(item, engine="scrapling_stealthy", source_type=src_type, http_status=200)



                mc = item.get("model_code", "Unknown")



                key = mc if mc != "Unknown" else item.get("title", "")



                if key in seen_this_query_batch:



                    continue



                seen_this_query_batch.add(key)



                model_dict[key] = item



            final_list = list(model_dict.values())



            with open(fpath, "w", encoding="utf-8") as f:



                json.dump(final_list, f, ensure_ascii=False, indent=2)



            print(f"     💾 Saved {fname:<25}: total={len(final_list):>3} verified live models", flush=True)







    print(f"\n✅ All Zero-Firecrawl country sessions completed in {time.time() - t0:.1f}s.", flush=True)



    print("\n================================================================================")



    print(" 🎉 ZERO-FIRECRAWL WESTERN EU SURVEY & MASTER REGISTRY REPLENISHMENT COMPLETE! ")



    print("================================================================================")







if __name__ == "__main__":



    import argparse



    parser = argparse.ArgumentParser(description="Zero-Firecrawl Western EU Scraper")



    parser.add_argument("--countries", type=str, default=None, help="Comma-separated country codes, e.g. DE,AT,ES,NL,IT")



    parser.add_argument("--queries", type=str, default=None, help="Subset of queries")



    parser.add_argument("--workers", type=int, default=1, help="Unused (uses in-browser parallel fetch)")



    args = parser.parse_args()



    run_targeted_western_eu(countries=args.countries, workers=args.workers, queries=args.queries)







