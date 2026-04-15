"""
models.py — Core data models for the Personal Finance Tracker.

OOP Concepts Demonstrated:
  - Abstraction: Transaction is an abstract base class (ABC) with abstract methods.
  - Inheritance: Income, Expense, Transfer extend the Transaction base class.
  - Polymorphism: Each subclass implements summary() and apply() differently.
  - Encapsulation: Private attributes (_amount, _balance) with controlled access.
  - Properties: @property decorators for getters and setters with validation.
  - Operator Overloading: __str__, __repr__, __lt__, __eq__, __add__, __radd__,
                          __iter__, __len__, __contains__ (Account).
  - Composition: Account HAS-A list of Transaction objects.
  - Class Methods: Factory method from_dict() to reconstruct objects from dicts.
  - Static Methods: validate_amount() for reusable input validation.
  - Multiple Inheritance / Mixin: SerializableMixin provides to_dict/from_dict.
  - Custom Decorator: @validate_positive for amount parameter validation.
  - Custom Exceptions: InvalidAmountError, InsufficientBalanceError.
  - Iterator Protocol: Account supports for-in loops, len(), and `in` operator.
"""

from __future__ import annotations

import functools
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Iterator, Optional


# ---------------------------------------------------------------------------
# Custom Exceptions  (Custom Exception Hierarchy)
# ---------------------------------------------------------------------------

class FinanceError(Exception):
    """Base exception for all finance-tracker errors."""


class InvalidAmountError(FinanceError):
    """Raised when a monetary amount is invalid (negative, zero, or wrong type)."""

    def __init__(self, amount: object) -> None:
        self.amount = amount
        super().__init__(f"Invalid amount: {amount!r} (must be a positive number)")


class InsufficientBalanceError(FinanceError):
    """Raised when an account does not have enough funds for a withdrawal."""

    def __init__(self, account_name: str, required: float,
                 available: float) -> None:
        self.account_name = account_name
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient balance in '{account_name}': "
            f"need ${required:,.2f}, have ${available:,.2f}")


class InvalidTransactionError(FinanceError):
    """Raised when a transaction fails validation."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Invalid transaction: {reason}")


# ---------------------------------------------------------------------------
# Custom Decorator  (validate_positive)
# ---------------------------------------------------------------------------

def validate_positive(param_name: str):
    """
    Decorator factory that validates a named parameter is a positive number.

    Usage:
        @validate_positive("amount")
        def deposit(self, amount): ...

    Demonstrates: custom decorator (function that returns a decorator).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try keyword arg first, then positional
            if param_name in kwargs:
                value = kwargs[param_name]
            else:
                # Find positional index by inspecting function signature
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        value = args[idx]
                    else:
                        return func(*args, **kwargs)  # let Python handle missing arg
                else:
                    return func(*args, **kwargs)
            if not isinstance(value, (int, float)) or value <= 0:
                raise InvalidAmountError(value)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Mixin — SerializableMixin  (Multiple Inheritance)
# ---------------------------------------------------------------------------

