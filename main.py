import customtkinter as ctk
from frames.billing import BillingFrame
from frames.customer import CustomerFrame
from frames.product import ProductFrame
from frames.report import ReportFrame
from frames.settings import SettingsFrame
from database import Database
import os

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
ctk.set_widget_scaling(1.1)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.db = Database('billing.db')

        self.title("Jaylaxmi Billing Software")
        self.geometry("1100x750")
        self.minsize(950, 650)

        # AppBar
        header = ctk.CTkFrame(self, height=54, corner_radius=0)
        header.pack(side="top", fill="x")
        ctk.CTkLabel(
            header,
            text="🛒 Jaylaxmi Billing Software",
            font=("Segoe UI", 21, "bold"),
            anchor="w"
        ).pack(side="left", padx=20, pady=12)

        # Status Bar
        self.status_bar = ctk.CTkLabel(
            self, text="Ready", anchor="w", font=("Segoe UI", 12),
            height=24
        )
        self.status_bar.pack(side="bottom", fill="x")

        # Sidebar + Content
        body = ctk.CTkFrame(self)
        body.pack(expand=True, fill="both")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # Sidebar Navigation
        sidebar = ctk.CTkFrame(body, width=200)
        sidebar.grid(row=0, column=0, sticky="ns", padx=(10,0), pady=10)
        self.side_buttons = {}

        tab_data = [
            ("Products", ProductFrame),
            ("Billing", BillingFrame),
            ("Reports", ReportFrame),
            ("Customers", CustomerFrame),
            ("Settings", SettingsFrame)
        ]

        for name, FrameClass in tab_data:
            btn = ctk.CTkButton(
                sidebar, text=name,
                fg_color="transparent", anchor="w",
                font=("Segoe UI", 15),
                command=lambda n=name: self.show_tab(n)
            )
            btn.pack(fill="x", pady=5, padx=12)
            self.side_buttons[name] = btn

        # Content Container
        self.container = ctk.CTkFrame(body)
        self.container.grid(row=0, column=1, sticky="nsew", padx=10, pady=16)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Initialize all frames and pass 'app=self' to enable refresh_all usage
        self.frames = {}
        for name, FrameClass in tab_data:
            if name == "Billing":
                frame = FrameClass(self.container, db=self.db, set_status=self.set_status, app=self)
            else:
                frame = FrameClass(self.container, db=self.db, set_status=self.set_status, app=self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[name] = frame

        self.show_tab("Products")

    def show_tab(self, name):
        for key, frame in self.frames.items():
            frame.grid_remove()
            self.side_buttons[key].configure(fg_color="transparent")
        
        self.frames[name].grid()
        self.side_buttons[name].configure(fg_color="#293040")
        self.set_status(f"{name} loaded.")

    def set_status(self, msg):
        self.status_bar.configure(text=msg)


if __name__ == "__main__":
    app = App()
    app.mainloop()
