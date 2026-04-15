"""
tests.py — Comprehensive test suite for the Personal Finance Tracker.

Demonstrates all OOP concepts through test cases with clear assertions.
Run with:  python tests.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

from models import (
    Account,
    Budget,
    Expense,
    FinanceError,
    Income,
    InsufficientBalanceError,
    InvalidAmountError,
    InvalidTransactionError,
    SerializableMixin,
    Transaction,
    TransactionType,
    Transfer,
    validate_positive,
)
from data_manager import DataManager
from reports import Report

# Track test results
_passed = 0
_failed = 0


def _test(name: str, condition: bool, detail: str = "") -> None:
    """Helper: record a PASS or FAIL for one assertion."""
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        msg = f" — {detail}" if detail else ""
        print(f"  FAIL  {name}{msg}")


# =========================================================================
# 1. Abstraction — ABC cannot be instantiated directly
# =========================================================================
def test_abstraction() -> None:
    print("\n--- Abstraction (ABC) ---")
    try:
        Transaction(100, "Test")  # type: ignore[abstract]
        _test("Cannot instantiate abstract Transaction", False)
    except TypeError:
        _test("Cannot instantiate abstract Transaction", True)

    # Concrete subclasses CAN be instantiated
    inc = Income(100, "Salary")
    _test("Income (concrete subclass) can be created", isinstance(inc, Transaction))
    _test("Income has abstract method summary()", callable(getattr(inc, "summary")))
    _test("Income has abstract method transaction_type()",
          callable(getattr(inc, "transaction_type")))


# =========================================================================
# 2. Inheritance — subclass relationships
# =========================================================================
def test_inheritance() -> None:
    print("\n--- Inheritance ---")
    inc = Income(500, "Salary", source="Company")
    exp = Expense(50, "Food", payee="Restaurant")
    tfr = Transfer(200, "Bank", "Cash")

    _test("Income is a Transaction", isinstance(inc, Transaction))
    _test("Expense is a Transaction", isinstance(exp, Transaction))
    _test("Transfer is a Transaction", isinstance(tfr, Transaction))

    # Each subclass has its own unique attributes
    _test("Income has 'source' attribute", hasattr(inc, "source"))
    _test("Expense has 'payee' attribute", hasattr(exp, "payee"))
    _test("Transfer has 'from_account'", hasattr(tfr, "from_account"))
    _test("Transfer has 'to_account'", hasattr(tfr, "to_account"))


# =========================================================================
# 3. Polymorphism — same method, different behaviour
# =========================================================================
def test_polymorphism() -> None:
    print("\n--- Polymorphism ---")
    inc = Income(1000, "Salary", source="Corp")
    exp = Expense(200, "Rent", payee="Landlord")
    tfr = Transfer(300, "Bank", "Cash")

    # summary() returns different strings per type
    _test("Income.summary() mentions 'Income'",
          "Income" in inc.summary())
    _test("Expense.summary() mentions 'Expense'",
          "Expense" in exp.summary())
    _test("Transfer.summary() mentions 'Transfer'",
          "Transfer" in tfr.summary())

    # transaction_type() returns different enum values
    _test("Income type is INCOME",
          inc.transaction_type() == TransactionType.INCOME)
    _test("Expense type is EXPENSE",
          exp.transaction_type() == TransactionType.EXPENSE)
    _test("Transfer type is TRANSFER",
          tfr.transaction_type() == TransactionType.TRANSFER)

    # Polymorphic collection — can treat all uniformly
    txns: list[Transaction] = [inc, exp, tfr]
    summaries = [t.summary() for t in txns]
    _test("Polymorphic iteration produces 3 summaries", len(summaries) == 3)


# =========================================================================
# 4. Encapsulation — private attrs + property access
# =========================================================================
def test_encapsulation() -> None:
    print("\n--- Encapsulation ---")
    inc = Income(500, "Salary")

    # Properties expose read access
    _test("amount property works", inc.amount == 500.0)
    _test("category property works", inc.category == "Salary")

    # Private attributes exist with underscore prefix
    _test("_amount is private", hasattr(inc, "_amount"))
    _test("_category is private", hasattr(inc, "_category"))

    # note has both getter and setter
    inc.note = "Updated"
    _test("note setter works", inc.note == "Updated")

    # Setter validates type
    try:
        inc.note = 12345  # type: ignore[assignment]
        _test("note setter rejects non-string", False)
    except TypeError:
        _test("note setter rejects non-string", True)

    # Budget limit setter validates positive
    b = Budget("Food", 500)
    try:
        b.monthly_limit = -100
        _test("Budget setter rejects negative", False)
    except ValueError:
        _test("Budget setter rejects negative", True)


# =========================================================================
# 5. Operator Overloading
# =========================================================================
def test_operator_overloading() -> None:
    print("\n--- Operator Overloading ---")
    tx1 = Income(100, "A", date=datetime(2026, 1, 1))
    tx2 = Expense(200, "B", date=datetime(2026, 1, 2))
    tx3 = Income(300, "C", date=datetime(2026, 1, 3))

    # __str__
    _test("__str__ returns readable string", "$" in str(tx1))

    # __repr__
    _test("__repr__ contains class name", "Income" in repr(tx1))

    # __lt__ — sort by date
    _test("tx1 < tx2 (earlier date)", tx1 < tx2)
    _test("not tx2 < tx1", not (tx2 < tx1))
    sorted_txs = sorted([tx3, tx1, tx2])
    _test("sorted() uses __lt__ correctly",
          [t.amount for t in sorted_txs] == [100, 200, 300])

    # __eq__ — by id
    _test("tx1 == tx1", tx1 == tx1)
    _test("tx1 != tx2", tx1 != tx2)

    # __add__ — add amounts
    _test("tx1 + tx2 == 300.0", tx1 + tx2 == 300.0)
    _test("tx1 + 50 == 150.0", tx1 + 50 == 150.0)

    # __radd__ — supports sum()
    total = sum([tx1, tx2, tx3])
    _test("sum([tx1, tx2, tx3]) == 600.0", total == 600.0)


# =========================================================================
# 6. Composition — Account contains Transactions
# =========================================================================
def test_composition() -> None:
    print("\n--- Composition ---")
    acct = Account("Bank", "bank", 1000)
    inc = Income(500, "Salary")
    exp = Expense(200, "Food")

    acct.add_transaction(inc)
    acct.add_transaction(exp)

    _test("Account holds 2 transactions", acct.transaction_count == 2)
    _test("Balance updated: 1000 + 500 - 200 = 1300",
          acct.balance == 1300.0)
    _test("transactions property returns a copy",
          acct.transactions is not acct._transactions)


# =========================================================================
# 7. Class Methods — factory from_dict()
# =========================================================================
def test_class_methods() -> None:
    print("\n--- Class Methods (Factory) ---")
    inc = Income(500, "Salary", source="Corp", note="Pay day",
                 date=datetime(2026, 4, 1))
    data = inc.to_dict()
    rebuilt = Transaction.from_dict(data)

    _test("from_dict returns Income instance", isinstance(rebuilt, Income))
    _test("Rebuilt amount matches", rebuilt.amount == 500.0)
    _test("Rebuilt category matches", rebuilt.category == "Salary")

    # Expense factory
    exp = Expense(100, "Food", payee="Cafe")
    exp_data = exp.to_dict()
    rebuilt_exp = Transaction.from_dict(exp_data)
    _test("Expense factory works", isinstance(rebuilt_exp, Expense))

    # Unknown type raises ValueError
    try:
        Transaction.from_dict({"type": "unknown"})
        _test("Unknown type raises error", False)
    except ValueError:
        _test("Unknown type raises error", True)


# =========================================================================
# 8. Static Methods — validate_amount()
# =========================================================================
def test_static_methods() -> None:
    print("\n--- Static Methods ---")
    _test("validate_amount(100) returns True",
          Transaction.validate_amount(100) is True)

    try:
        Transaction.validate_amount(-50)
        _test("validate_amount(-50) raises InvalidAmountError", False)
    except InvalidAmountError:
        _test("validate_amount(-50) raises InvalidAmountError", True)

    try:
        Transaction.validate_amount(0)
        _test("validate_amount(0) raises InvalidAmountError", False)
    except InvalidAmountError:
        _test("validate_amount(0) raises InvalidAmountError", True)

    try:
        Transaction.validate_amount("abc")  # type: ignore
        _test("validate_amount('abc') raises InvalidAmountError", False)
    except InvalidAmountError:
        _test("validate_amount('abc') raises InvalidAmountError", True)


# =========================================================================
# 9. Custom Exceptions
# =========================================================================
def test_custom_exceptions() -> None:
    print("\n--- Custom Exceptions ---")

    # InvalidAmountError is a FinanceError
    err = InvalidAmountError(-5)
    _test("InvalidAmountError is a FinanceError", isinstance(err, FinanceError))
    _test("InvalidAmountError stores the bad amount", err.amount == -5)

    # InsufficientBalanceError
    acct = Account("Test", "bank", 100)
    try:
        acct.withdraw(500)
        _test("withdraw() raises InsufficientBalanceError", False)
    except InsufficientBalanceError as e:
        _test("withdraw() raises InsufficientBalanceError", True)
        _test("Error stores account name", e.account_name == "Test")
        _test("Error stores required amount", e.required == 500)
        _test("Error stores available amount", e.available == 100)

    # InvalidTransactionError
    err2 = InvalidTransactionError("missing fields")
    _test("InvalidTransactionError stores reason",
          err2.reason == "missing fields")


# =========================================================================
# 10. Custom Decorator — @validate_positive
# =========================================================================
def test_custom_decorator() -> None:
    print("\n--- Custom Decorator (@validate_positive) ---")
    acct = Account("Wallet", "cash", 500)

    # Valid deposit
    acct.deposit(100)
    _test("deposit(100) works, balance = 600", acct.balance == 600.0)

    # Invalid deposit
    try:
        acct.deposit(-50)
        _test("deposit(-50) raises InvalidAmountError", False)
    except InvalidAmountError:
        _test("deposit(-50) raises InvalidAmountError", True)

    # Valid withdraw
    acct.withdraw(200)
    _test("withdraw(200) works, balance = 400", acct.balance == 400.0)

    # Withdraw too much
    try:
        acct.withdraw(9999)
        _test("withdraw(9999) raises InsufficientBalanceError", False)
    except InsufficientBalanceError:
        _test("withdraw(9999) raises InsufficientBalanceError", True)


# =========================================================================
# 11. Multiple Inheritance / Mixin — SerializableMixin
# =========================================================================
def test_mixin() -> None:
    print("\n--- Multiple Inheritance (SerializableMixin) ---")
    inc = Income(500, "Salary", source="Corp")
    acct = Account("Bank", "bank", 1000)
    budget = Budget("Food", 300)

    # All three classes inherit SerializableMixin
    _test("Income is a SerializableMixin", isinstance(inc, SerializableMixin))
    _test("Account is a SerializableMixin", isinstance(acct, SerializableMixin))
    _test("Budget is a SerializableMixin", isinstance(budget, SerializableMixin))

    # to_json_str() comes from the mixin
    json_str = inc.to_json_str()
    _test("to_json_str() returns valid JSON",
          isinstance(json.loads(json_str), dict))

    # MRO shows multiple bases
    mro = [c.__name__ for c in type(inc).__mro__]
    _test("Income MRO includes Transaction", "Transaction" in mro)
    _test("Income MRO includes SerializableMixin", "SerializableMixin" in mro)
    _test("Income MRO includes ABC", "ABC" in mro)


# =========================================================================
# 12. Iterator Protocol — Account
# =========================================================================
def test_iterator_protocol() -> None:
    print("\n--- Iterator Protocol (Account) ---")
    acct = Account("Bank", "bank", 0)
    tx1 = Income(100, "A")
    tx2 = Expense(50, "B")
    tx3 = Income(200, "C")
    acct.add_transaction(tx1)
    acct.add_transaction(tx2)
    acct.add_transaction(tx3)

    # __len__
    _test("len(account) == 3", len(acct) == 3)

    # __iter__ — for loop
    items = [tx for tx in acct]
    _test("for tx in account yields 3 items", len(items) == 3)

    # __contains__ — `in` operator
    _test("tx1 in account is True", tx1 in acct)
    other_tx = Income(999, "Z")
    _test("other_tx not in account", other_tx not in acct)


# =========================================================================
# 13. Context Manager — DataManager
# =========================================================================
def test_context_manager() -> None:
    print("\n--- Context Manager (DataManager) ---")
    test_path = "/tmp/test_ctx_manager.json"

    # Clean up from previous runs
    if os.path.exists(test_path):
        os.remove(test_path)

    # Create data with a regular call first
    dm = DataManager(test_path)
    dm.create_sample_data()

    # Use as context manager — should auto-load and auto-save
    with DataManager(test_path) as dm2:
        _test("__enter__ loads data", len(dm2.transactions) > 0)
        count_before = len(dm2.transactions)
        dm2.add_transaction(Expense(25, "Snack", payee="Vending"))
        _test("Can add transaction inside context",
              len(dm2.transactions) == count_before + 1)

    # After exiting, file should be saved — verify by loading again
    dm3 = DataManager(test_path)
    dm3.load()
    _test("__exit__ auto-saved (data persisted)",
          len(dm3.transactions) == count_before + 1)

    os.remove(test_path)


# =========================================================================
# 14. Data Persistence — save / load round-trip
# =========================================================================
def test_persistence() -> None:
    print("\n--- Data Persistence ---")
    test_path = "/tmp/test_persistence.json"

    dm = DataManager(test_path)
    dm.create_sample_data()

    dm2 = DataManager(test_path)
    loaded = dm2.load()
    _test("load() returns True for existing file", loaded is True)
    _test("8 transactions loaded", len(dm2.transactions) == 8)
    _test("3 accounts loaded", len(dm2.accounts) == 3)
    _test("4 budgets loaded", len(dm2.budgets) == 4)

    # Verify transaction types restored correctly
    incomes = [t for t in dm2.transactions if isinstance(t, Income)]
    expenses = [t for t in dm2.transactions if isinstance(t, Expense)]
    transfers = [t for t in dm2.transactions if isinstance(t, Transfer)]
    _test("2 Income transactions", len(incomes) == 2)
    _test("5 Expense transactions", len(expenses) == 5)
    _test("1 Transfer transaction", len(transfers) == 1)

    # Non-existent file
    dm3 = DataManager("/tmp/nonexistent_12345.json")
    _test("load() returns False for missing file", dm3.load() is False)

    os.remove(test_path)


# =========================================================================
# 15. Reports — filtering and statistics
# =========================================================================
def test_reports() -> None:
    print("\n--- Reports (Filtering & Statistics) ---")
    test_path = "/tmp/test_reports.json"
    dm = DataManager(test_path)
    dm.create_sample_data()
    dm2 = DataManager(test_path)
    dm2.load()

    report = Report(dm2.transactions)
    _test("total_income() == 5200", report.total_income() == 5200.0)
    _test("total_expense() == 1810", report.total_expense() == 1810.0)
    _test("net_amount() == 3390", report.net_amount() == 3390.0)
    _test("count == 8", report.count == 8)

    # Filter by category
    r2 = Report(dm2.transactions)
    r2.filter_by_category("Groceries")
    _test("Filter by Groceries: 1 result", r2.count == 1)
    _test("Groceries total: $350", r2.total_expense() == 350.0)

    # Filter by date
    r3 = Report(dm2.transactions)
    r3.filter_by_date(datetime(2026, 4, 5), datetime(2026, 4, 8, 23, 59))
    _test("Date filter Apr 5-8: 4 transactions", r3.count == 4)

    # Filter by type
    r4 = Report(dm2.transactions)
    r4.filter_by_type(TransactionType.INCOME)
    _test("Filter by INCOME: 2 results", r4.count == 2)

    # Category breakdown
    r5 = Report(dm2.transactions)
    breakdown = r5.category_breakdown()
    _test("Breakdown has Rent category", "Rent" in breakdown)
    _test("Rent total is 1200", breakdown.get("Rent") == 1200.0)

    # Reset filter
    r5.reset_filters()
    _test("reset_filters restores all", r5.count == 8)

    os.remove(test_path)


# =========================================================================
# 16. Budget logic
# =========================================================================
def test_budget() -> None:
    print("\n--- Budget ---")
    b = Budget("Food", 500)

    _test("Initial spent is 0", b.spent == 0.0)
    _test("Remaining is 500", b.remaining == 500.0)
    _test("Usage is 0%", b.usage_percent == 0.0)
    _test("Status is OK", b.status_label() == "OK")

    b.record_expense(400)
    _test("After $400: usage = 80%", b.usage_percent == 80.0)
    _test("Near limit at 80%", b.is_near_limit())
    _test("Status is Warning", b.status_label() == "Warning")

    b.record_expense(200)
    _test("After $600 total: over budget", b.is_over_budget())
    _test("Status is Over Budget", b.status_label() == "Over Budget")
    _test("Remaining is 0 (capped)", b.remaining == 0.0)


# =========================================================================
# Main — run all tests
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Personal Finance Tracker — Test Suite")
    print("=" * 60)

    test_abstraction()
    test_inheritance()
    test_polymorphism()
    test_encapsulation()
    test_operator_overloading()
    test_composition()
    test_class_methods()
    test_static_methods()
    test_custom_exceptions()
    test_custom_decorator()
    test_mixin()
    test_iterator_protocol()
    test_context_manager()
    test_persistence()
    test_reports()
    test_budget()

    print("\n" + "=" * 60)
    print(f"Results: {_passed} passed, {_failed} failed, "
          f"{_passed + _failed} total")
    print("=" * 60)

    if _failed > 0:
        sys.exit(1)
