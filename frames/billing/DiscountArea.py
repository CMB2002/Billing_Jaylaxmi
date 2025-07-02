import customtkinter as ctk

class DiscountArea(ctk.CTkFrame):
    """
    Discount input area (amount or percent).
    Calls on_discount_change callback with (discount_value, discount_type)
    """
    def __init__(self, master, on_discount_change=None):
        super().__init__(master, fg_color="transparent")
        self.on_discount_change = on_discount_change

        self.discount_val = ctk.StringVar()
        self.discount_type = ctk.StringVar(value="₹")

        ctk.CTkLabel(self, text="Discount:", font=("Segoe UI", 13)).pack(side="left", padx=(0,3))
        discount_entry = ctk.CTkEntry(self, textvariable=self.discount_val, width=70,
                                      placeholder_text="0", font=("Segoe UI", 13), corner_radius=7)
        discount_entry.pack(side="left", padx=1)
        discount_entry.bind("<FocusOut>", self._on_discount_edit)
        discount_entry.bind("<Return>", self._on_discount_edit)

        discount_type_menu = ctk.CTkOptionMenu(self, values=["₹", "%"], variable=self.discount_type,
                                               font=("Segoe UI", 13), width=54)
        discount_type_menu.pack(side="left", padx=1)
        discount_type_menu.configure(command=lambda _: self._on_discount_edit())

        apply_btn = ctk.CTkButton(self, text="Apply Discount", font=("Segoe UI", 13),
                                  fg_color="#324076", hover_color="#7dd3fc", corner_radius=8,
                                  width=124, command=self._on_discount_edit)
        apply_btn.pack(side="left", padx=12)

    def _on_discount_edit(self, event=None):
        """Called whenever discount value/type changes or Apply is pressed."""
        val = self.discount_val.get().strip()
        d_type = self.discount_type.get()
        try:
            discount = float(val) if val else 0.0
        except Exception:
            discount = 0.0
        if self.on_discount_change:
            self.on_discount_change(discount, d_type)

    def get_discount(self):
        """Utility to get current discount and type."""
        try:
            discount = float(self.discount_val.get())
        except Exception:
            discount = 0.0
        return discount, self.discount_type.get()
