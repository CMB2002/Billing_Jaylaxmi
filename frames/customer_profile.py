import customtkinter as ctk
from tkinter import ttk

class CustomerProfileFrame(ctk.CTkToplevel):
    def __init__(self, parent, db, customer_id):
        super().__init__(parent)
        self.db = db
        self.customer_id = customer_id
        self.title("Customer Profile")
        self.geometry("680x540")
        self.resizable(False, False)

        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=22, pady=22)

        cur = self.db.cursor()
        cur.execute("SELECT name, phone FROM customers WHERE id=?", (self.customer_id,))
        cust = cur.fetchone()
        cust_name, cust_phone = cust if cust else ("-", "-")
        ctk.CTkLabel(main, text=f"👤 {cust_name}  ({cust_phone})", font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0,8))

        cur.execute("SELECT COALESCE(SUM(total), 0) FROM invoices WHERE customer_id=?", (self.customer_id,))
        total_spent = cur.fetchone()[0]

        # Dummy logic for "money owed" (update this logic as needed!)
        money_owed = 0

        stats = ctk.CTkFrame(main, fg_color="transparent")
        stats.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(stats, text=f"Total Spent: ₹{total_spent:.2f}", font=("Segoe UI", 13)).pack(side="left", padx=12)
        ctk.CTkLabel(stats, text=f"Money Owed: ₹{money_owed:.2f}", font=("Segoe UI", 13)).pack(side="left", padx=12)

        # Invoices table
        columns = ("id", "date", "total", "mode")
        tree = ttk.Treeview(main, columns=columns, show="headings", height=10)
        tree.heading("id", text="Invoice #")
        tree.heading("date", text="Date")
        tree.heading("total", text="Total")
        tree.heading("mode", text="Payment Mode")

        tree.column("id", width=80, anchor="center")
        tree.column("date", width=150, anchor="center")
        tree.column("total", width=110, anchor="center")
        tree.column("mode", width=120, anchor="center")

        tree.pack(fill="both", expand=True, pady=(8, 4))

        # Fetch invoices (add "mode" column if your DB supports it, else "Unknown")
        cur.execute("SELECT id, timestamp, total FROM invoices WHERE customer_id=? ORDER BY timestamp DESC", (self.customer_id,))
        for inv_id, ts, total in cur.fetchall():
            payment_mode = "Unknown"
            tree.insert("", "end", values=(inv_id, ts, f"₹{total:.2f}", payment_mode))
