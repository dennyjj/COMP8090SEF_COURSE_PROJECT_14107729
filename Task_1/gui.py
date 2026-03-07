import tkinter as tk
from tkinter import ttk


class App(tk.Tk):
    """Main application window for Personal Finance Tracker."""

    def __init__(self):
        super().__init__()
        self.title("Personal Finance Tracker")
        self.geometry("900x600")
        self.minsize(800, 500)
        self._build_layout()

    def _build_layout(self):
        """Build the main layout with sidebar and content area."""
        # Sidebar
        self._sidebar = tk.Frame(self, bg="#2c3e50", width=200)
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self._sidebar.pack_propagate(False)

        # App title in sidebar
        tk.Label(
            self._sidebar,
            text="Finance Tracker",
            bg="#2c3e50",
            fg="white",
            font=("Arial", 14, "bold"),
            pady=20,
        ).pack(fill=tk.X)

        # Navigation buttons
        nav_items = ["Dashboard", "Transactions", "Accounts", "Budgets", "Reports"]
        for item in nav_items:
            btn = tk.Button(
                self._sidebar,
                text=item,
                bg="#34495e",
                fg="white",
                font=("Arial", 11),
                relief=tk.FLAT,
                pady=10,
                activebackground="#1abc9c",
                activeforeground="white",
                command=lambda name=item: self._show_page(name),
            )
            btn.pack(fill=tk.X, padx=10, pady=2)

        # Content area
        self._content = tk.Frame(self, bg="#ecf0f1")
        self._content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Show dashboard by default
        self._show_page("Dashboard")

    def _show_page(self, name):
        """Switch the content area to the selected page."""
        # Clear current content
        for widget in self._content.winfo_children():
            widget.destroy()

        # Page header
        tk.Label(
            self._content,
            text=name,
            bg="#ecf0f1",
            font=("Arial", 20, "bold"),
            anchor="w",
            padx=20,
            pady=20,
        ).pack(fill=tk.X)

        # Placeholder content
        tk.Label(
            self._content,
            text=f"{name} page — coming soon",
            bg="#ecf0f1",
            font=("Arial", 12),
            fg="#7f8c8d",
            padx=20,
        ).pack(anchor="w")
