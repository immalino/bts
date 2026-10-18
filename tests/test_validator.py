"""
Unit tests untuk validasi nama file dan batch (tests/test_validator.py)
"""

import os
import pytest
from src.utils.file_utils import (
    WINDOWS_ILLEGAL_CHARS,
    is_windows_reserved_name,
    sanitize_filename,
    split_filename_and_ext,
)
from src.core.validator import (
    ValidationResult,
    validate_single_filename,
    validate_batch,
)


class TestFileUtils:
    def test_split_filename_and_ext(self):
        stem, ext = split_filename_and_ext("foto_keluarga.jpg")
        assert stem == "foto_keluarga"
        assert ext == ".jpg"

        stem, ext = split_filename_and_ext("arsip.tar.gz")
        assert stem == "arsip.tar"
        assert ext == ".gz"

        stem, ext = split_filename_and_ext("tanpa_ekstensi")
        assert stem == "tanpa_ekstensi"
        assert ext == ""

    def test_is_windows_reserved_name(self):
        # Reserved names case-insensitive
        assert is_windows_reserved_name("CON") is True
        assert is_windows_reserved_name("con.txt") is True
        assert is_windows_reserved_name("prn.png") is True
        assert is_windows_reserved_name("Aux") is True
        assert is_windows_reserved_name("nul") is True
        assert is_windows_reserved_name("com1.jpg") is True
        assert is_windows_reserved_name("COM9") is True
        assert is_windows_reserved_name("lpt3.pdf") is True
        assert is_windows_reserved_name("LPT8") is True

        # Non-reserved
        assert is_windows_reserved_name("CON_1.jpg") is False
        assert is_windows_reserved_name("contact.txt") is False
        assert is_windows_reserved_name("printer.png") is False
        assert is_windows_reserved_name("normal_file.jpg") is False

    def test_sanitize_filename(self):
        assert sanitize_filename(r'foto\keluarga/liburan:bali*1?2"3<4>5|6') == "foto_keluarga_liburan_bali_1_2_3_4_5_6"
        assert sanitize_filename("  nama_file...  ") == "nama_file"
        assert sanitize_filename("foto.kucing.") == "foto.kucing"


class TestValidateSingleFilename:
    def test_valid_filenames(self):
        valid_samples = [
            "foto_1.jpg",
            "Budi Santoso",
            "01-Siswa-Kelas-XII.png",
            "My Document (Final)",
            "laporan_keuangan_2026.xlsx",
        ]
        for name in valid_samples:
            res = validate_single_filename(name)
            assert res.is_valid is True, f"Harusnya valid: {name}, tapi error: {res.error_message}"
            assert res.error_message == ""

    def test_empty_or_whitespace(self):
        for empty in ["", "   ", "\t", "\n"]:
            res = validate_single_filename(empty)
            assert res.is_valid is False
            assert "kosong" in res.error_message.lower()

    def test_illegal_windows_characters(self):
        for char in WINDOWS_ILLEGAL_CHARS:
            bad_name = f"foto{char}test.jpg"
            res = validate_single_filename(bad_name)
            assert res.is_valid is False
            assert "karakter ilegal" in res.error_message.lower()

    def test_trailing_space_or_dot(self):
        bad_endings = ["foto_liburan ", "foto_keluarga.", "nama ."]
        for name in bad_endings:
            res = validate_single_filename(name)
            assert res.is_valid is False
            assert "berakhiran spasi atau titik" in res.error_message.lower()

    def test_windows_reserved_names(self):
        reserved_samples = ["CON", "con.jpg", "PRN", "aux.png", "NUL", "COM1", "com9.jpeg", "LPT1", "lpt5.png"]
        for name in reserved_samples:
            res = validate_single_filename(name)
            assert res.is_valid is False
            assert "reserved" in res.error_message.lower() or "terlarang" in res.error_message.lower()


