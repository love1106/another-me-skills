# Excel Spreadsheet (XLSX) — Hướng Dẫn Chi Tiết

## Tạo XLSX Mới — openpyxl

### Step-by-step (PHẢI THEO THỨ TỰ)

1. Import + tạo Workbook
2. Set sheet name
3. Define styles (header, body, number formats)
4. Thêm header row với formatting
5. Thêm data rows
6. Thêm formulas (KHÔNG hardcode calculated values)
7. Set column widths
8. Freeze panes
9. Save file
10. Verify bằng checklist

### Template Code — Data Report

```python
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = 'Báo Cáo'

# ============================================================
# STYLES — Define trước, dùng lại
# ============================================================
# Font priority: VN → Be Vietnam Pro → Arial | EN → Inter → Arial
# XLSX font render phụ thuộc máy mở file — chọn font phổ biến
FONT_VN = 'Be Vietnam Pro'  # Vietnamese content
FONT_EN = 'Inter'            # English content
FONT = FONT_VN  # ← Đổi sang FONT_EN cho English docs

# Header style
header_font = Font(name=FONT, size=10, bold=True, color='FFFFFF')
header_fill = PatternFill(start_color='2B579A', end_color='2B579A', fill_type='solid')
header_align = Alignment(horizontal='center', vertical='center', wrap_text=True)

# Body style
body_font = Font(name=FONT, size=10, color='333333')
body_align = Alignment(vertical='center', wrap_text=True)
number_align = Alignment(horizontal='right', vertical='center')

# Border
thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9'),
)

# Alternating row fill
alt_fill = PatternFill(start_color='F2F7FB', end_color='F2F7FB', fill_type='solid')

# Total row
total_font = Font(name=FONT, size=10, bold=True, color='1B3A65')
total_fill = PatternFill(start_color='E8EEF4', end_color='E8EEF4', fill_type='solid')

# ============================================================
# TITLE ROW (Row 1)
# ============================================================
ws.merge_cells('A1:E1')
title_cell = ws['A1']
title_cell.value = 'BÁO CÁO DOANH THU Q1/2026'
title_cell.font = Font(name=FONT, size=14, bold=True, color='1B3A65')
title_cell.alignment = Alignment(horizontal='center', vertical='center')
ws.row_dimensions[1].height = 35

# Subtitle row
ws.merge_cells('A2:E2')
ws['A2'].value = 'Ngày tạo: 15/04/2026'
ws['A2'].font = Font(name=FONT, size=9, color='666666')
ws['A2'].alignment = Alignment(horizontal='center')
ws.row_dimensions[2].height = 20

# Empty row
ws.row_dimensions[3].height = 10

# ============================================================
# HEADER ROW (Row 4)
# ============================================================
headers = ['STT', 'Khu vực', 'Doanh thu (₫)', 'Chi phí (₫)', 'Lợi nhuận (₫)']
for col, text in enumerate(headers, 1):
    cell = ws.cell(row=4, column=col, value=text)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_align
    cell.border = thin_border
ws.row_dimensions[4].height = 30

# ============================================================
# DATA ROWS (Row 5+)
# ============================================================
data = [
    [1, 'Miền Bắc',  5000000000, 3000000000],
    [2, 'Miền Trung', 3000000000, 2000000000],
    [3, 'Miền Nam',   7000000000, 4000000000],
    [4, 'Online',     2000000000,  800000000],
]

for i, row_data in enumerate(data):
    row_num = 5 + i
    # STT
    ws.cell(row=row_num, column=1, value=row_data[0]).alignment = Alignment(horizontal='center')
    # Khu vực
    ws.cell(row=row_num, column=2, value=row_data[1])
    # Doanh thu
    ws.cell(row=row_num, column=3, value=row_data[2])
    # Chi phí
    ws.cell(row=row_num, column=4, value=row_data[3])
    # Lợi nhuận = FORMULA, KHÔNG HARDCODE
    ws.cell(row=row_num, column=5).value = f'=C{row_num}-D{row_num}'

    # Apply styles
    for col in range(1, 6):
        cell = ws.cell(row=row_num, column=col)
        cell.font = body_font
        cell.border = thin_border
        cell.alignment = body_align if col <= 2 else number_align
        # Number format cho cột tiền
        if col >= 3:
            cell.number_format = '#,##0'
        # Alternating rows
        if i % 2 == 0:
            cell.fill = alt_fill

# ============================================================
# TOTAL ROW
# ============================================================
total_row = 5 + len(data)
ws.cell(row=total_row, column=1, value='').border = thin_border
ws.cell(row=total_row, column=2, value='TỔNG CỘNG')
# FORMULAS — KHÔNG BAO GIỜ HARDCODE
ws.cell(row=total_row, column=3).value = f'=SUM(C5:C{total_row-1})'
ws.cell(row=total_row, column=4).value = f'=SUM(D5:D{total_row-1})'
ws.cell(row=total_row, column=5).value = f'=SUM(E5:E{total_row-1})'

for col in range(1, 6):
    cell = ws.cell(row=total_row, column=col)
    cell.font = total_font
    cell.fill = total_fill
    cell.border = thin_border
    cell.alignment = number_align if col >= 3 else body_align
    if col >= 3:
        cell.number_format = '#,##0'

# ============================================================
# COLUMN WIDTHS
# ============================================================
column_widths = {'A': 6, 'B': 18, 'C': 20, 'D': 20, 'E': 20}
for col_letter, width in column_widths.items():
    ws.column_dimensions[col_letter].width = width

# ============================================================
# FREEZE PANES — Freeze header row
# ============================================================
ws.freeze_panes = 'A5'

# ============================================================
# PRINT SETTINGS
# ============================================================
ws.print_title_rows = '4:4'  # Repeat header on each page
ws.sheet_properties.pageSetUpPr.fitToPage = True

# ============================================================
# SAVE
# ============================================================
wb.save('report.xlsx')
```

