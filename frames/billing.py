import json
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from frames.preview import PreviewWindow  # Import from frames directory

class BillingFrame(ctk.CTkFrame):
    def __init__(self, master, db, refresh_callback=None, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app
        self.cart = []
        self.total = 0
        self.refresh_callback = refresh_callback
        self.set_status = set_status or (lambda msg: None)

        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_customer_row()
        self._build_input_row()
        self._build_cart_area()
        self._build_payment_options()
        self._build_bottom_row()
        self._build_customer_search_handlers()

    # --- Customer selection and search ---
    def _build_customer_row(self):
        frm = ctk.CTkFrame(self)
        frm.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 1))
        frm.grid_columnconfigure(0, weight=2)
        frm.grid_columnconfigure(1, weight=2)
        frm.grid_columnconfigure(2, weight=1)
        self.cust_name_entry = ctk.CTkEntry(frm, placeholder_text="Customer Name")
        self.cust_name_entry.grid(row=0, column=0, sticky="ew", padx=(0,5))
        self.cust_name_entry.bind("<KeyRelease>", self._on_customer_type)
        self.cust_name_entry.bind("<Down>", self._on_cust_entry_down)
        self.cust_name_entry.bind("<Tab>", lambda e: self.cust_phone_entry.focus_set())
        self.cust_phone_entry = ctk.CTkEntry(frm, placeholder_text="Customer Phone")
        self.cust_phone_entry.grid(row=0, column=1, sticky="ew", padx=(0,5))
        self.cust_phone_entry.bind("<Return>", lambda e: self.prod_entry.focus_set())

        # Suggestion Listbox for customer
        self.cust_suggestion_listbox = tk.Listbox(
            self, height=5,
            font=("Helvetica", 14),
            activestyle="dotbox",
            selectbackground="#268bd2"
        )
        self.cust_suggestion_listbox.bind("<Return>", self._on_customer_suggest_select)
        self.cust_suggestion_listbox.bind("<Down>", self._on_customer_suggest_down)
        self.cust_suggestion_listbox.bind("<Up>", self._on_customer_suggest_up)

    def _build_customer_search_handlers(self):
        pass

    def _on_customer_type(self, event):
        term = self.cust_name_entry.get().strip()
        if not term:
            self.cust_suggestion_listbox.place_forget()
            return
        cur = self.db.cursor()
        cur.execute("SELECT name, phone FROM customers WHERE name LIKE ? COLLATE NOCASE LIMIT 5", (f"%{term}%",))
        results = cur.fetchall()
        if results:
            self.cust_suggestion_listbox.delete(0, tk.END)
            for name, phone in results:
                self.cust_suggestion_listbox.insert(tk.END, f"{name} ({phone})")
            x = self.cust_name_entry.winfo_rootx() - self.winfo_rootx()
            y = self.cust_name_entry.winfo_rooty() - self.winfo_rooty() + self.cust_name_entry.winfo_height()
            self.cust_suggestion_listbox.place(
                x=x, y=y,
                width=self.cust_name_entry.winfo_width()
            )
            self.cust_suggestion_listbox.lift()
        else:
            self.cust_suggestion_listbox.place_forget()

    def _on_cust_entry_down(self, event):
        if self.cust_suggestion_listbox.size() > 0:
            self.cust_suggestion_listbox.focus_set()
            self.cust_suggestion_listbox.selection_clear(0, tk.END)
            self.cust_suggestion_listbox.selection_set(0)
            self.cust_suggestion_listbox.activate(0)

    def _on_customer_suggest_down(self, event):
        lb = self.cust_suggestion_listbox
        size = lb.size()
        if size == 0: return
        cur = lb.curselection()
        idx = (cur[0]+1) if cur else 0
        if idx >= size: idx = 0
        lb.selection_clear(0, tk.END)
        lb.select_set(idx)
        lb.activate(idx)

    def _on_customer_suggest_up(self, event):
        lb = self.cust_suggestion_listbox
        size = lb.size()
        if size == 0: return
        cur = lb.curselection()
        idx = (cur[0]-1) if cur else size-1
        lb.selection_clear(0, tk.END)
        lb.select_set(idx)
        lb.activate(idx)

    def _on_customer_suggest_select(self, event):
        lb = self.cust_suggestion_listbox
        sel = lb.curselection()
        if sel:
            val = lb.get(sel[0])
            # Parse out name and phone
            if "(" in val and val.endswith(")"):
                name, phone = val.rsplit("(", 1)
                self.cust_name_entry.delete(0, tk.END)
                self.cust_name_entry.insert(0, name.strip())
                self.cust_phone_entry.delete(0, tk.END)
                self.cust_phone_entry.insert(0, phone[:-1].strip())
            self.cust_suggestion_listbox.place_forget()
            self.cust_phone_entry.focus_set()

    # --- Product entry & suggestions ---
    def _build_input_row(self):
        frm = ctk.CTkFrame(self)
        frm.grid(row=1, column=0, sticky="ew", padx=20, pady=(1, 1))
        frm.grid_columnconfigure(0, weight=3)
        frm.grid_columnconfigure(1, weight=1)
        frm.grid_columnconfigure(2, weight=1)
        self.prod_entry = ctk.CTkEntry(frm, placeholder_text="Product Name")
        self.prod_entry.grid(row=0, column=0, sticky="ew", padx=(0,5))
        self.prod_entry.bind("<KeyRelease>", self._on_name_type)
        self.prod_entry.bind("<Down>", self._on_entry_down)
        self.prod_entry.bind("<Return>", self._on_entry_return)
        self.prod_entry.bind("<Tab>", lambda e: self.qty_entry.focus_set())
        self.suggestion_listbox = tk.Listbox(
            self, height=5,
            font=("Helvetica", 14),
            activestyle="dotbox",
            selectbackground="#268bd2"
        )
        self.suggestion_listbox.bind("<Return>", self._on_suggest_select)
        self.suggestion_listbox.bind("<Tab>", lambda e: self.qty_entry.focus_set())
        self.suggestion_listbox.bind("<Down>", self._on_suggest_down)
        self.suggestion_listbox.bind("<Up>", self._on_suggest_up)
        self.qty_entry = ctk.CTkEntry(frm, placeholder_text="Quantity")
        self.qty_entry.grid(row=0, column=1, padx=5)
        self.qty_entry.bind("<Return>", lambda e: self.add_btn.invoke())
        self.qty_entry.bind("<Tab>", lambda e: self.add_btn.focus_set())
        self.add_btn = ctk.CTkButton(frm, text="Add to Cart", command=self.add_to_cart)
        self.add_btn.grid(row=0, column=2, padx=5)
        self.add_btn.bind("<Return>", lambda e: self.add_to_cart())
        self.add_btn.bind("<Tab>", lambda e: self.bill_btn.focus_set())

    def _on_name_type(self, event):
        term = self.prod_entry.get().strip()
        if not term:
            self.suggestion_listbox.place_forget()
            return
        cur = self.db.cursor()
        cur.execute(
            "SELECT name FROM products WHERE name LIKE ? COLLATE NOCASE LIMIT 5",
            (f"%{term}%",)
        )
        results = [r[0] for r in cur.fetchall()]
        if results:
            self.suggestion_listbox.delete(0, tk.END)
            for name in results:
                self.suggestion_listbox.insert(tk.END, name)
            x = self.prod_entry.winfo_rootx() - self.winfo_rootx()
            y = self.prod_entry.winfo_rooty() - self.winfo_rooty() + self.prod_entry.winfo_height()
            self.suggestion_listbox.place(
                x=x, y=y,
                width=self.prod_entry.winfo_width()
            )
            self.suggestion_listbox.lift()
        else:
            self.suggestion_listbox.place_forget()

    def _on_entry_down(self, event):
        if self.suggestion_listbox.size() > 0:
            self.suggestion_listbox.focus_set()
            self.suggestion_listbox.selection_clear(0, tk.END)
            self.suggestion_listbox.selection_set(0)
            self.suggestion_listbox.activate(0)

    def _on_entry_return(self, event):
        if self.suggestion_listbox.size() > 0:
            self.suggestion_listbox.focus_set()
            self.suggestion_listbox.selection_clear(0, tk.END)
            self.suggestion_listbox.selection_set(0)
            self.suggestion_listbox.activate(0)
        else:
            self.qty_entry.focus_set()

    def _on_suggest_down(self, event):
        lb = self.suggestion_listbox
        size = lb.size()
        if size == 0: return
        cur = lb.curselection()
        idx = (cur[0]+1) if cur else 0
        if idx >= size: idx = 0
        lb.selection_clear(0, tk.END)
        lb.select_set(idx)
        lb.activate(idx)

    def _on_suggest_up(self, event):
        lb = self.suggestion_listbox
        size = lb.size()
        if size == 0: return
        cur = lb.curselection()
        idx = (cur[0]-1) if cur else size-1
        lb.selection_clear(0, tk.END)
        lb.select_set(idx)
        lb.activate(idx)

    def _on_suggest_select(self, event):
        lb = self.suggestion_listbox
        sel = lb.curselection()
        if sel:
            val = lb.get(sel[0])
            self.prod_entry.delete(0, tk.END)
            self.prod_entry.insert(0, val)
        self.suggestion_listbox.place_forget()
        self.qty_entry.focus_set()

    # --- Cart operations ---
    def _build_cart_area(self):
        self.cart_frame = ctk.CTkScrollableFrame(self)
        self.cart_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(1, 1))

    def add_to_cart(self):
        name = self.prod_entry.get().strip()
        try:
            qty = int(self.qty_entry.get())
        except ValueError:
            self.set_status("Invalid quantity.")
            return messagebox.showerror("Input Error", "Enter a valid quantity.")
        cur = self.db.cursor()
        cur.execute("SELECT price, stock FROM products WHERE name = ?", (name,))
        row = cur.fetchone()
        if not row:
            self.set_status("Product not found.")
            return messagebox.showerror("Product Error", "Product not found.")
        price, stock = row
        if qty > stock:
            from utils.logger import log
            log.warning(f"Low stock for product: {name} (requested {qty}, available {stock})")
            self.set_status("Stock too low!")
            return messagebox.showwarning("Stock Error", f"Only {stock} in stock.")
        total_price = qty * price
        self.cart.append((name, qty, price, total_price))
        self.total += total_price
        cur.execute("UPDATE products SET stock = stock - ? WHERE name = ?", (qty, name))
        self.db.commit()
        self.set_status(f"{name} added to cart.")
        self.refresh_cart()
        self.prod_entry.delete(0, "end")
        self.qty_entry.delete(0, "end")

    def remove_from_cart(self, idx):
        name, qty, price, total = self.cart[idx]
        cur = self.db.cursor()
        cur.execute("UPDATE products SET stock = stock + ? WHERE name = ?", (qty, name))
        self.db.commit()
        self.total -= total
        del self.cart[idx]
        self.set_status(f"{name} removed from cart.")
        self.refresh_cart()

    def refresh_cart(self):
        for w in self.cart_frame.winfo_children():
            w.destroy()
        for i, (n, q, p, t) in enumerate(self.cart):
            row = ctk.CTkFrame(self.cart_frame)
            row.pack(fill="x", padx=5, pady=2)
            ctk.CTkLabel(row, text=f"{n} x{q} @ ₹{p:.2f} = ₹{t:.2f}", anchor="w")\
               .pack(side="left", expand=True)
            ctk.CTkButton(row, text="Remove", width=80, fg_color="tomato",
                          command=lambda i=i: self.remove_from_cart(i)).pack(side="right", padx=5)
        self._update_summary()

    # --- New: Payment and Discount section ---
    def _build_payment_options(self):
        # Payment methods
        self.payment_methods = {"cash": ctk.BooleanVar(), "upi": ctk.BooleanVar(), "card": ctk.BooleanVar()}
        self.payment_amounts = {"cash": ctk.StringVar(), "upi": ctk.StringVar(), "card": ctk.StringVar()}
        pm_frame = ctk.CTkFrame(self)
        pm_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(1, 1))
        ctk.CTkLabel(pm_frame, text="Payment:").pack(side="left", padx=(0,8))
        for method in self.payment_methods:
            ctk.CTkCheckBox(pm_frame, text=method.capitalize(), variable=self.payment_methods[method]).pack(side="left", padx=3)
            ctk.CTkEntry(pm_frame, textvariable=self.payment_amounts[method], width=70, placeholder_text="₹").pack(side="left", padx=1)
        # Discount
        self.discount_val = ctk.StringVar()
        self.discount_type = ctk.StringVar(value="₹")
        df = ctk.CTkFrame(self)
        df.grid(row=4, column=0, sticky="ew", padx=20, pady=(1, 1))
        ctk.CTkLabel(df, text="Discount:").pack(side="left", padx=(0,3))
        ctk.CTkEntry(df, textvariable=self.discount_val, width=70, placeholder_text="0").pack(side="left", padx=1)
        ctk.CTkOptionMenu(df, values=["₹", "%"], variable=self.discount_type).pack(side="left", padx=1)
        # Paid/Partial
        self.paid_type = ctk.StringVar(value="Full")
        self.partial_amount = ctk.StringVar()
        pf = ctk.CTkFrame(self)
        pf.grid(row=5, column=0, sticky="ew", padx=20, pady=(1, 2))
        ctk.CTkLabel(pf, text="Paid:").pack(side="left")
        ctk.CTkRadioButton(pf, text="Full", variable=self.paid_type, value="Full", command=self._update_partial_entry).pack(side="left", padx=2)
        ctk.CTkRadioButton(pf, text="Partial", variable=self.paid_type, value="Partial", command=self._update_partial_entry).pack(side="left", padx=2)
        self.partial_entry = ctk.CTkEntry(pf, textvariable=self.partial_amount, width=90, placeholder_text="Amount Paid")
        self.partial_entry.pack(side="left", padx=2)
        self.partial_entry.configure(state="disabled")

    def _update_partial_entry(self):
        if self.paid_type.get() == "Partial":
            self.partial_entry.configure(state="normal")
        else:
            self.partial_entry.delete(0, "end")
            self.partial_entry.configure(state="disabled")

    def _update_summary(self):
        # Recalculate summary after cart/payment/discount changes (for UI updates if needed)
        pass  # Add total/discount/paid/owed display if desired

    # --- Bottom row and bill generation ---
    def _build_bottom_row(self):
        bottom = ctk.CTkFrame(self)
        bottom.grid(row=6, column=0, sticky="ew", padx=20, pady=10)
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        self.total_label = ctk.CTkLabel(bottom, text="Total: ₹0.00", font=("Arial", 16))
        self.total_label.grid(row=0, column=0, sticky="w")
        self.bill_btn = ctk.CTkButton(bottom, text="Generate Bill", command=self.generate_bill)
        self.bill_btn.grid(row=0, column=1, sticky="e")
        self.bill_btn.bind("<Return>", lambda e: self.generate_bill())

    def generate_bill(self):
        if not self.cart:
            self.set_status("Cart empty.")
            return messagebox.showwarning("Cart Empty", "Add items before generating.")
        cust_name = self.cust_name_entry.get().strip()
        cust_phone = self.cust_phone_entry.get().strip()
        if not cust_name:
            return messagebox.showerror("Customer Info", "Enter customer name.")
        cur = self.db.cursor()
        # Ensure customer exists
        cur.execute("SELECT id FROM customers WHERE name=? AND phone=?", (cust_name, cust_phone))
        row = cur.fetchone()
        if row:
            cust_id = row[0]
        else:
            cur.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (cust_name, cust_phone))
            self.db.commit()
            cust_id = cur.lastrowid

        # Discount calculation
        subtotal = sum(item[3] for item in self.cart)
        discount_val = self.discount_val.get().strip()
        discount_type = self.discount_type.get()
        discount = 0.0
        if discount_val:
            try:
                dval = float(discount_val)
                if discount_type == "%":
                    discount = subtotal * dval / 100.0
                else:
                    discount = dval
            except ValueError:
                return messagebox.showerror("Discount Error", "Enter valid discount amount or %.")
        grand_total = max(subtotal - discount, 0.0)

        # Payment method splitting
        pm_selected = {k: v.get() for k, v in self.payment_methods.items()}
        pm_amounts = {}
        paid_sum = 0.0
        for method, selected in pm_selected.items():
            if selected:
                try:
                    amt = float(self.payment_amounts[method].get() or 0)
                    pm_amounts[method] = amt
                    paid_sum += amt
                except ValueError:
                    return messagebox.showerror("Payment Error", f"Enter amount for {method.capitalize()}")
        if not any(pm_selected.values()):
            return messagebox.showerror("Payment Error", "Select at least one payment method.")
        # Paid/partial logic
        paid_type = self.paid_type.get()
        amount_paid = 0.0
        amount_owed = 0.0
        if paid_type == "Full":
            amount_paid = grand_total
        else:
            try:
                amount_paid = float(self.partial_amount.get())
            except ValueError:
                return messagebox.showerror("Payment Error", "Enter valid amount paid.")
            if amount_paid > grand_total:
                return messagebox.showerror("Payment Error", "Paid amount can't exceed grand total.")
            amount_owed = grand_total - amount_paid
        # Validate split matches paid
        if abs(paid_sum - amount_paid) > 0.01:
            return messagebox.showerror("Payment Error", "Sum of payment methods must equal amount paid.")

        # Pass all info to PreviewWindow
        def _after_print_save():
            self.cart.clear()
            self.total = 0
            self.refresh_cart()
            self.cust_name_entry.delete(0, "end")
            self.cust_phone_entry.delete(0, "end")
            for m in self.payment_amounts:
                self.payment_amounts[m].set("")
                self.payment_methods[m].set(False)
            self.discount_val.set("")
            self.paid_type.set("Full")
            self.partial_amount.set("")
            self.set_status("Invoice saved.")
            if self.refresh_callback:
                self.refresh_callback()
            if self.app:
                refresh_all(self.app)

        def _alter():
            self.set_status("Returned for alteration.")

        PreviewWindow(
            parent=self,
            cart=self.cart,
            total=grand_total,
            db=self.db,
            on_alter=_alter,
            on_finish=_after_print_save,
            customer_id=cust_id,
            customer_name=cust_name,
            customer_phone=cust_phone,
            discount=discount,
            discount_type=discount_type,
            payment_methods=pm_amounts,
            amount_paid=amount_paid,
            amount_owed=amount_owed
        )
        self.set_status("Invoice preview opened.")

    def _on_invoice_complete(self):
        self.cart.clear()
        self.total = 0
        self.refresh_cart()
        self.cust_name_entry.delete(0, "end")
        self.cust_phone_entry.delete(0, "end")
        for m in self.payment_amounts:
            self.payment_amounts[m].set("")
            self.payment_methods[m].set(False)
        self.discount_val.set("")
        self.paid_type.set("Full")
        self.partial_amount.set("")
        if self.refresh_callback:
            self.refresh_callback()
        if self.app:
            refresh_all(self.app)
        self.set_status("Bill generated and cart cleared.")
