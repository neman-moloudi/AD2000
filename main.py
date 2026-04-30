"""AD-2000 Pressure Vessel Calculator — application entry point."""
import sys
import os

# Ensure the project root is on sys.path so all packages resolve correctly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AD-2000 Pressure Vessel Calculator")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
