"""
Pytest configuration and shared fixtures for BTS Document Control.
"""

import os
import sys

# Pastikan platform headless / offscreen aktif sebelum PySide6 di-load (penting untuk CI Windows & Linux)
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Memastikan instance QApplication selalu aktif untuk seluruh sesi pengujian."""
    app = QApplication.instance()
    if app is None:
        args = [sys.argv[0]]
        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            args += ["-platform", "offscreen"]
        app = QApplication(args)
    yield app
