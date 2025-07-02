import customtkinter as ctk
from tkinter import messagebox

class AddProductDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, name, qty, on_success):
        super().__init__(parent)
        self.title("Add New Product")
        self.geometry("600x750")  # Doubled height

        self.db = db
        self.on_success = on_success

        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="Add New Product", font=("Segoe UI", 15, "bold")).pack(pady=(26, 16))

        ctk.CTkLabel(self, text="Product Name:", font=("Segoe UI", 13)).pack(anchor="w", padx=56)
        self.name_var = ctk.StringVar(value=name)
        name_entry = ctk.CTkEntry(self, textvariable=self.name_var, font=("Segoe UI", 13))
        name_entry.pack(fill="x", padx=56, pady=(0, 20))

        ctk.CTkLabel(self, text="Quantity:", font=("Segoe UI", 13)).pack(anchor="w", padx=56)
        self.qty_var = ctk.StringVar(value=str(qty))
        qty_entry = ctk.CTkEntry(self, textvariable=self.qty_var, font=("Segoe UI", 13))
        qty_entry.pack(fill="x", padx=56, pady=(0, 20))

        ctk.CTkLabel(self, text="Stock:", font=("Segoe UI", 13)).pack(anchor="w", padx=56)
        default_stock = int(qty) * 10 if str(qty).isdigit() else 10
        self.stock_var = ctk.StringVar(value=str(default_stock))
        stock_entry = ctk.CTkEntry(self, textvariable=self.stock_var, font=("Segoe UI", 13))
        stock_entry.pack(fill="x", padx=56, pady=(0, 20))

        ctk.CTkLabel(self, text="Min Price:", font=("Segoe UI", 13)).pack(anchor="w", padx=56)
        self.min_price_var = ctk.StringVar(value="0")
        min_price_entry = ctk.CTkEntry(self, textvariable=self.min_price_var, font=("Segoe UI", 13))
        min_price_entry.pack(fill="x", padx=56, pady=(0, 20))

        ctk.CTkLabel(self, text="Max Price:", font=("Segoe UI", 13)).pack(anchor="w", padx=56)
        self.max_price_var = ctk.StringVar(value="0")
        max_price_entry = ctk.CTkEntry(self, textvariable=self.max_price_var, font=("Segoe UI", 13))
        max_price_entry.pack(fill="x", padx=56, pady=(0, 20))

        ctk.CTkLabel(self, text="Purchase Price:", font=("Segoe UI", 13)).pack(anchor="w", padx=56)
        self.purchase_price_var = ctk.StringVar(value="0")
        purchase_price_entry = ctk.CTkEntry(self, textvariable=self.purchase_price_var, font=("Segoe UI", 13))
        purchase_price_entry.pack(fill="x", padx=56, pady=(0, 30))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(10, 18))
        add_btn = ctk.CTkButton(btn_frame, text="Add", command=self._add_product, width=120, font=("Segoe UI", 13, "bold"))
        add_btn.pack(side="left", padx=60)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=self._on_cancel, width=100)
        cancel_btn.pack(side="right", padx=60)

        self.bind("<Return>", lambda e: self._add_product())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.resizable(False, False)

    def _add_product(self):
        name = self.name_var.get().strip()
        try:
            qty = int(self.qty_var.get().strip())
            stock = int(self.stock_var.get().strip())
            min_price = int(self.min_price_var.get().strip())
            max_price = int(self.max_price_var.get().strip())
            purchase_price = int(self.purchase_price_var.get().strip())
        except Exception:
            messagebox.showerror("Invalid Input", "Enter numeric values for qty, stock, and prices.", parent=self)
            return
        if not name or qty <= 0:
            messagebox.showerror("Input Error", "Product name and valid quantity are required.", parent=self)
            return
        try:
            cur = self.db.cursor()
            cur.execute("INSERT INTO products (name, stock, min_price, max_price, purchase_price) VALUES (?, ?, ?, ?, ?)",
                        (name, stock, min_price, max_price, purchase_price))
            self.db.commit()
            if self.on_success:
                product_info = {
                    "name": name, "qty": qty,
                    "min_price": min_price, "max_price": max_price, "purchase_price": purchase_price,
                    "assigned_price": None, "total": None
                }
                self.on_success(product_info)
            self.destroy()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not add product:\n{e}", parent=self)
            self.destroy()

    def _on_cancel(self):
        self.destroy()
