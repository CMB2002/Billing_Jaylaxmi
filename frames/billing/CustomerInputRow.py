import customtkinter as ctk
import tkinter as tk

class CustomerInputRow(ctk.CTkFrame):
    def __init__(self, master, db, on_customer_select=None, product_entry=None):
        super().__init__(master, fg_color="transparent")
        self.db = db
        self.master = master.winfo_toplevel()
        self.on_customer_select = on_customer_select
        self.product_entry = product_entry  # set this after both rows created if needed

        self.grid_columnconfigure((0, 1), weight=1)

        self.cust_name_entry = ctk.CTkEntry(self, placeholder_text="Customer Name", font=("Segoe UI", 13))
        self.cust_name_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.cust_name_entry.bind("<KeyRelease>", self._on_keyrelease)
        self.cust_name_entry.bind("<Down>", self._focus_suggestions_first)
        self.cust_name_entry.bind("<FocusOut>", self._on_entry_focusout)

        self.cust_phone_entry = ctk.CTkEntry(self, placeholder_text="Customer Phone", font=("Segoe UI", 13))
        self.cust_phone_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.cust_phone_entry.bind("<Return>", self._on_return)

        self.suggestions = tk.Listbox(self.master, font=("Segoe UI", 13), height=5,
                                      bg="#222831", fg="#ffffff",
                                      selectbackground="#68a1ff", selectforeground="#101318",
                                      highlightthickness=1, highlightcolor="#444",
                                      relief="flat", borderwidth=1, activestyle="none")
        self.suggestions.bind("<Down>", self._on_down)
        self.suggestions.bind("<Up>", self._on_up)
        self.suggestions.bind("<Return>", self._on_select)
        self.suggestions.bind("<ButtonRelease-1>", self._on_select)
        self.suggestions.bind("<FocusOut>", self._on_suggestions_focusout)
        self.listbox_visible = False

    def _on_keyrelease(self, event):
        if event.keysym in ("Up", "Down", "Return"):
            return
        self.update_suggestions()

    def _focus_suggestions_first(self, event=None):
        if self.listbox_visible and self.suggestions.size() > 0:
            self.suggestions.focus_set()
            self.suggestions.selection_clear(0, tk.END)
            self.suggestions.selection_set(0)
            self.suggestions.activate(0)
        return "break"

    def _on_down(self, event=None):
        sel = self.suggestions.curselection()
        size = self.suggestions.size()
        if not sel:
            idx = 0
        else:
            idx = sel[0] + 1
            if idx >= size:
                idx = size - 1
        self.suggestions.selection_clear(0, tk.END)
        self.suggestions.selection_set(idx)
        self.suggestions.activate(idx)
        return "break"

    def _on_up(self, event=None):
        sel = self.suggestions.curselection()
        size = self.suggestions.size()
        if not sel:
            idx = 0
        else:
            idx = sel[0] - 1
            if idx < 0:
                idx = 0
        self.suggestions.selection_clear(0, tk.END)
        self.suggestions.selection_set(idx)
        self.suggestions.activate(idx)
        return "break"

    def _on_select(self, event=None):
        sel = self.suggestions.curselection()
        if sel:
            val = self.suggestions.get(sel[0])
            name, phone = val.rsplit('(', 1)
            phone = phone.rstrip(')')
            self.cust_name_entry.delete(0, tk.END)
            self.cust_name_entry.insert(0, name.strip())
            self.cust_phone_entry.delete(0, tk.END)
            self.cust_phone_entry.insert(0, phone.strip())
            self.suggestions.place_forget()
            self.listbox_visible = False
            self.select_customer()
            # Move focus to product search bar if reference is provided
            if self.product_entry:
                self.product_entry.focus_set()
        return "break"

    def _on_entry_focusout(self, event=None):
        # Hide suggestions on focus out, unless focus moved to suggestions
        widget = self.master.focus_get()
        if widget != self.suggestions:
            self.suggestions.place_forget()
            self.listbox_visible = False

    def _on_suggestions_focusout(self, event=None):
        self.suggestions.place_forget()
        self.listbox_visible = False

    def _on_return(self, event=None):
        self.select_customer()
        # Move focus to product entry after pressing Enter in phone field
        if self.product_entry:
            self.product_entry.focus_set()

    def update_suggestions(self):
        term = self.cust_name_entry.get().strip()
        if term:
            cursor = self.db.cursor()
            cursor.execute("SELECT name, phone FROM customers WHERE name LIKE ? COLLATE NOCASE LIMIT 8", (f"%{term}%",))
            results = cursor.fetchall()
            if results:
                self.suggestions.delete(0, tk.END)
                for name, phone in results:
                    self.suggestions.insert(tk.END, f"{name} ({phone})")
                x = self.cust_name_entry.winfo_rootx() - self.master.winfo_rootx()
                y = self.cust_name_entry.winfo_rooty() - self.master.winfo_rooty() + self.cust_name_entry.winfo_height()
                self.suggestions.place(x=x, y=y, width=self.cust_name_entry.winfo_width())
                self.suggestions.lift()
                self.listbox_visible = True
                return
        self.suggestions.place_forget()
        self.listbox_visible = False

    def select_customer(self):
        customer = {
            "name": self.cust_name_entry.get().strip(),
            "phone": self.cust_phone_entry.get().strip()
        }
        if self.on_customer_select:
            self.on_customer_select(customer)
