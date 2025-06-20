# ui_windows.py

import customtkinter as ctk
from tkinter import messagebox

# ---- Generic Confirm Dialog ----
class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str, on_confirm):
        super().__init__(parent)
        self.title(title)
        self.grab_set()
        self.resizable(False, False)
        self.geometry("390x180")
        self.configure(fg_color="#23272f")
        ctk.CTkLabel(
            self,
            text=f"❓ {message}",
            font=("Segoe UI", 15, "bold"),
            text_color="#7dd3fc",
            wraplength=350
        ).pack(padx=22, pady=(24, 12))

        btn_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#23272f")
        btn_frame.pack(pady=(0, 14))

        ctk.CTkButton(
            btn_frame,
            text="✔️ Yes",
            width=96,
            font=("Segoe UI", 13, "bold"),
            fg_color="#2d6a4f",
            hover_color="#43aa8b",
            corner_radius=9,
            command=lambda: (on_confirm(), self.destroy())
        ).pack(side="left", padx=18)

        ctk.CTkButton(
            btn_frame,
            text="❌ No",
            width=96,
            font=("Segoe UI", 13, "bold"),
            fg_color="#293040",
            hover_color="#e56",
            corner_radius=9,
            command=self.destroy
        ).pack(side="right", padx=18)

# ---- Generic Edit Form ----
class EditFormDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, fields: list, initial_values: dict, on_submit):
        super().__init__(parent)
        self.title(title)
        self.grab_set()
        self.resizable(False, False)
        self.configure(fg_color="#23272f")
        self.entries = {}
        frm = ctk.CTkFrame(self, fg_color="#212836", corner_radius=16)
        frm.pack(padx=26, pady=16, fill="both", expand=True)
        ctk.CTkLabel(frm, text=f"📝 {title}", font=("Segoe UI", 16, "bold"), text_color="#7dd3fc").grid(
            row=0, column=0, columnspan=2, pady=(4, 14)
        )
        for idx, field in enumerate(fields):
            ctk.CTkLabel(frm, text=field + ":", anchor="e", font=("Segoe UI", 13)).grid(
                row=idx + 1, column=0, sticky="e", pady=7, padx=7
            )
            entry = ctk.CTkEntry(frm, font=("Segoe UI", 13), corner_radius=8)
            entry.grid(row=idx + 1, column=1, pady=7, padx=7, sticky="ew")
            entry.insert(0, initial_values.get(field, ""))
            self.entries[field] = entry
        frm.grid_columnconfigure(1, weight=1)

        btn_frame = ctk.CTkFrame(self, fg_color="#23272f")
        btn_frame.pack(pady=(0, 16))

        ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            width=96,
            font=("Segoe UI", 13, "bold"),
            fg_color="#324076",
            hover_color="#7dd3fc",
            corner_radius=9,
            command=lambda: self._submit(on_submit)
        ).pack(side="left", padx=16)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=96,
            font=("Segoe UI", 13, "bold"),
            fg_color="#293040",
            hover_color="#e56",
            corner_radius=9,
            command=self.destroy
        ).pack(side="right", padx=16)

    def _submit(self, on_submit):
        values = {field: entry.get().strip() for field, entry in self.entries.items()}
        on_submit(values)
        self.destroy()

# ---- Simple Info Message ----
def info_dialog(parent, title, message):
    messagebox.showinfo(f"ℹ️ {title}", message, parent=parent)

# ---- Simple Error Message ----
def error_dialog(parent, title, message):
    messagebox.showerror(f"❌ {title}", message, parent=parent)
