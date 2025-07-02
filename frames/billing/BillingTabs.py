import customtkinter as ctk
from .BillingFrame import BillingFrame
from tkinter import messagebox

class BillingTabs(ctk.CTkFrame):
    MAX_TABS = 6

    def __init__(self, master, db, set_status=None, app=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.set_status = set_status
        self.app = app
        self.tabs = []
        self.tab_buttons = []
        self.active_index = 0

        # Transparent tab bar (no background)
        self.tab_bar = ctk.CTkFrame(self, fg_color="transparent", height=48)
        self.tab_bar.pack(side="top", fill="x", padx=16, pady=(8, 0))

        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(side="top", fill="both", expand=True)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        self.add_new_tab(init=True)

    def add_new_tab(self, init=False):
        if len(self.tabs) >= self.MAX_TABS:
            messagebox.showwarning("Tab Limit", f"Maximum {self.MAX_TABS} tabs allowed.")
            return

        billing_frame = BillingFrame(self.content_area, db=self.db, set_status=self.set_status, app=self.app)
        billing_frame.grid(row=0, column=0, sticky="nsew")

        tab_number = len(self.tabs) + 1
        tab_title = f"Bill {tab_number}"

        def switch_tab_closure(idx):
            return lambda: self.switch_tab(idx)
        def close_tab_closure(idx):
            return lambda: self.close_tab(idx)

        tab_btn = ctk.CTkFrame(
            self.tab_bar,
            fg_color="#374151" if self.active_index != len(self.tabs) else "#111827",
            border_color="#4b5563", border_width=1,
            corner_radius=12, height=40, width=160
        )
        tab_btn.pack_propagate(False)
        tab_btn.pack(side="left", padx=(0, 12), pady=4)

        title_btn = ctk.CTkButton(
            tab_btn, text=tab_title, width=110, height=32,
            fg_color="transparent", hover_color="#4b5563",
            text_color="#d1d5db" if self.active_index != len(self.tabs) else "#f9fafb",
            font=("Segoe UI", 14, "bold"),
            command=switch_tab_closure(len(self.tabs))
        )
        title_btn.pack(side="left", padx=(10, 0))

        close_btn = ctk.CTkButton(
            tab_btn, text="✕", width=32, height=32,
            fg_color="transparent", hover_color="#ef4444",
            text_color="#9ca3af" if self.active_index != len(self.tabs) else "#f9fafb",
            font=("Segoe UI", 15, "bold"),
            command=close_tab_closure(len(self.tabs))
        )
        close_btn.pack(side="right", padx=(0, 6))
        if len(self.tabs) == 0:
            close_btn.configure(state="disabled")

        self.tabs.append(billing_frame)
        self.tab_buttons.append(tab_btn)

        # "+ New Tab" button at end
        if hasattr(self, "add_tab_btn"):
            self.add_tab_btn.destroy()
        self.add_tab_btn = ctk.CTkButton(
            self.tab_bar, text="+", width=40, height=32,
            fg_color="#374151" if len(self.tabs) < self.MAX_TABS else "#1f2937",
            hover_color="#4b5563", text_color="#9ca3af" if len(self.tabs) < self.MAX_TABS else "#4b5563",
            font=("Segoe UI", 18, "bold"),
            corner_radius=10,
            command=self.add_new_tab,
            state="normal" if len(self.tabs) < self.MAX_TABS else "disabled"
        )
        self.add_tab_btn.pack(side="left", padx=(0, 8))

        self.switch_tab(len(self.tabs) - 1)

    def switch_tab(self, idx):
        if idx == self.active_index:
            return
        for tab in self.tabs:
            tab.grid_remove()
        self.tabs[idx].grid()
        self.active_index = idx
        self.refresh_tab_bar_styles()

    def close_tab(self, idx):
        if len(self.tabs) == 1:
            messagebox.showwarning("Required", "At least one billing tab must remain open.")
            return
        if messagebox.askyesno("Close Tab", f"Close Bill {idx+1}?"):
            self.tabs[idx].destroy()
            self.tabs.pop(idx)
            self.tab_buttons[idx].destroy()
            self.tab_buttons.pop(idx)
            self.active_index = max(0, idx - 1)
            self.switch_tab(self.active_index)
            for i, tab_btn in enumerate(self.tab_buttons):
                tab_btn.winfo_children()[0].configure(text=f"Bill {i+1}")
                tab_btn.winfo_children()[1].configure(state="normal" if i != 0 else "disabled")
            if len(self.tabs) < self.MAX_TABS:
                self.add_tab_btn.configure(state="normal", fg_color="#374151", text_color="#9ca3af")

    def refresh_tab_bar_styles(self):
        for i, tab_btn in enumerate(self.tab_buttons):
            if i == self.active_index:
                tab_btn.configure(fg_color="#111827")
                tab_btn.winfo_children()[0].configure(text_color="#f9fafb")
                tab_btn.winfo_children()[1].configure(text_color="#f9fafb")
            else:
                tab_btn.configure(fg_color="#374151")
                tab_btn.winfo_children()[0].configure(text_color="#d1d5db")
                tab_btn.winfo_children()[1].configure(text_color="#9ca3af")
