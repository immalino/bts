"""
Unit tests untuk src/utils/excel_utils.py dan src/core/excel_generator.py (Sesi 9).

Memverifikasi:
1. Kalkulasi dimensi sel tunggal dan merged cell di openpyxl.
2. Kalkulasi proporsional fitted dimensions dengan aspect ratio dan padding.
3. Pembuatan file Excel laporan berbasis template multi-sheet dengan gambar tertanam.
4. Dukungan EXIF orientation transpose pada gambar.
5. Mode ukuran fit_to_cell dan custom sizing.
6. Penanganan error (template hilang, sheet hilang, foto tidak ditemukan/korup).
7. Pembatalan (cancellation) proses pembuatan dokumen.
"""

import os
from pathlib import Path
import openpyxl
from PIL import Image
import pytest

from src.core.excel_generator import ExcelGeneratorThread
from src.core.models import PhotoFieldConfig, ProjectData, TemplateConfig
from src.utils.excel_utils import calculate_fitted_dimensions, get_cell_dimensions


# =====================================================================
# Fixtures
# =====================================================================

@pytest.fixture
def dummy_template_path(tmp_path: Path) -> str:
    """Membuat file template Excel dummy dengan 3 sheet dan sel merged."""
    wb = openpyxl.Workbook()
    # Sheet 1: Antenna
    ws1 = wb.active
    ws1.title = "Antenna"
    ws1["A1"] = "LAPORAN FOTO ANTENA"
    ws1.column_dimensions["B"].width = 20.0
    ws1.column_dimensions["C"].width = 20.0
    ws1.column_dimensions["D"].width = 20.0
    ws1.column_dimensions["E"].width = 20.0
    for r in range(5, 16):
        ws1.row_dimensions[r].height = 25.0
    ws1.merge_cells("B5:E15")

    # Sheet 2: Equipment
    ws2 = wb.create_sheet(title="Equipment")
    ws2["A1"] = "FOTO PERANGKAT DAN RACK"
    ws2.column_dimensions["B"].width = 30.0
    ws2.row_dimensions[4].height = 50.0

    # Sheet 3: Tower
    ws3 = wb.create_sheet(title="Tower")
    ws3["A1"] = "FOTO STRUKTUR TOWER"
    ws3.column_dimensions["C"].width = 25.0
    ws3.row_dimensions[6].height = 40.0

    template_file = str(tmp_path / "dummy_template.xlsx")
    wb.save(template_file)
    return template_file


@pytest.fixture
def sample_photos(tmp_path: Path) -> dict:
    """Membuat beberapa file foto dummy (standar, portrait, EXIF orientation)."""
    photos_dir = tmp_path / "photos"
    photos_dir.mkdir()

    # 1. Foto standar landscape 800x600
    p1 = photos_dir / "antenna_1.jpg"
    img1 = Image.new("RGB", (800, 600), color="blue")
    img1.save(str(p1), format="JPEG")

    # 2. Foto portrait 600x800
    p2 = photos_dir / "equipment_1.jpg"
    img2 = Image.new("RGB", (600, 800), color="green")
    img2.save(str(p2), format="JPEG")

    # 3. Foto dengan tag EXIF orientation (6 = Rotate 90 CW)
    p3 = photos_dir / "tower_1.jpg"
    img3 = Image.new("RGB", (1000, 500), color="red")
    exif = img3.getexif()
    exif[0x0112] = 6
    img3.save(str(p3), format="JPEG", exif=exif)

    return {
        "p1": str(p1),
        "p2": str(p2),
        "p3": str(p3),
    }


# =====================================================================
# Test Excel Utils
# =====================================================================

