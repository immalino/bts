"""
Photo Rename Studio - Komponen Row Widget
"""

import os
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.config import SUPPORTED_EXTENSIONS, THUMBNAIL_SIZE, ThemeColors
from src.core.image_loader import create_thumbnail
from src.core.validator import validate_single_filename
from src.ui.drop_zone import DropZoneWidget
from src.ui.icons import get_icon
from src.ui.lightbox import PhotoLightboxDialog
from src.ui.styles import ThemeManager
from src.utils.file_utils import split_filename_and_ext


class RowStatus:
    EMPTY = "Kosong"
    READY = "Siap"
    ERROR = "Error"
    SUCCESS = "Sukses"


class RowWidget(QFrame):
    """
    Komponen representasi 1 baris foto dan nama tujuan.
    
    Elemen:
    - Label nomor urut.
    - Thumbnail foto 64x64 px.
    - Area DropZoneWidget & info file sumber.
    - Input QLineEdit untuk target stem nama file + label ekstensi file otomatis.
    - Tombol "Pilih Foto" dan tombol "Hapus Foto".
    - Badge / Label indikator status baris (Kosong, Siap, Error, Sukses).
    """

    data_changed = Signal()

    def __init__(self, row_index: int = 1, parent: Optional[QFrame] = None):
        super().__init__(parent)
        self.row_index: int = row_index
        self.source_photo: Optional[str] = None
        self._target_stem: str = ""
        self._extension: str = ""
        self._status: str = RowStatus.EMPTY
        self._status_message: str = ""

        self._init_ui()
        self._setup_connections()
        self.update_status()

    def _init_ui(self) -> None:
        self.setFixedHeight(84)
        self.setObjectName("RowWidget")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(12)

        # 1. Nomor Urut
        self.lbl_index = QLabel(f"{self.row_index:02d}", self)
        self.lbl_index.setFixedWidth(28)
        self.lbl_index.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_index.setStyleSheet(f"""
            font-weight: bold;
            font-size: 13px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        main_layout.addWidget(self.lbl_index)

        # 2. Thumbnail Foto
        self.lbl_thumbnail = QLabel(self)
        self.lbl_thumbnail.setFixedSize(THUMBNAIL_SIZE[0], THUMBNAIL_SIZE[1])
        self.lbl_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_thumbnail.setStyleSheet(f"""
            border: 1px solid {ThemeColors.BORDER};
            border-radius: 4px;
            background-color: #F1F5F9;
            color: {ThemeColors.TEXT_MUTED};
            font-size: 10px;
        """)
        self.lbl_thumbnail.setText("No Img")
        main_layout.addWidget(self.lbl_thumbnail)

        # 3. Area DropZone (Drag & Drop)
        self.drop_zone = DropZoneWidget(self)
        self.drop_zone.setFixedWidth(240)
        main_layout.addWidget(self.drop_zone)

        # 4. Input Target Name + Ekstensi
        name_container = QFrame(self)
        name_layout = QHBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(4)

        self.input_name = QLineEdit(self)
        self.input_name.setPlaceholderText("Nama file baru (tanpa ekstensi)...")
        self.input_name.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                background-color: {ThemeColors.SURFACE};
                color: {ThemeColors.TEXT};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {ThemeColors.BORDER_FOCUS};
            }}
        """)
        name_layout.addWidget(self.input_name, stretch=1)

        self.lbl_extension = QLabel("", self)
        self.lbl_extension.setMinimumWidth(44)
        self.lbl_extension.setStyleSheet(f"""
            color: {ThemeColors.TEXT_MUTED};
            font-size: 12px;
            font-weight: 500;
        """)
        name_layout.addWidget(self.lbl_extension)

        main_layout.addWidget(name_container, stretch=1)

        # 5. Tombol Aksi (Pilih Foto & Hapus Foto)
        btn_container = QFrame(self)
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(6)

        self.btn_select = QPushButton("Pilih Foto", self)
        self.btn_select.setIcon(get_icon("folder", color="#FFFFFF", size=14))
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.PRIMARY_HOVER};
            }}
        """)
        btn_layout.addWidget(self.btn_select)

        self.btn_clear = QPushButton("Hapus Foto", self)
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
            }}
            QPushButton:hover {{
                background-color: #E2E8F0;
                color: {ThemeColors.ERROR};
            }}
        """)
        btn_layout.addWidget(self.btn_clear)

        main_layout.addWidget(btn_container)

        # 6. Status Badge
        self.lbl_status = QLabel(RowStatus.EMPTY, self)
        self.lbl_status.setFixedWidth(70)
        self.lbl_status.setFixedHeight(24)
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_status)

        p = ThemeManager.instance().get_palette()
        self.setStyleSheet(f"""
            QFrame#RowWidget {{
                background-color: {p.SURFACE};
                border-bottom: 1px solid {p.BORDER};
            }}
        """)

    def _setup_connections(self) -> None:
        self.drop_zone.file_dropped.connect(self.set_source_photo)
        self.btn_select.clicked.connect(self._on_choose_photo_clicked)
        self.btn_clear.clicked.connect(self.clear_photo)
        self.input_name.textChanged.connect(self._on_target_name_changed)

        # Klik pada thumbnail membuka Lightbox Modal
        orig_thumb_press = self.lbl_thumbnail.mousePressEvent

        def on_thumb_click(event):
            if event.button() == Qt.MouseButton.LeftButton and self.source_photo and os.path.isfile(self.source_photo):
                dlg = PhotoLightboxDialog(
                    photo_path=self.source_photo,
                    title=f"Baris #{self.row_index:02d}",
                    subtitle=os.path.basename(self.source_photo),
                    parent=self,
                )
                dlg.exec()
            else:
                orig_thumb_press(event)

        self.lbl_thumbnail.mousePressEvent = on_thumb_click

    def set_row_index(self, index: int) -> None:
        """Memperbarui nomor urut baris."""
        self.row_index = index
        self.lbl_index.setText(f"{self.row_index:02d}")

    def _on_choose_photo_clicked(self) -> None:
        """Membuka QFileDialog untuk memilih foto tunggal."""
        ext_patterns = " ".join([f"*{ext}" for ext in SUPPORTED_EXTENSIONS])
        file_filter = f"File Gambar ({ext_patterns});;Semua File (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Pilih Foto untuk Baris #{self.row_index}",
            "",
            file_filter
        )
        if file_path:
            self.set_source_photo(file_path)

    def _on_target_name_changed(self, text: str) -> None:
        self._target_stem = text.strip()
        self.update_status()
        self.data_changed.emit()

    def set_source_photo(self, photo_path: Optional[str]) -> None:
        """Menyetel foto sumber dan membuat thumbnail 64x64 px."""
        if photo_path and os.path.isfile(photo_path):
            self.source_photo = os.path.abspath(photo_path)
            _, ext = split_filename_and_ext(self.source_photo)
            self._extension = ext.lower()
            self.lbl_extension.setText(self._extension)

            # Buat thumbnail via image_loader
            pixmap = create_thumbnail(self.source_photo, THUMBNAIL_SIZE)
            if pixmap and not pixmap.isNull():
                self.lbl_thumbnail.setPixmap(pixmap)
                self.lbl_thumbnail.setText("")
            else:
                self.lbl_thumbnail.setPixmap(QPixmap())
                self.lbl_thumbnail.setText("Corrupt")

            self.drop_zone.set_file_info(self.source_photo)
        else:
            self.clear_photo()
            return

        self.update_status()
        self.data_changed.emit()

    def clear_photo(self) -> None:
        """Mengosongkan foto dari baris (tanpa menghapus baris itu sendiri)."""
        self.source_photo = None
        self._extension = ""
        self.lbl_extension.setText("")
        self.lbl_thumbnail.setPixmap(QPixmap())
        self.lbl_thumbnail.setText("No Img")
        self.drop_zone.set_file_info(None)

        self.update_status()
        self.data_changed.emit()

    def set_target_name(self, name: str) -> None:
        """Menyetel nilai nama tujuan ke input teks."""
        # Jika nama yang dimasukkan memiliki ekstensi, kita pisahkan stem-nya
        stem, _ = split_filename_and_ext(name)
        self.input_name.setText(stem)

    def set_data(self, source_photo: Optional[str] = None, target_name: Optional[str] = None) -> None:
        """Menyetel foto dan target nama sekaligus."""
        if target_name is not None:
            self.set_target_name(target_name)
        if source_photo is not None:
            self.set_source_photo(source_photo)

    def get_data(self) -> Dict[str, Any]:
        """Mengambil data baris saat ini."""
        stem = self.input_name.text().strip()
        target_fullname = f"{stem}{self._extension}" if (stem and self._extension) else stem
        return {
            "row_index": self.row_index,
            "source_photo": self.source_photo,
            "source_path": self.source_photo,
            "target_stem": stem,
            "extension": self._extension,
            "target_name": target_fullname,
            "status": self._status,
            "status_message": self._status_message,
        }

    def set_status(self, status: str, message: str = "") -> None:
        """Menyetel status baris secara eksplisit (misal dari MainWindow validator / exporter)."""
        self._status = status
        self._status_message = message
        self._update_status_badge()

    def update_status(self) -> None:
        """Memperbarui status baris secara otomatis berdasarkan foto dan nama tujuan."""
        stem = self.input_name.text().strip()

        # Status: Kosong (belum ada foto dan belum ada target nama)
        if not self.source_photo and not stem:
            self._status = RowStatus.EMPTY
            self._status_message = "Baris kosong"
        elif not self.source_photo and stem:
            # Ada nama tapi belum ada foto
            self._status = RowStatus.EMPTY
            self._status_message = "Foto belum dipilih"
        elif self.source_photo and not stem:
            # Ada foto tapi belum ada nama
            self._status = RowStatus.EMPTY
            self._status_message = "Nama baru belum diisi"
        else:
            # Kedua foto dan stem ada -> validasi nama
            validation = validate_single_filename(f"{stem}{self._extension}")
            if not validation.is_valid:
                self._status = RowStatus.ERROR
                self._status_message = validation.error_message
            else:
                self._status = RowStatus.READY
                self._status_message = "Siap untuk diproses"

        self._update_status_badge()

    def _update_status_badge(self) -> None:
        """Memperbarui tampilan visual badge status dan border baris sesuai tema aktif."""
        p = ThemeManager.instance().get_palette()
        text = self._status
        tooltip = self._status_message

        if self._status == RowStatus.READY:
            bg_color = p.SUCCESS_BG
            text_color = p.SUCCESS_TEXT
            border_left = f"4px solid {p.SUCCESS}"
        elif self._status == RowStatus.SUCCESS:
            bg_color = p.SUCCESS_BG
            text_color = p.SUCCESS_TEXT
            border_left = f"4px solid {p.SUCCESS}"
        elif self._status == RowStatus.ERROR:
            bg_color = p.DANGER_BG
            text_color = p.DANGER_TEXT
            border_left = f"4px solid {p.DANGER}"
        else:  # EMPTY / default
            bg_color = p.SURFACE_ALT
            text_color = p.TEXT_MUTED
            border_left = "4px solid transparent"

        self.lbl_status.setText(text)
        self.lbl_status.setToolTip(tooltip)
        self.lbl_status.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        self.setStyleSheet(f"""
            QFrame#RowWidget {{
                background-color: {p.SURFACE};
                border-bottom: 1px solid {p.BORDER};
                border-left: {border_left};
            }}
        """)

