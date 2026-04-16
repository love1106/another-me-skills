# Template: Business Report

## Structure

```
Trang bìa
├── Tên báo cáo (title)
├── Phụ đề (subtitle) 
├── Tên tổ chức / Tác giả
└── Ngày tháng

Mục lục (nếu > 5 trang)

1. Tổng quan (Executive Summary)
   └── Tóm tắt 3-5 câu: mục đích, kết quả chính, đề xuất

2. Bối cảnh & Phạm vi
   ├── Mục tiêu báo cáo
   ├── Phạm vi (scope)
   ├── Nguồn dữ liệu
   └── Phương pháp

3. Phân tích chi tiết
   ├── 3.1 [Chủ đề 1] + Data/Table + Nhận xét
   ├── 3.2 [Chủ đề 2] + Data/Table + Nhận xét
   └── 3.3 [Chủ đề 3]

4. Kết luận & Đề xuất
   ├── Kết luận chính (3-5 points)
   └── Đề xuất hành động (action items)

5. Phụ lục (nếu có)
```

## Quick-Start Code — DOCX

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import datetime

doc = Document()

# Page layout A4
section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
section.top_margin = Cm(2.54)
section.bottom_margin = Cm(2.54)
section.left_margin = Cm(3.18)
section.right_margin = Cm(2.54)

# Styles
for style_name in ['Normal']:
    s = doc.styles[style_name]
    s.font.name = 'Be Vietnam Pro'
    s.font.size = Pt(11)
    s.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
    s.paragraph_format.line_spacing = 1.15

for level, size, color in [(1, 18, '1B3A65'), (2, 14, '2B579A'), (3, 12, '2E75B6')]:
    h = doc.styles[f'Heading {level}']
    h.font.name = 'Be Vietnam Pro'
    h.font.size = Pt(size)
    h.font.bold = True
    h.font.color.rgb = RGBColor(int(color[:2],16), int(color[2:4],16), int(color[4:],16))

# Title page
for _ in range(5): doc.add_paragraph()
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('TÊN BÁO CÁO')  # ← THAY TÊN
run.font.size = Pt(28)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1B, 0x3A, 0x65)
run.font.name = 'Be Vietnam Pro'

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run('Phụ đề mô tả')  # ← THAY
run.font.size = Pt(13)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

date_p = doc.add_paragraph()
date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = date_p.add_run(datetime.datetime.now().strftime('%d/%m/%Y'))
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_page_break()

# Content — THAY NỘI DUNG BÊN DƯỚI
doc.add_heading('1. Tổng Quan', level=1)
doc.add_paragraph('Nội dung tổng quan...')

doc.add_heading('2. Phân Tích Chi Tiết', level=1)
doc.add_heading('2.1 Chủ đề 1', level=2)
doc.add_paragraph('Nội dung phân tích...')

doc.add_heading('3. Kết Luận & Đề Xuất', level=1)
for item in ['Kết luận 1', 'Kết luận 2', 'Kết luận 3']:
    doc.add_paragraph(item, style='List Bullet')

# Header + Footer (xem docs/docx.md cho page number code)

doc.save('report.docx')
```

## Quick-Start Code — PDF

```python
# Import ReportPDF class từ docs/pdf.md
# pdf = ReportPDF(title='Tên Báo Cáo', company='Tên Công Ty', lang='vi')
# pdf.alias_nb_pages()
# pdf.add_title_page('Tên Báo Cáo', 'Phụ đề')
# pdf.add_page()
# pdf.add_heading('1. Tổng Quan', level=1)
# pdf.add_body('Nội dung...')
# pdf.add_table(headers, data, col_widths)
# pdf.output('report.pdf')
```

## Khi Nào Dùng

- Báo cáo doanh thu / tài chính
- Báo cáo dự án
- Báo cáo nghiên cứu / khảo sát
- Báo cáo tổng kết
