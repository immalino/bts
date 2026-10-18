"""
Photo Rename Studio - Antarmuka Visual Project Manager Dialog
Menyediakan dialog PySide6 untuk manajemen proyek site:
- Memilih dan membuka riwayat proyek site yang tersimpan
- Membuat proyek site baru (input Nama/ID Site dan pilihan template Excel)
- Menghapus riwayat proyek site
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
import uuid

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config import APP_ICON_PNG, ThemeColors
from src.core.models import ProjectData, TemplateConfig
from src.core.storage import StorageManager
from src.ui.icons import get_icon, render_svg_pixmap
from src.ui.template_dialog import TemplateManagerDialog


class NewProjectDialog(QDialog):
    """
    Dialog form visual untuk membuat proyek site baru.
    
    Input:
    - Nama / ID Site (contoh: "JKT-042 Pasar Minggu")
    - Pilihan Template Laporan Excel (dropdown dari template yang tersedia)
    """

    def __init__(
        self,
        storage: StorageManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.storage = storage
        self.created_project: Optional[ProjectData] = None
        self.available_templates: List[TemplateConfig] = []

        self._init_ui()
        self._load_templates()

    def _init_ui(self) -> None:
        self.setWindowTitle("Buat Proyek Site Baru")
        self.resize(480, 280)
        self.setMinimumSize(420, 240)
        self.setModal(True)

        if APP_ICON_PNG.is_file():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        lbl_title = QLabel("Proyek Site Baru", self)
        lbl_title.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        header_layout.addWidget(lbl_title)

        lbl_subtitle = QLabel(
            "Masukkan nama/ID site dan pilih template laporan yang akan digunakan",
            self,
        )
        lbl_subtitle.setStyleSheet(f"""
            font-size: 11px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # Form Group
        form_group = QGroupBox("Detail Proyek", self)
        form_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 12px;
                font-weight: 600;
                color: {ThemeColors.TEXT};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }}
        """)
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Nama / ID Site
        lbl_site = QLabel("Nama / ID Site:", form_group)
        lbl_site.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        form_layout.addWidget(lbl_site)

        self.edit_site_name = QLineEdit(form_group)
        self.edit_site_name.setPlaceholderText("Contoh: JKT-042 Pasar Minggu Telkomsel")
        form_layout.addWidget(self.edit_site_name)

        # 2. Pemilihan Template
        lbl_tpl = QLabel("Pilih Template Excel:", form_group)
        lbl_tpl.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        form_layout.addWidget(lbl_tpl)

        tpl_choice_layout = QHBoxLayout()
        tpl_choice_layout.setSpacing(8)

        self.combo_template = QComboBox(form_group)
        tpl_choice_layout.addWidget(self.combo_template, stretch=1)

        self.btn_manage_tpl = QPushButton("Kelola Template", form_group)
        self.btn_manage_tpl.setIcon(get_icon("file_spreadsheet", size=16))
        self.btn_manage_tpl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_manage_tpl.clicked.connect(self._on_manage_templates_clicked)
        tpl_choice_layout.addWidget(self.btn_manage_tpl)

        form_layout.addLayout(tpl_choice_layout)
        layout.addWidget(form_group)

        layout.addStretch(1)

        # Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        footer_layout.addStretch(1)

        self.btn_cancel = QPushButton("Batal", self)
        self.btn_cancel.setIcon(get_icon("x", size=14))
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)

        self.btn_create = QPushButton("Buat Proyek", self)
        self.btn_create.setObjectName("PrimaryButton")
        self.btn_create.setIcon(get_icon("plus", color="#FFFFFF", size=14))
        self.btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_create.setDefault(True)
        self.btn_create.clicked.connect(self._on_create_clicked)
        footer_layout.addWidget(self.btn_create)

        layout.addLayout(footer_layout)

    def _load_templates(self) -> None:
        self.combo_template.clear()
        self.available_templates = self.storage.list_templates()

        if not self.available_templates:
            self.combo_template.addItem("(Belum ada template - klik Kelola Template)")
            self.combo_template.setEnabled(False)
            self.btn_create.setEnabled(False)
        else:
            self.combo_template.setEnabled(True)
            self.btn_create.setEnabled(True)
            for tpl in self.available_templates:
                self.combo_template.addItem(
                    f"{tpl.name} ({len(tpl.fields)} field foto)",
                    tpl.template_id,
                )

    def _on_manage_templates_clicked(self) -> None:
        dlg = TemplateManagerDialog(storage=self.storage, parent=self)
        dlg.exec()
        self._load_templates()

    def _on_create_clicked(self) -> None:
        site_name = self.edit_site_name.text().strip()
        if not site_name:
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                "Nama atau ID Site tidak boleh kosong.",
            )
            self.edit_site_name.setFocus()
            return

        if self.combo_template.currentIndex() < 0 or not self.available_templates:
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                "Silakan pilih template laporan Excel terlebih dahulu.",
            )
            return

        template_id = self.combo_template.currentData()
        if not template_id:
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                "Template yang dipilih tidak valid.",
            )
            return

        project_id = f"proj_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
        new_project = ProjectData(
            project_id=project_id,
            site_name=site_name,
            template_id=str(template_id),
            photo_assignments={},
            created_at=datetime.now().isoformat(),
        )

        self.storage.save_project(new_project)
        self.created_project = new_project
        self.accept()

    def get_created_project(self) -> Optional[ProjectData]:
        """Mengambil ProjectData yang baru saja dibuat."""
        return self.created_project


class ProjectManagerDialog(QDialog):
    """
    Dialog modal manajemen proyek site.
    
    Fitur:
    - Menampilkan tabel seluruh riwayat proyek site yang tersimpan
    - Tombol "Proyek Site Baru" -> membuat site baru dan mengaitkannya ke template
    - Tombol "Buka Site" -> membuka workspace foto untuk site terpilih
    - Tombol "Hapus Site" -> menghapus riwayat proyek site dari storage
    - Tombol "Tutup" -> kembali ke jendela utama
    """

    def __init__(
        self,
        storage: Optional[StorageManager] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.storage = storage or StorageManager()
        self.selected_project: Optional[ProjectData] = None
        self.loaded_projects: List[ProjectData] = []

        self._init_ui()
        self.load_projects()

    def _init_ui(self) -> None:
        self.setWindowTitle("Manajemen Proyek Site")
        self.resize(780, 480)
        self.setMinimumSize(620, 380)
        self.setModal(True)

        if APP_ICON_PNG.is_file():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        lbl_title = QLabel("Manajemen Proyek Site", self)
        lbl_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        header_layout.addWidget(lbl_title)

        lbl_subtitle = QLabel(
            "Pilih proyek site yang pernah dikerjakan atau buat proyek baru untuk memulai dokumentasi",
            self,
        )
        lbl_subtitle.setStyleSheet(f"""
            font-size: 11px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # 2. Toolbar Tombol Proyek
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)

        self.btn_new = QPushButton("Proyek Site Baru", self)
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.setIcon(get_icon("plus", color="#FFFFFF", size=14))
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new.clicked.connect(self._on_new_project_clicked)
        toolbar_layout.addWidget(self.btn_new)

        self.btn_delete = QPushButton("Hapus Site", self)
        self.btn_delete.setObjectName("DangerButton")
        self.btn_delete.setIcon(get_icon("trash", size=14))
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete_project_clicked)
        toolbar_layout.addWidget(self.btn_delete)

        toolbar_layout.addStretch(1)

        # Search Bar
        lbl_search = QLabel(self)
        lbl_search.setPixmap(render_svg_pixmap("search", size=14))
        toolbar_layout.addWidget(lbl_search)

        self.input_search = QLineEdit(self)
        self.input_search.setPlaceholderText("Cari nama atau ID site...")
        self.input_search.setFixedWidth(220)
        self.input_search.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self.input_search)

        layout.addLayout(toolbar_layout)

        # 3. Table Projects
        self.table_projects = QTableWidget(self)
        self.table_projects.setColumnCount(4)
        self.table_projects.setHorizontalHeaderLabels([
            "Nama / ID Site",
            "Template Digunakan",
            "Foto Terpasang",
            "Tanggal Dibuat",
        ])
        self.table_projects.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_projects.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_projects.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_projects.verticalHeader().setVisible(False)
        self.table_projects.itemSelectionChanged.connect(self._on_project_selection_changed)
        self.table_projects.itemDoubleClicked.connect(self._on_project_double_clicked)

        header = self.table_projects.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table_projects, stretch=1)

        # 4. Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        self.btn_open = QPushButton("Buka Site", self)
        self.btn_open.setObjectName("PrimaryButton")
        self.btn_open.setIcon(get_icon("folder", color="#FFFFFF", size=14))
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self._on_open_project_clicked)
        footer_layout.addWidget(self.btn_open)

        footer_layout.addStretch(1)

        self.btn_close = QPushButton("Tutup", self)
        self.btn_close.setIcon(get_icon("x", size=14))
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_close)

        layout.addLayout(footer_layout)

    def load_projects(self) -> None:
        """Memuat seluruh proyek site dari storage ke tabel."""
        self.loaded_projects = self.storage.list_projects()
        self.table_projects.setRowCount(len(self.loaded_projects))

        for row_idx, proj in enumerate(self.loaded_projects):
            # 0: Nama Site
            item_site = QTableWidgetItem(proj.site_name)
            self.table_projects.setItem(row_idx, 0, item_site)

            # 1: Nama Template
            template_name = proj.template_id
            try:
                tpl = self.storage.load_template(proj.template_id)
                template_name = tpl.name
            except Exception:
                pass
            item_tpl = QTableWidgetItem(template_name)
            self.table_projects.setItem(row_idx, 1, item_tpl)

            # 2: Foto Terisi
            filled_count = len([p for p in proj.photo_assignments.values() if p])
            item_filled = QTableWidgetItem(f"{filled_count} foto")
            item_filled.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_projects.setItem(row_idx, 2, item_filled)

            # 3: Tanggal Dibuat
            date_display = proj.created_at[:10] if proj.created_at else "-"
            item_date = QTableWidgetItem(date_display)
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_projects.setItem(row_idx, 3, item_date)

        self._on_project_selection_changed()

    def _on_project_selection_changed(self) -> None:
        selected_rows = self.table_projects.selectionModel().selectedRows()
        has_sel = len(selected_rows) > 0
        self.btn_open.setEnabled(has_sel)
        self.btn_delete.setEnabled(has_sel)

    def _on_search_changed(self, text: str) -> None:
        """Menyaring baris tabel site berdasarkan query pencarian."""
        query = text.strip().lower()
        for row in range(self.table_projects.rowCount()):
            item_site = self.table_projects.item(row, 0)
            item_tpl = self.table_projects.item(row, 1)
            site_text = item_site.text().lower() if item_site else ""
            tpl_text = item_tpl.text().lower() if item_tpl else ""
            match = (query in site_text) or (query in tpl_text)
            self.table_projects.setRowHidden(row, not match)

    def _get_selected_project(self) -> Optional[ProjectData]:
        selected_rows = self.table_projects.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row_idx = selected_rows[0].row()
        if 0 <= row_idx < len(self.loaded_projects):
            return self.loaded_projects[row_idx]
        return None

    def _on_project_double_clicked(self, item: QTableWidgetItem) -> None:
        self._on_open_project_clicked()

    def _on_new_project_clicked(self) -> None:
        dlg = NewProjectDialog(storage=self.storage, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_projects()
            if dlg.get_created_project():
                self.selected_project = dlg.get_created_project()
                self.accept()

    def _on_open_project_clicked(self) -> None:
        proj = self._get_selected_project()
        if not proj:
            return
        self.selected_project = proj
        self.accept()

    def _on_delete_project_clicked(self) -> None:
        proj = self._get_selected_project()
        if not proj:
            return

        reply = QMessageBox.question(
            self,
            "Konfirmasi Hapus Site",
            f"Apakah Anda yakin ingin menghapus data proyek site '{proj.site_name}'?\n"
            "Tindakan ini akan menghapus riwayat penempatan foto site tersebut.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.storage.delete_project(proj.project_id)
            self.load_projects()

    def get_selected_project(self) -> Optional[ProjectData]:
        """Mengambil proyek site yang dipilih pengguna untuk dibuka."""
        return self.selected_project

