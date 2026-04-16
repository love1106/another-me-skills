# Ví Dụ Input → Output

Mỗi ví dụ cho thấy: user nói gì → agent PHẢI làm gì → output format nào.

---

## Ví dụ 1: Tạo báo cáo doanh thu (DOCX)

**User:** "Tạo báo cáo doanh thu Q1/2026, doanh thu Bắc 5 tỷ, Trung 3 tỷ, Nam 7 tỷ"

**Agent PHẢI:**
1. Xác định: báo cáo → dùng template report → format DOCX
2. Đọc `docs/docx.md` → lấy template code
3. Thay data vào template:
   - Title: "Báo Cáo Doanh Thu Q1/2026"
   - Table data: 3 rows (Bắc/Trung/Nam + số liệu)
   - Tổng = SUM
4. Apply styles theo SKILL.md (font Be Vietnam Pro, colors, margins)
5. Save file
6. Verify checklist
7. Gửi file cho user

**Output:** File `bao-cao-doanh-thu-q1-2026.docx`

---

## Ví dụ 2: Tạo hóa đơn (PDF)

**User:** "Tạo hóa đơn cho Công ty ABC, 10h tư vấn AI giá 5tr/h, 1 chatbot 50tr"

**Agent PHẢI:**
1. Xác định: hóa đơn → dùng template invoice → format PDF
2. Đọc `templates/invoice.md` → lấy function `create_invoice()`
3. Fill params:
   - customer_name: "Công Ty ABC"
   - items: [("Tư vấn AI", 10, 5000000), ("Phát triển chatbot", 1, 50000000)]
   - VAT 10%
4. Chạy script
5. Verify: file mở được, tiếng Việt đúng dấu, tổng tiền đúng
6. Gửi file cho user

**Output:** File `invoice.pdf` — 1 trang A4

---

## Ví dụ 3: Tạo bảng tính phân tích (XLSX)

**User:** "Tạo Excel so sánh doanh thu 4 quý 2025 cho 3 khu vực Bắc Trung Nam"

**Agent PHẢI:**
1. Xác định: bảng tính + data → format XLSX
2. Đọc `docs/xlsx.md` → lấy template code
3. Tạo workbook:
   - Sheet "Doanh Thu": header row + data 3×4 + formulas SUM/AVERAGE
   - Styled: header #2B579A, alternating rows, number format #,##0
   - Chart: clustered bar chart
4. **FORMULAS, KHÔNG HARDCODE** — `=SUM(B5:E5)`, không tính Python rồi ghi số
5. Column widths, freeze panes
6. Save + verify
7. Gửi file cho user

**Output:** File `doanh-thu-2025.xlsx` — 1 sheet data + chart

---

## Ví dụ 4: Tạo slide trình bày (PPTX)

**User:** "Tạo slide 5 trang về kết quả kinh doanh 2025"

**Agent PHẢI:**
1. Xác định: presentation → format PPTX
2. Đọc `docs/pptx.md` → chọn color palette (Business/Corporate)
3. Plan 5 slides:
   - Slide 1: Title "Kết Quả Kinh Doanh 2025"
   - Slide 2: Agenda (4 mục)
   - Slide 3: KPI cards (doanh thu, lợi nhuận, tăng trưởng)
   - Slide 4: Table chi tiết
   - Slide 5: Kế hoạch 2026
4. Dùng python-pptx, font Arial (web-safe), 16:9
5. Tối đa 6 dòng text / slide
6. Save + verify
7. Gửi file cho user

**Output:** File `ket-qua-kd-2025.pptx` — 5 slides

---

## Ví dụ 5: Convert format

**User:** "Chuyển file report.docx sang PDF"

**Agent PHẢI:**
1. Xác định: convert → đọc `docs/cross-format.md`
2. Chạy: `pandoc report.docx -o report.pdf`
3. Nếu có tiếng Việt: `pandoc report.docx -o report.pdf --pdf-engine=xelatex`
4. Verify: file mở được, không lỗi font
5. Gửi file cho user

---

## Ví dụ 6: Tạo biên bản họp (DOCX)

**User:** "Ghi biên bản cuộc họp hôm nay: tham dự có Khôi, Lan, Minh. Quyết định deploy v2 ngày 20/4. Action: Khôi review code trước 18/4, Lan test QA trước 19/4"

**Agent PHẢI:**
1. Xác định: meeting notes → template meeting-notes → DOCX
2. Đọc `templates/meeting-notes.md` → structure
3. Fill:
   - Thành viên: Khôi ✅, Lan ✅, Minh ✅
   - Quyết định: Deploy v2 ngày 20/04/2026
   - Action items table: 2 rows (Khôi review 18/4, Lan test 19/4)
4. Apply styles, save
5. Gửi file

---

## Ví dụ 7: English report (PDF)

**User:** "Create a PDF report about Q1 2026 revenue, in English"

**Agent PHẢI:**
1. Xác định: English → dùng Inter font, lang='en'
2. Đọc `docs/pdf.md` → dùng ReportPDF class với `lang='en'`
3. Tạo content bằng tiếng Anh
4. Save + verify
5. Gửi file

---

## Ví dụ 8: Giữ template, thay nội dung (DOCX)

**User:** gửi file `hop-dong-mau.docx` + "Thay tên khách hàng thành Công Ty XYZ, ngày ký 20/04/2026, giá trị 200 triệu"

**Agent PHẢI:**
1. Xác định: giữ template, thay nội dung → đọc `docs/template-fill.md`
2. Backup file gốc: `shutil.copy('hop-dong-mau.docx', 'hop-dong-mau_backup.docx')`
3. Mở file, tìm text cần thay:
   - Tìm placeholder (`{{TEN_KH}}`) hoặc text cụ thể ("Tên khách hàng")
   - Thay qua `run.text` — KHÔNG dùng `para.text =` (mất formatting)
4. Save output.docx
5. Verify: layout giữ nguyên, data thay đúng, font không bị phá
6. Gửi file cho user

**Output:** File `hop-dong-xyz.docx` — layout y hệt mẫu, chỉ thay data

---

## Ví dụ 9: Fill data vào Excel template

**User:** gửi file `bao-cao-mau.xlsx` + "Cập nhật doanh thu tháng 3: Bắc 2 tỷ, Trung 1.5 tỷ, Nam 3 tỷ"

**Agent PHẢI:**
1. Xác định: giữ template Excel → `docs/template-fill.md` § XLSX
2. Backup file gốc
3. `load_workbook('bao-cao-mau.xlsx')` — KHÔNG `data_only=True`
4. Thay `cell.value` — formatting + formulas giữ nguyên
5. Save + verify
6. Gửi file

**Output:** File `bao-cao-t3.xlsx` — formulas tự recalculate

---

## Quy Tắc Chung

1. **Luôn xác định ngôn ngữ trước** → Vietnamese = Be Vietnam Pro, English = Inter
2. **Luôn đọc doc tương ứng** trước khi code — không code từ trí nhớ
3. **Copy template code, thay data** — không viết từ đầu
4. **Formulas cho Excel** — KHÔNG BAO GIỜ hardcode calculated values
5. **Verify sau khi tạo** — mở file, check font, check data
6. **Gửi file cho user** kèm mô tả ngắn nội dung
