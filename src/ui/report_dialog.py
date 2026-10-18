"""
Photo Rename Studio - Modal Dialog Laporan Hasil Ekspor
"""

import os
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config import ThemeColors
from src.utils.file_utils import open_folder_in_explorer


class ReportDialog(QDialog):
    """
    Dialog modal ringkasan laporan hasil ekspor foto.
    
    Fitur:
    - Menampilkan kartu ringkasan: Total Diproses, Berhasil, Gagal, Dilewati.
    - Menampilkan tabel rincian kegagalan/error jika ada item yang gagal atau dilewati.
    - Tombol 'Buka Folder Output' untuk membuka hasil ekspor di File Explorer.
    - Tombol 'Tutup' untuk kembali ke jendela utama.
    """

    def __init__(
        self,
        success_count: int,
        fail_count: int,
        skipped_count: int,
        errors: List[Dict[str, Any]],
        output_directory: str,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.success_count = success_count
        self.fail_count = fail_count
        self.skipped_count = skipped_count
        self.errors = errors
        self.output_directory = output_directory

        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Laporan Hasil Ekspor")
        self.resize(680, 520)
        self.setMinimumSize(540, 420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 1. Header Judul
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title_label = QLabel("📊 Ringkasan Hasil Ekspor", self)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        header_layout.addWidget(title_label)

        dir_display = self.output_directory if self.output_directory else "(Belum ditentukan)"
        sub_label = QLabel(f"Folder tujuan: {dir_display}", self)
        sub_label.setStyleSheet(f"""
            font-size: 12px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        header_layout.addWidget(sub_label)
        layout.addLayout(header_layout)

        # 2. Kartu Statistik Ringkasan
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        total_processed = self.success_count + self.fail_count + self.skipped_count

        stats_layout.addWidget(
            self._create_stat_card("Total", total_processed, "#EFF6FF", ThemeColors.PRIMARY)
        )
        stats_layout.addWidget(
            self._create_stat_card("Berhasil", self.success_count, "#DCFCE7", "#166534")
        )
        stats_layout.addWidget(
            self._create_stat_card("Gagal", self.fail_count, "#FEE2E2", ThemeColors.ERROR)
        )
        stats_layout.addWidget(
            self._create_stat_card("Dilewati", self.skipped_count, "#FEF3C7", "#B45309")
        )

        layout.addLayout(stats_layout)

        # 3. Bagian Tabel Error atau Pesan Sukses Penuh
        if self.errors:
            error_section = QVBoxLayout()
            error_section.setSpacing(6)

            error_header = QLabel("⚠️ Rincian File yang Gagal / Bermasalah:", self)
            error_header.setStyleSheet(f"""
                font-size: 13px;
                font-weight: 600;
                color: {ThemeColors.ERROR};
            """)
            error_section.addWidget(error_header)

            self.table_errors = QTableWidget(self)
            self.table_errors.setColumnCount(4)
            self.table_errors.setHorizontalHeaderLabels(
                ["Baris", "File Sumber", "Nama Target", "Keterangan / Alasan Error"]
            )
            self.table_errors.setRowCount(len(self.errors))
            self.table_errors.setAlternatingRowColors(True)
            self.table_errors.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.table_errors.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

            header = self.table_errors.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

            self.table_errors.setColumnWidth(1, 150)
            self.table_errors.setColumnWidth(2, 150)

            for row_idx, err in enumerate(self.errors):
                row_num_str = str(err.get("row_index", "-"))
                src_path = str(err.get("source_path", "-"))
                src_name = os.path.basename(src_path) if src_path != "-" else "-"
                target_name = str(err.get("target_filename", "-"))
                reason = str(err.get("error", "-"))

                item_row = QTableWidgetItem(row_num_str)
                item_row.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_src = QTableWidgetItem(src_name)
                item_src.setToolTip(src_path)
                item_tgt = QTableWidgetItem(target_name)
                item_reason = QTableWidgetItem(reason)
                item_reason.setToolTip(reason)

                self.table_errors.setItem(row_idx, 0, item_row)
                self.table_errors.setItem(row_idx, 1, item_src)
                self.table_errors.setItem(row_idx, 2, item_tgt)
                self.table_errors.setItem(row_idx, 3, item_reason)

            error_section.addWidget(self.table_errors)
            layout.addLayout(error_section, stretch=1)
        else:
            success_card = QFrame(self)
            success_card.setStyleSheet("""
                QFrame {
                    background-color: #F0FDF4;
                    border: 1px solid #BBF7D0;
                    border-radius: 8px;
                    padding: 24px;
                }
            """)
            success_layout = QVBoxLayout(success_card)
            success_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl_success_icon = QLabel("🎉", success_card)
            lbl_success_icon.setStyleSheet("font-size: 32px;")
            lbl_success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            success_layout.addWidget(lbl_success_icon)

            lbl_success_text = QLabel(
                "Semua foto berhasil disalin dan diganti namanya tanpa kendala!",
                success_card,
            )
            lbl_success_text.setStyleSheet("""
                font-size: 14px;
                font-weight: 600;
                color: #166534;
            """)
            lbl_success_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            success_layout.addWidget(lbl_success_text)

            layout.addWidget(success_card, stretch=1)

        # 4. Footer Tombol Aksi
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        self.btn_open_folder = QPushButton("📁 Buka Folder Output", self)
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.clicked.connect(self._on_open_folder_clicked)
        footer_layout.addWidget(self.btn_open_folder)

        footer_layout.addStretch(1)

        self.btn_close = QPushButton("Tutup", self)
        self.btn_close.setObjectName("PrimaryButton")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setDefault(True)
        self.btn_close.clicked.connect(self.accept)
        footer_layout.addWidget(self.btn_close)

        layout.addLayout(footer_layout)

    def _create_stat_card(
        self,
        title: str,
        count: int,
        bg_color: str,
        text_color: str,
    ) -> QFrame:
        """Membuat komponen kartu metrik statistik ringkas."""
        card = QFrame(self)
        card.setFixedHeight(68)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {bg_color};
                border-radius: 8px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(10, 8, 10, 8)
        c_layout.setSpacing(2)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_count = QLabel(str(count), card)
        lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_count.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {text_color};
        """)
        c_layout.addWidget(lbl_count)

        lbl_title = QLabel(title, card)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {text_color};
        """)
        c_layout.addWidget(lbl_title)

        return card

    def _on_open_folder_clicked(self) -> None:
        """Handler tombol untuk membuka folder output di File Explorer."""
        if not self.output_directory or not os.path.isdir(self.output_directory):
            QMessageBox.warning(
                self,
                "Folder Tidak Ditemukan",
                f"Direktori output tidak ditemukan atau belum valid:\n{self.output_directory}",
            )
            return

        success = open_folder_in_explorer(self.output_directory)
        if not success:
            QMessageBox.warning(
                self,
                "Gagal Membuka Folder",
                f"Tidak dapat membuka direktori output:\n{self.output_directory}",
            )
