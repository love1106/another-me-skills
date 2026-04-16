# Word Document (DOCX) — Hướng Dẫn Chi Tiết

## Tạo DOCX Mới — python-docx

### Step-by-step (PHẢI THEO THỨ TỰ)

1. Import + tạo Document
2. Set page layout (A4, margins)
3. Define styles (heading, body, table)
4. Thêm content theo structure
5. Thêm header/footer + page numbers
6. Save file
7. Verify bằng checklist

### Template Code — Business Report

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
import datetime

doc = Document()

# ============================================================
# STEP 1: Page Layout — A4
# ============================================================
section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
section.top_margin = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin = Cm(3.18)
section.right_margin = Cm(2.54)

# ============================================================
# STEP 2: Define Styles
# ============================================================
# Font priority by language:
#   Vietnamese: Be Vietnam Pro → Arial (fallback)
#   English:    Inter → Arial (fallback)
# Check font availability: fc-list | grep -i "vietnam" / fc-list | grep -i "inter"
FONT_VN = 'Be Vietnam Pro'       # Vietnamese content (primary)
FONT_EN = 'Inter'                 # English content (primary)
FONT_FALLBACK = 'Arial'           # Universal fallback
# ← Set FONT based on document language
FONT = FONT_VN  # Vietnamese doc. Change to FONT_EN for English

style = doc.styles['Normal']
font = style.font
font.name = FONT
font.size = Pt(11)
font.color.rgb = RGBColor(0x33, 0x33, 0x33)
paragraph_format = style.paragraph_format
paragraph_format.space_after = Pt(6)
paragraph_format.line_spacing = 1.15

# Heading 1
h1 = doc.styles['Heading 1']
h1.font.name = FONT
h1.font.size = Pt(18)
h1.font.bold = True
h1.font.color.rgb = RGBColor(0x1B, 0x3A, 0x65)
h1.paragraph_format.space_before = Pt(24)
h1.paragraph_format.space_after = Pt(12)

# Heading 2
h2 = doc.styles['Heading 2']
h2.font.name = FONT
h2.font.size = Pt(14)
h2.font.bold = True
h2.font.color.rgb = RGBColor(0x2B, 0x57, 0x9A)
h2.paragraph_format.space_before = Pt(18)
h2.paragraph_format.space_after = Pt(6)

# Heading 3
h3 = doc.styles['Heading 3']
h3.font.name = FONT
h3.font.size = Pt(12)
h3.font.bold = True
h3.font.color.rgb = RGBColor(0x2E, 0x75, 0xB6)

# ============================================================
# STEP 3: Title Page (optional)
# ============================================================
# Add empty paragraphs for vertical centering
for _ in range(6):
    doc.add_paragraph()

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('TÊN BÁO CÁO')
run.font.size = Pt(28)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1B, 0x3A, 0x65)
run.font.name = FONT

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run('Phụ đề hoặc mô tả ngắn')
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
run.font.name = FONT

date_para = doc.add_paragraph()
date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = date_para.add_run(datetime.datetime.now().strftime('%d/%m/%Y'))
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_page_break()

# ============================================================
# STEP 4: Content
# ============================================================
doc.add_heading('1. Tổng quan', level=1)
doc.add_paragraph(
    'Nội dung tổng quan của báo cáo. Mô tả mục đích, phạm vi, '
    'và bối cảnh của tài liệu.'
)

doc.add_heading('2. Phân tích chi tiết', level=1)
doc.add_heading('2.1 Dữ liệu', level=2)
doc.add_paragraph('Mô tả nguồn dữ liệu và phương pháp thu thập.')

# ============================================================
# STEP 5: Table — Styled
# ============================================================
table = doc.add_table(rows=4, cols=4)
table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

# Header row
header_cells = table.rows[0].cells
headers = ['STT', 'Hạng mục', 'Giá trị', 'Ghi chú']
for i, text in enumerate(headers):
    cell = header_cells[i]
    cell.text = text
    # Style header
    for paragraph in cell.paragraphs:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in paragraph.runs:
            run.font.bold = True
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.name = FONT
    # Background color
    shading = cell._element.get_or_add_tcPr()
    shading_elm = shading.makeelement(qn('w:shd'), {
        qn('w:val'): 'clear',
        qn('w:color'): 'auto',
        qn('w:fill'): '2B579A'
    })
    shading.append(shading_elm)

