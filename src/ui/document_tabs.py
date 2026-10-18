"""
BTS Document Control - Document Tabs Component
Komponen tab bar multi-dokumen untuk mengelola beberapa template laporan Excel
dalam 1 Proyek Site fisik (misal: Laporan ATP, Laporan CME, Dokumen BAST).
"""

import os
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.core.models import ProjectData, SiteDocument, TemplateConfig
from src.core.storage import StorageManager
from src.ui.icons import get_icon, render_svg_pixmap
from src.ui.styles import ThemeManager


class AddDocumentDialog(QDialog):
    """
    Dialog form visual untuk menambahkan template dokumen baru ke site aktif.
    """

    def __init__(
        self,
        storage: StorageManager,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.storage = storage
        self.selected_template_id: str = ""
        self.document_name: str = ""
        self.available_templates: List[TemplateConfig] = []

        self._init_ui()
        self._load_templates()

    def _init_ui(self) -> None:
        self.setWindowTitle("Tambah Template Dokumen ke Site")
        self.resize(460, 240)
        self.setMinimumSize(400, 220)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        lbl_title = QLabel("Tambah Dokumen Baru", self)
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        header_layout.addWidget(lbl_title)

        lbl_sub = QLabel(
            "Pilih template laporan Excel dan berikan nama dokumen (contoh: Laporan CME)",
            self,
        )
        lbl_sub.setStyleSheet("font-size: 11px; opacity: 0.7;")
        header_layout.addWidget(lbl_sub)
        layout.addLayout(header_layout)

        # Form
        form_frame = QFrame(self)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(0, 4, 0, 4)
        form_layout.setSpacing(10)

        # 1. Pilihan Template
        tpl_label = QLabel("Pilih Template Excel:", form_frame)
        tpl_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        form_layout.addWidget(tpl_label)

        self.combo_template = QComboBox(form_frame)
        self.combo_template.currentIndexChanged.connect(self._on_template_changed)
        form_layout.addWidget(self.combo_template)

        # 2. Nama Dokumen
        name_label = QLabel("Nama Dokumen di Site:", form_frame)
        name_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        form_layout.addWidget(name_label)

        self.edit_name = QLineEdit(form_frame)
        self.edit_name.setPlaceholderText("Contoh: Laporan CME / Dokumen ATP")
        form_layout.addWidget(self.edit_name)

        layout.addWidget(form_frame)

        # Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        footer_layout.addStretch(1)

        self.btn_cancel = QPushButton("Batal", self)
        self.btn_cancel.setIcon(get_icon("x", size=14))
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)

        self.btn_submit = QPushButton("Tambah Dokumen", self)
        self.btn_submit.setObjectName("PrimaryButton")
        self.btn_submit.setIcon(get_icon("plus", color="#FFFFFF", size=14))
        self.btn_submit.clicked.connect(self._on_submit_clicked)
        footer_layout.addWidget(self.btn_submit)

        layout.addLayout(footer_layout)

    def _load_templates(self) -> None:
        self.available_templates = self.storage.list_templates()
        self.combo_template.clear()

        for tpl in self.available_templates:
            field_count = len(tpl.fields)
            self.combo_template.addItem(
                f"{tpl.name} ({field_count} field)",
                userData=tpl.template_id,
            )

        if self.available_templates:
            self.edit_name.setText(self.available_templates[0].name)
            self.btn_submit.setEnabled(True)
        else:
            self.combo_template.addItem("-- Tidak ada template tersimpan --", userData="")
            self.btn_submit.setEnabled(False)

    def _on_template_changed(self, index: int) -> None:
        if 0 <= index < len(self.available_templates):
            tpl = self.available_templates[index]
            # Jika user belum mengetik atau masih sama dengan nama template sebelumnya
            self.edit_name.setText(tpl.name)

    def _on_submit_clicked(self) -> None:
        idx = self.combo_template.currentIndex()
        if idx < 0 or idx >= len(self.available_templates):
            QMessageBox.warning(self, "Peringatan", "Silakan pilih template Excel yang valid.")
            return

        tpl = self.available_templates[idx]
        self.selected_template_id = tpl.template_id
        doc_name = self.edit_name.text().strip() or tpl.name
        self.document_name = doc_name
        self.accept()


