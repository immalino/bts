"""
Unit tests untuk modul importer (tests/test_importer.py)
"""

import pytest
from src.core.importer import import_names_from_txt, import_names_from_csv


class TestImportFromTxt:
    def test_import_valid_txt(self, tmp_path):
        txt_file = tmp_path / "names.txt"
        txt_file.write_text(
            "Andi Pratama\n"
            "  Budi Santoso  \n"
            "\n"
            "Citra Dewi\n"
            "   \n"
            "Deni Kurniawan\n",
            encoding="utf-8",
        )

        names = import_names_from_txt(str(txt_file))
        assert names == [
            "Andi Pratama",
            "Budi Santoso",
            "Citra Dewi",
            "Deni Kurniawan",
        ]

    def test_import_empty_txt(self, tmp_path):
        txt_file = tmp_path / "empty.txt"
        txt_file.write_text("\n   \n\t\n", encoding="utf-8")

        names = import_names_from_txt(str(txt_file))
        assert names == []

    def test_import_non_existent_txt(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            import_names_from_txt(str(tmp_path / "non_existent.txt"))


class TestImportFromCsv:
    def test_import_csv_comma_delimiter(self, tmp_path):
        csv_file = tmp_path / "data_comma.csv"
        csv_file.write_text(
            "Nama,Kelas,NIS\n"
            "Ahmad Fauzi,XII-IPA-1,1001\n"
            "Bella Safira,XII-IPA-1,1002\n"
            "  ,XII-IPA-1,1003\n"
            "Chandra Wijaya,XII-IPA-1,1004\n",
            encoding="utf-8",
        )

        # Import kolom 0 (Nama)
        names = import_names_from_csv(str(csv_file), column_index=0)
        assert names == ["Nama", "Ahmad Fauzi", "Bella Safira", "Chandra Wijaya"]

        # Import kolom 2 (NIS)
        nis = import_names_from_csv(str(csv_file), column_index=2)
        assert nis == ["NIS", "1001", "1002", "1003", "1004"]

    def test_import_csv_semicolon_delimiter(self, tmp_path):
        csv_file = tmp_path / "data_semicolon.csv"
        csv_file.write_text(
            "Nama Siswa;Jurusan;Nilai\n"
            "Doni Pratama;TKJ;90\n"
            "Eka Saputri;RPL;95\n"
            "Fahri Hamzah;MM;88\n",
            encoding="utf-8",
        )

        names = import_names_from_csv(str(csv_file), column_index=0)
        assert names == ["Nama Siswa", "Doni Pratama", "Eka Saputri", "Fahri Hamzah"]

    def test_import_csv_tab_delimiter(self, tmp_path):
        csv_file = tmp_path / "data_tab.tsv"
        csv_file.write_text(
            "ID\tNama Lengkap\n"
            "1\tGita Gutawa\n"
            "2\tHendra Setiawan\n",
            encoding="utf-8",
        )

        names = import_names_from_csv(str(csv_file), column_index=1)
        assert names == ["Nama Lengkap", "Gita Gutawa", "Hendra Setiawan"]

    def test_import_csv_out_of_bounds_column(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("Siswa1,A\nSiswa2,B\n", encoding="utf-8")

        names = import_names_from_csv(str(csv_file), column_index=5)
        assert names == []

    def test_import_non_existent_csv(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            import_names_from_csv(str(tmp_path / "missing.csv"))
