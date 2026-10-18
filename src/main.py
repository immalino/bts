"""
Photo Rename Studio - Entry Point Aplikasi
"""

import sys
from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.ui.styles import APP_STYLESHEET


def main() -> int:
    """Fungsi utama untuk menginisialisasi dan menjalankan aplikasi Photo Rename Studio."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Terapkan stylesheet global
    app.setStyleSheet(APP_STYLESHEET)

    # Inisialisasi dan tampilkan jendela utama
    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
