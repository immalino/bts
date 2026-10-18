"""
Photo Rename Studio - Core Excel Generator Engine (QThread)
Membaca template Excel, menanamkan foto asli yang telah di-orientasikan EXIF
secara proporsional (auto-fit cell) ke sheet & sel target, dan menyimpan
laporan final di latar belakang.
"""

import os
import tempfile
from typing import Dict, List, Optional, Union

import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image as PILImage, ImageOps
from PySide6.QtCore import QThread, Signal

from src.core.models import PhotoFieldConfig, ProjectData, TemplateConfig
from src.utils.excel_utils import calculate_fitted_dimensions, get_cell_dimensions


class ExcelGeneratorThread(QThread):
    """
    Worker QThread untuk pembuatan dan penanaman foto ke dalam dokumen Excel
    secara asynchronous di latar belakang agar UI tetap lancar dan responsif.

    Signals:
        progress_updated(current_step: int, total_steps: int, message: str)
            Dipancarkan saat tahapan proses diperbarui.
        item_finished(field_id: str, success: bool, message: str)
            Dipancarkan setelah setiap field foto selesai diproses atau gagal.
        generation_completed(output_path: str, success_count: int, fail_count: int, errors: list)
            Dipancarkan setelah seluruh proses pembuatan dokumen selesai atau dibatalkan.
    """

    progress_updated = Signal(int, int, str)
    item_finished = Signal(str, bool, str)
    generation_completed = Signal(str, int, int, list)

    def __init__(
        self,
        template: Optional[Union[TemplateConfig, str]] = None,
        output_path: str = "",
        photo_assignments: Optional[Dict[str, str]] = None,
        fields: Optional[List[PhotoFieldConfig]] = None,
        project_data: Optional[ProjectData] = None,
        parent: Optional[object] = None,
    ) -> None:
        super().__init__(parent)
        self.output_path = output_path
        self.project_data = project_data
        self.photo_assignments = dict(photo_assignments or {})
        self._is_cancelled: bool = False

        # Inisialisasi dari project_data jika ada
        if self.project_data is not None:
            if not self.photo_assignments:
                self.photo_assignments = dict(self.project_data.photo_assignments)
            if not self.output_path and self.project_data.output_dir:
                site_name = self.project_data.site_name.strip() or "BTS_Site"
                self.output_path = os.path.join(
                    self.project_data.output_dir, f"Laporan_{site_name}.xlsx"
                )

        # Inisialisasi template & fields
        if isinstance(template, TemplateConfig):
            self.template_path = template.template_file_path
            self.fields = list(fields if fields is not None else template.fields)
        elif isinstance(template, str):
            self.template_path = template
            self.fields = list(fields or [])
        else:
            self.template_path = ""
            self.fields = list(fields or [])

    def cancel(self) -> None:
        """Meminta pembatalan proses pembuatan dokumen Excel."""
        self._is_cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Memeriksa apakah proses telah dibatalkan."""
        return self._is_cancelled

    def run(self) -> None:
        """
        Alur kerja pembuatan file Excel:
        1. Validasi file template dan tujuan.
        2. Buka workbook template dengan openpyxl.
        3. Iterasi setiap field foto dalam konfigurasi template.
        4. Transpose orientasi EXIF foto via Pillow.
        5. Kalkulasi dimensi sel (termasuk merged cells) dan hitung ukuran proporsional.
        6. Tempel gambar ke sheet & sel target via openpyxl.drawing.image.Image.
        7. Simpan dokumen hasil ke output_path.
        """
        success_count = 0
        fail_count = 0
        errors: List[str] = []
        total_fields = len(self.fields)
        total_steps = total_fields + 2  # step 0: load wb, step 1..N: fields, step N+1: save wb

        # Validasi pembatalan awal
        if self._is_cancelled:
            self.generation_completed.emit(
                self.output_path, 0, 0, ["Proses dibatalkan sebelum dimulai."]
            )
            return

        # Validasi keberadaan file template
        if not self.template_path or not os.path.exists(self.template_path):
            err_msg = f"File template tidak ditemukan: '{self.template_path}'"
            errors.append(err_msg)
            self.generation_completed.emit(self.output_path, 0, total_fields, errors)
            return

        # Validasi output path
        if not self.output_path:
            err_msg = "Path output dokumen Excel belum ditentukan."
            errors.append(err_msg)
            self.generation_completed.emit(self.output_path, 0, total_fields, errors)
            return

        self.progress_updated.emit(0, total_steps, "Membuka workbook template...")

        try:
            wb = openpyxl.load_workbook(self.template_path)
        except Exception as e:
            err_msg = f"Gagal membaca file template Excel: {e}"
            errors.append(err_msg)
            self.generation_completed.emit(self.output_path, 0, total_fields, errors)
            return

        # Gunakan TemporaryDirectory untuk menyimpan file gambar hasil penyesuaian EXIF & resize
        with tempfile.TemporaryDirectory() as temp_dir:
            for idx, field in enumerate(self.fields, start=1):
                if self._is_cancelled:
                    errors.append("Proses dibatalkan oleh pengguna.")
                    break

                field_name = field.label or field.field_id
                self.progress_updated.emit(
                    idx, total_steps, f"Memproses field foto '{field_name}'..."
                )

                # 1. Validasi sheet target pada workbook
                if field.sheet_name not in wb.sheetnames:
                    err_msg = (
                        f"Sheet '{field.sheet_name}' untuk field '{field.field_id}' "
                        f"tidak ditemukan di file template."
                    )
                    errors.append(err_msg)
                    fail_count += 1
                    self.item_finished.emit(field.field_id, False, err_msg)
                    continue

                ws = wb[field.sheet_name]

                # 2. Periksa apakah foto di-assign
                photo_path = self.photo_assignments.get(field.field_id)
                if not photo_path or not str(photo_path).strip():
                    err_msg = f"Tidak ada foto yang di-assign untuk field '{field_name}'"
                    errors.append(err_msg)
                    fail_count += 1
                    self.item_finished.emit(field.field_id, False, err_msg)
                    continue

                if not os.path.isfile(photo_path):
                    err_msg = f"File foto tidak ditemukan: '{photo_path}'"
                    errors.append(err_msg)
                    fail_count += 1
                    self.item_finished.emit(field.field_id, False, err_msg)
                    continue

                # 3. Baca gambar & rotasi EXIF dengan Pillow
                try:
                    with PILImage.open(photo_path) as raw_img:
                        pil_img = ImageOps.exif_transpose(raw_img)
                        # Pastikan format warna didukung
                        if pil_img.mode in ("RGBA", "LA") or (
                            pil_img.mode == "P" and "transparency" in pil_img.info
                        ):
                            pil_img = pil_img.convert("RGBA")
                        else:
                            pil_img = pil_img.convert("RGB")
                        orig_w, orig_h = pil_img.size

                        # 4. Tentukan ukuran target
                        if (
                            field.sizing_mode == "custom"
                            and field.custom_width > 0
                            and field.custom_height > 0
                        ):
                            target_w = field.custom_width
                            target_h = field.custom_height
                        else:
                            # Mode default: fit_to_cell
                            cell_w, cell_h = get_cell_dimensions(ws, field.cell_anchor)
                            target_w, target_h = calculate_fitted_dimensions(
                                img_width=orig_w,
                                img_height=orig_h,
                                max_width=cell_w,
                                max_height=cell_h,
                                padding=field.padding,
                            )

                        # 5. Resize proporsional dengan filter LANCZOS
                        resized_img = pil_img.resize(
                            (target_w, target_h), PILImage.Resampling.LANCZOS
                        )

                        # 6. Simpan gambar sementara ke disk
                        temp_img_path = os.path.join(
                            temp_dir, f"img_{field.field_id}_{idx}.png"
                        )
                        resized_img.save(temp_img_path, format="PNG")

                    # 7. Tambahkan ke worksheet openpyxl
                    openpyxl_img = OpenpyxlImage(temp_img_path)
                    openpyxl_img.width = target_w
                    openpyxl_img.height = target_h
                    ws.add_image(openpyxl_img, field.cell_anchor)

                    success_count += 1
                    self.item_finished.emit(
                        field.field_id, True, f"Foto berhasil disisipkan ke {field.cell_anchor}"
                    )

                except Exception as ex:
                    err_msg = f"Gagal memproses gambar '{photo_path}': {ex}"
                    errors.append(err_msg)
                    fail_count += 1
                    self.item_finished.emit(field.field_id, False, err_msg)
                    continue

            # Jika dibatalkan di tengah proses, jangan simpan dokumen
            if self._is_cancelled:
                self.generation_completed.emit(
                    self.output_path, success_count, fail_count, errors
                )
                return

            # Simpan workbook ke output_path
            self.progress_updated.emit(
                total_steps, total_steps, "Menyimpan dokumen Excel final..."
            )
            try:
                out_dir = os.path.dirname(os.path.abspath(self.output_path))
                if out_dir:
                    os.makedirs(out_dir, exist_ok=True)
                wb.save(self.output_path)
            except Exception as ex:
                err_msg = f"Gagal menyimpan file Excel ke '{self.output_path}': {ex}"
                errors.append(err_msg)
                fail_count += 1

        self.generation_completed.emit(self.output_path, success_count, fail_count, errors)

