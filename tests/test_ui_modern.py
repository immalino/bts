"""
Photo Rename Studio - Pengujian Unit Fitur UI Modern & Dark Mode
Menguji:
1. Engine SVG Icon (render_svg_pixmap, get_icon, fallback)
2. ThemeManager & Stylesheet Generator (Light Mode, Dark Mode, Palette, Signal)
3. PhotoLightboxDialog (Viewer resolusi tinggi, metadata EXIF/dimensi)
4. Filter & Search pada DynamicPhotoRow dan DynamicTextRow
5. WorkspaceEmptyState onboarding widget
"""

import os
import tempfile
from pathlib import Path
from PIL import Image
import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from src.core.models import PhotoFieldConfig
from src.ui.empty_state import WorkspaceEmptyState
from src.ui.dynamic_row import DynamicPhotoRow, DynamicTextRow
from src.ui.icons import get_icon, render_svg_pixmap, SVG_ICONS
from src.ui.lightbox import PhotoLightboxDialog
from src.ui.styles import DARK_PALETTE, LIGHT_PALETTE, ThemeManager, generate_stylesheet


# ==============================================================================
# 1. PENGUJIAN SVG ICON ENGINE
# ==============================================================================

def test_render_svg_pixmap():
    """Memastikan render_svg_pixmap menghasilkan QPixmap valid dengan ukuran dan warna tepat."""
    svg_simple = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="{color}"/></svg>'
    pixmap = render_svg_pixmap(svg_simple, size=32, color="#2563EB")
    assert isinstance(pixmap, QPixmap)
    assert not pixmap.isNull()
    assert pixmap.width() == 32
    assert pixmap.height() == 32


def test_get_icon_known_icons():
    """Memastikan semua ikon SVG standar yang terdaftar dapat di-load menjadi QIcon yang valid."""
    core_icons = [
        "folder", "file_spreadsheet", "plus", "trash", "refresh", "search",
        "check", "x", "sun", "moon", "camera", "arrow_up", "arrow_down",
        "eye", "external_link", "sparkles", "upload_cloud", "building"
    ]
    for name in core_icons:
        icon = get_icon(name, size=20)
        assert isinstance(icon, QIcon), f"Icon {name} bukan instance QIcon"
        pixmap = icon.pixmap(20, 20)
        assert not pixmap.isNull(), f"Icon {name} menghasilkan pixmap null"


def test_get_icon_fallback_unknown():
    """Memastikan ikon yang tidak dikenal menghasilkan fallback QIcon tanpa melempar error."""
    icon = get_icon("icon_yang_tidak_ada_di_katalog_xyz", size=24)
    assert isinstance(icon, QIcon)
    pixmap = icon.pixmap(24, 24)
    assert not pixmap.isNull()


def test_get_icon_custom_color():
    """Memastikan get_icon dapat menerima warna kustom hex."""
    icon = get_icon("check", color="#10B981", size=16)
    assert isinstance(icon, QIcon)
    assert not icon.pixmap(16, 16).isNull()


# ==============================================================================
# 2. PENGUJIAN THEME MANAGER & DESIGN SYSTEM
# ==============================================================================

def test_palettes_tokens_integrity():
    """Memastikan LIGHT_PALETTE dan DARK_PALETTE memiliki kumpulan token wajib yang identik."""
    required_attrs = [
        "BACKGROUND", "SURFACE", "SURFACE_ALT", "BORDER", "BORDER_LIGHT",
        "PRIMARY", "PRIMARY_HOVER", "PRIMARY_LIGHT",
        "TEXT", "TEXT_MUTED", "TEXT_SUBTLE",
        "SUCCESS", "DANGER", "WARNING"
    ]
    for attr in required_attrs:
        assert hasattr(LIGHT_PALETTE, attr), f"LIGHT_PALETTE kehilangan atribut {attr}"
        assert hasattr(DARK_PALETTE, attr), f"DARK_PALETTE kehilangan atribut {attr}"
    assert LIGHT_PALETTE.is_dark is False
    assert DARK_PALETTE.is_dark is True


def test_generate_stylesheet():
    """Memastikan generate_stylesheet menghasilkan CSS lengkap untuk light dan dark mode."""
    qss_light = generate_stylesheet("light")
    qss_dark = generate_stylesheet("dark")
    qss_palette = generate_stylesheet(LIGHT_PALETTE)

    assert isinstance(qss_light, str) and len(qss_light) > 500
    assert isinstance(qss_dark, str) and len(qss_dark) > 500
    assert isinstance(qss_palette, str) and len(qss_palette) > 500

    # Memeriksa elemen CSS utama
    assert "QMainWindow" in qss_light
    assert "QPushButton#PrimaryButton" in qss_light
    assert "QTableWidget" in qss_light
    assert "QHeaderView::section" in qss_light
    assert "QLineEdit" in qss_light

    assert "QMainWindow" in qss_dark
    assert "QPushButton#PrimaryButton" in qss_dark
    assert "QTableWidget" in qss_dark


