import openpyxl

# 1. Fix EU workbook: Public_GR_LG - 75QNED83B6A (400 EUR discount badge)
wb_eu_path = 'data/price tracker_EU_2026 0924_v1.xlsx'
wb_eu = openpyxl.load_workbook(wb_eu_path)
ws_gr = wb_eu['Public_GR_LG']

rows_to_delete = []
for idx, row in enumerate(ws_gr.iter_rows(values_only=True), start=1):
    if row and len(row) > 6 and row[4]:
        code = str(row[4]).upper().strip()
        price = row[5] # Selling price
        if '75QNED83' in code and price == 400.0:
            rows_to_delete.append(idx)

for r_idx in reversed(rows_to_delete):
    print(f"Deleting row {r_idx} from Public_GR_LG (anomalous 400 EUR badge)")
    ws_gr.delete_rows(r_idx)

wb_eu.save(wb_eu_path)
print("Saved EU workbook.")

# 2. Fix Swiss workbook: Digitec_LG_Full - 65QNED93A6A (marketplace 2,448.5 CHF)
wb_ch_path = 'data/price tracker_swiss_2026 0924_v1.xlsx'
wb_ch = openpyxl.load_workbook(wb_ch_path)
ws_dig = wb_ch['Digitec_LG_Full']

ch_delete = []
for idx, row in enumerate(ws_dig.iter_rows(values_only=True), start=1):
    if row and len(row) > 6 and row[4]:
        code = str(row[4]).upper().strip()
        price = row[5]
        if '65QNED93A6A' in code and price and float(price) > 2000:
            ch_delete.append(idx)

for r_idx in reversed(ch_delete):
    print(f"Deleting row {r_idx} from Digitec_LG_Full (marketplace outlier {price} CHF)")
    ws_dig.delete_rows(r_idx)

wb_ch.save(wb_ch_path)
print("Saved Swiss workbook.")
