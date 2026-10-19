"""
BTS Document Control - Pengujian Fitur Paste Image & Top Bar Terpadu
"""

import os
import tempfile
from pathlib import Path
from PySide6.QtCore import QMimeData, QUrl, Qt
from PySide6.QtGui import QColor, QImage, QKeyEvent, QPainter
from PySide6.QtWidgets import QApplication

from src.config import CLIPBOARD_DIR
from src.core.models import PhotoFieldConfig
from src.ui.dynamic_row import DynamicPhotoRow, DynamicRowStatus
from src.ui.main_window import MainWindow


def _create_sample_qimage(width: int = 100, height: int = 100, color: QColor = Qt.GlobalColor.blue) -> QImage:
    """Helper untuk membuat QImage sederhana dalam memori."""
    img = QImage(width, height, QImage.Format.Format_RGB32)
    img.fill(color)
    return img


def test_dynamic_row_paste_button_exists(qapp):
    """Verifikasi bahwa tombol Tempel ada di DynamicPhotoRow."""
    field = PhotoFieldConfig(
        field_id="antenna_01",
        label="Foto Antena Sektoral",
        sheet_name="Antenna",
        cell_anchor="B5",
    )
    row = DynamicPhotoRow(field_config=field, row_index=1)

    assert hasattr(row, "btn_paste")
    assert row.btn_paste.text() == "Tempel"
    assert "clipboard" in row.btn_paste.toolTip().lower() or "ctrl+v" in row.btn_paste.toolTip().lower()
    assert row.btn_select.text() == "Pilih"
    assert row.btn_clear.text() == "Hapus"


def test_dynamic_row_paste_bitmap_image(qapp):
    """Verifikasi menempel gambar bitmap (seperti hasil Copy Image dari browser)."""
    field = PhotoFieldConfig(
        field_id="tower_base",
        label="Pondasi Tower",
        sheet_name="Civil",
        cell_anchor="C10",
    )
    row = DynamicPhotoRow(field_config=field, row_index=1)

    # Siapkan sinyal tracker
    emitted = []
    row.photo_changed.connect(lambda fid, path: emitted.append((fid, path)))

    # Masukkan QImage ke clipboard sistem
    sample_img = _create_sample_qimage(120, 90, Qt.GlobalColor.red)
    clipboard = QApplication.clipboard()
    clipboard.setImage(sample_img)

    # Eksekusi paste
    success = row.paste_from_clipboard()
    assert success is True
    assert row.photo_path is not None
    assert os.path.isfile(row.photo_path)
    assert Path(row.photo_path).suffix.lower() == ".png"
    assert "paste_tower_base_" in os.path.basename(row.photo_path)
    assert row.lbl_status.text() == DynamicRowStatus.FILLED
    assert len(emitted) == 1
    assert emitted[0][0] == "tower_base"
    assert emitted[0][1] == row.photo_path


def test_dynamic_row_paste_file_url(qapp):
    """Verifikasi menempel file gambar lokal yang disalin dari File Explorer."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Tulis gambar valid ke file sementara
        img = _create_sample_qimage(80, 80, Qt.GlobalColor.green)
        img.save(tmp_path, "JPEG")

        field = PhotoFieldConfig(
            field_id="shelter_door",
            label="Pintu Shelter",
            sheet_name="Civil",
            cell_anchor="D12",
        )
        row = DynamicPhotoRow(field_config=field, row_index=2)

        # Masukkan URL berkas ke clipboard
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(tmp_path)])
        QApplication.clipboard().setMimeData(mime_data)

        success = row.paste_from_clipboard()
        assert success is True
        assert row.photo_path == tmp_path
        assert row.lbl_status.text() == DynamicRowStatus.FILLED
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_dynamic_row_paste_empty_or_text_clipboard(qapp):
    """Verifikasi perilaku saat clipboard tidak berisi gambar sama sekali."""
    field = PhotoFieldConfig(
        field_id="grounding_rod",
        label="Kabel Grounding",
        sheet_name="Power",
        cell_anchor="B20",
    )
    row = DynamicPhotoRow(field_config=field, row_index=3)

    # Isi clipboard dengan teks murni
    QApplication.clipboard().setText("Ini bukan gambar")

    success = row.paste_from_clipboard()
    assert success is False
    assert row.photo_path is None
    assert row.lbl_status.text() == DynamicRowStatus.EMPTY


def test_dynamic_row_ctrl_v_keypress(qapp):
    """Verifikasi bahwa tombol shortcut Ctrl+V memicu paste_from_clipboard."""
    field = PhotoFieldConfig(
        field_id="battery_bank",
        label="Bank Baterai",
        sheet_name="Power",
        cell_anchor="E15",
    )
    row = DynamicPhotoRow(field_config=field, row_index=4)

    # Masukkan gambar ke clipboard
    img = _create_sample_qimage(64, 64, Qt.GlobalColor.yellow)
    QApplication.clipboard().setImage(img)

    # Kirim event penekanan tombol Ctrl+V
    key_event = QKeyEvent(
        QKeyEvent.Type.KeyPress,
        Qt.Key.Key_V,
        Qt.KeyboardModifier.ControlModifier,
        "v",
    )
    row.keyPressEvent(key_event)

    assert row.photo_path is not None
    assert os.path.isfile(row.photo_path)
    assert row.lbl_status.text() == DynamicRowStatus.FILLED


def test_top_bar_redesign_and_legacy_cleanup(qapp):
    """Verifikasi bahwa Top Bar terpadu modern dan tombol lama disembunyikan."""
    window = MainWindow(default_rows=0)

    # Verifikasi pill konteks interaktif
    assert hasattr(window, "lbl_active_site")
    assert hasattr(window, "lbl_active_template")
    assert "Site:" in window.lbl_active_site.text()
    assert "Template:" in window.lbl_active_template.text()

    # Verifikasi Quick Search & Filter Bar ada di toolbar terpadu
    assert hasattr(window, "input_search")
    assert hasattr(window, "btn_filter_all")
    assert hasattr(window, "btn_filter_empty")
    assert hasattr(window, "btn_filter_filled")

    # Verifikasi tombol legacy tidak terlihat di antarmuka
    assert window.btn_import.isVisible() is False
    assert window.btn_add_row.isVisible() is False
    assert window.btn_remove_empty.isVisible() is False
    assert window.btn_reset.isVisible() is False
    assert window.chk_overwrite.isVisible() is False

    window.close()

