import json
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from frames.preview import PreviewWindow
from utils.helpers import refresh_all
# from logic.Prices import Calculate_Prices  # Will import in assign_prices dynamically

class BillingFrame(ctk.CTkFrame):
    def __init__(self, master, db, refresh_callback=None, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app
        self.cart = []  # list of dicts with name, qty, min_price, max_price, purchase_price, assigned_price, total
        self.total = 0
        self.refresh_callback = refresh_callback
        self.set_status = set_status or (lambda msg: None)

        self.grid_rowconfigure(10, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_customer_row()
        self._build_input_row()
        self._build_cart_area()
        self._build_profit_option()
        self._build_assign_prices_button()
        self._build_discount_area()
        self._build_total_area()
        self._build_paid_section()
        self._build_payment_options()
        self._build_bottom_row()

    def _build_header(self):
        ctk.CTkLabel(
            self,
            text="🧾 Billing & Invoicing",
            font=("Segoe UI", 20, "bold"),
            text_color="#7dd3fc"
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 4))

    def _build_customer_row(self):
        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.grid(row=1, column=0, sticky="ew", padx=20, pady=(2, 2))
        frm.grid_columnconfigure(0, weight=2)
        frm.grid_columnconfigure(1, weight=2)
        frm.grid_columnconfigure(2, weight=1)

        self.cust_name_entry = ctk.CTkEntry(frm, placeholder_text="Customer Name", font=("Segoe UI", 13), corner_radius=8)
        self.cust_name_entry.grid(row=0, column=0, sticky="ew", padx=(0,5))
        self.cust_name_entry.bind("<KeyRelease>", self._on_customer_type)
        self.cust_name_entry.bind("<Down>", self._on_cust_entry_down)
        self.cust_name_entry.bind("<Tab>", lambda e: self.cust_phone_entry.focus_set())

        self.cust_phone_entry = ctk.CTkEntry(frm, placeholder_text="Customer Phone", font=("Segoe UI", 13), corner_radius=8)
        self.cust_phone_entry.grid(row=0, column=1, sticky="ew", padx=(0,5))
        self.cust_phone_entry.bind("<Return>", lambda e: self.prod_entry.focus_set())

        self.cust_suggestion_listbox = tk.Listbox(
            self, height=5,
            font=("Segoe UI", 13),
            activestyle="dotbox",
            selectbackground="#268bd2"
        )
        self.cust_suggestion_listbox.bind("<Return>", self._on_customer_suggest_select)
        self.cust_suggestion_listbox.bind("<Down>", self._on_customer_suggest_down)
        self.cust_suggestion_listbox.bind("<Up>", self._on_customer_suggest_up)

    def _build_input_row(self):
        frm = ctk.CTkFrame(self, fg_color="transparent")
        frm.grid(row=2, column=0, sticky="ew", padx=20, pady=(1, 2))
        frm.grid_columnconfigure(0, weight=3)
        frm.grid_columnconfigure(1, weight=1)
        frm.grid_columnconfigure(2, weight=1)
        frm.grid_columnconfigure(3, weight=1)

        self.prod_entry = ctk.CTkEntry(frm, placeholder_text="Product Name", font=("Segoe UI", 13), corner_radius=8)
        self.prod_entry.grid(row=0, column=0, sticky="ew", padx=(0,5))
        self.prod_entry.bind("<KeyRelease>", self._on_name_type)
        self.prod_entry.bind("<Down>", self._on_entry_down)
        self.prod_entry.bind("<Return>", self._on_entry_return)
        self.prod_entry.bind("<Tab>", lambda e: self.qty_entry.focus_set())

        self.qty_entry = ctk.CTkEntry(frm, placeholder_text="Quantity", font=("Segoe UI", 13), corner_radius=8)
        self.qty_entry.grid(row=0, column=1, padx=5)
        self.qty_entry.bind("<Return>", lambda e: self.add_btn.invoke())
        self.qty_entry.bind("<Tab>", lambda e: self.add_btn.focus_set())

        self.add_btn = ctk.CTkButton(frm, text="➕ Add to Cart", font=("Segoe UI", 13, "bold"),
                                     fg_color="#324076", hover_color="#7dd3fc", corner_radius=10,
                                     command=self.add_to_cart)
        self.add_btn.grid(row=0, column=3, padx=5)
        self.add_btn.bind("<Return>", lambda e: self.add_to_cart())

        self.suggestion_listbox = tk.Listbox(
            self, height=5,
            font=("Segoe UI", 13),
            activestyle="dotbox",
            selectbackground="#268bd2"
        )
        self.suggestion_listbox.bind("<Return>", self._on_suggest_select)
        self.suggestion_listbox.bind("<Tab>", lambda e: self.qty_entry.focus_set())
        self.suggestion_listbox.bind("<Down>", self._on_suggest_down)
        self.suggestion_listbox.bind("<Up>", self._on_suggest_up)

    def _build_cart_area(self):
        self.cart_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.cart_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(1, 2))
        self.refresh_cart()

    def _build_profit_option(self):
        pf = ctk.CTkFrame(self, fg_color="transparent")
        pf.grid(row=4, column=0, sticky="w", padx=22, pady=(4, 2))
        ctk.CTkLabel(pf, text="Profit Option:", font=("Segoe UI", 13)).pack(side="left", padx=(2, 8))
        self.profit_option = ctk.StringVar(value="A")
        ctk.CTkOptionMenu(
            pf, variable=self.profit_option, values=["A", "B", "C"], width=68,
            font=("Segoe UI", 13)
        ).pack(side="left", padx=(2, 10))

    def _build_assign_prices_button(self):
        btn = ctk.CTkButton(self, text="Assign Prices", font=("Segoe UI", 14, "bold"),
                            fg_color="#8be9fd", text_color="#23272f", corner_radius=10, width=180, height=38,
                            command=self.assign_prices)
        btn.grid(row=5, column=0, sticky="e", padx=28, pady=(4, 2))

    def add_to_cart(self):
        name = self.prod_entry.get().strip()
        try:
            qty = int(self.qty_entry.get())
        except ValueError:
            self.set_status("Invalid quantity.")
            return messagebox.showerror("Input Error", "Enter valid quantity.")
        cur = self.db.cursor()
        cur.execute("SELECT stock, min_price, max_price, purchase_price FROM products WHERE name = ?", (name,))
        row = cur.fetchone()
        if not row:
            self.set_status("Product not found.")
            return messagebox.showerror("Product Error", "Product not found.")
        stock, min_price, max_price, purchase_price = row
        if qty > stock:
            from utils.logger import log
            log.warning(f"Low stock for product: {name} (requested {qty}, available {stock})")
            self.set_status("Stock too low!")
            return messagebox.showwarning("Stock Error", f"Only {stock} in stock.")

        self.cart.append({
            "name": name,
            "qty": qty,
            "min_price": min_price,
            "max_price": max_price,
            "purchase_price": purchase_price,
            "assigned_price": None,
            "total": None
        })
        cur.execute("UPDATE products SET stock = stock - ? WHERE name = ?", (qty, name))
        self.db.commit()
        self.set_status(f"{name} added to cart.")
        self.refresh_cart()
        self.prod_entry.delete(0, "end")
        self.qty_entry.delete(0, "end")

    def refresh_cart(self):
        for w in self.cart_frame.winfo_children():
            w.destroy()
        for i, item in enumerate(self.cart):
            text = f"{item['name']} x{item['qty']}"
            if item["assigned_price"] is not None:
                text += f" @ ₹{item['assigned_price']:.2f} = ₹{item['total']:.2f}"
            ctk.CTkLabel(self.cart_frame, text=text, anchor="w", font=("Segoe UI", 13)).pack(side="top", fill="x", padx=3, pady=2)




    def assign_prices(self):
        if not self.cart:
            return messagebox.showwarning("Cart Empty", "Add products to cart before assigning prices.")

        try:
            from logic.Prices import Calculate_Prices
        except ImportError:
            return messagebox.showerror("Not Implemented", "The Prices.py/Calculate_Prices logic is missing.")

        product_data = []
        for item in self.cart:
            product_data.append((
                item["min_price"],
                item["max_price"],
                item["purchase_price"],
                item["name"],
                item["qty"],
            ))

        profit_option = self.profit_option.get() if hasattr(self, 'profit_option') else 'A'
        assigned_prices = Calculate_Prices(product_data, profit_option=profit_option)

        for i, price in enumerate(assigned_prices):
            self.cart[i]["assigned_price"] = price
            self.cart[i]["total"] = price * self.cart[i]["qty"]

        self.refresh_cart()
        self.set_status("Prices assigned. You can now edit prices in cart if needed.")
        self._add_editable_cart_entries()

    def _add_editable_cart_entries(self):
        for w in self.cart_frame.winfo_children():
            w.destroy()
        for i, item in enumerate(self.cart):
            row = ctk.CTkFrame(self.cart_frame, fg_color="transparent")
            row.pack(fill="x", padx=3, pady=2)
            ctk.CTkLabel(row, text=f"{item['name']} x{item['qty']}", font=("Segoe UI", 13), anchor="w")\
                .pack(side="left", padx=(2, 12))

            if item["assigned_price"] is not None:
                var = ctk.StringVar(value=str(item["assigned_price"]))
                def make_callback(idx=i, var=var):
                    def callback(*_):
                        try:
                            val = float(var.get())
                            if val < self.cart[idx]['purchase_price']:
                                self.set_status("Warning: Price below purchase price!")
                                messagebox.showwarning("Low Price", "Assigned price is below purchase price!")
                            self.cart[idx]['assigned_price'] = val
                            self.cart[idx]['total'] = val * self.cart[idx]['qty']
                            self._update_summary()
                        except Exception:
                            pass
                    return callback
                entry = ctk.CTkEntry(row, textvariable=var, width=70, font=("Segoe UI", 13), corner_radius=7)
                entry.pack(side="left", padx=(0, 6))
                entry.bind("<FocusOut>", make_callback())
                entry.bind("<Return>", make_callback())
                ctk.CTkLabel(row, text=f"= ₹{item['total']:.2f}", font=("Segoe UI", 13)).pack(side="left", padx=(0, 6))

    def _build_discount_area(self):
        discount_row = ctk.CTkFrame(self, fg_color="transparent")
        discount_row.grid(row=6, column=0, sticky="ew", padx=20, pady=(2, 2))
        ctk.CTkLabel(discount_row, text="Discount:", font=("Segoe UI", 13)).pack(side="left", padx=(0,3))
        self.discount_val = ctk.StringVar()
        self.discount_type = ctk.StringVar(value="₹")
        discount_entry = ctk.CTkEntry(discount_row, textvariable=self.discount_val, width=70,
                                      placeholder_text="0", font=("Segoe UI", 13), corner_radius=7)
        discount_entry.pack(side="left", padx=1)
        discount_type_menu = ctk.CTkOptionMenu(discount_row, values=["₹", "%"], variable=self.discount_type,
                                               font=("Segoe UI", 13), width=54)
        discount_type_menu.pack(side="left", padx=1)
        apply_btn = ctk.CTkButton(discount_row, text="Apply Discount", font=("Segoe UI", 13),
                                  fg_color="#324076", hover_color="#7dd3fc", corner_radius=8,
                                  width=124, command=self._apply_discount)
        apply_btn.pack(side="left", padx=12)

    def _build_total_area(self):
        total_row = ctk.CTkFrame(self, fg_color="transparent")
        total_row.grid(row=7, column=0, sticky="ew", padx=20, pady=(1, 2))
        self.total_label = ctk.CTkLabel(total_row, text="Total: ₹0", font=("Segoe UI", 16, "bold"), text_color="#8be9fd")
        self.total_label.pack(side="right", padx=(0, 18))

    def _apply_discount(self):
        self._update_summary()

    def _update_summary(self):
        subtotal = sum(item["total"] or 0 for item in self.cart if item.get("total") is not None)
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
            except Exception:
                discount = 0.0
        grand_total = max(subtotal - discount, 0.0)
        rounded_total = round(grand_total)
        self.total_label.configure(text=f"Total: ₹{rounded_total}")


    def _build_paid_section(self):
        pf = ctk.CTkFrame(self, fg_color="transparent")
        pf.grid(row=8, column=0, sticky="ew", padx=20, pady=(1, 2))
        ctk.CTkLabel(pf, text="Paid:", font=("Segoe UI", 13)).pack(side="left")
        self.paid_type = ctk.StringVar(value="Full")
        self.partial_amount = ctk.StringVar()
        ctk.CTkRadioButton(
            pf, text="Full", variable=self.paid_type, value="Full",
            font=("Segoe UI", 13), command=self._update_partial_entry
        ).pack(side="left", padx=2)
        ctk.CTkRadioButton(
            pf, text="Partial", variable=self.paid_type, value="Partial",
            font=("Segoe UI", 13), command=self._update_partial_entry
        ).pack(side="left", padx=2)
        self.partial_entry = ctk.CTkEntry(
            pf, textvariable=self.partial_amount, width=90,
            placeholder_text="Amount Paid", font=("Segoe UI", 13), corner_radius=8
        )
        self.partial_entry.pack(side="left", padx=2)
        self.partial_entry.configure(state="disabled")

    def _build_payment_options(self):
        pm_frame = ctk.CTkFrame(self, fg_color="transparent")
        pm_frame.grid(row=9, column=0, sticky="ew", padx=20, pady=(1, 2))
        ctk.CTkLabel(pm_frame, text="Payment:", font=("Segoe UI", 13)).pack(side="left", padx=(0,8))

        self.payment_amounts = {
            "cash": ctk.StringVar(),
            "upi": ctk.StringVar(),
            "card": ctk.StringVar()
        }
        self.payment_entries = {}
        for method in ["cash", "upi", "card"]:
            ctk.CTkLabel(pm_frame, text=method.capitalize()+":", font=("Segoe UI", 13)).pack(side="left", padx=(5,1))
            entry = ctk.CTkEntry(pm_frame, textvariable=self.payment_amounts[method],
                                 width=75, placeholder_text="0", font=("Segoe UI", 13), corner_radius=7)
            entry.pack(side="left", padx=(0,5))
            entry.bind("<KeyRelease>", lambda e: self._update_payment_remain())
            self.payment_entries[method] = entry

        self.payment_remain_label = ctk.CTkLabel(pm_frame, text="", font=("Segoe UI", 11), text_color="#e56")
        self.payment_remain_label.pack(side="left", padx=10)
        self._update_payment_remain()

    def _update_partial_entry(self):
        if self.paid_type.get() == "Partial":
            self.partial_entry.configure(state="normal")
        else:
            self.partial_entry.delete(0, "end")
            self.partial_entry.configure(state="disabled")
        self._update_payment_remain()

    def _update_payment_remain(self):
        subtotal = sum(item["total"] or 0 for item in self.cart if item.get("total") is not None)
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
            except Exception:
                discount = 0.0
        grand_total = max(subtotal - discount, 0.0)
        rounded_total = round(grand_total)

        paid_type = self.paid_type.get()
        if paid_type == "Full":
            amount_paid = rounded_total
        else:
            try:
                amount_paid = float(self.partial_amount.get())
            except Exception:
                amount_paid = 0.0

        paid_sum = 0.0
        for m in self.payment_amounts:
            try:
                paid_sum += float(self.payment_amounts[m].get())
            except Exception:
                pass
        remain = max(0, amount_paid - paid_sum)
        if remain > 0.01:
            self.payment_remain_label.configure(text=f"Remaining to allocate: ₹{remain:.2f}")
        elif remain < -0.01:
            self.payment_remain_label.configure(text=f"Overpaid by: ₹{-remain:.2f}")
        else:
            self.payment_remain_label.configure(text="")

    def _build_bottom_row(self):
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=10, column=0, sticky="ew", padx=20, pady=10)
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        self.bill_btn = ctk.CTkButton(bottom, text="🧾 Generate Bill", command=self.generate_bill, font=("Segoe UI", 15, "bold"),
                                      fg_color="#324076", hover_color="#7dd3fc", corner_radius=12,
                                      width=170, height=46)
        self.bill_btn.grid(row=0, column=1, sticky="e")
        self.bill_btn.bind("<Return>", lambda e: self.generate_bill())

    def generate_bill(self):
        if not self.cart or not all(item.get("assigned_price") is not None for item in self.cart):
            self.set_status("Cart incomplete.")
            return messagebox.showwarning("Cart Error", "Add products and assign prices before generating bill.")
        cust_name = self.cust_name_entry.get().strip()
        cust_phone = self.cust_phone_entry.get().strip()
        if not cust_name:
            return messagebox.showerror("Customer Info", "Enter customer name.")
        cur = self.db.cursor()
        cur.execute("SELECT id FROM customers WHERE name=? AND phone=?", (cust_name, cust_phone))
        row = cur.fetchone()
        if row:
            cust_id = row[0]
        else:
            cur.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (cust_name, cust_phone))
            self.db.commit()
            cust_id = cur.lastrowid

        subtotal = sum(item["total"] or 0 for item in self.cart)
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
        rounded_total = round(grand_total)

        paid_type = self.paid_type.get()
        if paid_type == "Full":
            amount_paid = rounded_total
        else:
            try:
                amount_paid = float(self.partial_amount.get())
            except ValueError:
                return messagebox.showerror("Payment Error", "Enter valid amount paid.")
            if amount_paid > rounded_total:
                return messagebox.showerror("Payment Error", "Paid amount can't exceed total.")

        pm_amounts = {}
        paid_sum = 0.0
        for method in ["cash", "upi", "card"]:
            val = self.payment_amounts[method].get()
            try:
                amt = float(val) if val else 0.0
                if amt > 0:
                    pm_amounts[method] = amt
                paid_sum += amt
            except Exception:
                if val:
                    return messagebox.showerror("Payment Error", f"Enter valid amount for {method.capitalize()}")
        if paid_sum == 0:
            return messagebox.showerror("Payment Error", "Enter payment amount(s).")
        if abs(paid_sum - amount_paid) > 0.01:
            return messagebox.showerror("Payment Error", "Sum of payment methods must equal amount paid.")

        amount_owed = rounded_total - amount_paid

        def _after_print_save():
            self.cart.clear()
            self.total = 0
            self.refresh_cart()
            self.cust_name_entry.delete(0, "end")
            self.cust_phone_entry.delete(0, "end")
            for m in self.payment_amounts:
                self.payment_amounts[m].set("")
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
            total=rounded_total,
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

    # ----------- CUSTOMER SUGGESTION HANDLERS -----------
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
            if "(" in val and val.endswith(")"):
                name, phone = val.rsplit("(", 1)
                self.cust_name_entry.delete(0, tk.END)
                self.cust_name_entry.insert(0, name.strip())
                self.cust_phone_entry.delete(0, tk.END)
                self.cust_phone_entry.insert(0, phone[:-1].strip())
            self.cust_suggestion_listbox.place_forget()
            self.cust_phone_entry.focus_set()

    # ----------- PRODUCT SUGGESTION HANDLERS -----------
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
        results = cur.fetchall()
        if results:
            self.suggestion_listbox.delete(0, tk.END)
            for (name,) in results:
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
