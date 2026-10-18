"""
Photo Rename Studio - Script Demo Pengujian Visual RowWidget & DropZoneWidget
"""

import os
import sys

from PySide6.QtCore import Qt, QUrl, QMimeData, QPointF
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.config import ThemeColors
from src.ui.row_widget import RowWidget, RowStatus


class DemoRowWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo RowWidget & DropZone - Photo Rename Studio")
        self.resize(850, 520)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Header demo
        header = QLabel("Uji Visual: RowWidget & DropZoneWidget", self)
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E293B;")
        main_layout.addWidget(header)

        instruction = QLabel(
            "Coba interaksi:\n"
            "1. Drag file foto (.jpg, .png, .webp, dll) langsung ke kotak 'Tarik & Lepas Foto'.\n"
            "2. Klik 'Pilih Foto' untuk memilih dari dialog OS.\n"
            "3. Ketik nama baru pada input teks -> perhatikan label ekstensi dan perubahan badge status.\n"
            "4. Klik 'Hapus Foto' untuk mengosongkan foto.",
            self,
        )
        instruction.setStyleSheet(
            f"font-size: 12px; color: {ThemeColors.TEXT_MUTED}; background-color: #F8FAFC; padding: 10px; border-radius: 6px; border: 1px solid {ThemeColors.BORDER};"
        )
        main_layout.addWidget(instruction)

        # Scroll area berisi beberapa baris contoh
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.rows_layout = QVBoxLayout(scroll_content)
        self.rows_layout.setContentsMargins(4, 4, 4, 4)
        self.rows_layout.setSpacing(6)

        self.rows = []
        for i in range(1, 5):
            row = RowWidget(row_index=i, parent=scroll_content)
            row.data_changed.connect(self._on_row_data_changed)
            self.rows_layout.addWidget(row)
            self.rows.append(row)

        self.rows_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

        # Toolbar bawah untuk print data
        bottom_bar = QHBoxLayout()
        self.btn_print = QPushButton("Cetak Data Baris ke Konsol", self)
        self.btn_print.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_print.setStyleSheet(f"""
            QPushButton {{
                background-color: {ThemeColors.PRIMARY};
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ThemeColors.PRIMARY_HOVER};
            }}
        """)
        self.btn_print.clicked.connect(self._print_data)
        bottom_bar.addWidget(self.btn_print)

        self.lbl_info = QLabel("Siap menguji.", self)
        self.lbl_info.setStyleSheet(f"color: {ThemeColors.TEXT_MUTED}; font-size: 11px;")
        bottom_bar.addWidget(self.lbl_info, stretch=1)

        main_layout.addLayout(bottom_bar)

    def _on_row_data_changed(self) -> None:
        self.lbl_info.setText("Data baris mengalami perubahan.")

    def _print_data(self) -> None:
        print("\n--- DATA BARIS SAAT INI ---")
        for r in self.rows:
            data = r.get_data()
            print(f"Baris #{data['row_index']:02d}: Foto={data['source_photo']} | Target={data['target_name']} | Status={data['status']} ({data['status_message']})")
        print("---------------------------\n")
        self.lbl_info.setText("Data berhasil dicetak ke konsol!")


def run_automated_verification(window: DemoRowWindow, sample_img_path: str):
    """Menguji fungsionalitas drag-drop, input nama, thumbnail, status, dan clear secara otomatis."""
    print("[TEST] Memulai verifikasi fungsionalitas visual dan logis RowWidget...")
    row1 = window.rows[0]
    assert row1.get_data()["status"] == RowStatus.EMPTY, "Status awal harus Kosong"

    # 1. Simulasikan drop event file gambar
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(sample_img_path)])
    drop_event = QDropEvent(
        QPointF(10, 10),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    row1.drop_zone.dropEvent(drop_event)

    assert row1.source_photo == sample_img_path, f"Expected {sample_img_path}, got {row1.source_photo}"
    assert row1.lbl_extension.text() == ".jpg"
    print("[PASS] Drag & drop file gambar berhasil diset pada RowWidget.")

    # 2. Input nama valid
    row1.set_target_name("001_Ahmad_Dahlan")
    assert row1.get_data()["target_name"] == "001_Ahmad_Dahlan.jpg"
    assert row1.get_data()["status"] == RowStatus.READY
    print("[PASS] Input nama valid -> status berubah menjadi 'Siap'.")

    # 3. Input nama invalid Windows
    row1.set_target_name("001/Ahmad*Dahlan")
    assert row1.get_data()["status"] == RowStatus.ERROR
    print("[PASS] Input nama invalid -> status berubah menjadi 'Error'.")

    # 4. Kembalikan ke nama valid lalu uji tombol clear foto
    row1.set_target_name("001_Ahmad_Dahlan")
    row1.btn_clear.click()
    assert row1.source_photo is None
    assert row1.lbl_extension.text() == ""
    assert row1.get_data()["status"] == RowStatus.EMPTY
    print("[PASS] Tombol Hapus Foto berhasil mengosongkan foto.")

    print("[SUCCESS] Seluruh interaksi RowWidget dan DropZoneWidget lolos verifikasi!")


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = DemoRowWindow()
    window.show()

    # Jika dipanggil dengan flag --test atau dalam mode offscreen, jalankan verifikasi otomatis
    is_headless = "QT_QPA_PLATFORM" in os.environ and os.environ["QT_QPA_PLATFORM"] == "offscreen"
    is_test_mode = "--test" in sys.argv or is_headless

    if is_test_mode:
        import tempfile
        from PIL import Image

        temp_dir = tempfile.mkdtemp()
        sample_img = os.path.join(temp_dir, "foto_santri_01.jpg")
        img = Image.new("RGB", (200, 200), color=(73, 109, 137))
        img.save(sample_img)

        run_automated_verification(window, sample_img)
        window._print_data()

        if is_headless:
            print("Demo selesai dieksekusi dalam mode offscreen.")
            return 0

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
