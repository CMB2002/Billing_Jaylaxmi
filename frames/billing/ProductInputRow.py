import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from .add_product_dialog import AddProductDialog  # <-- Make sure this file is present

class ProductInputRow(ctk.CTkFrame):
    def __init__(self, master, db, on_add_to_cart=None, set_status=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.master = master.winfo_toplevel()
        self.on_add_to_cart = on_add_to_cart
        self.set_status = set_status or (lambda msg: None)

        self.grid_columnconfigure((0, 1, 2), weight=1)

        self.prod_entry = ctk.CTkEntry(self, placeholder_text="Product Name", font=("Segoe UI", 13))
        self.prod_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.prod_entry.bind("<KeyRelease>", self._on_keyrelease)
        self.prod_entry.bind("<Down>", self._focus_suggestions_first)
        self.prod_entry.bind("<FocusOut>", self._on_entry_focusout)

        self.qty_entry = ctk.CTkEntry(self, placeholder_text="Quantity", font=("Segoe UI", 13))
        self.qty_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.qty_entry.bind("<Return>", lambda e: self.add_product_to_cart())

        self.add_btn = ctk.CTkButton(self, text="➕ Add to Cart", font=("Segoe UI", 13, "bold"),
                                     command=self.add_product_to_cart)
        self.add_btn.grid(row=0, column=2, padx=5, pady=5)

        self.suggestions = tk.Listbox(self.master, font=("Segoe UI", 13), height=6,
                                      bg="#222831", fg="#ffffff",
                                      selectbackground="#68a1ff", selectforeground="#101318",
                                      highlightthickness=1, highlightcolor="#444",
                                      relief="flat", borderwidth=1, activestyle="none")
        self.suggestions.bind("<Down>", self._on_down)
        self.suggestions.bind("<Up>", self._on_up)
        self.suggestions.bind("<Return>", self._on_select)
        self.suggestions.bind("<ButtonRelease-1>", self._on_select)
        self.suggestions.bind("<FocusOut>", self._on_suggestions_focusout)
        self.listbox_visible = False

    def _on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Return"):
            return
        self.update_suggestions()

    def _focus_suggestions_first(self, event=None):
        if self.listbox_visible and self.suggestions.size() > 0:
            self.suggestions.focus_set()
            self.suggestions.selection_clear(0, tk.END)
            self.suggestions.selection_set(0)
            self.suggestions.activate(0)
        return "break"

    def _on_down(self, event=None):
        sel = self.suggestions.curselection()
        size = self.suggestions.size()
        if not sel:
            idx = 0
        else:
            idx = sel[0] + 1
            if idx >= size:
                idx = size - 1
        self.suggestions.selection_clear(0, tk.END)
        self.suggestions.selection_set(idx)
        self.suggestions.activate(idx)
        return "break"

    def _on_up(self, event=None):
        sel = self.suggestions.curselection()
        size = self.suggestions.size()
        if not sel:
            idx = 0
        else:
            idx = sel[0] - 1
            if idx < 0:
                idx = 0
        self.suggestions.selection_clear(0, tk.END)
        self.suggestions.selection_set(idx)
        self.suggestions.activate(idx)
        return "break"

    def _on_select(self, event=None):
        sel = self.suggestions.curselection()
        if sel:
            name = self.suggestions.get(sel[0])
            self.prod_entry.delete(0, tk.END)
            self.prod_entry.insert(0, name.strip())
            self.suggestions.place_forget()
            self.listbox_visible = False
            self.qty_entry.focus_set()
        return "break"

    def _on_entry_focusout(self, event=None):
        widget = self.master.focus_get()
        if widget != self.suggestions:
            self.suggestions.place_forget()
            self.listbox_visible = False

    def _on_suggestions_focusout(self, event=None):
        self.suggestions.place_forget()
        self.listbox_visible = False

    def update_suggestions(self):
        term = self.prod_entry.get().strip()
        if term:
            cursor = self.db.cursor()
            cursor.execute("SELECT name FROM products WHERE name LIKE ? COLLATE NOCASE LIMIT 8", (f"%{term}%",))
            results = cursor.fetchall()
            if results:
                self.suggestions.delete(0, tk.END)
                for (name,) in results:
                    self.suggestions.insert(tk.END, name)
                x = self.prod_entry.winfo_rootx() - self.master.winfo_rootx()
                y = self.prod_entry.winfo_rooty() - self.master.winfo_rooty() + self.prod_entry.winfo_height()
                self.suggestions.place(x=x, y=y, width=self.prod_entry.winfo_width())
                self.suggestions.lift()
                self.listbox_visible = True
                return
        self.suggestions.place_forget()
        self.listbox_visible = False

    def add_product_to_cart(self):
        name = self.prod_entry.get().strip()
        qty_str = self.qty_entry.get().strip()
        print(f"add_product_to_cart called with: {name=}, {qty_str=}")
        if not name or not qty_str.isdigit():
            self.set_status("Enter valid product name and quantity.")
            messagebox.showerror("Invalid Input", "Please enter a valid product name and numeric quantity.")
            print("Invalid input for product add.")
            return
        qty = int(qty_str)
        cursor = self.db.cursor()
        cursor.execute("SELECT stock, min_price, max_price, purchase_price FROM products WHERE name = ?", (name,))
        product = cursor.fetchone()
        if not product:
            print(f"Product '{name}' not found in database, opening AddProductDialog.")
            def after_product_added(product_data):
                print("after_product_added called:", product_data)
                if self.on_add_to_cart:
                    self.on_add_to_cart(product_data)
                self.prod_entry.delete(0, tk.END)
                self.qty_entry.delete(0, tk.END)
                self.set_status(f"{name} added to cart.")
            AddProductDialog(self, self.db, name, qty, after_product_added)
            return

        stock, min_price, max_price, purchase_price = product
        print(f"Product '{name}' found. Stock={stock}, min_price={min_price}, max_price={max_price}, purchase_price={purchase_price}")
        if qty > stock:
            self.set_status(f"Insufficient stock. Only {stock} available.")
            messagebox.showwarning("Low Stock", f"Only {stock} units available for {name}.")
            return
        product_data = {
            "name": name, "qty": qty, "min_price": min_price, "max_price": max_price,
            "purchase_price": purchase_price, "assigned_price": None, "total": None
        }
        if self.on_add_to_cart:
            self.on_add_to_cart(product_data)
        self.prod_entry.delete(0, tk.END)
        self.qty_entry.delete(0, tk.END)
        self.set_status(f"{name} added to cart.")
