# PowerPoint (PPTX) — Hướng Dẫn Chi Tiết

## Tạo PPTX Mới — python-pptx

### Step-by-step

1. Import + tạo Presentation
2. Set slide size (16:9)
3. Thêm slides theo layout
4. Apply styling (colors, fonts)
5. Save file
6. Verify bằng checklist

### Design Rules — BẮT BUỘC

Trước khi tạo bất kỳ slide nào:

1. **Xác định chủ đề** → chọn color palette phù hợp
2. **Chỉ dùng web-safe fonts**: Arial, Verdana, Tahoma, Georgia, Times New Roman, Trebuchet MS
3. **Tối đa 6 dòng text / slide** — ít text hơn = tốt hơn
4. **Contrast ratio tối thiểu 4.5:1** cho text trên background
5. **Consistent spacing** — dùng cùng padding/margin xuyên suốt

### Color Palettes — Chọn 1 Theo Chủ Đề

**Business / Corporate:**
- Primary: `#1B3A65` (navy) | Accent: `#2E75B6` (blue) | BG: `#FFFFFF` | Text: `#333333`

**Technology / Modern:**
- Primary: `#0D1117` (dark) | Accent: `#58A6FF` (bright blue) | BG: `#161B22` | Text: `#E6EDF3`

**Creative / Bold:**
- Primary: `#E74C3C` (red) | Accent: `#F39C12` (orange) | BG: `#FFFFFF` | Text: `#2C3E50`

**Healthcare / Trust:**
- Primary: `#0E6655` (teal) | Accent: `#48C9B0` (light teal) | BG: `#FFFFFF` | Text: `#2C3E50`

**Finance / Premium:**
- Primary: `#1C2833` (charcoal) | Accent: `#BF9A4A` (gold) | BG: `#F8F9FA` | Text: `#2C3E50`

### Template Code — Business Presentation

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

# ⚠️ PPTX: CHỈ DÙNG WEB-SAFE FONTS (Arial, Verdana, Tahoma...)
# Khác với DOCX/PDF/XLSX — PPTX render trên máy người xem,
# Be Vietnam Pro / Inter có thể không có → bị fallback xấu.
# Font: Arial (hỗ trợ tiếng Việt có dấu ✓)

prs = Presentation()

# 16:9 slide size
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# ============================================================
# COLORS — Define once
# ============================================================
PRIMARY = RGBColor(0x1B, 0x3A, 0x65)     # Navy
ACCENT = RGBColor(0x2E, 0x75, 0xB6)      # Blue
TEXT_DARK = RGBColor(0x33, 0x33, 0x33)    # Dark gray
TEXT_LIGHT = RGBColor(0xFF, 0xFF, 0xFF)   # White
BG_LIGHT = RGBColor(0xF2, 0xF7, 0xFB)    # Light blue bg
BORDER = RGBColor(0xD9, 0xD9, 0xD9)      # Gray border