# Data rows
data = [
    ['1', 'Doanh thu', '1.500.000.000 ₫', 'Q1/2026'],
    ['2', 'Chi phí', '800.000.000 ₫', 'Q1/2026'],
    ['3', 'Lợi nhuận', '700.000.000 ₫', 'Q1/2026'],
]
for row_idx, row_data in enumerate(data):
    row = table.rows[row_idx + 1]
    for col_idx, text in enumerate(row_data):
        cell = row.cells[col_idx]
        cell.text = text
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(10)
                run.font.name = FONT
    # Alternating row color
    if row_idx % 2 == 0:
        for cell in row.cells:
            shading = cell._element.get_or_add_tcPr()
            shading_elm = shading.makeelement(qn('w:shd'), {
                qn('w:val'): 'clear',
                qn('w:color'): 'auto',
                qn('w:fill'): 'F2F7FB'
            })
            shading.append(shading_elm)

# ============================================================
# STEP 6: Header & Footer + Page Numbers
# ============================================================
section = doc.sections[0]

# Header
header = section.header
header_para = header.paragraphs[0]
header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = header_para.add_run('Tên Công Ty — Báo Cáo Nội Bộ')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
run.font.name = FONT

# Footer with page number
footer = section.footer
footer_para = footer.paragraphs[0]
footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = footer_para.add_run('Trang ')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
# Page number field
fldChar1 = footer_para._element.makeelement(qn('w:fldChar'), {qn('w:fldCharType'): 'begin'})
run._element.addnext(fldChar1)
instrText = footer_para._element.makeelement(qn('w:instrText'), {})
instrText.text = 'PAGE'
fldChar1.addnext(instrText)
fldChar2 = footer_para._element.makeelement(qn('w:fldChar'), {qn('w:fldCharType'): 'end'})
instrText.addnext(fldChar2)

# ============================================================
# STEP 7: Save
# ============================================================
doc.save('report.docx')
```

### Thêm Content Types

#### Bullet List
```python
for item in ['Mục 1', 'Mục 2', 'Mục 3']:
    doc.add_paragraph(item, style='List Bullet')
```

#### Numbered List
```python
for item in ['Bước 1: Chuẩn bị', 'Bước 2: Thực hiện', 'Bước 3: Kiểm tra']:
    doc.add_paragraph(item, style='List Number')
```

#### Image
```python
doc.add_picture('chart.png', width=Inches(5.0))
last_paragraph = doc.paragraphs[-1]
last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

#### Page Break
```python
doc.add_page_break()
```

## Sửa DOCX Có Sẵn

### Đọc & Extract Text
```bash
# Convert sang markdown để đọc nhanh
pandoc input.docx -o output.md

# Với tracked changes
pandoc --track-changes=all input.docx -o output.md
```

### Sửa bằng python-docx
```python
from docx import Document

doc = Document('existing.docx')

# Thay text trong paragraphs
for para in doc.paragraphs:
    if 'OLD_TEXT' in para.text:
        for run in para.runs:
            if 'OLD_TEXT' in run.text:
                run.text = run.text.replace('OLD_TEXT', 'NEW_TEXT')

# Thêm content vào cuối
doc.add_heading('Phần bổ sung', level=1)
doc.add_paragraph('Nội dung thêm vào.')

doc.save('modified.docx')
```

### Sửa OOXML trực tiếp (nâng cao)

Khi cần tracked changes, comments, hoặc preserve formatting phức tạp:

1. Unzip file docx: `unzip document.docx -d unpacked/`
2. Sửa XML trong `unpacked/word/document.xml`
3. Pack lại: `cd unpacked && zip -r ../modified.docx .`

**Tracked changes XML pattern:**
```xml
<!-- Xóa "30" thêm "60" -->
<w:r><w:t>The term is </w:t></w:r>
<w:del w:author="Agent" w:date="2026-04-15T00:00:00Z">
  <w:r><w:delText>30</w:delText></w:r>
</w:del>
<w:ins w:author="Agent" w:date="2026-04-15T00:00:00Z">
  <w:r><w:t>60</w:t></w:r>
</w:ins>
<w:r><w:t> days.</w:t></w:r>
```

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| Font □□□ | Font không có trên máy mở file | VN: Be Vietnam Pro → Arial fallback. EN: Inter → Arial fallback |
| Tiếng Việt lỗi dấu | Encoding sai hoặc font không hỗ trợ | Đảm bảo UTF-8, dùng Be Vietnam Pro (VN) hoặc Inter (EN) |
| Table tràn trang | Column width quá rộng | Set column width cụ thể |
| Page number sai | Không add field code | Dùng PAGE field (xem template trên) |
| Style bị reset | Override style sai | Define style TRƯỚC khi add content |
