# Template Fill — Giữ Template, Thay Nội Dung

User gửi file mẫu (DOCX, XLSX, PDF, PPTX) + yêu cầu thay đổi nội dung → giữ nguyên layout/style.

## Nguyên Tắc Chung

1. **KHÔNG tạo file mới từ đầu** — mở file gốc, sửa in-place
2. **Giữ nguyên formatting** — font, size, color, alignment, margins, header/footer
3. **Chỉ thay text/data** — không thêm/xóa section trừ khi user yêu cầu
4. **Backup trước khi sửa** — copy file gốc sang `{name}_backup.{ext}`
5. **So sánh trước/sau** — verify structure không bị phá

## DOCX — Giữ Template Thay Nội Dung

### Cách 1: Placeholder Replacement (Khuyến nghị)

Nếu file template có placeholder (VD: `{{TEN_KHACH_HANG}}`, `[COMPANY]`, `___`):

```python
from docx import Document
import shutil

# Backup
shutil.copy('template.docx', 'template_backup.docx')

doc = Document('template.docx')

# Define replacements
replacements = {
    '{{TEN_KHACH_HANG}}': 'Công Ty ABC',
    '{{NGAY}}': '16/04/2026',
    '{{SO_HOP_DONG}}': 'HD-2026-0042',
    '{{GIA_TRI}}': '500.000.000 ₫',
}

# Replace trong paragraphs — GIỮ NGUYÊN formatting của run
for para in doc.paragraphs:
    for key, value in replacements.items():
        if key in para.text:
            for run in para.runs:
                if key in run.text:
                    run.text = run.text.replace(key, value)

# Replace trong tables
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                for key, value in replacements.items():
                    if key in para.text:
                        for run in para.runs:
                            if key in run.text:
                                run.text = run.text.replace(key, value)

# Replace trong headers/footers
for section in doc.sections:
    for para in section.header.paragraphs:
        for key, value in replacements.items():
            if key in para.text:
                for run in para.runs:
                    if key in run.text:
                        run.text = run.text.replace(key, value)
    for para in section.footer.paragraphs:
        for key, value in replacements.items():
            if key in para.text:
                for run in para.runs:
                    if key in run.text:
                        run.text = run.text.replace(key, value)

doc.save('output.docx')
```

### Cách 2: Run-level Replacement (Xử lý placeholder bị split)

python-docx có thể split placeholder thành nhiều runs (VD: `{{TEN` + `_KHACH` + `_HANG}}`).

```python
from docx import Document
import re

def replace_in_paragraph(para, replacements):
    """Replace text trong paragraph, xử lý split-run.
    
    Cách hoạt động:
    1. Ghép toàn bộ runs thành 1 string
    2. Tìm & replace
    3. Phân phối text mới lại vào runs (giữ formatting run đầu)
    """
    full_text = ''.join(run.text for run in para.runs)
    
    changed = False
    for key, value in replacements.items():
        if key in full_text:
            full_text = full_text.replace(key, value)
            changed = True
    
    if not changed:
        return
    
    # Redistribute text vào runs — giữ formatting run đầu tiên
    if para.runs:
        para.runs[0].text = full_text
        for run in para.runs[1:]:
            run.text = ''


def fill_template(template_path, output_path, replacements):
    """Fill template DOCX với replacements dict."""
    doc = Document(template_path)
    
    # Paragraphs
    for para in doc.paragraphs:
        replace_in_paragraph(para, replacements)
    
    # Tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    replace_in_paragraph(para, replacements)
    
    # Headers & Footers
    for section in doc.sections:
        for para in section.header.paragraphs:
            replace_in_paragraph(para, replacements)
        for para in section.footer.paragraphs:
            replace_in_paragraph(para, replacements)
    
    doc.save(output_path)


# Sử dụng:
# fill_template('template.docx', 'output.docx', {
#     '{{NAME}}': 'Nguyễn Văn A',
#     '{{DATE}}': '16/04/2026',
# })
```

### Cách 3: Thay nội dung theo vị trí (không có placeholder)

Khi template KHÔNG có placeholder — phải tìm theo text content:

