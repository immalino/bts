# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec Configuration untuk BTS Document Control.
Menghasilkan standalone Windows EXE tanpa konsol (--noconsole / --windowed).
"""

import sys
import os
from pathlib import Path

# Tentukan root direktori proyek secara absolut
SPEC_ROOT = Path(SPECPATH).resolve()
PROJECT_ROOT = SPEC_ROOT.parent if SPEC_ROOT.name == "build_scripts" else SPEC_ROOT

# Path aset dan ikon
assets_dir = PROJECT_ROOT / "assets"
icon_ico = assets_dir / "icon.ico"

# Sertakan folder assets ke dalam bundle executable
datas = []
if assets_dir.exists():
    datas.append((str(assets_dir), "assets"))

# Hidden imports yang krusial untuk PySide6, Pillow, dan openpyxl
hiddenimports = [
    "PIL",
    "PIL.Image",
    "PIL.ImageOps",
    "PIL.ExifTags",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "openpyxl",
    "openpyxl.styles",
    "openpyxl.utils",
    "openpyxl.drawing.image",
    "et_xmlfile",
]

# Modul-modul yang tidak dipakai diexclude untuk memangkas ukuran file EXE secara drastis
excludes = [
    "tkinter",
    "unittest",
    "test",
    "pytest",
    "_pytest",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.QtCharts",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtSpatialAudio",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtNetwork",
]

a = Analysis(
    [str(PROJECT_ROOT / "src" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="BTSDocumentControl",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Target tanpa konsol DOS hitam (--noconsole / --windowed)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_ico) if icon_ico.exists() else None,
)

