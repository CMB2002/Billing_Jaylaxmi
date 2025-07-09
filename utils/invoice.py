import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register DejaVu font (ensure DejaVuSans.ttf is in the project or fonts folder)
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

def generate_invoice(
    cart_items,                # list of tuples (name, qty, rate, subtotal)
    total_amount,              # float
    invoice_id,                # int or str
    customer_name=None,
    customer_phone=None,
    notes="",
    discount=0.0,
    discount_type="₹",
    payment_methods=None,      # dict (not used for billing estimate, but must be accepted)
    amount_paid=None,          # float (not used)
    amount_owed=None,          # float (not used)
    db=None,                   # for settings access
    shop_name="Jaylaxmi Electricals",
    gst_number="-",
    logo_path="logo.png"
):
    invoices_dir = os.path.join(os.getcwd(), "invoices")
    if not os.path.exists(invoices_dir):
        os.makedirs(invoices_dir)
    filename = os.path.join(invoices_dir, f"invoice_{invoice_id}.pdf")
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    y = height - 50

    # --- Fetch settings ---
    if db:
        try:
            from utils.helpers import get_setting
            shop_name = get_setting(db, "shop_name", shop_name)
            gst_number = get_setting(db, "gst", gst_number)  # <-- Corrected key!
            logo_path = get_setting(db, "logo_path", logo_path)
        except Exception:
            pass

    # --- Date & Logo at Top-Right ---
    logo_size = 110
    logo_y = height - 70
    if os.path.exists(logo_path):
        c.drawImage(logo_path, width - 160, logo_y - 60, width=logo_size, height=logo_size, preserveAspectRatio=True)
    c.setFont("DejaVu", 9)
    c.drawString(width - 160, logo_y - 50, f"Date: {datetime.now():%Y-%m-%d}")

    # --- Shop Name (centered, bold) ---
    c.setFont("DejaVu", 18)
    c.drawCentredString(width // 2, y, shop_name)
    y -= 26

    # --- "Billing Estimate" Small Under Shop Name ---
    c.setFont("DejaVu", 11)
    c.drawCentredString(width // 2, y, "Billing Estimate")
    y -= 18

    # --- GST No. under shop name (centered) ---
    c.setFont("DejaVu", 9)
    c.drawCentredString(width // 2, y, f"GST No.: {gst_number}")
    y -= 18

    # --- Customer details (left aligned) ---
    c.setFont("DejaVu", 10)
    if customer_name:
        c.drawString(50, y, f"Customer: {customer_name}")
        y -= 15
    if customer_phone:
        c.drawString(50, y, f"Phone: {customer_phone}")
        y -= 18

    # --- Table header ---
    c.setFont("DejaVu", 11)
    c.drawString(50, y, "S.No.")
    c.drawString(95, y, "Item")
    c.drawString(290, y, "Qty")
    c.drawString(340, y, "Rate")
    c.drawString(420, y, "Amount")
    y -= 15

    # --- Table rows ---
    c.setFont("DejaVu", 10)
    for idx, (name, qty, rate, amount) in enumerate(cart_items, 1):
        c.drawString(50, y, str(idx))
        c.drawString(95, y, name)
        c.drawString(290, y, str(qty))
        c.drawString(340, y, f"₹{rate}")
        c.drawString(420, y, f"₹{amount}")
        y -= 13

    # --- Discount & Total ---
    y -= 6
    c.setFont("DejaVu", 11)
    c.drawString(320, y, "Discount:")
    c.drawString(420, y, f"₹{discount}{discount_type if discount_type != '₹' else ''}")
    y -= 15
    c.drawString(320, y, "Total:")
    c.drawString(420, y, f"₹{total_amount}")
    y -= 18

    # --- Note ---
    if notes:
        c.setFont("DejaVu", 9)
        c.drawString(50, y, f"Note: {notes}")
        y -= 12

    # --- Disclaimer Footer ---
    c.setFont("DejaVu", 6)
    c.drawString(50, 30, "This is a Billing estimate not GST Invoice.")

    c.save()
    return filename
