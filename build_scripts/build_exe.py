"""
Build Script untuk Mengemas Photo Rename Studio menjadi Executable Portabel (EXE).
Mendukung eksekusi di Windows (target .exe) serta testing kompilasi lokal.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Impor generator ikon lokal jika ikon belum tersedia
try:
    from build_scripts.generate_icons import generate_app_icons
except ImportError:
    from generate_icons import generate_app_icons


def run_build(clean: bool = True) -> int:
    """Menjalankan proses build aplikasi menggunakan PyInstaller."""
    project_root = Path(__file__).resolve().parent.parent
    spec_path = project_root / "build_scripts" / "photo_rename_studio.spec"
    assets_dir = project_root / "assets"
    icon_ico = assets_dir / "icon.ico"
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    print("=" * 60)
    print("   PHOTO RENAME STUDIO - EXECUTABLE BUILD SCRIPT")
    print("=" * 60)
    print(f"Platform Saat Ini : {platform.system()} ({platform.machine()})")
    print(f"Python Executable : {sys.executable} (v{platform.python_version()})")
    print(f"Project Root      : {project_root}")
    print(f"Spec File         : {spec_path}")
    print("-" * 60)

    # 1. Pastikan aset icon tersedia
    if not icon_ico.exists():
        print("[*] Ikon aplikasi tidak ditemukan, menghasilkan ikon baru di assets/...")
        generate_app_icons(assets_dir)
    else:
        print(f"[OK] Ikon aplikasi ditemukan: {icon_ico}")

    # 2. Bersihkan sisa build sebelumnya jika diminta
    if clean:
        print("[*] Membersihkan direktori build sebelumnya (build/, dist/)...")
        for folder in [build_dir, dist_dir]:
            if folder.exists():
                try:
                    shutil.rmtree(folder)
                    print(f"    - Menghapus {folder}")
                except Exception as e:
                    print(f"    - Peringatan: Tidak dapat menghapus {folder}: {e}")

    # 3. Jalankan PyInstaller
    start_time = time.time()
    print("[*] Menjalankan PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        str(spec_path),
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
    ]

    try:
        result = subprocess.run(cmd, cwd=str(project_root), check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Kompilasi gagal dengan exit code {e.returncode}!")
        return e.returncode
    except FileNotFoundError:
        print("\n[ERROR] PyInstaller tidak ditemukan dalam environment saat ini!")
        print("Silakan install dengan: pip install pyinstaller")
        return 1

    elapsed = time.time() - start_time
    print("-" * 60)
    print(f"[OK] Build berhasil diselesaikan dalam {elapsed:.2f} detik!")

    # 4. Ringkasan Hasil Build
    exe_name = "PhotoRenameStudio.exe" if platform.system() == "Windows" else "PhotoRenameStudio"
    output_binary = dist_dir / exe_name

    if output_binary.exists():
        size_mb = output_binary.stat().st_size / (1024 * 1024)
        print(f"Lokasi File Output: {output_binary}")
        print(f"Ukuran File       : {size_mb:.2f} MB")
    else:
        print(f"Direktori Output  : {dist_dir}")
        for item in dist_dir.glob("*"):
            size_mb = item.stat().st_size / (1024 * 1024) if item.is_file() else 0
            print(f"  - {item.name} ({size_mb:.2f} MB)")

    if platform.system() != "Windows":
        print("\n[CATATAN UNTUK PENGEMBANG WINDOWS]:")
        print("Anda saat ini menjalankan build di non-Windows OS.")
        print("Untuk menghasilkan file biner Windows .exe asli, jalankan script ini di:")
        print("  Windows OS:  python build_scripts/build_exe.py")
        print("Atau gunakan runner CI/CD Windows (seperti GitHub Actions).")

    print("=" * 60)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Script Otomatisasi Build EXE Photo Rename Studio menggunakan PyInstaller"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Jangan hapus folder build/ dan dist/ sebelum kompilasi",
    )
    args = parser.parse_args()

    exit_code = run_build(clean=not args.no_clean)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
