"""
Unit tests untuk memverifikasi kesiapan aset ikon, konfigurasi build PyInstaller, dan dokumentasi.
"""

from pathlib import Path
from PIL import Image

from src.config import APP_ICON_ICO, APP_ICON_PNG, ASSETS_DIR, BASE_DIR


def test_asset_paths_and_files_exist():
    """Memastikan direktori assets dan file icon ada serta terbaca."""
    assert ASSETS_DIR.exists(), "Direktori assets harus ada."
    assert APP_ICON_PNG.exists(), "File assets/icon.png harus ada."
    assert APP_ICON_ICO.exists(), "File assets/icon.ico harus ada."


def test_icon_properties():
    """Memastikan icon.png dan icon.ico valid dan memiliki resolusi yang tepat."""
    with Image.open(APP_ICON_PNG) as img:
        assert img.format == "PNG"
        assert img.size == (256, 256)
        assert img.mode in ("RGBA", "RGB")

    with Image.open(APP_ICON_ICO) as img:
        assert img.format == "ICO"
        assert img.size[0] >= 16


def test_pyinstaller_spec_configuration():
    """Memastikan file spec PyInstaller memuat konfigurasi noconsole, ikon, dan excludes."""
    spec_path = BASE_DIR / "build_scripts" / "photo_rename_studio.spec"
    assert spec_path.exists(), "File build_scripts/photo_rename_studio.spec harus ada."

    content = spec_path.read_text(encoding="utf-8")
    assert "console=False" in content, "Target executable harus noconsole / windowed."
    assert "icon.ico" in content, "Spec harus menetapkan ikon aplikasi."
    assert "excludes=" in content, "Spec harus mengabaikan modul yang tidak digunakan."
    assert "PySide6.QtWebEngineCore" in content, "Spec harus mengabaikan modul berat seperti WebEngine."


def test_build_exe_script():
    """Memastikan script build_exe.py tersedia dan siap dijalankan."""
    build_script = BASE_DIR / "build_scripts" / "build_exe.py"
    assert build_script.exists(), "File build_scripts/build_exe.py harus ada."

    content = build_script.read_text(encoding="utf-8")
    assert "PyInstaller" in content
    assert "photo_rename_studio.spec" in content


def test_readme_documentation_completeness():
    """Memastikan README.md ada dan mencakup seluruh aspek penting proyek."""
    readme_path = BASE_DIR / "README.md"
    assert readme_path.exists(), "README.md harus ada."

    content = readme_path.read_text(encoding="utf-8")
    required_keywords = [
        "Photo Rename Studio",
        "Fitur Utama",
        "Zero Data Loss",
        "Dukungan Format File",
        "Instalasi",
        "Panduan Penggunaan",
        "PyInstaller",
        "Windows EXE",
        "--noconsole",
        "pytest",
    ]
    for kw in required_keywords:
        assert kw in content, f"README.md harus mencakup topik: '{kw}'"
