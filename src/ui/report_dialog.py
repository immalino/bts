"""
Photo Rename Studio - Modal Dialog Laporan Hasil Ekspor & Dokumen Excel
"""

import os
from typing import Any, Dict, List, Optional, Union

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config import ThemeColors
from src.ui.icons import get_icon
from src.utils.file_utils import open_folder_in_explorer


class ReportDialog(QDialog):
    """
    Dialog modal ringkasan laporan hasil ekspor foto dan pembuatan dokumen Excel.
    
    Fitur:
    - Menampilkan kartu ringkasan: Total Diproses, Berhasil, Gagal, Dilewati.
    - Menampilkan tabel rincian kegagalan/error jika ada item yang gagal atau dilewati.
    - Tombol 'Buka Dokumen Excel' untuk membuka file spreadsheet secara langsung.
    - Tombol 'Buka Folder Output' untuk membuka hasil ekspor di File Explorer.
    - Tombol 'Tutup' untuk kembali ke jendela utama.
    """

    def __init__(
        self,
        success_count: int,
        fail_count: int,
        skipped_count: int,
        errors: List[Union[Dict[str, Any], str]],
        output_directory: str = "",
        excel_path: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.success_count = success_count
        self.fail_count = fail_count
        self.skipped_count = skipped_count
        self.errors = errors
        self.excel_path = excel_path

        if not output_directory and excel_path:
            self.output_directory = os.path.dirname(os.path.abspath(excel_path))
        else:
            self.output_directory = output_directory

        self._init_ui()

    def _init_ui(self) -> None:
        title_text = "Laporan Hasil Dokumen Excel" if self.excel_path else "Laporan Hasil Ekspor"
        self.setWindowTitle(title_text)
        self.resize(700, 520)
        self.setMinimumSize(560, 420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 1. Header Judul
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)

        title_label = QLabel(title_text, self)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        header_layout.addWidget(title_label)

        sub_info = (
            f"Dokumen: {os.path.basename(self.excel_path)}"
            if self.excel_path
            else f"Folder tujuan: {self.output_directory or '(Belum ditentukan)'}"
        )
        sub_label = QLabel(sub_info, self)
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

            error_header = QLabel("Rincian Item yang Gagal / Bermasalah:", self)
            error_header.setStyleSheet(f"""
                font-size: 13px;
                font-weight: 600;
                color: {ThemeColors.ERROR};
            """)
            error_section.addWidget(error_header)

            self.table_errors = QTableWidget(self)
            self.table_errors.setColumnCount(4)
            self.table_errors.setHorizontalHeaderLabels(
                ["No", "File Sumber", "Nama Target", "Keterangan / Alasan Error"]
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
                if isinstance(err, dict):
                    row_no = str(err.get("row_index", row_idx + 1))
                    src_path = str(err.get("source_path", "-"))
                    target_name = str(err.get("target_filename", "-"))
                    reason = str(err.get("error", "-"))
                else:
                    row_no = str(row_idx + 1)
                    src_path = "-"
                    target_name = "-"
                    reason = str(err)

                item_row = QTableWidgetItem(row_no)
                item_row.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_src = QTableWidgetItem(os.path.basename(src_path) if src_path != "-" else "-")
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
            success_layout.setSpacing(10)

            lbl_success_badge = QLabel("SUKSES", success_card)
            lbl_success_badge.setStyleSheet("""
                font-size: 13px;
                font-weight: 700;
                color: #166534;
                background-color: #DCFCE7;
                border: 1px solid #BBF7D0;
                border-radius: 4px;
                padding: 4px 14px;
            """)
            lbl_success_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            success_layout.addWidget(lbl_success_badge)

            msg_text = (
                "Dokumen Excel laporan foto berhasil digenerate dengan penataan gambar rapi!"
                if self.excel_path
                else "Semua foto berhasil disalin dan diganti namanya tanpa kendala!"
            )
            lbl_success_text = QLabel(msg_text, success_card)
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

        # Tombol Buka Dokumen Excel (jika ada file Excel)
        if self.excel_path and os.path.isfile(self.excel_path):
            self.btn_open_excel = QPushButton("Buka Dokumen Excel", self)
            self.btn_open_excel.setObjectName("PrimaryButton")
            self.btn_open_excel.setIcon(get_icon("file_spreadsheet", color="#ffffff", size=16))
            self.btn_open_excel.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_open_excel.clicked.connect(self._on_open_excel_clicked)
            footer_layout.addWidget(self.btn_open_excel)

        # Tombol Buka Folder Output
        self.btn_open_folder = QPushButton("Buka Folder Output", self)
        self.btn_open_folder.setIcon(get_icon("folder", size=16))
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.clicked.connect(self._on_open_folder_clicked)
        footer_layout.addWidget(self.btn_open_folder)

        footer_layout.addStretch(1)

        self.btn_close = QPushButton("Tutup", self)
        self.btn_close.setIcon(get_icon("x", size=16))
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

    def _on_open_excel_clicked(self) -> None:
        """Handler tombol untuk membuka dokumen Excel hasil secara langsung."""
        if not self.excel_path or not os.path.isfile(self.excel_path):
            QMessageBox.warning(
                self,
                "File Tidak Ditemukan",
                f"Dokumen Excel tidak ditemukan:\n{self.excel_path}",
            )
            return

        file_url = QUrl.fromLocalFile(os.path.abspath(self.excel_path))
        QDesktopServices.openUrl(file_url)

    def _on_open_folder_clicked(self) -> None:
        """Handler tombol untuk membuka folder output di File Explorer."""
        target_dir = self.output_directory
        if not target_dir and self.excel_path:
            target_dir = os.path.dirname(os.path.abspath(self.excel_path))

        if not target_dir or not os.path.isdir(target_dir):
            QMessageBox.warning(
                self,
                "Folder Tidak Ditemukan",
                f"Direktori output tidak ditemukan atau belum valid:\n{target_dir}",
            )
            return

        success = open_folder_in_explorer(target_dir)
        if not success:
            QMessageBox.warning(
                self,
                "Gagal Membuka Folder",
                f"Tidak dapat membuka direktori output:\n{target_dir}",
            )
