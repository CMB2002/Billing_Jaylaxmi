import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog, simpledialog
from ui_windows import ConfirmDialog, EditFormDialog
from utils.helpers import refresh_all
from datetime import datetime, date, timedelta  # <-- add timedelta here
import calendar
import csv


ADMIN_PASSWORD = "7058620579"  # Set your admin password here

class StaffFrame(ctk.CTkFrame):
    def __init__(self, master, db, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app
        self.set_status = set_status or (lambda msg: None)
        self.search_term = ""
        self.displayed_rows = []

        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_tables_if_not_exists()
        self._build_header()
        self._build_form()
        self._build_search()
        self._build_table()
        self._build_export_button()
        self._auto_create_monthly_salary_expenses()
        self.refresh_staff()

    def _create_tables_if_not_exists(self):
        cur = self.db.cursor()
        # Staff
        cur.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                salary REAL NOT NULL
            )
        """)
        # Advances
        cur.execute("""
            CREATE TABLE IF NOT EXISTS staff_advances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY(staff_id) REFERENCES staff(id)
            )
        """)
        self.db.commit()

    def _build_header(self):
        ctk.CTkLabel(
            self,
            text="👔 Staff Management",
            font=("Segoe UI", 20, "bold"),
            text_color="#7dd3fc"
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 6))

    def _build_form(self):
        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.grid(row=1, column=0, sticky="ew", padx=20, pady=(4, 8))
        frm.grid_columnconfigure(0, weight=2)
        frm.grid_columnconfigure(1, weight=2)
        frm.grid_columnconfigure(2, weight=1)
        frm.grid_columnconfigure(3, weight=1)

        self.name_entry = ctk.CTkEntry(frm, placeholder_text="Staff Name", font=("Segoe UI", 13), corner_radius=8)
        self.role_entry = ctk.CTkEntry(frm, placeholder_text="Role", font=("Segoe UI", 13), corner_radius=8)
        self.salary_entry = ctk.CTkEntry(frm, placeholder_text="Salary (₹)", font=("Segoe UI", 13), corner_radius=8)
        add_btn = ctk.CTkButton(frm, text="➕ Add Staff", font=("Segoe UI", 13, "bold"),
                                fg_color="#324076", hover_color="#7dd3fc", corner_radius=10,
                                command=self._on_add)
        self.name_entry.grid(row=0, column=0, padx=6, sticky="ew")
        self.role_entry.grid(row=0, column=1, padx=6, sticky="ew")
        self.salary_entry.grid(row=0, column=2, padx=6, sticky="ew")
        add_btn.grid(row=0, column=3, padx=6, sticky="ew")

    def _build_search(self):
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 6))
        sf.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(sf, placeholder_text="🔍 Search staff by name or role...", font=("Segoe UI", 13), corner_radius=7)
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=6)
        self.search_entry.bind("<KeyRelease>", self._on_search)

    def _build_table(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 6))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        columns = ("name", "role", "salary", "advance_this_month", "add_advance", "edit", "delete")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("name", text="Name")
        self.tree.heading("role", text="Role")
        self.tree.heading("salary", text="Salary (₹)")
        self.tree.heading("advance_this_month", text="Advance Paid (₹)")
        self.tree.heading("add_advance", text="Advance")
        self.tree.heading("edit", text="✏️")
        self.tree.heading("delete", text="🗑️")

        self.tree.column("name", width=180, anchor="w")
        self.tree.column("role", width=130, anchor="center")
        self.tree.column("salary", width=110, anchor="center")
        self.tree.column("advance_this_month", width=140, anchor="center")
        self.tree.column("add_advance", width=100, anchor="center")
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

    def _on_add(self):
        name = self.name_entry.get().strip()
        role = self.role_entry.get().strip()
        salary_text = self.salary_entry.get().strip()
        if not name or not role:
            messagebox.showerror("Input Error", "Name and Role are required.")
            return
        try:
            salary = float(salary_text)
            if salary < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Salary must be a positive number.")
            return

        cur = self.db.cursor()
        try:
            cur.execute("INSERT INTO staff (name, role, salary) VALUES (?, ?, ?)",
                        (name, role, salary))
            self.db.commit()
            self.set_status(f"Added staff member: {name}")
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not add staff member:\n{e}")
            return

        self.name_entry.delete(0, "end")
        self.role_entry.delete(0, "end")
        self.salary_entry.delete(0, "end")
        self.refresh_staff()
        if self.app:
            refresh_all(self.app)

    def _on_search(self, event):
        self.search_term = self.search_entry.get().strip()
        self.refresh_staff()

    def refresh_staff(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        cur = self.db.cursor()
        # Get all staff
        query = "SELECT id, name, role, salary FROM staff"
        params = []
        if self.search_term:
            query += " WHERE name LIKE ? OR role LIKE ?"
            params.extend((f"%{self.search_term}%", f"%{self.search_term}%"))
        query += " ORDER BY name"
        cur.execute(query, params)
        rows = cur.fetchall()
        self.displayed_rows = rows

        # Get advance payment totals for this month
        advances = {}
        month_start = date.today().replace(day=1).isoformat()
        next_month = (date.today().replace(day=28) + timedelta(days=4)).replace(day=1).isoformat()
        for sid, *_ in rows:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM staff_advances 
                WHERE staff_id=? AND date>=? AND date<? 
            """, (sid, month_start, next_month))
            advances[sid] = cur.fetchone()[0]

        for sid, name, role, salary in rows:
            advance = advances.get(sid, 0.0)
            self.tree.insert("", "end", iid=str(sid),
                             values=(name, role, f"₹{salary:.2f}", f"₹{advance:.2f}", "➕", "✏️", "🗑️"))

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
        sid = int(rowid)
        cur = self.db.cursor()

        if colname == "add_advance":
            staff_row = self.tree.item(rowid, "values")
            name = staff_row[0]
            salary = float(staff_row[2].replace("₹", ""))
            # Get current month advance
            month_start = date.today().replace(day=1).isoformat()
            next_month = (date.today().replace(day=28) + timedelta(days=4)).replace(day=1).isoformat()
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0) FROM staff_advances 
                WHERE staff_id=? AND date>=? AND date<? 
            """, (sid, month_start, next_month))
            current_advance = cur.fetchone()[0]

            # Ask amount
            amount = simpledialog.askfloat(
                "Advance Payment",
                f"Enter advance payment for {name} (max salary: ₹{salary:.2f}):",
                minvalue=0, maxvalue=salary
            )
            if amount is None or amount <= 0:
                return

            # If adding would exceed salary, ask admin password
            if current_advance + amount > salary:
                pw = simpledialog.askstring("Admin Password Required", "Advance exceeds salary for this month. Enter admin password:", show="*")
                if pw != ADMIN_PASSWORD:
                    messagebox.showerror("Admin Check", "Incorrect admin password. Operation cancelled.")
                    return

            # Record advance in DB and instantly create expense
            today_str = date.today().isoformat()
            cur.execute("INSERT INTO staff_advances (staff_id, amount, date) VALUES (?, ?, ?)", (sid, amount, today_str))
            cur.execute(
                "INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
                (today_str, "Staff Advance Payment", amount, f"Advance payment to {name}"))
            self.db.commit()
            self.set_status(f"Advance payment ₹{amount:.2f} given to {name}.")
            self.refresh_staff()
            if self.app:
                refresh_all(self.app)

        elif colname == "delete":
            cur.execute("SELECT name FROM staff WHERE id=?", (sid,))
            row = cur.fetchone()
            if row:
                ConfirmDialog(
                    self,
                    "Delete Staff Member",
                    f"Delete staff member '{row[0]}'? (Advances history will remain.)",
                    lambda: self._delete_staff(sid)
                )
        elif colname == "edit":
            cur.execute("SELECT name, role, salary FROM staff WHERE id=?", (sid,))
            row = cur.fetchone()
            if row:
                def save_edit(values):
                    try:
                        salary = float(values["Salary (₹)"])
                        if salary < 0:
                            raise ValueError
                    except ValueError:
                        messagebox.showerror("Input Error", "Salary must be a positive number.")
                        return
                    cur.execute(
                        "UPDATE staff SET name=?, role=?, salary=? WHERE id=?",
                        (values["Name"], values["Role"], salary, sid)
                    )
                    self.db.commit()
                    self.set_status(f"Staff member updated: {values['Name']}")
                    self.refresh_staff()
                    if self.app:
                        refresh_all(self.app)

                EditFormDialog(
                    self,
                    "Edit Staff Member",
                    fields=["Name", "Role", "Salary (₹)"],
                    initial_values={
                        "Name": row[0],
                        "Role": row[1],
                        "Salary (₹)": str(row[2])
                    },
                    on_submit=save_edit
                )

    def _delete_staff(self, sid):
        cur = self.db.cursor()
        cur.execute("DELETE FROM staff WHERE id=?", (sid,))
        self.db.commit()
        self.set_status("Staff member deleted.")
        self.refresh_staff()
        if self.app:
            refresh_all(self.app)

    def _export_csv(self):
        if not self.displayed_rows:
            messagebox.showwarning("Export CSV", "No staff members to export.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save staff list as CSV"
        )
        if not file_path:
            return
        with open(file_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Role", "Salary (₹)", "Advance Paid This Month (₹)"])
            for row in self.displayed_rows:
                sid, name, role, salary = row
                advance = self._get_advance_this_month(sid)
                writer.writerow([name, role, f"{salary:.2f}", f"{advance:.2f}"])
        messagebox.showinfo("Exported", f"Staff list exported to {file_path}")

    def _get_advance_this_month(self, sid):
        cur = self.db.cursor()
        month_start = date.today().replace(day=1).isoformat()
        next_month = (date.today().replace(day=28) + timedelta(days=4)).replace(day=1).isoformat()
        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM staff_advances 
            WHERE staff_id=? AND date>=? AND date<? 
        """, (sid, month_start, next_month))
        return cur.fetchone()[0]

    def _auto_create_monthly_salary_expenses(self):
        """On the 1st of each month, create a net payout expense for each staff (salary - total advances taken that month)."""
        today = date.today()
        if today.day != 1:
            return  # Only run on the 1st day of the month

        cur = self.db.cursor()
        # Prevent duplicate payouts for the month
        cur.execute("""
            SELECT COUNT(*) FROM expenses WHERE category='Staff Salary Payout' 
            AND date BETWEEN date('now','start of month') AND date('now','start of month','+1 month','-1 day')
        """)
        count = cur.fetchone()[0]
        if count > 0:
            return

        cur.execute("SELECT id, name, salary FROM staff")
        staff_list = cur.fetchall()
        for sid, name, salary in staff_list:
            advance = self._get_advance_this_month(sid)
            net_payout = max(salary - advance, 0.0)
            cur.execute(
                "INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
                (today.isoformat(), "Staff Salary Payout", net_payout, f"Net salary to {name} (Salary: ₹{salary:.2f} - Advance: ₹{advance:.2f})"))
        self.db.commit()
        self.set_status("Created staff salary payout expenses for this month.")
        if self.app:
            refresh_all(self.app)
