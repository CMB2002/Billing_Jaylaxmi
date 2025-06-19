import customtkinter as ctk
from tkinter import ttk, messagebox
import json
import os

class CustomerProfileFrame(ctk.CTkToplevel):
    def __init__(self, parent, db, customer_id):
        super().__init__(parent)
        self.db = db
        self.customer_id = customer_id
        self.title("Customer Profile")
        self.geometry("670x560")
        self.minsize(500, 420)
        self.transient(parent)
        self.attributes('-topmost', True)
        self.lift()
        self.focus_force()
        self._build_ui()
        self._populate_data()

    def _build_ui(self):
        self.main = ctk.CTkFrame(self)
        self.main.pack(expand=True, fill="both", padx=16, pady=16)

        self.name_label = ctk.CTkLabel(self.main, text="", font=("Segoe UI", 18, "bold"))
        self.name_label.pack(anchor="w", pady=(0,6))
        self.phone_label = ctk.CTkLabel(self.main, text="", font=("Segoe UI", 13))
        self.phone_label.pack(anchor="w")

        statsf = ctk.CTkFrame(self.main)
        statsf.pack(fill="x", pady=(8, 10))
        self.invoice_count_label = ctk.CTkLabel(statsf, text="", font=("Segoe UI", 13))
        self.invoice_count_label.pack(side="left", padx=(0,18))
        self.spent_label = ctk.CTkLabel(statsf, text="", font=("Segoe UI", 13))
        self.spent_label.pack(side="left", padx=(0,18))
        self.owed_label = ctk.CTkLabel(statsf, text="", font=("Segoe UI", 13), text_color="#e56")
        self.owed_label.pack(side="left", padx=(0,18))

        # Table for Invoices
        tablef = ctk.CTkFrame(self.main)
        tablef.pack(fill="both", expand=True, pady=(4,0))
        columns = ("id", "date", "total", "paid", "owed", "payments", "pdf")
        self.tree = ttk.Treeview(tablef, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="Invoice #")
        self.tree.heading("date", text="Date")
        self.tree.heading("total", text="Total")
        self.tree.heading("paid", text="Paid")
        self.tree.heading("owed", text="Owed")
        self.tree.heading("payments", text="Payments")
        self.tree.heading("pdf", text="PDF")
        for col in columns:
            self.tree.column(col, width=80, anchor="center")
        self.tree.column("payments", width=160)
        self.tree.column("pdf", width=60)
        self.tree.pack(fill="both", expand=True, padx=3, pady=3)
        vsb = ttk.Scrollbar(tablef, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Button-1>", self._on_tree_click)

    def _populate_data(self):
        # Customer info
        cur = self.db.cursor()
        cur.execute("SELECT name, phone FROM customers WHERE id=?", (self.customer_id,))
        row = cur.fetchone()
        if not row:
            self.name_label.configure(text="Unknown Customer")
            return
        self.name_label.configure(text=row[0])
        self.phone_label.configure(text=f"Phone: {row[1] or '-'}")

        # Invoices and stats
        cur.execute(
            """
            SELECT id, total, paid, owed, pdf_path, timestamp, payment_methods
            FROM (
                SELECT 
                    id, total,
                    COALESCE(amount_paid, total) as paid,
                    COALESCE(amount_owed, 0) as owed,
                    pdf_path, timestamp,
                    payment_methods
                FROM invoices WHERE customer_id=?
            )
            ORDER BY timestamp DESC
            """,
            (self.customer_id,)
        )
        invoices = cur.fetchall()
        invoice_count = len(invoices)
        total_spent = sum(inv[2] for inv in invoices)
        total_owed = sum(inv[3] for inv in invoices)
        self.invoice_count_label.configure(text=f"Invoices: {invoice_count}")
        self.spent_label.configure(text=f"Spent: ₹{total_spent:.2f}")
        self.owed_label.configure(text=f"Owed: ₹{total_owed:.2f}")

        for i in self.tree.get_children():
            self.tree.delete(i)
        for iid, total, paid, owed, pdf_path, ts, pm_json in invoices:
            payments = ""
            if pm_json:
                try:
                    pm = json.loads(pm_json)
                    payments = " / ".join(f"{k.capitalize()}: ₹{v:.2f}" for k,v in pm.items() if v)
                except Exception:
                    payments = pm_json
            self.tree.insert(
                "", "end", iid=str(iid),
                values=(iid, ts.split(" ")[0], f"₹{total:.2f}", f"₹{paid:.2f}", f"₹{owed:.2f}", payments, "Open")
            )

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        rowid = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not rowid:
            return
        col_idx = int(col[1:]) - 1
        colname = self.tree["columns"][col_idx]
        if colname == "pdf":
            cur = self.db.cursor()
            cur.execute("SELECT pdf_path FROM invoices WHERE id=?", (int(rowid),))
            row = cur.fetchone()
            if row and row[0]:
                try:
                    os.startfile(row[0])
                except Exception as e:
                    messagebox.showerror("Open PDF", f"Cannot open PDF: {e}", parent=self)
