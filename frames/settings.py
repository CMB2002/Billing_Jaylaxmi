import customtkinter as ctk
from tkinter import messagebox, filedialog
import json
import os

DEFAULTS = {
    "shop_name": "Jaylaxmi Shop",
    "shop_addr": "",
    "gst": "0",
    "phone": "",
    "email": "",
    "currency": "₹",
    "invoice_note": "Thank you for shopping with us!"
}

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, db, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app
        self.set_status = set_status or (lambda msg: None)

        self._create_table()
        self._build_form()
        self._load_settings()

    def _create_table(self):
        cur = self.db.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.db.commit()

    def _build_form(self):
        frm = ctk.CTkFrame(self)
        frm.pack(padx=20, pady=20, fill="both", expand=True)

        # Shop Details
        shop_frame = ctk.CTkLabel(frm, text="🏪 Shop Information", font=("Segoe UI", 15, "bold"))
        shop_frame.grid(row=0, column=0, columnspan=2, pady=(5,10))

        labels = ["Shop Name:", "Shop Address:", "Phone Number:", "Email:"]
        self.entries = {}

        for i, label in enumerate(labels):
            ctk.CTkLabel(frm, text=label, font=("Segoe UI", 13)).grid(row=i+1, column=0, sticky="e", padx=10, pady=5)
            entry = ctk.CTkEntry(frm, width=350)
            entry.grid(row=i+1, column=1, pady=5, sticky="w")
            self.entries[label] = entry

        # Invoice & Currency Settings
        inv_frame = ctk.CTkLabel(frm, text="🧾 Invoice & Currency Settings", font=("Segoe UI", 15, "bold"))
        inv_frame.grid(row=5, column=0, columnspan=2, pady=(15,10))

        ctk.CTkLabel(frm, text="GST Percent (%):", font=("Segoe UI", 13)).grid(row=6, column=0, sticky="e", padx=10, pady=5)
        self.gst = ctk.CTkEntry(frm, width=100)
        self.gst.grid(row=6, column=1, pady=5, sticky="w")

        ctk.CTkLabel(frm, text="Currency Symbol:", font=("Segoe UI", 13)).grid(row=7, column=0, sticky="e", padx=10, pady=5)
        self.currency = ctk.CTkEntry(frm, width=100)
        self.currency.grid(row=7, column=1, pady=5, sticky="w")

        ctk.CTkLabel(frm, text="Invoice Note:", font=("Segoe UI", 13)).grid(row=8, column=0, sticky="ne", padx=10, pady=5)
        self.invoice_note = ctk.CTkTextbox(frm, width=350, height=80)
        self.invoice_note.grid(row=8, column=1, pady=5, sticky="w")

        # Buttons Frame
        btns = ctk.CTkFrame(frm)
        btns.grid(row=9, column=0, columnspan=2, pady=(15,5))

        ctk.CTkButton(btns, text="💾 Save Settings", command=self._save_settings).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="🔄 Reload", command=self._load_settings).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="🔙 Reset to Default", fg_color="tomato", command=self._reset_defaults).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="📤 Export Settings", command=self._export_settings).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="📥 Import Settings", command=self._import_settings).pack(side="left", padx=8)

    def _load_settings(self):
        cur = self.db.cursor()
        cur.execute("SELECT key, value FROM settings")
        values = dict(cur.fetchall())

        self.entries["Shop Name:"].delete(0, "end")
        self.entries["Shop Name:"].insert(0, values.get("shop_name", DEFAULTS["shop_name"]))

        self.entries["Shop Address:"].delete(0, "end")
        self.entries["Shop Address:"].insert(0, values.get("shop_addr", DEFAULTS["shop_addr"]))

        self.entries["Phone Number:"].delete(0, "end")
        self.entries["Phone Number:"].insert(0, values.get("phone", DEFAULTS["phone"]))

        self.entries["Email:"].delete(0, "end")
        self.entries["Email:"].insert(0, values.get("email", DEFAULTS["email"]))

        self.gst.delete(0, "end")
        self.gst.insert(0, values.get("gst", DEFAULTS["gst"]))

        self.currency.delete(0, "end")
        self.currency.insert(0, values.get("currency", DEFAULTS["currency"]))

        self.invoice_note.delete("1.0", "end")
        self.invoice_note.insert("1.0", values.get("invoice_note", DEFAULTS["invoice_note"]))

        self.set_status("Settings successfully loaded.")

    def _save_settings(self):
        data = {
            "shop_name": self.entries["Shop Name:"].get().strip(),
            "shop_addr": self.entries["Shop Address:"].get().strip(),
            "phone": self.entries["Phone Number:"].get().strip(),
            "email": self.entries["Email:"].get().strip(),
            "gst": self.gst.get().strip(),
            "currency": self.currency.get().strip(),
            "invoice_note": self.invoice_note.get("1.0", "end").strip()
        }

        try:
            gst_value = float(data["gst"])
            if not 0 <= gst_value <= 100:
                raise ValueError
        except ValueError:
            messagebox.showerror("GST Error", "GST percent must be between 0 and 100.")
            return

        cur = self.db.cursor()
        for k, v in data.items():
            cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (k, v))
        self.db.commit()

        self.set_status("Settings successfully saved.")
        messagebox.showinfo("Success", "Settings saved!")

        if self.app:
            from utils.helpers import refresh_all
            refresh_all(self.app)

    def _reset_defaults(self):
        cur = self.db.cursor()
        for k, v in DEFAULTS.items():
            cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (k, v))
        self.db.commit()
        self._load_settings()
        self.set_status("Settings reset to default values.")
        messagebox.showinfo("Reset", "Settings reset to default!")

        if self.app:
            from utils.helpers import refresh_all
            refresh_all(self.app)

    def _export_settings(self):
        cur = self.db.cursor()
        cur.execute("SELECT key, value FROM settings")
        settings = dict(cur.fetchall())
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            messagebox.showinfo("Exported", f"Settings exported to:\n{filepath}")

    def _import_settings(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if filepath:
            with open(filepath, "r", encoding="utf-8") as f:
                settings = json.load(f)
            cur = self.db.cursor()
            for k, v in settings.items():
                cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (k, v))
            self.db.commit()
            self._load_settings()
            messagebox.showinfo("Imported", "Settings imported successfully!")
            if self.app:
                from utils.helpers import refresh_all
                refresh_all(self.app)

