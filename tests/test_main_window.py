"""
Photo Rename Studio - Pengujian Unit & Integrasi MainWindow
"""

import os
import tempfile
import pytest
from PySide6.QtWidgets import QApplication

from src.config import DEFAULT_ROW_COUNT
from src.ui.main_window import MainWindow
from src.ui.row_widget import RowStatus


@pytest.fixture
def main_window(qapp):
    """Fixture MainWindow instance."""
    window = MainWindow(default_rows=DEFAULT_ROW_COUNT)
    yield window
    window.close()


def test_main_window_init(main_window):
    """Verifikasi inisialisasi awal MainWindow."""
    assert len(main_window.row_widgets) == DEFAULT_ROW_COUNT
    assert main_window.row_widgets[0].row_index == 1
    assert main_window.row_widgets[-1].row_index == 100
    assert main_window.scroll_area.widgetResizable() is True
    assert "Total: 100 baris" in main_window.lbl_stats.text()
    assert main_window.get_output_directory() == ""
    assert main_window.is_overwrite_allowed() is False


def test_main_window_add_row(main_window):
    """Verifikasi penambahan baris secara dinamis."""
    initial_count = len(main_window.row_widgets)
    new_row = main_window.add_row(target_name="Foto_Baru")

    assert len(main_window.row_widgets) == initial_count + 1
    assert new_row.row_index == initial_count + 1
    assert new_row.get_data()["target_stem"] == "Foto_Baru"
    assert f"Total: {initial_count + 1} baris" in main_window.lbl_stats.text()


def test_main_window_output_dir_and_overwrite(main_window):
    """Verifikasi setter dan getter folder output dan opsi overwrite."""
    with tempfile.TemporaryDirectory() as tmpdir:
        main_window.set_output_directory(tmpdir)
        assert os.path.normpath(main_window.get_output_directory()) == os.path.normpath(tmpdir)

        main_window.set_overwrite_allowed(True)
        assert main_window.is_overwrite_allowed() is True

        main_window.set_overwrite_allowed(False)
        assert main_window.is_overwrite_allowed() is False


def test_main_window_import_names_txt(main_window):
    """Verifikasi pemetaan impor nama dari file TXT."""
    sample_names = ["Santri_01", "Santri_02", "Santri_03"]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("\n".join(sample_names))
        tmp_path = f.name

    try:
        count = main_window.import_names_from_file_path(tmp_path)
        assert count == 3
        assert main_window.row_widgets[0].get_data()["target_stem"] == "Santri_01"
        assert main_window.row_widgets[1].get_data()["target_stem"] == "Santri_02"
        assert main_window.row_widgets[2].get_data()["target_stem"] == "Santri_03"
    finally:
        os.remove(tmp_path)


def test_main_window_import_names_csv_and_auto_expand(main_window):
    """Verifikasi impor nama CSV yang melebihi jumlah baris dan auto penambahan baris."""
    # Buat 105 nama untuk menguji auto ekspansi dari 100 baris
    names = [f"Murid_{i:03d}" for i in range(1, 106)]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("Nama Lengkap,Kelas\n")
        for name in names:
            f.write(f"{name},A\n")
        tmp_path = f.name

    try:
        # Note: row 0 adalah header 'Nama Lengkap', total baris 106
        count = main_window.import_names_from_file_path(tmp_path)
        assert count == 106
        assert len(main_window.row_widgets) == 106
        assert main_window.row_widgets[0].get_data()["target_stem"] == "Nama Lengkap"
        assert main_window.row_widgets[1].get_data()["target_stem"] == "Murid_001"
        assert main_window.row_widgets[105].get_data()["target_stem"] == "Murid_105"
        assert main_window.row_widgets[105].row_index == 106
    finally:
        os.remove(tmp_path)


def test_main_window_remove_empty_rows(qapp):
    """Verifikasi penghapusan baris kosong dan renumbering."""
    window = MainWindow(default_rows=5)
    assert len(window.row_widgets) == 5

    # Isi baris ke-2 dan ke-4
    window.row_widgets[1].set_target_name("Ada_Nama_1")
    window.row_widgets[3].set_target_name("Ada_Nama_2")

    # Baris kosong adalah baris 0, 2, 4 (3 baris)
    empty_rows = [r for r in window.row_widgets if not r.source_photo and not r.get_data()["target_stem"]]
    assert len(empty_rows) == 3

    # Hapus langsung via iterasi logic seperti di handler
    window.scroll_content.setUpdatesEnabled(False)
    for r in empty_rows:
        window.rows_layout.removeWidget(r)
        window.row_widgets.remove(r)
        r.setParent(None)
        r.deleteLater()

    for idx, r in enumerate(window.row_widgets, start=1):
        r.set_row_index(idx)

    window.scroll_content.setUpdatesEnabled(True)
    window.update_summary_stats()

    assert len(window.row_widgets) == 2
    assert window.row_widgets[0].row_index == 1
    assert window.row_widgets[0].get_data()["target_stem"] == "Ada_Nama_1"
    assert window.row_widgets[1].row_index == 2
    assert window.row_widgets[1].get_data()["target_stem"] == "Ada_Nama_2"
    assert "Total: 2 baris" in window.lbl_stats.text()
    window.close()


def test_main_window_reset_all(main_window):
    """Verifikasi fungsi reset_all mengembalikan ke 100 baris kosong."""
    main_window.set_output_directory("/tmp/test_dir")
    main_window.set_overwrite_allowed(True)
    main_window.row_widgets[0].set_target_name("Target_Custom")
    main_window.add_row("Ekstra_1")

    assert len(main_window.row_widgets) == 101
    assert main_window.is_overwrite_allowed() is True

    main_window.reset_all()

    assert len(main_window.row_widgets) == DEFAULT_ROW_COUNT
    assert main_window.get_output_directory() == ""
    assert main_window.is_overwrite_allowed() is False
    assert main_window.row_widgets[0].get_data()["target_stem"] == ""
