"""
main.py — Entry point for the Personal Finance Tracker application.

Initialises the DataManager (loads or creates sample data) and launches
the Tkinter GUI.
"""

from data_manager import DataManager
from gui import App


def main() -> None:
    dm = DataManager()

    # Try to load persisted data; fall back to sample data on first run
    if not dm.load():
        print("No existing data found — creating sample data …")
        dm.create_sample_data()

    app = App(dm)
    app.mainloop()


if __name__ == "__main__":
    main()
