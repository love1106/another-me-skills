---
name: am-document-skills
version: 1.0.0
author: khoidoan
description: >
  Create professional documents: PDF, Word (DOCX), Excel (XLSX), PowerPoint (PPTX).
  Use when: user needs reports, invoices, spreadsheets, presentations, meeting notes,
  proposals, or any document file. Also handles reading, editing, converting between formats,
  and filling templates (keep layout, replace content).
  Triggers: "tạo báo cáo", "tạo file", "create report", "make PDF", "tạo Excel",
  "tạo slide", "tạo hóa đơn", "create invoice", "convert to PDF", "chuyển sang Word",
  "tạo biên bản", "make spreadsheet", "create presentation",
  "giữ template", "thay nội dung", "fill template", "điền vào mẫu".
  NOT for: image generation, web scraping, database operations, code generation.
---
<!-- Converted from hc-document-skills v1.3.0 -->

# Document Skills — Tạo File Chuyên Nghiệp

## Khi Nào Dùng Skill Này

User yêu cầu tạo, sửa, hoặc convert file:
- Báo cáo (report) → DOCX hoặc PDF
- Bảng tính, data → XLSX
- Trình bày (presentation) → PPTX
- Hóa đơn, hợp đồng → PDF
- Convert giữa các format
- Giữ template, thay nội dung (fill template)

## Decision Tree — PHẢI THEO THỨ TỰ

```
User cần gì?
│
├── Tạo file MỚI
│   ├── Báo cáo / Hợp đồng / Thư / Proposal → docs/docx.md (+ templates/)
│   ├── Bảng tính / Data / Financial model → docs/xlsx.md
│   ├── PDF report / Invoice / Certificate → docs/pdf.md (+ templates/)
│   └── Slide / Presentation → docs/pptx.md
│
├── SỬA file có sẵn
│   ├── .docx → docs/docx.md § "Editing"
│   ├── .xlsx → docs/xlsx.md § "Editing"
│   ├── .pdf → docs/pdf.md § "Editing"
│   └── .pptx → docs/pptx.md § "Editing"
│
├── GIỮ TEMPLATE, THAY NỘI DUNG (user gửi file mẫu)
│   └── Mọi format → docs/template-fill.md
│
├── ĐỌC / EXTRACT data
│   ├── PDF → docs/pdf.md § "Extract"
│   ├── Excel → docs/xlsx.md § "Reading"
│   └── Word/PPT → dùng pandoc convert sang markdown
│
└── CONVERT format
    └── docs/cross-format.md
```

## Quy Tắc Bắt Buộc (MỌI FORMAT)

### 0. Tiếng Việt LUÔN CÓ DẤU

Nội dung tiếng Việt **BẮT BUỘC** phải có dấu — không bao giờ bỏ dấu.
Áp dụng cho MỌI format (DOCX, XLSX, PDF, PPTX), MỌI vị trí (title, heading, body, table, header, footer, chart labels, slide text).

Arial, Be Vietnam Pro đều hỗ trợ Unicode tiếng Việt đầy đủ — không có lý do bỏ dấu.

### 1. Font Standards

**Ngôn ngữ xác định font (thứ tự ưu tiên):**

| Nội dung | Primary | Fallback 1 | Fallback 2 |
|----------|---------|------------|------------|
| Tiếng Việt (có dấu) | **Be Vietnam Pro** | Arial | DejaVu Sans |
| English | **Inter** | Arial | Helvetica |
| Monospace / Code | **Courier New** | monospace | — |
| PPTX (web-safe, có dấu VN) | **Arial** | Tahoma | Verdana |

**Be Vietnam Pro font paths** (Linux default — dùng `fc-list` để auto-detect):
```
/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-Regular.ttf
/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-Bold.ttf
/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-Italic.ttf
/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-BoldItalic.ttf
/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-Medium.ttf
/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-SemiBold.ttf
/usr/share/fonts/truetype/be-vietnam-pro/BeVietnamPro-Light.ttf
```

**Inter font paths** (Linux default — dùng `fc-list` để auto-detect):
```
/usr/share/fonts/truetype/inter/Inter-Regular.ttf
/usr/share/fonts/truetype/inter/Inter-Bold.ttf
/usr/share/fonts/truetype/inter/Inter-Italic.ttf
/usr/share/fonts/truetype/inter/Inter-BoldItalic.ttf
/usr/share/fonts/truetype/inter/Inter-Medium.ttf
/usr/share/fonts/truetype/inter/Inter-MediumItalic.ttf
/usr/share/fonts/truetype/inter/Inter-SemiBold.ttf
/usr/share/fonts/truetype/inter/Inter-SemiBoldItalic.ttf
/usr/share/fonts/truetype/inter/Inter-Light.ttf
/usr/share/fonts/truetype/inter/Inter-LightItalic.ttf
```

