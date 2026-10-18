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
    QPushButton,
    QStyle,
    QVBoxLayout,
)

from src.config import SUPPORTED_EXTENSIONS, THUMBNAIL_SIZE, ThemeColors
from src.core.image_loader import create_thumbnail
from src.core.models import PhotoFieldConfig
from src.ui.drop_zone import DropZoneWidget


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
        self.btn_select.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
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
        self.btn_clear.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
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

        self.setStyleSheet(f"""
            QFrame#DynamicPhotoRow {{
                background-color: {ThemeColors.SURFACE};
                border-bottom: 1px solid {ThemeColors.BORDER};
            }}
        """)

    def _setup_connections(self) -> None:
        self.drop_zone.file_dropped.connect(self.set_photo)
        self.btn_select.clicked.connect(self._on_choose_photo_clicked)
        self.btn_clear.clicked.connect(self.clear_photo)

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
        """Memperbarui teks dan warna badge status (Kosong / Terisi)."""
        if self.photo_path and os.path.isfile(self.photo_path):
            self.lbl_status.setText(DynamicRowStatus.FILLED)
            self.lbl_status.setStyleSheet("""
                QLabel {
                    background-color: #DCFCE7;
                    color: #166534;
                    font-size: 11px;
                    font-weight: 700;
                    border-radius: 4px;
                    border: 1px solid #BBF7D0;
                }
            """)
        else:
            self.lbl_status.setText(DynamicRowStatus.EMPTY)
            self.lbl_status.setStyleSheet(f"""
                QLabel {{
                    background-color: #F1F5F9;
                    color: {ThemeColors.TEXT_MUTED};
                    font-size: 11px;
                    font-weight: 600;
                    border-radius: 4px;
                    border: 1px solid {ThemeColors.BORDER};
                }}
            """)

    def get_photo(self) -> Optional[str]:
        """Mengambil path foto sumber yang terpasang."""
        return self.photo_path

    def get_field_id(self) -> str:
        """Mengambil ID field foto."""
        return self.field_config.field_id

    def get_field_config(self) -> PhotoFieldConfig:
        """Mengambil model PhotoFieldConfig baris ini."""
        return self.field_config