class DocumentTabButton(QFrame):
    """
    Tombol Tab Dokumen interaktif dengan ikon, nama dokumen, badge status, dan tombol close.
    """

    clicked = Signal(str)  # doc_id
    close_clicked = Signal(str)  # doc_id
    rename_requested = Signal(str)  # doc_id

    def __init__(
        self,
        doc_id: str,
        title: str,
        badge_text: str = "",
        is_active: bool = False,
        can_close: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.doc_id = doc_id
        self.title = title
        self.badge_text = badge_text
        self.is_active = is_active
        self.can_close = can_close

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._init_ui()
        self._apply_style()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)

        # Ikon Dokumen
        self.lbl_icon = QLabel(self)
        icon_color = "#3B82F6" if self.is_active else "#64748B"
        self.lbl_icon.setPixmap(render_svg_pixmap("file_spreadsheet", color=icon_color, size=14))
        layout.addWidget(self.lbl_icon)

        # Judul Dokumen
        self.lbl_title = QLabel(self.title, self)
        layout.addWidget(self.lbl_title)

        # Badge Kesiapan Foto
        if self.badge_text:
            self.lbl_badge = QLabel(self.badge_text, self)
            layout.addWidget(self.lbl_badge)
        else:
            self.lbl_badge = None

        # Tombol Close / Hapus Tab
        if self.can_close:
            self.btn_close = QPushButton(self)
            self.btn_close.setFixedSize(16, 16)
            self.btn_close.setIcon(get_icon("x", size=10))
            self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btn_close.setToolTip("Hapus dokumen ini dari site")
            self.btn_close.clicked.connect(lambda: self.close_clicked.emit(self.doc_id))
            layout.addWidget(self.btn_close)
        else:
            self.btn_close = None

    def _apply_style(self) -> None:
        p = ThemeManager.instance().get_palette()
        if self.is_active:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {p.SURFACE};
                    border: 1px solid {p.PRIMARY};
                    border-bottom: 2px solid {p.PRIMARY};
                    border-radius: 6px;
                }}
                QLabel {{
                    font-weight: 700;
                    font-size: 12px;
                    color: {p.PRIMARY};
                }}
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: {p.DANGER_BG};
                }}
            """)
            if self.lbl_badge:
                self.lbl_badge.setStyleSheet(f"""
                    background-color: {p.PRIMARY_LIGHT};
                    color: {p.PRIMARY};
                    font-size: 10px;
                    font-weight: 700;
                    padding: 1px 5px;
                    border-radius: 3px;
                """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {p.SURFACE_ALT};
                    border: 1px solid {p.BORDER};
                    border-radius: 6px;
                }}
                QFrame:hover {{
                    background-color: {p.SURFACE};
                    border-color: {p.PRIMARY};
                }}
                QLabel {{
                    font-weight: 500;
                    font-size: 12px;
                    color: {p.TEXT_MUTED};
                }}
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 3px;
                }}
                QPushButton:hover {{
                    background-color: {p.DANGER_BG};
                }}
            """)
            if self.lbl_badge:
                self.lbl_badge.setStyleSheet(f"""
                    background-color: {p.BORDER_LIGHT};
                    color: {p.TEXT_MUTED};
                    font-size: 10px;
                    font-weight: 600;
                    padding: 1px 5px;
                    border-radius: 3px;
                """)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.doc_id)
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def _show_context_menu(self, global_pos) -> None:
        menu = QMenu(self)
        action_rename = menu.addAction(get_icon("edit", size=14), "Ganti Nama Dokumen")
        action_close = None
        if self.can_close:
            action_close = menu.addAction(get_icon("trash", color="#EF4444", size=14), "Hapus Dokumen")

        chosen = menu.exec(global_pos)
        if chosen == action_rename:
            self.rename_requested.emit(self.doc_id)
        elif action_close and chosen == action_close:
            self.close_clicked.emit(self.doc_id)


