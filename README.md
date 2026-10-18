# Photo Rename Studio & Document Control BTS 📸📊

> **Aplikasi desktop modern, cepat, dan aman untuk penggantian nama foto massal (Tahap 1) serta Document Control & Generator Laporan Excel Lapangan BTS Telkom (Tahap 2) dengan antarmuka visual interaktif.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52.svg)](https://wiki.qt.io/Qt_for_Python)
[![openpyxl](https://img.shields.io/badge/excel-openpyxl-green.svg)](https://openpyxl.readthedocs.io/)
[![Pillow](https://img.shields.io/badge/image-Pillow-yellow.svg)](https://python-pillow.org/)
[![Tests](https://img.shields.io/badge/tests-pytest%20(100%25%20passed)-brightgreen.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-informational.svg)](LICENSE)

---

## 📌 Daftar Isi
1. [Tentang Aplikasi](#-tentang-aplikasi)
2. [Fitur Utama](#-fitur-utama)
   - [Mode Tahap 1: Batch Renaming Cepat](#mode-tahap-1-batch-renaming-cepat)
   - [Mode Tahap 2: Document Control BTS Telkom](#mode-tahap-2-document-control-bts-telkom)
3. [Jaminan Keamanan File (Zero Data Loss)](#-jaminan-keamanan-file-zero-data-loss)
4. [Dukungan Format File Foto](#-dukungan-format-file-foto)
5. [Struktur Proyek](#-struktur-proyek)
6. [Instalasi & Menjalankan dari Source Code](#-instalasi--menjalankan-dari-source-code)
7. [Panduan Penggunaan Alur Document Control BTS (Tahap 2)](#-panduan-penggunaan-alur-document-control-bts-tahap-2)
8. [Panduan Penggunaan Alur Batch Renaming (Tahap 1)](#-panduan-penggunaan-alur-batch-renaming-tahap-1)
9. [Panduan Build Windows EXE Portabel](#-panduan-build-windows-exe-portabel)
10. [Menjalankan Pengujian Otomatis (Unit Tests)](#-menjalankan-pengujian-otomatis-unit-tests)
11. [Troubleshooting & FAQ](#-troubleshooting--faq)

---

## 📖 Tentang Aplikasi

**Photo Rename Studio** berevolusi dari sekadar alat penggantian nama foto massal menjadi sistem **Document Control Lapangan BTS** terintegrasi. 

Aplikasi ini mengatasi tantangan utama tim lapangan telekomunikasi dan Document Control (DC):
- Menyusun ratusan foto dokumentasi site (antena sektoral, perangkat microwave, rectifier, tower) ke dalam template laporan resmi Microsoft Excel (`.xlsx`).
- Menata ukuran gambar secara proporsional sesuai dimensi sel target Excel (*Auto-Fit Cell & Merged Cells*).
- Menghilangkan proses manual *insert picture* satu per satu di Microsoft Excel yang memakan waktu berjam-jam.

---

## ✨ Fitur Utama

### Mode Tahap 1: Batch Renaming Cepat
- 🎨 **Antarmuka Bersih & Modern**: Dibangun menggunakan PySide6 (Qt6) tanpa emoji murahan, menggunakan icon sistem native Qt yang tajam.
- 🖱️ **Drag-and-Drop Intuitif**: Tarik dan lepas file foto langsung dari File Explorer Windows ke baris yang diinginkan.
- 🖼️ **Thumbnail Preview Otomatis**: Pratinjau instan foto thumbnail dengan koreksi rotasi EXIF otomatis (foto potret/lanskap tegak sempurna).
- 📋 **Impor Nama Massal (TXT & CSV)**: Dukungan file `.txt` dan `.csv` dengan berbagai delimiter dan auto-expand baris.
- 🛡️ **Validasi Penamaan Windows Real-Time**: Deteksi karakter ilegal (`\ / : * ? " < > |`), reserved names (`CON`, `PRN`), dan duplikasi nama *case-insensitive*.

### Mode Tahap 2: Document Control BTS Telkom
- 📁 **Manajemen Proyek Site (Site Manager)**:
  - Membuat dan beralih antar proyek site (contoh: `JKT-042 Pasar Minggu`) dengan riwayat status tersimpan otomatis.
  - State Auto-Persistence: Setiap foto yang di-drop langsung tercatat ke database lokal JSON tanpa risiko kehilangan progres kerja.
- 📊 **Visual Template Manager & Inspector**:
  - Konfigurasi template laporan `.xlsx` tanpa menyentuh kode.
  - **Auto-Load Sheet Inspector**: Membaca otomatis seluruh sheet di workbook Excel template.
  - Visual Field Table: Menentukan label foto, sheet tujuan, sel anchor (misal `B5`), dan mode ukuran gambar.
- 📐 **Auto-Fit Cell Engine & Merged Cells Support**:
  - Menghitung lebar dan tinggi sel Excel tunggal maupun *merged cells* dalam satuan piksel.
  - Resize proporsional dengan filter lanczos dan margin/padding otomatis agar tidak menabrak border sel.
  - Mode custom size (lebar $\times$ tinggi kustom) untuk kebutuhan khusus.
- ⚡ **Background Generation & 1-Klik Handover**:
  - Pembuatan dokumen Excel berjalan non-blocking di background thread (`ExcelGeneratorThread`) dengan progress bar real-time.
  - Tombol pintasan **"Buka Dokumen Excel"** dan **"Buka Folder Output"** langsung setelah proses selesai.

---

## 🔒 Jaminan Keamanan File (Zero Data Loss)

1. **Non-Destructive Copying**:
   - Sistem **TIDAK PERNAH** memindahkan atau mengubah file foto sumber asli.
   - Foto sumber selalu dibaca secara *read-only*.
2. **Perlindungan Overwrite**:
   - Mencegah penimpaan file yang tidak disengaja.
3. **Penyalinan Atomik**:
   - Data state JSON disimpan secara atomik (`.tmp` $\rightarrow$ swap) untuk mencegah kerusakan berkas jika listrik mati mendadak.

---

## 📁 Dukungan Format File Foto

| Format | Ekstensi yang Didukung | Keterangan |
| :--- | :--- | :--- |
| **JPEG** | `.jpg`, `.jpeg` | Mendukung EXIF Auto-Orientation |
| **PNG** | `.png` | Mendukung transparansi RGBA |
| **WebP** | `.webp` | Format web modern kompresi tinggi |
| **BMP** | `.bmp` | Windows Bitmap format standar |
| **TIFF** | `.tiff`, `.tif` | Format master fotografi resolusi tinggi |
| **GIF** | `.gif` | Format citra frame pertama |

---

## 🏗️ Struktur Proyek

```text
my-bts/
├── assets/                          # Aset visual (icon.png, icon.ico)
├── build_scripts/                   # Skrip otomatisasi packaging EXE
│   ├── build_exe.py                 # Runner build PyInstaller
│   ├── generate_icons.py            # Generator ikon resolusi tinggi
│   └── photo_rename_studio.spec     # Konfigurasi PyInstaller Windows
├── src/                             # Kode Sumber Utama
│   ├── config.py                    # Konstanta, tema warna & ekstensi
│   ├── main.py                      # Titik masuk aplikasi (Entry Point)
│   ├── core/                        # Engine Pemrosesan & Data Models
│   │   ├── excel_generator.py       # Engine generator Excel & background worker
│   │   ├── exporter.py              # Engine ekspor salin aman file foto (Tahap 1)
│   │   ├── image_loader.py          # Loader thumbnail & koreksi EXIF
│   │   ├── importer.py              # Parser impor TXT dan CSV
│   │   ├── models.py                # Model PhotoFieldConfig, TemplateConfig, ProjectData
│   │   ├── storage.py               # Manajer persistensi data JSON lokal
│   │   └── validator.py             # Validasi penamaan aturan Windows
│   ├── ui/                          # Antarmuka Pengguna Grafis (PySide6)
│   │   ├── drop_zone.py             # Drop zone interaktif drag-and-drop
│   │   ├── dynamic_row.py           # Komponen baris foto dinamis berbasis template
│   │   ├── main_window.py           # Jendela utama aplikasi & routing workspace
│   │   ├── project_dialog.py        # Dialog manajemen proyek site
│   │   ├── report_dialog.py         # Modal ringkasan laporan hasil & shortcut open Excel
│   │   ├── row_widget.py            # Baris foto individual 100 baris (Tahap 1)
│   │   ├── styles.py                # Tema modern QSS / stylesheet
│   │   └── template_dialog.py       # Dialog visual template manager & editor field
│   └── utils/                       # Utilitas Pendukung
│       ├── excel_utils.py           # Kalkulator dimensi sel, auto-fit, & sheet reader
│       └── file_utils.py            # Utilitas file hash & explorer
├── tests/                           # Unit Tests & Automated Test Suites
│   ├── test_dynamic_workspace.py    # Pengujian integrasi workspace dinamis & auto-save
│   ├── test_e2e_excel_flow.py       # Pengujian end-to-end pembuatan dokumen Excel
│   ├── test_excel_generator.py      # Pengujian unit engine Excel generator
│   ├── test_export_flow.py          # Pengujian integrasi ekspor foto Tahap 1
│   ├── test_exporter.py             # Pengujian unit penyalinan file foto
│   ├── test_importer.py             # Pengujian parsing TXT dan CSV
│   ├── test_main_window.py          # Pengujian antarmuka GUI MainWindow
│   ├── test_report_dialog.py        # Pengujian dialog laporan hasil
│   ├── test_storage.py              # Pengujian persistensi storage template & project
│   ├── test_template_dialog.py      # Pengujian dialog template & editor field
│   └── test_validator.py            # Pengujian validasi penamaan Windows
├── IMPLEMENTATION.md                # Spesifikasi implementasi dan checklist modul
├── requirements.txt                 # Dependensi Python runtime
└── README.md                        # Dokumentasi lengkap proyek
```

---

## 🚀 Instalasi & Menjalankan dari Source Code

### Prasyarat
- Python 3.10 atau versi yang lebih baru terpasang di sistem.
- Pip package manager.

### Langkah-langkah:

1. **Buka Repositori Proyek:**
   ```bash
   cd my-bts
   ```

2. **Buat dan Aktifkan Virtual Environment:**
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

## 🎯 Panduan Penggunaan Alur Document Control BTS (Tahap 2)

### 1. Kelola Template Excel
- Klik tombol **"Kelola Template"** pada toolbar atas.
- Klik **"Buat Template Baru"**.
- Beri nama template (contoh: `Template Telkomsel BTS 4G/5G`).
- Pilih file template master `.xlsx` Anda. Nama-nama sheet di dalam file akan terbaca secara otomatis.
- Klik **"Tambah Field"** untuk menambahkan posisi foto:
  - Beri nama label field (contoh: `Foto Antenna Sector 1`).
  - Pilih sheet target (contoh: `Antenna`).
  - Masukkan sel anchor (contoh: `B5`).
  - Pilih mode ukuran (Auto-Fit Cell direkomendasikan).
- Klik **"Simpan Template"**.

### 2. Buat atau Pilih Proyek Site
- Klik tombol **"Ganti / Pilih Site"** pada toolbar atas.
- Klik **"Proyek Site Baru"**.
- Masukkan Nama/ID Site (contoh: `JKT-042 Pasar Minggu`) dan pilih template yang telah dibuat.
- Klik **"Buat Proyek"**.
- Workspace akan langsung menampilkan baris-baris foto dinamis sesuai urutan field template Anda!

### 3. Masukkan Foto Dokumentasi Lapangan
- Tarik (*drag-and-drop*) file foto dari File Explorer ke kotak dropzone baris yang sesuai, atau klik tombol **"Pilih"**.
- Thumbnail foto akan langsung tampil tegak sesuai rotasi EXIF kamera.
- Status baris akan berubah menjadi badge hijau **"Terisi"**.
- Setiap foto yang dimasukkan **otomatis tersimpan** ke file project lokal (aman jika aplikasi tertutup).

### 4. Generate Dokumen Excel Laporan
- Klik tombol biru **"Generate Dokumen Excel"** di bagian bawah.
- Tentukan nama dan lokasi file hasil laporan (contoh: `Laporan_JKT_042_20261018.xlsx`).
- Generator akan memproses foto di background: membaca dimensi sel target, meresize foto secara proporsional, dan menanamkannya ke sheet Excel yang tepat.
- Setelah selesai, dialog laporan akan muncul:
  - Klik **"Buka Dokumen Excel"** untuk langsung membuka Microsoft Excel / LibreOffice dan meninjau hasil dokumen.
  - Klik **"Buka Folder Output"** untuk melihat berkas di file manager.

---

## 📸 Panduan Penggunaan Alur Batch Renaming (Tahap 1)

1. Buka aplikasi tanpa memilih proyek site (tampilan default 100 baris).
2. Isi nama baru manual atau klik **"Impor Nama (TXT/CSV)"**.
3. Tarik dan lepas foto ke baris yang bersangkutan.
4. Tentukan folder output dengan mengklik **"Pilih Folder"**.
5. Klik **"Generate Dokumen Excel" / "Proses Ekspor"** untuk mengekspor foto salinan berurutan.

---

## 📦 Panduan Build Windows EXE Portabel

Aplikasi dapat dikompilasi menjadi satu file eksekutabel tunggal portabel (`.exe`) yang berjalan di Windows tanpa perlu menginstal Python di komputer target:

```powershell
pip install pyinstaller
python build_scripts/build_exe.py
```

### Parameter Konfigurasi PyInstaller yang Digunakan:
- `--noconsole` / `--windowed`: Mencegah jendela console DOS muncul di belakang aplikasi.
- `--onefile`: Mengemas seluruh komponen ke dalam satu file biner tunggal portabel.
- `--icon "assets/icon.ico"`: Menyematkan ikon resmi aplikasi pada file `.exe`.
- `--add-data "assets;assets"`: Memasukkan bundel aset ikon ke dalam aplikasi.

File portabel siap digunakan berada di:
```text
dist/PhotoRenameStudio.exe
```

---

## 🧪 Menjalankan Pengujian Otomatis (Unit Tests)

Proyek ini dilengkapi dengan 105 pengujian otomatis menggunakan `pytest` dengan cakupan 100% lulus.

Jalankan seluruh test suite:
```bash
./venv/bin/pytest -v
```

Jalankan test suite modul spesifik:
```bash
# Pengujian alur end-to-end generator Excel (Tahap 2):
pytest tests/test_e2e_excel_flow.py -v

# Pengujian dynamic workspace & auto-persistence:
pytest tests/test_dynamic_workspace.py -v

# Pengujian template visual dialog:
pytest tests/test_template_dialog.py -v

# Pengujian core excel generator & auto-fit:
pytest tests/test_excel_generator.py -v

# Pengujian storage manager JSON:
pytest tests/test_storage.py -v

# Pengujian alur ekspor Tahap 1:
pytest tests/test_export_flow.py -v
```

---

## ❓ Troubleshooting & FAQ

#### Q: Mengapa gambar di Excel pas dengan ukuran kotak sel tanpa merusak rasio foto?
> **Jawab**: Engine generator menghitung dimensi piksel sel target (termasuk *merged cells*), lalu menerapkan algoritma aspect-ratio fitting dengan filter Lanczos resolusi tinggi dan margin internal 2px.

#### Q: Apakah file template master `.xlsx` asli saya akan tertimpa saat generate?
> **Jawab**: Tidak pernah. Template master hanya dibaca, dan salinan baru dokumen laporan disimpan ke path output yang Anda tentukan.

#### Q: Bagaimana jika saya tidak sengaja menutup aplikasi saat sedang mengisi foto?
> **Jawab**: Setiap perubahan foto langsung dicatat (*auto-save*) ke dalam berkas JSON proyek Anda. Saat Anda membuka site tersebut kembali melalui "Ganti / Pilih Site", seluruh foto akan kembali terpasang seperti semula.

---

## 📄 Lisensi

Proyek ini dirilis di bawah lisensi [MIT License](LICENSE).
