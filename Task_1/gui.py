"""
gui.py — Tkinter GUI for the Personal Finance Tracker.

Provides a sidebar-navigation desktop application with five pages:
  Dashboard, Transactions, Accounts, Budgets, Reports.

Each page is built dynamically inside the content frame when the user
clicks the corresponding sidebar button.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from models import Account, Budget, Expense, Income, Transfer
from data_manager import DataManager
from reports import Report


# ---------------------------------------------------------------------------
# Colour palette — explicit fg colours prevent macOS dark-mode issues
# ---------------------------------------------------------------------------
_SIDEBAR_BG = "#2c3e50"
_SIDEBAR_BTN = "#34495e"
_SIDEBAR_ACTIVE = "#1abc9c"
_CONTENT_BG = "#ecf0f1"
_CARD_BG = "#ffffff"
_TEXT = "#2c3e50"          # dark text on light backgrounds
_TEXT_LIGHT = "#555555"    # secondary / muted text
_GREEN = "#27ae60"
_RED = "#e74c3c"
_ORANGE = "#f39c12"
_GREY = "#7f8c8d"

# Shared entry style: explicit light bg + dark fg to avoid dark-mode issues
_ENTRY_OPTS = {"bg": "#ffffff", "fg": "#000000",
               "insertbackground": "#000000", "relief": tk.SOLID, "bd": 1}


class App(tk.Tk):
    """Main application window."""

    def __init__(self, data_manager: DataManager) -> None:
        super().__init__()
        self.title("Personal Finance Tracker")
        self.geometry("960x640")
        self.minsize(860, 540)
        self._dm = data_manager
        self._build_layout()

    # ------------------------------------------------------------------ layout

    def _build_layout(self) -> None:
        """Create the sidebar and the switchable content area."""
        sidebar = tk.Frame(self, bg=_SIDEBAR_BG, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="Finance Tracker", bg=_SIDEBAR_BG, fg="white",
            font=("Arial", 14, "bold"), pady=20,
        ).pack(fill=tk.X)

        self._nav_buttons: dict[str, tk.Button] = {}
        for name in ("Dashboard", "Transactions", "Accounts",
                      "Budgets", "Reports"):
            btn = tk.Button(
                sidebar, text=name, bg=_SIDEBAR_BTN, fg="white",
                font=("Arial", 11), pady=10,
                activebackground=_SIDEBAR_ACTIVE, activeforeground="white",
                command=lambda n=name: self._show_page(n),
            )
            btn.pack(fill=tk.X, padx=10, pady=2)
            self._nav_buttons[name] = btn

        self._content = tk.Frame(self, bg=_CONTENT_BG)
        self._content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._current_page = ""
        self._show_page("Dashboard")

    def _refresh_page(self) -> None:
        """Force-rebuild the current page."""
        page = self._current_page
        self._current_page = ""
        self._show_page(page)

    def _show_page(self, name: str) -> None:
        """Clear the content frame and build the requested page."""
        if not name or name == self._current_page:
            return
        self._current_page = name

        for btn_name, btn in self._nav_buttons.items():
            btn.configure(bg=_SIDEBAR_ACTIVE if btn_name == name
                          else _SIDEBAR_BTN)

        for w in self._content.winfo_children():
            w.destroy()

        tk.Label(
            self._content, text=name, bg=_CONTENT_BG, fg=_TEXT,
            font=("Arial", 20, "bold"), anchor="w", padx=20, pady=15,
        ).pack(fill=tk.X)

        builders = {
            "Dashboard": self._build_dashboard,
            "Transactions": self._build_transactions,
            "Accounts": self._build_accounts,
            "Budgets": self._build_budgets,
            "Reports": self._build_reports,
        }
        builders[name]()

    # ================================================================== PAGES

    # ---- Dashboard --------------------------------------------------------

    def _build_dashboard(self) -> None:
        wrapper = tk.Frame(self._content, bg=_CONTENT_BG)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Account balance cards
        cards = tk.Frame(wrapper, bg=_CONTENT_BG)
        cards.pack(fill=tk.X, pady=(0, 10))

        for acct in self._dm.accounts:
            card = tk.Frame(cards, bg=_CARD_BG, relief=tk.RIDGE, bd=1,
                            padx=15, pady=10)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            tk.Label(card, text=acct.name, bg=_CARD_BG, fg=_TEXT,
                     font=("Arial", 11)).pack(anchor="w")
            colour = _GREEN if acct.balance >= 0 else _RED
            tk.Label(card, text=f"${acct.balance:,.2f}", bg=_CARD_BG,
                     fg=colour, font=("Arial", 16, "bold")).pack(anchor="w")
            tk.Label(card, text=acct.account_type, bg=_CARD_BG,
                     fg=_GREY, font=("Arial", 9)).pack(anchor="w")

        # Monthly summary
        report = Report(self._dm.transactions)
        sf = tk.Frame(wrapper, bg=_CARD_BG, relief=tk.RIDGE, bd=1,
                      padx=15, pady=10)
        sf.pack(fill=tk.X, pady=(0, 10))
        tk.Label(sf, text="Monthly Summary", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 12, "bold")).pack(anchor="w")
        info = (f"Income: ${report.total_income():,.2f}    "
                f"Expenses: ${report.total_expense():,.2f}    "
                f"Net: ${report.net_amount():,.2f}")
        tk.Label(sf, text=info, bg=_CARD_BG, fg=_TEXT_LIGHT,
                 font=("Arial", 11)).pack(anchor="w", pady=3)

        # Budget alerts
        alerts = [b for b in self._dm.budgets if b.is_near_limit()]
        if alerts:
            af = tk.Frame(wrapper, bg="#fdf2e9", relief=tk.RIDGE,
                          bd=1, padx=15, pady=8)
            af.pack(fill=tk.X, pady=(0, 10))
            tk.Label(af, text="Budget Alerts", bg="#fdf2e9",
                     fg=_ORANGE, font=("Arial", 11, "bold")).pack(anchor="w")
            for b in alerts:
                c = _RED if b.is_over_budget() else _ORANGE
                tk.Label(
                    af, bg="#fdf2e9", fg=c,
                    text=(f"  {b.category}: ${b.spent:,.2f} / "
                          f"${b.monthly_limit:,.2f} — {b.status_label()}"),
                    font=("Arial", 10),
                ).pack(anchor="w")

        # Recent transactions
        tk.Label(wrapper, text="Recent Transactions", bg=_CONTENT_BG,
                 fg=_TEXT, font=("Arial", 12, "bold")).pack(
                     anchor="w", pady=(5, 3))

        tree = self._make_transaction_tree(wrapper)
        for tx in self._dm.get_transactions_sorted()[:10]:
            tag = tx.transaction_type().value
            tree.insert("", "end", values=(
                tx.date.strftime("%Y-%m-%d"),
                tx.transaction_type().value.title(),
                tx.category,
                f"${tx.amount:,.2f}",
                tx.summary(),
            ), tags=(tag,))
        tree.tag_configure("income", foreground=_GREEN)
        tree.tag_configure("expense", foreground=_RED)
        tree.tag_configure("transfer", foreground="#2980b9")

    # ---- Transactions page ------------------------------------------------

    def _build_transactions(self) -> None:
        wrapper = tk.Frame(self._content, bg=_CONTENT_BG)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # -- Form: grid layout with labels above inputs ----------------------
        form = tk.LabelFrame(wrapper, text=" Add Transaction ",
                             bg=_CARD_BG, fg=_TEXT,
                             font=("Arial", 11, "bold"), padx=12, pady=10)
        form.pack(fill=tk.X, pady=(0, 10))

        # Row 0 — Type radio buttons
        tk.Label(form, text="Type", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10, "bold")).grid(
                     row=0, column=0, sticky="w", pady=(0, 2))
        type_frame = tk.Frame(form, bg=_CARD_BG)
        type_frame.grid(row=1, column=0, columnspan=4, sticky="w",
                        pady=(0, 8))
        type_var = tk.StringVar(value="expense")
        for val in ("income", "expense", "transfer"):
            tk.Radiobutton(
                type_frame, text=val.title(), variable=type_var,
                value=val, bg=_CARD_BG, fg=_TEXT,
                selectcolor=_CARD_BG, activebackground=_CARD_BG,
                activeforeground=_TEXT,
            ).pack(side=tk.LEFT, padx=(0, 15))

        # Row 2-3 — Amount + Category
        tk.Label(form, text="Amount ($)", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=2, column=0, sticky="w")
        amount_var = tk.StringVar()
        tk.Entry(form, textvariable=amount_var, width=14,
                 **_ENTRY_OPTS).grid(row=3, column=0, sticky="w",
                                     padx=(0, 12), pady=(0, 8))

        tk.Label(form, text="Category", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=2, column=1, sticky="w")
        cat_var = tk.StringVar()
        ttk.Combobox(form, textvariable=cat_var, width=14, state="readonly",
                     values=["Salary", "Freelance", "Rent",
                             "Groceries", "Transport", "Dining",
                             "Entertainment", "Utilities",
                             "Other"]).grid(
                                 row=3, column=1, sticky="w",
                                 padx=(0, 12), pady=(0, 8))

        # Row 2-3 — Source/Payee + Note
        tk.Label(form, text="Source / Payee", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=2, column=2, sticky="w")
        detail_var = tk.StringVar()
        tk.Entry(form, textvariable=detail_var, width=18,
                 **_ENTRY_OPTS).grid(row=3, column=2, sticky="w",
                                     padx=(0, 12), pady=(0, 8))

        tk.Label(form, text="Note", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=2, column=3, sticky="w")
        note_var = tk.StringVar()
        tk.Entry(form, textvariable=note_var, width=18,
                 **_ENTRY_OPTS).grid(row=3, column=3, sticky="w",
                                     pady=(0, 8))

        # Row 4-5 — Transfer accounts (From / To)
        tk.Label(form, text="From Account", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=4, column=0, sticky="w")
        from_var = tk.StringVar()
        ttk.Combobox(form, textvariable=from_var, width=14, state="readonly",
                     values=self._dm.get_account_names()).grid(
                         row=5, column=0, sticky="w",
                         padx=(0, 12), pady=(0, 8))

        tk.Label(form, text="To Account", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=4, column=1, sticky="w")
        to_var = tk.StringVar()
        ttk.Combobox(form, textvariable=to_var, width=14, state="readonly",
                     values=self._dm.get_account_names()).grid(
                         row=5, column=1, sticky="w",
                         padx=(0, 12), pady=(0, 8))

        # Hint text for transfer fields
        transfer_hint = tk.Label(form, text="(only for transfers)",
                                 bg=_CARD_BG, fg=_GREY,
                                 font=("Arial", 9, "italic"))
        transfer_hint.grid(row=5, column=2, sticky="w")

        def _add() -> None:
            try:
                amt = float(amount_var.get())
            except ValueError:
                messagebox.showerror("Error", "Amount must be a number.")
                return

            tx_type = type_var.get()
            try:
                if tx_type == "income":
                    tx = Income(amt, cat_var.get() or "Other",
                                source=detail_var.get(),
                                note=note_var.get())
                elif tx_type == "expense":
                    tx = Expense(amt, cat_var.get() or "Other",
                                 payee=detail_var.get(),
                                 note=note_var.get())
                else:
                    if not from_var.get() or not to_var.get():
                        messagebox.showerror(
                            "Error", "Select both accounts for transfer.")
                        return
                    tx = Transfer(amt, from_var.get(), to_var.get(),
                                  note=note_var.get())
            except ValueError as e:
                messagebox.showerror("Validation Error", str(e))
                return

            self._dm.add_transaction(tx)
            self._dm.update_budgets_from_transactions()
            self._dm.save()
            self._refresh_page()

        tk.Button(form, text="Add Transaction", bg=_SIDEBAR_ACTIVE,
                  fg="white", font=("Arial", 10, "bold"),
                  activebackground="#16a085", activeforeground="white",
                  cursor="hand2", padx=16, pady=4,
                  command=_add).grid(row=6, column=0, columnspan=2,
                                     sticky="w", pady=(4, 0))

        # -- Transaction list ------------------------------------------------
        tk.Label(wrapper, text="All Transactions", bg=_CONTENT_BG,
                 fg=_TEXT, font=("Arial", 12, "bold")).pack(
                     anchor="w", pady=(5, 3))

        tree = self._make_transaction_tree(wrapper)
        for tx in self._dm.get_transactions_sorted():
            tag = tx.transaction_type().value
            tree.insert("", "end", values=(
                tx.date.strftime("%Y-%m-%d"),
                tx.transaction_type().value.title(),
                tx.category,
                f"${tx.amount:,.2f}",
                tx.summary(),
            ), tags=(tag,))
        tree.tag_configure("income", foreground=_GREEN)
        tree.tag_configure("expense", foreground=_RED)
        tree.tag_configure("transfer", foreground="#2980b9")

    # ---- Accounts page ----------------------------------------------------

    def _build_accounts(self) -> None:
        wrapper = tk.Frame(self._content, bg=_CONTENT_BG)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # -- Form: grid layout -----------------------------------------------
        form = tk.LabelFrame(wrapper, text=" Add Account ",
                             bg=_CARD_BG, fg=_TEXT,
                             font=("Arial", 11, "bold"), padx=12, pady=10)
        form.pack(fill=tk.X, pady=(0, 10))

        tk.Label(form, text="Account Name", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        name_var = tk.StringVar()
        tk.Entry(form, textvariable=name_var, width=18,
                 **_ENTRY_OPTS).grid(row=1, column=0, sticky="w",
                                     padx=(0, 12), pady=(0, 8))

        tk.Label(form, text="Account Type", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=0, column=1, sticky="w")
        type_var = tk.StringVar(value="bank")
        ttk.Combobox(form, textvariable=type_var, width=14, state="readonly",
                     values=["cash", "bank", "credit_card"]).grid(
                         row=1, column=1, sticky="w",
                         padx=(0, 12), pady=(0, 8))

        tk.Label(form, text="Initial Balance ($)", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=0, column=2, sticky="w")
        bal_var = tk.StringVar(value="0")
        tk.Entry(form, textvariable=bal_var, width=14,
                 **_ENTRY_OPTS).grid(row=1, column=2, sticky="w",
                                     pady=(0, 8))

        def _add_account() -> None:
            n = name_var.get().strip()
            if not n:
                messagebox.showerror("Error", "Account name is required.")
                return
            if self._dm.get_account(n):
                messagebox.showerror("Error",
                                     f"Account '{n}' already exists.")
                return
            try:
                bal = float(bal_var.get())
            except ValueError:
                bal = 0.0
            self._dm.add_account(Account(n, type_var.get(), bal))
            self._dm.save()
            self._refresh_page()

        tk.Button(form, text="Add Account", bg=_SIDEBAR_ACTIVE,
                  fg="white", font=("Arial", 10, "bold"),
                  activebackground="#16a085", activeforeground="white",
                  cursor="hand2", padx=16, pady=4,
                  command=_add_account).grid(
                      row=2, column=0, columnspan=2,
                      sticky="w", pady=(4, 0))

        # -- Account list ----------------------------------------------------
        tk.Label(wrapper, text="Your Accounts", bg=_CONTENT_BG,
                 fg=_TEXT, font=("Arial", 12, "bold")).pack(
                     anchor="w", pady=(5, 3))

        cols = ("Name", "Type", "Balance", "Transactions")
        tree = ttk.Treeview(wrapper, columns=cols, show="headings", height=8)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=160)
        tree.pack(fill=tk.BOTH, expand=True)

        for acct in self._dm.accounts:
            tree.insert("", "end", values=(
                acct.name,
                acct.account_type,
                f"${acct.balance:,.2f}",
                acct.transaction_count,
            ))

    # ---- Budgets page -----------------------------------------------------

    def _build_budgets(self) -> None:
        wrapper = tk.Frame(self._content, bg=_CONTENT_BG)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # -- Form: grid layout -----------------------------------------------
        form = tk.LabelFrame(wrapper, text=" Set Budget ",
                             bg=_CARD_BG, fg=_TEXT,
                             font=("Arial", 11, "bold"), padx=12, pady=10)
        form.pack(fill=tk.X, pady=(0, 10))

        tk.Label(form, text="Category", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        cat_var = tk.StringVar()
        ttk.Combobox(form, textvariable=cat_var, width=16, state="readonly",
                     values=["Groceries", "Transport", "Dining",
                             "Entertainment", "Utilities", "Rent",
                             "Other"]).grid(
                                 row=1, column=0, sticky="w",
                                 padx=(0, 12), pady=(0, 8))

        tk.Label(form, text="Monthly Limit ($)", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=0, column=1, sticky="w")
        limit_var = tk.StringVar()
        tk.Entry(form, textvariable=limit_var, width=14,
                 **_ENTRY_OPTS).grid(row=1, column=1, sticky="w",
                                     pady=(0, 8))

        def _add_budget() -> None:
            cat = cat_var.get().strip()
            if not cat:
                messagebox.showerror("Error", "Category is required.")
                return
            try:
                lim = float(limit_var.get())
                if lim <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error",
                                     "Limit must be a positive number.")
                return
            current_month = datetime.now().strftime("%Y-%m")
            existing = self._dm.get_budget(cat, current_month)
            if existing:
                existing.monthly_limit = lim
            else:
                self._dm.add_budget(Budget(cat, lim, current_month))
            self._dm.update_budgets_from_transactions()
            self._dm.save()
            self._refresh_page()

        tk.Button(form, text="Set Budget", bg=_SIDEBAR_ACTIVE,
                  fg="white", font=("Arial", 10, "bold"),
                  activebackground="#16a085", activeforeground="white",
                  cursor="hand2", padx=16, pady=4,
                  command=_add_budget).grid(
                      row=2, column=0, columnspan=2,
                      sticky="w", pady=(4, 0))

        # -- Budget status cards ---------------------------------------------
        tk.Label(wrapper, text="Budget Status", bg=_CONTENT_BG,
                 fg=_TEXT, font=("Arial", 12, "bold")).pack(
                     anchor="w", pady=(5, 3))

        for b in self._dm.budgets:
            card = tk.Frame(wrapper, bg=_CARD_BG, relief=tk.RIDGE, bd=1,
                            padx=12, pady=8)
            card.pack(fill=tk.X, pady=3)

            # Top row: category name + status
            top = tk.Frame(card, bg=_CARD_BG)
            top.pack(fill=tk.X)
            tk.Label(top, text=b.category, bg=_CARD_BG, fg=_TEXT,
                     font=("Arial", 11, "bold")).pack(side=tk.LEFT)
            status_colour = {
                "OK": _GREEN, "Warning": _ORANGE, "Over Budget": _RED,
            }[b.status_label()]
            tk.Label(top, text=b.status_label(), bg=_CARD_BG,
                     fg=status_colour,
                     font=("Arial", 10, "bold")).pack(side=tk.RIGHT)

            # Progress bar
            pct = min(b.usage_percent, 100)
            bar_bg = tk.Frame(card, bg="#dcdde1", height=14)
            bar_bg.pack(fill=tk.X, pady=4)
            bar_fill = tk.Frame(bar_bg, bg=status_colour, height=14)
            bar_fill.place(x=0, y=0, relheight=1.0,
                           relwidth=max(pct / 100, 0.01))

            # Info text
            info = (f"Spent: ${b.spent:,.2f} / ${b.monthly_limit:,.2f}"
                    f"     Remaining: ${b.remaining:,.2f}"
                    f"     ({b.usage_percent:.0f}%)")
            tk.Label(card, text=info, bg=_CARD_BG, fg=_TEXT_LIGHT,
                     font=("Arial", 10)).pack(anchor="w")

    # ---- Reports page -----------------------------------------------------

    def _build_reports(self) -> None:
        wrapper = tk.Frame(self._content, bg=_CONTENT_BG)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # -- Filter bar: grid layout -----------------------------------------
        fbar = tk.LabelFrame(wrapper, text=" Filter ", bg=_CARD_BG,
                             fg=_TEXT, font=("Arial", 11, "bold"),
                             padx=12, pady=10)
        fbar.pack(fill=tk.X, pady=(0, 10))

        now = datetime.now()
        years = [str(y) for y in range(2024, now.year + 2)]
        months = [f"{m:02d}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]

        # From date — own row
        tk.Label(fbar, text="From", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        from_frame = tk.Frame(fbar, bg=_CARD_BG)
        from_frame.grid(row=0, column=1, sticky="w", padx=(0, 12))
        s_year = tk.StringVar(value="2026")
        s_month = tk.StringVar(value="01")
        s_day = tk.StringVar(value="01")
        ttk.Combobox(from_frame, textvariable=s_year, width=5,
                     values=years, state="readonly").pack(side=tk.LEFT)
        tk.Label(from_frame, text="-", bg=_CARD_BG, fg=_TEXT).pack(
            side=tk.LEFT)
        ttk.Combobox(from_frame, textvariable=s_month, width=3,
                     values=months, state="readonly").pack(side=tk.LEFT)
        tk.Label(from_frame, text="-", bg=_CARD_BG, fg=_TEXT).pack(
            side=tk.LEFT)
        ttk.Combobox(from_frame, textvariable=s_day, width=3,
                     values=days, state="readonly").pack(side=tk.LEFT)

        # To date — own row
        tk.Label(fbar, text="To", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=1, column=0, sticky="w")
        to_frame = tk.Frame(fbar, bg=_CARD_BG)
        to_frame.grid(row=1, column=1, sticky="w", padx=(0, 12),
                      pady=(6, 0))
        e_year = tk.StringVar(value=str(now.year))
        e_month = tk.StringVar(value=f"{now.month:02d}")
        e_day = tk.StringVar(value=f"{now.day:02d}")
        ttk.Combobox(to_frame, textvariable=e_year, width=5,
                     values=years, state="readonly").pack(side=tk.LEFT)
        tk.Label(to_frame, text="-", bg=_CARD_BG, fg=_TEXT).pack(
            side=tk.LEFT)
        ttk.Combobox(to_frame, textvariable=e_month, width=3,
                     values=months, state="readonly").pack(side=tk.LEFT)
        tk.Label(to_frame, text="-", bg=_CARD_BG, fg=_TEXT).pack(
            side=tk.LEFT)
        ttk.Combobox(to_frame, textvariable=e_day, width=3,
                     values=days, state="readonly").pack(side=tk.LEFT)

        # Category dropdown — same row as To
        tk.Label(fbar, text="Category", bg=_CARD_BG, fg=_TEXT,
                 font=("Arial", 10)).grid(row=0, column=2, sticky="w",
                                          padx=(12, 0))
        cat_var = tk.StringVar(value="All")
        ttk.Combobox(fbar, textvariable=cat_var, width=14, state="readonly",
                     values=["All", "Salary", "Freelance", "Rent",
                             "Groceries", "Transport", "Dining",
                             "Entertainment", "Utilities",
                             "Other"]).grid(
                                 row=0, column=3, sticky="w")

        # Summary text
        summary_label = tk.Label(wrapper, text="", bg=_CONTENT_BG,
                                 fg=_TEXT, font=("Courier", 11),
                                 justify=tk.LEFT, anchor="nw")
        summary_label.pack(fill=tk.X, pady=(0, 5))

        tree_frame = tk.Frame(wrapper, bg=_CONTENT_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        def _apply_filter() -> None:
            report = Report(self._dm.transactions)
            try:
                start_str = f"{s_year.get()}-{s_month.get()}-{s_day.get()}"
                end_str = f"{e_year.get()}-{e_month.get()}-{e_day.get()}"
                start = datetime.strptime(start_str, "%Y-%m-%d")
                end = datetime.strptime(end_str, "%Y-%m-%d").replace(
                    hour=23, minute=59, second=59)
                report.filter_by_date(start, end)
            except ValueError:
                pass
            cat = cat_var.get()
            if cat and cat != "All":
                report.filter_by_category(cat)

            summary_label.configure(text=report.summary_text())

            for w in tree_frame.winfo_children():
                w.destroy()
            tree = self._make_transaction_tree(tree_frame)
            for tx in report.results:
                tag = tx.transaction_type().value
                tree.insert("", "end", values=(
                    tx.date.strftime("%Y-%m-%d"),
                    tx.transaction_type().value.title(),
                    tx.category,
                    f"${tx.amount:,.2f}",
                    tx.summary(),
                ), tags=(tag,))
            tree.tag_configure("income", foreground=_GREEN)
            tree.tag_configure("expense", foreground=_RED)
            tree.tag_configure("transfer", foreground="#2980b9")

        tk.Button(fbar, text="Apply Filter", bg=_SIDEBAR_ACTIVE,
                  fg="white", font=("Arial", 10, "bold"),
                  activebackground="#16a085", activeforeground="white",
                  cursor="hand2", padx=16, pady=4,
                  command=_apply_filter).grid(
                      row=2, column=0, columnspan=2,
                      sticky="w", pady=(8, 0))

        _apply_filter()

    # ================================================================= UTILS

    def _make_transaction_tree(self, parent: tk.Widget) -> ttk.Treeview:
        """Create a standard Treeview for displaying transactions."""
        cols = ("Date", "Type", "Category", "Amount", "Summary")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=10)
        widths = {"Date": 90, "Type": 80, "Category": 100,
                  "Amount": 100, "Summary": 300}
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=widths.get(c, 120), minwidth=60)
        scrollbar = ttk.Scrollbar(parent, orient="vertical",
                                  command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return tree
