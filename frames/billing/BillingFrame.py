import customtkinter as ctk
from .CustomerInputRow import CustomerInputRow
from .ProductInputRow import ProductInputRow
from .CartArea import CartArea
from .DiscountArea import DiscountArea
from .PaymentArea import PaymentArea
from .BillingLogic import calculate_subtotal, apply_discount
from logic.Prices import Calculate_Prices
from ..preview import PreviewWindow
from .add_customer_dialog import AddCustomerDialog

class BillingFrame(ctk.CTkFrame):
    def __init__(self, master, db, refresh_callback=None, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app
        self.refresh_callback = refresh_callback
        self.set_status = set_status or (lambda msg: None)

        self.cart = []
        self.customer = None
        self.discount = 0.0
        self.discount_type = "₹"
        self.total = 0
        self.payment_info = {}
        self.amount_paid = 0.0
        self.amount_owed = 0.0
        self.cart_edit_mode = False

        self.grid_rowconfigure(10, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.reset_btn = ctk.CTkButton(
            self, text="Reset", font=("Segoe UI", 13, "bold"),
            fg_color="#FF6464", text_color="white", corner_radius=8, width=80, height=32,
            command=self.reset_form
        )
        self.reset_btn.grid(row=0, column=0, sticky="e", padx=16, pady=(10, 2))

        self.customer_row = CustomerInputRow(self, db, on_customer_select=self.on_customer_select)
        self.customer_row.grid(row=1, column=0, sticky="ew", padx=20, pady=(2, 2))

        self.product_row = ProductInputRow(self, db, on_add_to_cart=self.on_add_to_cart, set_status=self.set_status)
        self.product_row.grid(row=2, column=0, sticky="ew", padx=20, pady=(1, 2))

        self.cart_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", height=220)
        self.cart_scroll.grid(row=3, column=0, sticky="nsew", padx=20, pady=(1, 2))
        self.cart_area = CartArea(self.cart_scroll, self.cart, on_cart_change=self.on_cart_change, parent_frame=self)
        self.cart_area.pack(fill="both", expand=True)

        self.profit_option = ctk.StringVar(value="A")
        profit_frame = ctk.CTkFrame(self, fg_color="transparent")
        profit_frame.grid(row=4, column=0, sticky="w", padx=22, pady=(4, 2))
        ctk.CTkLabel(profit_frame, text="Profit Option:", font=("Segoe UI", 13)).pack(side="left", padx=(2, 8))
        ctk.CTkOptionMenu(
            profit_frame, variable=self.profit_option, values=["A", "B", "C"], width=68,
            font=("Segoe UI", 13)
        ).pack(side="left", padx=(2, 10))

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=5, column=0, sticky="e", padx=24, pady=(4, 2))

        self.assign_prices_btn = ctk.CTkButton(
            self.btn_frame, text="Assign Prices", font=("Segoe UI", 14, "bold"),
            fg_color="#8be9fd", text_color="#23272f", corner_radius=10, width=150, height=38,
            command=self.assign_prices, state="disabled"
        )
        self.assign_prices_btn.grid(row=0, column=0, padx=6)

        self.edit_prices_btn = ctk.CTkButton(
            self.btn_frame, text="Edit Prices", font=("Segoe UI", 14, "bold"),
            fg_color="#fcbf49", text_color="#23272f", corner_radius=10, width=150, height=38,
            command=self.enable_edit_prices, state="disabled"
        )
        self.edit_prices_btn.grid(row=0, column=1, padx=6)

        self.confirm_edit_btn = ctk.CTkButton(
            self.btn_frame, text="Confirm Edit", font=("Segoe UI", 14, "bold"),
            fg_color="#42d181", text_color="#23272f", corner_radius=10, width=150, height=38,
            command=self.confirm_edit_prices, state="disabled"
        )
        self.confirm_edit_btn.grid(row=0, column=2, padx=6)

        self.discount_area = DiscountArea(self, on_discount_change=self.on_discount_change)
        self.discount_area.grid(row=6, column=0, sticky="ew", padx=20, pady=(2, 2))

        self.payment_area = PaymentArea(self, on_payment_update=self.on_payment_update)
        self.payment_area.grid(row=8, column=0, sticky="ew", padx=20, pady=(1, 2))

        self.total_label = ctk.CTkLabel(self, text="Total: ₹0", font=("Segoe UI", 16, "bold"), text_color="#8be9fd")
        self.total_label.grid(row=7, column=0, sticky="e", padx=20, pady=(1, 2))

        self.bill_btn = ctk.CTkButton(self, text="🧾 Generate Bill", command=self.generate_bill,
                                      font=("Segoe UI", 15, "bold"), fg_color="#324076", hover_color="#7dd3fc",
                                      corner_radius=12, width=170, height=46)
        self.bill_btn.grid(row=10, column=0, sticky="e", padx=20, pady=10)

        self._set_button_states("reset")
        self._update_summary()

    def _set_button_states(self, state):
        cart_has_products = len(self.cart) > 0
        if state == "reset":
            self.assign_prices_btn.configure(state="disabled")
            self.edit_prices_btn.configure(state="disabled")
            self.confirm_edit_btn.configure(state="disabled")
        elif state == "assignable":
            self.assign_prices_btn.configure(state="normal" if cart_has_products else "disabled")
            self.edit_prices_btn.configure(state="disabled")
            self.confirm_edit_btn.configure(state="disabled")
        elif state == "assigned":
            self.assign_prices_btn.configure(state="disabled")
            self.edit_prices_btn.configure(state="normal")
            self.confirm_edit_btn.configure(state="normal")
        elif state == "editing":
            self.assign_prices_btn.configure(state="disabled")
            self.edit_prices_btn.configure(state="disabled")
            self.confirm_edit_btn.configure(state="normal")
        elif state == "edited":
            self.assign_prices_btn.configure(state="disabled")
            self.edit_prices_btn.configure(state="normal")
            self.confirm_edit_btn.configure(state="disabled")

    def on_customer_select(self, customer):
        self.customer = customer
        self.set_status(f"Customer selected: {customer.get('name', '')}")

    def on_add_to_cart(self, product):
        self.cart.append(product)
        self.cart_area.refresh(self.cart)
        self._set_button_states("assignable")
        self._update_summary()
        self.set_status(f"Added to cart: {product.get('name', '')}")

    def on_cart_change(self, cart):
        self.cart = cart
        self.cart_area.refresh(self.cart)
        if len(self.cart) == 0:
            self._set_button_states("reset")
        else:
            self._set_button_states("assignable")
        self._update_summary()
        self.set_status("Cart updated.")
        if len(self.cart) == 0:
            self.reset_form()

    def on_discount_change(self, discount, discount_type):
        self.discount = discount
        self.discount_type = discount_type
        self._update_summary()
        self.set_status(f"Discount applied: {discount}{discount_type}")

    def on_payment_update(self, payment_info):
        self.payment_info = payment_info
        self._update_summary()
        self.set_status("Payment info updated.")

    def assign_prices(self):
        if not self.cart:
            self.set_status("Add products to cart before assigning prices.")
            return
        product_data = [
            (
                item["min_price"],
                item["max_price"],
                item["purchase_price"],
                item["name"],
                item["qty"],
            )
            for item in self.cart
        ]
        profit_option = self.profit_option.get()
        assigned_prices = Calculate_Prices(product_data, profit_option=profit_option)
        for i, price in enumerate(assigned_prices):
            price_float = float(price)
            self.cart[i]["assigned_price"] = price_float
            self.cart[i]["total"] = price_float * self.cart[i]["qty"]

        self.cart_area.set_edit_mode(False)
        self.cart_area.refresh(self.cart)
        self._update_summary()
        self._set_button_states("assigned")
        self.set_status("Prices assigned. Edit or confirm to proceed.")

    def enable_edit_prices(self):
        self.cart_edit_mode = True
        self.cart_area.set_edit_mode(True)
        self.cart_area.refresh(self.cart)
        self._set_button_states("editing")
        self.set_status("Editing prices. Click Confirm after edit.")

    def confirm_edit_prices(self):
        self.cart_edit_mode = False
        for idx, entry in enumerate(self.cart_area.price_entry_widgets):
            if entry is not None:
                try:
                    val = float(entry.get())
                    self.cart[idx]["assigned_price"] = val
                    self.cart[idx]["total"] = val * self.cart[idx]["qty"]
                except Exception:
                    pass
        self.cart_area.set_edit_mode(False)
        self.cart_area.refresh(self.cart)
        self._update_summary()
        self._set_button_states("edited")
        self.set_status("Prices confirmed. Proceed with discount or payment.")

    def _update_summary(self):
        subtotal = calculate_subtotal(self.cart)
        discount_amount, grand_total = apply_discount(subtotal, self.discount, self.discount_type)
        self.total = int(round(grand_total))

        payment_info = self.payment_area.get_payment_info()
        paid_type = payment_info.get("paid_type", "Full")
        cash = float(payment_info.get("cash") or 0)
        upi = float(payment_info.get("upi") or 0)
        card = float(payment_info.get("card") or 0)
        partial = float(payment_info.get("partial_amount") or 0)

        if paid_type == "Full":
            base = self.total
        else:
            base = partial
        due = max(base - (cash + upi + card), 0)
        paid = (cash + upi + card) if paid_type == "Full" else partial
        owed = max(self.total - paid, 0)

        self.amount_paid = paid
        self.amount_owed = owed
        self.total_label.configure(text=f"Total: ₹{self.total}")
        self.payment_area.set_total_due(due, cash, upi, card)

    def get_or_create_customer(self, name, phone, on_success):
        cur = self.db.cursor()
        cur.execute("SELECT id FROM customers WHERE name=? AND phone=?", (name, phone))
        row = cur.fetchone()
        if row:
            on_success(row[0], name, phone)
        else:
            AddCustomerDialog(self, self.db, name, phone, 
                lambda *args, **kwargs: self._safe_on_success(on_success, *args, **kwargs))

    def _safe_on_success(self, on_success, *args, **kwargs):
        try:
            on_success(*args, **kwargs)
        except Exception as e:
            print(f"Exception in after_customer_added: {e}")

    def generate_bill(self):
        # Always pull latest values from customer input fields:
        self.customer = {
            "name": self.customer_row.cust_name_entry.get().strip(),
            "phone": self.customer_row.cust_phone_entry.get().strip()
        }

        if not self.cart or not all(item.get("assigned_price") is not None for item in self.cart):
            self.set_status("Cart incomplete or prices not assigned.")
            return
        if not self.customer or not self.customer.get("name"):
            self.set_status("Enter/select customer name.")
            return

        payment_info = self.payment_area.get_payment_info()
        paid_type = payment_info.get("paid_type", "Full")
        cash = float(payment_info.get("cash") or 0)
        upi = float(payment_info.get("upi") or 0)
        card = float(payment_info.get("card") or 0)
        partial = float(payment_info.get("partial_amount") or 0)
        total = self.total

        if paid_type == "Full":
            if abs((cash + upi + card) - total) > 0.01:
                self.set_status("For full payment, sum of payment methods must match total.")
                return
            paid = cash + upi + card
            owed = max(total - paid, 0)
        else:
            if partial <= 0 or partial >= total:
                self.set_status("Partial amount must be less than total and more than 0.")
                return
            if abs((cash + upi + card) - partial) > 0.01:
                self.set_status("Sum of payment methods must match the partial amount.")
                return
            paid = partial
            owed = max(total - partial, 0)

        payment_methods = {
            "cash": cash, "upi": upi, "card": card
        }

        cart_for_preview = [
            (
                item.get('name', ''),
                item.get('qty', 0),
                item.get('assigned_price', item.get('price', 0)),
                item.get('total', item.get('subtotal', 0))
            )
            for item in self.cart
        ]

        customer_name = self.customer.get("name", "")
        customer_phone = self.customer.get("phone", "")

        def after_customer_added(customer_id, name, phone):
            try:
                preview = PreviewWindow(
                    self,
                    cart=cart_for_preview,
                    total=total,
                    db=self.db,
                    customer_id=customer_id,
                    customer_name=name,
                    customer_phone=phone,
                    discount=self.discount,
                    discount_type=self.discount_type,
                    payment_methods=payment_methods,
                    amount_paid=paid,
                    amount_owed=owed
                )
                preview.wait_window()
                if self.refresh_callback:
                    self.refresh_callback()
                self.reset_form()
                if self.app:
                    from utils.helpers import refresh_all
                    refresh_all(self.app)
                self.set_status("Bill generated and saved.")
            except Exception as e:
                print("ERROR in after_customer_added callback:", e)

        self.get_or_create_customer(customer_name, customer_phone, after_customer_added)

    def reset_form(self):
        self.cart.clear()
        self.cart_area.refresh(self.cart)
        self.cart_area.set_edit_mode(False)
        self.discount_area.discount_val.set("")
        self.discount_area.discount_type.set("₹")
        self.payment_area.payment_amounts["cash"].set("")
        self.payment_area.payment_amounts["upi"].set("")
        self.payment_area.payment_amounts["card"].set("")
        self.payment_area.partial_amount.set("")
        self.payment_area.paid_type.set("Full")
        self.customer_row.cust_name_entry.delete(0, "end")
        self.customer_row.cust_phone_entry.delete(0, "end")
        self._set_button_states("reset")
        self._update_summary()
