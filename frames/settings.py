import customtkinter as ctk
from tkinter import messagebox

DEFAULTS = {
    "shop_name": "Jaylaxmi Shop",
    "shop_addr": "",
    "gst": "",
}

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, db, set_status=None, app=None):
        super().__init__(master)
        self.db = db
        self.app = app  # store app instance if needed for refresh_all or callbacks
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
        frm.pack(padx=30, pady=30, fill="y", expand=False)

        ctk.CTkLabel(frm, text="Shop Name:", font=("Segoe UI", 13)).grid(row=0, column=0, sticky="e", pady=7, padx=7)
        self.shop_name = ctk.CTkEntry(frm, width=300)
        self.shop_name.grid(row=0, column=1, pady=7, padx=7, sticky="w")

        ctk.CTkLabel(frm, text="Shop Address:", font=("Segoe UI", 13)).grid(row=1, column=0, sticky="e", pady=7, padx=7)
        self.shop_addr = ctk.CTkEntry(frm, width=300)
        self.shop_addr.grid(row=1, column=1, pady=7, padx=7, sticky="w")

        ctk.CTkLabel(frm, text="GST Percent (%):", font=("Segoe UI", 13)).grid(row=2, column=0, sticky="e", pady=7, padx=7)
        self.gst = ctk.CTkEntry(frm, width=100)
        self.gst.grid(row=2, column=1, pady=7, padx=7, sticky="w")

        btns = ctk.CTkFrame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=(15, 5))
        save_btn = ctk.CTkButton(btns, text="Save Settings", command=self._save_settings)
        save_btn.pack(side="left", padx=10)
        reload_btn = ctk.CTkButton(btns, text="Reload", command=self._load_settings)
        reload_btn.pack(side="left", padx=10)
        reset_btn = ctk.CTkButton(btns, text="Reset to Default", fg_color="tomato", command=self._reset_defaults)
        reset_btn.pack(side="left", padx=10)

    def _load_settings(self):
        cur = self.db.cursor()
        cur.execute("SELECT key, value FROM settings")
        values = dict(cur.fetchall())
        self.shop_name.delete(0, "end")
        self.shop_name.insert(0, values.get("shop_name", DEFAULTS["shop_name"]))
        self.shop_addr.delete(0, "end")
        self.shop_addr.insert(0, values.get("shop_addr", DEFAULTS["shop_addr"]))
        self.gst.delete(0, "end")
        self.gst.insert(0, values.get("gst", DEFAULTS["gst"]))
        self.set_status("Settings loaded.")

    def _save_settings(self):
        name = self.shop_name.get().strip()
        addr = self.shop_addr.get().strip()
        gst = self.gst.get().strip()
        # Validate GST percent
        if gst:
            try:
                gval = float(gst)
                if gval < 0 or gval > 100:
                    raise ValueError
            except Exception:
                messagebox.showerror("Input Error", "GST percent must be a number between 0 and 100.")
                return
        cur = self.db.cursor()
        cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", ("shop_name", name))
        cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", ("shop_addr", addr))
        cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", ("gst", gst))
        self.db.commit()
        self.set_status("Settings saved.")
        messagebox.showinfo("Settings", "Settings saved!")

        # Optionally refresh other parts of app if needed
        if self.app:
            from utils.helpers import refresh_all
            refresh_all(self.app)

    def _reset_defaults(self):
        cur = self.db.cursor()
        for k, v in DEFAULTS.items():
            cur.execute("INSERT OR REPLACE INTO settings VALUES (?, ?)", (k, v))
        self.db.commit()
        self._load_settings()
        self.set_status("Settings reset to default.")
        messagebox.showinfo("Settings", "Settings reset to default!")

        # Optionally refresh app UI after reset
        if self.app:
            from utils.helpers import refresh_all
            refresh_all(self.app)
