import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from ui_windows import ConfirmDialog, EditFormDialog
from frames.customer_profile import CustomerProfileFrame
from utils.logger import log
from utils.helpers import refresh_all
import csv

class HoverTreeview(ttk.Treeview):
    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self._last_hover = None
        self.bind('<Motion>', self._on_motion)
        self.tag_configure('hover', background='#324076')  # Dark blue hover background

    def _on_motion(self, event):
        row_id = self.identify_row(event.y)
        if self._last_hover != row_id:
            if self._last_hover:
                self.item(self._last_hover, tags=())  # Remove hover tag from previous row
            if row_id:
                self.item(row_id, tags=('hover',))  # Add hover tag to current row
            self._last_hover = row_id

class CustomerFrame(ctk.CTkFrame):
    def __init__(self, master, db, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app
        self.set_status = set_status or (lambda msg: None)
        self.search_term = ""
        self.filter_owing = ctk.BooleanVar(value=False)
        self.displayed_rows = []  # For export

        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_form()
        self._build_search_and_filter()
        self._build_table()
        self._build_export_button()
        self.refresh_customers()

    def _build_header(self):
        ctk.CTkLabel(
            self,
            text="👥 Customer Management",
            font=("Segoe UI", 20, "bold"),
            text_color="#7dd3fc"
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 4))

    def _build_form(self):
        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.grid(row=1, column=0, sticky="ew", padx=20, pady=(6, 2))
        frm.grid_columnconfigure(0, weight=2)
        frm.grid_columnconfigure(1, weight=2)
        frm.grid_columnconfigure(2, weight=1)

        self.name_entry = ctk.CTkEntry(frm, placeholder_text="Customer Name", font=("Segoe UI", 13), corner_radius=8)
        self.phone_entry = ctk.CTkEntry(frm, placeholder_text="Phone Number", font=("Segoe UI", 13), corner_radius=8)
        self.name_entry.grid(row=0, column=0, padx=6, sticky="ew")
        self.phone_entry.grid(row=0, column=1, padx=6, sticky="ew")
        add_btn = ctk.CTkButton(frm, text="➕ Add Customer", font=("Segoe UI", 13, "bold"),
                                fg_color="#324076", hover_color="#7dd3fc", corner_radius=10,
                                command=self._on_add)
        add_btn.grid(row=0, column=2, padx=6, sticky="ew")

        self.name_entry.bind("<Return>", lambda e: self.phone_entry.focus_set())
        self.phone_entry.bind("<Return>", lambda e: add_btn.invoke())

    def _build_search_and_filter(self):
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 4))
        sf.grid_columnconfigure(0, weight=1)
        sf.grid_columnconfigure(1, weight=0)

        self.search_entry = ctk.CTkEntry(sf, placeholder_text="🔍 Search customers...", font=("Segoe UI", 13), corner_radius=7)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=6)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        filter_btn = ctk.CTkCheckBox(
            sf,
            text="Show only owing",
            variable=self.filter_owing,
            command=self.refresh_customers,
            width=30,
            height=26,
            font=("Segoe UI", 13)
        )
        filter_btn.grid(row=0, column=1, sticky="e", padx=(2, 0), pady=6)

    def _build_table(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 2))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        columns = ("name", "phone", "invoices", "spent", "owed", "profile", "edit", "delete")
        self.tree = HoverTreeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Customer Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("invoices", text="Invoices")
        self.tree.heading("spent", text="Total Spent")
        self.tree.heading("owed", text="Owed")
        self.tree.heading("profile", text="👤")
        self.tree.heading("edit", text="✏️")
        self.tree.heading("delete", text="🗑️")

        self.tree.column("name", width=200, anchor="w")
        self.tree.column("phone", width=140, anchor="center")
        self.tree.column("invoices", width=80, anchor="center")
        self.tree.column("spent", width=100, anchor="center")
        self.tree.column("owed", width=90, anchor="center")
        self.tree.column("profile", width=50, anchor="center")
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
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", lambda e: self.tree.config(cursor=""))

    def _build_export_button(self):
        exp_frame = ctk.CTkFrame(self, fg_color="transparent")
        exp_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 6))
        export_btn = ctk.CTkButton(exp_frame, text="📤 Export CSV", font=("Segoe UI", 13),
                                   fg_color="#1a8cff", hover_color="#0e68b1", corner_radius=10,
                                   command=self._export_csv)
        export_btn.pack(side="right", padx=2)

    def _on_tree_motion(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            self.tree.config(cursor="")
            return
        if region == "cell":
            col = self.tree.identify_column(event.x)
            if col in ("#6", "#7", "#8"):  # profile, edit, delete columns
                self.tree.config(cursor="hand2")
            else:
                self.tree.config(cursor="")
        else:
            self.tree.config(cursor="")

    def _on_search(self, event):
        self.search_term = self.search_entry.get().strip()
        self.refresh_customers()

    def _on_add(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        if not name:
            messagebox.showerror("Input Error", "Enter customer name.")
            return
        cur = self.db.cursor()
        try:
            cur.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
            self.db.commit()
            self.set_status(f"Added customer: {name}")
            log.info(f"Added customer: {name}")
        except Exception as e:
            log.error("Failed to add customer: %s", str(e))
            if "UNIQUE" in str(e).upper():
                messagebox.showerror("Duplicate", "Customer already exists.")
            else:
                messagebox.showerror("Error", f"Failed to add customer:\n{e}")
            return
        self.name_entry.delete(0,"end")
        self.phone_entry.delete(0,"end")
        self.refresh_customers()
        if self.app:
            refresh_all(self.app)

    def refresh_customers(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        cur = self.db.cursor()
        filter_owing = self.filter_owing.get()
        query = """
            SELECT id, name, phone,
                   (SELECT COUNT(*) FROM invoices WHERE customer_id=customers.id) AS invoice_count,
                   COALESCE((SELECT SUM(total) FROM invoices WHERE customer_id=customers.id),0) AS total_spent,
                   COALESCE((SELECT SUM(amount_owed) FROM invoices WHERE customer_id=customers.id), 0) AS total_owed
            FROM customers
        """
        params = ()
        where = []
        if self.search_term:
            where.append("(name LIKE ? OR phone LIKE ?)")
            params += (f"%{self.search_term}%", f"%{self.search_term}%")
        if filter_owing:
            where.append("(COALESCE((SELECT SUM(amount_owed) FROM invoices WHERE customer_id=customers.id), 0) > 0)")
        if where:
            query += " WHERE " + " AND ".join(where)
        if filter_owing:
            query += " ORDER BY total_owed DESC"
        else:
            query += " ORDER BY name"
        cur.execute(query, params)
        rows = cur.fetchall()
        self.displayed_rows = rows
        for cid, name, phone, inv_count, total_spent, total_owed in rows:
            self.tree.insert(
                "", "end", iid=str(cid),
                values=(name, phone, inv_count, f"₹{total_spent:.2f}", f"₹{total_owed:.2f}", "👤", "✏️", "🗑️")
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

        if colname == "delete":
            cid = int(rowid)
            cur = self.db.cursor()
            cur.execute("SELECT name FROM customers WHERE id=?", (cid,))
            row = cur.fetchone()
            if row:
                ConfirmDialog(
                    self,
                    "Delete Customer",
                    f"Delete '{row[0]}'? This will not delete invoices.",
                    lambda: self._delete_customer(cid)
                )
        elif colname == "edit":
            cid = int(rowid)
            cur = self.db.cursor()
            cur.execute("SELECT name, phone FROM customers WHERE id=?", (cid,))
            row = cur.fetchone()
            if row:
                def save_edit(values):
                    new_name = values["Name"].strip()
                    new_phone = values["Phone"].strip()
                    if not new_name:
                        messagebox.showerror("Input Error", "Enter customer name.")
                        return
                    cur.execute("UPDATE customers SET name=?, phone=? WHERE id=?", (new_name, new_phone, cid))
                    self.db.commit()
                    self.set_status(f"Customer updated: {new_name}")
                    self.refresh_customers()
                    if self.app:
                        refresh_all(self.app)

                EditFormDialog(
                    self,
                    "Edit Customer",
                    fields=["Name", "Phone"],
                    initial_values={"Name": row[0], "Phone": row[1]},
                    on_submit=save_edit
                )
        elif colname == "profile":
            cid = int(rowid)
            profile_win = CustomerProfileFrame(self, self.db, customer_id=cid)
            profile_win.transient(self.winfo_toplevel())
            profile_win.grab_set()
            profile_win.focus_set()

    def _delete_customer(self, cid):
        cur = self.db.cursor()
        cur.execute("DELETE FROM customers WHERE id=?", (cid,))
        self.db.commit()
        self.set_status("Customer deleted.")
        self.refresh_customers()
        if self.app:
            refresh_all(self.app)

    def _export_csv(self):
        if not self.displayed_rows:
            messagebox.showwarning("Export CSV", "No customers to export.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save customer list as CSV"
        )
        if not file_path:
            return
        with open(file_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Phone", "Invoices", "Total Spent", "Owed"])
            for row in self.displayed_rows:
                writer.writerow([
                    row[1], row[2], row[3], f"{row[4]:.2f}", f"{row[5]:.2f}"
                ])
        messagebox.showinfo("Exported", f"Customer list exported to {file_path}")
