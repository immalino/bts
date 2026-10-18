"""
Photo Rename Studio - Entry Point Aplikasi
"""

import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.config import APP_ICON_ICO, APP_ICON_PNG, APP_NAME
from src.ui.main_window import MainWindow
from src.ui.styles import APP_STYLESHEET


def main() -> int:
    """Fungsi utama untuk menginisialisasi dan menjalankan aplikasi BTS Document Control."""
    print(f"Memulai {APP_NAME}...")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Set icon aplikasi
    if APP_ICON_PNG.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PNG)))
    elif APP_ICON_ICO.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_ICO)))

    # Terapkan stylesheet global
    app.setStyleSheet(APP_STYLESHEET)

    # Inisialisasi dan tampilkan jendela utama
    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()

    print(f"{APP_NAME} siap. Tutup jendela aplikasi untuk mengakhiri.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
