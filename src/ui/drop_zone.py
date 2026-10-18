"""
Photo Rename Studio - Komponen Drop Zone untuk Drag & Drop File Foto
"""

import os
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from src.config import SUPPORTED_EXTENSIONS, ThemeColors


class DropZoneWidget(QFrame):
    """
    Widget drop zone interaktif untuk menerima file gambar tunggal via drag & drop.
    
    Fitur:
    - Garis putus-putus (*dashed border*).
    - Efek visual saat drag hover (border color berubah).
    - Validasi: menerima hanya 1 file dan memastikan format berekstensi gambar didukung.
    - Signal: file_dropped(file_path: str) dipancarkan saat file valid berhasil di-drop.
    """

    file_dropped = Signal(str)

    def __init__(self, parent: Optional[QFrame] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._is_hovered: bool = False
        self._has_file: bool = False

        self._init_ui()
        self._apply_style()

    def _init_ui(self) -> None:
        self.setMinimumHeight(56)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(2)

        self.label_main = QLabel("Tarik & Lepas Foto di sini", self)
        self.label_main.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label_sub = QLabel("atau klik tombol 'Pilih Foto'", self)
        self.label_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.label_main)
        self.layout.addWidget(self.label_sub)

    def _apply_style(self) -> None:
        """Memperbarui stylesheet berdasarkan state hover atau ada file."""
        if self._is_hovered:
            border_color = ThemeColors.PRIMARY
            bg_color = "#EFF6FF"  # Biru sangat muda / light highlight
            text_color = ThemeColors.PRIMARY
            border_style = "2px dashed"
        elif self._has_file:
            border_color = ThemeColors.SUCCESS
            bg_color = "#F0FDF4"  # Hijau sangat muda
            text_color = ThemeColors.TEXT
            border_style = "1px solid"
        else:
            border_color = ThemeColors.BORDER
            bg_color = ThemeColors.SURFACE
            text_color = ThemeColors.TEXT_MUTED
            border_style = "1.5px dashed"

        self.setStyleSheet(f"""
            DropZoneWidget {{
                background-color: {bg_color};
                border: {border_style} {border_color};
                border-radius: 6px;
            }}
            QLabel {{
                background: transparent;
                border: none;
            }}
        """)
        self.label_main.setStyleSheet(f"font-size: 11px; font-weight: 500; color: {text_color};")
        self.label_sub.setStyleSheet(f"font-size: 10px; color: {ThemeColors.TEXT_MUTED};")

    def set_file_info(self, file_path: Optional[str]) -> None:
        """Menyetel tampilan teks ketika file foto telah dipilih/dikosongkan."""
        if file_path:
            self._has_file = True
            filename = os.path.basename(file_path)
            self.label_main.setText(filename)
            self.label_main.setToolTip(file_path)
            self.label_sub.setText("Foto terpasang (Tarik foto lain untuk mengganti)")
        else:
            self._has_file = False
            self.label_main.setText("Tarik & Lepas Foto di sini")
            self.label_main.setToolTip("")
            self.label_sub.setText("atau klik tombol 'Pilih Foto'")
        self._apply_style()

    def _extract_valid_image_path(self, mime_data) -> Optional[str]:
        """Memeriksa MIME data dan mengekstrak path file jika valid."""
        if not mime_data.hasUrls():
            return None

        urls = mime_data.urls()
        # Batasi hanya 1 file
        if len(urls) != 1:
            return None

        file_url = urls[0]
        if not file_url.isLocalFile():
            return None

        file_path = file_url.toLocalFile()
        ext = os.path.splitext(file_path)[1].lower()
        if ext in SUPPORTED_EXTENSIONS and os.path.isfile(file_path):
            return file_path

        return None

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Menerima drag jika data adalah file gambar valid."""
        valid_path = self._extract_valid_image_path(event.mimeData())
        if valid_path:
            event.acceptProposedAction()
            self._is_hovered = True
            self._apply_style()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Menjaga event drag tetap aktif selama berada di atas widget."""
        valid_path = self._extract_valid_image_path(event.mimeData())
        if valid_path:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        """Mengembalikan style normal saat pointer drag meninggalkan widget."""
        self._is_hovered = False
        self._apply_style()
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        """Menangani drop file dan memancarkan sinyal file_dropped."""
        self._is_hovered = False
        self._apply_style()

        valid_path = self._extract_valid_image_path(event.mimeData())
        if valid_path:
            event.acceptProposedAction()
            self.file_dropped.emit(valid_path)
        else:
            event.ignore()
