"""
Photo Rename Studio - Jendela Utama (MainWindow)
"""

import os
import re
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStyle,
    QVBoxLayout,
    QWidget,
)
from datetime import datetime

from src.config import APP_ICON_ICO, APP_ICON_PNG, APP_NAME, BASE_DIR, DEFAULT_ROW_COUNT, ThemeColors
from src.core.excel_generator import ExcelGeneratorThread
from src.core.exporter import ExportTask, ExporterThread
from src.core.importer import import_names_from_csv, import_names_from_txt
from src.core.models import ProjectData, TemplateConfig
from src.core.storage import StorageManager
from src.core.validator import validate_batch
from src.ui.dynamic_row import DynamicPhotoRow, DynamicTextRow
from src.ui.project_dialog import ProjectManagerDialog
from src.ui.report_dialog import ReportDialog
from src.ui.row_widget import RowStatus, RowWidget
from src.ui.template_dialog import TemplateManagerDialog
from src.utils.file_utils import split_filename_and_ext


class MainWindow(QMainWindow):
    """
    Jendela Utama Aplikasi Photo Rename Studio.
    
    Fitur Utama:
    - Header aplikasi: Informasi Site aktif dan Template aktif yang sedang digunakan.
    - Toolbar aksi: Ganti/Pilih Site, Kelola Template, Impor Nama (TXT/CSV), Tambah Baris, Hapus Baris Kosong, Reset.
    - Area tengah: QScrollArea vertikal dengan DynamicPhotoRow dinamis atau 100 baris RowWidget secara default.
    - Panel bawah: Pemilihan Folder Output, opsi Checkbox Overwrite, Progress Bar, Status, dan Tombol Ekspor.
    """

    def __init__(
        self,
        default_rows: int = DEFAULT_ROW_COUNT,
        storage: Optional[StorageManager] = None,
    ):
        super().__init__()
        self.storage: StorageManager = storage or StorageManager()
        self.current_project: Optional[ProjectData] = None
        self.current_template: Optional[TemplateConfig] = None
        self.dynamic_rows: List[DynamicPhotoRow] = []
        self.default_rows_count: int = default_rows
        self.row_widgets: List[RowWidget] = []
        self.exporter_thread: Optional[ExporterThread] = None
        self.excel_generator_thread: Optional[ExcelGeneratorThread] = None

        self._init_ui()
        self._setup_connections()
        self.init_rows(self.default_rows_count)


    def _init_ui(self) -> None:
        self.setWindowTitle(APP_NAME)
        self.resize(1024, 768)
        self.setMinimumSize(880, 600)

        # Set Window Icon jika tersedia
        if APP_ICON_PNG.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))
        elif APP_ICON_ICO.exists():
            self.setWindowIcon(QIcon(str(APP_ICON_ICO)))

        # Central widget & main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.main_layout.setSpacing(12)

        # 1. Header Card (Judul & Panduan Singkat)
        self._create_header_section()

        # 2. Toolbar Card (Tombol Aksi & Statistik)
        self._create_toolbar_section()

        # 3. Middle Area (QScrollArea dengan baris-baris RowWidget)
        self._create_scroll_area_section()

        # 4. Bottom Panel Card (Folder Output & Opsi Overwrite)
        self._create_footer_section()

    def _create_header_section(self) -> None:
        """Membuat bagian header dengan judul, info site & template aktif, dan panduan ringkas."""
        header_card = QFrame(self)
        header_card.setObjectName("HeaderCard")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(6)

        # Baris Header: Judul & Status Badge Site/Template
        header_top_layout = QHBoxLayout()
        header_top_layout.setSpacing(10)

        title_label = QLabel(APP_NAME, header_card)
        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        header_top_layout.addWidget(title_label)
        header_top_layout.addStretch(1)

        # Badge Site Aktif
        self.lbl_active_site = QLabel("Site: (Belum dipilih)", header_card)
        self.lbl_active_site.setStyleSheet(f"""
            background-color: #EFF6FF;
            color: {ThemeColors.PRIMARY};
            border: 1px solid #BFDBFE;
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_top_layout.addWidget(self.lbl_active_site)

        # Badge Template Aktif
        self.lbl_active_template = QLabel("Template: (Belum dipilih)", header_card)
        self.lbl_active_template.setStyleSheet(f"""
            background-color: #F8FAFC;
            color: {ThemeColors.TEXT_MUTED};
            border: 1px solid {ThemeColors.BORDER};
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
        """)
        header_top_layout.addWidget(self.lbl_active_template)
        header_layout.addLayout(header_top_layout)

        guide_label = QLabel(
            "Alur Dokumen BTS: 1. Pilih/Buat Proyek Site  •  "
            "2. Tarik & lepas foto ke field template aktif (auto-save)  •  "
            "3. Generate dokumen laporan Excel.",
            header_card,
        )
        guide_label.setStyleSheet(f"""
            font-size: 12px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        header_layout.addWidget(guide_label)

        self.main_layout.addWidget(header_card)

    def _create_toolbar_section(self) -> None:
        """Membuat toolbar aksi di bagian atas."""
        toolbar_card = QFrame(self)
        toolbar_card.setObjectName("ToolbarCard")
        toolbar_layout = QHBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(14, 10, 14, 10)
        toolbar_layout.setSpacing(10)

        # Tombol Ganti / Pilih Site
        self.btn_select_site = QPushButton("Ganti / Pilih Site", toolbar_card)
        self.btn_select_site.setObjectName("PrimaryButton")
        self.btn_select_site.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon))
        self.btn_select_site.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select_site.setToolTip("Pilih proyek site yang aktif atau buat proyek site baru")
        toolbar_layout.addWidget(self.btn_select_site)

        # Tombol Kelola Template
        self.btn_manage_template = QPushButton("Kelola Template", toolbar_card)
        self.btn_manage_template.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.btn_manage_template.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_manage_template.setToolTip("Buka dialog manajemen template laporan Excel")
        toolbar_layout.addWidget(self.btn_manage_template)

        # Separator visual
        sep = QFrame(toolbar_card)
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet(f"color: {ThemeColors.BORDER};")
        toolbar_layout.addWidget(sep)

        # Tombol Impor
        self.btn_import = QPushButton("Impor Nama (TXT/CSV)", toolbar_card)
        self.btn_import.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import.setToolTip("Impor daftar nama dari file .txt atau .csv")
        toolbar_layout.addWidget(self.btn_import)

        # Tombol Tambah Baris
        self.btn_add_row = QPushButton("Tambah Baris", toolbar_card)
        self.btn_add_row.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.btn_add_row.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_row.setToolTip("Tambahkan 1 baris baru di posisi paling bawah")
        toolbar_layout.addWidget(self.btn_add_row)

        # Tombol Hapus Baris Kosong
        self.btn_remove_empty = QPushButton("Hapus Baris Kosong", toolbar_card)
        self.btn_remove_empty.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.btn_remove_empty.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_remove_empty.setToolTip("Hapus semua baris yang tidak memiliki foto dan nama")
        toolbar_layout.addWidget(self.btn_remove_empty)

        # Tombol Reset
        self.btn_reset = QPushButton("Reset Semua", toolbar_card)
        self.btn_reset.setObjectName("DangerButton")
        self.btn_reset.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset.setToolTip("Kembalikan semua baris dan pengaturan ke kondisi awal")
        toolbar_layout.addWidget(self.btn_reset)

        toolbar_layout.addStretch(1)

        # Label Statistik Baris
        self.lbl_stats = QLabel("Total: 0 baris | Foto: 0 | Siap: 0", toolbar_card)
        self.lbl_stats.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {ThemeColors.TEXT_MUTED};
        """)
        toolbar_layout.addWidget(self.lbl_stats)

        self.main_layout.addWidget(toolbar_card)

    def _create_scroll_area_section(self) -> None:
        """Membuat area QScrollArea vertikal untuk menampung baris-baris foto."""
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.scroll_content = QWidget()
        self.rows_layout = QVBoxLayout(self.scroll_content)
        self.rows_layout.setContentsMargins(6, 6, 6, 6)
        self.rows_layout.setSpacing(6)

        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area, stretch=1)

    def _create_footer_section(self) -> None:
        """Membuat panel bawah untuk pemilihan folder output dan opsi overwrite."""
        self.footer_card = QFrame(self)
        self.footer_card.setObjectName("FooterCard")
        footer_layout = QVBoxLayout(self.footer_card)
        footer_layout.setContentsMargins(16, 12, 16, 12)
        footer_layout.setSpacing(10)

        # Baris 1: Folder Output
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(8)

        lbl_dir = QLabel("Folder Output:", self.footer_card)
        lbl_dir.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT};")
        lbl_dir.setFixedWidth(95)
        dir_layout.addWidget(lbl_dir)

        self.input_output_dir = QLineEdit(self.footer_card)
        self.input_output_dir.setPlaceholderText("Pilih folder tujuan hasil ekspor foto...")
        dir_layout.addWidget(self.input_output_dir, stretch=1)

        self.btn_browse_dir = QPushButton("Pilih Folder", self.footer_card)
        self.btn_browse_dir.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.btn_browse_dir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse_dir.setFixedWidth(130)
        dir_layout.addWidget(self.btn_browse_dir)

        footer_layout.addLayout(dir_layout)

        # Baris 2: Checkbox Overwrite
        opt_layout = QHBoxLayout()
        self.chk_overwrite = QCheckBox("Izinkan menimpa file yang sudah ada (Overwrite)", self.footer_card)
        self.chk_overwrite.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_overwrite.setChecked(False)
        opt_layout.addWidget(self.chk_overwrite)
        opt_layout.addStretch(1)

        footer_layout.addLayout(opt_layout)

        # Baris 3: Progress Bar & Label Status Ekspor
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(4)

        self.lbl_export_status = QLabel("Siap untuk mengekspor.", self.footer_card)
        self.lbl_export_status.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 500;
            color: {ThemeColors.TEXT_MUTED};
        """)
        progress_layout.addWidget(self.lbl_export_status)

        self.progress_bar = QProgressBar(self.footer_card)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)

        footer_layout.addLayout(progress_layout)

        # Baris 4: Tombol Aksi Ekspor & Tombol Batal
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        self.btn_cancel_export = QPushButton("Batal Proses", self.footer_card)
        self.btn_cancel_export.setObjectName("DangerButton")
        self.btn_cancel_export.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.btn_cancel_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel_export.setEnabled(False)
        self.btn_cancel_export.setVisible(False)
        action_layout.addWidget(self.btn_cancel_export)

        action_layout.addStretch(1)

        self.btn_export = QPushButton("Generate Dokumen Excel", self.footer_card)
        self.btn_export.setObjectName("ExportButton")
        self.btn_export.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setToolTip("Mulai validasi dan generate dokumen laporan Excel")
        action_layout.addWidget(self.btn_export)

        footer_layout.addLayout(action_layout)

        self.main_layout.addWidget(self.footer_card)

    def _setup_connections(self) -> None:
        """Menghubungkan sinyal aksi tombol ke method penangan."""
        self.btn_select_site.clicked.connect(self.open_project_manager)
        self.btn_manage_template.clicked.connect(self.open_template_manager)
        self.btn_import.clicked.connect(self.on_import_clicked)
        self.btn_add_row.clicked.connect(self.on_add_row_clicked)
        self.btn_remove_empty.clicked.connect(self.on_remove_empty_clicked)
        self.btn_reset.clicked.connect(self.on_reset_all_clicked)
        self.btn_browse_dir.clicked.connect(self.on_choose_directory_clicked)
        self.btn_export.clicked.connect(self.start_export)
        self.btn_cancel_export.clicked.connect(self.cancel_export)


    # =========================================================================
    # Manajemen Proyek & Dynamic Photo Workspace (Sesi 11)
    # =========================================================================

    def _update_header_info(self) -> None:
        """Memperbarui informasi site dan template aktif di header."""
        site_name = self.current_project.site_name if self.current_project else "(Belum dipilih)"
        self.lbl_active_site.setText(f"Site: {site_name}")

        template_name = self.current_template.name if self.current_template else "(Belum dipilih)"
        self.lbl_active_template.setText(f"Template: {template_name}")

    def open_project_manager(self) -> None:
        """Membuka dialog ProjectManagerDialog untuk memilih atau membuat site baru."""
        dlg = ProjectManagerDialog(storage=self.storage, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            project = dlg.get_selected_project()
            if project:
                self.set_project(project)

    def open_template_manager(self) -> None:
        """Membuka dialog TemplateManagerDialog untuk mengelola template Excel."""
        dlg = TemplateManagerDialog(storage=self.storage, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            template = dlg.get_selected_template()
            if template:
                self.set_template(template)

    def set_project(self, project: ProjectData) -> None:
        """
        Menyetel proyek site aktif, memuat template terkait, dan me-render workspace dinamis.
        """
        self.current_project = project
        try:
            self.current_template = self.storage.load_template(project.template_id)
        except Exception:
            self.current_template = None

        self._update_header_info()

        if self.current_template:
            self.render_dynamic_workspace(self.current_template, self.current_project)
        else:
            QMessageBox.warning(
                self,
                "Template Tidak Ditemukan",
                f"Template ID '{project.template_id}' tidak ditemukan di penyimpanan.\n"
                "Silakan pilih atau buat template melalui tombol 'Kelola Template'.",
            )

    def set_template(self, template: TemplateConfig) -> None:
        """
        Menyetel template aktif dan me-render workspace dinamis.
        """
        self.current_template = template
        if self.current_project:
            self.current_project.template_id = template.template_id
            self.storage.save_project(self.current_project)

        self._update_header_info()
        self.render_dynamic_workspace(template, self.current_project)

    def render_dynamic_workspace(
        self,
        template: TemplateConfig,
        project: Optional[ProjectData] = None,
    ) -> None:
        """
        Me-render daftar DynamicPhotoRow dan DynamicTextRow pada ScrollArea sesuai daftar field template.
        """
        self.scroll_content.setUpdatesEnabled(False)
        self.clear_all_rows()

        for idx, fld in enumerate(template.fields, start=1):
            fld_type = getattr(fld, "field_type", "photo")
            if fld_type == "text":
                row = DynamicTextRow(
                    field_config=fld,
                    row_index=idx,
                    parent=self.scroll_content,
                )
                if project and fld.field_id in project.text_assignments:
                    row.set_text(project.text_assignments[fld.field_id], emit_signal=False)
                elif getattr(fld, "default_text", ""):
                    row.set_text(fld.default_text, emit_signal=False)

                row.text_changed.connect(self._on_dynamic_text_changed)
                row.data_changed.connect(self.update_summary_stats)
            else:
                row = DynamicPhotoRow(
                    field_config=fld,
                    row_index=idx,
                    parent=self.scroll_content,
                )
                # Jika ada foto yang sudah terpasang di project, pasang ke row
                if project and fld.field_id in project.photo_assignments:
                    photo_path = project.photo_assignments[fld.field_id]
                    if photo_path and os.path.isfile(photo_path):
                        row.set_photo(photo_path, emit_signal=False)

                row.photo_changed.connect(self._on_dynamic_photo_changed)
                row.data_changed.connect(self.update_summary_stats)

            self.dynamic_rows.append(row)
            self.rows_layout.addWidget(row)

        self.rows_layout.addStretch()
        self.scroll_content.setUpdatesEnabled(True)
        self.update_summary_stats()

    def _on_dynamic_photo_changed(self, field_id: str, photo_path: str) -> None:
        """
        Auto-save perubahan foto ke data proyek aktif dan persistensi ke storage.
        """
        if self.current_project:
            if photo_path:
                self.current_project.photo_assignments[field_id] = photo_path
            else:
                self.current_project.photo_assignments.pop(field_id, None)

            self.storage.save_project(self.current_project)

        self.update_summary_stats()

    def _on_dynamic_text_changed(self, field_id: str, text_value: str) -> None:
        """
        Auto-save perubahan teks ke data proyek aktif dan persistensi ke storage.
        """
        if self.current_project:
            if text_value:
                self.current_project.text_assignments[field_id] = text_value
            else:
                self.current_project.text_assignments.pop(field_id, None)

            self.storage.save_project(self.current_project)

        self.update_summary_stats()

    # =========================================================================
    # Manajemen Baris (Row Management)
    # =========================================================================

    def init_rows(self, count: int = DEFAULT_ROW_COUNT) -> None:
        """Menginisialisasi sejumlah baris (default 100 baris)."""
        self.scroll_content.setUpdatesEnabled(False)
        self.clear_all_rows()

        for i in range(1, count + 1):
            row = RowWidget(row_index=i, parent=self.scroll_content)
            row.data_changed.connect(self._on_row_data_changed)
            self.row_widgets.append(row)
            self.rows_layout.addWidget(row)

        self.rows_layout.addStretch()
        self.scroll_content.setUpdatesEnabled(True)
        self.update_summary_stats()

    def clear_all_rows(self) -> None:
        """Membersihkan seluruh widget baris yang ada di layout."""
        for row in self.row_widgets:
            self.rows_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self.row_widgets.clear()

        for row in self.dynamic_rows:
            self.rows_layout.removeWidget(row)
            row.setParent(None)
            row.deleteLater()
        self.dynamic_rows.clear()

        # Bersihkan item stretch yang tersisa di layout
        while self.rows_layout.count() > 0:
            item = self.rows_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def add_row(
        self,
        target_name: Optional[str] = None,
        photo_path: Optional[str] = None,
    ) -> RowWidget:
        """Menambahkan satu baris baru di akhir daftar baris."""
        next_index = len(self.row_widgets) + 1
        row = RowWidget(row_index=next_index, parent=self.scroll_content)
        row.data_changed.connect(self._on_row_data_changed)

        if target_name:
            row.set_target_name(target_name)
        if photo_path:
            row.set_source_photo(photo_path)

        # Selipkan widget sebelum stretch (item terakhir layout)
        insert_pos = max(0, self.rows_layout.count() - 1)
        self.rows_layout.insertWidget(insert_pos, row)
        self.row_widgets.append(row)

        self.update_summary_stats()
        return row

    def on_add_row_clicked(self) -> None:
        """Handler tombol tambah baris."""
        self.add_row()

    def on_remove_empty_clicked(self) -> None:
        """Menghapus semua baris yang kosong (tanpa foto dan tanpa nama)."""
        empty_rows: List[RowWidget] = []
        for row in self.row_widgets:
            data = row.get_data()
            if not data["source_photo"] and not data["target_stem"]:
                empty_rows.append(row)

        if not empty_rows:
            QMessageBox.information(
                self,
                "Info",
                "Tidak ada baris kosong untuk dihapus.",
            )
            return

        self.scroll_content.setUpdatesEnabled(False)
        for row in empty_rows:
            self.rows_layout.removeWidget(row)
            self.row_widgets.remove(row)
            row.setParent(None)
            row.deleteLater()

        # Renumber baris yang tersisa
        for idx, row in enumerate(self.row_widgets, start=1):
            row.set_row_index(idx)

        self.scroll_content.setUpdatesEnabled(True)
        self.update_summary_stats()

        QMessageBox.information(
            self,
            "Baris Dihapus",
            f"Berhasil menghapus {len(empty_rows)} baris kosong.",
        )

    def on_reset_all_clicked(self) -> None:
        """Mereset semua baris dan input ke kondisi awal setelah konfirmasi."""
        reply = QMessageBox.question(
            self,
            "Konfirmasi Reset",
            "Apakah Anda yakin ingin mereset semua baris dan pengaturan kembali ke 100 baris kosong?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.reset_all()

    def reset_all(self) -> None:
        """Eksekusi reset semua data."""
        self.input_output_dir.clear()
        self.chk_overwrite.setChecked(False)
        self.progress_bar.setValue(0)
        self.lbl_export_status.setText("Siap untuk mengekspor.")
        self.lbl_export_status.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 500;
            color: {ThemeColors.TEXT_MUTED};
        """)
        self.current_project = None
        self.current_template = None
        self._update_header_info()
        self.init_rows(self.default_rows_count)


    # =========================================================================
    # Impor Nama (TXT / CSV)
    # =========================================================================

    def on_import_clicked(self) -> None:
        """Membuka dialog file untuk memilih daftar nama TXT atau CSV."""
        file_filter = "File Nama (*.txt *.csv);;File Teks (*.txt);;File CSV (*.csv);;Semua File (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih File Daftar Nama",
            "",
            file_filter,
        )

        if not file_path:
            return

        try:
            imported_count = self.import_names_from_file_path(file_path)
            QMessageBox.information(
                self,
                "Impor Berhasil",
                f"Berhasil mengimpor {imported_count} nama ke dalam baris.",
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Gagal Impor",
                f"Terjadi kesalahan saat mengimpor nama:\n{str(e)}",
            )

    def import_names_from_file_path(self, file_path: str) -> int:
        """
        Mengimpor nama dari path file TXT atau CSV.
        Jika nama lebih banyak daripada baris saat ini, tambahkan baris otomatis.
        Mengembalikan jumlah nama yang berhasil diimpor.
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == ".csv":
            names = import_names_from_csv(file_path)
        else:
            names = import_names_from_txt(file_path)

        if not names:
            return 0

        self.scroll_content.setUpdatesEnabled(False)

        # Jika nama yang diimpor melebihi jumlah baris saat ini, tambahkan baris baru
        needed_rows = len(names)
        current_rows = len(self.row_widgets)
        if needed_rows > current_rows:
            diff = needed_rows - current_rows
            for _ in range(diff):
                self.add_row()

        # Petakan nama ke baris-baris
        for i, name in enumerate(names):
            self.row_widgets[i].set_target_name(name)

        self.scroll_content.setUpdatesEnabled(True)
        self.update_summary_stats()
        return len(names)

    # =========================================================================
    # Pemilihan Folder Output & Getter/Setter
    # =========================================================================

    def on_choose_directory_clicked(self) -> None:
        """Membuka dialog pemilihan folder output."""
        current_dir = self.input_output_dir.text().strip()
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Pilih Folder Output",
            current_dir if os.path.isdir(current_dir) else "",
        )
        if dir_path:
            self.set_output_directory(dir_path)

    def set_output_directory(self, path: str) -> None:
        """Menyetel path folder output."""
        self.input_output_dir.setText(os.path.abspath(path))

    def get_output_directory(self) -> str:
        """Mengambil path folder output."""
        return self.input_output_dir.text().strip()

    def set_overwrite_allowed(self, allowed: bool) -> None:
        """Menyetel opsi overwrite."""
        self.chk_overwrite.setChecked(allowed)

    def is_overwrite_allowed(self) -> bool:
        """Memeriksa apakah opsi overwrite dicentang."""
        return self.chk_overwrite.isChecked()

    def get_all_rows_data(self) -> List[Dict[str, Any]]:
        """Mengambil data semua baris saat ini."""
        return [row.get_data() for row in self.row_widgets]

    # =========================================================================
    # Pembaruan Status & Sinyal
    # =========================================================================

    def _on_row_data_changed(self) -> None:
        """Dipanggil saat salah satu baris mengalami perubahan data."""
        self.update_summary_stats()

    def update_summary_stats(self) -> None:
        """Menghitung dan menampilkan statistik baris saat ini."""
        if self.dynamic_rows:
            total = len(self.dynamic_rows)
            photo_rows = [r for r in self.dynamic_rows if getattr(r, "field_type", "photo") == "photo"]
            text_rows = [r for r in self.dynamic_rows if getattr(r, "field_type", "photo") == "text"]

            if not text_rows:
                with_photos = len([r for r in photo_rows if r.get_photo()])
                self.lbl_stats.setText(f"Total: {total} field | Foto Terisi: {with_photos} / {total}")
            elif not photo_rows:
                with_texts = len([r for r in text_rows if r.get_text()])
                self.lbl_stats.setText(f"Total: {total} field | Teks Terisi: {with_texts} / {total}")
            else:
                photo_filled = len([r for r in photo_rows if r.get_photo()])
                text_filled = len([r for r in text_rows if r.get_text()])
                total_filled = photo_filled + text_filled
                self.lbl_stats.setText(
                    f"Total: {total} field | Terisi: {total_filled} / {total} "
                    f"(Foto: {photo_filled}/{len(photo_rows)}, Teks: {text_filled}/{len(text_rows)})"
                )
            return

        total = len(self.row_widgets)
        with_photos = 0
        ready_count = 0
        error_count = 0

        for row in self.row_widgets:
            if row.source_photo:
                with_photos += 1
            if row._status == RowStatus.READY:
                ready_count += 1
            elif row._status == RowStatus.ERROR:
                error_count += 1

        stats_text = f"Total: {total} baris | Foto: {with_photos} | Siap: {ready_count}"
        if error_count > 0:
            stats_text += f" | Error: {error_count}"

        self.lbl_stats.setText(stats_text)

    # =========================================================================
    # Alur Proses Ekspor (Export Pipeline)
    # =========================================================================

    def start_export(self) -> None:
        """
        Memulai proses validasi dan ekspor/generate tergantung mode aktif:
        - Jika dynamic workspace aktif (berbasis template): jalankan start_excel_generation() via ExcelGeneratorThread.
        - Jika baris statis (rename biasa): jalankan start_photo_rename_export() via ExporterThread.
        """
        if self.dynamic_rows:
            self.start_excel_generation()
        else:
            self.start_photo_rename_export()

    def start_excel_generation(self) -> None:
        """
        Memulai alur validasi dan pembuatan dokumen Excel laporan foto via ExcelGeneratorThread.
        """
        if not self.current_template:
            QMessageBox.warning(
                self,
                "Template Belum Dipilih",
                "Template laporan Excel belum dipilih.\n"
                "Silakan buka atau buat proyek site dengan template yang valid.",
            )
            return

        if not self.current_template.template_file_path or not os.path.isfile(self.current_template.template_file_path):
            QMessageBox.warning(
                self,
                "Template Tidak Ditemukan",
                f"File template Excel tidak ditemukan pada lokasi:\n{self.current_template.template_file_path}",
            )
            return

        filled_photo_assignments = {
            row.get_field_id(): row.get_photo()
            for row in self.dynamic_rows
            if getattr(row, "field_type", "photo") == "photo" and row.get_photo() and os.path.isfile(row.get_photo())
        }
        filled_text_assignments = {
            row.get_field_id(): row.get_text()
            for row in self.dynamic_rows
            if getattr(row, "field_type", "photo") == "text" and row.get_text().strip()
        }

        if not filled_photo_assignments and not filled_text_assignments:
            has_photo_fields = any(getattr(r, "field_type", "photo") == "photo" for r in self.dynamic_rows)
            has_text_fields = any(getattr(r, "field_type", "photo") == "text" for r in self.dynamic_rows)
            if has_photo_fields and not has_text_fields:
                title = "Foto Belum Dimasukkan"
                msg = (
                    "Belum ada foto yang dimasukkan pada baris template.\n"
                    "Silakan masukkan setidaknya satu foto sebelum melakukan generate dokumen Excel."
                )
            elif has_text_fields and not has_photo_fields:
                title = "Teks Belum Dimasukkan"
                msg = (
                    "Belum ada teks yang dimasukkan pada baris template.\n"
                    "Silakan masukkan setidaknya satu teks sebelum melakukan generate dokumen Excel."
                )
            else:
                title = "Data Belum Dimasukkan"
                msg = (
                    "Belum ada foto atau teks yang dimasukkan pada baris template.\n"
                    "Silakan masukkan setidaknya satu foto atau teks sebelum melakukan generate dokumen Excel."
                )
            QMessageBox.warning(self, title, msg)
            return

        # Tentukan nama dan lokasi file output default
        site_slug = "BTS_Site"
        if self.current_project and self.current_project.site_name.strip():
            site_slug = re.sub(r'[\\/*?:"<>|\s]+', "_", self.current_project.site_name.strip())
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"Laporan_{site_slug}_{date_str}.xlsx"

        if self.input_output_dir.text().strip() and os.path.isdir(self.input_output_dir.text().strip()):
            initial_dir = self.input_output_dir.text().strip()
        elif self.current_project and self.current_project.output_dir and os.path.isdir(self.current_project.output_dir):
            initial_dir = self.current_project.output_dir
        else:
            initial_dir = str(BASE_DIR / "output")
            os.makedirs(initial_dir, exist_ok=True)

        default_save_path = os.path.join(initial_dir, default_name)

        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Dokumen Laporan Excel",
            default_save_path,
            "Excel Spreadsheet (*.xlsx);;Semua Berkas (*.*)",
        )
        if not output_file:
            return

        out_dir = os.path.dirname(os.path.abspath(output_file))
        self.set_output_directory(out_dir)
        if self.current_project:
            self.current_project.output_dir = out_dir
            self.storage.save_project(self.current_project)

        # Kunci kontrol UI dan jalankan generator thread di background
        self._set_exporting_state(True)
        self.progress_bar.setRange(0, len(self.dynamic_rows) + 1)
        self.progress_bar.setValue(0)
        self.lbl_export_status.setText("Menyiapkan dokumen Excel...")
        self.lbl_export_status.setStyleSheet(
            f"font-size: 11px; font-weight: 500; color: {ThemeColors.TEXT_MUTED};"
        )

        self.excel_generator_thread = ExcelGeneratorThread(
            template=self.current_template,
            output_path=output_file,
            photo_assignments=filled_photo_assignments,
            text_assignments=filled_text_assignments,
            fields=[row.get_field_config() for row in self.dynamic_rows],
            project_data=self.current_project,
            parent=self,
        )
        self.excel_generator_thread.progress_updated.connect(self._on_excel_progress)
        self.excel_generator_thread.item_finished.connect(self._on_excel_item_finished)
        self.excel_generator_thread.generation_completed.connect(self._on_excel_completed)
        self.excel_generator_thread.start()

    def _on_excel_progress(self, current: int, total: int, message: str) -> None:
        """Update progress bar dan label status Excel generator secara real-time."""
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.lbl_export_status.setText(message)

    def _on_excel_item_finished(self, field_id: str, success: bool, message: str) -> None:
        """Dipanggil saat satu foto selesai disisipkan ke Excel."""
        for row in self.dynamic_rows:
            if row.get_field_id() == field_id:
                if not success:
                    row.lbl_status.setText("Error")
                    row.lbl_status.setStyleSheet(f"""
                        QLabel {{
                            background-color: #FEE2E2;
                            color: {ThemeColors.ERROR};
                            font-size: 11px;
                            font-weight: 700;
                            border-radius: 4px;
                            border: 1px solid #FCA5A5;
                        }}
                    """)
                break

    def _on_excel_completed(
        self,
        output_path: str,
        success_count: int,
        fail_count: int,
        errors: list,
    ) -> None:
        """Dipanggil saat ExcelGeneratorThread selesai."""
        self._set_exporting_state(False)
        self.progress_bar.setValue(self.progress_bar.maximum())

        if self.current_project:
            self.current_project.last_exported_at = datetime.now().isoformat()
            self.storage.save_project(self.current_project)

        if self.excel_generator_thread and self.excel_generator_thread.is_cancelled:
            self.progress_bar.setValue(0)
            self.lbl_export_status.setText("Pembuatan dokumen dibatalkan.")
            QMessageBox.information(
                self,
                "Dibatalkan",
                "Proses pembuatan dokumen Excel telah dibatalkan.",
            )
            return

        status_text = f"Selesai: {success_count} foto disisipkan, {fail_count} gagal/dilewati."
        self.lbl_export_status.setText(status_text)
        color = ThemeColors.SUCCESS if fail_count == 0 else ThemeColors.WARNING
        self.lbl_export_status.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {color};"
        )
        self.update_summary_stats()

        dialog = ReportDialog(
            success_count=success_count,
            fail_count=fail_count,
            skipped_count=0,
            errors=errors,
            output_directory=os.path.dirname(os.path.abspath(output_path)) if output_path else "",
            excel_path=output_path if (output_path and os.path.isfile(output_path)) else None,
            parent=self,
        )
        dialog.exec()

    def start_photo_rename_export(self) -> None:
        """
        Memulai proses validasi dan ekspor baris rename foto biasa (Tahap 1):
        1. Kumpulkan data seluruh baris aktif.
        2. Jalankan validasi batch (validate_batch).
        3. Jika tidak valid, sorot baris yang bermasalah dan munculkan pesan error.
        4. Jika valid, kunci UI dan jalankan ExporterThread di background thread (non-blocking).
        """
        raw_items = []
        for row in self.row_widgets:
            data = row.get_data()
            raw_items.append({
                "row_index": row.row_index,
                "source_path": data.get("source_photo") or "",
                "target_name": data.get("target_name") or "",
            })

        output_dir = self.get_output_directory()
        allow_overwrite = self.is_overwrite_allowed()

        is_valid, error_list = validate_batch(
            row_items=raw_items,
            output_dir=output_dir,
            allow_overwrite=allow_overwrite,
        )

        if not is_valid:
            first_problematic_row: Optional[RowWidget] = None
            for err in error_list:
                match = re.search(r"Baris (\d+):", err)
                if match:
                    row_idx = int(match.group(1))
                    for row in self.row_widgets:
                        if row.row_index == row_idx:
                            row.set_status(RowStatus.ERROR, err)
                            if first_problematic_row is None:
                                first_problematic_row = row
                            break

            self.update_summary_stats()

            if first_problematic_row is not None:
                self.scroll_area.ensureWidgetVisible(first_problematic_row)
            elif not output_dir or not os.path.isdir(output_dir):
                self.input_output_dir.setFocus()

            self.lbl_export_status.setText("Validasi gagal: perbaiki baris yang bermasalah.")
            self.lbl_export_status.setStyleSheet(
                f"font-size: 11px; font-weight: 600; color: {ThemeColors.ERROR};"
            )

            max_display = 8
            err_summary = "\n• " + "\n• ".join(error_list[:max_display])
            if len(error_list) > max_display:
                err_summary += f"\n... dan {len(error_list) - max_display} kesalahan lainnya."

            QMessageBox.warning(
                self,
                "Validasi Ekspor Gagal",
                f"Ditemukan kendala sebelum ekspor dapat dimulai:\n{err_summary}",
            )
            return

        # Kumpulkan tugas ekspor yang valid
        tasks: List[ExportTask] = []
        for row in self.row_widgets:
            data = row.get_data()
            src = data.get("source_photo")
            tgt = data.get("target_name")
            if src and tgt:
                _, src_ext = split_filename_and_ext(src)
                tgt_stem, tgt_ext = split_filename_and_ext(tgt)
                final_ext = tgt_ext if tgt_ext else src_ext
                final_filename = f"{tgt_stem}{final_ext}"
                tasks.append(ExportTask(
                    source_path=src,
                    target_filename=final_filename,
                    row_index=row.row_index,
                ))

        if not tasks:
            QMessageBox.information(
                self,
                "Tidak Ada Foto",
                "Tidak ada baris foto dan nama yang siap untuk diekspor.",
            )
            return

        # Kunci kontrol UI dan mulai proses ekspor di background thread
        self._set_exporting_state(True)
        self.progress_bar.setRange(0, len(tasks))
        self.progress_bar.setValue(0)
        self.lbl_export_status.setText(f"Menyiapkan ekspor {len(tasks)} foto...")
        self.lbl_export_status.setStyleSheet(
            f"font-size: 11px; font-weight: 500; color: {ThemeColors.TEXT_MUTED};"
        )

        self.exporter_thread = ExporterThread(
            tasks=tasks,
            output_directory=output_dir,
            allow_overwrite=allow_overwrite,
            parent=self,
        )
        self.exporter_thread.progress_updated.connect(self._on_export_progress)
        self.exporter_thread.item_finished.connect(self._on_export_item_finished)
        self.exporter_thread.export_completed.connect(self._on_export_completed)
        self.exporter_thread.start()

    def cancel_export(self) -> None:
        """Membatalkan proses ekspor atau pembuatan dokumen yang sedang berlangsung."""
        if self.excel_generator_thread and self.excel_generator_thread.isRunning():
            self.excel_generator_thread.cancel()
            self.btn_cancel_export.setEnabled(False)
            self.lbl_export_status.setText("Membatalkan pembuatan dokumen Excel...")
            return

        if self.exporter_thread and self.exporter_thread.isRunning():
            self.exporter_thread.cancel()
            self.btn_cancel_export.setEnabled(False)
            self.lbl_export_status.setText("Membatalkan proses ekspor...")

    def _set_exporting_state(self, exporting: bool) -> None:
        """Mengunci atau membuka kembali kontrol UI selama proses ekspor/generate berlangsung."""
        self.btn_export.setEnabled(not exporting)
        self.btn_import.setEnabled(not exporting)
        self.btn_add_row.setEnabled(not exporting)
        self.btn_remove_empty.setEnabled(not exporting)
        self.btn_reset.setEnabled(not exporting)
        self.btn_browse_dir.setEnabled(not exporting)
        self.btn_select_site.setEnabled(not exporting)
        self.btn_manage_template.setEnabled(not exporting)
        self.input_output_dir.setEnabled(not exporting)
        self.chk_overwrite.setEnabled(not exporting)

        self.btn_cancel_export.setVisible(exporting)
        self.btn_cancel_export.setEnabled(exporting)

        for row in self.row_widgets:
            row.input_name.setEnabled(not exporting)
            row.btn_select.setEnabled(not exporting)
            row.btn_clear.setEnabled(not exporting)

        for row in self.dynamic_rows:
            if hasattr(row, "btn_select"):
                row.btn_select.setEnabled(not exporting)
            if hasattr(row, "edit_text"):
                row.edit_text.setEnabled(not exporting)
            if hasattr(row, "btn_clear"):
                row.btn_clear.setEnabled(not exporting)

    def _on_export_progress(self, current_index: int, total: int, current_filename: str) -> None:
        """Memperbarui progress bar dan status label secara real-time."""
        self.progress_bar.setValue(current_index)
        self.lbl_export_status.setText(f"Menyalin ({current_index}/{total}): {current_filename}")
        self.lbl_export_status.setStyleSheet(
            f"font-size: 11px; font-weight: 500; color: {ThemeColors.TEXT_MUTED};"
        )

    def _on_export_item_finished(self, row_index: int, success: bool, message: str) -> None:
        """Memperbarui status badge dan border baris secara real-time saat selesai disalin."""
        for row in self.row_widgets:
            if row.row_index == row_index:
                if success:
                    row.set_status(RowStatus.SUCCESS, message)
                else:
                    row.set_status(RowStatus.ERROR, message)
                break
        self.update_summary_stats()

    def _on_export_completed(
        self,
        success_count: int,
        fail_count: int,
        skipped_count: int,
        errors: list,
    ) -> None:
        """Menangani selesainya proses ekspor dan menampilkan modal dialog laporan."""
        self._set_exporting_state(False)
        self.progress_bar.setValue(self.progress_bar.maximum())
        status_text = f"Selesai: {success_count} berhasil, {fail_count} gagal, {skipped_count} dilewati."
        self.lbl_export_status.setText(status_text)
        color = ThemeColors.SUCCESS if fail_count == 0 else ThemeColors.WARNING
        self.lbl_export_status.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {color};"
        )
        self.update_summary_stats()

        dialog = ReportDialog(
            success_count=success_count,
            fail_count=fail_count,
            skipped_count=skipped_count,
            errors=errors,
            output_directory=self.get_output_directory(),
            parent=self,
        )
        dialog.exec()

    def closeEvent(self, event) -> None:
        """Menangani penutupan jendela saat proses ekspor/generate masih berlangsung."""
        is_running = (
            (hasattr(self, "exporter_thread") and self.exporter_thread and self.exporter_thread.isRunning())
            or (hasattr(self, "excel_generator_thread") and self.excel_generator_thread and self.excel_generator_thread.isRunning())
        )
        if is_running:
            reply = QMessageBox.question(
                self,
                "Proses Masih Berjalan",
                "Proses ekspor/generate masih berlangsung di latar belakang.\nApakah Anda yakin ingin membatalkan dan keluar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                if self.exporter_thread and self.exporter_thread.isRunning():
                    self.exporter_thread.cancel()
                    self.exporter_thread.wait(2000)
                if self.excel_generator_thread and self.excel_generator_thread.isRunning():
                    self.excel_generator_thread.cancel()
                    self.excel_generator_thread.wait(2000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