def test_theme_manager_toggle_and_signals():
    """Memastikan ThemeManager singleton dapat beralih tema dan memancarkan sinyal theme_changed."""
    tm = ThemeManager.get_instance()
    
    # Simpan tema awal
    initial_theme = tm.current_theme

    received_themes = []
    tm.theme_changed.connect(lambda t: received_themes.append(t))

    # Test set_theme
    tm.set_theme("dark")
    assert tm.is_dark_mode() is True
    assert tm.get_palette() == DARK_PALETTE
    assert "dark" in received_themes

    # Test toggle
    toggled = tm.toggle_theme()
    assert toggled == "light"
    assert tm.is_dark_mode() is False
    assert tm.get_palette() == LIGHT_PALETTE
    assert "light" in received_themes

    # Kembalikan ke tema awal
    tm.set_theme(initial_theme)


# ==============================================================================
# 3. PENGUJIAN PHOTO LIGHTBOX MODAL
# ==============================================================================

def test_photo_lightbox_dialog_with_image(qapp):
    """Memastikan PhotoLightboxDialog dapat memuat gambar dan menampilkan informasi dimensi."""
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, "test_lightbox.jpg")
        img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        img.save(img_path, "JPEG")

        dialog = PhotoLightboxDialog(photo_path=img_path, title="Foto Antena Test")
        dialog.show()
        qapp.processEvents()

        # Verifikasi judul dan metadata
        assert "Foto Antena Test" in dialog.windowTitle()
        assert "800 × 600" in dialog.lbl_meta_dims.text()
        assert os.path.exists(dialog.photo_path)

        dialog.close()


def test_photo_lightbox_dialog_nonexistent_image(qapp):
    """Memastikan PhotoLightboxDialog menangani path file yang tidak ada tanpa crash."""
    dialog = PhotoLightboxDialog(photo_path="/non/existent/image.jpg", title="File Hilang")
    dialog.show()
    qapp.processEvents()

    assert "File Hilang" in dialog.windowTitle()
    assert "tidak ditemukan" in dialog.lbl_image.text()
    dialog.close()


# ==============================================================================
# 4. PENGUJIAN FILTER & INSTANT SEARCH PADA ROW WIDGETS
# ==============================================================================

def test_dynamic_photo_row_filtering(qapp):
    """Memastikan matches_filter pada DynamicPhotoRow memfilter berdasarkan query teks dan status terisi/kosong."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = PhotoFieldConfig(
            field_id="antenna_1",
            label="Foto Antena Sektoral 1",
            sheet_name="Documentation",
            cell_anchor="B5",
            field_type="photo",
        )
        row = DynamicPhotoRow(field_config=cfg)

        # 1. Awal: Belum terisi foto
        assert row.photo_path is None
        assert row.matches_filter(search_text="", status_filter="all") is True
        assert row.matches_filter(search_text="", status_filter="empty") is True
        assert row.matches_filter(search_text="", status_filter="filled") is False

        # Pencarian teks (cocok dengan label)
        assert row.matches_filter(search_text="Antena", status_filter="all") is True
        assert row.matches_filter(search_text="Baterai", status_filter="all") is False

        # 2. Isi foto ke row
        sample_img = os.path.join(tmpdir, "antenna.jpg")
        Image.new("RGB", (100, 100), color=(255, 0, 0)).save(sample_img)
        row.set_photo(sample_img)

        assert row.photo_path == sample_img
        assert row.matches_filter(search_text="", status_filter="all") is True
        assert row.matches_filter(search_text="", status_filter="empty") is False
        assert row.matches_filter(search_text="", status_filter="filled") is True

        # Pencarian teks (cocok dengan nama label/sheet/sel)
        assert row.matches_filter(search_text="Documentation", status_filter="all") is True
        assert row.matches_filter(search_text="B5", status_filter="all") is True
        assert row.matches_filter(search_text="nonexistent", status_filter="all") is False


def test_dynamic_text_row_filtering(qapp):
    """Memastikan matches_filter pada DynamicTextRow memfilter berdasarkan field_name dan isi nilai."""
    cfg_text = PhotoFieldConfig(
        field_id="site_id",
        label="Site ID & Nama Lokasi",
        sheet_name="Documentation",
        cell_anchor="C2",
        field_type="text",
    )
    row = DynamicTextRow(field_config=cfg_text)

    # Awal kosong
    assert row.matches_filter(search_text="", status_filter="all") is True
    assert row.matches_filter(search_text="", status_filter="empty") is True
    assert row.matches_filter(search_text="", status_filter="filled") is False

    # Pencarian query nama label
    assert row.matches_filter(search_text="Site", status_filter="all") is True
    assert row.matches_filter(search_text="Tower", status_filter="all") is False

    # Isi teks nilai
    row.set_text("JKT-042")
    assert row.matches_filter(search_text="", status_filter="all") is True
    assert row.matches_filter(search_text="", status_filter="empty") is False
    assert row.matches_filter(search_text="", status_filter="filled") is True
    assert row.matches_filter(search_text="Lokasi", status_filter="all") is True


# ==============================================================================
# 5. PENGUJIAN WORKSPACE EMPTY STATE
# ==============================================================================

def test_workspace_empty_state(qapp):
    """Memastikan widget WorkspaceEmptyState diinisialisasi dengan ikon dan tombol aksi aktif."""
    widget = WorkspaceEmptyState()
    assert widget.btn_site is not None
    assert widget.btn_template is not None

    clicked_actions = []
    widget.select_site_clicked.connect(lambda: clicked_actions.append("site"))
    widget.manage_template_clicked.connect(lambda: clicked_actions.append("template"))

    widget.btn_site.click()
    widget.btn_template.click()

    assert clicked_actions == ["site", "template"]
