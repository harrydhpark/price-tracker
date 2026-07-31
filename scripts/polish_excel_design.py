import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import os
import copy
import sys

sys.stdout.reconfigure(encoding='utf-8')

import glob
from datetime import datetime, timedelta

data_dir = r"d:\TV 유럽영업\15. AX Task\2026 AX 실행과제\Price Tracker\data"
today_mmdd = datetime.now().strftime("%m%d")
files = glob.glob(os.path.join(data_dir, f"Swiss_ATA_Comparison_2026_{today_mmdd}*.xlsx"))
files = [f for f in files if not os.path.basename(f).startswith("~$")]
if not files:
    # Fallback to yesterday
    yesterday_mmdd = (datetime.now() - timedelta(days=1)).strftime("%m%d")
    files = glob.glob(os.path.join(data_dir, f"Swiss_ATA_Comparison_2026_{yesterday_mmdd}*.xlsx"))
    files = [f for f in files if not os.path.basename(f).startswith("~$")]

# Borders
thin_side = Side(style='thin', color='D9D9D9')
thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
thick_bottom = Border(bottom=Side(style='double', color='333333'))

# Fills
header_fill = PatternFill(start_color="1B3A4B", end_color="1B3A4B", fill_type="solid") # Dark Ocean Blue
summary_hdr_fill = PatternFill(start_color="D9E2EC", end_color="D9E2EC", fill_type="solid") # Soft Blue-Grey
lg_row_fill = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid") # Ultra-soft light grey
samsung_row_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid") # Pure white

# Fonts
hdr_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=15, bold=True, color="1B3A4B")

sam_bold_font = Font(name="Calibri", size=10, bold=True, color="002060") # Samsung Bold Dark Navy (Project Standard)
sam_reg_font = Font(name="Calibri", size=10, bold=False, color="002060") # Samsung Regular Navy (Project Standard)

lg_bold_font = Font(name="Calibri", size=10, bold=True, color="2C2C2C") # LG Bold Charcoal Gray
lg_reg_font = Font(name="Calibri", size=10, bold=False, color="2C2C2C") # LG Regular Charcoal Gray

