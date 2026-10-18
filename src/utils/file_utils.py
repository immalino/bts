"""
Photo Rename Studio - Utilitas File dan String
"""

import os
import re
from typing import Final, Set, Tuple

# Karakter ilegal pada nama file di sistem Windows: \ / : * ? " < > |
WINDOWS_ILLEGAL_CHARS: Final[Set[str]] = set(r'\/:*?"<>|')
WINDOWS_ILLEGAL_REGEX: Final[re.Pattern] = re.compile(r'[\\/:*?"<>|]')

# Reserved device names di Windows (case-insensitive, tidak boleh digunakan sebagai stem)
# CON, PRN, AUX, NUL, COM1-COM9, LPT1-LPT9
WINDOWS_RESERVED_NAMES: Final[Set[str]] = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def split_filename_and_ext(filename: str) -> Tuple[str, str]:
    """
    Memisahkan nama file dan ekstensinya.
    Mengembalikan tuple (stem, ext). Contoh: 'foto.jpg' -> ('foto', '.jpg')
    """
    stem, ext = os.path.splitext(filename)
    return stem, ext


def is_windows_reserved_name(name: str) -> bool:
    """
    Memeriksa apakah stem nama file merupakan salah satu reserved name Windows.
    Pemeriksaan dilakukan secara case-insensitive pada nama dasar (tanpa ekstensi).
    """
    stem, _ = split_filename_and_ext(name)
    return stem.strip().upper() in WINDOWS_RESERVED_NAMES


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """
    Membersihkan nama file dari karakter ilegal Windows dan trailing spaces/dots.
    Mengganti karakter ilegal dengan `replacement`.
    """
    # Ganti karakter ilegal
    sanitized = WINDOWS_ILLEGAL_REGEX.sub(replacement, name)
    # Hapus spasi dan titik di awal dan akhir
    sanitized = sanitized.strip(" .")
    return sanitized


def open_folder_in_explorer(folder_path: str) -> bool:
    """
    Membuka folder di file explorer sistem (Windows Explorer, macOS Finder, atau Linux File Manager).
    Mengembalikan True jika perintah berhasil dijalankan, False jika gagal.
    """
    import subprocess
    import sys

    if not folder_path or not os.path.isdir(folder_path):
        return False

    abs_path = os.path.abspath(folder_path)
    try:
        if sys.platform == "win32":
            os.startfile(abs_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", abs_path])
        else:
            subprocess.Popen(["xdg-open", abs_path])
        return True
    except Exception:
        return False


def reveal_in_explorer(file_path: str) -> bool:
    """
    Membuka file manager dan menyorot berkas tertentu (Windows / macOS / Linux).
    """
    import subprocess
    import sys

    if not file_path or not os.path.exists(file_path):
        return False

    abs_path = os.path.abspath(file_path)
    try:
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", abs_path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", abs_path])
        else:
            parent_dir = os.path.dirname(abs_path)
            subprocess.Popen(["xdg-open", parent_dir])
        return True
    except Exception:
        return False



