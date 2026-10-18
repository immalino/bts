"""
Photo Rename Studio - Komponen Dynamic Photo Row
Widget baris foto dinamis untuk workspace berbasis template Excel.
Menampilkan: Nomor urut, Nama Field Foto, Badge Info Sheet & Sel, Thumbnail,
DropZone interaktif, Tombol Pilih/Hapus Foto, dan Status (Kosong / Terisi).
"""

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QVBoxLayout,
)

from src.config import SUPPORTED_EXTENSIONS, THUMBNAIL_SIZE, ThemeColors
from src.core.image_loader import create_thumbnail
from src.core.models import PhotoFieldConfig
from src.ui.drop_zone import DropZoneWidget
from src.ui.icons import get_icon
from src.ui.lightbox import PhotoLightboxDialog
from src.ui.styles import ThemeManager


class DynamicRowStatus:
    EMPTY = "Kosong"
    FILLED = "Terisi"


class DynamicPhotoRow(QFrame):
    """
    Widget baris foto dinamis yang mewakili satu PhotoFieldConfig dari template.
    
    Fitur:
    - Nomor urut baris foto.
    - Label nama field foto (teks tebal).
    - Badge informasi sheet target dan sel anchor.
    - Thumbnail foto resolusi 64x64 px.
    - DropZone interaktif (drag-and-drop file gambar & klik pilih).
    - Tombol 'Pilih Foto' dan 'Hapus Foto' dengan icon resmi.
    - Badge indikator status (Kosong / Terisi).
    - Signal photo_changed(field_id, photo_path) untuk auto-save ke project.
    """

    photo_changed = Signal(str, str)  # (field_id, photo_path)
    data_changed = Signal()

    def __init__(
        self,
        field_config: PhotoFieldConfig,
        row_index: int = 1,
        parent: Optional[QFrame] = None,
    ) -> None:
        super().__init__(parent)
        self.field_config: PhotoFieldConfig = field_config
        self.row_index: int = row_index
        self.photo_path: Optional[str] = None

        self._init_ui()
        self._setup_connections()
        self.update_status()

    def _init_ui(self) -> None:
        self.setFixedHeight(84)
        self.setObjectName("DynamicPhotoRow")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, 8, 14, 8)
        main_layout.setSpacing(12)

        # 1. Nomor Urut
        self.lbl_index = QLabel(f"{self.row_index:02d}", self)
        self.lbl_index.setFixedWidth(28)
        self.lbl_index.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_index.setStyleSheet(f"""
            font-weight: 700;
            font-size: 13px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        main_layout.addWidget(self.lbl_index)

        # 2. Thumbnail Foto (64x64 px)
        self.lbl_thumbnail = QLabel(self)
        self.lbl_thumbnail.setFixedSize(THUMBNAIL_SIZE[0], THUMBNAIL_SIZE[1])
        self.lbl_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_thumbnail.setStyleSheet(f"""
            border: 1px solid {ThemeColors.BORDER};
            border-radius: 6px;
            background-color: #F1F5F9;
            color: {ThemeColors.TEXT_MUTED};
            font-size: 10px;
        """)
        self.lbl_thumbnail.setText("No Img")
        main_layout.addWidget(self.lbl_thumbnail)

        # 3. Info Field & Badge Target Sheet/Sel
        info_container = QFrame(self)
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 4, 0, 4)
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Label Nama Field Foto (Teks Tebal)
        self.lbl_field_name = QLabel(self.field_config.label, info_container)
        self.lbl_field_name.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        self.lbl_field_name.setToolTip(self.field_config.label)
        info_layout.addWidget(self.lbl_field_name)

        # Badge Info ("Sheet: Antenna | Sel: B5")
        badge_text = f"Sheet: {self.field_config.sheet_name}  |  Sel: {self.field_config.cell_anchor}"
        if self.field_config.sizing_mode == "custom":
            badge_text += f"  |  Kustom {self.field_config.custom_width}x{self.field_config.custom_height}"
        else:
            badge_text += "  |  Auto-Fit"

        self.lbl_badge = QLabel(badge_text, info_container)
        self.lbl_badge.setStyleSheet(f"""
            QLabel {{
                background-color: #EFF6FF;
                color: {ThemeColors.PRIMARY};
                border: 1px solid #BFDBFE;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            }}
        """)
        info_layout.addWidget(self.lbl_badge)
        main_layout.addWidget(info_container, stretch=1)

        # 4. DropZone (Drag & Drop + Klik Pilih)
        self.drop_zone = DropZoneWidget(self)
        self.drop_zone.setFixedWidth(240)
        self.drop_zone.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(self.drop_zone)

        # 5. Tombol Aksi (Pilih Foto & Hapus Foto)
        btn_container = QFrame(self)
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)

        self.btn_select = QPushButton("Pilih", self)
        self.btn_select.setIcon(get_icon("folder", color="#FFFFFF", size=14))
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.PRIMARY_HOVER};
            }}
        """)
        btn_layout.addWidget(self.btn_select)

        self.btn_clear = QPushButton("Hapus", self)
        self.btn_clear.setIcon(get_icon("trash", size=14))
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: #F1F5F9;
                color: {ThemeColors.TEXT};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #FEE2E2;
                border-color: #FCA5A5;
                color: {ThemeColors.ERROR};
            }}
        """)
        btn_layout.addWidget(self.btn_clear)
        main_layout.addWidget(btn_container)

        # 6. Status Badge (Kosong / Terisi)
        self.lbl_status = QLabel(DynamicRowStatus.EMPTY, self)
        self.lbl_status.setFixedWidth(72)
        self.lbl_status.setFixedHeight(24)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_status)

        p = ThemeManager.instance().get_palette()
        self.setStyleSheet(f"""
            QFrame#DynamicPhotoRow {{
                background-color: {p.SURFACE};
                border-bottom: 1px solid {p.BORDER};
            }}
        """)

    def _setup_connections(self) -> None:
        self.drop_zone.file_dropped.connect(self.set_photo)
        self.btn_select.clicked.connect(self._on_choose_photo_clicked)
        self.btn_clear.clicked.connect(self.clear_photo)

        # Klik pada thumbnail membuka Lightbox Modal
        orig_thumb_press = self.lbl_thumbnail.mousePressEvent

        def on_thumb_click(event):
            if event.button() == Qt.MouseButton.LeftButton and self.photo_path and os.path.isfile(self.photo_path):
                dlg = PhotoLightboxDialog(
                    photo_path=self.photo_path,
                    title=self.field_config.label,
                    subtitle=f"Sheet: {self.field_config.sheet_name}  |  Sel: {self.field_config.cell_anchor}",
                    parent=self,
                )
                dlg.exec()
            else:
                orig_thumb_press(event)

        self.lbl_thumbnail.mousePressEvent = on_thumb_click

        # Mengizinkan klik pada DropZone untuk memilih file
        orig_mouse_press = self.drop_zone.mousePressEvent

        def on_dropzone_click(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._on_choose_photo_clicked()
            else:
                orig_mouse_press(event)

        self.drop_zone.mousePressEvent = on_dropzone_click

    def set_row_index(self, index: int) -> None:
        """Memperbarui nomor urut baris foto."""
        self.row_index = index
        self.lbl_index.setText(f"{self.row_index:02d}")

    def _on_choose_photo_clicked(self) -> None:
        """Membuka dialog file untuk memilih foto bagi field ini."""
        ext_patterns = " ".join([f"*{ext}" for ext in SUPPORTED_EXTENSIONS])
        file_filter = f"File Gambar ({ext_patterns});;Semua Berkas (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Pilih Foto: {self.field_config.label}",
            "",
            file_filter,
        )
        if file_path:
            self.set_photo(file_path)

    def set_photo(self, photo_path: Optional[str], emit_signal: bool = True) -> None:
        """
        Menyetel foto pada baris dinamis dan memperbarui thumbnail serta status.
        
        Args:
            photo_path: Lokasi berkas gambar.
            emit_signal: Apakah memancarkan sinyal photo_changed (untuk auto-save).
        """
        if photo_path and os.path.isfile(photo_path):
            self.photo_path = os.path.abspath(photo_path)
            pixmap = create_thumbnail(self.photo_path, THUMBNAIL_SIZE)
            if pixmap and not pixmap.isNull():
                self.lbl_thumbnail.setPixmap(pixmap)
                self.lbl_thumbnail.setText("")
            else:
                self.lbl_thumbnail.setPixmap(QPixmap())
                self.lbl_thumbnail.setText("Korup")

            self.drop_zone.set_file_info(self.photo_path)
        else:
            self.clear_photo(emit_signal=emit_signal)
            return

        self.update_status()
        if emit_signal:
            self.photo_changed.emit(self.field_config.field_id, self.photo_path or "")
            self.data_changed.emit()

    def clear_photo(self, emit_signal: bool = True) -> None:
        """Mengosongkan foto dari baris dinamis."""
        self.photo_path = None
        self.lbl_thumbnail.setPixmap(QPixmap())
        self.lbl_thumbnail.setText("No Img")
        self.drop_zone.set_file_info(None)

        self.update_status()
        if emit_signal:
            self.photo_changed.emit(self.field_config.field_id, "")
            self.data_changed.emit()

    def update_status(self) -> None:
        """Memperbarui teks dan warna badge status (Kosong / Terisi) sesuai tema aktif."""
        p = ThemeManager.instance().get_palette()
        if self.photo_path and os.path.isfile(self.photo_path):
            self.lbl_status.setText(DynamicRowStatus.FILLED)
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    background-color: {p.SUCCESS_BG};
                    color: {p.SUCCESS_TEXT};
                    font-size: 11px;
                    font-weight: 700;
                    border-radius: 4px;
                    border: 1px solid {p.SUCCESS_BORDER};
                }}
            """)
            self.lbl_thumbnail.setToolTip("Klik untuk melihat foto resolusi penuh")
            self.lbl_thumbnail.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.lbl_status.setText(DynamicRowStatus.EMPTY)
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    background-color: {p.SURFACE_ALT};
                    color: {p.TEXT_MUTED};
                    font-size: 11px;
                    font-weight: 600;
                    border-radius: 4px;
                    border: 1px solid {p.BORDER};
                }}
            """)
            self.lbl_thumbnail.setToolTip("")
            self.lbl_thumbnail.setCursor(Qt.CursorShape.ArrowCursor)

    def matches_filter(self, search_text: str = "", status_filter: str = "all") -> bool:
        """
        Memeriksa apakah baris ini memenuhi kriteria pencarian dan filter status.
        """
        has_photo = bool(self.photo_path and os.path.isfile(self.photo_path))
        if status_filter == "filled" and not has_photo:
            return False
        if status_filter == "empty" and has_photo:
            return False

        if search_text:
            query = search_text.lower().strip()
            label_match = query in self.field_config.label.lower()
            sheet_match = query in self.field_config.sheet_name.lower()
            cell_match = query in self.field_config.cell_anchor.lower()
            if not (label_match or sheet_match or cell_match):
                return False

        return True

    def get_photo(self) -> Optional[str]:
        """Mengambil path foto sumber yang terpasang."""
        return self.photo_path

    def get_text(self) -> str:
        """Duck typing: field foto tidak memiliki nilai teks."""
        return ""

    def get_field_id(self) -> str:
        """Mengambil ID field foto."""
        return self.field_config.field_id

    def get_field_config(self) -> PhotoFieldConfig:
        """Mengambil model PhotoFieldConfig baris ini."""
        return self.field_config


class DynamicTextRow(QFrame):
    """
    Widget baris teks dinamis yang mewakili satu PhotoFieldConfig bertipe 'text' dari template.
    
    Fitur:
    - Nomor urut baris.
    - Label nama field teks (teks tebal).
    - Badge informasi sheet target dan sel anchor.
    - Icon visual indikator teks 64x64 px.
    - Input QLineEdit untuk teks nilai sel Excel.
    - Tombol 'Hapus' / 'Kosongkan'.
    - Badge indikator status (Kosong / Terisi).
    - Signal text_changed(field_id, text_value) untuk auto-save ke project.
    """

    text_changed = Signal(str, str)  # (field_id, text_value)
    data_changed = Signal()

    def __init__(
        self,
        field_config: PhotoFieldConfig,
        row_index: int = 1,
        parent: Optional[QFrame] = None,
    ) -> None:
        super().__init__(parent)
        self.field_config: PhotoFieldConfig = field_config
        self.row_index: int = row_index
        self.field_type: str = "text"

        self._init_ui()
        self._setup_connections()
        self.update_status()

    def _init_ui(self) -> None:
        self.setFixedHeight(84)
        self.setObjectName("DynamicTextRow")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, 8, 14, 8)
        main_layout.setSpacing(12)

        # 1. Nomor Urut
        self.lbl_index = QLabel(f"{self.row_index:02d}", self)
        self.lbl_index.setFixedWidth(28)
        self.lbl_index.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_index.setStyleSheet(f"""
            font-weight: 700;
            font-size: 13px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        main_layout.addWidget(self.lbl_index)

        # 2. Icon Visual Teks (64x64 px)
        self.lbl_icon = QLabel(self)
        self.lbl_icon.setFixedSize(THUMBNAIL_SIZE[0], THUMBNAIL_SIZE[1])
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_icon.setStyleSheet(f"""
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            background-color: #F8FAFC;
            color: {ThemeColors.PRIMARY};
            font-size: 11px;
            font-weight: 700;
        """)
        self.lbl_icon.setText("TEKS")
        main_layout.addWidget(self.lbl_icon)

        # 3. Info Field & Badge Target Sheet/Sel
        info_container = QFrame(self)
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 4, 0, 4)
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Label Nama Field Teks
        self.lbl_field_name = QLabel(self.field_config.label, info_container)
        self.lbl_field_name.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        self.lbl_field_name.setToolTip(self.field_config.label)
        info_layout.addWidget(self.lbl_field_name)

        # Badge Info
        badge_text = f"Teks  |  Sheet: {self.field_config.sheet_name}  |  Sel: {self.field_config.cell_anchor}"
        self.lbl_badge = QLabel(badge_text, info_container)
        self.lbl_badge.setStyleSheet(f"""
            QLabel {{
                background-color: #F0FDF4;
                color: #166534;
                border: 1px solid #BBF7D0;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            }}
        """)
        info_layout.addWidget(self.lbl_badge)
        main_layout.addWidget(info_container, stretch=1)

        # 4. Input Teks QLineEdit
        self.edit_text = QLineEdit(self)
        self.edit_text.setPlaceholderText(f"Ketik teks untuk sel {self.field_config.cell_anchor}...")
        self.edit_text.setFixedHeight(36)
        self.edit_text.setMinimumWidth(240)
        self.edit_text.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FFFFFF;
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 12px;
                color: {ThemeColors.TEXT};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {ThemeColors.PRIMARY};
            }}
        """)
        main_layout.addWidget(self.edit_text, stretch=1)

        # 5. Tombol Hapus / Kosongkan
        self.btn_clear = QPushButton("Hapus", self)
        self.btn_clear.setIcon(get_icon("trash", size=14))
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: #F1F5F9;
                color: {ThemeColors.TEXT};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: #FEE2E2;
                border-color: #FCA5A5;
                color: {ThemeColors.ERROR};
            }}
        """)
        main_layout.addWidget(self.btn_clear)

        # 6. Status Badge (Kosong / Terisi)
        self.lbl_status = QLabel(DynamicRowStatus.EMPTY, self)
        self.lbl_status.setFixedWidth(72)
        self.lbl_status.setFixedHeight(24)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_status)

        p = ThemeManager.instance().get_palette()
        self.setStyleSheet(f"""
            QFrame#DynamicTextRow {{
                background-color: {p.SURFACE};
                border-bottom: 1px solid {p.BORDER};
            }}
        """)

    def _setup_connections(self) -> None:
        self.edit_text.textChanged.connect(self._on_text_edited)
        self.btn_clear.clicked.connect(self.clear_text)

    def _on_text_edited(self, text: str) -> None:
        self.update_status()
        self.text_changed.emit(self.field_config.field_id, text)
        self.data_changed.emit()

    def set_row_index(self, index: int) -> None:
        """Memperbarui nomor urut baris teks."""
        self.row_index = index
        self.lbl_index.setText(f"{self.row_index:02d}")

    def set_text(self, text: Optional[str], emit_signal: bool = True) -> None:
        """Menyetel nilai teks baris dinamis."""
        val = str(text or "")
        self.edit_text.blockSignals(not emit_signal)
        self.edit_text.setText(val)
        self.edit_text.blockSignals(False)
        self.update_status()
        if emit_signal:
            self.text_changed.emit(self.field_config.field_id, val)
            self.data_changed.emit()

    def get_text(self) -> str:
        """Mengambil teks input baris ini."""
        return self.edit_text.text()

    def clear_text(self, emit_signal: bool = True) -> None:
        """Mengosongkan teks input."""
        self.set_text("", emit_signal=emit_signal)

    def get_photo(self) -> Optional[str]:
        """Duck typing: field teks tidak memiliki foto."""
        return None

    def update_status(self) -> None:
        """Memperbarui teks dan warna badge status (Kosong / Terisi) sesuai tema aktif."""
        p = ThemeManager.instance().get_palette()
        val = self.edit_text.text().strip()
        if val:
            self.lbl_status.setText(DynamicRowStatus.FILLED)
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    background-color: {p.SUCCESS_BG};
                    color: {p.SUCCESS_TEXT};
                    font-size: 11px;
                    font-weight: 700;
                    border-radius: 4px;
                    border: 1px solid {p.SUCCESS_BORDER};
                }}
            """)
        else:
            self.lbl_status.setText(DynamicRowStatus.EMPTY)
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    background-color: {p.SURFACE_ALT};
                    color: {p.TEXT_MUTED};
                    font-size: 11px;
                    font-weight: 600;
                    border-radius: 4px;
                    border: 1px solid {p.BORDER};
                }}
            """)

    def matches_filter(self, search_text: str = "", status_filter: str = "all") -> bool:
        """
        Memeriksa apakah baris teks ini memenuhi kriteria pencarian dan filter status.
        """
        has_text = bool(self.get_text().strip())
        if status_filter == "filled" and not has_text:
            return False
        if status_filter == "empty" and has_text:
            return False

        if search_text:
            query = search_text.lower().strip()
            label_match = query in self.field_config.label.lower()
            sheet_match = query in self.field_config.sheet_name.lower()
            cell_match = query in self.field_config.cell_anchor.lower()
            if not (label_match or sheet_match or cell_match):
                return False

        return True


    def get_field_id(self) -> str:
        """Mengambil ID field teks."""
        return self.field_config.field_id

    def get_field_config(self) -> PhotoFieldConfig:
        """Mengambil model PhotoFieldConfig baris ini."""
        return self.field_config


