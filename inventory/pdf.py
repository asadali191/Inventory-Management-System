from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def invoice_pdf(invoice):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"INVOICE {invoice.invoice_no}")
    y -= 25

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Customer: {invoice.customer_display()}")
    y -= 18
    c.drawString(50, y, f"Date: {invoice.date.strftime('%Y-%m-%d %H:%M')}")
    y -= 25

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "SKU")
    c.drawString(160, y, "Product")
    c.drawString(380, y, "Qty")
    c.drawString(420, y, "Price")
    c.drawString(490, y, "Total")
    y -= 15

    c.setFont("Helvetica", 10)
    for line in invoice.lines.select_related("product").all():
        c.drawString(50, y, line.product.sku)
        c.drawString(160, y, line.product.product_name[:28])
        c.drawString(380, y, str(line.qty))
        c.drawString(420, y, str(line.unit_price))
        c.drawString(490, y, str(line.line_total))
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 50

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(420, y, "Grand Total:")
    c.drawString(520, y, str(invoice.grand_total))

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

def return_pdf(ret):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"RETURN {ret.return_no}")
    y -= 25

    c.setFont("Helvetica", 11)
    if ret.invoice:
        c.drawString(50, y, f"Against Invoice: {ret.invoice.invoice_no}")
        y -= 18
    c.drawString(50, y, f"Date: {ret.date.strftime('%Y-%m-%d %H:%M')}")
    y -= 25

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "SKU")
    c.drawString(160, y, "Product")
    c.drawString(380, y, "Qty")
    c.drawString(420, y, "Price")
    c.drawString(490, y, "Total")
    y -= 15

    c.setFont("Helvetica", 10)
    for line in ret.lines.select_related("product").all():
        c.drawString(50, y, line.product.sku)
        c.drawString(160, y, line.product.product_name[:28])
        c.drawString(380, y, str(line.qty))
        c.drawString(420, y, str(line.unit_price))
        c.drawString(490, y, str(line.line_total))
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 50

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(420, y, "Total Refund:")
    c.drawString(520, y, str(ret.total_refund))

    c.showPage()
    c.save()
    buf.seek(0)
    return buf