```python
from docx import Document

doc = Document('template.docx')

# Tìm paragraph chứa text cụ thể → thay nội dung
for para in doc.paragraphs:
    # Thay text cụ thể, giữ style
    if 'Tên công ty' in para.text:
        for run in para.runs:
            run.text = run.text.replace('Tên công ty', 'Công Ty ABC')
    
    # Thay toàn bộ paragraph text (giữ style run đầu)
    if para.text.strip() == 'Nội dung cần thay':
        if para.runs:
            para.runs[0].text = 'Nội dung mới'
            for run in para.runs[1:]:
                run.text = ''

doc.save('output.docx')
```

### ⚠️ Lưu ý DOCX

- **Không dùng `para.text = 'xxx'`** — sẽ xóa hết runs, mất formatting
- **Luôn sửa qua `run.text`** — giữ được font, size, color, bold/italic
- **Nested tables** — cần recursive traverse
- **Content Controls (form fields)** — cần access qua XML: `doc.element.findall()`

---

## XLSX — Giữ Template Thay Data

### Cách 1: Thay cell values trực tiếp

```python
from openpyxl import load_workbook
import shutil

# Backup
shutil.copy('template.xlsx', 'template_backup.xlsx')

# ⚠️ KHÔNG dùng data_only=True — sẽ MẤT formulas
wb = load_workbook('template.xlsx')
ws = wb.active

# Thay data — GIỮ NGUYÊN formatting, formulas
ws['B2'] = 'Công Ty ABC'          # Text
ws['C5'] = 5000000000              # Number — format giữ nguyên
ws['C6'] = 3000000000
ws['D2'] = '16/04/2026'           # Date as string

# KHÔNG ĐỤNG cells có formula — chúng tự recalculate
# VD: C10 = =SUM(C5:C9) → giữ nguyên, chỉ thay C5:C9

wb.save('output.xlsx')
```

### Cách 2: Thay data theo range (batch)

```python
from openpyxl import load_workbook

wb = load_workbook('template.xlsx')
ws = wb.active

# Data mới — list of rows
new_data = [
    ['Miền Bắc', 5000000000, 3000000000],
    ['Miền Trung', 3000000000, 2000000000],
    ['Miền Nam', 7000000000, 4000000000],
]

# Thay data từ row 5, col B
start_row = 5
for i, row_data in enumerate(new_data):
    for j, value in enumerate(row_data):
        ws.cell(row=start_row + i, column=2 + j, value=value)
        # Formatting giữ nguyên — chỉ thay .value

wb.save('output.xlsx')
```

### Cách 3: Thay placeholder trong cells

```python
from openpyxl import load_workbook

wb = load_workbook('template.xlsx')

replacements = {
    '{{COMPANY}}': 'Công Ty ABC',
    '{{PERIOD}}': 'Q1/2026',
    '{{AUTHOR}}': 'Nguyễn Khôi',
}

for ws in wb.worksheets:
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str):
                for key, value in replacements.items():
                    if key in cell.value:
                        cell.value = cell.value.replace(key, value)

wb.save('output.xlsx')
```

### ⚠️ Lưu ý XLSX

- **KHÔNG `data_only=True`** khi save — mất formulas
- **Chỉ thay `.value`** — `.font`, `.fill`, `.border`, `.number_format` giữ nguyên tự động
- **Formulas tự recalculate** khi mở trong Excel — không cần sửa formula cells
- **Merged cells** — chỉ thay cell trên-trái (top-left), cells khác trong merge là None
- **Charts** — tự update nếu data range không đổi

---

## PDF — Giữ Template Thay Nội Dung

PDF là format **read-only by design**. Có 3 approaches:

### Cách 1: Fill PDF Form Fields (Tốt nhất)

Nếu PDF có form fields (fillable PDF):

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader('template.pdf')
writer = PdfWriter()
writer.append(reader)

# Fill form fields
writer.update_page_form_field_values(
    writer.pages[0],
    {
        'ten_cong_ty': 'Công Ty ABC',
        'ngay': '16/04/2026',
        'so_hop_dong': 'HD-2026-0042',
        'gia_tri': '500.000.000 ₫',
    }
)

