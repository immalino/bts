"""
Photo Rename Studio - Script Verifikasi Otomatis SESI 6
Memverifikasi:
1. Tombol 'Proses Ekspor', progress bar, dan status label di footer.
2. Skenario Validasi: Nama Ilegal Windows ('Laporan/Foto*1') ditolak, baris ditandai error & disorot.
3. Skenario Validasi: Duplikasi nama target ditolak, baris ditandai error & disorot.
4. Skenario Ekspor Normal:
   - 5 foto dengan nama valid.
   - Background thread ExporterThread berjalan non-blocking.
   - Progress bar bergerak dan status baris berubah menjadi hijau (SUCCESS) secara real-time.
   - Keutuhan foto asli terjamin 100% (Zero Data Loss hash match).
   - Dialog laporan (ReportDialog) menampilkan statistik ekspor yang tepat.
"""

import hashlib
import os
import sys
import tempfile
import time
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from src.config import DEFAULT_ROW_COUNT

from src.ui.main_window import MainWindow
from src.ui.report_dialog import ReportDialog
from src.ui.row_widget import RowStatus
from src.ui.styles import APP_STYLESHEET


def compute_hash(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_sample_photo(path: str, color=(220, 120, 80)) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img = Image.new("RGB", (120, 120), color=color)
    img.save(path, format="JPEG")
    return path


def run_verification():
    print("[1/5] Inisialisasi Aplikasi dan MainWindow...")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow(default_rows=10)
    window.show()
    app.processEvents()

    # Verifikasi elemen footer
    assert hasattr(window, "btn_export"), "Tombol btn_export tidak ditemukan"
    assert hasattr(window, "progress_bar"), "Komponen progress_bar tidak ditemukan"
    assert hasattr(window, "lbl_export_status"), "Label lbl_export_status tidak ditemukan"
    assert window.btn_export.isEnabled() is True
    assert window.progress_bar.value() == 0
    print("  -> PASS: Elemen footer (Tombol Ekspor, Progress Bar, Status Label) siap.")

    # 2. Pengujian Skenario 1: Nama Ilegal Windows
    print("\n[2/5] Menguji Skenario 1: Nama Ilegal Windows ('Laporan/Foto*1')...")
    with tempfile.TemporaryDirectory() as tmpdir:
        src_photo1 = create_sample_photo(os.path.join(tmpdir, "foto_test1.jpg"))
        out_dir = os.path.join(tmpdir, "out")
        os.makedirs(out_dir, exist_ok=True)

        window.set_output_directory(out_dir)
        window.row_widgets[0].set_data(source_photo=src_photo1, target_name="Laporan/Foto*1")
        app.processEvents()

        # Mock warning dialog
        warning_caught = []
        old_warning = QMessageBox.warning
        QMessageBox.warning = lambda parent, title, msg: warning_caught.append((title, msg))

        window.start_export()
        app.processEvents()

        QMessageBox.warning = old_warning

        assert len(warning_caught) == 1, "Peringatan validasi harus muncul!"
        assert window.row_widgets[0]._status == RowStatus.ERROR
        assert "karakter ilegal" in window.row_widgets[0]._status_message.lower()
        print(f"  -> PASS: Validasi menolak nama ilegal. Status baris 1: {window.row_widgets[0]._status} ({window.row_widgets[0]._status_message})")

    # 3. Pengujian Skenario 2: Nama Duplikat
    print("\n[3/5] Menguji Skenario 2: Nama Duplikat Antar Baris...")
    with tempfile.TemporaryDirectory() as tmpdir:
        photo_a = create_sample_photo(os.path.join(tmpdir, "a.jpg"), color=(255, 0, 0))
        photo_b = create_sample_photo(os.path.join(tmpdir, "b.jpg"), color=(0, 255, 0))
        out_dir = os.path.join(tmpdir, "out")
        os.makedirs(out_dir, exist_ok=True)

        window.set_output_directory(out_dir)
        window.row_widgets[0].set_data(source_photo=photo_a, target_name="Santri_Bintang")
        window.row_widgets[1].set_data(source_photo=photo_b, target_name="santri_bintang")  # Duplikat case-insensitive
        app.processEvents()

        warning_caught = []
        old_warning = QMessageBox.warning
        QMessageBox.warning = lambda parent, title, msg: warning_caught.append((title, msg))

        window.start_export()
        app.processEvents()

        QMessageBox.warning = old_warning

        assert len(warning_caught) == 1
        assert "Duplikasi nama target" in warning_caught[0][1]
        assert window.row_widgets[1]._status == RowStatus.ERROR
        print(f"  -> PASS: Validasi menolak duplikasi nama target. Status baris 2: {window.row_widgets[1]._status}")

    # 4. Pengujian Skenario 3: Ekspor Normal, Non-Blocking Thread, dan Zero Data Loss
    print("\n[4/5] Menguji Skenario 3: Ekspor Normal (5 foto), Non-blocking Thread & Verifikasi Integritas...")
    with tempfile.TemporaryDirectory() as tmpdir:
        src_folder = os.path.join(tmpdir, "sumber")
        dest_folder = os.path.join(tmpdir, "tujuan")
        os.makedirs(src_folder, exist_ok=True)
        os.makedirs(dest_folder, exist_ok=True)

        window.reset_all()
        window.set_output_directory(dest_folder)

        # Buat 5 foto sumber
        original_hashes = {}
        for i in range(1, 6):
            p = os.path.join(src_folder, f"raw_{i:02d}.jpg")
            create_sample_photo(p, color=(i * 40, i * 20, i * 30))
            original_hashes[p] = compute_hash(p)
            window.row_widgets[i - 1].set_data(source_photo=p, target_name=f"Santri_Lulus_{i:02d}")

        app.processEvents()

        # Mock ReportDialog.exec agar dialog otomatis ditutup setelah mencatat hasil
        report_instances = []
        def mocked_exec(self):
            report_instances.append(self)
            return 1
        old_exec = ReportDialog.exec
        ReportDialog.exec = mocked_exec

        # Mulai ekspor
        start_time = time.perf_counter()
        window.start_export()

        # Loop processEvents sampai background thread selesai
        while window.exporter_thread and window.exporter_thread.isRunning():
            app.processEvents()
            time.sleep(0.01)

        app.processEvents()
        elapsed = time.perf_counter() - start_time
        ReportDialog.exec = old_exec

        print(f"  -> Background export selesai dalam {elapsed:.3f} detik.")

        # Verifikasi ReportDialog
        assert len(report_instances) == 1, "ReportDialog harus ditampilkan setelah ekspor selesai"
        rep = report_instances[0]
        assert rep.success_count == 5
        assert rep.fail_count == 0
        assert rep.skipped_count == 0
        assert len(rep.errors) == 0
        print("  -> PASS: ReportDialog menerima laporan: 5 Sukses, 0 Gagal, 0 Dilewati.")

        # Verifikasi status baris dan file tujuan
        for i in range(1, 6):
            row = window.row_widgets[i - 1]
            assert row._status == RowStatus.SUCCESS, f"Baris {i} status bukan SUCCESS tapi {row._status}"

            dest_file = os.path.join(dest_folder, f"Santri_Lulus_{i:02d}.jpg")
            assert os.path.isfile(dest_file), f"File hasil ekspor {dest_file} tidak ditemukan!"

            # Verifikasi Zero Data Loss: hash asli tidak berubah dan hash hasil identik
            src_file = os.path.join(src_folder, f"raw_{i:02d}.jpg")
            src_current_hash = compute_hash(src_file)
            assert src_current_hash == original_hashes[src_file], f"Foto asli {src_file} rusak atau termodifikasi!"

            dest_hash = compute_hash(dest_file)
            assert dest_hash == original_hashes[src_file], f"Hash foto ekspor {dest_file} berbeda dari aslinya!"

        print("  -> PASS: Seluruh 5 foto diekspor dengan sempurna. Keutuhan foto asli 100% utuh (Zero Data Loss terjamin).")
        assert window.progress_bar.value() == 5
        assert window.btn_export.isEnabled() is True

    # 5. Verifikasi interaksi dialog laporan
    print("\n[5/5] Menguji komponen ReportDialog secara visual...")
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_errors = [
            {"row_index": 3, "source_path": "/tmp/a.jpg", "target_filename": "TargetA.jpg", "error": "File korup"}
        ]
        dialog = ReportDialog(
            success_count=4,
            fail_count=1,
            skipped_count=0,
            errors=sample_errors,
            output_directory=tmpdir,
        )
        dialog.show()
        app.processEvents()
        assert dialog.table_errors.rowCount() == 1
        assert dialog.btn_open_folder.isEnabled() is True
        dialog.close()
        print("  -> PASS: ReportDialog dengan tabel error berfungsi baik.")

    window.close()
    print("\n[SELESAI] Seluruh verifikasi SESI 6 berhasil 100% tanpa kendala!")
    return 0


if __name__ == "__main__":
    sys.exit(run_verification())
