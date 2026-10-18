"""
Photo Rename Studio - Skeleton Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from src.config import ThemeColors

class MainWindowSkeleton(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Rename Studio - Skeleton")
        self.resize(800, 600)
        self.setStyleSheet(f"background-color: {ThemeColors.BACKGROUND};")

def main():
    app = QApplication(sys.argv)
    window = MainWindowSkeleton()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())