**Quy tắc chọn font (theo ngôn ngữ):**
1. **Tiếng Việt** → Be Vietnam Pro → Arial (fallback) → DejaVu Sans
2. **English** → Inter → Arial (fallback)
3. **Luôn check font trước**: `fc-list | grep -i vietnam` hoặc `fc-list | grep -i inter`
4. PDF (fpdf2): PHẢI `add_font()` trước khi dùng — font core (Helvetica, Arial) KHÔNG hỗ trợ Unicode
5. DOCX/XLSX: Vietnamese → Be Vietnam Pro, English → Inter. Font render phụ thuộc máy mở file
6. PPTX: Chỉ dùng web-safe fonts (Arial, Verdana...) — Be Vietnam Pro/Inter có thể không có trên máy người xem

**Detect font path (multi-OS):**
```bash
# Tìm font path tự động
BVP_PATH=$(fc-list | grep -i "Be Vietnam Pro" | head -1 | cut -d: -f1 | xargs dirname 2>/dev/null)
INTER_PATH=$(fc-list | grep -i "Inter" | head -1 | cut -d: -f1 | xargs dirname 2>/dev/null)
echo "Be Vietnam Pro: ${BVP_PATH:-NOT FOUND}"
echo "Inter: ${INTER_PATH:-NOT FOUND}"
```

**Cài font Be Vietnam Pro (nếu chưa có):**
```bash
# Download từ google/fonts repo
FONT_DIR="/usr/share/fonts/truetype/be-vietnam-pro"  # Linux default
mkdir -p "$FONT_DIR"
BASE="https://raw.githubusercontent.com/google/fonts/main/ofl/bevietnampro"
for v in Regular Bold Italic BoldItalic Medium SemiBold Light; do
  curl -sL -o "${FONT_DIR}/BeVietnamPro-${v}.ttf" "${BASE}/BeVietnamPro-${v}.ttf"
done
fc-cache -f
```

### 2. Page Layout — A4

| Property | Value |
|----------|-------|
| Page size | 210 × 297 mm (A4) |
| Top margin | 2.54 cm (1 inch) |
| Bottom margin | 2.54 cm (1 inch) |
| Left margin | 3.18 cm (1.25 inch) |
| Right margin | 2.54 cm (1 inch) |
| Line spacing | 1.15 |
| Paragraph spacing after | 6pt |

### 3. Color System

**Primary palette (business documents):**

| Role | Hex | Dùng cho |
|------|-----|----------|
| Primary | `#2B579A` | Headers, table header background |
| Primary Dark | `#1B3A65` | Heading text |
| Accent | `#2E75B6` | Links, highlights |
| Text | `#333333` | Body text |
| Text Light | `#666666` | Secondary text, captions |
| Border | `#D9D9D9` | Table borders, dividers |
| Background Light | `#F2F7FB` | Alternating row, callout boxes |
| White | `#FFFFFF` | Background, table header text |
| Success | `#28A745` | Positive values |
| Danger | `#DC3545` | Negative values, warnings |

### 4. Font Size Scale

| Element | Size (pt) |
|---------|-----------|
| Document title | 24 |
| Section heading (H1) | 18 |
| Sub-heading (H2) | 14 |
| Sub-sub-heading (H3) | 12 bold |
| Body text | 11 |
| Table content | 10 |
| Caption / Footer | 9 |
| Page number | 9 |

### 5. Number & Date Format (Vietnamese)

| Type | Format | Example |
|------|--------|---------|
| Date | dd/MM/yyyy | 15/04/2026 |
| Currency VND | #.##0 ₫ | 1.500.000 ₫ |
| Currency USD | $#,##0.00 | $1,500.00 |
| Percentage | 0,0% | 15,5% |
| Phone | +84 xxx xxx xxx | +84 909 623 304 |
| Negative number | (1.500) hoặc -1.500 | Dùng ngoặc cho financial |

### 6. Output Checklist — CHẠY SAU MỖI FILE

Sau khi tạo file, verify:

- [ ] File mở được không lỗi
- [ ] Font hiển thị đúng (không bị fallback □□□)
- [ ] Tiếng Việt có dấu đầy đủ (KHÔNG BAO GIỊ bỏ dấu)
- [ ] Page size đúng A4
- [ ] Margins đúng spec
- [ ] Header/Footer có (nếu multi-page)
- [ ] Page numbers có (nếu > 1 trang)
- [ ] Bảng biểu alignment đúng
- [ ] Màu sắc nhất quán theo palette
- [ ] Không có text overflow / bị cắt

## Dependencies

