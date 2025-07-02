import customtkinter as ctk

class CartArea(ctk.CTkFrame):
    def __init__(self, master, cart, on_cart_change=None, parent_frame=None):
        super().__init__(master, fg_color="transparent")
        self.cart = cart
        self.on_cart_change = on_cart_change
        self.parent_frame = parent_frame
        self.cart_widgets = []
        self.price_entry_widgets = []
        self.edit_mode = False
        self.render_cart()

    def set_edit_mode(self, mode):
        self.edit_mode = mode
        self.refresh(self.cart)

    def refresh(self, cart=None):
        if cart is not None:
            self.cart = cart
        for widget in self.cart_widgets:
            widget.destroy()
        self.cart_widgets = []
        self.price_entry_widgets = []
        self.render_cart()

    def render_cart(self):
        if not self.cart:
            dummy_row = ctk.CTkFrame(self, fg_color="transparent", height=32)
            dummy_row.pack(fill="x", padx=3, pady=4)
            self.cart_widgets.append(dummy_row)
            return

        for idx, item in enumerate(self.cart):
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=3, pady=2)
            self.cart_widgets.append(row)

            label_text = f"{item.get('name', '')} x{item.get('qty', 0)}"
            ctk.CTkLabel(row, text=label_text, font=("Segoe UI", 13), anchor="w")\
                .pack(side="left", padx=(2, 12))

            # Show/edit price as integer rupees always
            if item.get("assigned_price") is not None:
                if self.edit_mode:
                    var = ctk.StringVar(value=str(int(item["assigned_price"])))
                    entry = ctk.CTkEntry(row, textvariable=var, width=64, font=("Segoe UI", 13), corner_radius=7)
                    entry.pack(side="left", padx=(0, 6))
                    self.price_entry_widgets.append(entry)
                    ctk.CTkLabel(
                        row,
                        text=f"= ₹{int(item['qty']) * int(item['assigned_price'])}",
                        font=("Segoe UI", 13)
                    ).pack(side="left", padx=(0, 6))
                else:
                    ctk.CTkLabel(
                        row,
                        text=f"@ ₹{int(item['assigned_price'])} = ₹{int(item['total'])}",
                        font=("Segoe UI", 13)
                    ).pack(side="left", padx=(0, 6))
                    self.price_entry_widgets.append(None)
            else:
                self.price_entry_widgets.append(None)

            def remove_item(idx=idx):
                if 0 <= idx < len(self.cart):
                    self.cart.pop(idx)
                    if self.on_cart_change:
                        self.on_cart_change(self.cart)
                    if len(self.cart) == 0 and self.parent_frame and hasattr(self.parent_frame, "reset_form"):
                        self.parent_frame.reset_form()
                    self.refresh()
            ctk.CTkButton(row, text="🗑️", width=28, height=28, font=("Segoe UI", 13),
                          fg_color="#e56", hover_color="#ffb0b0", corner_radius=8,
                          command=remove_item).pack(side="right", padx=3)
