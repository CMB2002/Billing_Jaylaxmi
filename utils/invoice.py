import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

def generate_invoice(
    cart_items, total_amount, invoice_id,
    customer_name=None, customer_phone=None,
    notes="", discount=0.0, discount_type="₹",
    payment_methods=None, amount_paid=0.0, amount_owed=0.0
):
    """
    Generates a PDF invoice and returns its filepath.
    All files are placed under the 'invoices/' directory.
    """
    # 1. Ensure the invoices directory exists
    invoices_dir = "invoices"
    os.makedirs(invoices_dir, exist_ok=True)

    # 2. Build the PDF filename inside that directory
    filename = os.path.join(invoices_dir, f"invoice_{invoice_id}.pdf")

    # 3. Create the PDF
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

    # Line items
    c.setFont("Helvetica", 11)
    for name, qty, price, total in cart_items:
        c.drawString(50, y, name)
        c.drawString(250, y, str(qty))
        c.drawString(300, y, f"₹{price:.2f}")
        c.drawString(400, y, f"₹{total:.2f}")
        y -= 20

    # Subtotal, Discount, Total
    y -= 12
    c.setFont("Helvetica", 11)
    subtotal = sum(row[3] for row in cart_items)
    c.drawString(300, y, "Subtotal:")
    c.drawString(400, y, f"₹{subtotal:.2f}")
    y -= 18
    if discount and discount > 0:
        c.drawString(300, y, f"Discount ({discount_type}):")
        c.drawString(400, y, f"-₹{discount:.2f}")
        y -= 18
    c.setFont("Helvetica-Bold", 12)
    c.drawString(300, y, "Grand Total:")
    c.drawString(400, y, f"₹{total_amount:.2f}")
    y -= 20

    # Payment method breakdown
    if payment_methods:
        c.setFont("Helvetica", 10)
        c.drawString(50, y, "Paid via:")
        pm_str = " / ".join(f"{k.capitalize()}: ₹{v:.2f}" for k, v in payment_methods.items() if v)
        c.drawString(120, y, pm_str)
        y -= 18

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Paid: ₹{amount_paid:.2f}")
    y -= 14
    c.drawString(50, y, f"Owed: ₹{amount_owed:.2f}")
    y -= 16

    # Notes
    if notes:
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(50, y, f"Notes: {notes}")
        y -= 16

    # 4. Save and return
    c.save()
    return filename
