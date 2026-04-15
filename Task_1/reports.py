"""
reports.py — Reporting, filtering, and statistical analysis.

Provides functions to filter transactions by date range, category, or type,
and to compute summary statistics (totals, breakdowns, averages).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from models import Expense, Income, Transaction, TransactionType, Transfer


class Report:
    """
    Generates filtered views and statistics over a list of transactions.

    Usage:
        report = Report(all_transactions)
        report.filter_by_date(start, end)
        report.filter_by_category("Groceries")
        print(report.total_income())
    """

    def __init__(self, transactions: list[Transaction]) -> None:
        self._all: list[Transaction] = list(transactions)
        self._filtered: list[Transaction] = list(transactions)

    # ---- Filtering ---------------------------------------------------------

    def reset_filters(self) -> None:
        """Remove all filters and restore the full transaction list."""
        self._filtered = list(self._all)

    def filter_by_date(self, start: datetime | None = None,
                       end: datetime | None = None) -> "Report":
        """Keep only transactions within [start, end]."""
        if start:
            self._filtered = [
                t for t in self._filtered if t.date >= start
            ]
        if end:
            self._filtered = [
                t for t in self._filtered if t.date <= end
            ]
        return self

    def filter_by_category(self, category: str) -> "Report":
        """Keep only transactions matching the given category."""
        self._filtered = [
            t for t in self._filtered if t.category == category
        ]
        return self

    def filter_by_type(self, tx_type: TransactionType) -> "Report":
        """Keep only transactions of a specific type (income/expense/transfer)."""
        self._filtered = [
            t for t in self._filtered
            if t.transaction_type() == tx_type
        ]
        return self

    # ---- Accessors ---------------------------------------------------------

    @property
    def results(self) -> list[Transaction]:
        """Return the current filtered list sorted newest-first."""
        return sorted(self._filtered, reverse=True)

    @property
    def count(self) -> int:
        return len(self._filtered)

    # ---- Aggregation -------------------------------------------------------

    def total_income(self) -> float:
        """Sum of all Income transactions in the filtered set."""
        return sum(
            t.amount for t in self._filtered if isinstance(t, Income)
        )

    def total_expense(self) -> float:
        """Sum of all Expense transactions in the filtered set."""
        return sum(
            t.amount for t in self._filtered if isinstance(t, Expense)
        )

    def net_amount(self) -> float:
        """Income minus expenses (transfers are neutral)."""
        return self.total_income() - self.total_expense()

    def average_expense(self) -> float:
        """Average expense amount, or 0.0 if no expenses."""
        expenses = [t for t in self._filtered if isinstance(t, Expense)]
        if not expenses:
            return 0.0
        # Uses __add__ / __radd__ from Transaction for sum()
        return sum(expenses) / len(expenses)

    def category_breakdown(self) -> dict[str, float]:
        """
        Return a dict mapping category -> total amount for expenses.
        Useful for pie charts or spending breakdowns.
        """
        breakdown: dict[str, float] = {}
        for t in self._filtered:
            if isinstance(t, Expense):
                breakdown[t.category] = breakdown.get(t.category, 0.0) + t.amount
        return breakdown

    def monthly_summary(self) -> dict[str, dict[str, float]]:
        """
        Group transactions by month and return income/expense totals.

        Returns:
            {"2026-04": {"income": 5200.0, "expense": 1810.0}, ...}
        """
        summary: dict[str, dict[str, float]] = {}
        for t in self._filtered:
            month_key = t.date.strftime("%Y-%m")
            if month_key not in summary:
                summary[month_key] = {"income": 0.0, "expense": 0.0}
            if isinstance(t, Income):
                summary[month_key]["income"] += t.amount
            elif isinstance(t, Expense):
                summary[month_key]["expense"] += t.amount
        return summary

    # ---- Display helpers ---------------------------------------------------

    def summary_text(self) -> str:
        """Return a multi-line text summary of the filtered data."""
        lines = [
            f"Transactions: {self.count}",
            f"Total Income:  ${self.total_income():,.2f}",
            f"Total Expense: ${self.total_expense():,.2f}",
            f"Net:           ${self.net_amount():,.2f}",
            f"Avg Expense:   ${self.average_expense():,.2f}",
        ]
        breakdown = self.category_breakdown()
        if breakdown:
            lines.append("\nSpending by Category:")
            for cat, amt in sorted(breakdown.items(),
                                   key=lambda x: x[1], reverse=True):
                lines.append(f"  {cat:<20s} ${amt:>10,.2f}")
        return "\n".join(lines)
