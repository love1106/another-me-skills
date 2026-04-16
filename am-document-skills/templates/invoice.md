# Template: Invoice / Hóa Đơn

## Structure

```
Header: Logo + Tên công ty + Địa chỉ + MST
Thông tin HĐ: Số HĐ, Ngày, Hạn thanh toán
Khách hàng: Tên, Địa chỉ, MST
Bảng chi tiết: STT | Mô tả | SL | Đơn giá | Thành tiền
Tổng: Tạm tính → VAT → Tổng cộng
Thanh toán: Ngân hàng, STK, Chủ TK, Nội dung CK
Footer: Ghi chú / Điều khoản
```

## Quick-Start Code — PDF Invoice

```python
from fpdf import FPDF

FONT_VN = '/usr/share/fonts/truetype/be-vietnam-pro'


class InvoicePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font('VN', '', f'{FONT_VN}/BeVietnamPro-Regular.ttf')
        self.add_font('VN', 'B', f'{FONT_VN}/BeVietnamPro-Bold.ttf')
        self.add_font('VN', 'I', f'{FONT_VN}/BeVietnamPro-Italic.ttf')
        self.set_auto_page_break(auto=True, margin=15)


def create_invoice(
    company_name, company_address, company_tax_id,
    customer_name, customer_address, customer_tax_id,
    invoice_number, invoice_date, due_date,
    items,  # list of (description, quantity, unit_price)
    vat_rate=0.10,
    bank_name='', bank_account='', bank_holder='',
    output_path='invoice.pdf'
):
    pdf = InvoicePDF()
    pdf.add_page()

    # === HEADER ===
    pdf.set_font('VN', 'B', 16)
    pdf.set_text_color(27, 58, 101)
    pdf.cell(0, 10, company_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('VN', '', 10)
    pdf.set_text_color(102, 102, 102)
    pdf.cell(0, 5, company_address, new_x="LMARGIN", new_y="NEXT")
    if company_tax_id:
        pdf.cell(0, 5, f'MST: {company_tax_id}', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # === INVOICE TITLE ===
    pdf.set_font('VN', 'B', 22)
    pdf.set_text_color(27, 58, 101)
    pdf.cell(0, 12, 'H\u00d3A \u0110\u01a0N', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # === INVOICE INFO ===
    pdf.set_font('VN', '', 10)
    pdf.set_text_color(51, 51, 51)
    info_left = [
        f'Kh\u00e1ch h\u00e0ng: {customer_name}',
        f'\u0110\u1ecba ch\u1ec9: {customer_address}',
    ]
    if customer_tax_id:
        info_left.append(f'MST: {customer_tax_id}')
    info_right = [
        f'S\u1ed1 H\u0110: {invoice_number}',
        f'Ng\u00e0y: {invoice_date}',
        f'H\u1ea1n TT: {due_date}',
    ]
    for i in range(max(len(info_left), len(info_right))):
        left = info_left[i] if i < len(info_left) else ''
        right = info_right[i] if i < len(info_right) else ''
        pdf.cell(110, 6, left)
        pdf.cell(0, 6, right, align='R', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # === TABLE ===
    col_w = [12, 75, 18, 35, 40]
    headers = ['STT', 'M\u00f4 t\u1ea3', 'SL', '\u0110\u01a1n gi\u00e1', 'Th\u00e0nh ti\u1ec1n']

    pdf.set_font('VN', 'B', 9)
    pdf.set_fill_color(43, 87, 154)
    pdf.set_text_color(255, 255, 255)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 9, h, border=1, fill=True, align='C')
    pdf.ln()

    pdf.set_font('VN', '', 9)
    pdf.set_text_color(51, 51, 51)
    subtotal = 0
    for idx, (desc, qty, price) in enumerate(items, 1):
        amount = qty * price
        subtotal += amount
        bg = idx % 2 == 1
        if bg:
            pdf.set_fill_color(242, 247, 251)
        pdf.cell(col_w[0], 8, str(idx), border=1, fill=bg, align='C')
        pdf.cell(col_w[1], 8, desc, border=1, fill=bg)
        pdf.cell(col_w[2], 8, str(qty), border=1, fill=bg, align='C')
        pdf.cell(col_w[3], 8, f'{price:,.0f}', border=1, fill=bg, align='R')
        pdf.cell(col_w[4], 8, f'{amount:,.0f}', border=1, fill=bg, align='R')
        pdf.ln()

    # === TOTALS ===
    pdf.ln(3)
    vat_amount = subtotal * vat_rate
    total = subtotal + vat_amount

    pdf.set_font('VN', '', 10)
    x_label = 120
    x_value = 170
    for label, value in [
        ('T\u1ea1m t\u00ednh:', f'{subtotal:,.0f} \u0111'),
        (f'VAT ({int(vat_rate*100)}%):', f'{vat_amount:,.0f} \u0111'),
    ]:
        pdf.set_x(x_label)
        pdf.cell(50, 7, label, align='R')
        pdf.cell(0, 7, value, align='R', new_x="LMARGIN", new_y="NEXT")

    pdf.set_font('VN', 'B', 12)
    pdf.set_text_color(27, 58, 101)
    pdf.set_x(x_label)
    pdf.cell(50, 9, 'T\u1ed4NG C\u1ed8NG:', align='R')
    pdf.cell(0, 9, f'{total:,.0f} \u0111', align='R', new_x="LMARGIN", new_y="NEXT")

    # === PAYMENT INFO ===
    if bank_name:
        pdf.ln(8)
        pdf.set_font('VN', 'B', 10)
        pdf.set_text_color(27, 58, 101)
        pdf.cell(0, 7, 'Th\u00f4ng tin thanh to\u00e1n', new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('VN', '', 10)
        pdf.set_text_color(51, 51, 51)
        pdf.cell(0, 6, f'Ng\u00e2n h\u00e0ng: {bank_name}', new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f'S\u1ed1 TK: {bank_account}', new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f'Ch\u1ee7 TK: {bank_holder}', new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f'N\u1ed9i dung CK: {invoice_number}', new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_path)
    return output_path


# === CÁCH DÙNG ===
# create_invoice(
#     company_name='Công Ty ABC',
#     company_address='123 Nguyễn Huệ, Q1, TP.HCM',
#     company_tax_id='0123456789',
#     customer_name='Công Ty ABC',
#     customer_address='456 Lê Lợi, Q3, TP.HCM',
#     customer_tax_id='9876543210',
#     invoice_number='INV-2026-0001',
#     invoice_date='15/04/2026',
#     due_date='15/05/2026',
#     items=[
#         ('Dịch vụ tư vấn AI', 10, 5000000),
#         ('Phát triển chatbot', 1, 50000000),
#         ('Hosting 12 tháng', 12, 2000000),
#     ],
#     vat_rate=0.10,
#     bank_name='Vietcombank',
#     bank_account='0123456789',
#     bank_holder='CONG TY ABC',
#     output_path='invoice.pdf'
# )
```
