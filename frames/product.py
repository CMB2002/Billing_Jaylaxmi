import customtkinter as ctk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilename
from ui_windows import ConfirmDialog, EditFormDialog
from utils.logger import log
from utils.helpers import refresh_all

class ProductFrame(ctk.CTkFrame):
    def __init__(self, master, db, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app  # main app instance for centralized refresh
        self.set_status = set_status or (lambda msg: None)
        self.search_term = ""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_form()
        self._build_search()
        self._build_table()
        self._create_table()
        self.refresh_products()

    def _build_form(self):
        frm = ctk.CTkFrame(self)
        frm.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        for i in range(5):
            frm.grid_columnconfigure(i, weight=1)
        self.name_entry  = ctk.CTkEntry(frm, placeholder_text="Product Name")
        self.price_entry = ctk.CTkEntry(frm, placeholder_text="Price")
        self.stock_entry = ctk.CTkEntry(frm, placeholder_text="Stock")
        self.name_entry.grid(row=0,column=0, padx=5, sticky="ew")
        self.price_entry.grid(row=0,column=1, padx=5, sticky="ew")
        self.stock_entry.grid(row=0,column=2, padx=5, sticky="ew")
        add_btn = ctk.CTkButton(frm, text="Add Product", command=self._on_add)
        add_btn.grid(row=0, column=3, padx=5)
        import_btn = ctk.CTkButton(frm, text="Import CSV", command=self._import_csv)
        import_btn.grid(row=0, column=4, padx=5)
        self.name_entry.bind("<Return>", lambda e: self.price_entry.focus_set())
        self.price_entry.bind("<Return>", lambda e: self.stock_entry.focus_set())
        self.stock_entry.bind("<Return>", lambda e: add_btn.invoke())

    def _build_search(self):
        sf = ctk.CTkFrame(self)
        sf.grid(row=1, column=0, sticky="ew", padx=20, pady=(0,10))
        sf.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(sf, placeholder_text="Search products...")
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._on_search)

    def _build_table(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0,10))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        columns = ("name", "price", "stock", "delete")
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#1b1d22",
            fieldbackground="#23252a",
            foreground="#ededed",
            rowheight=38,
            font=("Segoe UI", 15),
            bordercolor="#23252a",
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#20232a",
            foreground="#fafafa",
            font=("Segoe UI", 16, "bold")
        )
        style.map("Treeview", background=[('selected', '#324076')])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Product Name")
        self.tree.heading("price", text="Price")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("delete", text="")
        self.tree.column("name", width=280, anchor="w")
        self.tree.column("price", width=90, anchor="center")
        self.tree.column("stock", width=90, anchor="center")
        self.tree.column("delete", width=80, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        self.tree.bind("<Button-1>", self._on_tree_click)

        self.tree.tag_configure('hover', background='#232940')
        self.tree.tag_configure('delete-hover', foreground='#ff5858')
        self.tree.tag_configure("stripe", background="#23252a")
        self.tree.bind('<Motion>', self._on_tree_motion)
        self.tree.bind('<Leave>', self._on_tree_leave)
        self.last_row = None
        self.last_col = None

    def _create_table(self):
        cur = self.db.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT    UNIQUE NOT NULL,
                price REAL    NOT NULL,
                stock INTEGER NOT NULL
            )
        """)
        self.db.commit()

    def _on_add(self):
        name = self.name_entry.get().strip()
        try:
            price = float(self.price_entry.get())
            stock = int(self.stock_entry.get())
        except ValueError:
            self.set_status("Invalid price/stock.")
            return messagebox.showerror("Input Error", "Enter valid price & stock.")
        cur = self.db.cursor()
        try:
            cur.execute("INSERT INTO products (name,price,stock) VALUES (?,?,?)",
                        (name,price,stock))
            self.db.commit()
        except Exception as e:
            if "UNIQUE" in str(e):
                self.set_status("Product already exists.")
                return messagebox.showerror("Duplicate", "Product already exists.")
            raise
        self.name_entry.delete(0, "end")
        self.price_entry.delete(0, "end")
        self.stock_entry.delete(0, "end")
        self.set_status(f"Added product: {name}")
        log.info(f"Product added successfully: {name}")
        self.refresh_products()
        if self.app:
            refresh_all(self.app)

    def _on_search(self, event):
        self.search_term = self.search_entry.get().strip()
        self.refresh_products()

    def _import_csv(self):
        path = askopenfilename(title="Select CSV", filetypes=[("CSV or Excel Files", "*.csv *.xlsx *.xls")])
        if not path:
            return
        count, skipped = 0, 0
        try:
            import pandas as pd
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            cols = [col.lower().strip().replace(" ", "") for col in df.columns]
            df.columns = cols
            colmap = {}
            for col in cols:
                if col in ("name", "productname"):
                    colmap['name'] = col
                elif col == "price":
                    colmap['price'] = col
                elif col == "stock":
                    colmap['stock'] = col
            if set(colmap) != {"name", "price", "stock"}:
                raise Exception("File must have columns: Product Name (or name), Price, Stock")
            for _, row in df.iterrows():
                try:
                    name = str(row[colmap['name']]).strip()
                    price = float(row[colmap['price']])
                    stock = int(row[colmap['stock']])
                    cur = self.db.cursor()
                    cur.execute("INSERT OR IGNORE INTO products (name,price,stock) VALUES (?,?,?)", (name, price, stock))
                    self.db.commit()
                    count += 1
                except Exception:
                    skipped += 1
            msg = f"Imported {count} products."
            if skipped: msg += f" Skipped {skipped} invalid/duplicate rows."
            self.set_status(msg)
            self.refresh_products()
            messagebox.showinfo("Import Finished", msg)
            if self.app:
                refresh_all(self.app)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {e}")

    def refresh_products(self):
        self.tree.delete(*self.tree.get_children())
        cur = self.db.cursor()
        if self.search_term:
            q = f"%{self.search_term}%"
            cur.execute("SELECT id, name, price, stock FROM products WHERE name LIKE ? COLLATE NOCASE ORDER BY name", (q,))
        else:
            cur.execute("SELECT id, name, price, stock FROM products ORDER BY name")
        for i, (pid, name, price, stock) in enumerate(cur.fetchall()):
            tags = ()
            if i % 2 == 1:
                tags = ("stripe",)
            self.tree.insert(
                "", "end", iid=str(pid),
                values=(name, f"₹{price:.2f}", stock, "🗑️"),
                tags=tags
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
            pid = int(rowid)
            cur = self.db.cursor()
            cur.execute("SELECT name FROM products WHERE id=?", (pid,))
            row = cur.fetchone()
            if row:
                ConfirmDialog(
                    self,
                    "Delete Product",
                    f"Delete '{row[0]}'?",
                    lambda: self._on_delete(pid)
                )
        else:
            self.tree.selection_set(rowid)

    def _on_tree_double_click(self, event):
        rowid = self.tree.identify_row(event.y)
        if not rowid:
            return
        pid = int(rowid)
        cur = self.db.cursor()
        cur.execute("SELECT name, price, stock FROM products WHERE id=?", (pid,))
        row = cur.fetchone()
        if row:
            def save_edit(values):
                try:
                    price = float(values["Price"])
                    stock = int(values["Stock"])
                except ValueError:
                    messagebox.showerror("Input Error", "Enter valid price & stock.")
                    return
                self._on_edit(pid, values["Name"], price, stock)
            EditFormDialog(
                self,
                f"Edit Product #{pid}",
                fields=["Name", "Price", "Stock"],
                initial_values={"Name": row[0], "Price": str(row[1]), "Stock": str(row[2])},
                on_submit=save_edit
            )

    def _on_delete(self, pid):
        cur = self.db.cursor()
        cur.execute("DELETE FROM products WHERE id = ?", (pid,))
        self.db.commit()
        self.set_status("Product deleted.")
        self.refresh_products()
        if self.app:
            refresh_all(self.app)

    def _on_edit(self, pid, name, price, stock):
        cur = self.db.cursor()
        cur.execute("""
            UPDATE products
               SET name=?, price=?, stock=?
             WHERE id=?
        """, (name, price, stock, pid))
        self.db.commit()
        self.set_status(f"Product updated: {name}")
        self.refresh_products()
        if self.app:
            refresh_all(self.app)
    
    def _on_tree_motion(self, event):
        rowid = self.tree.identify_row(event.y)
        colid = self.tree.identify_column(event.x)
        if self.last_row is not None and self.last_col is not None:
            self.tree.item(self.last_row, tags=())
        if rowid:
            if colid == '#4':
                self.tree.item(rowid, tags=('delete-hover',))
            else:
                self.tree.item(rowid, tags=('hover',))
            self.last_row, self.last_col = rowid, colid
        else:
            self.last_row = None
            self.last_col = None

    def _on_tree_leave(self, event):
        if self.last_row is not None:
            self.tree.item(self.last_row, tags=())
        self.last_row = None
        self.last_col = None