## QUY TẮC BẮT BUỘC

### ❌ TUYỆT ĐỐI KHÔNG Hardcode Calculated Values

```python
# ❌ SAI — tính bằng Python rồi ghi số
total = sum(values)
ws['C10'] = total  # Hardcode 17000000000

# ✅ ĐÚNG — dùng Excel formula
ws['C10'] = '=SUM(C5:C9)'
```

Áp dụng cho TẤT CẢ phép tính: SUM, AVERAGE, COUNT, IF, VLOOKUP...

### Color Coding (Financial Models)

| Màu chữ | Ý nghĩa |
|----------|----------|
| **Xanh dương** (0,0,255) | Input thủ công, user thay đổi |
| **Đen** (0,0,0) | Formulas, tính toán |
| **Xanh lá** (0,128,0) | Link từ sheet khác |
| **Đỏ** (255,0,0) | Link từ file khác |
| **Nền vàng** (255,255,0) | Assumptions cần chú ý |

### Number Format Standards

| Loại | Format Code | Ví dụ |
|------|-------------|-------|
| Tiền VND | `#,##0` | 1,500,000 |
| Tiền USD | `$#,##0.00` | $1,500.00 |
| Phần trăm | `0.0%` | 15.5% |
| Năm | `@` (text) | 2026 (không phải 2,026) |
| Số âm | `#,##0;(#,##0);"-"` | (1,500) |

## Sửa XLSX Có Sẵn

```python
from openpyxl import load_workbook

# ⚠️ KHÔNG dùng data_only=True nếu save lại — sẽ MẤT formulas
wb = load_workbook('existing.xlsx')
ws = wb.active

# Sửa cell
ws['A1'] = 'New Value'

# Thêm row
ws.insert_rows(5)

# Thêm sheet
ws_new = wb.create_sheet('Sheet Mới')

wb.save('modified.xlsx')
```

## Đọc & Phân Tích Data

```python
import pandas as pd

# Đọc
df = pd.read_excel('data.xlsx')
df = pd.read_excel('data.xlsx', sheet_name='Sheet2')
all_sheets = pd.read_excel('data.xlsx', sheet_name=None)  # Dict of DataFrames

# Phân tích
df.describe()  # Thống kê
df.groupby('region')['sales'].sum()  # Group by
pivot = pd.pivot_table(df, values='sales', index='region', columns='quarter', aggfunc='sum')

# Filter
high_sales = df[df['sales'] > 1000000]
```

## Auto-Adjust Column Width

```python
def auto_adjust_width(ws):
    """Tự động điều chỉnh width theo content."""
    for column_cells in ws.columns:
        max_length = 0
        col_letter = get_column_letter(column_cells[0].column)
        for cell in column_cells:
            try:
                cell_length = len(str(cell.value or ''))
                if cell_length > max_length:
                    max_length = cell_length
            except:
                pass
        ws.column_dimensions[col_letter].width = min(max_length + 3, 50)
```

## Recalculate Formulas

Sau khi save file có formulas, cần recalculate để giá trị hiển thị đúng:

```bash
# Dùng LibreOffice (cần cài sẵn)
libreoffice --headless --calc --convert-to xlsx output.xlsx

# Hoặc dùng script recalc.py nếu có
python scripts/recalc.py output.xlsx
```

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| #REF! | Cell reference sai | Kiểm tra range trong formula |
| #DIV/0! | Chia cho 0 | Dùng `=IF(B2=0,0,A2/B2)` |
| #VALUE! | Sai data type | Kiểm tra cell có text trong cột số |
| #NAME? | Tên function sai | Kiểm tra spelling |
| Số hiện 2,026 thay vì 2026 | Năm bị format number | Format cell as Text `@` |
| Formula không tính | openpyxl không tính | Chạy recalc sau khi save |
| Mất formulas | load_workbook(data_only=True) | KHÔNG dùng data_only nếu save |
