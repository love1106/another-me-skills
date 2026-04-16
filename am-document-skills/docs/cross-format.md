# Cross-Format Workflows

## Workflow 1: Data → Excel Report → PDF Summary

**Use case:** Có raw data, cần tạo Excel chi tiết + PDF tóm tắt.

### Steps

1. **Nhận data** (CSV, JSON, database query, user input)
2. **Tạo Excel** (docs/xlsx.md) — full data, formulas, charts
3. **Tạo PDF summary** (docs/pdf.md) — key metrics, charts as images
4. **Deliver cả 2 file**

### Code Flow

```python
import pandas as pd
from openpyxl import Workbook
# ... (tạo Excel theo xlsx.md template)

# Extract key metrics từ data
total_revenue = df['revenue'].sum()
total_profit = df['profit'].sum()
top_region = df.loc[df['revenue'].idxmax(), 'region']

# Tạo chart image cho PDF
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 4))
df.plot(x='region', y='revenue', kind='bar', ax=ax, color='#2B579A')
ax.set_title('Doanh Thu Theo Khu Vực')
plt.tight_layout()
plt.savefig('/tmp/chart.png', dpi=150)
plt.close()

# Tạo PDF với chart
# ... (dùng pdf.md template, embed chart.png)
```

## Workflow 2: Data → PowerPoint Presentation

**Use case:** Có data/analysis, cần tạo slide deck trình bày.

### Steps

1. **Phân tích data** → xác định key insights
2. **Outline slides:**
   - Slide 1: Title
   - Slide 2: Agenda
   - Slide 3: Key Metrics (số liệu lớn)
   - Slide 4-N: Chi tiết (tables, charts)
   - Slide cuối: Summary / Next Steps
3. **Tạo PPTX** (docs/pptx.md)

### Rule: Mỗi slide = 1 ý chính
- KHÔNG nhồi nhiều bảng/chart vào 1 slide
- Số → hiển thị to, bold
- Text → tối đa 6 bullet points

## Workflow 3: Word Report + Excel Appendix

**Use case:** Báo cáo chính bằng Word, số liệu chi tiết trong Excel đính kèm.

### Steps

1. **Tạo Excel** (docs/xlsx.md) — data đầy đủ
2. **Tạo charts từ Excel data** → export as PNG
3. **Tạo Word** (docs/docx.md) — narrative report, embed chart images
4. **Reference Excel** trong Word: "Chi tiết xem file đính kèm report_data.xlsx"

## Workflow 4: Convert Formats

### Kiểm tra tool trước khi dùng
```bash
# Check pandoc
command -v pandoc &>/dev/null || echo "❌ pandoc chưa cài: apt-get install -y pandoc"

# Check libreoffice
command -v libreoffice &>/dev/null || echo "❌ libreoffice chưa cài: apt-get install -y libreoffice-calc"

# Check xelatex (cho Vietnamese PDF)
command -v xelatex &>/dev/null || echo "❌ xelatex chưa cài: apt-get install -y texlive-xetex"
```

### Pandoc Conversions
```bash
# Markdown → Word
pandoc report.md -o report.docx

# Markdown → PDF (cần xelatex cho Vietnamese)
pandoc report.md -o report.pdf --pdf-engine=xelatex

# Word → Markdown
pandoc report.docx -o report.md

# Word → PDF
pandoc report.docx -o report.pdf

# Markdown → PowerPoint
pandoc slides.md -o presentation.pptx

# HTML → Word
pandoc page.html -o document.docx
```

### Pandoc Markdown → PPTX

Mỗi H2 (`##`) = 1 slide mới:

```markdown
---
title: Báo Cáo Q1/2026
author: Company Name
date: 15/04/2026
---

## Tổng Quan

- Doanh thu tăng 23%
- Lợi nhuận tăng 35%
- Mở rộng 3 thị trường mới

## Doanh Thu Theo Khu Vực

| Khu vực | Doanh thu | Tăng trưởng |
|---------|-----------|-------------|
| Bắc     | 5 tỷ      | +20%        |
| Trung   | 3 tỷ      | +15%        |
| Nam     | 7 tỷ      | +30%        |

## Kế Hoạch Q2

1. Mở rộng online
2. Tối ưu chi phí
3. Ra mắt sản phẩm mới
```

```bash
pandoc slides.md -o presentation.pptx
```

> **Hạn chế:** Pandoc tạo PPTX basic — không custom colors, layouts. Muốn đẹp → dùng python-pptx trực tiếp.

## Workflow 5: PDF Form → Data → Excel

```python
# 1. Extract form data từ PDF
from pypdf import PdfReader
reader = PdfReader('form.pdf')
fields = reader.get_form_text_fields()
# fields = {'name': 'Nguyen Van A', 'amount': '1500000', ...}

# 2. Parse data
import pandas as pd
data = [fields]  # Có thể loop nhiều forms
df = pd.DataFrame(data)

# 3. Export to Excel
df.to_excel('form_data.xlsx', index=False)
```

## Decision Matrix — Chọn Output Format

| Nhu cầu | Format | Lý do |
|---------|--------|-------|
| Báo cáo narrative + tables | DOCX | Dễ edit, tracked changes |
| Chỉ cần đọc, không edit | PDF | Fixed layout, universal viewer |
| Data + formulas + analysis | XLSX | Interactive, recalculate |
| Trình bày / Pitch | PPTX | Visual, slide-based |
| Archive / Share read-only | PDF | Không bị thay đổi |
| Data entry form | PDF (fillable) | Form fields |
| Print chuyên nghiệp | PDF | Consistent across printers |