```bash
# Python (pip install)
pip install python-docx openpyxl fpdf2 python-pptx reportlab pdfplumber pypdf pandas matplotlib

# System tools
apt-get install -y pandoc poppler-utils qpdf libreoffice-calc

# Node.js (npm install) — cho DOCX nâng cao + PPTX
npm install docx pptxgenjs puppeteer
```

## Quick Reference — Chọn Tool

| Task | Tool | Khi nào |
|------|------|---------|
| Tạo DOCX đơn giản | `python-docx` | Report, letter, basic docs |
| Tạo DOCX phức tạp | `docx` (npm) | TOC, footnotes, complex styles |
| Sửa DOCX có sẵn | `python-docx` hoặc OOXML trực tiếp | Giữ formatting gốc |
| Tạo XLSX | `openpyxl` | Formulas, formatting, charts |
| Phân tích data XLSX | `pandas` + `openpyxl` | Read, filter, pivot |
| Tạo PDF từ scratch | `fpdf2` | Đơn giản, nhẹ, nhanh |
| Tạo PDF phức tạp | `reportlab` | Multi-page, tables, images |
| Đọc/merge/split PDF | `pypdf` + `pdfplumber` | Extract, merge, split |
| Tạo PPTX | `python-pptx` | Slides, charts, shapes |
| Convert formats | `pandoc` CLI | MD↔DOCX↔PDF↔HTML |

## Permissions

- **reads:** input files (DOCX, XLSX, PDF, PPTX, CSV, JSON), font files
- **writes:** output document files to workspace/outbound
- **third-party:** none
- **destructive:** none — only creates new files, never modifies source
- **requires_confirmation:** none

## References

- [references/charts-matplotlib.md](references/charts-matplotlib.md) — Chart/visualization templates

## Docs Chi Tiết

- [docs/docx.md](docs/docx.md) — Word: tạo, sửa, tracked changes
- [docs/xlsx.md](docs/xlsx.md) — Excel: tạo, formulas, charts, data analysis
- [docs/pdf.md](docs/pdf.md) — PDF: tạo, merge, split, forms, OCR
- [docs/pptx.md](docs/pptx.md) — PowerPoint: tạo, layouts, design
- [docs/cross-format.md](docs/cross-format.md) — Workflows convert & combo
- [docs/template-fill.md](docs/template-fill.md) — Giữ template, thay nội dung (placeholder, form fill, overlay)

## Templates

- [templates/report.md](templates/report.md) — Business report structure
- [templates/invoice.md](templates/invoice.md) — Invoice / Hóa đơn
- [templates/proposal.md](templates/proposal.md) — Business proposal
- [templates/meeting-notes.md](templates/meeting-notes.md) — Meeting notes / Biên bản

## Ví Dụ Input → Output

Xem [docs/examples.md](docs/examples.md) — 9 ví dụ hoàn chỉnh: user nói gì → agent làm gì → output gì.

## Verify Script

Sau khi tạo file, **BẮT BUỘC** chạy verify:

```bash
python3 scripts/verify.py <file_path>
```

Checks:
- File mở được, không rỗng
- DOCX: fonts, headings, tables, header/footer, margins
- XLSX: formulas (PHẢI > 0), freeze panes, styling
- PDF: pages, Vietnamese rendering (không tofu □), metadata
- PPTX: slide count, aspect ratio, web-safe fonts

**Nếu có ❌ → FIX theo Error Recovery flow bên dưới.**

## Error Recovery — Verify Fail

Khi `verify.py` trả về ❌:

| Lỗi | Nguyên nhân thường gặp | Fix |
|------|-------------------|-----|
| Font □□□ / Tofu | Font chưa cài hoặc chưa `add_font()` | 1. `fc-list \| grep vietnam` 2. Cài font nếu thiếu 3. Đảm bảo `add_font()` trước `set_font()` |
| File không mở được | Code crash giữa chừng | Check Python traceback, fix logic, tạo lại |
| Formula = 0 (XLSX) | Hardcode giá trị thay vì formula | Thay bằng `=SUM(...)`, `=AVERAGE(...)` |
| No headings (DOCX) | Dùng `add_paragraph` thay vì `add_heading` | Đổi sang `doc.add_heading(text, level=N)` |
| Non-web-safe font (PPTX) | Dùng Be Vietnam Pro trong PPTX | Đổi sang Arial |
| Vietnamese renders FAIL | `add_font()` sai path | Check `ls /usr/share/fonts/truetype/be-vietnam-pro/` |

**Retry flow:**
1. Đọc lỗi từ verify output
2. Fix code theo bảng trên
3. Tạo lại file
4. Chạy `verify.py` lần 2
5. Vẫn fail → đọc doc tương ứng (`docs/pdf.md`, `docs/docx.md`...) tìm root cause
6. Tối đa 3 lần retry → báo user kèm error details
