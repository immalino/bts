"""
Unit tests untuk src/core/exporter.py dan src/core/image_loader.py
Memverifikasi:
1. File asli tetap utuh setelah ekspor (hash SHA-256 sama persis sebelum & sesudah ekspor).
2. File tujuan berhasil dibuat dengan nama baru dan format ekstensi yang sesuai.
3. Penanganan allow_overwrite=True vs allow_overwrite=False.
4. Fitur cancel() untuk menghentikan proses ekspor.
5. Pembuatan thumbnail dan fallback saat file gambar korup atau missing.
"""

import hashlib
import os
import pytest
from PIL import Image

from src.core.exporter import ExportTask, ExporterThread
from src.core.image_loader import create_thumbnail


def compute_sha256(file_path: str) -> str:
    """Menghitung hash SHA-256 dari file untuk menguji integritas data."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


class TestImageLoader:
    def test_create_thumbnail_valid_image(self, tmp_path):
        img_path = str(tmp_path / "sample.jpg")
        img = Image.new("RGB", (200, 100), color="blue")
        img.save(img_path, format="JPEG")

        pixmap = create_thumbnail(img_path, (64, 64))
        assert pixmap is not None
        assert not pixmap.isNull()
        assert pixmap.width() <= 64
        assert pixmap.height() <= 64

    def test_create_thumbnail_with_exif_orientation(self, tmp_path):
        img_path = str(tmp_path / "exif_sample.jpg")
        img = Image.new("RGB", (100, 200), color="red")
        # Simpan dengan tag EXIF orientation (6 = Rotate 90 CW)
        exif = img.getexif()
        exif[0x0112] = 6
        img.save(img_path, format="JPEG", exif=exif)

        pixmap = create_thumbnail(img_path, (64, 64))
        assert pixmap is not None
        assert not pixmap.isNull()

    def test_create_thumbnail_corrupt_file(self, tmp_path):
        corrupt_path = str(tmp_path / "corrupt.jpg")
        with open(corrupt_path, "wb") as f:
            f.write(b"NOT_A_VALID_IMAGE_DATA_CORRUPT_BYTES")

        pixmap = create_thumbnail(corrupt_path)
        assert pixmap is None

    def test_create_thumbnail_non_existent_file(self, tmp_path):
        pixmap = create_thumbnail(str(tmp_path / "does_not_exist.jpg"))
        assert pixmap is None


class TestExporterThread:
    def test_export_preserves_original_file_hash_zero_data_loss(self, tmp_path):
        """Pastikan hash SHA-256 file sumber tidak berubah sedikit pun sebelum dan sesudah diekspor."""
        src_dir = tmp_path / "source"
        src_dir.mkdir()
        out_dir = tmp_path / "output"

        src_file = src_dir / "original.jpg"
        content = b"ORIGINAL_PHOTO_CONTENT_RAW_BYTES_12345"
        src_file.write_bytes(content)

        hash_before = compute_sha256(str(src_file))

        task = ExportTask(
            source_path=str(src_file),
            target_filename="renamed_photo.jpg",
            row_index=0,
        )

        completed_events = []
        finished_items = []

        thread = ExporterThread(tasks=[task], output_directory=str(out_dir))
        thread.item_finished.connect(lambda r, s, m: finished_items.append((r, s, m)))
        thread.export_completed.connect(
            lambda s, f, sk, err: completed_events.append((s, f, sk, err))
        )

        thread.run()

        # 1. Pastikan hash file asli persis sama
        hash_after = compute_sha256(str(src_file))
        assert hash_before == hash_after

        # 2. Pastikan file target terbuat dengan isi sama
        dest_file = out_dir / "renamed_photo.jpg"
        assert dest_file.exists()
        assert compute_sha256(str(dest_file)) == hash_before

        # 3. Verifikasi sinyal yang dipancarkan
        assert len(completed_events) == 1
        success_cnt, fail_cnt, skipped_cnt, errors = completed_events[0]
        assert success_cnt == 1
        assert fail_cnt == 0
        assert skipped_cnt == 0
        assert errors == []

        assert len(finished_items) == 1
        assert finished_items[0][1] is True

    def test_export_multiple_files_order_and_signals(self, tmp_path):
        src_dir = tmp_path / "source"
        src_dir.mkdir()
        out_dir = tmp_path / "output"

        tasks = []
        for i in range(3):
            file_path = src_dir / f"photo_{i}.png"
            file_path.write_bytes(f"DATA_{i}".encode("utf-8"))
            tasks.append(
                ExportTask(
                    source_path=str(file_path),
                    target_filename=f"student_{i}.png",
                    row_index=i,
                )
            )

        progress_calls = []
        item_finished_calls = []
        completed_calls = []

        thread = ExporterThread(tasks=tasks, output_directory=str(out_dir))
        thread.progress_updated.connect(lambda c, t, f: progress_calls.append((c, t, f)))
        thread.item_finished.connect(lambda r, s, m: item_finished_calls.append((r, s, m)))
        thread.export_completed.connect(lambda s, f, sk, err: completed_calls.append((s, f, sk, err)))

        thread.run()

        assert len(progress_calls) == 3
        assert len(item_finished_calls) == 3
        assert len(completed_calls) == 1

        succ, fail, skip, errs = completed_calls[0]
        assert succ == 3
        assert fail == 0
        assert skip == 0

        for i in range(3):
            assert (out_dir / f"student_{i}.png").exists()

    def test_export_collision_without_overwrite(self, tmp_path):
        """Ketika file tujuan sudah ada dan allow_overwrite=False, proses harus melewatkan file tersebut."""
        src_dir = tmp_path / "source"
        src_dir.mkdir()
        out_dir = tmp_path / "output"
        out_dir.mkdir()

        src_file = src_dir / "foto1.jpg"
        src_file.write_bytes(b"NEW_VERSION")

        dest_file = out_dir / "target.jpg"
        dest_file.write_bytes(b"EXISTING_OLD_VERSION")

        task = ExportTask(
            source_path=str(src_file),
            target_filename="target.jpg",
            row_index=0,
        )

        completed_events = []
        thread = ExporterThread(
            tasks=[task],
            output_directory=str(out_dir),
            allow_overwrite=False,
        )
        thread.export_completed.connect(lambda s, f, sk, err: completed_events.append((s, f, sk, err)))

        thread.run()

        # File tujuan tidak boleh tertimpa
        assert dest_file.read_bytes() == b"EXISTING_OLD_VERSION"

        succ, fail, skip, errors = completed_events[0]
        assert succ == 0
        assert fail == 0
        assert skip == 1
        assert len(errors) == 1
        assert "sudah ada" in errors[0]["error"]

    def test_export_collision_with_overwrite(self, tmp_path):
        """Ketika allow_overwrite=True, file tujuan lama boleh diganti."""
        src_dir = tmp_path / "source"
        src_dir.mkdir()
        out_dir = tmp_path / "output"
        out_dir.mkdir()

        src_file = src_dir / "foto1.jpg"
        src_file.write_bytes(b"NEW_VERSION")

        dest_file = out_dir / "target.jpg"
        dest_file.write_bytes(b"EXISTING_OLD_VERSION")

        task = ExportTask(
            source_path=str(src_file),
            target_filename="target.jpg",
            row_index=0,
        )

        completed_events = []
        thread = ExporterThread(
            tasks=[task],
            output_directory=str(out_dir),
            allow_overwrite=True,
        )
        thread.export_completed.connect(lambda s, f, sk, err: completed_events.append((s, f, sk, err)))

        thread.run()

        # File tujuan berhasil diperbarui
        assert dest_file.read_bytes() == b"NEW_VERSION"

        succ, fail, skip, errors = completed_events[0]
        assert succ == 1
        assert fail == 0
        assert skip == 0
        assert errors == []

    def test_export_source_file_missing(self, tmp_path):
        out_dir = tmp_path / "output"

        task = ExportTask(
            source_path=str(tmp_path / "non_existent.jpg"),
            target_filename="result.jpg",
            row_index=5,
        )

        completed_events = []
        finished_items = []
        thread = ExporterThread(tasks=[task], output_directory=str(out_dir))
        thread.item_finished.connect(lambda r, s, m: finished_items.append((r, s, m)))
        thread.export_completed.connect(lambda s, f, sk, err: completed_events.append((s, f, sk, err)))

        thread.run()

        succ, fail, skip, errors = completed_events[0]
        assert succ == 0
        assert fail == 1
        assert skip == 0
        assert finished_items[0][1] is False
        assert "tidak ditemukan" in errors[0]["error"]

    def test_export_cancellation(self, tmp_path):
        """Uji pembatalan proses ekspor dengan cancel()."""
        src_dir = tmp_path / "source"
        src_dir.mkdir()
        out_dir = tmp_path / "output"

        tasks = []
        for i in range(5):
            p = src_dir / f"img_{i}.jpg"
            p.write_bytes(b"test")
            tasks.append(ExportTask(str(p), f"out_{i}.jpg", i))

        thread = ExporterThread(tasks=tasks, output_directory=str(out_dir))

        def on_item_finished(row, success, msg):
            if row == 1:
                thread.cancel()

        thread.item_finished.connect(on_item_finished)
        completed_events = []
        thread.export_completed.connect(lambda s, f, sk, err: completed_events.append((s, f, sk, err)))

        thread.run()

        assert thread.is_cancelled is True
        succ, fail, skip, errors = completed_events[0]
        # Item 0 dan 1 sukses disalin, item 2, 3, 4 dilewati karena cancel
        assert succ == 2
        assert skip == 3
        assert (out_dir / "out_0.jpg").exists()
        assert (out_dir / "out_1.jpg").exists()
        assert not (out_dir / "out_2.jpg").exists()
        assert not (out_dir / "out_3.jpg").exists()
        assert not (out_dir / "out_4.jpg").exists()
