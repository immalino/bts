"""
BTS Document Control - Konfigurasi dan Konstanta Aplikasi
"""

import sys
from pathlib import Path
from typing import Final, Tuple

# Nama Aplikasi Resmi
APP_NAME: Final[str] = "BTS Document Control"

# Menentukan direktori aset (bundle PyInstaller) dan direktori aplikasi persisten
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BUNDLE_DIR: Final[Path] = Path(sys._MEIPASS)
else:
    BUNDLE_DIR: Final[Path] = Path(__file__).resolve().parent.parent

if getattr(sys, "frozen", False):
    # Mode Executable (.exe): Data disimpan portabel di sebelah file .exe
    APP_DIR: Final[Path] = Path(sys.executable).resolve().parent
else:
    # Mode Source Code Python: Data disimpan di direktori root proyek
    APP_DIR: Final[Path] = Path(__file__).resolve().parent.parent

BASE_DIR: Final[Path] = APP_DIR
DATA_DIR: Final[Path] = APP_DIR / "data"
CLIPBOARD_DIR: Final[Path] = DATA_DIR / "clipboard"

ASSETS_DIR: Final[Path] = BUNDLE_DIR / "assets"
APP_ICON_PNG: Final[Path] = ASSETS_DIR / "icon.png"
APP_ICON_ICO: Final[Path] = ASSETS_DIR / "icon.ico"

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

