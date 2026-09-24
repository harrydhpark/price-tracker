import os
import re
import openpyxl

wb_path = os.path.abspath('data/price tracker_EU_2026 0924_v1.xlsx')
wb = openpyxl.load_workbook(wb_path)

def extract_size_from_text(code, title, url):
    # 1. Try from model code: e.g. 55M80H, UE43U8072H, OLED55C55LA, 65QNED87A6B
    code_str = str(code or '').upper().strip()
    m = re.search(r'(?:^|[A-Z]{1,3})(\d{2,3})(?:[A-Z]|$)', code_str)
    if m:
        sz = int(m.group(1))
        if sz in [24, 27, 32, 40, 42, 43, 48, 50, 55, 65, 70, 75, 77, 83, 85, 86, 98, 100, 115]:
            return sz

    # 2. Try from URL slug: e.g. .../samsung-mini-led-55-4k-...
    url_str = str(url or '').lower()
    m_url = re.search(r'-(24|27|32|40|42|43|48|50|55|65|70|75|77|83|85|86|98|100|115)-(?:4k|oled|qled|smart|full-hd|led|qned)', url_str)
    if m_url:
        return int(m_url.group(1))

    # 3. Try from title: e.g. 55" or 55 4K
    title_str = str(title or '')
    m_title = re.search(r'(24|27|32|40|42|43|48|50|55|65|70|75|77|83|85|86|98|100|115)[\"\”\s]*(?:4K|Smart|OLED|QLED|LED|QNED|Nano|Mini|Micro)', title_str, re.I)
    if m_title:
        return int(m_title.group(1))

    return 55 # default fallback

for sheet_name in ['Public_GR_Samsung', 'Public_GR_LG']:
    if sheet_name not in wb.sheetnames:
        continue
    ws = wb[sheet_name]
    fixed_count = 0
    for r in range(2, ws.max_row + 1):
        curr_size = ws.cell(row=r, column=4).value
        code = ws.cell(row=r, column=5).value
        url = ws.cell(row=r, column=11).value
        title = ws.cell(row=r, column=12).value if ws.max_column >= 12 else ''

        real_size = extract_size_from_text(code, title, url)
        if real_size != curr_size:
            ws.cell(row=r, column=4, value=real_size)
            fixed_count += 1
            print(f"[{sheet_name}] Row {r}: {code} -> Size corrected: {curr_size} -> {real_size}\"")

    print(f"[{sheet_name}] Fixed {fixed_count} rows with corrupted size!")

wb.save(wb_path)
print(f"Saved workbook with corrected Public.gr sizes to {wb_path}")