def add_background(slide, color):
    """Set solid background color."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(slide, text, left, top, width, height,
                font_size=18, bold=False, color=TEXT_DARK,
                alignment=PP_ALIGN.LEFT, font_name='Arial'):
    """Add styled textbox."""
    txBox = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = alignment
    return txBox


def add_shape_bg(slide, left, top, width, height, color):
    """Add colored rectangle shape."""
    from pptx.enum.shapes import MSO_SHAPE
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


# ============================================================
# SLIDE 1: Title Slide
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
add_background(slide, PRIMARY)

# Accent bar on left
add_shape_bg(slide, 0, 0, 0.15, 7.5, ACCENT)

# Title
add_textbox(slide, 'BÁO CÁO DOANH THU', 1.5, 2.0, 10, 1.5,
            font_size=40, bold=True, color=TEXT_LIGHT)

# Subtitle
add_textbox(slide, 'Quý 1 Năm 2026', 1.5, 3.8, 8, 0.8,
            font_size=20, color=RGBColor(0xAA, 0xBB, 0xCC))

# Date & Author
add_textbox(slide, '15/04/2026  |  Công Ty ABC', 1.5, 5.0, 6, 0.5,
            font_size=14, color=RGBColor(0x88, 0x99, 0xAA))


# ============================================================
# SLIDE 2: Agenda / TOC
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])

# Header bar
add_shape_bg(slide, 0, 0, 13.333, 1.2, PRIMARY)
add_textbox(slide, 'NỘI DUNG', 0.8, 0.2, 6, 0.8,
            font_size=28, bold=True, color=TEXT_LIGHT)

# Agenda items
items = [
    '01    Tổng Quan Kết Quả',
    '02    Doanh Thu Theo Khu Vực',
    '03    Phân Tích Chi Phí',
    '04    Kế Hoạch Q2/2026',
]
for i, item in enumerate(items):
    y = 1.8 + i * 1.2
    add_textbox(slide, item, 1.5, y, 10, 0.8,
                font_size=22, color=TEXT_DARK)
    # Divider line
    if i < len(items) - 1:
        from pptx.util import Inches as In
        shape = slide.shapes.add_connector(
            1, Inches(1.5), Inches(y + 1.0), Inches(11.5), Inches(y + 1.0)
        )


# ============================================================
# SLIDE 3: Content Slide with Key Numbers
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])

# Header bar
add_shape_bg(slide, 0, 0, 13.333, 1.2, PRIMARY)
add_textbox(slide, 'TỔNG QUAN KẾT QUẢ', 0.8, 0.2, 8, 0.8,
            font_size=28, bold=True, color=TEXT_LIGHT)

# KPI cards
kpis = [
    ('17 TỶ', 'Tổng Doanh Thu', '+23%'),
    ('9 TỶ', 'Tổng Chi Phí', '+15%'),
    ('8 TỶ', 'Lợi Nhuận Ròng', '+35%'),
]
for i, (value, label, change) in enumerate(kpis):
    x = 1.0 + i * 4.0
    # Card background
    add_shape_bg(slide, x, 2.0, 3.5, 3.0, BG_LIGHT)
    # Value
    add_textbox(slide, value, x + 0.3, 2.3, 3, 1.0,
                font_size=36, bold=True, color=PRIMARY,
                alignment=PP_ALIGN.CENTER)
    # Label
    add_textbox(slide, label, x + 0.3, 3.5, 3, 0.5,
                font_size=14, color=TEXT_DARK,
                alignment=PP_ALIGN.CENTER)
    # Change
    change_color = RGBColor(0x28, 0xA7, 0x45) if '+' in change else RGBColor(0xDC, 0x35, 0x45)
    add_textbox(slide, change, x + 0.3, 4.1, 3, 0.5,
                font_size=16, bold=True, color=change_color,
                alignment=PP_ALIGN.CENTER)


# ============================================================
# SLIDE 4: Table Slide
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])

# Header bar
add_shape_bg(slide, 0, 0, 13.333, 1.2, PRIMARY)
add_textbox(slide, 'DOANH THU THEO KHU VỰC', 0.8, 0.2, 8, 0.8,
            font_size=28, bold=True, color=TEXT_LIGHT)

# Table
from pptx.util import Inches
rows, cols = 5, 4
table_shape = slide.shapes.add_table(
    rows, cols,
    Inches(1.5), Inches(1.8), Inches(10.5), Inches(4.5)
)
table = table_shape.table

# Set column widths
table.columns[0].width = Inches(0.8)
table.columns[1].width = Inches(3.0)
table.columns[2].width = Inches(3.35)
table.columns[3].width = Inches(3.35)

# Header
header_data = ['STT', 'Khu Vực', 'Doanh Thu', 'Lợi Nhuận']
for i, text in enumerate(header_data):
    cell = table.cell(0, i)
    cell.text = text
    cell.fill.solid()
    cell.fill.fore_color.rgb = PRIMARY
    for paragraph in cell.text_frame.paragraphs:
        paragraph.font.size = Pt(12)
        paragraph.font.bold = True
        paragraph.font.color.rgb = TEXT_LIGHT
        paragraph.font.name = 'Arial'
        paragraph.alignment = PP_ALIGN.CENTER

# Data
table_data = [
    ['1', 'Miền Bắc',    '5,000,000,000', '2,000,000,000'],
    ['2', 'Miền Trung',   '3,000,000,000', '1,000,000,000'],
    ['3', 'Miền Nam',     '7,000,000,000', '3,000,000,000'],
    ['4', 'Online',       '2,000,000,000', '1,200,000,000'],
]
for row_idx, row_data in enumerate(table_data):
    for col_idx, text in enumerate(row_data):
        cell = table.cell(row_idx + 1, col_idx)
        cell.text = text
        # Alternating row
        if row_idx % 2 == 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = BG_LIGHT
        for paragraph in cell.text_frame.paragraphs:
            paragraph.font.size = Pt(11)
            paragraph.font.color.rgb = TEXT_DARK
            paragraph.font.name = 'Arial'


# ============================================================
# SAVE
# ============================================================
prs.save('presentation.pptx')
```

### Thêm Content Types

#### Image
```python
slide.shapes.add_picture('chart.png', Inches(1.5), Inches(2.0), width=Inches(8))
```

#### Chart (từ python-pptx)
```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

chart_data = CategoryChartData()
chart_data.categories = ['Q1', 'Q2', 'Q3', 'Q4']
chart_data.add_series('Doanh Thu', (5000, 6000, 7000, 8000))
chart_data.add_series('Chi Phi', (3000, 3500, 4000, 4500))

chart = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    Inches(1.5), Inches(2.0), Inches(10), Inches(5),
    chart_data
).chart
chart.has_legend = True
```

#### Speaker Notes
```python
notes_slide = slide.notes_slide
notes_slide.notes_text_frame.text = 'Ghi chú cho người trình bày.'
```

## Sửa PPTX Có Sẵn

```python
from pptx import Presentation

prs = Presentation('existing.pptx')

# Duyệt slides
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if 'OLD_TEXT' in run.text:
                        run.text = run.text.replace('OLD_TEXT', 'NEW_TEXT')

# Xóa slide (theo index)
# pptx không có delete trực tiếp — cần manipulate XML
rId = prs.slides._sldIdLst[2].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
prs.part.drop_rel(rId)
del prs.slides._sldIdLst[2]

prs.save('modified.pptx')
```

## Vietnamese Text trong PPTX

**Arial hỗ trợ tiếng Việt có dấu đầy đủ.** Mặc định tiếng Việt LUÔN CÓ DẤU — không bao giờ bỏ dấu.

**Quy tắc font PPTX:**
- **Arial** = font mặc định cho PPTX — có sẵn trên Windows/Mac/Linux, hỗ trợ Unicode tiếng Việt ✅
- **Tahoma, Verdana** = fallback, cũng hỗ trợ tiếng Việt ✅
- **KHÔNG dùng Be Vietnam Pro / Inter** cho PPTX — người xem có thể không có font → bị fallback xấu
- Luôn set `paragraph.font.name = 'Arial'` cho mọi text element

## Lỗi Thường Gặp

| Lỗi | Nguyên nhân | Fix |
|-----|-------------|-----|
| Text bị cắt | Textbox quá nhỏ | Tăng height hoặc giảm font size |
| Font bị đổi | Font không có trên máy mở | Chỉ dùng web-safe fonts |
| Background trắng | Không set fill | `slide.background.fill.solid()` |
| Table layout lệch | Column width không đủ | Tính tổng width = slide width - margins |
| Chart không hiện | Missing chart data | Đảm bảo có ít nhất 1 series + categories |
