# Personal Finance Tracker

A Python-based personal finance management application built with Object-Oriented Programming principles and a Tkinter GUI.

## Project Overview

This application helps users manage their personal finances by tracking income, expenses, and transfers across multiple accounts. It provides budgeting tools, category-based organization, and reporting features to give users a clear picture of their financial health.

## Features

- **Multi-Account Management** — Track finances across cash, bank, and credit card accounts
- **Transaction Tracking** — Record income, expenses, and transfers with categories and notes
- **Budget Management** — Set monthly budgets per category with alerts when approaching limits
- **Dashboard** — View account balances, recent transactions, and spending summary at a glance
- **Reports & Filtering** — Filter transactions by date range, category, or account; view totals and breakdowns
- **Persistent Storage** — All data saved locally in JSON format
- **Graphical User Interface** — Built with Tkinter for an intuitive desktop experience

## OOP Concepts Used

- **Classes & Objects** — Core data models (Transaction, Account, Budget, Report)
- **Inheritance** — `Income`, `Expense`, `Transfer` subclasses extend a base `Transaction` class
- **Polymorphism** — `summary()` method behaves differently for each transaction type
- **Encapsulation** — Private attributes with controlled access via properties
- **Abstraction** — Abstract base class for `Transaction` using Python's `abc` module
- **Operator Overloading** — `__str__`, `__lt__`, `__add__` for intuitive object operations
- **Composition** — `Account` contains a collection of `Transaction` objects
- **Class/Static Methods** — Factory methods and validation helpers
- **Properties** — `@property` decorators for getters/setters

## Project Structure

```
Task_1/
├── main.py              # Entry point, launches the application
├── models.py            # Core data classes (Transaction, Account, Budget)
├── gui.py               # Tkinter GUI components
├── data_manager.py      # File I/O for saving/loading data (JSON)
├── reports.py           # Reporting, filtering, and statistics
└── README.md
```

## How to Run

### Prerequisites

- Python 3.8 or above
- Tkinter (included with standard Python installation)

### Running the Application

```bash
cd Task_1
python main.py
```

No external packages are required.

## Data Storage

Transaction and account data are stored in a local `data.json` file, created automatically on first run.