class DocumentTabBar(QFrame):
    """
    Bilah navigasi tab dokumen untuk Proyek Site aktif.
    Menampilkan tab untuk setiap template dokumen dan tombol untuk menambah dokumen.
    """

    document_selected = Signal(str)  # doc_id
    add_document_requested = Signal()
    remove_document_requested = Signal(str)  # doc_id
    rename_document_requested = Signal(str)  # doc_id

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("DocumentTabBar")
        self.current_project: Optional[ProjectData] = None
        self.tab_buttons: Dict[str, DocumentTabButton] = {}

        self._init_ui()

    def _init_ui(self) -> None:
        self.setFixedHeight(44)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 4, 10, 4)
        main_layout.setSpacing(8)

        # Label Indikator
        self.lbl_section = QLabel("Dokumen:", self)
        self.lbl_section.setStyleSheet("font-size: 11px; font-weight: 700; opacity: 0.7;")
        main_layout.addWidget(self.lbl_section)

        # Scroll area untuk tab jika banyak
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFixedHeight(36)

        self.tab_container = QWidget()
        self.tabs_layout = QHBoxLayout(self.tab_container)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs_layout.setSpacing(6)
        self.tabs_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.scroll_area.setWidget(self.tab_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # Tombol + Tambah Dokumen
        self.btn_add_doc = QPushButton("Tambah Dokumen", self)
        self.btn_add_doc.setIcon(get_icon("plus", color="#2563EB", size=13))
        self.btn_add_doc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_doc.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
                border: 1px dashed #CBD5E1;
                border-radius: 6px;
                background-color: transparent;
            }
            QPushButton:hover {
                border-color: #2563EB;
                background-color: #EFF6FF;
                color: #2563EB;
            }
        """)
        self.btn_add_doc.clicked.connect(self.add_document_requested.emit)
        main_layout.addWidget(self.btn_add_doc)

    def update_documents(
        self,
        project: Optional[ProjectData],
        storage: StorageManager,
    ) -> None:
        """
        Memperbarui daftar tab tombol sesuai `project.documents`.
        """
        self.current_project = project
        self.tab_buttons.clear()

        # Bersihkan widget tab lama
        while self.tabs_layout.count() > 0:
            item = self.tabs_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not project or not project.documents:
            self.setVisible(False)
            return

        self.setVisible(True)
        can_close = len(project.documents) > 1

        for doc in project.documents:
            # Hitung jumlah foto terisi vs total field template
            try:
                tpl = storage.load_template(doc.template_id)
                total_fields = len(tpl.fields)
                doc_title = doc.name or tpl.name
            except Exception:
                total_fields = 0
                doc_title = doc.name or f"Dokumen ({doc.template_id[:6]})"

            filled_count = len(doc.photo_assignments) + len([v for v in doc.text_assignments.values() if v.strip()])
            badge_text = f"{filled_count}/{total_fields}" if total_fields > 0 else ""

            is_active = (doc.doc_id == project.active_doc_id)

            btn = DocumentTabButton(
                doc_id=doc.doc_id,
                title=doc_title,
                badge_text=badge_text,
                is_active=is_active,
                can_close=can_close,
                parent=self.tab_container,
            )
            btn.clicked.connect(self.document_selected.emit)
            btn.close_clicked.connect(self.remove_document_requested.emit)
            btn.rename_requested.connect(self.rename_document_requested.emit)

            self.tab_buttons[doc.doc_id] = btn
            self.tabs_layout.addWidget(btn)

    def set_active_document(self, doc_id: str) -> None:
        """Memperbarui visual tab aktif tanpa rebuild seluruh layout."""
        if not self.current_project:
            return
        self.current_project.active_doc_id = doc_id
        for d_id, btn in self.tab_buttons.items():
            btn.is_active = (d_id == doc_id)
            btn._apply_style()

