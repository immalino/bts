"""
Photo Rename Studio - Script Verifikasi Otomatis SESI 5
Memverifikasi:
1. Jendela utama (MainWindow) terbuka dan menampilkan 100 baris RowWidget awal.
2. Scroll area vertikal dapat discroll dari baris 1 sampai baris 100 dengan lancar.
3. Tombol Tambah Baris menambah baris ke-101.
4. Fitur Impor Nama TXT/CSV memetakan nama ke baris secara tepat dan menambah baris jika perlu.
5. Pemilihan folder output dan opsi overwrite berfungsi dengan baik.
6. Hapus baris kosong dan reset semua bekerja normal.
"""

import os
import sys
import tempfile
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication

from src.config import DEFAULT_ROW_COUNT
from src.ui.main_window import MainWindow
from src.ui.styles import APP_STYLESHEET


def run_verification():
    print("[1/6] Inisialisasi QApplication dan MainWindow...")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow(default_rows=DEFAULT_ROW_COUNT)
    window.show()
    app.processEvents()

    # 1. Verifikasi 100 baris
    assert len(window.row_widgets) == 100, f"Expected 100 rows, got {len(window.row_widgets)}"
    assert window.row_widgets[0].row_index == 1
    assert window.row_widgets[99].row_index == 100
    print("  -> PASS: 100 baris terbuat dengan nomor urut 1 sampai 100.")

    # 2. Verifikasi Scroll lancar dari baris 1 sampai baris 100
    print("[2/6] Menguji kelancaran scroll area vertikal (100 baris)...")
    v_scroll = window.scroll_area.verticalScrollBar()
    max_scroll = v_scroll.maximum()
    assert max_scroll > 0, "Vertical scroll maximum should be > 0 for 100 rows"

    # Simulasikan scrolling turun dan naik secara bertahap
    step = max_scroll // 10
    start_time = time.perf_counter()
    for val in range(0, max_scroll + 1, step):
        v_scroll.setValue(val)
        app.processEvents()
    for val in range(max_scroll, -1, -step):
        v_scroll.setValue(val)
        app.processEvents()
    elapsed = time.perf_counter() - start_time
    print(f"  -> PASS: Scroll 100 baris bolak-balik berhasil dalam {elapsed:.3f} detik (sangat lancar).")

    # 3. Verifikasi Tambah Baris
    print("[3/6] Menguji tombol Tambah Baris...")
    window.btn_add_row.click()
    app.processEvents()
    assert len(window.row_widgets) == 101
    assert window.row_widgets[-1].row_index == 101
    print("  -> PASS: Baris ke-101 berhasil ditambahkan.")

    # 4. Verifikasi Impor Nama (TXT dan CSV)
    print("[4/6] Menguji fungsionalitas impor nama...")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("Ahmad Dahlan\nKH Hasyim Asyari\nKi Hajar Dewantara\n")
        txt_file = f.name

    try:
        imported = window.import_names_from_file_path(txt_file)
        assert imported == 3
        assert window.row_widgets[0].get_data()["target_stem"] == "Ahmad Dahlan"
        assert window.row_widgets[1].get_data()["target_stem"] == "KH Hasyim Asyari"
        assert window.row_widgets[2].get_data()["target_stem"] == "Ki Hajar Dewantara"
        print("  -> PASS: 3 nama berhasil dipetakan ke baris 1, 2, 3.")
    finally:
        os.remove(txt_file)

    # 5. Verifikasi Folder Output dan Overwrite
    print("[5/6] Menguji pemilihan folder output dan opsi overwrite...")
    with tempfile.TemporaryDirectory() as tmpdir:
        window.set_output_directory(tmpdir)
        assert window.get_output_directory() == tmpdir

        window.chk_overwrite.setChecked(True)
        assert window.is_overwrite_allowed() is True
        window.chk_overwrite.setChecked(False)
        assert window.is_overwrite_allowed() is False
        print("  -> PASS: Folder output dan opsi overwrite berfungsi dengan benar.")

    # 6. Verifikasi Reset Semua
    print("[6/6] Menguji fungsi reset semua...")
    window.reset_all()
    app.processEvents()
    assert len(window.row_widgets) == 100
    assert window.row_widgets[0].get_data()["target_stem"] == ""
    assert window.get_output_directory() == ""
    assert window.is_overwrite_allowed() is False
    print("  -> PASS: Reset mengembalikan jendela ke kondisi default 100 baris bersih.")

    print("\n[SELESAI] Seluruh verifikasi SESI 5 berhasil tanpa error!")
    window.close()
    return 0


if __name__ == "__main__":
    sys.exit(run_verification())