class TestExcelUtils:
    def test_single_cell_dimensions(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.column_dimensions["B"].width = 20.0
        ws.row_dimensions[5].height = 30.0

        w_px, h_px = get_cell_dimensions(ws, "B5")
        # lebar: 20 * 7 + 5 = 145 px
        # tinggi: round(30 * 96 / 72) = 40 px
        assert w_px == 145
        assert h_px == 40

    def test_merged_cell_dimensions(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        # Merge B5:D6 (3 kolom: B, C, D; 2 baris: 5, 6)
        ws.column_dimensions["B"].width = 10.0  # 10*7+5 = 75 px
        ws.column_dimensions["C"].width = 10.0  # 75 px
        ws.column_dimensions["D"].width = 10.0  # 75 px
        ws.row_dimensions[5].height = 20.0     # round(20 * 4/3) = 27 px
        ws.row_dimensions[6].height = 20.0     # 27 px

        ws.merge_cells("B5:D6")

        # Cek koordinat awal merged cell
        w_px, h_px = get_cell_dimensions(ws, "B5")
        assert w_px == 75 * 3  # 225 px
        assert h_px == 27 * 2  # 54 px

        # Cek sel di dalam rentang merged cell juga menghasilkan dimensi total
        w_inner, h_inner = get_cell_dimensions(ws, "C6")
        assert w_inner == 225
        assert h_inner == 54

    def test_coordinate_normalization_and_invalid(self):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.column_dimensions["A"].width = 15.0
        ws.row_dimensions[1].height = 15.0

        # Case-insensitive dan whitespace
        w1, h1 = get_cell_dimensions(ws, " a1 ")
        w2, h2 = get_cell_dimensions(ws, "$A$1")
        assert w1 == w2
        assert h1 == h2

        # Invalid coordinate
        with pytest.raises(ValueError):
            get_cell_dimensions(ws, "")

        with pytest.raises(ValueError):
            get_cell_dimensions(ws, "INVALID_CELL")

    def test_calculate_fitted_dimensions_landscape(self):
        # Gambar landscape 800x400 (rasio 2:1), sel 200x200, padding 2
        # Ruang tersedia: 200 - 4 = 196
        # Skala: min(196/800, 196/400) = 196/800 = 0.245
        # new_w = 196, new_h = round(400 * 0.245) = 98
        w, h = calculate_fitted_dimensions(800, 400, 200, 200, padding=2)
        assert w == 196
        assert h == 98
        assert w <= 196
        assert h <= 196

    def test_calculate_fitted_dimensions_portrait(self):
        # Gambar portrait 400x800 (rasio 1:2), sel 200x200, padding 0
        w, h = calculate_fitted_dimensions(400, 800, 200, 200, padding=0)
        assert w == 100
        assert h == 200

    def test_calculate_fitted_dimensions_edge_cases(self):
        # Ukuran nol / negatif
        w, h = calculate_fitted_dimensions(0, 0, 100, 100, padding=2)
        assert w == 96
        assert h == 96

        # Padding melebihi ukuran kotak
        w, h = calculate_fitted_dimensions(500, 500, 10, 10, padding=20)
        assert w >= 1
        assert h >= 1


# =====================================================================
# Test ExcelGeneratorThread
# =====================================================================

class TestExcelGeneratorThread:
    def test_generate_multi_sheet_with_merged_cells(
        self, tmp_path: Path, dummy_template_path: str, sample_photos: dict
    ):
        """
        Pengujian pembuatan file Excel dengan 3 sheet dan sel merged.
        Verifikasi gambar terpasang di sheet yang sesuai dan dimensi sel dihormati.
        """
        output_file = str(tmp_path / "output_report.xlsx")

        fields = [
            PhotoFieldConfig(
                field_id="f_antenna",
                label="Foto Antena",
                sheet_name="Antenna",
                cell_anchor="B5",
                sizing_mode="fit_to_cell",
                padding=2,
            ),
            PhotoFieldConfig(
                field_id="f_equip",
                label="Foto Equipment",
                sheet_name="Equipment",
                cell_anchor="B4",
                sizing_mode="fit_to_cell",
                padding=2,
            ),
            PhotoFieldConfig(
                field_id="f_tower",
                label="Foto Tower",
                sheet_name="Tower",
                cell_anchor="C6",
                sizing_mode="fit_to_cell",
                padding=2,
            ),
        ]

        photo_assignments = {
            "f_antenna": sample_photos["p1"],
            "f_equip": sample_photos["p2"],
            "f_tower": sample_photos["p3"],
        }

        template_config = TemplateConfig(
            template_id="tpl_multi",
            name="Template Multi Sheet",
            template_file_path=dummy_template_path,
            fields=fields,
        )

        progress_events = []
        finished_items = []
        completed_events = []

        thread = ExcelGeneratorThread(
            template=template_config,
            output_path=output_file,
            photo_assignments=photo_assignments,
        )
        thread.progress_updated.connect(lambda s, t, m: progress_events.append((s, t, m)))
        thread.item_finished.connect(lambda fid, s, m: finished_items.append((fid, s, m)))
        thread.generation_completed.connect(
            lambda out, sc, fc, errs: completed_events.append((out, sc, fc, errs))
        )

        # Eksekusi thread
        thread.run()

        # 1. Verifikasi completion signal
        assert len(completed_events) == 1
        out_p, success_cnt, fail_cnt, errors = completed_events[0]
        assert out_p == output_file
        assert success_cnt == 3
        assert fail_cnt == 0
        assert errors == []

        # 2. Verifikasi item_finished signals
        assert len(finished_items) == 3
        for fid, success, _ in finished_items:
            assert success is True
            assert fid in photo_assignments

        # 3. Verifikasi progress signals
        assert len(progress_events) >= 4

        # 4. Verifikasi file fisik terbentuk
        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 0

        # 5. Reload workbook dan verifikasi gambar tertanam di tiap sheet
        wb_out = openpyxl.load_workbook(output_file)
        assert "Antenna" in wb_out.sheetnames
        assert "Equipment" in wb_out.sheetnames
        assert "Tower" in wb_out.sheetnames

        ws1 = wb_out["Antenna"]
        assert len(ws1._images) == 1
        img1 = ws1._images[0]
        # B5: col B (index 1), row 5 (index 4)
        assert img1.anchor._from.col == 1
        assert img1.anchor._from.row == 4

        ws2 = wb_out["Equipment"]
        assert len(ws2._images) == 1
        img2 = ws2._images[0]
        # B4: col B (index 1), row 4 (index 3)
        assert img2.anchor._from.col == 1
        assert img2.anchor._from.row == 3

        ws3 = wb_out["Tower"]
        assert len(ws3._images) == 1
        img3 = ws3._images[0]
        # C6: col C (index 2), row 6 (index 5)
        assert img3.anchor._from.col == 2
        assert img3.anchor._from.row == 5

    def test_custom_sizing_mode(
        self, tmp_path: Path, dummy_template_path: str, sample_photos: dict
    ):
        """Verifikasi mode ukuran kustom (custom_width & custom_height)."""
        output_file = str(tmp_path / "output_custom.xlsx")

        field = PhotoFieldConfig(
            field_id="f_custom",
            label="Foto Custom Size",
            sheet_name="Equipment",
            cell_anchor="B2",
            sizing_mode="custom",
            custom_width=150,
            custom_height=120,
        )

        thread = ExcelGeneratorThread(
            template=dummy_template_path,
            output_path=output_file,
            fields=[field],
            photo_assignments={"f_custom": sample_photos["p1"]},
        )
        thread.run()

        wb = openpyxl.load_workbook(output_file)
        ws = wb["Equipment"]
        assert len(ws._images) == 1
        img = ws._images[0]
        # 1 px = 9525 EMUs
        assert round(img.anchor.ext.cx / 9525) == 150
        assert round(img.anchor.ext.cy / 9525) == 120

    def test_with_project_data(
        self, tmp_path: Path, dummy_template_path: str, sample_photos: dict
    ):
        """Verifikasi inisialisasi menggunakan model ProjectData."""
        out_dir = tmp_path / "project_out"
        out_dir.mkdir()

        field = PhotoFieldConfig(
            field_id="sec1",
            label="Sector 1",
            sheet_name="Antenna",
            cell_anchor="B5",
        )
        template_cfg = TemplateConfig(
            template_id="t1",
            name="T1",
            template_file_path=dummy_template_path,
            fields=[field],
        )
        proj = ProjectData(
            project_id="p100",
            site_name="SITE_JKT_01",
            template_id="t1",
            photo_assignments={"sec1": sample_photos["p1"]},
            output_dir=str(out_dir),
        )

        thread = ExcelGeneratorThread(template=template_cfg, project_data=proj)
        assert thread.output_path == str(out_dir / "Laporan_SITE_JKT_01.xlsx")
        thread.run()

        assert os.path.exists(thread.output_path)

    def test_error_missing_template(self, tmp_path: Path):
        """Verifikasi penanganan error jika file template tidak ditemukan."""
        output_file = str(tmp_path / "out.xlsx")
        thread = ExcelGeneratorThread(
            template="/non_existent/template.xlsx",
            output_path=output_file,
            fields=[],
        )
        completed = []
        thread.generation_completed.connect(lambda o, s, f, err: completed.append((o, s, f, err)))
        thread.run()

        assert len(completed) == 1
        _, success, fail, errors = completed[0]
        assert success == 0
        assert len(errors) > 0
        assert "tidak ditemukan" in errors[0]

    def test_error_missing_sheet_and_missing_photo(
        self, tmp_path: Path, dummy_template_path: str
    ):
        """Verifikasi pelaporan kegagalan per field jika sheet atau foto hilang."""
        output_file = str(tmp_path / "out.xlsx")
        fields = [
            PhotoFieldConfig(
                field_id="f_no_sheet",
                label="No Sheet",
                sheet_name="NonExistentSheet",
                cell_anchor="A1",
            ),
            PhotoFieldConfig(
                field_id="f_no_photo",
                label="No Photo",
                sheet_name="Antenna",
                cell_anchor="B5",
            ),
            PhotoFieldConfig(
                field_id="f_invalid_file",
                label="Invalid File",
                sheet_name="Antenna",
                cell_anchor="B5",
            ),
        ]
        photo_assignments = {
            "f_no_sheet": "dummy.jpg",
            # f_no_photo unassigned
            "f_invalid_file": "/path/to/missing_file.jpg",
        }

        finished = []
        completed = []
        thread = ExcelGeneratorThread(
            template=dummy_template_path,
            output_path=output_file,
            fields=fields,
            photo_assignments=photo_assignments,
        )
        thread.item_finished.connect(lambda fid, s, m: finished.append((fid, s, m)))
        thread.generation_completed.connect(lambda o, s, f, err: completed.append((o, s, f, err)))
        thread.run()

        assert len(finished) == 3
        for _, s, _ in finished:
            assert s is False

        _, success, fail, errors = completed[0]
        assert success == 0
        assert fail == 3
        assert len(errors) == 3

    def test_error_corrupt_photo_file(
        self, tmp_path: Path, dummy_template_path: str
    ):
        """Verifikasi penanganan gambar yang korup."""
        output_file = str(tmp_path / "out.xlsx")
        corrupt_img = tmp_path / "corrupt.jpg"
        corrupt_img.write_bytes(b"CORRUPT_NOT_AN_IMAGE_DATA")

        field = PhotoFieldConfig(
            field_id="corrupt_field",
            label="Corrupt Photo",
            sheet_name="Antenna",
            cell_anchor="B5",
        )

        finished = []
        thread = ExcelGeneratorThread(
            template=dummy_template_path,
            output_path=output_file,
            fields=[field],
            photo_assignments={"corrupt_field": str(corrupt_img)},
        )
        thread.item_finished.connect(lambda fid, s, m: finished.append((fid, s, m)))
        thread.run()

        assert len(finished) == 1
        assert finished[0][1] is False
        assert "Gagal memproses" in finished[0][2] or "Format foto tidak valid" in finished[0][2]

    def test_cancellation(
        self, tmp_path: Path, dummy_template_path: str, sample_photos: dict
    ):
        """Verifikasi fitur cancel() membatalkan proses generator."""
        output_file = str(tmp_path / "cancelled.xlsx")
        field = PhotoFieldConfig(
            field_id="f1",
            label="Field 1",
            sheet_name="Antenna",
            cell_anchor="B5",
        )
        thread = ExcelGeneratorThread(
            template=dummy_template_path,
            output_path=output_file,
            fields=[field],
            photo_assignments={"f1": sample_photos["p1"]},
        )
        thread.cancel()
        assert thread.is_cancelled is True

        completed = []
        thread.generation_completed.connect(lambda o, s, f, err: completed.append((o, s, f, err)))
        thread.run()

        assert len(completed) == 1
        _, success, fail, errors = completed[0]
        assert "dibatalkan" in errors[0]
        assert not os.path.exists(output_file)
