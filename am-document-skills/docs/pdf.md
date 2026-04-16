# PDF — Hướng Dẫn Chi Tiết

## Tạo PDF Mới — fpdf2

`fpdf2` nhẹ, nhanh, phù hợp cho phần lớn use cases. Dùng `reportlab` khi cần features nâng cao (complex tables, flowables).

### Step-by-step

1. Import + tạo FPDF object
2. **BẮT BUỘC: Register font Be Vietnam Pro** (hoặc Inter cho English)
3. Set metadata (title, author)
4. Add page + content
5. Save file
6. Verify bằng checklist

### 🔴 RULE: Font cho fpdf2

```
Nội dung tiếng Việt → Be Vietnam Pro (BẮT BUỘC register trước khi dùng)
Nội dung tiếng Anh  → Inter (BẮT BUỘC register trước khi dùng)
KHÔNG BAO GIỜ dùng Helvetica/Arial/Courier cho nội dung có Unicode
```

Font core của fpdf2 (Helvetica, Arial, Courier, Times) **KHÔNG HỖ TRỢ Unicode**.
Bullet `•`, em dash `—`, tiếng Việt có dấu → đều LỖI nếu dùng font core.

### Template Code — Vietnamese Report PDF

```python
from fpdf import FPDF
import datetime

# ============================================================
# FONT PATHS — Auto-detect hoặc hardcode nếu biết path
# ============================================================
import subprocess

def _find_font_dir(font_name, fallback):
    """Auto-detect font directory via fc-list."""
    try:
        out = subprocess.check_output(
            f'fc-list | grep -i "{font_name}" | head -1 | cut -d: -f1',
            shell=True, text=True
        ).strip()
        if out:
            import os
            return os.path.dirname(out)
    except Exception:
        pass
    return fallback

FONT_VN = _find_font_dir('Be Vietnam Pro', '/usr/share/fonts/truetype/be-vietnam-pro')
FONT_EN = _find_font_dir('Inter', '/usr/share/fonts/truetype/inter')


class ReportPDF(FPDF):
    """PDF report template với Be Vietnam Pro font."""

    def __init__(self, title='Báo Cáo', company='Công Ty', lang='vi'):
        super().__init__()
        self.report_title = title
        self.company = company
        self.lang = lang
        self.set_auto_page_break(auto=True, margin=25)

        # Register fonts — PHẢI LÀM TRƯỚC KHI DÙNG
        if lang == 'vi':
            self.add_font('MainFont', '', f'{FONT_VN}/BeVietnamPro-Regular.ttf')
            self.add_font('MainFont', 'B', f'{FONT_VN}/BeVietnamPro-Bold.ttf')
            self.add_font('MainFont', 'I', f'{FONT_VN}/BeVietnamPro-Italic.ttf')
            self.add_font('MainFont', 'BI', f'{FONT_VN}/BeVietnamPro-BoldItalic.ttf')
        else:
            self.add_font('MainFont', '', f'{FONT_EN}/Inter-Regular.ttf')
            self.add_font('MainFont', 'B', f'{FONT_EN}/Inter-Bold.ttf')
            self.add_font('MainFont', 'I', f'{FONT_EN}/Inter-Italic.ttf')
            self.add_font('MainFont', 'BI', f'{FONT_EN}/Inter-BoldItalic.ttf')

    def header(self):
        if self.page_no() > 1:
            self.set_font('MainFont', 'I', 9)
            self.set_text_color(153, 153, 153)
            self.cell(0, 10, f'{self.company} \u2014 {self.report_title}',
                      align='R', new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(217, 217, 217)
            self.line(10, 18, 200, 18)
            self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(217, 217, 217)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_font('MainFont', 'I', 9)
        self.set_text_color(153, 153, 153)
        self.cell(0, 10, f'Trang {self.page_no()}/{{nb}}', align='C')

    def add_title_page(self, title, subtitle='', date=None):
        """Trang bìa."""
        self.add_page()
        self.ln(60)
        # Title
        self.set_font('MainFont', 'B', 32)
        self.set_text_color(27, 58, 101)  # #1B3A65
        self.multi_cell(0, 15, title, align='C')
        # Divider
        self.ln(3)
        self.set_draw_color(46, 117, 182)
        self.set_line_width(1)
        self.line(60, self.get_y(), 150, self.get_y())
        self.set_line_width(0.2)
        # Subtitle
        if subtitle:
            self.ln(8)
            self.set_font('MainFont', '', 14)
            self.set_text_color(102, 102, 102)
            self.multi_cell(0, 10, subtitle, align='C')
        # Date
        self.ln(10)
        self.set_font('MainFont', '', 12)
        self.set_text_color(102, 102, 102)
        date_str = date or datetime.datetime.now().strftime('%d/%m/%Y')
        self.cell(0, 10, date_str, align='C', new_x="LMARGIN", new_y="NEXT")

    def add_heading(self, text, level=1):
        """Thêm heading với underline cho H1."""
        sizes = {1: 18, 2: 14, 3: 12}
        colors = {1: (27, 58, 101), 2: (43, 87, 154), 3: (46, 117, 182)}
        self.ln(4)
        self.set_font('MainFont', 'B', sizes.get(level, 12))
        self.set_text_color(*colors.get(level, (51, 51, 51)))
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        if level == 1:
            y = self.get_y()
            self.set_draw_color(43, 87, 154)
            self.set_line_width(0.5)
            self.line(10, y, 80, y)
            self.set_line_width(0.2)
        self.ln(2)

    def add_body(self, text):
        """Body text."""
        self.set_font('MainFont', '', 11)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def add_bullet(self, text):
        """Bullet point với dấu •."""
        self.set_font('MainFont', '', 11)
        self.set_text_color(51, 51, 51)
        x = self.get_x()
        self.cell(8, 6, '\u2022', new_x="END")
        self.multi_cell(0, 6, text)
        self.ln(1)

    def add_image(self, image_path, width=180, caption=None):
        """Embed image (chart, logo...) with optional caption.

        Args:
            image_path: path to PNG/JPG file
            width: image width in mm (default 180 = full width)
            caption: optional caption text below image
        """
        x = (self.w - width) / 2  # Center horizontally
        self.image(image_path, x=x, w=width)
        if caption:
            self.ln(2)
            self.set_font('MainFont', 'I', 9)
            self.set_text_color(102, 102, 102)
            self.cell(0, 5, caption, align='C', new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(51, 51, 51)
        self.ln(4)

    def add_table(self, headers, data, col_widths=None):
        """Bảng với header màu, alternating rows.

        Args:
            headers: list of strings
            data: list of lists. Dòng cuối cùng = total row (bold).
            col_widths: list of mm. None = auto equal.
        """
        if col_widths is None:
            available = self.w - self.l_margin - self.r_margin
            col_widths = [available / len(headers)] * len(headers)

        # Header row
        self.set_font('MainFont', 'B', 9)
        self.set_fill_color(43, 87, 154)   # #2B579A
        self.set_text_color(255, 255, 255)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 9, header, border=1, fill=True, align='C')
        self.ln()

        # Data rows
        self.set_font('MainFont', '', 9)
        for row_idx, row in enumerate(data):
            # Alternating background
            if row_idx % 2 == 0:
                self.set_fill_color(242, 247, 251)  # #F2F7FB
            else:
                self.set_fill_color(255, 255, 255)

            # Total row = last row
            is_total = row_idx == len(data) - 1
            if is_total:
                self.set_font('MainFont', 'B', 9)
                self.set_fill_color(232, 238, 244)  # #E8EEF4
                self.set_text_color(27, 58, 101)
            else:
                self.set_text_color(51, 51, 51)

            for i, cell_data in enumerate(row):
                text = str(cell_data)
                align = 'C' if i > 0 else 'L'
                # Color code negative numbers red, positive green
                if not is_total and i > 0:
                    try:
                        val = float(text.replace(',', '').replace('%', ''))
                        if val < 0:
                            self.set_text_color(220, 53, 69)   # red
                        elif val > 0:
                            self.set_text_color(40, 167, 69)   # green
                        else:
                            self.set_text_color(51, 51, 51)
                    except ValueError:
                        self.set_text_color(51, 51, 51)
                self.cell(col_widths[i], 8, text, border=1, fill=True, align=align)
                self.set_text_color(51, 51, 51)

            if is_total:
                self.set_font('MainFont', '', 9)
            self.ln()


# ============================================================
# CÁCH SỬ DỤNG
# ============================================================
# Vietnamese:
# pdf = ReportPDF(title='Báo Cáo Doanh Thu', company='Công Ty ABC', lang='vi')
#
# English:
# pdf = ReportPDF(title='Revenue Report', company='Công Ty ABC', lang='en')
#
# pdf.alias_nb_pages()
# pdf.add_title_page('Tiêu Đề Báo Cáo', 'Phụ đề mô tả')
# pdf.add_page()
# pdf.add_heading('1. Tổng Quan', level=1)
# pdf.add_body('Nội dung báo cáo...')
# pdf.add_bullet('Điểm quan trọng thứ nhất')
# pdf.add_table(['Cột 1', 'Cột 2'], [['A', '100'], ['B', '200'], ['Tổng', '300']])
# pdf.output('report.pdf')
```

