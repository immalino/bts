"""
Photo Rename Studio - Konfigurasi dan Konstanta Aplikasi
"""

from typing import Final, Tuple

# Ekstensi gambar yang didukung aplikasi
SUPPORTED_EXTENSIONS: Final[Tuple[str, ...]] = (
    '.jpg',
    '.jpeg',
    '.png',
    '.webp',
    '.bmp',
    '.gif',
    '.tiff',
    '.tif',
)

# Jumlah baris default di antarmuka
DEFAULT_ROW_COUNT: Final[int] = 100

# Dimensi ukuran thumbnail foto (lebar, tinggi) dalam piksel
THUMBNAIL_SIZE: Final[Tuple[int, int]] = (64, 64)

# Konfigurasi Palet Warna Tema (Clean & Modern)
class ThemeColors:
    PRIMARY = "#2563EB"       # Biru utama (actions / buttons)
    PRIMARY_HOVER = "#1D4ED8" # Biru gelap saat hover
    BACKGROUND = "#F8FAFC"    # Latar belakang aplikasi terang
    SURFACE = "#FFFFFF"       # Kartu / baris input
    BORDER = "#E2E8F0"        # Garis batas default
    BORDER_FOCUS = "#3B82F6"  # Garis batas saat fokus
    TEXT = "#1E293B"          # Teks utama
    TEXT_MUTED = "#64748B"    # Teks sekunder / placeholder
    SUCCESS = "#10B981"       # Status berhasil / valid
    ERROR = "#EF4444"         # Status error / duplikasi
    WARNING = "#F59E0B"       # Status peringatan

