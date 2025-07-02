import customtkinter as ctk
from frames.billing.BillingTabs import BillingTabs         # <-- NEW import!
from frames.customer import CustomerFrame
from frames.product import ProductFrame
from frames.report import ReportFrame
from frames.settings import SettingsFrame
from frames.dashboard import DashboardFrame
from frames.expense import ExpenseFrame
from frames.staff import StaffFrame
from database import Database
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.1)

class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent, password, on_success):
        super().__init__(parent)
        self.title("Enter Password")
        self.geometry("380x180")
        self.resizable(False, False)
        self.attributes('-topmost', True)
        self.lift()
        self.grab_set()
        self.password = password
        self.on_success = on_success

        frm = ctk.CTkFrame(self, corner_radius=18)
        frm.pack(expand=True, fill="both", padx=22, pady=22)
        ctk.CTkLabel(frm, text="🔒 Enter Password", font=("Segoe UI", 17, "bold")).pack(pady=(8, 18))
        self.entry = ctk.CTkEntry(frm, width=180, show="*", font=("Segoe UI", 14))
        self.entry.pack(pady=6)
        self.entry.focus()
        ctk.CTkButton(frm, text="Unlock", font=("Segoe UI", 14, "bold"), corner_radius=10,
                      command=self.check_password).pack(pady=18)
        self.entry.bind("<Return>", lambda e: self.check_password())
        self.error_label = ctk.CTkLabel(frm, text="", text_color="#e56", font=("Segoe UI", 12))
        self.error_label.pack()

    def check_password(self):
        entered = self.entry.get()
        if entered == self.password:
            self.grab_release()
            self.destroy()
            self.on_success()
        else:
            self.error_label.configure(text="Incorrect password. Try again.")
            self.entry.delete(0, "end")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.db = Database('billing.db')

        self.title("Jaylaxmi Billing Software")
        self.geometry("1180x770")
        self.minsize(1000, 670)

        header = ctk.CTkFrame(self, height=58, corner_radius=0, fg_color="#1a1e25")
        header.pack(side="top", fill="x")
        ctk.CTkLabel(
            header,
            text="🛒 Jaylaxmi Billing Software",
            font=("Segoe UI", 22, "bold"),
            anchor="w",
            text_color="#7dd3fc"
        ).pack(side="left", padx=24, pady=12)

        self.status_bar = ctk.CTkLabel(
            self, text="Ready", anchor="w", font=("Segoe UI", 12),
            height=28, fg_color="#23272f"
        )
        self.status_bar.pack(side="bottom", fill="x")

        body = ctk.CTkFrame(self, fg_color="#181c23")
        body.pack(expand=True, fill="both")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(body, width=220, corner_radius=18, fg_color="#23272f")
        sidebar.grid(row=0, column=0, sticky="ns", padx=(16, 0), pady=16)
        self.side_buttons = {}

        tab_data = [
            ("Dashboard", "📊", DashboardFrame),
            ("Products", "📦", ProductFrame),
            ("Billing", "🧾", BillingTabs),        # <-- Use BillingTabs here!
            ("Reports", "📋", ReportFrame),
            ("Expenses", "💸", ExpenseFrame),
            ("Staff", "👔", StaffFrame),
            ("Customers", "👥", CustomerFrame),
            ("Settings", "⚙️", SettingsFrame),
        ]

        for name, icon, FrameClass in tab_data:
            btn = ctk.CTkButton(
                sidebar,
                text=f"{icon}  {name}",
                fg_color="transparent",
                anchor="w",
                font=("Segoe UI", 15, "bold"),
                corner_radius=10,
                height=44,
                command=lambda n=name: self.show_tab(n)
            )
            btn.pack(fill="x", pady=7, padx=14)
            self.side_buttons[name] = btn

        self.container = ctk.CTkFrame(body, corner_radius=18, fg_color="#212836")
        self.container.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        for name, _, FrameClass in tab_data:
            frame = FrameClass(self.container, db=self.db, set_status=self.set_status, app=self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[name] = frame

        self.show_tab("Dashboard")

    def show_tab(self, name):
        for key, frame in self.frames.items():
            frame.grid_remove()
            self.side_buttons[key].configure(fg_color="transparent")
        self.frames[name].grid()
        self.side_buttons[name].configure(fg_color="#293040")
        self.set_status(f"{name} loaded.")

    def set_status(self, msg):
        self.status_bar.configure(text=msg)

def launch_main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()
    def on_success():
        root.destroy()
        launch_main()
    PasswordDialog(root, password="7058620579", on_success=on_success)
    root.mainloop()
