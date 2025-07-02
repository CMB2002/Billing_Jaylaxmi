import customtkinter as ctk

class PaymentArea(ctk.CTkFrame):
    def __init__(self, master, on_payment_update=None):
        super().__init__(master, fg_color="transparent")
        self.on_payment_update = on_payment_update

        ctk.CTkLabel(self, text="Paid:", font=("Segoe UI", 13)).pack(side="left")
        self.paid_type = ctk.StringVar(value="Full")
        self.partial_amount = ctk.StringVar()

        ctk.CTkRadioButton(self, text="Full", variable=self.paid_type, value="Full",
                           font=("Segoe UI", 13), command=self._update_payment_type).pack(side="left", padx=2)
        ctk.CTkRadioButton(self, text="Partial", variable=self.paid_type, value="Partial",
                           font=("Segoe UI", 13), command=self._update_payment_type).pack(side="left", padx=2)

        self.partial_entry = ctk.CTkEntry(self, textvariable=self.partial_amount, width=90,
                                          placeholder_text="Partial Amt", font=("Segoe UI", 13), corner_radius=8)
        self.partial_entry.pack(side="left", padx=2)
        self.partial_entry.configure(state="disabled")
        self.partial_entry.bind("<KeyRelease>", self._on_payment_edit)
        self.partial_entry.bind("<FocusOut>", self._on_payment_edit)
        self.partial_entry.bind("<Return>", self._on_payment_edit)

        self.payment_amounts = {
            "cash": ctk.StringVar(),
            "upi": ctk.StringVar(),
            "card": ctk.StringVar()
        }

        for method in ["cash", "upi", "card"]:
            ctk.CTkLabel(self, text=method.capitalize() + ":", font=("Segoe UI", 13)).pack(side="left", padx=(5, 1))
            entry = ctk.CTkEntry(self, textvariable=self.payment_amounts[method],
                                 width=75, placeholder_text="0", font=("Segoe UI", 13), corner_radius=7)
            entry.pack(side="left", padx=(0, 5))
            entry.bind("<KeyRelease>", self._on_payment_edit)

        self.payment_remain_label = ctk.CTkLabel(self, text="Due: ₹0", font=("Segoe UI", 11), text_color="#e56")
        self.payment_remain_label.pack(side="left", padx=10)

    def _update_payment_type(self):
        if self.paid_type.get() == "Partial":
            self.partial_entry.configure(state="normal")
        else:
            self.partial_entry.delete(0, "end")
            self.partial_entry.configure(state="disabled")
        self._on_payment_edit()

    def _on_payment_edit(self, event=None):
        payment_info = {
            "paid_type": self.paid_type.get(),
            "partial_amount": self.partial_amount.get(),
            "cash": self.payment_amounts["cash"].get(),
            "upi": self.payment_amounts["upi"].get(),
            "card": self.payment_amounts["card"].get(),
        }
        if self.on_payment_update:
            self.on_payment_update(payment_info)

    def set_total_due(self, due, *_):
        """Just display the due passed in. BillingFrame is the source of truth."""
        try:
            due = int(round(float(due)))
        except Exception:
            due = 0
        self.payment_remain_label.configure(text=f"Due: ₹{due}")

    def get_payment_info(self):
        return {
            "paid_type": self.paid_type.get(),
            "partial_amount": self.partial_amount.get(),
            "cash": self.payment_amounts["cash"].get(),
            "upi": self.payment_amounts["upi"].get(),
            "card": self.payment_amounts["card"].get(),
        }
