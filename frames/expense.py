import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from ui_windows import ConfirmDialog, EditFormDialog
from utils.helpers import refresh_all
from datetime import datetime
from tkcalendar import DateEntry
import csv

class ExpenseFrame(ctk.CTkFrame):
    def __init__(self, master, db, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app
        self.set_status = set_status or (lambda msg: None)
        self.search_term = ""

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_form()
        self._build_search_filter()
        self._build_table()
        self._build_export_button()
        self.refresh_expenses()

    def _build_header(self):
        ctk.CTkLabel(
            self,
            text="💸 Expense Management",
            font=("Segoe UI", 20, "bold"),
            text_color="#7dd3fc"
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 4))

    def _build_form(self):
        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.grid(row=1, column=0, sticky="ew", padx=20, pady=(4, 8))
        frm.grid_columnconfigure(0, weight=1)
        frm.grid_columnconfigure(1, weight=1)
        frm.grid_columnconfigure(2, weight=1)
        frm.grid_columnconfigure(3, weight=1)
        frm.grid_columnconfigure(4, weight=1)

        ctk.CTkLabel(frm, text="Date:", font=("Segoe UI", 13)).grid(row=0, column=0, sticky="w", padx=(4,8))
        self.date_entry = DateEntry(frm, date_pattern="yyyy-mm-dd", font=("Segoe UI", 13), width=14)
        self.date_entry.grid(row=0, column=1, sticky="ew", padx=4)

        ctk.CTkLabel(frm, text="Category:", font=("Segoe UI", 13)).grid(row=0, column=2, sticky="w", padx=(12,8))
        self.category_var = ctk.StringVar(value="Salaries")
        categories = [
            "Salaries", "Rent", "Maintenance", "Utilities", "Marketing",
            "Office Supplies", "Travel", "Insurance", "Tax", "Others"
        ]
        self.category_menu = ctk.CTkOptionMenu(frm, values=categories, variable=self.category_var, font=("Segoe UI", 13))
        self.category_menu.grid(row=0, column=3, sticky="ew", padx=4)

        ctk.CTkLabel(frm, text="Amount:", font=("Segoe UI", 13)).grid(row=0, column=4, sticky="w", padx=(12,8))
        self.amount_entry = ctk.CTkEntry(frm, placeholder_text="₹0.00", font=("Segoe UI", 13), corner_radius=7)
        self.amount_entry.grid(row=0, column=5, sticky="ew", padx=4)

        ctk.CTkLabel(frm, text="Note:", font=("Segoe UI", 13)).grid(row=1, column=0, sticky="w", padx=(4,8), pady=(12,0))
        self.note_entry = ctk.CTkEntry(frm, placeholder_text="Optional notes", font=("Segoe UI", 13), corner_radius=7)
        self.note_entry.grid(row=1, column=1, columnspan=4, sticky="ew", padx=4, pady=(12,0))

        add_btn = ctk.CTkButton(
            frm, text="➕ Add Expense", font=("Segoe UI", 14, "bold"),
            fg_color="#324076", hover_color="#7dd3fc", corner_radius=10,
            command=self._on_add_expense
        )
        add_btn.grid(row=1, column=5, sticky="ew", padx=4, pady=(12,0))

    def _build_search_filter(self):
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 6))
        sf.grid_columnconfigure(0, weight=1)
        sf.grid_columnconfigure(1, weight=0)
        sf.grid_columnconfigure(2, weight=0)

        self.search_entry = ctk.CTkEntry(sf, placeholder_text="🔍 Search expenses...", font=("Segoe UI", 13), corner_radius=7)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=6)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        ctk.CTkLabel(sf, text="Filter by category:", font=("Segoe UI", 13)).grid(row=0, column=1, sticky="e", padx=(8,4))
        self.filter_category = ctk.StringVar(value="All")
        categories = ["All", "Salaries", "Rent", "Maintenance", "Utilities", "Marketing", "Office Supplies", "Travel", "Insurance", "Tax", "Others"]
        self.category_filter_menu = ctk.CTkOptionMenu(sf, values=categories, variable=self.filter_category, font=("Segoe UI", 13), width=140)
        self.category_filter_menu.grid(row=0, column=2, sticky="e", padx=(0, 0))
        self.category_filter_menu.configure(command=lambda _: self.refresh_expenses())

    def _build_table(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 6))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        columns = ("date", "category", "amount", "note", "edit", "delete")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("amount", text="Amount")
        self.tree.heading("note", text="Note")
        self.tree.heading("edit", text="✏️")
        self.tree.heading("delete", text="🗑️")

        self.tree.column("date", width=120, anchor="center")
        self.tree.column("category", width=140, anchor="center")
        self.tree.column("amount", width=100, anchor="center")
        self.tree.column("note", width=300, anchor="w")
        self.tree.column("edit", width=40, anchor="center")
        self.tree.column("delete", width=40, anchor="center")

        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview",
                        background="#1b1d22",
                        foreground="#ededed",
                        rowheight=32,
                        fieldbackground="#23252a",
                        font=("Segoe UI", 13))
        style.configure("Treeview.Heading", font=("Segoe UI", 13, "bold"))
        style.map("Treeview", background=[('selected', '#324076')])

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Button-1>", self._on_tree_click)

    def _build_export_button(self):
        exp_frame = ctk.CTkFrame(self, fg_color="transparent")
        exp_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 10))
        export_btn = ctk.CTkButton(exp_frame, text="📤 Export CSV", font=("Segoe UI", 13),
                                   fg_color="#1a8cff", hover_color="#0e68b1", corner_radius=10,
                                   command=self._export_csv)
        export_btn.pack(side="right", padx=2)

    def _on_add_expense(self):
        date = self.date_entry.get_date().strftime("%Y-%m-%d")
        category = self.category_var.get()
        amount_text = self.amount_entry.get().strip()
        note = self.note_entry.get().strip()

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Enter a valid positive amount.")
            return

        cur = self.db.cursor()
        cur.execute("INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
                    (date, category, amount, note))
        self.db.commit()
        self.set_status(f"Expense added: {category} - ₹{amount:.2f}")

        # Clear form
        self.amount_entry.delete(0, "end")
        self.note_entry.delete(0, "end")
        self.category_var.set("Salaries")
        self.date_entry.set_date(datetime.now())

        self.refresh_expenses()
        if self.app:
            refresh_all(self.app)

    def _on_search(self, event):
        self.search_term = self.search_entry.get().strip()
        self.refresh_expenses()

    def refresh_expenses(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        cur = self.db.cursor()

        query = "SELECT id, date, category, amount, note FROM expenses"
        params = []
        filters = []
        if self.search_term:
            filters.append("(category LIKE ? OR note LIKE ?)")
            params.extend((f"%{self.search_term}%", f"%{self.search_term}%"))
        cat_filter = self.filter_category.get()
        if cat_filter and cat_filter != "All":
            filters.append("category = ?")
            params.append(cat_filter)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY date DESC"

        cur.execute(query, params)
        rows = cur.fetchall()
        for eid, date, category, amount, note in rows:
            self.tree.insert("", "end", iid=str(eid),
                             values=(date, category, f"₹{amount:.2f}", note, "✏️", "🗑️"))

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

        if colname == "delete":
            eid = int(rowid)
            cur = self.db.cursor()
            cur.execute("SELECT category, amount FROM expenses WHERE id=?", (eid,))
            row = cur.fetchone()
            if row:
                ConfirmDialog(
                    self,
                    "Delete Expense",
                    f"Delete {row[0]} expense of ₹{row[1]:.2f}?",
                    lambda: self._delete_expense(eid)
                )
        elif colname == "edit":
            eid = int(rowid)
            cur = self.db.cursor()
            cur.execute("SELECT date, category, amount, note FROM expenses WHERE id=?", (eid,))
            row = cur.fetchone()
            if row:
                def save_edit(values):
                    try:
                        amount = float(values["Amount"])
                        if amount <= 0:
                            raise ValueError
                    except ValueError:
                        messagebox.showerror("Input Error", "Enter a valid positive amount.")
                        return
                    cur.execute("UPDATE expenses SET date=?, category=?, amount=?, note=? WHERE id=?",
                                (values["Date"], values["Category"], amount, values["Note"], eid))
                    self.db.commit()
                    self.set_status(f"Expense updated: {values['Category']} - ₹{amount:.2f}")
                    self.refresh_expenses()
                    if self.app:
                        refresh_all(self.app)

                EditFormDialog(
                    self,
                    "Edit Expense",
                    fields=["Date", "Category", "Amount", "Note"],
                    initial_values={
                        "Date": row[0],
                        "Category": row[1],
                        "Amount": str(row[2]),
                        "Note": row[3] or ""
                    },
                    on_submit=save_edit
                )

    def _delete_expense(self, eid):
        cur = self.db.cursor()
        cur.execute("DELETE FROM expenses WHERE id=?", (eid,))
        self.db.commit()
        self.set_status("Expense deleted.")
        self.refresh_expenses()
        if self.app:
            refresh_all(self.app)

    def _export_csv(self):
        cur = self.db.cursor()
        query = "SELECT date, category, amount, note FROM expenses"
        params = []
        filters = []
        if self.search_term:
            filters.append("(category LIKE ? OR note LIKE ?)")
            params.extend((f"%{self.search_term}%", f"%{self.search_term}%"))
        cat_filter = self.filter_category.get()
        if cat_filter and cat_filter != "All":
            filters.append("category = ?")
            params.append(cat_filter)
        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY date DESC"
        cur.execute(query, params)
        rows = cur.fetchall()
        if not rows:
            messagebox.showwarning("Export CSV", "No expenses to export.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save expenses list as CSV"
        )
        if not file_path:
            return
        with open(file_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Category", "Amount", "Note"])
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"Expenses exported to {file_path}")
