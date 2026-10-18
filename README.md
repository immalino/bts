# Photo Rename Studio 📸✨

> **Aplikasi desktop modern, cepat, dan aman untuk penggantian nama foto massal (batch renaming) dengan antarmuka visual interaktif.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52.svg)](https://wiki.qt.io/Qt_for_Python)
[![Pillow](https://img.shields.io/badge/image-Pillow-yellow.svg)](https://python-pillow.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-informational.svg)](LICENSE)

---

## 📌 Daftar Isi
1. [Tentang Aplikasi](#-tentang-aplikasi)
2. [Fitur Utama](#-fitur-utama)
3. [Jaminan Keamanan File (Zero Data Loss)](#-jaminan-keamanan-file-zero-data-loss)
4. [Dukungan Format File Foto](#-dukungan-format-file-foto)
5. [Struktur Proyek](#-struktur-proyek)
6. [Instalasi & Menjalankan dari Source Code](#-instalasi--menjalankan-dari-source-code)
7. [Panduan Penggunaan Langkah-demi-Langkah](#-panduan-penggunaan-langkah-demi-langkah)
8. [Panduan Build Windows EXE Portabel](#-panduan-build-windows-exe-portabel)
9. [Menjalankan Pengujian Otomatis (Unit Tests)](#-menjalankan-pengujian-otomatis-unit-tests)
10. [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 📖 Tentang Aplikasi

**Photo Rename Studio** dirancang khusus untuk fotografer, pengelola aset visual, panitia buku tahunan sekolah (BTS), staf administrasi, dan profesional kreatif yang sering menghadapi tantangan mengganti nama ratusan hingga ribuan foto secara berurutan sesuai daftar nama (misalnya daftar siswa, nomor induk, atau kode produk).

Dengan pendekatan visual drag-and-drop dan verifikasi real-time, pengguna dapat memetakan foto sumber ke nama target baru tanpa risiko kehilangan data atau kesalahan pengetikan karakter ilegal Windows.

---

## ✨ Fitur Utama

- 🎨 **Antarmuka Bersih & Modern**: Dibangun menggunakan PySide6 (Qt6) dengan palet warna kontras yang ramah mata (*Slate Blue & Emerald*).
- 🖱️ **Drag-and-Drop Intuitif**: Tarik dan lepas (*drag-and-drop*) file foto langsung dari File Explorer Windows ke baris yang diinginkan.
- 🖼️ **Thumbnail Preview Otomatis**: Pratinjau instan foto thumbnail dengan orientasi EXIF otomatis (foto tegak tidak akan terbalik).
- 📋 **Impor Nama Massal (TXT & CSV)**:
  - Dukungan file `.txt` (satu nama per baris).
  - Dukungan file `.csv` dengan berbagai delimiter (koma `,`, titik koma `;`, atau tab `\t`) dan pemilihan kolom target secara otomatis atau interaktif.
  - Auto-expand: Baris otomatis bertambah jika nama yang diimpor melebihi 100 baris.
- 🛡️ **Validasi Aturan Penamaan Windows Real-Time**:
  - Deteksi dan peringatan karakter ilegal Windows (`\ / : * ? " < > |`).
  - Pencegahan nama reserved Windows (`CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`).
  - Deteksi nama duplikat secara *case-insensitive* (`Foto.jpg` vs `foto.jpg`).
  - Penanganan spasi dan titik di akhir nama.
- ⚡ **Background Processing & Multi-Threading**:
  - Proses penyalinan berjalan di thread terpisah (`QThread`) sehingga UI tetap responsif tanpa *freeze*.
  - Dilengkapi tombol pembatalan proses (*Cancel*) yang aman sewaktu-waktu.
- 📊 **Progress Bar & Dialog Laporan Interaktif**:
  - Indikator persentase penyalinan real-time.
  - Dialog laporan hasil akhir dengan kartu statistik (Total, Berhasil, Gagal, Dilewati).
  - Tab rincian log kesalahan dengan tombol salin log (*Copy to Clipboard*).
  - Tombol pintasan langsung membuka folder hasil di File Explorer.

---

## 🔒 Jaminan Keamanan File (Zero Data Loss)

Keamanan data foto sumber Anda adalah prioritas nomor satu. Photo Rename Studio menerapkan arsitektur perlindungan data yang ketat:

1. **Non-Destructive Copying**:
   - Aplikasi **TIDAK PERNAH** menggunakan perintah `os.rename()` atau `shutil.move()` pada file foto asli.
   - Aplikasi menggunakan `shutil.copy2()`, yang membuat salinan baru ke folder tujuan sambil mempertahankan metadata asli foto (*date modified*, dsb).
   - Foto sumber Anda tetap 100% utuh di lokasi awalnya.
2. **Perlindungan Terhadap Overwrite yang Tidak Disengaja**:
   - Jika file dengan nama target sudah ada di folder tujuan, sistem secara default **menolak** menimpa file tersebut dan menandainya sebagai error/skip.
   - Pengguna harus secara sadar mencentang kotak *Checkbox* **"Timpa file jika sudah ada"** jika memang bermaksud menimpa file lama.
3. **Penyalinan Ekstensi Asli Otomatis**:
   - Ekstensi file asli (`.jpg`, `.png`, dll.) selalu dipertahankan secara otomatis meskipun pengguna tidak mengetikkan ekstensi pada kolom nama baru.

---

## 📁 Dukungan Format File Foto

Photo Rename Studio mendukung berbagai format citra raster modern:

| Format | Ekstensi yang Didukung | Keterangan |
| :--- | :--- | :--- |
| **JPEG** | `.jpg`, `.jpeg` | Mendukung EXIF Auto-Orientation |
| **PNG** | `.png` | Mendukung transparansi RGBA |
| **WebP** | `.webp` | Format web modern kompresi tinggi |
| **BMP** | `.bmp` | Windows Bitmap format standar |
| **TIFF** | `.tiff`, `.tif` | Format master fotografi resolusi tinggi |
| **GIF** | `.gif` | Format citra diam/animasi frame pertama |

---

## 🏗️ Struktur Proyek

```text
photo-rename-studio/
├── assets/                          # Aset visual (icon.png, icon.ico)
├── build_scripts/                   # Skrip otomatisasi packaging EXE
│   ├── build_exe.py                 # Runner build PyInstaller lintas platform
│   ├── generate_icons.py            # Generator ikon resolusi tinggi
│   └── photo_rename_studio.spec     # Konfigurasi PyInstaller Windows
├── src/                             # Kode Sumber Utama
│   ├── config.py                    # Konstanta, konfigurasi tema & ekstensi
│   ├── main.py                      # Titik masuk aplikasi (Entry Point)
│   ├── core/                        # Logika Inti & Pemrosesan
│   │   ├── exporter.py              # Engine ekspor salin aman & thread pekerja
│   │   ├── image_loader.py          # Loader thumbnail & EXIF orientation
│   │   ├── importer.py              # Parser impor TXT dan CSV
│   │   └── validator.py             # Validasi nama file aturan Windows
│   ├── ui/                          # Komponen Antarmuka Grafis (PySide6)
│   │   ├── drop_zone.py             # Komponen visual drag-and-drop foto
│   │   ├── main_window.py           # Jendela utama aplikasi & tabel 100 baris
│   │   ├── report_dialog.py         # Modal ringkasan laporan hasil ekspor
│   │   ├── row_widget.py            # Komponen baris individual foto & nama
│   │   └── styles.py                # Lembar gaya global (QSS / Qt Stylesheet)
│   └── utils/                       # Utilitas Pendukung
│       └── file_utils.py            # Utilitas file hash, reserved name & explorer
├── tests/                           # Unit Tests & Automated Test Suites
│   ├── conftest.py                  # Fixtures pytest & mock environment
│   ├── test_export_flow.py          # Pengujian skenario integrasi end-to-end
│   ├── test_exporter.py             # Pengujian unit salin aman & threading
│   ├── test_importer.py             # Pengujian parsing TXT dan CSV
│   ├── test_main_window.py          # Pengujian antarmuka GUI jendela utama
│   ├── test_report_dialog.py        # Pengujian dialog laporan hasil ekspor
│   └── test_validator.py            # Pengujian validasi penamaan Windows
├── IMPLEMENTATION.md                # Spesifikasi implementasi dan checklist modul
├── requirements.txt                 # Dependensi Python runtime
└── README.md                        # Dokumentasi lengkap proyek
```

---

## 🚀 Instalasi & Menjalankan dari Source Code

### Prasyarat
- Python 3.10 atau versi yang lebih baru terpasang di sistem Anda.
- Git (opsional, untuk mengklon repositori).

### Langkah-langkah:

1. **Klon atau Buka Repositori Proyek:**
   ```bash
   git clone https://github.com/username/photo-rename-studio.git
   cd photo-rename-studio
   ```

2. **Buat dan Aktifkan Virtual Environment (Direkomendasikan):**
   - **Di Windows:**
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **Di Linux / macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instal Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Jalankan Aplikasi:**
   ```bash
   python -m src.main
   ```

---

## 🎯 Panduan Penggunaan Langkah-demi-Langkah

### Langkah 1: Siapkan Nama Baru
Anda dapat mengisi nama baru dengan dua cara:
- **Ketik Manual**: Langsung ketikkan nama target pada kolom teks di baris yang bersangkutan.
- **Impor Massal**:
  - Klik tombol **"📄 Impor Nama (.txt/.csv)"** pada toolbar atas.
  - Pilih file `.txt` atau `.csv` yang berisi daftar nama.
  - Jika file CSV memiliki banyak kolom, aplikasi akan menanyakan nomor kolom nama yang ingin digunakan.
  - Baris akan terisi secara otomatis dari atas ke bawah.

### Langkah 2: Pasangkan Foto Sumber
- Tarik (*drag*) file foto dari File Explorer dan lepas (*drop*) ke kotak **"Tarik Foto ke Sini"** pada baris yang sesuai.
- Atau klik kotak tersebut untuk membuka dialog pemilihan file foto manual.
- Thumbnail foto dan nama file asli akan langsung ditampilkan.

### Langkah 3: Pilih Folder Tujuan (Output)
- Pada bagian bawah aplikasi, klik tombol **"📁 Pilih Folder..."**.
- Tentukan direktori tempat salinan foto dengan nama baru akan disimpan.

### Langkah 4: Opsi Tambahan (Opsional)
- **Hapus Baris Kosong**: Klik tombol **"🗑️ Hapus Baris Kosong"** di toolbar untuk membersihkan baris yang tidak digunakan.
- **Tambah Baris**: Klik tombol **"➕ Tambah Baris"** jika membutuhkan slot baris tambahan.
- **Timpa File**: Centang kotak **"Timpa file jika sudah ada"** hanya jika Anda mengizinkan file lama di folder tujuan digantikan oleh salinan baru.

### Langkah 5: Ekspor Foto
- Klik tombol biru besar **"🚀 Mulai Ekspor Foto"**.
- Sistem akan melakukan validasi kilat. Jika ada kesalahan (seperti nama duplikat atau karakter terlarang), sistem akan membatalkan proses dan menunjukkan baris yang perlu diperbaiki.
- Perhatikan indikator progress bar selama penyalinan berlangsung.
- Setelah selesai, dialog **Laporan Hasil Ekspor** akan muncul dengan ringkasan status. Klik tombol **"📂 Buka Folder Output"** untuk langsung meninjau hasilnya di Windows Explorer.

---

## 📦 Panduan Build Windows EXE Portabel

Aplikasi dapat dikompilasi menjadi satu file eksekutabel tunggal portabel (`.exe`) yang berjalan di Windows tanpa perlu menginstal Python di komputer target.

### Cara Cepat (Menggunakan Script Otomatis):
Di komputer Windows dengan environment Python yang aktif:
```powershell
pip install pyinstaller
python build_scripts/build_exe.py
```

### Cara Manual (Menggunakan PyInstaller Spec):
```powershell
pyinstaller build_scripts/photo_rename_studio.spec
```

### Parameter Konfigurasi PyInstaller yang Digunakan:
- `--noconsole` / `--windowed`: Mencegah jendela hitam command prompt (DOS) muncul di belakang aplikasi.
- `--onefile`: Mengemas seluruh komponen ke dalam satu file biner `dist/PhotoRenameStudio.exe`.
- `--icon "assets/icon.ico"`: Menyematkan ikon resmi aplikasi pada file `.exe`.
- `--add-data "assets;assets"`: Memasukkan aset grafis ke dalam *bundle package*.
- **Optimization Excludes**: Mengabaikan pustaka Qt besar yang tidak digunakan (seperti WebEngine, 3D, QML, Multimedia, Test) guna memangkas ukuran biner dan mempercepat waktu pemuatan.

Hasil akhir file biner portabel dapat ditemukan di direktori:
```text
dist/PhotoRenameStudio.exe
```

---

## 🧪 Menjalankan Pengujian Otomatis (Unit Tests)

Proyek ini dilengkapi dengan cakupan pengujian unit komprehensif menggunakan `pytest`.

Jalankan seluruh test suite dengan perintah:
```bash
pytest -v
```

Untuk menjalankan test suite spesifik:
```bash
# Pengujian alur ekspor dan skenario integrasi:
pytest tests/test_export_flow.py -v

# Pengujian validasi penamaan Windows:
pytest tests/test_validator.py -v

# Pengujian mesin penyalinan file aman:
pytest tests/test_exporter.py -v

# Pengujian pengimpor file teks dan CSV:
pytest tests/test_importer.py -v
```

---

## ❓ Troubleshooting & FAQ

#### Q: Mengapa muncul pesan error "Nama sudah digunakan" padahal hurufnya berbeda?
> **Jawab**: Sistem berkas Windows bersifat *case-insensitive* (`Foto_01.jpg` dianggap sama dengan `foto_01.jpg`). Validator aplikasi mencegah benturan nama ini sejak awal untuk melindungi data Anda.

#### Q: Kursor menampilkan lambang dilarang (🚫) saat menarik foto ke baris?
> **Jawab**: Pastikan format foto yang Anda tarik termasuk dalam daftar ekstensi yang didukung (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`, `.gif`). Format selain foto akan ditolak secara otomatis.

#### Q: Apakah foto asli saya aman jika terjadi mati lampu saat ekspor?
> **Jawab**: Sangat aman. Sistem hanya membaca file asli dan menuliskan berkas salinan baru ke folder tujuan. Foto asli tidak pernah dimodifikasi atau dipindahkan.

---

## 📄 Lisensi

Proyek ini dirilis di bawah lisensi [MIT License](LICENSE). Bebas digunakan dan dimodifikasi untuk keperluan pribadi, komersial, maupun edukasi.
