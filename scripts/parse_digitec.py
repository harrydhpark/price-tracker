import json
import re

def parse_digitec_file(filepath, brand):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        markdown = data.get("markdown", "")
        
    # 이미지 링크들 제거해서 잘못 매핑되는 것 방지
    markdown = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', markdown)
        
    # 각 상품은 상품명 링크로 시작
    # 예: [Samsung QE65QN70FAU (65", QN70F, NeoQLED, 4K, 2025, CH)](...)
    pattern = rf'\[{brand}\s+([^\]]+)\]\(([^)]+)\)'
    matches = list(re.finditer(pattern, markdown, re.IGNORECASE))
    
    products = []
    for idx, match in enumerate(matches):
        full_title = f"{brand} " + match.group(1)
        link = match.group(2)
        
        start_pos = match.end()
        end_pos = matches[idx+1].start() if idx+1 < len(matches) else len(markdown)
        block = markdown[start_pos:end_pos]
        
        # 제외 대상: 중고/리퍼비시 (Refurbished, Returned, Returned & Tested, Used)
        block_upper = block.upper()
        title_upper = full_title.upper()
        if "RETURNED" in block_upper or "REFURBISHED" in block_upper or "USED" in block_upper:
            continue
            
        # 가격 파싱
        # 예: CHF799.– 또는 CHF 799.-
        price_val = 0.0
        price_match = re.search(r'CHF\s*([\d\s’\x27\x60,.]*[,.]\d{2})', block)
        if not price_match:
            price_match = re.search(r'CHF\s*(\d+)[.–]?', block)
        if price_match:
            p_str = price_match.group(1).replace("\u2019", "").replace("'", "").replace("`", "").replace(" ", "").replace(",", ".").replace(".–", "").strip()
            try:
                price_val = float(p_str)
            except ValueError:
                price_val = 0.0
                
        # 모델 코드 및 사이즈 추출
        # 예: Samsung QE65QN70FAU (65", QN70F, NeoQLED, 4K, 2025, CH)
        # 괄호 안에서 파싱
        inner_match = re.search(r'\(([^)]+)\)', full_title)
        size_val = 55
        model_code = "Unknown"
        year_val = 2025
        
        # 첫 부분에서 모델 코드 추출 시도
        # 예: Samsung QE65QN70FAU -> QE65QN70FAU
        words = title_upper.split()
        for w in words:
            clean_w = w.replace("(", "").replace(")", "").replace(",", "")
            if any(char.isdigit() for char in clean_w) and len(clean_w) >= 6:
                model_code = clean_w
                break
                
        if inner_match:
            parts = [p.strip() for p in inner_match.group(1).split(",")]
            for p in parts:
                if '"' in p:
                    # 사이즈
                    try:
                        size_val = int(p.replace('"', '').strip())
                    except ValueError:
                        pass
                if p.isdigit() and len(p) == 4:
                    year_val = int(p)
                    
        # 파트너사 판매 여부 검사
        is_partner = False
        partner_name = "Digitec"
        
        partner_match = re.search(r'(?:Offer by|Angebot von|Verkauf und Versand durch)\s+\[?([^\]\n]+)\]?', block, re.IGNORECASE)
        if partner_match:
            name = partner_match.group(1).strip()
            if "Digitec" not in name and "Galaxus" not in name:
                is_partner = True
                partner_name = name
                
        # 모니터류 오진입 방지
        if "MONITOR" in title_upper or "ODYSSEY" in title_upper or "ULTRAGEAR" in title_upper or "MYVIEW" in title_upper:
            continue
            
        products.append({
            "brand": brand,
            "year": year_val,
            "title": full_title,
            "link": link,
            "price": price_val,
            "is_partner": is_partner,
            "partner_name": partner_name,
            "size": size_val,
            "model_code": model_code
        })
        
    return products

if __name__ == "__main__":
    samsungs = parse_digitec_file("C:/Users/harry.park/.gemini/antigravity/brain/f7b3e514-69f3-40c5-9d95-806bc168c4c7/.system_generated/steps/729/output.txt", "Samsung")
    lgs = parse_digitec_file("C:/Users/harry.park/.gemini/antigravity/brain/f7b3e514-69f3-40c5-9d95-806bc168c4c7/.system_generated/steps/731/output.txt", "LG")
    
    print(f"=== DIGITEC SAMSUNG (Direct & In Stock: {len([p for p in samsungs if not p['is_partner']])}) ===")
    for idx, p in enumerate([p for p in samsungs if not p['is_partner']][:15]):
        print(f"  [{idx+1}] Code: {p['model_code']} | Size: {p['size']}\" | Price: {p['price']} | Partner: {p['partner_name']}")
