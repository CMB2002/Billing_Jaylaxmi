import os
import csv
import json
import customtkinter as ctk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
from datetime import datetime
from ui_windows import ConfirmDialog
from utils.helpers import refresh_all

REPORTS_DIR = "reports"

class HoverTreeview(ttk.Treeview):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._last_hover = None
        self.bind('<Motion>', self._on_motion)
        self.tag_configure('hover', background='#2d3340')

    def _on_motion(self, event):
        row_id = self.identify_row(event.y)
        if self._last_hover != row_id:
            if self._last_hover:
                current_tags = list(self.item(self._last_hover, "tags"))
                if "hover" in current_tags:
                    current_tags.remove("hover")
                self.item(self._last_hover, tags=tuple(current_tags))
            if row_id:
                current_tags = list(self.item(row_id, "tags"))
                if "hover" not in current_tags:
                    current_tags.append("hover")
                self.item(row_id, tags=tuple(current_tags))
            self._last_hover = row_id

class ReportFrame(ctk.CTkFrame):
    def __init__(self, master, db, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app
        self.set_status = set_status or (lambda msg: None)

        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_filters()
        self._build_stats()
        self._build_summary()
        self._build_table()
        self.refresh_report()

    def _build_header(self):
        ctk.CTkLabel(
            self,
            text="📊 Sales & Estimate Reports",
            font=("Segoe UI", 20, "bold"),
            text_color="#7dd3fc"
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 0))

    def _build_filters(self):
        today = datetime.now().date()
        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.grid(row=1, column=0, sticky="ew", padx=10, pady=(14, 6))
        for i in range(7):
            frm.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(frm, text="From:", font=("Segoe UI", 13)).grid(row=0, column=0, sticky="w")
        self.from_date = DateEntry(frm, date_pattern="yyyy-mm-dd", font=("Segoe UI", 13), width=12, maxdate=today)
        self.from_date.set_date(today)
        self.from_date.grid(row=0, column=1, sticky="ew", padx=5)

        ctk.CTkLabel(frm, text="To:", font=("Segoe UI", 13)).grid(row=0, column=2, sticky="w")
        self.to_date = DateEntry(frm, date_pattern="yyyy-mm-dd", font=("Segoe UI", 13), width=12, maxdate=today)
        self.to_date.set_date(today)
        self.to_date.grid(row=0, column=3, sticky="ew", padx=5)

        ctk.CTkButton(frm, text="🔎 Filter", font=("Segoe UI", 13, "bold"), fg_color="#324076",
                      hover_color="#7dd3fc", corner_radius=8, command=self.refresh_report)\
            .grid(row=0, column=4, sticky="e", padx=5)
        ctk.CTkButton(frm, text="📤 Export CSV", font=("Segoe UI", 13), fg_color="#1a8cff",
                      hover_color="#0e68b1", corner_radius=8, command=self.export_csv)\
            .grid(row=0, column=5, sticky="e", padx=5)
        ctk.CTkButton(frm, text="📁 Open Folder", font=("Segoe UI", 13), fg_color="#23272f",
                      hover_color="#324076", corner_radius=8, command=self.open_reports_folder)\
            .grid(row=0, column=6, sticky="e", padx=5)

    def _build_stats(self):
        self.top_cust_label = ctk.CTkLabel(
            self, text="👥 Top Customers: —",
            font=("Segoe UI", 13, "bold"),
            text_color="#cccccc"
        )
        self.top_cust_label.grid(row=2, column=0, sticky="w", padx=24, pady=(3, 1))
        self.top_prod_label = ctk.CTkLabel(
            self, text="🏆 Top Products: —",
            font=("Segoe UI", 13, "bold"),
            text_color="#cccccc"
        )
        self.top_prod_label.grid(row=2, column=0, sticky="w", padx=(550, 0), pady=(3, 1))

    def _build_summary(self):
        self.money_collected_label = ctk.CTkLabel(
            self, text="💰 Collected: ₹0.00",
            font=("Segoe UI", 14, "bold"),
            text_color="#8be9fd"
        )
        self.money_collected_label.grid(row=3, column=0, sticky="w", padx=24, pady=(1, 8))
        self.money_owed_label = ctk.CTkLabel(
            self, text="⏳ Owed: ₹0.00",
            font=("Segoe UI", 14, "bold"),
            text_color="#e56"
        )
        self.money_owed_label.grid(row=3, column=0, sticky="w", padx=(250, 0), pady=(1, 8))
        self.cash_label = ctk.CTkLabel(self, text="Cash: ₹0.00", font=("Segoe UI", 13), text_color="#cccccc")
        self.cash_label.grid(row=3, column=0, sticky="w", padx=(430, 0), pady=(1, 8))
        self.upi_label = ctk.CTkLabel(self, text="UPI: ₹0.00", font=("Segoe UI", 13), text_color="#cccccc")
        self.upi_label.grid(row=3, column=0, sticky="w", padx=(600, 0), pady=(1, 8))
        self.card_label = ctk.CTkLabel(self, text="Card: ₹0.00", font=("Segoe UI", 13), text_color="#cccccc")
        self.card_label.grid(row=3, column=0, sticky="w", padx=(720, 0), pady=(1, 8))

    def _build_table(self):
        frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0,14))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        columns = ("id", "total", "timestamp", "customer", "actions")
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#20232a",
                        fieldbackground="#1b1d22",
                        foreground="#ededed",
                        rowheight=33,
                        font=("Segoe UI", 13),
                        bordercolor="#1a1e25",
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background="#23272f",
                        foreground="#7dd3fc",
                        font=("Segoe UI", 15, "bold"))
        style.map("Treeview", background=[('selected', '#324076')])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.tree = HoverTreeview(frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="Invoice #")
        self.tree.heading("total", text="Total")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("customer", text="Customer")
        self.tree.heading("actions", text="Actions")

        self.tree.column("id", width=80, anchor="center")
        self.tree.column("total", width=100, anchor="center")
        self.tree.column("timestamp", width=175, anchor="center")
        self.tree.column("customer", width=210, anchor="w")
        self.tree.column("actions", width=140, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Button-1>", self._on_tree_click)

    def refresh_report(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        d0 = self.from_date.get_date()
        d1 = self.to_date.get_date()
        today = datetime.now().date()
        if d1 > today:
            d1 = today
            self.to_date.set_date(today)
        if d0 > d1:
            messagebox.showwarning("Date Error", "From date cannot be after To date.")
            return

        start = datetime(d0.year, d0.month, d0.day, 0,0,0)
        end = datetime(d1.year, d1.month, d1.day, 23,59,59)
        cur = self.db.cursor()
        cur.execute("""
            SELECT invoices.id, total, timestamp, customers.name, customers.phone, pdf_path, items, 
                   COALESCE(amount_paid, total) as paid,
                   COALESCE(amount_owed, 0) as owed,
                   COALESCE(payment_methods, '') as payment_methods
            FROM invoices
            LEFT JOIN customers ON invoices.customer_id = customers.id
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, (start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S')))

        rows = cur.fetchall()
        total_sum = 0
        total_paid = 0
        total_owed = 0
        pm_breakdown = {"cash": 0.0, "upi": 0.0, "card": 0.0}
        product_sales = {}

        for inv_id, total, ts, custname, custphone, pdf_path, items_json, paid, owed, pm_json in rows:
            cust_display = f"{custname or '-'} ({custphone or '-'})"
            total_sum += total
            total_paid += paid or 0
            total_owed += owed or 0
            if pm_json:
                try:
                    pm = json.loads(pm_json)
                    for key in pm_breakdown:
                        pm_breakdown[key] += float(pm.get(key, 0))
                except Exception:
                    pass
            self.tree.insert(
                "", "end", iid=str(inv_id),
                values=(inv_id, f"₹{total:.2f}", ts, cust_display, "View | Delete")
            )
            try:
                items = json.loads(items_json)
                for name, qty, price, subtotal in items:
                    product_sales[name] = product_sales.get(name, 0) + subtotal
            except Exception:
                pass

        self.money_collected_label.configure(text=f"💰 Collected: ₹{total_paid:.2f}")
        self.money_owed_label.configure(text=f"⏳ Owed: ₹{total_owed:.2f}")
        self.cash_label.configure(text=f"Cash: ₹{pm_breakdown['cash']:.2f}")
        self.upi_label.configure(text=f"UPI: ₹{pm_breakdown['upi']:.2f}")
        self.card_label.configure(text=f"Card: ₹{pm_breakdown['card']:.2f}")

        self.set_status(f"Loaded {len(rows)} invoices. Total Sales: ₹{total_sum:.2f}")

        self._update_top_customers()
        self._update_top_products(product_sales)

    def _update_top_customers(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT customers.name, COUNT(invoices.id) as inv_count, COALESCE(SUM(invoices.total), 0) as total_spent
            FROM customers
            LEFT JOIN invoices ON customers.id = invoices.customer_id
            GROUP BY customers.id
            ORDER BY total_spent DESC
            LIMIT 3
        """)
        rows = cur.fetchall()
        text = ", ".join([f"{name} (₹{total_spent:.2f})" for name, _, total_spent in rows]) or "—"
        self.top_cust_label.configure(text=f"👥 Top Customers: {text}")

    def _update_top_products(self, product_sales):
        if not product_sales:
            self.top_prod_label.configure(text="🏆 Top Products: —")
            return
        sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:3]
        text = ", ".join([f"{name} (₹{total:.2f})" for name, total in sorted_products])
        self.top_prod_label.configure(text=f"🏆 Top Products: {text}")

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        rowid = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not rowid:
            return
        col_idx = int(col[1:]) - 1
        if col_idx != 4:
            return

        inv_id = int(rowid)
        x_offset = event.x - self.tree.bbox(rowid, col)[0]

        cell_width = self.tree.column("actions", option="width")
        if x_offset < cell_width / 2:
            self._view_pdf(inv_id)
        else:
            self._confirm_delete(inv_id)

    def _view_pdf(self, inv_id):
        cur = self.db.cursor()
        cur.execute("SELECT pdf_path FROM invoices WHERE id=?", (inv_id,))
        row = cur.fetchone()
        if row and row[0]:
            path = row[0]
            try:
                os.startfile(path)
            except Exception as e:
                self.set_status("Cannot open PDF.")
                messagebox.showerror("Error", f"Cannot open {path!r}")
        else:
            messagebox.showinfo("Info", "PDF not found.")

    def _confirm_delete(self, inv_id):
        def confirm():
            self.db.cursor().execute("DELETE FROM invoices WHERE id=?", (inv_id,))
            self.db.commit()
            self.set_status(f"Invoice #{inv_id} deleted.")
            self.refresh_report()
            if self.app:
                refresh_all(self.app)
        ConfirmDialog(
            self,
            "Delete Invoice",
            f"Delete invoice #{inv_id}?",
            confirm
        )

    def export_csv(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        d0 = self.from_date.get_date()
        d1 = self.to_date.get_date()
        today = datetime.now().date()
        if d1 > today:
            d1 = today
            self.to_date.set_date(today)
        if d0 > d1:
            messagebox.showwarning("Date Error", "From date cannot be after To date.")
            return
        start = datetime(d0.year, d0.month, d0.day, 0,0,0)
        end = datetime(d1.year, d1.month, d1.day, 23,59,59)
        cur = self.db.cursor()
        cur.execute("""
            SELECT invoices.id, total, pdf_path, timestamp, customers.name, customers.phone,
                   COALESCE(amount_paid, total) as paid,
                   COALESCE(amount_owed, 0) as owed,
                   COALESCE(payment_methods, '') as payment_methods
              FROM invoices
              LEFT JOIN customers ON invoices.customer_id = customers.id
             WHERE timestamp BETWEEN ? AND ?
             ORDER BY timestamp DESC
        """, (
            start.strftime('%Y-%m-%d %H:%M:%S'),
            end.strftime('%Y-%m-%d %H:%M:%S')
        ))
        rows = cur.fetchall()
        filename = os.path.join(REPORTS_DIR, f"invoices_report_{datetime.now():%Y%m%d_%H%M%S}.csv")
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Invoice #", "Total", "PDF", "Timestamp", "Customer Name", "Customer Phone",
                "Paid", "Owed", "Payment Methods"
            ])
            for row in rows:
                writer.writerow(row)
        self.set_status(f"Exported {len(rows)} invoices to {filename}")
        messagebox.showinfo("Exported", f"Saved to {filename}")

    def open_reports_folder(self):
        try:
            folder = os.path.abspath(REPORTS_DIR)
            if os.name == 'nt':
                os.startfile(folder)
            elif os.name == 'posix':
                import subprocess
                subprocess.Popen(['xdg-open', folder])
            else:
                messagebox.showinfo("Open Folder", f"Please open manually: {folder}")
        except Exception as e:
            messagebox.showwarning("Open Folder", f"Failed to open folder:\n{e}")
