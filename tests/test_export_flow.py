"""
Photo Rename Studio - Pengujian Skenario & Integrasi Alur Ekspor (SESI 6)

Skenario:
1. Skenario Nama Ilegal Windows (misal: 'Laporan/Foto*1') -> Ditolak, baris ditandai error.
2. Skenario Nama Duplikat -> Ditolak, baris duplikat ditandai error.
3. Skenario Ekspor Normal -> Validasi sukses, background thread menyalin file,
   foto asli 100% utuh (Zero Data Loss hash match), status row menjadi Sukses.
4. Skenario Overwrite vs Non-Overwrite.
"""

import hashlib
import os
import tempfile
import pytest
from PIL import Image
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication, QMessageBox

from src.config import DEFAULT_ROW_COUNT
from src.ui.main_window import MainWindow
from src.ui.report_dialog import ReportDialog
from src.ui.row_widget import RowStatus


@pytest.fixture
def create_sample_image():
    """Helper membuat file gambar dummy untuk pengujian."""
    def _create(path: str, color=(200, 100, 50), size=(100, 100)):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        img = Image.new("RGB", size, color=color)
        img.save(path, format="JPEG")
        return path
    return _create


def get_file_hash(filepath: str) -> str:
    """Menghitung hash SHA-256 dari sebuah file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_scenario_illegal_windows_filename(qapp, create_sample_image, monkeypatch):
    """
    Skenario 1: Nama Ilegal Windows.
    Input: 'Laporan/Foto*1' -> Ditolak oleh validator, baris ditandai status ERROR.
    """
    # Mock QMessageBox agar tidak memblokir test
    warn_calls = []
    monkeypatch.setattr(QMessageBox, "warning", lambda parent, title, msg: warn_calls.append((title, msg)))

    with tempfile.TemporaryDirectory() as tmpdir:
        src_photo = os.path.join(tmpdir, "sumber.jpg")
        create_sample_image(src_photo)
        out_dir = os.path.join(tmpdir, "output")
        os.makedirs(out_dir, exist_ok=True)

        window = MainWindow(default_rows=5)
        window.set_output_directory(out_dir)

        # Set baris 1 dengan nama ilegal
        window.row_widgets[0].set_data(source_photo=src_photo, target_name="Laporan/Foto*1")

        # Jalankan ekspor
        window.start_export()

        assert len(warn_calls) == 1
        assert "Validasi Ekspor Gagal" in warn_calls[0][0]
        # Baris 1 harus ditandai status ERROR
        assert window.row_widgets[0]._status == RowStatus.ERROR
        assert "karakter ilegal" in window.row_widgets[0]._status_message.lower()
        window.close()


def test_scenario_duplicate_target_names(qapp, create_sample_image, monkeypatch):
    """
    Skenario 2: Nama Duplikat Antar Baris.
    Dua baris memiliki nama target yang sama -> Ditolak oleh validator.
    """
    warn_calls = []
    monkeypatch.setattr(QMessageBox, "warning", lambda parent, title, msg: warn_calls.append((title, msg)))

    with tempfile.TemporaryDirectory() as tmpdir:
        photo1 = os.path.join(tmpdir, "foto1.jpg")
        photo2 = os.path.join(tmpdir, "foto2.jpg")
        create_sample_image(photo1, color=(255, 0, 0))
        create_sample_image(photo2, color=(0, 255, 0))

        out_dir = os.path.join(tmpdir, "output")
        os.makedirs(out_dir, exist_ok=True)

        window = MainWindow(default_rows=5)
        window.set_output_directory(out_dir)

        # Beri dua baris nama target yang sama
        window.row_widgets[0].set_data(source_photo=photo1, target_name="Siswa_Juara")
        window.row_widgets[1].set_data(source_photo=photo2, target_name="siswa_juara")  # case-insensitive check!

        window.start_export()

        assert len(warn_calls) == 1
        assert "Duplikasi nama target" in warn_calls[0][1]
        assert window.row_widgets[1]._status == RowStatus.ERROR
        window.close()


def test_scenario_normal_export_with_integrity_verification(qapp, create_sample_image, monkeypatch):
    """
    Skenario 3: Ekspor Normal & Zero Data Loss.
    - 5 foto disalin dengan nama baru yang valid.
    - Menunggu worker background thread selesai.
    - Verifikasi SHA-256 foto asli tidak berubah sama sekali!
    - Verifikasi foto baru ada di direktori tujuan dengan konten yang identik.
    - Verifikasi progress bar dan status badge baris menjadi SUCCESS.
    """
    # Mock ReportDialog.exec agar tidak memunculkan modal dialog di test runner
    dialog_opened = []
    monkeypatch.setattr(ReportDialog, "exec", lambda self: dialog_opened.append(self))

    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, "src")
        out_dir = os.path.join(tmpdir, "dest")
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(out_dir, exist_ok=True)

        # Buat 5 foto sumber
        src_files = []
        original_hashes = {}
        for i in range(1, 6):
            p = os.path.join(src_dir, f"IMG_{i:03d}.jpg")
            create_sample_image(p, color=(i * 30, i * 40, i * 50))
            src_files.append(p)
            original_hashes[p] = get_file_hash(p)

        window = MainWindow(default_rows=10)
        window.set_output_directory(out_dir)

        # Isi 5 baris pertama
        for i in range(5):
            window.row_widgets[i].set_data(
                source_photo=src_files[i],
                target_name=f"Alumni_2026_{i+1:02d}",
            )

        # Eksekusi ekspor
        window.start_export()

        # Tunggu background worker thread selesai
        assert window.exporter_thread is not None
        window.exporter_thread.wait(5000)
        QCoreApplication.processEvents()

        # 1. Verifikasi dialog laporan terbuka
        assert len(dialog_opened) == 1
        report = dialog_opened[0]
        assert report.success_count == 5
        assert report.fail_count == 0
        assert report.skipped_count == 0
        assert len(report.errors) == 0

        # 2. Verifikasi status baris 1-5 adalah SUCCESS
        for i in range(5):
            assert window.row_widgets[i]._status == RowStatus.SUCCESS
            expected_dest = os.path.join(out_dir, f"Alumni_2026_{i+1:02d}.jpg")
            assert os.path.isfile(expected_dest), f"File {expected_dest} tidak ditemukan di folder tujuan!"

            # 3. Verifikasi Keutuhan Foto Asli (Zero Data Loss)
            src_p = src_files[i]
            current_src_hash = get_file_hash(src_p)
            assert current_src_hash == original_hashes[src_p], "Foto asli telah dimodifikasi atau rusak!"

            # Verifikasi foto hasil ekspor identik dengan foto asli
            dest_hash = get_file_hash(expected_dest)
            assert dest_hash == original_hashes[src_p], "Hash foto ekspor tidak sama dengan foto asli!"

        # 4. Verifikasi UI controls kembali aktif
        assert window.btn_export.isEnabled() is True
        assert window.btn_import.isEnabled() is True
        assert window.progress_bar.value() == 5

        window.close()


def test_scenario_export_overwrite_behavior(qapp, create_sample_image, monkeypatch):
    """
    Skenario 4: Collision dengan file yang sudah ada di output directory.
    - Tanpa overwrite: ditolak sebelum ekspor dimulai.
    - Dengan overwrite: berhasil menimpa file di output directory.
    """
    warn_calls = []
    monkeypatch.setattr(QMessageBox, "warning", lambda parent, title, msg: warn_calls.append((title, msg)))

    dialog_opened = []
    monkeypatch.setattr(ReportDialog, "exec", lambda self: dialog_opened.append(self))

    with tempfile.TemporaryDirectory() as tmpdir:
        src_photo = os.path.join(tmpdir, "foto_baru.jpg")
        create_sample_image(src_photo, color=(100, 200, 50))

        out_dir = os.path.join(tmpdir, "output")
        os.makedirs(out_dir, exist_ok=True)

        # File lama sudah ada di folder tujuan dengan nama yang sama
        existing_target = os.path.join(out_dir, "Foto_Target.jpg")
        create_sample_image(existing_target, color=(0, 0, 0))
        old_hash = get_file_hash(existing_target)

        window = MainWindow(default_rows=3)
        window.set_output_directory(out_dir)
        window.set_overwrite_allowed(False)

        window.row_widgets[0].set_data(source_photo=src_photo, target_name="Foto_Target")

        # 1. Coba ekspor tanpa overwrite -> Harus ditolak saat validasi
        window.start_export()
        assert len(warn_calls) == 1
        assert "sudah ada di direktori output" in warn_calls[0][1]

        # 2. Sekarang centang overwrite -> Harus berhasil ekspor dan menimpa file lama
        warn_calls.clear()
        window.set_overwrite_allowed(True)
        window.start_export()

        assert window.exporter_thread is not None
        window.exporter_thread.wait(5000)
        QCoreApplication.processEvents()

        assert len(dialog_opened) == 1
        assert dialog_opened[0].success_count == 1
        new_dest_hash = get_file_hash(existing_target)
        assert new_dest_hash != old_hash
        assert new_dest_hash == get_file_hash(src_photo)

        window.close()

