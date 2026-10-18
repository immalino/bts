"""
Photo Rename Studio - Pengujian Unit ReportDialog
"""

import sys
import tempfile
import pytest
from PySide6.QtWidgets import QApplication

from src.ui.report_dialog import ReportDialog
from src.utils.file_utils import open_folder_in_explorer


def test_report_dialog_success_only(qapp):
    """Verifikasi tampilan ReportDialog saat seluruh ekspor berhasil (tanpa error)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dialog = ReportDialog(
            success_count=5,
            fail_count=0,
            skipped_count=0,
            errors=[],
            output_directory=tmpdir,
        )
        dialog.show()
        qapp.processEvents()

        # Tidak ada table errors
        assert not hasattr(dialog, "table_errors")
        assert dialog.success_count == 5
        assert dialog.fail_count == 0
        assert dialog.skipped_count == 0
        dialog.close()


def test_report_dialog_with_errors(qapp):
    """Verifikasi tampilan ReportDialog saat terjadi error atau file dilewati."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_errors = [
            {
                "row_index": 2,
                "source_path": "/path/to/foto1.jpg",
                "target_filename": "Target_A.jpg",
                "error": "File sudah ada di folder tujuan",
            },
            {
                "row_index": 4,
                "source_path": "/path/to/foto2.jpg",
                "target_filename": "Target_B.jpg",
                "error": "File sumber tidak ditemukan",
            },
        ]
        dialog = ReportDialog(
            success_count=3,
            fail_count=1,
            skipped_count=1,
            errors=sample_errors,
            output_directory=tmpdir,
        )
        dialog.show()
        qapp.processEvents()

        assert hasattr(dialog, "table_errors")
        assert dialog.table_errors.rowCount() == 2
        assert dialog.table_errors.columnCount() == 4

        # Periksa isi baris 1
        assert dialog.table_errors.item(0, 0).text() == "2"
        assert dialog.table_errors.item(0, 1).text() == "foto1.jpg"
        assert dialog.table_errors.item(0, 2).text() == "Target_A.jpg"
        assert "File sudah ada" in dialog.table_errors.item(0, 3).text()

        # Periksa isi baris 2
        assert dialog.table_errors.item(1, 0).text() == "4"
        assert dialog.table_errors.item(1, 1).text() == "foto2.jpg"
        assert dialog.table_errors.item(1, 2).text() == "Target_B.jpg"
        assert "File sumber tidak ditemukan" in dialog.table_errors.item(1, 3).text()

        dialog.close()


def test_open_folder_in_explorer(monkeypatch):
    """Verifikasi fungsi utilitas open_folder_in_explorer."""
    # Folder non-existent harus return False
    assert open_folder_in_explorer("/non/existent/path/xyz123") is False
    assert open_folder_in_explorer("") is False

    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock pemanggilan shell explorer agar tidak me-lock folder temporary di Windows
        import os
        if sys.platform == "win32":
            monkeypatch.setattr(os, "startfile", lambda p: None, raising=False)
        else:
            import subprocess
            monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: None)

        res = open_folder_in_explorer(tmpdir)
        assert res is True

