"""
Photo Rename Studio - Modul Pengimpor Daftar Nama (TXT & CSV)
"""

import csv
import os
from typing import List


def import_names_from_txt(file_path: str, encoding: str = "utf-8") -> List[str]:
    """
    Mengimpor daftar nama dari file teks (.txt).
    - Membaca baris demi baris.
    - Mengabaikan baris kosong.
    - Menghapus whitespace di awal dan akhir setiap baris.
    - Mendukung fallback encoding utf-8-sig / latin1 jika terjadi UnicodeDecodeError.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File TXT tidak ditemukan: '{file_path}'")

    encodings_to_try = [encoding, "utf-8-sig", "latin1"]
    lines = None

    for enc in encodings_to_try:
        try:
            with open(file_path, "r", encoding=enc) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue

    if lines is None:
        raise ValueError(f"Gagal membaca file '{file_path}' dengan encoding yang didukung.")

    names = []
    for line in lines:
        cleaned = line.strip()
        if cleaned:
            names.append(cleaned)

    return names


def _detect_delimiter(sample_text: str) -> str:
    """
    Mendeteksi pemisah delimiter (koma, titik koma, tab) menggunakan csv.Sniffer
    dengan fallback berbasis hitungan frekuensi karakter.
    """
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=";,\t")
        return dialect.delimiter
    except Exception:
        # Fallback hitung frekuensi pemisah umum
        counts = {
            ",": sample_text.count(","),
            ";": sample_text.count(";"),
            "\t": sample_text.count("\t"),
        }
        best_delimiter = max(counts, key=counts.get)
        return best_delimiter if counts[best_delimiter] > 0 else ","


def import_names_from_csv(
    file_path: str,
    column_index: int = 0,
    encoding: str = "utf-8",
) -> List[str]:
    """
    Mengimpor daftar nama dari file CSV (.csv).
    - Mendukung auto-detect delimiter: koma (,), titik koma (;), atau tab (\\t).
    - Mengambil nilai dari kolom `column_index` (default 0 / kolom pertama).
    - Mengabaikan baris kosong atau sel yang kosong.
    - Menghapus whitespace di awal dan akhir string.
    - Mendukung fallback encoding (utf-8, utf-8-sig, latin1).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File CSV tidak ditemukan: '{file_path}'")

    encodings_to_try = [encoding, "utf-8-sig", "latin1"]
    content = None

    for enc in encodings_to_try:
        try:
            with open(file_path, "r", encoding=enc, newline="") as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        raise ValueError(f"Gagal membaca file '{file_path}' dengan encoding yang didukung.")

    # Deteksi delimiter dari cuplikan teks
    sample = content[:4096]
    delimiter = _detect_delimiter(sample)

    names: List[str] = []
    reader = csv.reader(content.splitlines(), delimiter=delimiter)

    for row in reader:
        if not row:
            continue
        if len(row) > column_index:
            val = row[column_index].strip()
            if val:
                names.append(val)

    return names
