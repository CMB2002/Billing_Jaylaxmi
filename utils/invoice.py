import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from datetime import datetime
from textwrap import wrap

def generate_invoice(
    cart_items,
    total_amount,
    invoice_id,
    customer_name=None,
    customer_phone=None,
    notes=None
):
    """
    Generates a PDF invoice and returns its filepath.
    All files are placed under the 'invoices/' directory.
    Optionally prints customer_name, customer_phone, and notes on invoice.
    Auto-paginates if items overflow.
    """
    invoices_dir = "invoices"
    os.makedirs(invoices_dir, exist_ok=True)

    filename = os.path.join(invoices_dir, f"invoice_{invoice_id}.pdf")

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    y = height - 50

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Jaylaxmi Shop - Tax Invoice")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Date: {datetime.now():%Y-%m-%d %H:%M:%S}")
    if customer_name or customer_phone:
        y -= 14
        c.drawString(50, y, f"Customer: {customer_name or '-'}  Phone: {customer_phone or '-'}")
    y -= 18

    # Table header
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Product")
    c.drawString(250, y, "Qty")
    c.drawString(300, y, "Price")
    c.drawString(400, y, "Total")
    y -= 20

    # Line items with page support
    c.setFont("Helvetica", 11)
    for i, (name, qty, price, total) in enumerate(cart_items):
        if y < 90:  # new page
            c.showPage()
            y = height - 50
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Product")
            c.drawString(250, y, "Qty")
            c.drawString(300, y, "Price")
            c.drawString(400, y, "Total")
            y -= 20
            c.setFont("Helvetica", 11)
        c.drawString(50, y, str(name))
        c.drawString(250, y, str(qty))
        c.drawString(300, y, f"₹{price:.2f}")
        c.drawString(400, y, f"₹{total:.2f}")
        y -= 20

    # Grand total
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(300, y, "Total:")
    c.drawString(400, y, f"₹{total_amount:.2f}")
    y -= 30

    # Notes/comments (if any)
    if notes:
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(50, y, "Notes:")
        y -= 15
        for line in wrap(notes, width=85):
            c.drawString(65, y, line)
            y -= 14

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    y -= 20
    c.drawString(50, y, "Thank you for your purchase! - Jaylaxmi Shop")

    c.save()
    return filename
