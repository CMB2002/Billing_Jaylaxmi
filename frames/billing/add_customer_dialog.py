import customtkinter as ctk
from tkinter import messagebox

class AddCustomerDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, name, phone, on_success):
        super().__init__(parent)
        self.title("Add New Customer")
        self.geometry("440x360")  # Increased height

        self.db = db
        self.on_success = on_success

        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)

        ctk.CTkLabel(self, text="Add New Customer", font=("Segoe UI", 15, "bold")).pack(pady=(24, 14))

        ctk.CTkLabel(self, text="Name:", font=("Segoe UI", 13)).pack(anchor="w", padx=36)
        self.name_var = ctk.StringVar(value=name)
        name_entry = ctk.CTkEntry(self, textvariable=self.name_var, font=("Segoe UI", 13))
        name_entry.pack(fill="x", padx=36, pady=(0, 14))

        ctk.CTkLabel(self, text="Phone:", font=("Segoe UI", 13)).pack(anchor="w", padx=36)
        self.phone_var = ctk.StringVar(value=phone)
        phone_entry = ctk.CTkEntry(self, textvariable=self.phone_var, font=("Segoe UI", 13))
        phone_entry.pack(fill="x", padx=36, pady=(0, 28))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", pady=(16, 16))
        add_btn = ctk.CTkButton(btn_frame, text="Add", command=self._add_customer, width=120, font=("Segoe UI", 13, "bold"))
        add_btn.pack(side="left", padx=40)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=self._on_cancel, width=100)
        cancel_btn.pack(side="right", padx=40)

        self.bind("<Return>", lambda e: self._add_customer())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.resizable(False, False)

    def _add_customer(self):
        print("Add button pressed")
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        if not name:
            messagebox.showerror("Input Error", "Name cannot be empty.", parent=self)
            return
        try:
            cur = self.db.cursor()
            cur.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", (name, phone))
            self.db.commit()
            customer_id = cur.lastrowid
            if self.on_success:
                try:
                    self.on_success(customer_id, name, phone)
                except Exception as cb_err:
                    print(f"Error in on_success callback: {cb_err}")
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not add customer:\n{e}", parent=self)
        finally:
            print("Destroying dialog now")
            self.destroy()


    def _on_cancel(self):
        print("Cancel clicked, closing dialog.")
        self.update()
        self.destroy()
