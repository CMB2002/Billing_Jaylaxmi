import customtkinter as ctk
from tkinter import ttk, messagebox
from ui_windows import ConfirmDialog, EditFormDialog
from frames.customer_profile import CustomerProfileFrame
from utils.logger import log
from utils.helpers import refresh_all

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

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_form()
        self._build_search()
        self._build_table()
        self.refresh_customers()

    def _build_form(self):
        frm = ctk.CTkFrame(self)
        frm.grid(row=0, column=0, sticky="ew", padx=20, pady=(2, 1))
        frm.grid_columnconfigure(0, weight=2)
        frm.grid_columnconfigure(1, weight=2)
        frm.grid_columnconfigure(2, weight=1)

        self.name_entry = ctk.CTkEntry(frm, placeholder_text="Customer Name")
        self.phone_entry = ctk.CTkEntry(frm, placeholder_text="Phone Number")
        self.name_entry.grid(row=0, column=0, padx=5, sticky="ew")
        self.phone_entry.grid(row=0, column=1, padx=5, sticky="ew")
        add_btn = ctk.CTkButton(frm, text="Add Customer", command=self._on_add)
        add_btn.grid(row=0, column=2, padx=5)

        self.name_entry.bind("<Return>", lambda e: self.phone_entry.focus_set())
        self.phone_entry.bind("<Return>", lambda e: add_btn.invoke())

    def _build_search(self):
        sf = ctk.CTkFrame(self)
        sf.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 1))
        sf.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(sf, placeholder_text="Search customers...")
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search)

    def _build_table(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 2))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        columns = ("name", "phone", "invoices", "spent", "profile", "edit", "delete")
        self.tree = HoverTreeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Customer Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("invoices", text="Invoices")
        self.tree.heading("spent", text="Total Spent")
        self.tree.heading("profile", text="👤")
        self.tree.heading("edit", text="✏️")
        self.tree.heading("delete", text="🗑️")

        self.tree.column("name", width=200, anchor="w")
        self.tree.column("phone", width=140, anchor="center")
        self.tree.column("invoices", width=80, anchor="center")
        self.tree.column("spent", width=100, anchor="center")
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

    def _on_tree_motion(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "heading":
            self.tree.config(cursor="")
            return
        if region == "cell":
            col = self.tree.identify_column(event.x)
            # Only change cursor for profile, edit, delete columns (#5, #6, #7)
            if col in ("#5", "#6", "#7"):
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
        if self.search_term:
            q = f"%{self.search_term}%"
            cur.execute("""
                SELECT id, name, phone,
                       (SELECT COUNT(*) FROM invoices WHERE customer_id=customers.id) AS invoice_count,
                       COALESCE((SELECT SUM(total) FROM invoices WHERE customer_id=customers.id),0) AS total_spent
                FROM customers
                WHERE name LIKE ? OR phone LIKE ?
                ORDER BY name
            """, (q,q))
        else:
            cur.execute("""
                SELECT id, name, phone,
                       (SELECT COUNT(*) FROM invoices WHERE customer_id=customers.id) AS invoice_count,
                       COALESCE((SELECT SUM(total) FROM invoices WHERE customer_id=customers.id),0) AS total_spent
                FROM customers
                ORDER BY name
            """)

        rows = cur.fetchall()
        for cid, name, phone, inv_count, total_spent in rows:
            self.tree.insert(
                "", "end", iid=str(cid),
                values=(name, phone, inv_count, f"₹{total_spent:.2f}", "👤", "✏️", "🗑️")
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
            profile_win.transient(self.winfo_toplevel())  # Make modal to main window
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
