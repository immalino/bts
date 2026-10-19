"""
Photo Rename Studio - Antarmuka Visual Template Manager & Editor Field Foto Excel
Modul ini menyediakan dialog PySide6 untuk mengelola konfigurasi template laporan Excel,
auto-load nama sheet dari file .xlsx, editor tabel field foto, dan integrasi dengan StorageManager.
"""

from datetime import datetime
import json
import os
from pathlib import Path
from typing import List, Optional
import uuid

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.config import APP_ICON_PNG, ThemeColors
from src.core.models import PhotoFieldConfig, TemplateConfig
from src.core.storage import StorageManager
from src.ui.icons import get_icon, render_svg_pixmap
from src.utils.excel_utils import get_sheet_names_from_excel, is_valid_cell_coordinate


class FocusSelectingLineEdit(QLineEdit):
    """QLineEdit yang otomatis memilih baris tabel tempat widget berada saat difokuskan."""

    def __init__(
        self, row: int, table: QTableWidget, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.row = row
        self.table = table

    def focusInEvent(self, event) -> None:
        self.table.selectRow(self.row)
        super().focusInEvent(event)


class FocusSelectingComboBox(QComboBox):
    """QComboBox yang otomatis memilih baris tabel tempat widget berada saat difokuskan."""

    def __init__(
        self, row: int, table: QTableWidget, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.row = row
        self.table = table

    def focusInEvent(self, event) -> None:
        self.table.selectRow(self.row)
        super().focusInEvent(event)


class FieldEditDialog(QDialog):
    """
    Dialog form visual untuk menambah atau mengedit konfigurasi PhotoFieldConfig.
    
    Field yang dikonfigurasi:
    - Label Field (contoh: "Foto Antenna Sector 1")
    - Sheet Target (pilihan dropdown combobox dari daftar sheet file .xlsx)
    - Sel Anchor (contoh: "B5")
    - Mode Ukuran: "Auto-Fit ke Ukuran Sel (Rekomendasi)" atau "Ukuran Kustom (Lebar x Tinggi)"
    - Padding: Ruang kosong di setiap sisi dalam piksel (default: 2 px)
    """

    def __init__(
        self,
        field_config: Optional[PhotoFieldConfig] = None,
        available_sheets: Optional[List[str]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.field_config = field_config
        self.available_sheets = available_sheets or []
        self.result_field_config: Optional[PhotoFieldConfig] = None

        self._init_ui()
        self._load_initial_data()

    def _init_ui(self) -> None:
        title = "Edit Field" if self.field_config else "Tambah Field Baru"
        self.setWindowTitle(title)
        self.resize(540, 580)
        self.setMinimumSize(480, 520)
        self.setModal(True)

        if APP_ICON_PNG.is_file():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        lbl_title = QLabel(title, self)
        lbl_title.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        header_layout.addWidget(lbl_title)

        lbl_subtitle = QLabel("Tentukan tipe field, penempatan pada sheet Excel, dan aturannya", self)
        lbl_subtitle.setStyleSheet(f"""
            font-size: 11px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # Form Group
        form_group = QGroupBox("Informasi Field", self)
        form_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 12px;
                font-weight: 600;
                color: {ThemeColors.TEXT};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 6px;
                margin-top: 10px;
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

        # 0. Tipe Field (Foto vs Teks)
        lbl_type = QLabel("Tipe Field:", form_group)
        lbl_type.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        form_layout.addWidget(lbl_type)

        self.btn_group_type = QButtonGroup(self)
        self.radio_type_photo = QRadioButton("Field Foto (Gambar / Kamera)", form_group)
        self.radio_type_photo.setChecked(True)
        self.radio_type_text = QRadioButton("Field Teks (Nilai String / Keterangan)", form_group)
        self.btn_group_type.addButton(self.radio_type_photo)
        self.btn_group_type.addButton(self.radio_type_text)

        type_btn_layout = QHBoxLayout()
        type_btn_layout.setSpacing(14)
        type_btn_layout.addWidget(self.radio_type_photo)
        type_btn_layout.addWidget(self.radio_type_text)
        type_btn_layout.addStretch(1)
        form_layout.addLayout(type_btn_layout)

        # 1. Label Field
        self.lbl_field_label = QLabel("Label Field Foto:", form_group)
        self.lbl_field_label.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        form_layout.addWidget(self.lbl_field_label)

        self.edit_label = QLineEdit(form_group)
        self.edit_label.setFixedHeight(34)
        self.edit_label.setPlaceholderText("Contoh: Foto Antenna Sector 1")
        form_layout.addWidget(self.edit_label)

        # 2. Sheet Target & Sel Anchor dalam 1 Baris
        coord_layout = QHBoxLayout()
        coord_layout.setSpacing(10)

        sheet_col = QVBoxLayout()
        sheet_col.setSpacing(4)
        lbl_sheet = QLabel("Sheet Target:", form_group)
        lbl_sheet.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        sheet_col.addWidget(lbl_sheet)

        self.combo_sheet = QComboBox(form_group)
        self.combo_sheet.setEditable(True)
        self.combo_sheet.setFixedHeight(34)
        self.combo_sheet.setPlaceholderText("Pilih atau ketik sheet...")
        if self.available_sheets:
            self.combo_sheet.addItems(self.available_sheets)
        sheet_col.addWidget(self.combo_sheet)
        coord_layout.addLayout(sheet_col, stretch=2)

        cell_col = QVBoxLayout()
        cell_col.setSpacing(4)
        lbl_cell = QLabel("Sel Anchor:", form_group)
        lbl_cell.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        cell_col.addWidget(lbl_cell)

        self.edit_cell = QLineEdit(form_group)
        self.edit_cell.setFixedHeight(34)
        self.edit_cell.setPlaceholderText("Contoh: B5")
        cell_col.addWidget(self.edit_cell)
        coord_layout.addLayout(cell_col, stretch=1)

        form_layout.addLayout(coord_layout)

        # 3. Kontainer Opsi Khusus Teks
        self.text_options_container = QWidget(form_group)
        text_opt_layout = QVBoxLayout(self.text_options_container)
        text_opt_layout.setContentsMargins(0, 4, 0, 4)
        text_opt_layout.setSpacing(4)

        lbl_def_text = QLabel("Teks Default (Opsional):", self.text_options_container)
        lbl_def_text.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        text_opt_layout.addWidget(lbl_def_text)

        self.edit_default_text = QLineEdit(self.text_options_container)
        self.edit_default_text.setFixedHeight(34)
        self.edit_default_text.setPlaceholderText("Contoh: Menara BTS 72M atau biarkan kosong...")
        text_opt_layout.addWidget(self.edit_default_text)

        self.text_options_container.setVisible(False)
        form_layout.addWidget(self.text_options_container)

        # 4. Kontainer Opsi Khusus Foto (Ukuran, Padding, Alignment)
        self.photo_options_container = QWidget(form_group)
        photo_opt_layout = QVBoxLayout(self.photo_options_container)
        photo_opt_layout.setContentsMargins(0, 4, 0, 4)
        photo_opt_layout.setSpacing(10)

        lbl_mode = QLabel("Mode Ukuran Gambar:", self.photo_options_container)
        lbl_mode.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        photo_opt_layout.addWidget(lbl_mode)

        self.btn_group_mode = QButtonGroup(self)
        self.radio_fit = QRadioButton("Auto-Fit ke Ukuran Sel (Rekomendasi)", self.photo_options_container)
        self.radio_fit.setChecked(True)
        self.radio_custom = QRadioButton("Ukuran Kustom (Lebar x Tinggi)", self.photo_options_container)
        self.btn_group_mode.addButton(self.radio_fit)
        self.btn_group_mode.addButton(self.radio_custom)

        photo_opt_layout.addWidget(self.radio_fit)
        photo_opt_layout.addWidget(self.radio_custom)

        # Dimensi Kustom
        custom_size_layout = QHBoxLayout()
        custom_size_layout.setSpacing(10)

        custom_w_layout = QVBoxLayout()
        custom_w_layout.setSpacing(2)
        lbl_w = QLabel("Lebar (px):", self.photo_options_container)
        lbl_w.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        custom_w_layout.addWidget(lbl_w)
        self.spin_width = QSpinBox(self.photo_options_container)
        self.spin_width.setFixedHeight(34)
        self.spin_width.setRange(10, 5000)
        self.spin_width.setValue(400)
        self.spin_width.setEnabled(False)
        custom_w_layout.addWidget(self.spin_width)
        custom_size_layout.addLayout(custom_w_layout)

        custom_h_layout = QVBoxLayout()
        custom_h_layout.setSpacing(2)
        lbl_h = QLabel("Tinggi (px):", self.photo_options_container)
        lbl_h.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        custom_h_layout.addWidget(lbl_h)
        self.spin_height = QSpinBox(self.photo_options_container)
        self.spin_height.setFixedHeight(34)
        self.spin_height.setRange(10, 5000)
        self.spin_height.setValue(300)
        self.spin_height.setEnabled(False)
        custom_h_layout.addWidget(self.spin_height)
        custom_size_layout.addLayout(custom_h_layout)

        # Margin / Padding
        padding_layout = QVBoxLayout()
        padding_layout.setSpacing(2)
        lbl_p = QLabel("Padding (px):", self.photo_options_container)
        lbl_p.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        padding_layout.addWidget(lbl_p)
        self.spin_padding = QSpinBox(self.photo_options_container)
        self.spin_padding.setFixedHeight(34)
        self.spin_padding.setRange(0, 100)
        self.spin_padding.setValue(2)
        padding_layout.addWidget(self.spin_padding)
        custom_size_layout.addLayout(padding_layout)

        photo_opt_layout.addLayout(custom_size_layout)

        # Perataan Posisi (Alignment)
        lbl_align = QLabel("Perataan Posisi Foto:", self.photo_options_container)
        lbl_align.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px; margin-top: 4px;")
        photo_opt_layout.addWidget(lbl_align)

        self.btn_group_align = QButtonGroup(self)
        self.radio_align_center = QRadioButton("Tengah / Center (Rekomendasi)", self.photo_options_container)
        self.radio_align_center.setChecked(True)
        self.radio_align_topleft = QRadioButton("Kiri-Atas / Top-Left", self.photo_options_container)
        self.btn_group_align.addButton(self.radio_align_center)
        self.btn_group_align.addButton(self.radio_align_topleft)

        align_btn_layout = QHBoxLayout()
        align_btn_layout.setSpacing(14)
        align_btn_layout.addWidget(self.radio_align_center)
        align_btn_layout.addWidget(self.radio_align_topleft)
        align_btn_layout.addStretch(1)
        photo_opt_layout.addLayout(align_btn_layout)

        form_layout.addWidget(self.photo_options_container)
        layout.addWidget(form_group)

        # Connect radio signals
        self.radio_custom.toggled.connect(self._on_mode_toggled)
        self.radio_type_photo.toggled.connect(self._on_type_toggled)

        layout.addStretch(1)

        # Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        footer_layout.addStretch(1)

        self.btn_cancel = QPushButton("Batal", self)
        self.btn_cancel.setIcon(get_icon("x", size=14))
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Simpan", self)
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.setIcon(get_icon("check", color="#FFFFFF", size=14))
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setFixedHeight(36)
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._on_save_clicked)
        footer_layout.addWidget(self.btn_save)

        layout.addLayout(footer_layout)

    def _on_type_toggled(self, checked: bool) -> None:
        is_photo = self.radio_type_photo.isChecked()
        self.photo_options_container.setVisible(is_photo)
        self.text_options_container.setVisible(not is_photo)
        if is_photo:
            self.lbl_field_label.setText("Label Field Foto:")
            self.edit_label.setPlaceholderText("Contoh: Foto Antenna Sector 1")
        else:
            self.lbl_field_label.setText("Label Field Teks:")
            self.edit_label.setPlaceholderText("Contoh: Nama Site / Ketinggian Tower")

    def _on_mode_toggled(self, checked: bool) -> None:
        self.spin_width.setEnabled(checked)
        self.spin_height.setEnabled(checked)

    def _load_initial_data(self) -> None:
        if not self.field_config:
            return

        self.edit_label.setText(self.field_config.label)
        # Cari sheet di combo
        sheet_idx = self.combo_sheet.findText(self.field_config.sheet_name)
        if sheet_idx >= 0:
            self.combo_sheet.setCurrentIndex(sheet_idx)
        else:
            self.combo_sheet.setCurrentText(self.field_config.sheet_name)

        self.edit_cell.setText(self.field_config.cell_anchor)

        fld_type = getattr(self.field_config, "field_type", "photo")
        if fld_type == "text":
            self.radio_type_text.setChecked(True)
            self.edit_default_text.setText(getattr(self.field_config, "default_text", ""))
            self._on_type_toggled(False)
        else:
            self.radio_type_photo.setChecked(True)
            self._on_type_toggled(True)

        if self.field_config.sizing_mode == "custom":
            self.radio_custom.setChecked(True)
            self.spin_width.setValue(max(10, self.field_config.custom_width))
            self.spin_height.setValue(max(10, self.field_config.custom_height))
        else:
            self.radio_fit.setChecked(True)

        self.spin_padding.setValue(max(0, self.field_config.padding))

        # Alignment
        alignment = getattr(self.field_config, "alignment", "center")
        if alignment == "top-left":
            self.radio_align_topleft.setChecked(True)
        else:
            self.radio_align_center.setChecked(True)

    def _on_save_clicked(self) -> None:
        label = self.edit_label.text().strip()
        sheet_name = self.combo_sheet.currentText().strip()
        cell_anchor = self.edit_cell.text().strip().upper()

        if not label:
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                "Label field foto tidak boleh kosong." if self.radio_type_photo.isChecked() else "Label field teks tidak boleh kosong.",
            )
            self.edit_label.setFocus()
            return

        if not sheet_name:
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                "Nama sheet target tidak boleh kosong.",
            )
            self.combo_sheet.setFocus()
            return

        if not is_valid_cell_coordinate(cell_anchor):
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                f"Koordinat sel anchor tidak valid: '{cell_anchor}'.\n"
                "Format yang benar contohnya: B5, C10, AA1.",
            )
            self.edit_cell.setFocus()
            return

        is_text = self.radio_type_text.isChecked()
        field_type = "text" if is_text else "photo"
        default_text = self.edit_default_text.text().strip() if is_text else ""

        if is_text:
            sizing_mode = "fit_to_cell"
            custom_width = 0
            custom_height = 0
            padding = 0
            alignment = "center"
        else:
            sizing_mode = "custom" if self.radio_custom.isChecked() else "fit_to_cell"
            custom_width = self.spin_width.value() if sizing_mode == "custom" else 0
            custom_height = self.spin_height.value() if sizing_mode == "custom" else 0
            padding = self.spin_padding.value()
            alignment = "top-left" if self.radio_align_topleft.isChecked() else "center"

        field_id = (
            self.field_config.field_id
            if self.field_config
            else f"fld_{uuid.uuid4().hex[:8]}"
        )

        self.result_field_config = PhotoFieldConfig(
            field_id=field_id,
            label=label,
            sheet_name=sheet_name,
            cell_anchor=cell_anchor,
            field_type=field_type,
            sizing_mode=sizing_mode,
            custom_width=custom_width,
            custom_height=custom_height,
            padding=padding,
            alignment=alignment,
            default_text=default_text,
        )
        self.accept()

    def get_field_config(self) -> Optional[PhotoFieldConfig]:
        """Mengambil PhotoFieldConfig hasil input dialog."""
        return self.result_field_config


class TemplateEditorDialog(QDialog):
    """
    Dialog form visual untuk membuat atau mengedit konfigurasi TemplateConfig.
    
    Fitur:
    - Input Nama Template
    - Pemilihan file template .xlsx dengan auto-load nama sheet
    - Tabel visual field foto dengan aksi Tambah, Edit, Hapus, Naik, Turun
    - Validasi form (nama kosong, file tidak valid, koordinat sel tidak valid)
    - Integrasi penyimpanan ke StorageManager
    """

    def __init__(
        self,
        template: Optional[TemplateConfig] = None,
        storage: Optional[StorageManager] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.template = template
        self.storage = storage
        self.fields: List[PhotoFieldConfig] = []
        self.available_sheets: List[str] = []
        self.saved_template: Optional[TemplateConfig] = None

        if self.template:
            # Salin fields agar tidak memodifikasi objek asal sebelum disimpan
            self.fields = [
                PhotoFieldConfig.from_dict(f.to_dict()) for f in self.template.fields
            ]

        self._init_ui()
        self._load_initial_data()

    def _init_ui(self) -> None:
        title = "Edit Template Laporan" if self.template else "Buat Template Laporan Baru"
        self.setWindowTitle(title)
        self.resize(960, 680)
        self.setMinimumSize(820, 560)
        self.setModal(True)

        if APP_ICON_PNG.is_file():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        lbl_title = QLabel(title, self)
        lbl_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        header_layout.addWidget(lbl_title)

        lbl_subtitle = QLabel(
            "Konfigurasikan template Excel induk, penamaan file hasil, dan daftar field foto/teks",
            self,
        )
        lbl_subtitle.setStyleSheet(f"""
            font-size: 11px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # 2. Template Metadata Card
        meta_card = QFrame(self)
        meta_card.setStyleSheet(f"""
            QFrame {{
                background-color: {ThemeColors.SURFACE};
                border: 1px solid {ThemeColors.BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        meta_layout = QVBoxLayout(meta_card)
        meta_layout.setSpacing(10)
        meta_layout.setContentsMargins(10, 10, 10, 10)

        # Input Nama Template
        name_layout = QVBoxLayout()
        name_layout.setSpacing(4)
        lbl_name = QLabel("Nama Template:", meta_card)
        lbl_name.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        name_layout.addWidget(lbl_name)

        self.edit_name = QLineEdit(meta_card)
        self.edit_name.setFixedHeight(34)
        self.edit_name.setPlaceholderText("Contoh: Template Telkomsel BTS 4G / 5G")
        name_layout.addWidget(self.edit_name)
        meta_layout.addLayout(name_layout)

        # Input File Template Excel .xlsx
        file_layout = QVBoxLayout()
        file_layout.setSpacing(4)
        lbl_file = QLabel("File Template Excel (.xlsx):", meta_card)
        lbl_file.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        file_layout.addWidget(lbl_file)

        file_browse_layout = QHBoxLayout()
        file_browse_layout.setSpacing(8)

        self.edit_file_path = QLineEdit(meta_card)
        self.edit_file_path.setFixedHeight(34)
        self.edit_file_path.setPlaceholderText("Pilih atau masukkan path file .xlsx template...")
        self.edit_file_path.textChanged.connect(self._on_file_path_changed)
        file_browse_layout.addWidget(self.edit_file_path, stretch=1)

        self.btn_browse = QPushButton("Pilih File .xlsx", meta_card)
        self.btn_browse.setIcon(get_icon("folder", size=14))
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.setFixedHeight(34)
        self.btn_browse.clicked.connect(self._on_browse_file_clicked)
        file_browse_layout.addWidget(self.btn_browse)

        file_layout.addLayout(file_browse_layout)

        # Status sheet auto-load
        self.lbl_sheet_status = QLabel("Sheet terdeteksi: (Belum ada file dipilih)", meta_card)
        self.lbl_sheet_status.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        self.lbl_sheet_status.setWordWrap(True)
        file_layout.addWidget(self.lbl_sheet_status)
        meta_layout.addLayout(file_layout)

        # Input Format Pola Nama File Output (Opsional)
        pattern_layout = QVBoxLayout()
        pattern_layout.setSpacing(4)
        lbl_pattern = QLabel("Format Nama File Output (Opsional):", meta_card)
        lbl_pattern.setStyleSheet(f"font-weight: 600; color: {ThemeColors.TEXT}; font-size: 12px;")
        pattern_layout.addWidget(lbl_pattern)

        self.edit_output_filename_pattern = QLineEdit(meta_card)
        self.edit_output_filename_pattern.setFixedHeight(34)
        self.edit_output_filename_pattern.setPlaceholderText("Contoh: Laporan_{site_name}_{date} atau {template_name}_{site_name}_{Nama Site}")
        pattern_layout.addWidget(self.edit_output_filename_pattern)

        lbl_pattern_hint = QLabel(
            "Variabel tersedia: {site_name}, {template_name}, {date}, {datetime}, serta label field teks (contoh: {Nama Site})",
            meta_card,
        )
        lbl_pattern_hint.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        pattern_layout.addWidget(lbl_pattern_hint)
        meta_layout.addLayout(pattern_layout)

        layout.addWidget(meta_card)

        # 3. Fields Section
        fields_section_layout = QVBoxLayout()
        fields_section_layout.setSpacing(6)

        # Baris Header: Judul, Indikator Jumlah & Aksi JSON
        fields_header_top = QHBoxLayout()
        lbl_fields_title = QLabel("Daftar Field", self)
        lbl_fields_title.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        fields_header_top.addWidget(lbl_fields_title)

        self.lbl_fields_count = QLabel("(0 field)", self)
        self.lbl_fields_count.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
        fields_header_top.addWidget(self.lbl_fields_count)

        fields_header_top.addStretch(1)

        self.btn_sample_json = QPushButton("Contoh JSON", self)
        self.btn_sample_json.setIcon(get_icon("file_text", size=14))
        self.btn_sample_json.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sample_json.setFixedHeight(28)
        self.btn_sample_json.setToolTip("Unduh berkas contoh format JSON untuk konfigurasi field")
        self.btn_sample_json.clicked.connect(self._on_sample_json_clicked)
        fields_header_top.addWidget(self.btn_sample_json)

        self.btn_import_json = QPushButton("Import JSON", self)
        self.btn_import_json.setIcon(get_icon("upload_cloud", size=14))
        self.btn_import_json.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import_json.setFixedHeight(28)
        self.btn_import_json.setToolTip("Impor konfigurasi field dari berkas JSON")
        self.btn_import_json.clicked.connect(self._on_import_json_clicked)
        fields_header_top.addWidget(self.btn_import_json)

        self.btn_export_json = QPushButton("Export JSON", self)
        self.btn_export_json.setIcon(get_icon("download", size=14))
        self.btn_export_json.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_json.setFixedHeight(28)
        self.btn_export_json.setToolTip("Ekspor daftar field saat ini ke berkas JSON")
        self.btn_export_json.clicked.connect(self._on_export_json_clicked)
        fields_header_top.addWidget(self.btn_export_json)

        fields_section_layout.addLayout(fields_header_top)

        # Baris Toolbar: Tombol Operasi Field & Navigasi Urutan Lengkap
        fields_toolbar = QHBoxLayout()
        fields_toolbar.setSpacing(6)

        self.btn_add_field = QPushButton("Tambah Field", self)
        self.btn_add_field.setIcon(get_icon("plus", color="#FFFFFF", size=14))
        self.btn_add_field.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_field.setFixedHeight(34)
        self.btn_add_field.clicked.connect(self._on_add_field_clicked)
        fields_toolbar.addWidget(self.btn_add_field)

        self.btn_duplicate_field = QPushButton("Duplikat", self)
        self.btn_duplicate_field.setIcon(get_icon("copy", size=14))
        self.btn_duplicate_field.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_duplicate_field.setFixedHeight(34)
        self.btn_duplicate_field.setToolTip("Duplikat field yang dipilih")
        self.btn_duplicate_field.setEnabled(False)
        self.btn_duplicate_field.clicked.connect(self._on_duplicate_field_clicked)
        fields_toolbar.addWidget(self.btn_duplicate_field)

        self.btn_edit_field = QPushButton("Edit Detail", self)
        self.btn_edit_field.setIcon(get_icon("edit", size=14))
        self.btn_edit_field.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit_field.setFixedHeight(34)
        self.btn_edit_field.setToolTip("Buka dialog untuk mengubah pengaturan ukuran/padding")
        self.btn_edit_field.setEnabled(False)
        self.btn_edit_field.clicked.connect(self._on_edit_field_clicked)
        fields_toolbar.addWidget(self.btn_edit_field)

        self.btn_delete_field = QPushButton("Hapus", self)
        self.btn_delete_field.setIcon(get_icon("trash", size=14))
        self.btn_delete_field.setObjectName("DangerButton")
        self.btn_delete_field.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete_field.setFixedHeight(34)
        self.btn_delete_field.setEnabled(False)
        self.btn_delete_field.clicked.connect(self._on_delete_field_clicked)
        fields_toolbar.addWidget(self.btn_delete_field)

        fields_toolbar.addSpacing(10)

        # Navigasi Urutan: Paling Atas, Naik 1 Tingkat, Turun 1 Tingkat, Paling Bawah
        self.btn_move_top = QPushButton("Paling Atas", self)
        self.btn_move_top.setIcon(get_icon("chevrons_up", size=14))
        self.btn_move_top.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_move_top.setFixedHeight(34)
        self.btn_move_top.setToolTip("Pindahkan field ke baris paling pertama")
        self.btn_move_top.setEnabled(False)
        self.btn_move_top.clicked.connect(self._on_move_top_clicked)
        fields_toolbar.addWidget(self.btn_move_top)

        self.btn_move_up = QPushButton("Naik", self)
        self.btn_move_up.setIcon(get_icon("arrow_up", size=14))
        self.btn_move_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_move_up.setFixedHeight(34)
        self.btn_move_up.setToolTip("Geser field naik 1 tingkat")
        self.btn_move_up.setEnabled(False)
        self.btn_move_up.clicked.connect(self._on_move_up_clicked)
        fields_toolbar.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("Turun", self)
        self.btn_move_down.setIcon(get_icon("arrow_down", size=14))
        self.btn_move_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_move_down.setFixedHeight(34)
        self.btn_move_down.setToolTip("Geser field turun 1 tingkat")
        self.btn_move_down.setEnabled(False)
        self.btn_move_down.clicked.connect(self._on_move_down_clicked)
        fields_toolbar.addWidget(self.btn_move_down)

        self.btn_move_bottom = QPushButton("Paling Bawah", self)
        self.btn_move_bottom.setIcon(get_icon("chevrons_down", size=14))
        self.btn_move_bottom.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_move_bottom.setFixedHeight(34)
        self.btn_move_bottom.setToolTip("Pindahkan field ke baris paling terakhir")
        self.btn_move_bottom.setEnabled(False)
        self.btn_move_bottom.clicked.connect(self._on_move_bottom_clicked)
        fields_toolbar.addWidget(self.btn_move_bottom)

        fields_toolbar.addStretch(1)

        fields_section_layout.addLayout(fields_toolbar)
        layout.addLayout(fields_section_layout)

        # Table Fields
        self.table_fields = QTableWidget(self)
        self.table_fields.setColumnCount(8)
        self.table_fields.setHorizontalHeaderLabels([
            "No",
            "Label Field",
            "Tipe",
            "Sheet Target",
            "Sel Anchor",
            "Mode Ukuran / Info",
            "Padding",
            "Posisi",
        ])
        self.table_fields.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_fields.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_fields.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_fields.verticalHeader().setVisible(False)
        self.table_fields.verticalHeader().setDefaultSectionSize(44)
        self.table_fields.verticalHeader().setMinimumSectionSize(40)
        self.table_fields.itemSelectionChanged.connect(self._on_field_selection_changed)
        self.table_fields.itemDoubleClicked.connect(self._on_field_table_double_clicked)

        header = self.table_fields.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table_fields, stretch=1)

        # 4. Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)
        footer_layout.addStretch(1)

        self.btn_cancel = QPushButton("Batal", self)
        self.btn_cancel.setIcon(get_icon("x", size=16))
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setFixedHeight(36)
        self.btn_cancel.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Simpan Template", self)
        self.btn_save.setObjectName("PrimaryButton")
        self.btn_save.setIcon(get_icon("check", color="#ffffff", size=16))
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setFixedHeight(36)
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._on_save_template_clicked)
        footer_layout.addWidget(self.btn_save)

        layout.addLayout(footer_layout)

    def _load_initial_data(self) -> None:
        if self.template:
            self.edit_name.setText(self.template.name)
            self.edit_file_path.blockSignals(True)
            self.edit_file_path.setText(self.template.template_file_path)
            self.edit_file_path.blockSignals(False)
            self.edit_output_filename_pattern.setText(
                getattr(self.template, "output_filename_pattern", "")
            )
            self.load_sheet_names(self.template.template_file_path)

        self._refresh_fields_table()

    def set_template_file(self, file_path: str) -> None:
        """Set file path template dan muat daftar sheet."""
        self.edit_file_path.setText(file_path)
        self.load_sheet_names(file_path)
        self._refresh_fields_table()

    def load_sheet_names(self, file_path: str) -> List[str]:
        """
        Membaca nama-nama sheet dari file Excel secara otomatis.
        
        Args:
            file_path: Lokasi file .xlsx.
            
        Returns:
            List[str]: Daftar nama sheet.
        """
        clean_path = file_path.strip()
        if not clean_path:
            self.available_sheets = []
            self.lbl_sheet_status.setText("Sheet terdeteksi: (Belum ada file dipilih)")
            self.lbl_sheet_status.setStyleSheet(f"font-size: 11px; color: {ThemeColors.TEXT_MUTED};")
            return []

        try:
            sheets = get_sheet_names_from_excel(clean_path)
            self.available_sheets = sheets
            sheets_text = ", ".join(sheets)
            self.lbl_sheet_status.setText(f"Sheet terdeteksi ({len(sheets)}): {sheets_text}")
            self.lbl_sheet_status.setStyleSheet(f"font-size: 11px; color: {ThemeColors.SUCCESS};")
            return sheets
        except Exception as err:
            self.available_sheets = []
            self.lbl_sheet_status.setText(f"Gagal membaca sheet: {err}")
            self.lbl_sheet_status.setStyleSheet(f"font-size: 11px; color: {ThemeColors.ERROR};")
            return []

    def _on_file_path_changed(self, text: str) -> None:
        if Path(text.strip()).is_file():
            self.load_sheet_names(text.strip())
            self._refresh_fields_table()

    def _on_browse_file_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Pilih File Template Excel",
            "",
            "Excel Spreadsheet (*.xlsx *.xlsm);;Semua Berkas (*.*)",
        )
        if file_path:
            self.set_template_file(file_path)

    def _refresh_fields_table(self) -> None:
        self._is_populating_table = True

        # Bersihkan seluruh cell widget lama agar tidak menjadi orphan/ghost di viewport
        for r in range(self.table_fields.rowCount()):
            for c in range(self.table_fields.columnCount()):
                w = self.table_fields.cellWidget(r, c)
                if w:
                    self.table_fields.removeCellWidget(r, c)
                    w.setParent(None)
                    w.deleteLater()

        for ch in list(self.table_fields.viewport().children()):
            if isinstance(ch, (FocusSelectingLineEdit, FocusSelectingComboBox)):
                ch.setParent(None)
                ch.deleteLater()

        self.table_fields.setRowCount(len(self.fields))
        if hasattr(self, "lbl_fields_count"):
            self.lbl_fields_count.setText(f"({len(self.fields)} field)")

        for row_idx, fld in enumerate(self.fields):
            # 0: No
            item_no = QTableWidgetItem(str(row_idx + 1))
            item_no.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_no.setFlags(item_no.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_fields.setItem(row_idx, 0, item_no)

            # 1: Label (In-place editable via FocusSelectingLineEdit)
            item_label = QTableWidgetItem(fld.label)
            item_label.setForeground(QColor(0, 0, 0, 0))
            self.table_fields.setItem(row_idx, 1, item_label)

            edit_label = FocusSelectingLineEdit(row_idx, self.table_fields)
            edit_label.setText(fld.label)
            edit_label.setPlaceholderText("Label field...")
            edit_label.setFixedHeight(32)
            edit_label.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-size: 12px;
                    background-color: {ThemeColors.SURFACE};
                    color: {ThemeColors.TEXT};
                }}
                QLineEdit:hover {{
                    border-color: {ThemeColors.BORDER_FOCUS};
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {ThemeColors.PRIMARY};
                    background-color: {ThemeColors.SURFACE};
                }}
            """)
            edit_label.textChanged.connect(
                lambda text, r=row_idx: self._on_inline_label_changed(r, text)
            )
            self.table_fields.setCellWidget(row_idx, 1, edit_label)

            # 2: Tipe (Foto / Teks)
            fld_type = getattr(fld, "field_type", "photo")
            type_str = "Teks" if fld_type == "text" else "Foto"
            item_type = QTableWidgetItem(type_str)
            item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_type.setFlags(item_type.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_fields.setItem(row_idx, 2, item_type)

            # 3: Sheet Target (In-place editable via FocusSelectingComboBox)
            item_sheet = QTableWidgetItem(fld.sheet_name or "")
            item_sheet.setForeground(QColor(0, 0, 0, 0))
            self.table_fields.setItem(row_idx, 3, item_sheet)

            combo_sheet = FocusSelectingComboBox(row_idx, self.table_fields)
            combo_sheet.setEditable(True)
            combo_sheet.setFixedHeight(32)
            combo_sheet.setStyleSheet(f"""
                QComboBox {{
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-size: 12px;
                    background-color: {ThemeColors.SURFACE};
                    color: {ThemeColors.TEXT};
                }}
                QComboBox:hover {{
                    border-color: {ThemeColors.BORDER_FOCUS};
                }}
                QComboBox:focus {{
                    border: 1.5px solid {ThemeColors.PRIMARY};
                }}
            """)
            if self.available_sheets:
                combo_sheet.addItems(self.available_sheets)
            if fld.sheet_name:
                combo_sheet.setCurrentText(fld.sheet_name)
            combo_sheet.currentTextChanged.connect(
                lambda text, r=row_idx: self._on_inline_sheet_changed(r, text)
            )
            self.table_fields.setCellWidget(row_idx, 3, combo_sheet)

            # 4: Sel Anchor (In-place editable via FocusSelectingLineEdit)
            item_cell = QTableWidgetItem(fld.cell_anchor or "")
            item_cell.setForeground(QColor(0, 0, 0, 0))
            self.table_fields.setItem(row_idx, 4, item_cell)

            edit_cell = FocusSelectingLineEdit(row_idx, self.table_fields)
            edit_cell.setText(fld.cell_anchor)
            edit_cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit_cell.setPlaceholderText("B5")
            edit_cell.setFixedHeight(32)
            edit_cell.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-size: 12px;
                    font-weight: 600;
                    background-color: {ThemeColors.SURFACE};
                    color: {ThemeColors.TEXT};
                }}
                QLineEdit:hover {{
                    border-color: {ThemeColors.BORDER_FOCUS};
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {ThemeColors.PRIMARY};
                }}
            """)
            edit_cell.textChanged.connect(
                lambda text, r=row_idx, w=edit_cell: self._on_inline_cell_changed(r, text, w)
            )
            self.table_fields.setCellWidget(row_idx, 4, edit_cell)

            # 5: Mode Ukuran / Info
            if fld_type == "text":
                def_text = getattr(fld, "default_text", "")
                mode_str = f"Teks (Default: {def_text})" if def_text else "Teks Sel"
            else:
                if fld.sizing_mode == "custom":
                    mode_str = f"Kustom ({fld.custom_width}x{fld.custom_height})"
                else:
                    mode_str = "Auto-Fit Sel"
            item_mode = QTableWidgetItem(mode_str)
            item_mode.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_mode.setFlags(item_mode.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_fields.setItem(row_idx, 5, item_mode)

            # 6: Padding
            pad_str = f"{fld.padding} px" if fld_type != "text" else "-"
            item_pad = QTableWidgetItem(pad_str)
            item_pad.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_pad.setFlags(item_pad.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_fields.setItem(row_idx, 6, item_pad)

            # 7: Posisi
            if fld_type != "text":
                align_val = getattr(fld, "alignment", "center")
                align_str = "Kiri-Atas" if align_val == "top-left" else "Tengah"
            else:
                align_str = "-"
            item_align = QTableWidgetItem(align_str)
            item_align.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_align.setFlags(item_align.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table_fields.setItem(row_idx, 7, item_align)

        self._is_populating_table = False
        self._on_field_selection_changed()

    def _on_inline_label_changed(self, row_idx: int, text: str) -> None:
        if getattr(self, "_is_populating_table", False):
            return
        if 0 <= row_idx < len(self.fields):
            self.fields[row_idx].label = text
            it = self.table_fields.item(row_idx, 1)
            if it:
                it.setText(text)

    def _on_inline_sheet_changed(self, row_idx: int, text: str) -> None:
        if getattr(self, "_is_populating_table", False):
            return
        if 0 <= row_idx < len(self.fields):
            self.fields[row_idx].sheet_name = text.strip()
            it = self.table_fields.item(row_idx, 3)
            if it:
                it.setText(text.strip())

    def _on_inline_cell_changed(self, row_idx: int, text: str, widget: QLineEdit) -> None:
        if getattr(self, "_is_populating_table", False):
            return
        clean_text = text.strip().upper()
        if 0 <= row_idx < len(self.fields):
            self.fields[row_idx].cell_anchor = clean_text
            it = self.table_fields.item(row_idx, 4)
            if it:
                it.setText(clean_text)

        # Visual validation
        if not clean_text or is_valid_cell_coordinate(clean_text):
            widget.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {ThemeColors.BORDER};
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-size: 12px;
                    font-weight: 600;
                    background-color: {ThemeColors.SURFACE};
                    color: {ThemeColors.TEXT};
                }}
                QLineEdit:hover {{
                    border-color: {ThemeColors.BORDER_FOCUS};
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {ThemeColors.PRIMARY};
                }}
            """)
        else:
            widget.setStyleSheet(f"""
                QLineEdit {{
                    border: 1.5px solid #EF4444;
                    background-color: #FEF2F2;
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-size: 12px;
                    font-weight: 600;
                    color: #991B1B;
                }}
            """)

    def _on_field_selection_changed(self) -> None:
        selected_rows = self.table_fields.selectionModel().selectedRows()
        has_sel = len(selected_rows) > 0
        self.btn_edit_field.setEnabled(has_sel)
        self.btn_duplicate_field.setEnabled(has_sel)
        self.btn_delete_field.setEnabled(has_sel)

        if has_sel:
            row_idx = selected_rows[0].row()
            self.btn_move_top.setEnabled(row_idx > 0)
            self.btn_move_up.setEnabled(row_idx > 0)
            self.btn_move_down.setEnabled(row_idx < len(self.fields) - 1)
            self.btn_move_bottom.setEnabled(row_idx < len(self.fields) - 1)
        else:
            self.btn_move_top.setEnabled(False)
            self.btn_move_up.setEnabled(False)
            self.btn_move_down.setEnabled(False)
            self.btn_move_bottom.setEnabled(False)

    def _on_field_table_double_clicked(self, item: QTableWidgetItem) -> None:
        self._on_edit_field_clicked()

    def _on_add_field_clicked(self) -> None:
        dlg = FieldEditDialog(
            available_sheets=self.available_sheets,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new_fld = dlg.get_field_config()
            if new_fld:
                self.fields.append(new_fld)
                self._refresh_fields_table()
                self.table_fields.selectRow(len(self.fields) - 1)

    def _on_duplicate_field_clicked(self) -> None:
        """Menduplikasi field yang dipilih secara instan."""
        selected_rows = self.table_fields.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        orig_fld = self.fields[row_idx]

        dup_data = orig_fld.to_dict()
        dup_data["field_id"] = f"fld_{uuid.uuid4().hex[:8]}"
        dup_data["label"] = f"{orig_fld.label} (Salinan)"
        dup_fld = PhotoFieldConfig.from_dict(dup_data)

        self.fields.insert(row_idx + 1, dup_fld)
        self._refresh_fields_table()
        self.table_fields.selectRow(row_idx + 1)

    def _on_edit_field_clicked(self) -> None:
        selected_rows = self.table_fields.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        current_fld = self.fields[row_idx]

        dlg = FieldEditDialog(
            field_config=current_fld,
            available_sheets=self.available_sheets,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated_fld = dlg.get_field_config()
            if updated_fld:
                self.fields[row_idx] = updated_fld
                self._refresh_fields_table()
                self.table_fields.selectRow(row_idx)

    def _on_delete_field_clicked(self) -> None:
        selected_rows = self.table_fields.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        target_fld = self.fields[row_idx]

        reply = QMessageBox.question(
            self,
            "Konfirmasi Hapus Field",
            f"Apakah Anda yakin ingin menghapus field '{target_fld.label}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.fields[row_idx]
            self._refresh_fields_table()

    def _on_move_top_clicked(self) -> None:
        """Memindahkan field yang dipilih ke baris paling pertama (paling atas)."""
        selected_rows = self.table_fields.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        if row_idx > 0:
            item = self.fields.pop(row_idx)
            self.fields.insert(0, item)
            self._refresh_fields_table()
            self.table_fields.selectRow(0)

    def _on_move_up_clicked(self) -> None:
        """Menggeser field yang dipilih naik 1 tingkat."""
        selected_rows = self.table_fields.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        if row_idx > 0:
            self.fields[row_idx], self.fields[row_idx - 1] = (
                self.fields[row_idx - 1],
                self.fields[row_idx],
            )
            self._refresh_fields_table()
            self.table_fields.selectRow(row_idx - 1)

    def _on_move_down_clicked(self) -> None:
        """Menggeser field yang dipilih turun 1 tingkat."""
        selected_rows = self.table_fields.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        if row_idx < len(self.fields) - 1:
            self.fields[row_idx], self.fields[row_idx + 1] = (
                self.fields[row_idx + 1],
                self.fields[row_idx],
            )
            self._refresh_fields_table()
            self.table_fields.selectRow(row_idx + 1)

    def _on_move_bottom_clicked(self) -> None:
        """Memindahkan field yang dipilih ke baris paling terakhir (paling bawah)."""
        selected_rows = self.table_fields.selectionModel().selectedRows()
        if not selected_rows:
            return
        row_idx = selected_rows[0].row()
        if row_idx < len(self.fields) - 1:
            item = self.fields.pop(row_idx)
            self.fields.append(item)
            self._refresh_fields_table()
            self.table_fields.selectRow(len(self.fields) - 1)

    def _on_export_json_clicked(self) -> None:
        """Mengekspor seluruh konfigurasi field template ke berkas JSON."""
        if not self.fields:
            QMessageBox.warning(
                self,
                "Export Gagal",
                "Belum ada field untuk diekspor. Silakan tambahkan field terlebih dahulu.",
            )
            return

        tpl_name = self.edit_name.text().strip() or "template"
        clean_tpl_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in tpl_name)
        default_filename = f"fields_{clean_tpl_name}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Konfigurasi Field ke JSON",
            default_filename,
            "JSON Files (*.json);;Semua Berkas (*.*)",
        )
        if not file_path:
            return

        export_data = {
            "version": "1.0",
            "template_name": self.edit_name.text().strip(),
            "export_date": datetime.now().isoformat(),
            "total_fields": len(self.fields),
            "fields": [f.to_dict() for f in self.fields],
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(
                self,
                "Export Berhasil",
                f"Berhasil mengekspor {len(self.fields)} konfigurasi field ke:\n{file_path}",
            )
        except Exception as err:
            QMessageBox.critical(
                self,
                "Export Gagal",
                f"Gagal menyimpan berkas JSON: {err}",
            )

    def _on_import_json_clicked(self) -> None:
        """Mengimpor konfigurasi field dari berkas JSON (Append atau Replace)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Konfigurasi Field dari JSON",
            "",
            "JSON Files (*.json);;Semua Berkas (*.*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as err:
            QMessageBox.critical(
                self,
                "Import Gagal",
                f"Gagal membaca berkas JSON: {err}",
            )
            return

        # Parsing format list langsung maupun dict { 'fields': [...] }
        if isinstance(raw_data, list):
            field_list = raw_data
        elif isinstance(raw_data, dict) and "fields" in raw_data and isinstance(raw_data["fields"], list):
            field_list = raw_data["fields"]
        else:
            QMessageBox.warning(
                self,
                "Format Tidak Valid",
                "Format JSON tidak dikenali. Berkas harus berupa daftar field [ {...} ] atau objek { \"fields\": [ {...} ] }.",
            )
            return

        imported_fields: List[PhotoFieldConfig] = []
        for item in field_list:
            if not isinstance(item, dict):
                continue
            item_dict = dict(item)
            # Pastikan selalu memiliki field_id unik agar tidak konflik
            item_dict["field_id"] = f"fld_{uuid.uuid4().hex[:8]}"

            try:
                fld_obj = PhotoFieldConfig.from_dict(item_dict)
                imported_fields.append(fld_obj)
            except Exception:
                pass

        if not imported_fields:
            QMessageBox.warning(
                self,
                "Import Gagal",
                "Tidak ada field valid yang dapat diimpor dari berkas JSON tersebut.",
            )
            return

        # Jika sudah ada field, tanyakan Append vs Replace
        if self.fields:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Mode Import Field")
            msg_box.setText(
                f"Ditemukan {len(imported_fields)} field dalam berkas JSON.\n"
                f"Template saat ini sudah memiliki {len(self.fields)} field.\n\n"
                "Pilih cara penggabungan:"
            )
            btn_replace = msg_box.addButton("Ganti Semua (Replace)", QMessageBox.ButtonRole.AcceptRole)
            btn_append = msg_box.addButton("Tambahkan (Append)", QMessageBox.ButtonRole.ActionRole)
            btn_cancel = msg_box.addButton("Batal", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(btn_append)
            msg_box.exec()

            clicked_btn = msg_box.clickedButton()
            if clicked_btn == btn_cancel:
                return
            elif clicked_btn == btn_replace:
                self.fields = imported_fields
            else:
                self.fields.extend(imported_fields)
        else:
            self.fields = imported_fields

        self._refresh_fields_table()
        QMessageBox.information(
            self,
            "Import Berhasil",
            f"Berhasil mengimpor {len(imported_fields)} field. Total field sekarang: {len(self.fields)}.",
        )

    def _on_sample_json_clicked(self) -> None:
        """Menyimpan berkas contoh format JSON konfigurasi field template."""
        sample_file_path = Path("data/templates/template_fields_sample.json")
        sample_data = None
        if sample_file_path.is_file():
            try:
                with open(sample_file_path, "r", encoding="utf-8") as f:
                    sample_data = json.load(f)
            except Exception:
                pass

        if not sample_data:
            sample_data = {
                "version": "1.0",
                "description": "Contoh Format Konfigurasi Field Template BTS Document Control",
                "fields": [
                    {
                        "field_id": "fld_sample_01",
                        "label": "Foto Antenna Sektor 1",
                        "sheet_name": "Sheet1",
                        "cell_anchor": "B5",
                        "field_type": "photo",
                        "sizing_mode": "fit_to_cell",
                        "custom_width": 0,
                        "custom_height": 0,
                        "padding": 2,
                        "alignment": "center",
                        "default_text": "",
                    },
                    {
                        "field_id": "fld_sample_02",
                        "label": "Foto Rack Perangkat",
                        "sheet_name": "Sheet1",
                        "cell_anchor": "I5",
                        "field_type": "photo",
                        "sizing_mode": "custom",
                        "custom_width": 400,
                        "custom_height": 300,
                        "padding": 4,
                        "alignment": "top-left",
                        "default_text": "",
                    },
                    {
                        "field_id": "fld_sample_03",
                        "label": "Nama Site",
                        "sheet_name": "Sheet1",
                        "cell_anchor": "C2",
                        "field_type": "text",
                        "sizing_mode": "fit_to_cell",
                        "custom_width": 0,
                        "custom_height": 0,
                        "padding": 0,
                        "alignment": "center",
                        "default_text": "SITE-001",
                    },
                ],
            }

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Contoh Format JSON Field",
            "template_fields_contoh.json",
            "JSON Files (*.json);;Semua Berkas (*.*)",
        )
        if not save_path:
            return

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(sample_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(
                self,
                "Berhasil Disimpan",
                f"Contoh format JSON berhasil disimpan ke:\n{save_path}",
            )
        except Exception as err:
            QMessageBox.critical(
                self,
                "Gagal Menyimpan",
                f"Gagal menyimpan contoh format JSON: {err}",
            )

    def validate_form(self) -> bool:
        """
        Validasi seluruh isian form:
        - Nama template tidak boleh kosong
        - File template harus valid dan ada
        - Setidaknya ada 1 field (foto atau teks)
        - Seluruh field memiliki koordinat sel yang valid
        """
        name = self.edit_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validasi Gagal", "Nama template tidak boleh kosong.")
            self.edit_name.setFocus()
            return False

        file_path = self.edit_file_path.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Validasi Gagal", "File template Excel tidak boleh kosong.")
            self.edit_file_path.setFocus()
            return False

        path_obj = Path(file_path)
        if not path_obj.is_file():
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                f"File template Excel tidak ditemukan pada lokasi:\n{file_path}",
            )
            self.edit_file_path.setFocus()
            return False

        if path_obj.suffix.lower() not in (".xlsx", ".xlsm", ".xltx", ".xltm"):
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                "File template harus merupakan spreadsheet Excel berformat .xlsx atau .xlsm.",
            )
            self.edit_file_path.setFocus()
            return False

        if not self.fields:
            QMessageBox.warning(
                self,
                "Validasi Gagal",
                "Template harus memiliki setidaknya satu field (foto atau teks).\n"
                "Klik tombol 'Tambah Field' untuk menambahkan field.",
            )
            return False

        for idx, fld in enumerate(self.fields):
            if not fld.label.strip():
                QMessageBox.warning(
                    self,
                    "Validasi Gagal",
                    f"Baris {idx + 1}: Label field tidak boleh kosong.",
                )
                return False

            if not fld.sheet_name.strip():
                QMessageBox.warning(
                    self,
                    "Validasi Gagal",
                    f"Baris {idx + 1} ('{fld.label}'): Nama sheet target tidak boleh kosong.",
                )
                return False

            if not is_valid_cell_coordinate(fld.cell_anchor):
                QMessageBox.warning(
                    self,
                    "Validasi Gagal",
                    f"Baris {idx + 1} ('{fld.label}'): Koordinat sel anchor '{fld.cell_anchor}' tidak valid.",
                )
                return False

        return True

    def _on_save_template_clicked(self) -> None:
        if not self.validate_form():
            return

        name = self.edit_name.text().strip()
        file_path = self.edit_file_path.text().strip()
        output_pattern = self.edit_output_filename_pattern.text().strip()
        now_iso = datetime.now().isoformat()

        if self.template:
            template_id = self.template.template_id
            created_at = self.template.created_at
        else:
            template_id = f"tpl_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
            created_at = now_iso

        self.saved_template = TemplateConfig(
            template_id=template_id,
            name=name,
            template_file_path=file_path,
            fields=list(self.fields),
            output_filename_pattern=output_pattern,
            created_at=created_at,
            updated_at=now_iso,
        )

        if self.storage is not None:
            self.storage.save_template(self.saved_template)

        self.accept()

    def get_template_config(self) -> Optional[TemplateConfig]:
        """Mengambil TemplateConfig hasil penyimpanan dialog."""
        return self.saved_template


class TemplateManagerDialog(QDialog):
    """
    Dialog visual untuk manajemen template laporan Excel.
    
    Fitur:
    - Menampilkan tabel seluruh template tersimpan
    - Tombol Buat Template Baru (membuka TemplateEditorDialog)
    - Tombol Edit Template (membuka TemplateEditorDialog)
    - Tombol Hapus Template (konfirmasi dan hapus dari storage)
    - Tombol Pilih Template Aktif (memilih template untuk digunakan di aplikasi)
    """

    def __init__(
        self,
        storage: Optional[StorageManager] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.storage = storage or StorageManager()
        self.selected_template: Optional[TemplateConfig] = None
        self.loaded_templates: List[TemplateConfig] = []

        self._init_ui()
        self.load_templates()

    def _init_ui(self) -> None:
        self.setWindowTitle("Manajemen Template Laporan")
        self.resize(840, 580)
        self.setMinimumSize(720, 480)
        self.setModal(True)

        if APP_ICON_PNG.is_file():
            self.setWindowIcon(QIcon(str(APP_ICON_PNG)))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        lbl_title = QLabel("Manajemen Template Laporan", self)
        lbl_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {ThemeColors.TEXT};
        """)
        header_layout.addWidget(lbl_title)

        lbl_subtitle = QLabel(
            "Pilih, buat, atau sesuaikan template laporan Excel dan pemetaan field foto",
            self,
        )
        lbl_subtitle.setStyleSheet(f"""
            font-size: 11px;
            color: {ThemeColors.TEXT_MUTED};
        """)
        header_layout.addWidget(lbl_subtitle)
        layout.addLayout(header_layout)

        # 2. Toolbar Tombol Template
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)

        self.btn_new = QPushButton("Buat Template Baru", self)
        self.btn_new.setObjectName("PrimaryButton")
        self.btn_new.setIcon(get_icon("plus", color="#ffffff", size=16))
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new.setFixedHeight(34)
        self.btn_new.clicked.connect(self._on_new_template_clicked)
        toolbar_layout.addWidget(self.btn_new)

        self.btn_edit = QPushButton("Edit Template", self)
        self.btn_edit.setIcon(get_icon("file_spreadsheet", size=16))
        self.btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_edit.setFixedHeight(34)
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._on_edit_template_clicked)
        toolbar_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Hapus Template", self)
        self.btn_delete.setObjectName("DangerButton")
        self.btn_delete.setIcon(get_icon("trash", color="#ef4444", size=16))
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setFixedHeight(34)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete_template_clicked)
        toolbar_layout.addWidget(self.btn_delete)

        toolbar_layout.addStretch(1)
        layout.addLayout(toolbar_layout)

        # 3. Table Templates
        self.table_templates = QTableWidget(self)
        self.table_templates.setColumnCount(4)
        self.table_templates.setHorizontalHeaderLabels([
            "Nama Template",
            "File Excel",
            "Jumlah Field",
            "Terakhir Diperbarui",
        ])
        self.table_templates.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_templates.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_templates.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_templates.verticalHeader().setVisible(False)
        self.table_templates.verticalHeader().setDefaultSectionSize(42)
        self.table_templates.verticalHeader().setMinimumSectionSize(38)
        self.table_templates.itemSelectionChanged.connect(self._on_template_selection_changed)
        self.table_templates.itemDoubleClicked.connect(self._on_template_double_clicked)

        header = self.table_templates.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table_templates, stretch=1)

        # 4. Footer Buttons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        self.btn_select = QPushButton("Pilih Template Aktif", self)
        self.btn_select.setObjectName("PrimaryButton")
        self.btn_select.setIcon(get_icon("check", color="#ffffff", size=16))
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.setFixedHeight(36)
        self.btn_select.setEnabled(False)
        self.btn_select.clicked.connect(self._on_select_template_clicked)
        footer_layout.addWidget(self.btn_select)

        footer_layout.addStretch(1)

        self.btn_close = QPushButton("Tutup", self)
        self.btn_close.setIcon(get_icon("x", size=16))
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setFixedHeight(36)
        self.btn_close.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_close)

        layout.addLayout(footer_layout)

    def load_templates(self) -> None:
        """Muat ulang seluruh template dari StorageManager ke tabel."""
        self.loaded_templates = self.storage.list_templates()
        self.table_templates.setRowCount(len(self.loaded_templates))

        for row_idx, tpl in enumerate(self.loaded_templates):
            # 0: Nama
            item_name = QTableWidgetItem(tpl.name)
            self.table_templates.setItem(row_idx, 0, item_name)

            # 1: File Excel
            filename = Path(tpl.template_file_path).name if tpl.template_file_path else "-"
            item_file = QTableWidgetItem(filename)
            item_file.setToolTip(tpl.template_file_path)
            self.table_templates.setItem(row_idx, 1, item_file)

            # 2: Jumlah Field
            item_fields = QTableWidgetItem(f"{len(tpl.fields)} field")
            item_fields.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_templates.setItem(row_idx, 2, item_fields)

            # 3: Tanggal
            date_display = tpl.updated_at[:10] if tpl.updated_at else "-"
            item_date = QTableWidgetItem(date_display)
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_templates.setItem(row_idx, 3, item_date)

        self._on_template_selection_changed()

    def _on_template_selection_changed(self) -> None:
        selected_rows = self.table_templates.selectionModel().selectedRows()
        has_sel = len(selected_rows) > 0
        self.btn_edit.setEnabled(has_sel)
        self.btn_delete.setEnabled(has_sel)
        self.btn_select.setEnabled(has_sel)

    def _get_selected_template(self) -> Optional[TemplateConfig]:
        selected_rows = self.table_templates.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row_idx = selected_rows[0].row()
        if 0 <= row_idx < len(self.loaded_templates):
            return self.loaded_templates[row_idx]
        return None

    def _on_template_double_clicked(self, item: QTableWidgetItem) -> None:
        self._on_edit_template_clicked()

    def _on_new_template_clicked(self) -> None:
        dlg = TemplateEditorDialog(storage=self.storage, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_templates()

    def _on_edit_template_clicked(self) -> None:
        tpl = self._get_selected_template()
        if not tpl:
            return

        dlg = TemplateEditorDialog(template=tpl, storage=self.storage, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_templates()

    def _on_delete_template_clicked(self) -> None:
        tpl = self._get_selected_template()
        if not tpl:
            return

        reply = QMessageBox.question(
            self,
            "Konfirmasi Hapus Template",
            f"Apakah Anda yakin ingin menghapus template '{tpl.name}'?\n"
            "Tindakan ini tidak dapat dibatalkan.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.storage.delete_template(tpl.template_id)
            self.load_templates()

    def _on_select_template_clicked(self) -> None:
        tpl = self._get_selected_template()
        if not tpl:
            return
        self.selected_template = tpl
        self.accept()

    def get_selected_template(self) -> Optional[TemplateConfig]:
        """Mengambil template yang dipilih pengguna untuk diaktifkan."""
        return self.selected_template