### Template Code — English Report PDF

```python
# Chỉ khác lang='en' → dùng Inter font
pdf = ReportPDF(title='Quarterly Report', company='Công Ty ABC', lang='en')
pdf.alias_nb_pages()
pdf.add_title_page('Quarterly Revenue Report', 'Q1 2026 Analysis')
pdf.add_page()
pdf.add_heading('1. Executive Summary', level=1)
pdf.add_body('This report provides an overview of Q1 2026 performance...')
pdf.output('report_en.pdf')
```

> **⚠️ QUAN TRỌNG — Vietnamese trong PDF:**
>
> fpdf2 với font core (Helvetica, Arial, Courier) **KHÔNG hỗ trợ Unicode**.
> Kể cả em dash `—`, bullet `•`, tiếng Việt có dấu đều **LỖI**.
>
> **BẮT BUỘC dùng Be Vietnam Pro:**
> ```python
> FONT_DIR = '/usr/share/fonts/truetype/be-vietnam-pro'
> pdf.add_font('BeVietnam', '', f'{FONT_DIR}/BeVietnamPro-Regular.ttf')
> pdf.add_font('BeVietnam', 'B', f'{FONT_DIR}/BeVietnamPro-Bold.ttf')
> pdf.add_font('BeVietnam', 'I', f'{FONT_DIR}/BeVietnamPro-Italic.ttf')
> pdf.add_font('BeVietnam', 'BI', f'{FONT_DIR}/BeVietnamPro-BoldItalic.ttf')
> pdf.set_font('BeVietnam', '', 11)
> ```
>
> **Nếu chưa cài Be Vietnam Pro**, dùng DejaVu Sans (có sẵn trên Linux):
> ```python
> pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
> pdf.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
> ```
>
> **KHÔNG BAO GIỜ** dùng `set_font('Helvetica')` hay `set_font('Arial')` cho nội dung tiếng Việt.

