import os
import json
import customtkinter as ctk
from datetime import datetime
from utils.invoice import generate_invoice
from tkinter import messagebox

INVOICES_DIR = "invoices"

class PreviewWindow(ctk.CTkToplevel):
    def __init__(
        self, parent, cart, total, db,
        on_alter=None, on_finish=None,
        customer_id=None, customer_name="", customer_phone="",
        discount=0.0, discount_type="₹", payment_methods=None,
        amount_paid=0.0, amount_owed=0.0
    ):
        super().__init__(parent)
        self.attributes('-topmost', True)
        self.lift()
        self.cart = cart
        self.total = total
        self.db = db
        self.on_alter = on_alter
        self.on_finish = on_finish
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.discount = discount
        self.discount_type = discount_type
        self.payment_methods = payment_methods or {}
        self.amount_paid = amount_paid
        self.amount_owed = amount_owed
        self.invoice_note = ctk.StringVar()
        self.title("Preview Invoice")
        self.geometry("740x600")
        self.minsize(520, 420)
        self._draw_ui()

    def _draw_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="#181c24", corner_radius=18)
        scroll.pack(side="top", fill="both", expand=True, padx=22, pady=(22,0))
        
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        self.invoice_no = int(now.timestamp())
        shop = "Jaylaxmi Shop"

        # Top info
        infof = ctk.CTkFrame(scroll, fg_color="transparent")
        infof.pack(fill="x", pady=(6,0))
        ctk.CTkLabel(infof, text=f"🧾 {shop}", font=("Segoe UI", 18, "bold"), anchor="w").pack(side="left", padx=(5, 25))
        ctk.CTkLabel(infof, text=f"Date: {date_str}   Time: {time_str}", font=("Segoe UI", 13), anchor="w").pack(side="left")
        ctk.CTkLabel(infof, text=f"  Invoice #: {self.invoice_no}", font=("Segoe UI", 13, "bold"), anchor="e").pack(side="right", padx=12)

        # Customer info
        custf = ctk.CTkFrame(scroll, fg_color="transparent")
        custf.pack(fill="x", pady=(2, 2), padx=4)
        ctk.CTkLabel(custf, text=f"Customer: {self.customer_name or '-'}", font=("Segoe UI", 13)).pack(side="left", padx=5)
        ctk.CTkLabel(custf, text=f"Phone: {self.customer_phone or '-'}", font=("Segoe UI", 13)).pack(side="left", padx=15)

        # Cart preview
        cartf = ctk.CTkFrame(scroll, fg_color="#202430", corner_radius=16)
        cartf.pack(fill="both", expand=True, padx=8, pady=(16, 5))
        ctk.CTkLabel(cartf, text="Item", font=("Segoe UI", 13, "bold"), width=180, anchor="w").grid(row=0, column=0, sticky="w", padx=(8,4), pady=2)
        ctk.CTkLabel(cartf, text="Qty", font=("Segoe UI", 13, "bold"), width=40).grid(row=0, column=1)
        ctk.CTkLabel(cartf, text="Price", font=("Segoe UI", 13, "bold"), width=80).grid(row=0, column=2)
        ctk.CTkLabel(cartf, text="Total", font=("Segoe UI", 13, "bold"), width=100).grid(row=0, column=3)
        for i, (name, qty, price, subtotal) in enumerate(self.cart, start=1):
            ctk.CTkLabel(cartf, text=name, font=("Segoe UI", 12), width=180, anchor="w").grid(row=i, column=0, sticky="w", padx=(8,4), pady=1)
            ctk.CTkLabel(cartf, text=str(qty), font=("Segoe UI", 12), width=40).grid(row=i, column=1)
            ctk.CTkLabel(cartf, text=f"₹{price:.2f}", font=("Segoe UI", 12), width=80).grid(row=i, column=2)
            ctk.CTkLabel(cartf, text=f"₹{subtotal:.2f}", font=("Segoe UI", 12), width=100).grid(row=i, column=3)

        # --- Summary ---
        summary = ctk.CTkFrame(scroll, fg_color="transparent")
        summary.pack(fill="x", padx=8, pady=(0,6))
        subtotal = sum(item[3] for item in self.cart)
        ctk.CTkLabel(summary, text=f"Subtotal: ₹{subtotal:.2f}", font=("Segoe UI", 13)).pack(side="left", padx=(2,10))
        ctk.CTkLabel(summary, text=f"Discount: {'-' if self.discount_type == '₹' else ''}{self.discount}{self.discount_type}", font=("Segoe UI", 13)).pack(side="left", padx=(10,10))
        ctk.CTkLabel(summary, text=f"Grand Total: ₹{self.total:.2f}", font=("Segoe UI", 16, "bold"), text_color="#4de563").pack(side="right", padx=10)

        # --- Payment breakdown ---
        paymentf = ctk.CTkFrame(scroll, fg_color="transparent")
        paymentf.pack(fill="x", padx=8, pady=(0,6))
        paystr = " / ".join(f"{k.capitalize()}: ₹{v:.2f}" for k,v in self.payment_methods.items() if v)
        ctk.CTkLabel(paymentf, text=f"Paid via: {paystr}", font=("Segoe UI", 13)).pack(side="left", padx=(2,10))
        ctk.CTkLabel(paymentf, text=f"Paid: ₹{self.amount_paid:.2f}", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(10,5))
        ctk.CTkLabel(paymentf, text=f"Owed: ₹{self.amount_owed:.2f}", font=("Segoe UI", 13, "bold"), text_color="#e56").pack(side="left", padx=10)

        # --- Notes section
        notesf = ctk.CTkFrame(scroll, fg_color="transparent")
        notesf.pack(fill="x", padx=8, pady=(0,8))
        ctk.CTkLabel(notesf, text="Add Notes (optional):", font=("Segoe UI", 13)).pack(side="left", padx=(2,6))
        ctk.CTkEntry(notesf, textvariable=self.invoice_note, width=400, placeholder_text="Type any note for this bill...").pack(side="left")

        # --- Bottom Buttons (always visible) ---
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=22, pady=10)
        ctk.CTkButton(btns, text="🖨️ Print", width=110, height=36, font=("Segoe UI", 13, "bold"),
                      command=self._on_print).pack(side="left", padx=14)
        ctk.CTkButton(btns, text="💾 Save", width=110, height=36, font=("Segoe UI", 13, "bold"),
                      command=self._on_save).pack(side="left", padx=14)
        ctk.CTkButton(btns, text="Open Invoice Folder", width=140, height=36,
                      font=("Segoe UI", 13), command=self._open_invoice_folder).pack(side="left", padx=14)
        ctk.CTkButton(btns, text="✏️ Alter", width=110, height=36, font=("Segoe UI", 13, "bold"),
                      command=self._on_alter).pack(side="right", padx=14)

    def _store_invoice(self, open_pdf=False, show_message=None):
        try:
            os.makedirs(INVOICES_DIR, exist_ok=True)
            items_json = json.dumps(self.cart)
            pm_json = json.dumps(self.payment_methods)
            pdf_path = generate_invoice(
                self.cart, self.total, self.invoice_no,
                customer_name=self.customer_name,
                customer_phone=self.customer_phone,
                notes=self.invoice_note.get(),
                discount=self.discount,
                discount_type=self.discount_type,
                payment_methods=self.payment_methods,
                amount_paid=self.amount_paid,
                amount_owed=self.amount_owed
            )
            cur = self.db.cursor()
            cur.execute(
                """
                INSERT INTO invoices (
                    customer_id, total, items, pdf_path, notes, timestamp,
                    discount, discount_type, payment_methods, amount_paid, amount_owed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.customer_id, self.total, items_json, pdf_path, self.invoice_note.get(),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    self.discount, self.discount_type, pm_json, self.amount_paid, self.amount_owed
                )
            )
            self.db.commit()
            if open_pdf:
                try:
                    os.startfile(pdf_path)
                except Exception as e:
                    messagebox.showwarning("Preview", f"Saved PDF, but could not open it.\n{e}", parent=self)
            if show_message == "Done":
                messagebox.showinfo("Done", "Invoice printed and saved.", parent=self)
            elif show_message == "Saved":
                messagebox.showinfo("Saved", "Invoice saved to reports.", parent=self)

            if self.on_finish:
                self.on_finish()
            self.destroy()
            return pdf_path
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save/print invoice:\n{e}")

    def _on_print(self):
        self._store_invoice(open_pdf=True, show_message="Done")

    def _on_save(self):
        self._store_invoice(open_pdf=False, show_message="Saved")

    def _on_alter(self):
        self.destroy()
        if self.on_alter:
            self.on_alter()

    def _open_invoice_folder(self):
        folder = os.path.abspath(INVOICES_DIR)
        try:
            if os.name == 'nt':
                os.startfile(folder)
            elif os.name == 'posix':
                import subprocess
                subprocess.Popen(['xdg-open', folder])
            else:
                messagebox.showinfo("Open Folder", f"Please open manually: {folder}")
        except Exception as e:
            messagebox.showwarning("Open Folder", f"Failed to open folder:\n{e}")
