import customtkinter as ctk
from tkinter import messagebox

class AddCustomerDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry("400x300")
        ctk.CTkLabel(self, text="Add New Customer", font=("Segoe UI", 15, "bold")).pack(pady=24)
        self.name_var = ctk.StringVar()
        name_entry = ctk.CTkEntry(self, textvariable=self.name_var)
        name_entry.pack(fill="x", padx=36, pady=10)
        add_btn = ctk.CTkButton(self, text="Add", command=self._add_customer)
        add_btn.pack(pady=18)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Return>", lambda e: self._add_customer())
        self.resizable(False, False)

    def _add_customer(self):
        print("Destroying dialog now")
        self.destroy()

if __name__ == "__main__":
    app = ctk.CTk()
    ctk.CTkButton(app, text="Open Dialog", command=lambda: AddCustomerDialog(app)).pack(pady=30)
    app.mainloop()