## Tạo PDF Phức Tạp — reportlab

Khi cần: multi-column layout, complex tables, images, flowable content.

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

# Register Be Vietnam Pro cho reportlab — dùng auto-detect
import subprocess as _sp
def _font_path(name, fallback):
    try:
        p = _sp.check_output(f'fc-list | grep -i "{name}" | head -1 | cut -d: -f1', shell=True, text=True).strip()
        return p if p else fallback
    except: return fallback

pdfmetrics.registerFont(TTFont('BeVietnam', _font_path('BeVietnamPro-Regular', '/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-Regular.ttf')))
pdfmetrics.registerFont(TTFont('BeVietnam-Bold', _font_path('BeVietnamPro-Bold', '/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-Bold.ttf')))
pdfmetrics.registerFont(TTFont('BeVietnam-Italic', _font_path('BeVietnamPro-Italic', '/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-Italic.ttf')))

doc = SimpleDocTemplate(
    'report.pdf',
    pagesize=A4,
    topMargin=2.54*cm,
    bottomMargin=2.54*cm,
    leftMargin=3.18*cm,
    rightMargin=2.54*cm,
)

styles = getSampleStyleSheet()

# Custom styles với Be Vietnam Pro
styles.add(ParagraphStyle(
    name='VNTitle', parent=styles['Title'],
    fontName='BeVietnam-Bold', fontSize=24,
    textColor=HexColor('#1B3A65'), spaceAfter=12,
))
styles.add(ParagraphStyle(
    name='VNH1', parent=styles['Heading1'],
    fontName='BeVietnam-Bold', fontSize=18,
    textColor=HexColor('#1B3A65'), spaceBefore=24, spaceAfter=12,
))
styles.add(ParagraphStyle(
    name='VNBody', parent=styles['Normal'],
    fontName='BeVietnam', fontSize=11,
    textColor=HexColor('#333333'), leading=16, spaceAfter=6,
))

