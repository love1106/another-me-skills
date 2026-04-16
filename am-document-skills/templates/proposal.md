# Template: Business Proposal / Đề Xuất Kinh Doanh

## Structure

```
Trang bìa
├── Tên đề xuất (title)
├── Khách hàng / Đối tác
├── Tên công ty
└── Ngày tháng

1. Giới thiệu (Introduction)
   ├── Giới thiệu công ty
   ├── Bối cảnh / Vấn đề cần giải quyết
   └── Mục tiêu đề xuất

2. Phạm vi công việc (Scope of Work)
   ├── 2.1 Giai đoạn 1: [Tên] — Mô tả + Deliverables
   ├── 2.2 Giai đoạn 2: [Tên] — Mô tả + Deliverables
   └── 2.3 Giai đoạn 3: [Tên] — Mô tả + Deliverables

3. Phương pháp & Công nghệ
   ├── Approach / Methodology
   └── Tech stack / Tools

4. Timeline
   └── Gantt-style table: Giai đoạn | Thời gian | Milestone

5. Đội ngũ (Team)
   └── Tên | Vai trò | Kinh nghiệm

6. Chi phí (Pricing)
   ├── Bảng chi tiết: Hạng mục | SL | Đơn giá | Thành tiền
   ├── Tổng chi phí
   ├── Điều khoản thanh toán
   └── Ghi chú (VAT, phát sinh...)

7. Điều khoản & Điều kiện
   ├── Thời hạn hiệu lực đề xuất
   ├── Bảo mật
   ├── Bảo hành / Hỗ trợ
   └── Điều kiện hủy

8. Phụ lục (nếu có)
   └── Portfolio, case studies, chứng chỉ
```

## Specs

| Property | Value |
|----------|-------|
| Format | DOCX hoặc PDF |
| Page | A4, 5-15 trang |
| Font | Be Vietnam Pro (VN), Arial fallback |
| Tone | Chuyên nghiệp, thuyết phục |
| Pricing table | PHẢI có — rõ ràng từng hạng mục |

## Quick-Start Code — DOCX Proposal

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
run = title.add_run('ĐỀ XUẤT KINH DOANH')  # ← THAY TÊN
run.font.size = Pt(28)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1B, 0x3A, 0x65)
run.font.name = 'Be Vietnam Pro'

client = doc.add_paragraph()
client.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = client.add_run('Khách hàng: [Tên khách hàng]')  # ← THAY
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

company = doc.add_paragraph()
company.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = company.add_run('Bởi: [Tên công ty]')  # ← THAY
run.font.size = Pt(13)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

date_p = doc.add_paragraph()
date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = date_p.add_run(datetime.datetime.now().strftime('%d/%m/%Y'))
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_page_break()

# Content — THAY NỘI DUNG
doc.add_heading('1. Giới Thiệu', level=1)
doc.add_paragraph('Giới thiệu công ty và bối cảnh dự án...')

doc.add_heading('2. Phạm Vi Công Việc', level=1)
doc.add_heading('2.1 Giai đoạn 1: Khảo sát', level=2)
doc.add_paragraph('Mô tả công việc giai đoạn 1...')

doc.add_heading('3. Chi Phí', level=1)
# Thêm pricing table — xem docs/docx.md cho table template

doc.add_heading('4. Điều Khoản', level=1)
doc.add_paragraph('Đề xuất có hiệu lực trong 30 ngày kể từ ngày phát hành.')

doc.save('proposal.docx')
```

## Khi Nào Dùng

- Đề xuất dự án cho khách hàng
- Proposal / Quotation
- Pitch deck dạng document (không phải slide)
- RFP response