# Optional: flatten (make fields non-editable)
# for page in writer.pages:
#     page['/Annots'] = []  # Remove form annotations

with open('output.pdf', 'wb') as f:
    writer.write(f)
```

### Cách 2: Overlay Text lên PDF Template

Khi PDF KHÔNG có form fields — đặt text lên vị trí cụ thể:

```python
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter
import io

FONT_VN = '/usr/share/fonts/truetype/be-vietnam-pro'

def overlay_text_on_pdf(template_path, output_path, overlays):
    """Overlay text lên PDF template.
    
    overlays: list of dict:
        page: int (0-indexed)
        x: float (mm from left)
        y: float (mm from top)  
        text: str
        font_size: int (default 11)
        bold: bool (default False)
    """
    reader = PdfReader(template_path)
    writer = PdfWriter()
    
    # Group overlays by page
    page_overlays = {}
    for ov in overlays:
        pg = ov.get('page', 0)
        page_overlays.setdefault(pg, []).append(ov)
    
    for i, page in enumerate(reader.pages):
        if i in page_overlays:
            # Create overlay PDF
            overlay = FPDF()
            overlay.add_font('VN', '', f'{FONT_VN}/BeVietnamPro-Regular.ttf')
            overlay.add_font('VN', 'B', f'{FONT_VN}/BeVietnamPro-Bold.ttf')
            overlay.add_page()
            overlay.set_auto_page_break(False)
            
            for ov in page_overlays[i]:
                style = 'B' if ov.get('bold') else ''
                overlay.set_font('VN', style, ov.get('font_size', 11))
                overlay.set_text_color(51, 51, 51)
                overlay.set_xy(ov['x'], ov['y'])
                overlay.cell(0, 0, ov['text'])
            
            overlay_bytes = overlay.output()
            overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
            page.merge_page(overlay_reader.pages[0])
        
        writer.add_page(page)
    
    with open(output_path, 'wb') as f:
        writer.write(f)


# Sử dụng — cần xác định tọa độ (x, y) bằng cách đo trên PDF
# overlay_text_on_pdf('template.pdf', 'output.pdf', [
#     {'page': 0, 'x': 50, 'y': 85, 'text': 'Công Ty ABC', 'bold': True},
#     {'page': 0, 'x': 50, 'y': 95, 'text': '16/04/2026'},
#     {'page': 0, 'x': 120, 'y': 85, 'text': '500.000.000 ₫'},
# ])
```

### Cách 3: PDF → DOCX → Edit → PDF (Last resort)

Khi PDF phức tạp, không có form, overlay khó:

```bash
# Convert PDF → DOCX (giữ layout tương đối)
libreoffice --headless --convert-to docx template.pdf

# Sửa DOCX (dùng python-docx — xem section DOCX ở trên)
# ...

# Convert DOCX → PDF
libreoffice --headless --convert-to pdf output.docx
```

⚠️ **Layout sẽ không 100% giống gốc** — chỉ dùng khi 2 cách trên không khả thi.

### ⚠️ Lưu ý PDF

- **PDF không thiết kế để edit** — overlay là cách tốt nhất
- **Tọa độ overlay** — cần đo thủ công hoặc dùng `pdfplumber` extract positions
- **Font phải add_font()** — không dùng font core cho Vietnamese
- **Flatten form** nếu muốn output không editable

---

## PPTX — Giữ Template Thay Nội Dung

### Cách 1: Thay text trong shapes

```python
from pptx import Presentation
import shutil

# Backup
shutil.copy('template.pptx', 'template_backup.pptx')

prs = Presentation('template.pptx')

replacements = {
    '{{TITLE}}': 'Báo Cáo Doanh Thu Q1/2026',
    '{{COMPANY}}': 'Công Ty ABC',
    '{{DATE}}': '16/04/2026',
    '{{REVENUE}}': '17 TỶ',
}