story = []
story.append(Paragraph('Báo Cáo Doanh Thu Q1/2026', styles['VNTitle']))
story.append(Spacer(1, 12))
story.append(Paragraph('1. Tổng Quan', styles['VNH1']))
story.append(Paragraph('Đây là báo cáo tổng hợp doanh thu quý 1 năm 2026.', styles['VNBody']))

# Table
table_data = [
    ['STT', 'Khu vực', 'Doanh thu', 'Lợi nhuận'],
    ['1', 'Miền Bắc', '5.000.000.000 ₫', '2.000.000.000 ₫'],
    ['2', 'Miền Nam', '7.000.000.000 ₫', '3.000.000.000 ₫'],
]
table = Table(table_data, colWidths=[30, 80, 100, 100])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2B579A')),
    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
    ('FONTNAME', (0, 0), (-1, 0), 'BeVietnam-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('FONTNAME', (0, 1), (-1, -1), 'BeVietnam'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#333333')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#F2F7FB'), HexColor('#FFFFFF')]),
    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#D9D9D9')),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
]))
story.append(table)

doc.build(story)
```

## Đọc & Extract

```python
# Extract text
import pdfplumber
with pdfplumber.open('doc.pdf') as pdf:
    for page in pdf.pages:
        print(page.extract_text())

# Extract tables → DataFrame
import pandas as pd
with pdfplumber.open('doc.pdf') as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            df = pd.DataFrame(table[1:], columns=table[0])
            print(df)
```

## Merge / Split

```python
from pypdf import PdfReader, PdfWriter

# Merge
writer = PdfWriter()
for f in ['part1.pdf', 'part2.pdf', 'part3.pdf']:
    reader = PdfReader(f)
    for page in reader.pages:
        writer.add_page(page)
with open('merged.pdf', 'wb') as out:
    writer.write(out)

# Split
reader = PdfReader('big.pdf')
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f'page_{i+1}.pdf', 'wb') as out:
        writer.write(out)
```

## Fill PDF Form

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader('form.pdf')
writer = PdfWriter()
writer.append(reader)

writer.update_page_form_field_values(
    writer.pages[0],
    {
        'full_name': 'Nguyễn Văn A',
        'email': 'email@example.com',
        'date': '15/04/2026',
    }
)
with open('filled_form.pdf', 'wb') as out:
    writer.write(out)
```

## Convert — Pandoc

```bash
# Markdown → PDF (cần xelatex cho Vietnamese)
pandoc report.md -o report.pdf --pdf-engine=xelatex

# DOCX → PDF
pandoc report.docx -o report.pdf

# HTML → PDF
pandoc report.html -o report.pdf
```

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| Tiếng Việt □□□ | Dùng font core (Helvetica/Arial) | **Dùng Be Vietnam Pro** — add_font() trước |
| `•` hoặc `—` crash | Font core không có Unicode | Dùng Be Vietnam Pro hoặc Inter |
| f-string `{nb}` lỗi | alias_nb_pages placeholder | Escape: `f'Trang {self.page_no()}/{{nb}}'` |
| Table tràn page | Table quá rộng | Giảm colWidths, chia nhỏ table |
| reportlab encoding error | Chưa register font | `pdfmetrics.registerFont(TTFont(...))` |
| Merge bị lỗi page size | PDF sources khác kích thước | Set uniform page size trước merge |
