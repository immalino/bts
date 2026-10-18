"""
Photo Rename Studio - Modul Validasi Nama File dan Batch
"""

import os
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

from src.utils.file_utils import (
    WINDOWS_ILLEGAL_CHARS,
    is_windows_reserved_name,
    split_filename_and_ext,
)


@dataclass
class ValidationResult:
    """Hasil validasi nama file tunggal."""
    is_valid: bool
    error_message: str = ""


def validate_single_filename(name: str) -> ValidationResult:
    """
    Validasi sebuah nama file sesuai aturan Windows secara ketat:
    - Tidak boleh kosong atau hanya whitespace.
    - Tidak boleh mengandung karakter ilegal Windows: \\ / : * ? " < > |
    - Tidak boleh berakhiran spasi atau titik.
    - Tidak boleh diawali spasi (direkomendasikan untuk Windows file sanity).
    - Tidak boleh menggunakan reserved names Windows (CON, PRN, AUX, NUL, COM1-9, LPT1-9).
    """
    if not name or not name.strip():
        return ValidationResult(is_valid=False, error_message="Nama file tidak boleh kosong.")

    # Cek karakter ilegal Windows
    illegal_found = [c for c in name if c in WINDOWS_ILLEGAL_CHARS]
    if illegal_found:
        unique_illegal = "".join(sorted(set(illegal_found)))
        return ValidationResult(
            is_valid=False,
            error_message=f"Mengandung karakter ilegal Windows: {unique_illegal}",
        )

    # Cek trailing dot atau trailing space
    if name.endswith(" ") or name.endswith("."):
        return ValidationResult(
            is_valid=False,
            error_message="Nama file tidak boleh berakhiran spasi atau titik.",
        )

    # Cek reserved names Windows
    if is_windows_reserved_name(name):
        stem, _ = split_filename_and_ext(name)
        return ValidationResult(
            is_valid=False,
            error_message=f"'{stem}' adalah nama terlarang sistem Windows (Reserved Device Name).",
        )

    return ValidationResult(is_valid=True, error_message="")


def validate_batch(
    row_items: List[Dict[str, Any]],
    output_dir: str,
    allow_overwrite: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validasi keseluruhan batch data baris sebelum proses ekspor:
    1. Output directory harus ada, berupa direktori, dan dapat ditulis (writable).
    2. Konsistensi baris:
       - Jika foto sumber dipilih, target name harus diisi dan valid.
       - Jika target name diisi, foto sumber harus dipilih dan file fisik sumber harus ada.
    3. Duplikasi nama target antar baris (case-insensitive sesuai filesystem Windows).
    4. Tabrakan nama file yang sudah ada di output_dir (jika allow_overwrite=False).

    Format item dalam row_items:
      dict dengan key:
        - "source_path": str (path file foto asli, bisa kosong jika belum dipilih)
        - "target_name": str (nama file baru yang diinginkan, bisa dengan atau tanpa ekstensi)
        - "row_index": Optional[int] (nomor baris untuk pelaporan error)

    Mengembalikan tuple (is_valid, list_of_errors).
    """
    errors: List[str] = []

    # 1. Cek output directory
    if not output_dir or not str(output_dir).strip():
        errors.append("Direktori output belum ditentukan.")
        return False, errors

    if not os.path.exists(output_dir):
        errors.append(f"Direktori output tidak ditemukan: '{output_dir}'.")
        return False, errors

    if not os.path.isdir(output_dir):
        errors.append(f"Path output bukan merupakan direktori: '{output_dir}'.")
        return False, errors

    if not os.access(output_dir, os.W_OK):
        errors.append(f"Direktori output tidak dapat ditulis (permission denied): '{output_dir}'.")
        return False, errors

    seen_target_names: Dict[str, int] = {}
    valid_active_rows = 0

    for idx, item in enumerate(row_items):
        row_num = item.get("row_index", idx + 1)
        source_path = str(item.get("source_path") or "").strip()
        target_name = str(item.get("target_name") or "").strip()

        # Baris kosong total (tidak ada foto & tidak ada target) dilewati
        if not source_path and not target_name:
            continue

        # Cek jika foto dipilih tapi target kosong
        if source_path and not target_name:
            errors.append(f"Baris {row_num}: Foto dipilih tetapi nama target masih kosong.")
            continue

        # Cek jika target diisi tapi foto belum dipilih
        if target_name and not source_path:
            errors.append(f"Baris {row_num}: Nama target diisi tetapi foto belum dipilih.")
            continue

        # Keduanya terisi, validasi keberadaan file sumber
        if not os.path.exists(source_path):
            errors.append(f"Baris {row_num}: File foto sumber tidak ditemukan di '{source_path}'.")
            continue

        # Validasi nama target secara individu
        single_res = validate_single_filename(target_name)
        if not single_res.is_valid:
            errors.append(f"Baris {row_num}: Nama target tidak valid ({single_res.error_message}).")
            continue

        # Menentukan nama file akhir (memastikan ekstensi dari file sumber jika target_name belum punya ekstensi)
        _, src_ext = split_filename_and_ext(source_path)
        tgt_stem, tgt_ext = split_filename_and_ext(target_name)
        final_ext = tgt_ext if tgt_ext else src_ext
        final_filename = f"{tgt_stem}{final_ext}"

        # Cek duplikasi antar baris (case-insensitive untuk Windows)
        normalized_name = final_filename.upper()
        if normalized_name in seen_target_names:
            first_row = seen_target_names[normalized_name]
            errors.append(
                f"Baris {row_num}: Duplikasi nama target '{final_filename}' dengan Baris {first_row}."
            )
        else:
            seen_target_names[normalized_name] = row_num

        # Cek collision dengan file yang sudah ada di output directory
        if not allow_overwrite:
            destination_path = os.path.join(output_dir, final_filename)
            if os.path.exists(destination_path):
                errors.append(
                    f"Baris {row_num}: File '{final_filename}' sudah ada di direktori output "
                    "(opsi overwrite nonaktif)."
                )

        valid_active_rows += 1

    if valid_active_rows == 0 and not errors:
        errors.append("Tidak ada data baris yang siap diproses.")

    return len(errors) == 0, errors
