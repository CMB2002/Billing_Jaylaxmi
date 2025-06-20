import customtkinter as ctk
from tkinter import ttk
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend for fast Figure rendering
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, db, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app
        self.set_status = set_status or (lambda msg: None)

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self._build_summary()
        self._build_graphs()

    def _build_header(self):
        ctk.CTkLabel(
            self,
            text="📊 Dashboard",
            font=("Segoe UI", 20, "bold"),
            text_color="#7dd3fc"
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 2))

    def _build_summary(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(2, 2))
        # Fetch summary stats
        cur = self.db.cursor()
        cur.execute("SELECT COUNT(*) FROM invoices")
        total_bills = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(total),0) FROM invoices")
        total_sales = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT customer_id) FROM invoices")
        total_customers = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(amount_owed),0) FROM invoices")
        total_owed = cur.fetchone()[0]

        ctk.CTkLabel(frame, text=f"🧾 Bills: {total_bills}", font=("Segoe UI", 15, "bold"), text_color="#7dd3fc")\
            .pack(side="left", padx=(0, 36))
        ctk.CTkLabel(frame, text=f"💰 Sales: ₹{total_sales:.2f}", font=("Segoe UI", 15, "bold"), text_color="#8be9fd")\
            .pack(side="left", padx=(0, 36))
        ctk.CTkLabel(frame, text=f"👥 Customers: {total_customers}", font=("Segoe UI", 15, "bold"), text_color="#bbf7d0")\
            .pack(side="left", padx=(0, 36))
        ctk.CTkLabel(frame, text=f"⏳ Owed: ₹{total_owed:.2f}", font=("Segoe UI", 15, "bold"), text_color="#e56")\
            .pack(side="left", padx=(0, 24))

    def _build_graphs(self):
        self.graphs_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.graphs_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(4, 10))
        self.graphs_frame.grid_rowconfigure(0, weight=1)
        self.graphs_frame.grid_columnconfigure(0, weight=1)
        self.graphs_frame.grid_columnconfigure(1, weight=1)

        self._draw_all_charts()

    def _draw_all_charts(self):
        for child in self.graphs_frame.winfo_children():
            child.destroy()

        # --- SALES/REVENUE OVER TIME ---
        fig1 = plt.Figure(figsize=(4, 2.2), dpi=100, facecolor='#23272f')
        ax1 = fig1.add_subplot(111)
        dates, sales, revenues = self._get_sales_data()
        x = np.arange(len(dates))
        ax1.bar(x, revenues, color="#7dd3fc", label="Revenue")
        ax1.set_xticks(x)
        ax1.set_xticklabels([d.strftime('%d-%b') for d in dates], rotation=45, fontsize=9, color="#ededed")
        ax1.set_facecolor("#23272f")
        fig1.subplots_adjust(left=0.15, bottom=0.25, right=0.97, top=0.85)
        ax1.set_title("Daily Revenue (last 14 days)", fontsize=12, color="#ededed")
        ax1.tick_params(axis='y', colors='#ededed')
        ax1.yaxis.label.set_color('#ededed')
        ax1.xaxis.label.set_color('#ededed')
        ax1.spines['bottom'].set_color('#ededed')
        ax1.spines['top'].set_color('#ededed')
        ax1.spines['right'].set_color('#ededed')
        ax1.spines['left'].set_color('#ededed')

        canvas1 = FigureCanvasTkAgg(fig1, master=self.graphs_frame)
        canvas1.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=12, pady=8)

        # --- TOP PRODUCTS PIE CHART ---
        fig2 = plt.Figure(figsize=(4, 2.2), dpi=100, facecolor='#23272f')
        ax2 = fig2.add_subplot(111)
        product_names, product_amounts = self._get_top_products()
        colors = ["#7dd3fc", "#bbf7d0", "#fbbf24", "#fda4af", "#a5b4fc"]
        if product_amounts:
            wedges, texts, autotexts = ax2.pie(product_amounts, labels=product_names, autopct='%1.1f%%',
                                               startangle=140, colors=colors[:len(product_amounts)],
                                               textprops={'color': '#23272f', 'fontsize': 10})
            ax2.set_title("Top Products (₹ Sales)", color="#ededed", fontsize=12)
        fig2.patch.set_facecolor('#23272f')
        canvas2 = FigureCanvasTkAgg(fig2, master=self.graphs_frame)
        canvas2.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=12, pady=8)

        # --- CUSTOMER GROWTH LINE CHART ---
        fig3 = plt.Figure(figsize=(4, 2.2), dpi=100, facecolor='#23272f')
        ax3 = fig3.add_subplot(111)
        join_dates, join_counts = self._get_customer_growth()
        x = np.arange(len(join_dates))
        ax3.plot(x, join_counts, color="#bbf7d0", marker="o", linewidth=2)
        ax3.set_xticks(x)
        ax3.set_xticklabels([d.strftime('%d-%b') for d in join_dates], rotation=45, fontsize=9, color="#ededed")
        ax3.set_facecolor("#23272f")
        fig3.subplots_adjust(left=0.15, bottom=0.25, right=0.97, top=0.85)
        ax3.set_title("Customer Trends (last 14 days)", fontsize=12, color="#ededed")
        ax3.tick_params(axis='y', colors='#ededed')
        ax3.spines['bottom'].set_color('#ededed')
        ax3.spines['top'].set_color('#ededed')
        ax3.spines['right'].set_color('#ededed')
        ax3.spines['left'].set_color('#ededed')

        canvas3 = FigureCanvasTkAgg(fig3, master=self.graphs_frame)
        canvas3.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=12, pady=8)

        # --- EXPENSES PIE/LINE CHART ---
        fig4 = plt.Figure(figsize=(4, 2.2), dpi=100, facecolor='#23272f')
        ax4 = fig4.add_subplot(111)
        expense_dates, expense_values = self._get_expense_data()
        if expense_values:
            x = np.arange(len(expense_dates))
            ax4.plot(x, expense_values, color="#fda4af", marker="s", linewidth=2)
            ax4.set_xticks(x)
            ax4.set_xticklabels([d.strftime('%d-%b') for d in expense_dates], rotation=45, fontsize=9, color="#ededed")
        ax4.set_facecolor("#23272f")
        fig4.subplots_adjust(left=0.15, bottom=0.25, right=0.97, top=0.85)
        ax4.set_title("Expenses (last 14 days)", fontsize=12, color="#ededed")
        ax4.tick_params(axis='y', colors='#ededed')
        ax4.spines['bottom'].set_color('#ededed')
        ax4.spines['top'].set_color('#ededed')
        ax4.spines['right'].set_color('#ededed')
        ax4.spines['left'].set_color('#ededed')

        canvas4 = FigureCanvasTkAgg(fig4, master=self.graphs_frame)
        canvas4.get_tk_widget().grid(row=1, column=1, sticky="nsew", padx=12, pady=8)

    def _get_sales_data(self):
        cur = self.db.cursor()
        dates = []
        revenues = []
        sales = []
        today = datetime.now().date()
        for i in range(13, -1, -1):
            day = today - timedelta(days=i)
            dates.append(day)
            cur.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM invoices WHERE DATE(timestamp)=?", (day.isoformat(),))
            s, r = cur.fetchone()
            sales.append(s or 0)
            revenues.append(r or 0.0)
        return dates, sales, revenues

    def _get_top_products(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT items FROM invoices WHERE timestamp >= DATE('now', '-30 days')
        """)
        product_sales = {}
        for (items_json,) in cur.fetchall():
            try:
                import json
                items = json.loads(items_json)
                for name, qty, price, subtotal in items:
                    product_sales[name] = product_sales.get(name, 0) + subtotal
            except Exception:
                pass
        top = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
        names = [x[0] for x in top]
        vals = [x[1] for x in top]
        return names, vals

    def _get_customer_growth(self):
        cur = self.db.cursor()
        dates = []
        counts = []
        today = datetime.now().date()
        for i in range(13, -1, -1):
            day = today - timedelta(days=i)
            dates.append(day)
            cur.execute("SELECT COUNT(*) FROM customers WHERE DATE(rowid) <= ?", (day.isoformat(),))
            c = cur.fetchone()[0]
            counts.append(c)
        return dates, counts

    def _get_expense_data(self):
        cur = self.db.cursor()
        # You can change table/column as per your Expense frame design!
        if 'expenses' not in [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]:
            return [], []
        dates = []
        vals = []
        today = datetime.now().date()
        for i in range(13, -1, -1):
            day = today - timedelta(days=i)
            dates.append(day)
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE DATE(date)=?", (day.isoformat(),))
            v = cur.fetchone()[0]
            vals.append(v or 0.0)
        return dates, vals
