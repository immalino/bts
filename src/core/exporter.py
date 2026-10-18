"""
Photo Rename Studio - Background Worker Ekspor Foto (QThread)
"""

from dataclasses import dataclass
from typing import List, Optional
import os
import shutil

from PySide6.QtCore import QThread, Signal


@dataclass
class ExportTask:
    """
    Data model untuk item tugas ekspor foto.
    
    Attributes:
        source_path: Path absolut atau relatif ke file foto asli.
        target_filename: Nama file tujuan (lengkap dengan ekstensi).
        row_index: Indeks baris di UI untuk pelaporan status kembali ke baris terkait.
    """
    source_path: str
    target_filename: str
    row_index: int


class ExporterThread(QThread):
    """
    Worker thread untuk mengeksekusi penyalinan foto di latar belakang
    agar UI tetap responsif.
    
    Signals:
        progress_updated(current_index: int, total: int, current_filename: str)
            Dipancarkan saat mulai memproses setiap item.
        item_finished(row_index: int, success: bool, message: str)
            Dipancarkan setelah setiap item selesai diproses (sukses, gagal, atau dilewati).
        export_completed(success_count: int, fail_count: int, skipped_count: int, errors: list)
            Dipancarkan setelah seluruh antrean selesai atau dibatalkan.
    """
    progress_updated = Signal(int, int, str)
    item_finished = Signal(int, bool, str)
    export_completed = Signal(int, int, int, list)

    def __init__(
        self,
        tasks: List[ExportTask],
        output_directory: str,
        allow_overwrite: bool = False,
        parent: Optional[object] = None,
    ) -> None:
        super().__init__(parent)
        self.tasks = tasks
        self.output_directory = output_directory
        self.allow_overwrite = allow_overwrite
        self._is_cancelled: bool = False

    def cancel(self) -> None:
        """Meminta pembatalan proses ekspor."""
        self._is_cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Memeriksa apakah proses ekspor telah dibatalkan."""
        return self._is_cancelled

    def run(self) -> None:
        """
        Mengeksekusi penyalinan file foto satu per satu.
        Menggunakan shutil.copy2 untuk menjaga keutuhan file asli dan metadatanya (Zero Data Loss).
        """
        success_count = 0
        fail_count = 0
        skipped_count = 0
        errors: List[dict] = []

        total_tasks = len(self.tasks)

        # Pastikan output directory ada
        try:
            os.makedirs(self.output_directory, exist_ok=True)
        except Exception as e:
            err_msg = f"Gagal membuat folder tujuan: {str(e)}"
            for task in self.tasks:
                errors.append({
                    "row_index": task.row_index,
                    "source_path": task.source_path,
                    "target_filename": task.target_filename,
                    "error": err_msg,
                })
                self.item_finished.emit(task.row_index, False, err_msg)
            self.export_completed.emit(0, total_tasks, 0, errors)
            return

        for idx, task in enumerate(self.tasks, start=1):
            if self._is_cancelled:
                # Proses dibatalkan di tengah jalan
                cancel_msg = "Proses dibatalkan oleh pengguna."
                errors.append({
                    "row_index": task.row_index,
                    "source_path": task.source_path,
                    "target_filename": task.target_filename,
                    "error": cancel_msg,
                })
                self.item_finished.emit(task.row_index, False, cancel_msg)
                skipped_count += 1
                continue

            self.progress_updated.emit(idx, total_tasks, task.target_filename)

            # Periksa keberadaan file sumber
            if not os.path.isfile(task.source_path):
                fail_count += 1
                err_msg = f"File sumber tidak ditemukan: {task.source_path}"
                errors.append({
                    "row_index": task.row_index,
                    "source_path": task.source_path,
                    "target_filename": task.target_filename,
                    "error": err_msg,
                })
                self.item_finished.emit(task.row_index, False, err_msg)
                continue

            dest_path = os.path.join(self.output_directory, task.target_filename)

            # Periksa jika file tujuan sudah ada
            if os.path.exists(dest_path):
                if not self.allow_overwrite:
                    skipped_count += 1
                    err_msg = f"File sudah ada di folder tujuan (overwrite dinonaktifkan): {task.target_filename}"
                    errors.append({
                        "row_index": task.row_index,
                        "source_path": task.source_path,
                        "target_filename": task.target_filename,
                        "error": err_msg,
                    })
                    self.item_finished.emit(task.row_index, False, err_msg)
                    continue

            # Eksekusi penyalinan file dengan shutil.copy2 (Non-destructive / Zero Data Loss)
            try:
                shutil.copy2(task.source_path, dest_path)
                success_count += 1
                self.item_finished.emit(task.row_index, True, "Berhasil disalin.")
            except Exception as e:
                fail_count += 1
                err_msg = f"Gagal menyalin file: {str(e)}"
                errors.append({
                    "row_index": task.row_index,
                    "source_path": task.source_path,
                    "target_filename": task.target_filename,
                    "error": err_msg,
                })
                self.item_finished.emit(task.row_index, False, err_msg)

        self.export_completed.emit(success_count, fail_count, skipped_count, errors)
