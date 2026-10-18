"""
Photo Rename Studio - Pembuat Thumbnail Foto Hemat Memori
"""

from typing import Optional, Tuple
import io
import os
import sys

from PIL import Image, ImageOps
from PySide6.QtGui import QGuiApplication, QImage, QPixmap

from src.config import THUMBNAIL_SIZE


def _ensure_gui_app() -> Optional[QGuiApplication]:
    """Memastikan instance QGuiApplication ada agar QPixmap dapat dibuat."""
    app = QGuiApplication.instance()
    if app is None:
        # Gunakan platform offscreen jika tidak ada DISPLAY (misal saat unit test / headless)
        if "QT_QPA_PLATFORM" not in os.environ and "DISPLAY" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
        app = QGuiApplication(sys.argv)
    return app


def create_thumbnail(
    image_path: str,
    size: Tuple[int, int] = THUMBNAIL_SIZE
) -> Optional[QPixmap]:
    """
    Memuat gambar dari disk dan menghasilkan QPixmap thumbnail secara hemat memori.
    
    Fitur:
    - Koreksi orientasi EXIF (misal foto kamera potret/lanskap agar tidak terputar 90 derajat).
    - Memanfaatkan Image.thumbnail() untuk downsampling efisien tanpa memuat ukuran penuh ke RAM secara persisten.
    - Menangani fallback jika file gambar corrupt, tidak ditemukan, atau format tidak didukung (mengembalikan None).
    """
    if not image_path or not os.path.exists(image_path) or not os.path.isfile(image_path):
        return None

    try:
        with Image.open(image_path) as img:
            # Koreksi rotasi berdasarkan metadata orientasi EXIF kamera
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                # Jika metadata EXIF rusak atau tidak bisa dibaca, lanjutkan dengan gambar asli
                pass

            # Konversi jika format palet/warna tidak langsung didukung PNG (misal CMYK)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")

            # Ubah ukuran secara proporsional dengan resampling lanczos berkualitas tinggi
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Simpan hasil thumbnail ke buffer in-memory
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer_bytes = buffer.getvalue()

        _ensure_gui_app()

        qimg = QImage.fromData(buffer_bytes)
        if qimg.isNull():
            return None

        pixmap = QPixmap.fromImage(qimg)
        if pixmap.isNull():
            return None

        return pixmap

    except Exception:
        # Fallback aman jika file rusak / korup / invalid
        return None