for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                for run in para.runs:
                    for key, value in replacements.items():
                        if key in run.text:
                            run.text = run.text.replace(key, value)
                            # Formatting (font, size, color) giữ nguyên
        
        # Tables trong slides
        if shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    for para in cell.text_frame.paragraphs:
                        for run in para.runs:
                            for key, value in replacements.items():
                                if key in run.text:
                                    run.text = run.text.replace(key, value)

prs.save('output.pptx')
```

### Cách 2: Thay data trong table (giữ style)

```python
from pptx import Presentation

prs = Presentation('template.pptx')

# Tìm slide có table (VD: slide 3)
slide = prs.slides[2]

for shape in slide.shapes:
    if shape.has_table:
        table = shape.table
        # Thay data — row 1+ (skip header row 0)
        new_data = [
            ['Miền Bắc', '5,000,000,000', '2,000,000,000'],
            ['Miền Trung', '3,000,000,000', '1,000,000,000'],
            ['Miền Nam', '7,000,000,000', '3,000,000,000'],
        ]
        for i, row_data in enumerate(new_data):
            for j, text in enumerate(row_data):
                cell = table.cell(i + 1, j)  # Skip header
                # Thay text — giữ formatting run đầu
                if cell.text_frame.paragraphs[0].runs:
                    cell.text_frame.paragraphs[0].runs[0].text = text
                    for run in cell.text_frame.paragraphs[0].runs[1:]:
                        run.text = ''
                else:
                    cell.text = text

prs.save('output.pptx')
```

### Cách 3: Thay hình ảnh (giữ vị trí & kích thước)

```python
from pptx import Presentation
from pptx.util import Inches

prs = Presentation('template.pptx')

for slide in prs.slides:
    for shape in slide.shapes:
        # Tìm hình cần thay — theo name hoặc alt text
        if shape.shape_type == 13:  # Picture
            if shape.name == 'chart_placeholder':
                # Lưu vị trí & kích thước
                left, top = shape.left, shape.top
                width, height = shape.width, shape.height
                
                # Xóa hình cũ
                sp = shape._element
                sp.getparent().remove(sp)
                
                # Thêm hình mới cùng vị trí
                slide.shapes.add_picture(
                    'new_chart.png', left, top, width, height
                )

prs.save('output.pptx')
```

### ⚠️ Lưu ý PPTX

- **Luôn sửa qua `run.text`** — không dùng `shape.text = 'xxx'` (mất formatting)
- **Slide master/layout** — không thay đổi, giữ nguyên theme
- **Charts** — python-pptx có thể update chart data trực tiếp
- **Grouped shapes** — cần iterate `shape.shapes` nếu shape là group

---

## Decision Flow — User Gửi File Template

```
User gửi file + yêu cầu thay nội dung
│
├── File có placeholder? ({{xxx}}, [xxx], ___)
│   ├── CÓ → Placeholder Replacement (Cách 1-2)
│   └── KHÔNG → Text-based search & replace (Cách 3)
│
├── Format?
│   ├── .docx → python-docx (giữ runs → giữ formatting)
│   ├── .xlsx → openpyxl (chỉ thay .value, KHÔNG data_only)
│   ├── .pdf → Form fields? → pypdf fill
│   │         Không form? → Overlay text (fpdf2 + merge)
│   │         Quá phức tạp? → PDF→DOCX→edit→PDF (last resort)
│   └── .pptx → python-pptx (runs trong shapes)
│
└── Verify
    ├── Mở file output — layout giữ nguyên?
    ├── Data thay đúng?
    ├── Formatting không bị phá?
    └── python3 scripts/verify.py output.{ext}
```

## Quy Tắc Bắt Buộc

1. **BACKUP file gốc trước khi sửa** — `shutil.copy()`
2. **KHÔNG tạo file mới** — mở file gốc, sửa in-place
3. **Sửa qua `run.text`** (DOCX/PPTX) hoặc `cell.value` (XLSX) — giữ formatting
4. **KHÔNG dùng `data_only=True`** cho XLSX — mất formulas
5. **PDF form fields > Overlay > Convert** — theo thứ tự ưu tiên
6. **Verify layout** sau khi thay — so sánh visual với file gốc