# Alignments
align_center = Alignment(horizontal="center", vertical="center")
align_right = Alignment(horizontal="right", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")

def polish_sheet(sheet, year):
    # Hide gridlines (strictly enforced)
    sheet.views.sheetView[0].showGridLines = False
    
    # 1. Title formatting (Row 1)
    for col in range(1, 18):
        cell = sheet.cell(row=1, column=col)
        if cell.value:
            cell.font = title_font
            cell.alignment = align_left
            
    # 2. Main Column Headers formatting (Row 3)
    for col in range(1, 18):
        cell = sheet.cell(row=3, column=col)
        cell.fill = header_fill
        cell.font = hdr_font
        cell.alignment = align_center
        cell.border = thin_border
    sheet.row_dimensions[3].height = 25
    
    # Calculate limits dynamically
    summary_hdr_row = None
    for r in range(4, 300):
        val_b = sheet.cell(row=r, column=2).value
        if val_b == "Series" and r > 10:
            summary_hdr_row = r
            break
            
    if summary_hdr_row is None:
        summary_hdr_row = 86 if year == 2025 else 132
        
    # Calculate last_row by scanning upwards from summary_hdr_row - 1
    last_row = summary_hdr_row - 1
    while last_row > 4:
        val_b = sheet.cell(row=last_row, column=2).value
        if val_b and str(val_b).strip():
            break
        last_row -= 1
    
    # 3. Data Matrix formatting (Row 4 to last_row)
    for r in range(4, last_row + 1):
        series_val = sheet.cell(row=r, column=2).value
        if not series_val:
            # Clear styles for blank rows
            for col in range(1, 18):
                c = sheet.cell(row=r, column=col)
                c.fill = samsung_row_fill
                c.border = thin_border
            continue
            
        clean_series = str(series_val).strip()
        is_lg = any(s in clean_series for s in ["G5", "C5", "B5", "QNED86A", "QNED80A", "UA75", "G6", "C6", "B6", "QNED86B", "QNED80B", "QNED90", "QNED85", "QNED80", "QNED70", "NU85"])
        brand = "LG" if is_lg else "Samsung"
        
        # Apply zebra striping fill
        row_fill = lg_row_fill if brand == "LG" else samsung_row_fill
        
        # Row height
        sheet.row_dimensions[r].height = 20
        
        for col in range(1, 18):
            cell = sheet.cell(row=r, column=col)
            cell.fill = row_fill
            cell.border = thin_border
            
            # Formats & alignments
            if col in [1, 2, 3, 8, 13]: # Display, Series, Models
                cell.alignment = align_center
            elif col in [5, 6, 10, 11, 15, 16]: # Prices & Cashbacks
                cell.alignment = align_right
                if cell.value is not None and isinstance(cell.value, (int, float)):
                    cell.number_format = "#,##0"
            elif col in [7, 12, 17]: # ATA percentages
                cell.alignment = align_right
                cell.number_format = "0%"
                
            # Font styling
            if brand == "Samsung":
                if col in [1, 2]: # Display & Series
                    cell.font = sam_bold_font
                else:
                    cell.font = sam_reg_font
            else:
                if col in [1, 2]:
                    cell.font = lg_bold_font
                else:
                    cell.font = lg_reg_font

    # 4. Summary Table Formatting (Dynamic)
    summary_start = summary_hdr_row + 1
    summary_end = sheet.max_row + 1
    
    # Format summary header row
    for col in range(1, 18):
        cell = sheet.cell(row=summary_hdr_row, column=col)
        cell.fill = summary_hdr_fill
        # Keep custom font style but make it bold & clean
        cell.font = Font(name="Calibri", size=10, bold=True, color="1B3A4B")
        cell.alignment = align_center
        cell.border = thin_border
    sheet.row_dimensions[summary_hdr_row].height = 24
    
    # Format summary rows
    for r in range(summary_start, summary_end):
        series_val = sheet.cell(row=r, column=2).value
        if not series_val:
            continue
            
        clean_series = str(series_val).strip()
        is_lg = any(s in clean_series for s in ["G5", "C5", "B5", "QNED86A", "QNED80A", "UA75", "G6", "C6", "B6", "QNED86B", "QNED80B", "QNED90", "QNED85", "QNED80", "QNED70", "NU85"])
        brand = "LG" if is_lg else "Samsung"
        row_fill = lg_row_fill if brand == "LG" else samsung_row_fill
        
        sheet.row_dimensions[r].height = 20
        
        for col in range(1, 18):
            cell = sheet.cell(row=r, column=col)
            cell.fill = row_fill
            cell.border = thin_border
            
            # Alignments & formats
            if col in [1, 2, 3, 8, 13]:
                cell.alignment = align_center
            elif col in [5, 6, 10, 11, 15, 16]:
                cell.alignment = align_right
                if cell.value is not None and isinstance(cell.value, (int, float)):
                    cell.number_format = "#,##0"
            elif col in [7, 12, 17]:
                cell.alignment = align_right
                cell.number_format = "0%"
                
            # Font styling
            if brand == "Samsung":
                if col in [1, 2]:
                    cell.font = sam_bold_font
                else:
                    cell.font = sam_reg_font
            else:
                if col in [1, 2]:
                    cell.font = lg_bold_font
                else:
                    cell.font = lg_reg_font

def main():
    for f in files:
        if not os.path.exists(f):
            print(f"[WARN] File not found: {f}")
            continue
            
        print(f"[POLISHING DESIGN] Processing file: {f}")
        wb = openpyxl.load_workbook(f)
        
        polish_sheet(wb["Swiss_2025"], 2025)
        polish_sheet(wb["Swiss_2026"], 2026)
        
        wb.save(f)
        wb.close()
        print(f"[POLISHING DONE] Successfully saved design updates to: {f}")

if __name__ == "__main__":
    main()
