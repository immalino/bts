"""
Photo Rename Studio - Excel Utilities
Fungsi pembantu untuk kalkulasi dimensi sel & merged cell di openpyxl
serta kalkulasi resize proporsional gambar (auto-fit cell).
"""

from pathlib import Path
from typing import List, Tuple, Union
import openpyxl
from openpyxl.utils import coordinate_to_tuple, get_column_letter
from openpyxl.worksheet.worksheet import Worksheet


def get_cell_dimensions(worksheet: Worksheet, cell_coordinate: str) -> Tuple[int, int]:
    """
    Menghitung dimensi lebar dan tinggi sel target dalam satuan piksel.
    Jika sel berada dalam rentang sel gabungan (merged cells), fungsi ini akan
    menjumlahkan seluruh lebar kolom dan tinggi baris dalam rentang tersebut.

    Konversi standar:
    - Lebar kolom (karakter openpyxl) -> piksel: round(lebar_char * 7 + 5)
    - Tinggi baris (points openpyxl) -> piksel: round(tinggi_pt * (96 / 72)) ≈ round(tinggi_pt * 1.333)

    Args:
        worksheet: Objek Worksheet dari openpyxl.
        cell_coordinate: Alamat koordinat sel (contoh: "B5", "C10").

    Returns:
        Tuple[int, int]: (lebar_px, tinggi_px) dalam piksel.
    """
    clean_coord = cell_coordinate.strip().replace("$", "").upper()
    if not clean_coord:
        raise ValueError(f"Koordinat sel tidak boleh kosong: '{cell_coordinate}'")

    # Cari apakah sel berada dalam rentang merged cells
    target_range = None
    for rng in worksheet.merged_cells.ranges:
        if clean_coord in rng:
            target_range = rng
            break

    if target_range is not None:
        min_col, min_row, max_col, max_row = target_range.bounds
    else:
        try:
            row, col = coordinate_to_tuple(clean_coord)
        except Exception as err:
            raise ValueError(f"Format koordinat sel tidak valid '{cell_coordinate}': {err}") from err
        min_col, max_col = col, col
        min_row, max_row = row, row

    # Hitung total lebar kolom dalam piksel
    total_width_px = 0
    for col_idx in range(min_col, max_col + 1):
        col_letter = get_column_letter(col_idx)
        col_dim = worksheet.column_dimensions.get(col_letter)
        if col_dim is not None and col_dim.width is not None:
            char_width = float(col_dim.width)
        elif getattr(worksheet.sheet_format, "defaultColWidth", None) is not None:
            char_width = float(worksheet.sheet_format.defaultColWidth)
        else:
            # Standar default kolom di Excel
            char_width = 8.43

        col_px = max(1, int(round(char_width * 7.0 + 5.0)))
        total_width_px += col_px

    # Hitung total tinggi baris dalam piksel
    total_height_px = 0
    for row_idx in range(min_row, max_row + 1):
        row_dim = worksheet.row_dimensions.get(row_idx)
        if row_dim is not None and row_dim.height is not None:
            pt_height = float(row_dim.height)
        elif getattr(worksheet.sheet_format, "defaultRowHeight", None) is not None:
            pt_height = float(worksheet.sheet_format.defaultRowHeight)
        else:
            # Standar default baris di Excel (15 pt = 20 px)
            pt_height = 15.0

        row_px = max(1, int(round(pt_height * (96.0 / 72.0))))
        total_height_px += row_px

    return (total_width_px, total_height_px)


def calculate_fitted_dimensions(
    img_width: int,
    img_height: int,
    max_width: int,
    max_height: int,
    padding: int = 2,
) -> Tuple[int, int]:
    """
    Menghitung ukuran dimensi gambar (lebar, tinggi) dalam piksel yang pas (fit)
    ke dalam batas kotak sel target dengan tetap mempertahankan rasio aspek asli (aspect ratio)
    serta menyisakan margin/padding di setiap sisinya agar tidak menabrak border sel.

    Args:
        img_width: Lebar asli gambar dalam piksel.
        img_height: Tinggi asli gambar dalam piksel.
        max_width: Lebar kotak sel target dalam piksel.
        max_height: Tinggi kotak sel target dalam piksel.
        padding: Margin internal di setiap sisi dalam piksel (default 2px).

    Returns:
        Tuple[int, int]: (lebar_fit, tinggi_fit) dalam piksel.
    """
    pad = max(0, padding)
    avail_w = max_width - (2 * pad)
    avail_h = max_height - (2 * pad)

    # Pastikan ruang tersedia minimal 1 piksel
    if avail_w <= 0:
        avail_w = max(1, max_width)
    if avail_h <= 0:
        avail_h = max(1, max_height)

    if img_width <= 0 or img_height <= 0:
        return (avail_w, avail_h)

    # Skala proporsional
    scale = min(avail_w / img_width, avail_h / img_height)
    new_w = max(1, int(round(img_width * scale)))
    new_h = max(1, int(round(img_height * scale)))

    return (new_w, new_h)


def is_valid_cell_coordinate(cell_coordinate: str) -> bool:
    """
    Validasi format koordinat sel Excel (misal: 'A1', 'B5', 'AA10').
    Mengembalikan True jika format koordinat valid, False jika tidak.
    """
    if not isinstance(cell_coordinate, str):
        return False
    clean = cell_coordinate.strip().replace("$", "").upper()
    if not clean:
        return False
    import re
    if not re.match(r"^[A-Z]{1,3}[1-9][0-9]{0,6}$", clean):
        return False
    try:
        row, col = coordinate_to_tuple(clean)
        return 1 <= row <= 1048576 and 1 <= col <= 16384
    except Exception:
        return False


def get_sheet_names_from_excel(file_path: Union[str, Path]) -> List[str]:
    """
    Membaca daftar nama sheet dari file workbook Excel (.xlsx, .xlsm, dll) secara cepat.

    Args:
        file_path: Path ke file Excel.

    Returns:
        List[str]: Daftar nama sheet di workbook.

    Raises:
        FileNotFoundError: Jika file tidak ditemukan.
        ValueError: Jika format file bukan Excel atau korup.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File Excel tidak ditemukan: {file_path}")
    if path.suffix.lower() not in (".xlsx", ".xlsm", ".xltx", ".xltm"):
        raise ValueError(f"File bukan format Excel spreadsheet yang didukung (.xlsx): {file_path}")

    try:
        wb = openpyxl.load_workbook(str(path), read_only=True)
        try:
            return list(wb.sheetnames)
        finally:
            wb.close()
    except Exception as err:
        if isinstance(err, (FileNotFoundError, ValueError)):
            raise
        raise ValueError(f"Gagal membaca sheet dari file Excel '{file_path}': {err}") from err

