# ui_windows.py

import customtkinter as ctk
from tkinter import Toplevel, messagebox

# ---- Generic Confirm Dialog ----
class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str, on_confirm):
        super().__init__(parent)
        self.title(title)
        self.grab_set()
        self.resizable(False, False)
        self.geometry("360x160")
        ctk.CTkLabel(self, text=message, font=("Segoe UI", 13), wraplength=340).pack(padx=20, pady=(22,12))
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=(0,18))
        ctk.CTkButton(btn_frame, text="Yes", width=90, command=lambda: (on_confirm(), self.destroy())).pack(side="left", padx=14)
        ctk.CTkButton(btn_frame, text="No", width=90, command=self.destroy).pack(side="right", padx=14)

# ---- Generic Edit Form ----
class EditFormDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, fields: list, initial_values: dict, on_submit):
        super().__init__(parent)
        self.title(title)
        self.grab_set()
        self.resizable(False, False)
        self.entries = {}
        frm = ctk.CTkFrame(self)
        frm.pack(padx=30, pady=22, fill="both", expand=True)
        for idx, field in enumerate(fields):
            ctk.CTkLabel(frm, text=field + ":", anchor="e").grid(row=idx, column=0, sticky="e", pady=7, padx=7)
            entry = ctk.CTkEntry(frm)
            entry.grid(row=idx, column=1, pady=7, padx=7, sticky="ew")
            entry.insert(0, initial_values.get(field, ""))
            self.entries[field] = entry
        frm.grid_columnconfigure(1, weight=1)
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=(0,18))
        ctk.CTkButton(btn_frame, text="Save", width=90, command=lambda: self._submit(on_submit)).pack(side="left", padx=14)
        ctk.CTkButton(btn_frame, text="Cancel", width=90, command=self.destroy).pack(side="right", padx=14)

    def _submit(self, on_submit):
        values = {field: entry.get().strip() for field, entry in self.entries.items()}
        on_submit(values)
        self.destroy()

# ---- Simple Info Message ----
def info_dialog(parent, title, message):
    messagebox.showinfo(title, message, parent=parent)

# ---- Simple Error Message ----
def error_dialog(parent, title, message):
    messagebox.showerror(title, message, parent=parent)


