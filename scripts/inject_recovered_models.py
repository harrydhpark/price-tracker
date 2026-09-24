import os
import openpyxl

wb_path = os.path.abspath('data/price tracker_EU_2026 0924_v1.xlsx')
wb = openpyxl.load_workbook(wb_path)

# 1. Samsung row
ws_s = wb['Alza_CZ_Samsung']
# Check if QE65QN70H is already in ws_s
existing_s = [str(r[4]).strip().upper() for r in ws_s.iter_rows(values_only=True) if r and len(r) > 4 and r[4]]
if 'QE65QN70H' not in existing_s:
    row_s = ['Samsung', 2026, 'QN70H', 65, 'QE65QN70H', 21990, 24433, 10, '2026ALZAEXTRA10', 0, 'https://www.alza.cz/65-samsung-qe65qn70h-d13360988.htm']
    ws_s.append(row_s)
    print(f"Appended QE65QN70H to Alza_CZ_Samsung (Row count now: {ws_s.max_row})")
else:
    print("QE65QN70H already in Alza_CZ_Samsung")

# 2. LG rows
ws_l = wb['Alza_CZ_LG']
existing_l = [str(r[4]).strip().upper() for r in ws_l.iter_rows(values_only=True) if r and len(r) > 4 and r[4]]

lg_recovered = [
    ['LG', 2026, 'NU8E', 65, '65NU8E0B3LA', 11753, 11753, 0, 'None', 0, 'https://www.alza.cz/65-lg-65nu8e0b3la-d13367895.htm'],
    ['LG', 2026, 'NU8E', 55, '55NU8E0B3LA', 8991, 9990, 10, '2026ALZAEXTRA10', 0, 'https://www.alza.cz/55-lg-55nu8e0b3la-d13367894.htm'],
    ['LG', 2026, 'NU8E', 43, '43NU8E0B3LA', 7884, 7884, 0, 'None', 0, 'https://www.alza.cz/43-lg-43nu8e0b3la-d13367899.htm'],
    ['LG', 2026, 'OLED C6', 42, 'OLED42C6ELB', 29400, 29400, 0, 'None', 0, 'https://www.alza.cz/42-lg-oled42c6elb-d13471223.htm'],
    ['LG', 2026, 'OLED C6', 48, 'OLED48C6ELB', 33322, 33322, 0, 'None', 0, 'https://www.alza.cz/48-lg-oled48c6elb-d13471226.htm']
]

for row in lg_recovered:
    code = row[4].upper()
    if code not in existing_l:
        ws_l.append(row)
        print(f"Appended {code} to Alza_CZ_LG (Row count now: {ws_l.max_row})")
    else:
        print(f"{code} already in Alza_CZ_LG")

wb.save(wb_path)
print(f"Saved updated EU workbook to {wb_path}")
