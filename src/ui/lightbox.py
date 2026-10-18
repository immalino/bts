"""
BTS Document Control - Lightbox Preview Modal Dialog
Menyediakan jendela pratinjau foto resolusi penuh interaktif dengan metadata:
dimensi gambar, ukuran file, orientasi, serta tombol pintas buka file.
"""

import os
from pathlib import Path
from typing import Optional

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.config import APP_ICON_PNG
from src.core.image_loader import load_image_with_exif
from src.ui.icons import get_icon
from src.ui.styles import ThemeManager
from src.utils.file_utils import reveal_in_explorer


class PhotoLightboxDialog(QDialog):
    """
    Dialog modal modern untuk melihat foto lapangan dalam resolusi penuh.
    Memungkinkan document controller dan engineer memeriksa ketajaman foto,
    detail objek, dan metadata sebelum digenerate ke laporan Excel.
    """

    def __init__(
        self,
        photo_path: str,
        title: str = "Pratinjau Foto",
        subtitle: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.photo_path = photo_path
        self.dialog_title = title
        self.dialog_subtitle = subtitle

        self._init_ui()
        self._load_photo()

    def _init_ui(self) -> None:
        self.setWindowTitle(f"Pratinjau: {self.dialog_title}")
        self.resize(800, 640)
        self.setMinimumSize(600, 480)
        self.setModal(True)

        if APP_ICON_PNG.is_file():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # 1. Header Card
        header_frame = QFrame(self)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)

        self.lbl_title = QLabel(self.dialog_title, header_frame)
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        title_container.addWidget(self.lbl_title)

        if self.dialog_subtitle:
            self.lbl_subtitle = QLabel(self.dialog_subtitle, header_frame)
            self.lbl_subtitle.setStyleSheet("font-size: 12px; opacity: 0.8;")
            title_container.addWidget(self.lbl_subtitle)

        header_layout.addLayout(title_container)
        header_layout.addStretch(1)

        # Tombol Buka di File Explorer
        self.btn_open_file = QPushButton("Buka Berkas", header_frame)
        self.btn_open_file.setIcon(get_icon("external_link", size=14))
        self.btn_open_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_file.clicked.connect(self._on_open_file_clicked)
        header_layout.addWidget(self.btn_open_file)

        # Tombol Tutup
        self.btn_close = QPushButton("Tutup", header_frame)
        self.btn_close.setIcon(get_icon("x", size=14))
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.accept)
        header_layout.addWidget(self.btn_close)

        layout.addWidget(header_frame)

        # 2. Area Gambar (Scrollable Preview)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.img_container = QWidget()
        self.img_layout = QVBoxLayout(self.img_container)
        self.img_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_image = QLabel(self.img_container)
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setScaledContents(False)
        self.img_layout.addWidget(self.lbl_image)

        self.scroll_area.setWidget(self.img_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # 3. Footer Bar: Metadata (Dimensi & Ukuran Berkas)
        footer_frame = QFrame(self)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(4, 2, 4, 2)
        footer_layout.setSpacing(12)

        self.lbl_meta_dims = QLabel("Dimensi: -", footer_frame)
        self.lbl_meta_dims.setStyleSheet("font-size: 11px; font-weight: 600;")
        footer_layout.addWidget(self.lbl_meta_dims)

        self.lbl_meta_size = QLabel("Ukuran: -", footer_frame)
        self.lbl_meta_size.setStyleSheet("font-size: 11px; font-weight: 600;")
        footer_layout.addWidget(self.lbl_meta_size)

        footer_layout.addStretch(1)

        self.lbl_path = QLabel("", footer_frame)
        self.lbl_path.setStyleSheet("font-size: 11px; opacity: 0.7;")
        footer_layout.addWidget(self.lbl_path)

        layout.addWidget(footer_frame)

    def _load_photo(self) -> None:
        """Memuat gambar dan menampilkan metadata."""
        if not self.photo_path or not os.path.isfile(self.photo_path):
            self.lbl_image.setText("Berkas foto tidak ditemukan atau korup.")
            return

        self.lbl_path.setText(os.path.basename(self.photo_path))
        self.lbl_path.setToolTip(self.photo_path)

        try:
            # Dapatkan info ukuran file
            file_bytes = os.path.getsize(self.photo_path)
            if file_bytes < 1024 * 1024:
                size_str = f"{file_bytes / 1024:.1f} KB"
            else:
                size_str = f"{file_bytes / (1024 * 1024):.2f} MB"
            self.lbl_meta_size.setText(f"Ukuran: {size_str}")

            # Muat gambar dengan koreksi orientasi EXIF
            pil_img = load_image_with_exif(self.photo_path)
            if pil_img:
                width, height = pil_img.size
                self.lbl_meta_dims.setText(f"Dimensi: {width} × {height} px")

                # Skala gambar agar pas dengan dialog (maksimal 1600x1200)
                max_w, max_h = 1000, 700
                scale = min(max_w / width, max_h / height, 1.0)
                display_w = int(width * scale)
                display_h = int(height * scale)

                resized = pil_img.resize((display_w, display_h), Image.Resampling.LANCZOS)
                
                # Konversi ke QPixmap
                from PIL.ImageQt import ImageQt
                qimage = ImageQt(resized)
                pixmap = QPixmap.fromImage(qimage)
                self.lbl_image.setPixmap(pixmap)
            else:
                self.lbl_image.setText("Gagal membaca citra gambar.")
        except Exception as e:
            self.lbl_image.setText(f"Error memuat gambar: {e}")

    def _on_open_file_clicked(self) -> None:
        """Membuka folder lokasi file foto di file manager sistem."""
        if self.photo_path and os.path.isfile(self.photo_path):
            reveal_in_explorer(self.photo_path)