class SerializableMixin:
    """
    Mixin that provides a serialisation interface.

    Any class that inherits from SerializableMixin must implement
    to_dict() and the classmethod from_dict().

    Demonstrates: Multiple Inheritance / Mixin pattern — a class can
    inherit from both a primary base class and this mixin to gain
    serialisation capabilities.
    """

    def to_dict(self) -> dict:
        """Serialise this object to a JSON-compatible dictionary."""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict):
        """Reconstruct an object from a dictionary."""
        raise NotImplementedError

    def to_json_str(self) -> str:
        """Convenience: return a compact JSON string."""
        import json
        return json.dumps(self.to_dict(), default=str)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class TransactionType(Enum):
    """Enumeration for the three kinds of financial transaction."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class AccountType(Enum):
    """Enumeration for supported account types."""
    CASH = "cash"
    BANK = "bank"
    CREDIT_CARD = "credit_card"


# ---------------------------------------------------------------------------
# Abstract Base Class — Transaction  (Abstraction + Mixin)
# ---------------------------------------------------------------------------

class Transaction(ABC, SerializableMixin):
    """
    Abstract base class for all financial transactions.

    Demonstrates:
      - Abstraction via @abstractmethod (summary, transaction_type)
      - Multiple Inheritance: inherits ABC + SerializableMixin
      - Encapsulation via private attributes and @property
      - Operator overloading via __str__, __lt__, __add__
      - Static method for validation
      - Class method as a factory (from_dict)
    """

    _id_counter: int = 0  # class-level auto-increment counter

    def __init__(self, amount: float, category: str,
                 note: str = "", date: datetime | None = None) -> None:
        Transaction.validate_amount(amount)
        Transaction._id_counter += 1
        self._id: int = Transaction._id_counter
        self._amount: float = float(amount)
        self._category: str = category
        self._note: str = note
        self._date: datetime = date or datetime.now()

    # ---- Properties (Encapsulation) ----------------------------------------

    @property
    def id(self) -> int:
        return self._id

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def category(self) -> str:
        return self._category

    @property
    def note(self) -> str:
        return self._note

    @note.setter
    def note(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Note must be a string")
        self._note = value

    @property
    def date(self) -> datetime:
        return self._date

    # ---- Abstract Methods (Abstraction) ------------------------------------

    @abstractmethod
    def summary(self) -> str:
        """Return a human-readable summary.  Each subclass formats it differently."""

    @abstractmethod
    def transaction_type(self) -> TransactionType:
        """Return the TransactionType enum value for this transaction."""

    # ---- Static Method (Validation) ----------------------------------------

    @staticmethod
    def validate_amount(amount: float) -> bool:
        """Validate that *amount* is a positive number."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise InvalidAmountError(amount)
        return True

    # ---- Class Method / Factory (from_dict) --------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """
        Factory that dispatches to the correct subclass based on data['type'].
        """
        type_map = {
            "income": Income,
            "expense": Expense,
            "transfer": Transfer,
        }
        tx_type = data.get("type", "")
        subcls = type_map.get(tx_type)
        if subcls is None:
            raise ValueError(f"Unknown transaction type: {tx_type}")
        return subcls.from_dict(data)

    # ---- Operator Overloading ----------------------------------------------

    def __str__(self) -> str:
        return (f"{self.transaction_type().value.title()}: "
                f"${self._amount:,.2f} [{self._category}] "
                f"on {self._date.strftime('%Y-%m-%d')}")

    def __repr__(self) -> str:
        return (f"{type(self).__name__}(amount={self._amount}, "
                f"category='{self._category}')")

    def __lt__(self, other: "Transaction") -> bool:
        """Compare by date so transactions can be sorted chronologically."""
        if not isinstance(other, Transaction):
            return NotImplemented
        return self._date < other._date

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented
        return self._id == other._id

    def __add__(self, other) -> float:
        """Add two transaction amounts, or a transaction amount and a number."""
        if isinstance(other, Transaction):
            return self._amount + other._amount
        if isinstance(other, (int, float)):
            return self._amount + other
        return NotImplemented

    def __radd__(self, other) -> float:
        """Support sum() which starts with 0 + Transaction."""
        if isinstance(other, (int, float)):
            return other + self._amount
        return NotImplemented

    # ---- Serialisation -----------------------------------------------------

    def to_dict(self) -> dict:
        """Convert to a JSON-serialisable dictionary."""
        return {
            "id": self._id,
            "type": self.transaction_type().value,
            "amount": self._amount,
            "category": self._category,
            "note": self._note,
            "date": self._date.isoformat(),
        }

    @classmethod
    def set_id_counter(cls, value: int) -> None:
        """Restore the counter after loading persisted data."""
        cls._id_counter = value


# ---------------------------------------------------------------------------
# Concrete Subclass — Income  (Inheritance + Polymorphism)
# ---------------------------------------------------------------------------

class Income(Transaction):
    """
    Represents money received (salary, freelance, interest, etc.).
    Inherits from Transaction and provides its own summary() implementation.
    """

    def __init__(self, amount: float, category: str, source: str = "",
                 note: str = "", date: datetime | None = None) -> None:
        super().__init__(amount, category, note, date)
        self._source: str = source

    @property
    def source(self) -> str:
        return self._source

    # ---- Polymorphism: summary() unique to Income --------------------------

    def transaction_type(self) -> TransactionType:
        return TransactionType.INCOME

    def summary(self) -> str:
        src = f" from {self._source}" if self._source else ""
        return f"Income of ${self._amount:,.2f}{src} [{self._category}]"

    # ---- Factory -----------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "Income":
        obj = cls(
            amount=data["amount"],
            category=data["category"],
            source=data.get("source", ""),
            note=data.get("note", ""),
            date=datetime.fromisoformat(data["date"]) if "date" in data else None,
        )
        if "id" in data:
            obj._id = data["id"]
        return obj

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["source"] = self._source
        return d


# ---------------------------------------------------------------------------
# Concrete Subclass — Expense  (Inheritance + Polymorphism)
# ---------------------------------------------------------------------------

class Expense(Transaction):
    """
    Represents money spent (groceries, rent, entertainment, etc.).
    """

    def __init__(self, amount: float, category: str, payee: str = "",
                 note: str = "", date: datetime | None = None) -> None:
        super().__init__(amount, category, note, date)
        self._payee: str = payee

    @property
    def payee(self) -> str:
        return self._payee

    def transaction_type(self) -> TransactionType:
        return TransactionType.EXPENSE

    def summary(self) -> str:
        pay = f" to {self._payee}" if self._payee else ""
        return f"Expense of ${self._amount:,.2f}{pay} [{self._category}]"

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        obj = cls(
            amount=data["amount"],
            category=data["category"],
            payee=data.get("payee", ""),
            note=data.get("note", ""),
            date=datetime.fromisoformat(data["date"]) if "date" in data else None,
        )
        if "id" in data:
            obj._id = data["id"]
        return obj

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["payee"] = self._payee
        return d


# ---------------------------------------------------------------------------
# Concrete Subclass — Transfer  (Inheritance + Polymorphism)
# ---------------------------------------------------------------------------

class Transfer(Transaction):
    """
    Represents money moved between two accounts owned by the user.
    """

    def __init__(self, amount: float, from_account: str, to_account: str,
                 note: str = "", date: datetime | None = None) -> None:
        super().__init__(amount, "Transfer", note, date)
        self._from_account: str = from_account
        self._to_account: str = to_account

    @property
    def from_account(self) -> str:
        return self._from_account

    @property
    def to_account(self) -> str:
        return self._to_account

    def transaction_type(self) -> TransactionType:
        return TransactionType.TRANSFER

    def summary(self) -> str:
        return (f"Transfer of ${self._amount:,.2f} "
                f"from {self._from_account} to {self._to_account}")

    @classmethod
    def from_dict(cls, data: dict) -> "Transfer":
        obj = cls(
            amount=data["amount"],
            from_account=data["from_account"],
            to_account=data["to_account"],
            note=data.get("note", ""),
            date=datetime.fromisoformat(data["date"]) if "date" in data else None,
        )
        if "id" in data:
            obj._id = data["id"]
        return obj

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["from_account"] = self._from_account
        d["to_account"] = self._to_account
        return d


# ---------------------------------------------------------------------------
# Account  (Composition — Account HAS-A list of Transactions)
# ---------------------------------------------------------------------------

class Account(SerializableMixin):
    """
    A financial account (cash, bank, credit card).

    Demonstrates:
      - Composition: an Account *contains* Transaction objects.
      - Iterator Protocol: __iter__, __len__, __contains__ let you
        write ``for tx in account``, ``len(account)``, ``tx in account``.
      - Multiple Inheritance: inherits SerializableMixin.
      - Custom Decorator: deposit/withdraw use @validate_positive.
    """

    def __init__(self, name: str, account_type: str = "bank",
                 balance: float = 0.0) -> None:
        self._name: str = name
        self._account_type: str = account_type
        self._balance: float = float(balance)
        self._transactions: list[Transaction] = []  # Composition

    # ---- Properties --------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def account_type(self) -> str:
        return self._account_type

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def transactions(self) -> list[Transaction]:
        """Return a shallow copy to prevent external mutation."""
        return list(self._transactions)

    @property
    def transaction_count(self) -> int:
        return len(self._transactions)

    # ---- Mutators ----------------------------------------------------------

    def add_transaction(self, transaction: Transaction) -> None:
        """Record a transaction and update the running balance."""
        self._transactions.append(transaction)
        if isinstance(transaction, Income):
            self._balance += transaction.amount
        elif isinstance(transaction, Expense):
            self._balance -= transaction.amount
        elif isinstance(transaction, Transfer):
            if transaction.from_account == self._name:
                self._balance -= transaction.amount
            elif transaction.to_account == self._name:
                self._balance += transaction.amount

    @validate_positive("amount")
    def deposit(self, amount: float) -> None:
        """Deposit money directly (uses @validate_positive decorator)."""
        self._balance += amount

    @validate_positive("amount")
    def withdraw(self, amount: float) -> None:
        """Withdraw money with balance check (uses @validate_positive decorator)."""
        if amount > self._balance:
            raise InsufficientBalanceError(self._name, amount, self._balance)
        self._balance -= amount

    def get_sorted_transactions(self) -> list[Transaction]:
        """Return transactions sorted by date (uses Transaction.__lt__)."""
        return sorted(self._transactions)

    # ---- Iterator Protocol -------------------------------------------------

    def __iter__(self) -> Iterator[Transaction]:
        """Allow ``for tx in account:`` — iterates over transactions."""
        return iter(self._transactions)

    def __len__(self) -> int:
        """Allow ``len(account)`` — returns number of transactions."""
        return len(self._transactions)

    def __contains__(self, item: object) -> bool:
        """Allow ``tx in account`` — checks if a transaction belongs here."""
        return item in self._transactions

    # ---- Operator Overloading ----------------------------------------------

    def __str__(self) -> str:
        return (f"{self._name} ({self._account_type}) — "
                f"balance: ${self._balance:,.2f}")

    def __repr__(self) -> str:
        return (f"Account(name='{self._name}', type='{self._account_type}', "
                f"balance={self._balance:.2f})")

    # ---- Serialisation (from SerializableMixin) ----------------------------

    def to_dict(self) -> dict:
        return {
            "name": self._name,
            "account_type": self._account_type,
            "balance": self._balance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        return cls(
            name=data["name"],
            account_type=data.get("account_type", "bank"),
            balance=data.get("balance", 0.0),
        )


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class Budget(SerializableMixin):
    """
    Monthly spending limit for a specific category.
    Tracks how much has been spent and warns when nearing the limit.
    """

    def __init__(self, category: str, monthly_limit: float,
                 month: str | None = None) -> None:
        self._category: str = category
        self._monthly_limit: float = float(monthly_limit)
        self._month: str = month or datetime.now().strftime("%Y-%m")
        self._spent: float = 0.0

    # ---- Properties --------------------------------------------------------

    @property
    def category(self) -> str:
        return self._category

    @property
    def monthly_limit(self) -> float:
        return self._monthly_limit

    @monthly_limit.setter
    def monthly_limit(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Monthly limit must be a positive number")
        self._monthly_limit = float(value)

    @property
    def spent(self) -> float:
        return self._spent

    @property
    def remaining(self) -> float:
        return max(self._monthly_limit - self._spent, 0.0)

    @property
    def month(self) -> str:
        return self._month

    @property
    def usage_percent(self) -> float:
        """Percentage of the budget already used (0–100+)."""
        if self._monthly_limit == 0:
            return 0.0
        return (self._spent / self._monthly_limit) * 100

    # ---- Logic -------------------------------------------------------------

    def record_expense(self, amount: float) -> None:
        """Add an expense amount to the running total."""
        self._spent += amount

    def is_over_budget(self) -> bool:
        return self._spent > self._monthly_limit

    def is_near_limit(self, threshold: float = 0.8) -> bool:
        """Return True when spending reaches *threshold* (default 80 %)."""
        return self.usage_percent >= threshold * 100

    def status_label(self) -> str:
        """Return a short label: OK / Warning / Over Budget."""
        if self.is_over_budget():
            return "Over Budget"
        if self.is_near_limit():
            return "Warning"
        return "OK"

    # ---- Operator Overloading ----------------------------------------------

    def __str__(self) -> str:
        return (f"Budget({self._category}: "
                f"${self._spent:,.2f} / ${self._monthly_limit:,.2f} "
                f"[{self._month}])")

    def __repr__(self) -> str:
        return self.__str__()

    # ---- Serialisation -----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "category": self._category,
            "monthly_limit": self._monthly_limit,
            "month": self._month,
            "spent": self._spent,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        budget = cls(
            category=data["category"],
            monthly_limit=data["monthly_limit"],
            month=data.get("month"),
        )
        budget._spent = data.get("spent", 0.0)
        return budget