class TestValidateBatch:
    def test_output_dir_validation(self, tmp_path):
        # 1. Output dir kosong
        is_valid, errors = validate_batch([], "")
        assert is_valid is False
        assert any("belum ditentukan" in e.lower() for e in errors)

        # 2. Output dir tidak eksis
        non_existent = str(tmp_path / "folder_gaib")
        is_valid, errors = validate_batch([], non_existent)
        assert is_valid is False
        assert any("tidak ditemukan" in e.lower() for e in errors)

        # 3. Output dir berupa file, bukan folder
        dummy_file = tmp_path / "file.txt"
        dummy_file.write_text("halo")
        is_valid, errors = validate_batch([], str(dummy_file))
        assert is_valid is False
        assert any("bukan merupakan direktori" in e.lower() for e in errors)

    def test_empty_batch(self, tmp_path):
        out_dir = str(tmp_path)
        is_valid, errors = validate_batch([], out_dir)
        assert is_valid is False
        assert any("tidak ada data" in e.lower() for e in errors)

    def test_inconsistent_rows(self, tmp_path):
        out_dir = str(tmp_path)
        img_file = tmp_path / "img1.jpg"
        img_file.write_bytes(b"dummy")

        # Foto dipilih tapi target kosong
        batch_1 = [{"source_path": str(img_file), "target_name": ""}]
        is_valid, errors = validate_batch(batch_1, out_dir)
        assert is_valid is False
        assert any("nama target masih kosong" in e.lower() for e in errors)

        # Target diisi tapi foto belum dipilih
        batch_2 = [{"source_path": "", "target_name": "Target1"}]
        is_valid, errors = validate_batch(batch_2, out_dir)
        assert is_valid is False
        assert any("foto belum dipilih" in e.lower() for e in errors)

        # File foto sumber tidak ada di disk
        batch_3 = [{"source_path": str(tmp_path / "missing.jpg"), "target_name": "Target1"}]
        is_valid, errors = validate_batch(batch_3, out_dir)
        assert is_valid is False
        assert any("tidak ditemukan" in e.lower() for e in errors)

    def test_invalid_target_filename_in_batch(self, tmp_path):
        out_dir = str(tmp_path)
        img_file = tmp_path / "img.jpg"
        img_file.write_bytes(b"dummy")

        batch = [{"source_path": str(img_file), "target_name": "CON"}]
        is_valid, errors = validate_batch(batch, out_dir)
        assert is_valid is False
        assert any("terlarang" in e.lower() or "reserved" in e.lower() for e in errors)

    def test_duplicate_target_names(self, tmp_path):
        out_dir = str(tmp_path)
        img1 = tmp_path / "img1.jpg"
        img2 = tmp_path / "img2.jpg"
        img1.write_bytes(b"1")
        img2.write_bytes(b"2")

        # Duplikasi case-insensitive (misal: "Budi.jpg" dan "BUDI.JPG")
        batch = [
            {"row_index": 1, "source_path": str(img1), "target_name": "Budi"},
            {"row_index": 2, "source_path": str(img2), "target_name": "budi"},
        ]
        is_valid, errors = validate_batch(batch, out_dir)
        assert is_valid is False
        assert any("duplikasi" in e.lower() for e in errors)

    def test_collision_with_existing_output_file(self, tmp_path):
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        existing = out_dir / "Siswa_01.jpg"
        existing.write_text("already here")

        src_img = tmp_path / "source.jpg"
        src_img.write_bytes(b"image")

        batch = [
            {"row_index": 1, "source_path": str(src_img), "target_name": "Siswa_01"}
        ]

        # Saat allow_overwrite=False, harus error
        is_valid, errors = validate_batch(batch, str(out_dir), allow_overwrite=False)
        assert is_valid is False
        assert any("sudah ada di direktori output" in e.lower() for e in errors)

        # Saat allow_overwrite=True, harus valid
        is_valid, errors = validate_batch(batch, str(out_dir), allow_overwrite=True)
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_batch_success(self, tmp_path):
        out_dir = str(tmp_path / "out")
        os.makedirs(out_dir)

        img1 = tmp_path / "a.jpg"
        img2 = tmp_path / "b.png"
        img1.write_bytes(b"a")
        img2.write_bytes(b"b")

        batch = [
            {"row_index": 1, "source_path": str(img1), "target_name": "Siswa_01"},
            {"row_index": 2, "source_path": "", "target_name": ""}, # Baris kosong diabaikan
            {"row_index": 3, "source_path": str(img2), "target_name": "Siswa_02.png"},
        ]
        is_valid, errors = validate_batch(batch, out_dir, allow_overwrite=False)
        assert is_valid is True
        assert errors == []
