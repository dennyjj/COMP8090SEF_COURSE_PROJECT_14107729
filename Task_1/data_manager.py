"""
data_manager.py — Persistent storage layer using JSON files.

Handles saving and loading of accounts, transactions, and budgets.
Demonstrates encapsulation of file I/O behind a clean interface so that
the rest of the application never touches the file system directly.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

from models import (
    Account,
    Budget,
    Expense,
    Income,
    Transaction,
    Transfer,
)

# Default data file placed next to the Python scripts
_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_PATH = os.path.join(_DATA_DIR, "data.json")


class DataManager:
    """
    Centralised read / write access for all application data.

    Internally stores three collections:
      - accounts   (list[Account])
      - transactions (list[Transaction])
      - budgets    (list[Budget])

    Supports the Context Manager protocol so it can be used as:
        with DataManager("data.json") as dm:
            dm.add_transaction(...)
        # auto-saves on exit
    """

    def __init__(self, filepath: str = _DEFAULT_PATH) -> None:
        self._filepath: str = filepath
        self._accounts: list[Account] = []
        self._transactions: list[Transaction] = []
        self._budgets: list[Budget] = []

    # ---- Context Manager Protocol ------------------------------------------

    def __enter__(self) -> "DataManager":
        """Load data when entering the context."""
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Auto-save data when exiting the context (even on exception)."""
        self.save()
        return False  # do not suppress exceptions

    # ---- Public accessors --------------------------------------------------

    @property
    def accounts(self) -> list[Account]:
        return list(self._accounts)

    @property
    def transactions(self) -> list[Transaction]:
        return list(self._transactions)

    @property
    def budgets(self) -> list[Budget]:
        return list(self._budgets)

    # ---- Account operations ------------------------------------------------

    def add_account(self, account: Account) -> None:
        self._accounts.append(account)

    def get_account(self, name: str) -> Account | None:
        for acct in self._accounts:
            if acct.name == name:
                return acct
        return None

    def get_account_names(self) -> list[str]:
        return [a.name for a in self._accounts]

    # ---- Transaction operations --------------------------------------------

    def add_transaction(self, transaction: Transaction) -> None:
        """Record a transaction globally and in the relevant account(s)."""
        self._transactions.append(transaction)

        if isinstance(transaction, Income):
            acct = self.get_account(transaction.category)
            # If no matching account, try the first one
            for a in self._accounts:
                a_name = a.name
                # Income: add to the account that receives it
                # We use a convention: income is added to the first account
                # unless explicitly routed
                break

        if isinstance(transaction, Transfer):
            src = self.get_account(transaction.from_account)
            dst = self.get_account(transaction.to_account)
            if src:
                src.add_transaction(transaction)
            if dst:
                dst.add_transaction(transaction)
        else:
            # For income/expense, add to every account so they can filter locally.
            # In practice we keep a flat global list; account balances are
            # recalculated on load.
            pass

    def get_transactions_sorted(self) -> list[Transaction]:
        """Return all transactions sorted by date (newest first)."""
        return sorted(self._transactions, reverse=True)

    # ---- Budget operations -------------------------------------------------

    def add_budget(self, budget: Budget) -> None:
        self._budgets.append(budget)

    def get_budget(self, category: str, month: str | None = None) -> Budget | None:
        month = month or datetime.now().strftime("%Y-%m")
        for b in self._budgets:
            if b.category == category and b.month == month:
                return b
        return None

    def update_budgets_from_transactions(self) -> None:
        """Recalculate budget spent amounts from the transaction list."""
        current_month = datetime.now().strftime("%Y-%m")
        # Reset spent
        for b in self._budgets:
            if b.month == current_month:
                b._spent = 0.0
        # Accumulate expenses
        for tx in self._transactions:
            if isinstance(tx, Expense):
                tx_month = tx.date.strftime("%Y-%m")
                budget = self.get_budget(tx.category, tx_month)
                if budget:
                    budget.record_expense(tx.amount)

    # ---- Persistence -------------------------------------------------------

    def save(self) -> None:
        """Serialise all data to a JSON file."""
        data = {
            "accounts": [a.to_dict() for a in self._accounts],
            "transactions": [t.to_dict() for t in self._transactions],
            "budgets": [b.to_dict() for b in self._budgets],
            "meta": {
                "last_saved": datetime.now().isoformat(),
                "id_counter": Transaction._id_counter,
            },
        }
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self) -> bool:
        """
        Load data from the JSON file.  Returns True on success,
        False if the file does not exist (caller may create sample data).
        """
        if not os.path.exists(self._filepath):
            return False

        with open(self._filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Restore ID counter first so new objects don't collide
        meta = data.get("meta", {})
        Transaction.set_id_counter(meta.get("id_counter", 0))

        # Accounts
        self._accounts = [
            Account.from_dict(a) for a in data.get("accounts", [])
        ]

        # Transactions (uses the factory on Transaction base class)
        self._transactions = [
            Transaction.from_dict(t) for t in data.get("transactions", [])
        ]

        # Budgets
        self._budgets = [
            Budget.from_dict(b) for b in data.get("budgets", [])
        ]

        # Link transactions to their accounts and recalc balances
        self._rebuild_account_balances()

        return True

    # ---- Helpers -----------------------------------------------------------

    def _rebuild_account_balances(self) -> None:
        """After loading, reset account balances and replay transactions."""
        # Reset balances
        for acct in self._accounts:
            acct._balance = 0.0
            acct._transactions = []

        for tx in self._transactions:
            if isinstance(tx, Income):
                # Income goes to the first account by default
                if self._accounts:
                    self._accounts[0].add_transaction(tx)
            elif isinstance(tx, Expense):
                if self._accounts:
                    self._accounts[0].add_transaction(tx)
            elif isinstance(tx, Transfer):
                src = self.get_account(tx.from_account)
                dst = self.get_account(tx.to_account)
                if src:
                    src.add_transaction(tx)
                if dst:
                    dst.add_transaction(tx)

    def create_sample_data(self) -> None:
        """Populate the store with demonstration data for first-time use."""
        # Accounts
        self._accounts = [
            Account("Cash", "cash", 0.0),
            Account("Bank", "bank", 0.0),
            Account("Credit Card", "credit_card", 0.0),
        ]

        # Sample transactions
        samples: list[Transaction] = [
            Income(5000.00, "Salary", source="Company Ltd",
                   note="Monthly salary",
                   date=datetime(2026, 4, 1)),
            Income(200.00, "Freelance", source="Client A",
                   note="Logo design",
                   date=datetime(2026, 4, 3)),
            Expense(1200.00, "Rent", payee="Landlord",
                    note="April rent",
                    date=datetime(2026, 4, 1)),
            Expense(350.00, "Groceries", payee="Supermarket",
                    note="Weekly groceries",
                    date=datetime(2026, 4, 5)),
            Expense(60.00, "Transport", payee="MTR",
                    note="Octopus top-up",
                    date=datetime(2026, 4, 6)),
            Expense(120.00, "Entertainment", payee="Cinema",
                    note="Movie night",
                    date=datetime(2026, 4, 7)),
            Expense(80.00, "Dining", payee="Restaurant",
                    note="Dinner with friends",
                    date=datetime(2026, 4, 8)),
            Transfer(500.00, "Bank", "Cash",
                     note="ATM withdrawal",
                     date=datetime(2026, 4, 2)),
        ]

        self._transactions = samples

        # Replay transactions into accounts
        self._rebuild_account_balances()

        # Sample budgets for current month
        current_month = datetime.now().strftime("%Y-%m")
        self._budgets = [
            Budget("Groceries", 600.00, current_month),
            Budget("Entertainment", 200.00, current_month),
            Budget("Dining", 300.00, current_month),
            Budget("Transport", 150.00, current_month),
        ]

        # Recalculate budget spent
        self.update_budgets_from_transactions()

        # Persist immediately
        self.save()
