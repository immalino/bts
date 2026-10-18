"""
Pytest configuration and shared fixtures for Photo Rename Studio.
"""

import os
import sys
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Memastikan instance QApplication selalu aktif untuk seluruh sesi pengujian."""
    if "QT_QPA_PLATFORM" not in os.environ and "DISPLAY" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
