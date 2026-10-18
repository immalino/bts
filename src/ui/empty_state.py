"""
BTS Document Control - Workspace Empty State Onboarding Component
Widget penyambut visual saat belum ada proyek site atau template yang dipilih.
Memberikan instruksi alur kerja yang jelas dan tombol aksi cepat.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.icons import get_icon, render_svg_pixmap
from src.ui.styles import ThemeManager


class WorkspaceEmptyState(QFrame):
    """
    Widget Onboarding Modern yang ditampilkan di area kerja utama
    ketika pengguna belum memilih Proyek Site atau Template Excel.
    """

    select_site_clicked = Signal()
    manage_template_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceEmptyState")
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(40, 48, 40, 48)
        main_layout.setSpacing(20)

        # 1. Icon Ilustrasi Pusat
        self.lbl_icon = QLabel(self)
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_icon()
        main_layout.addWidget(self.lbl_icon)

        # 2. Judul & Subtitle
        text_container = QVBoxLayout()
        text_container.setSpacing(6)
        text_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_title = QLabel("Mulai Proyek Dokumen BTS", self)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: 700;")
        text_container.addWidget(self.lbl_title)

        self.lbl_desc = QLabel(
            "Pilih proyek site yang tersimpan atau buat proyek baru untuk memuat\n"
            "seluruh slot foto sesuai template laporan Excel resmi.",
            self,
        )
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_desc.setStyleSheet("font-size: 13px; opacity: 0.75; line-height: 1.5;")
        text_container.addWidget(self.lbl_desc)

        main_layout.addLayout(text_container)

        # 3. Step Cards / Badges (3 Langkah Kerja)
        steps_layout = QHBoxLayout()
        steps_layout.setSpacing(12)
        steps_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        steps = [
            ("building", "1. Pilih / Buat Site", "Tentukan ID site BTS"),
            ("upload_cloud", "2. Tarik & Lepas Foto", "Auto-fit ke ukuran sel"),
            ("file_spreadsheet", "3. Generate Dokumen", "Laporan Excel siap serah"),
        ]

        for icon_name, step_title, step_desc in steps:
            card = QFrame(self)
            card.setObjectName("CardPanel")
            card.setFixedWidth(200)
            card.setFixedHeight(80)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(12, 10, 12, 10)
            c_layout.setSpacing(3)
            c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            h_head = QHBoxLayout()
            h_head.setSpacing(6)
            h_head.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon_lbl = QLabel(card)
            icon_lbl.setPixmap(render_svg_pixmap(icon_name, color="#2563EB", size=16))
            h_head.addWidget(icon_lbl)

            st_lbl = QLabel(step_title, card)
            st_lbl.setStyleSheet("font-size: 12px; font-weight: 600;")
            h_head.addWidget(st_lbl)

            c_layout.addLayout(h_head)

            desc_lbl = QLabel(step_desc, card)
            desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_lbl.setStyleSheet("font-size: 11px; opacity: 0.7;")
            c_layout.addWidget(desc_lbl)

            steps_layout.addWidget(card)

        main_layout.addLayout(steps_layout)

        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_site = QPushButton("Pilih / Buat Proyek Site", self)
        self.btn_site.setObjectName("PrimaryButton")
        self.btn_site.setIcon(get_icon("building", color="#FFFFFF", size=16))
        self.btn_site.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_site.setStyleSheet("padding: 9px 18px; font-size: 13px; font-weight: 600;")
        self.btn_site.clicked.connect(self.select_site_clicked.emit)
        btn_layout.addWidget(self.btn_site)

        self.btn_template = QPushButton("Kelola Template Excel", self)
        self.btn_template.setIcon(get_icon("file_spreadsheet", size=16))
        self.btn_template.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_template.setStyleSheet("padding: 9px 16px; font-size: 13px;")
        self.btn_template.clicked.connect(self.manage_template_clicked.emit)
        btn_layout.addWidget(self.btn_template)

        main_layout.addLayout(btn_layout)

    def _update_icon(self) -> None:
        """Memperbarui warna ikon sesuai tema aktif."""
        is_dark = ThemeManager.instance().is_dark
        icon_color = "#3B82F6" if is_dark else "#2563EB"
        self.lbl_icon.setPixmap(render_svg_pixmap("folder", color=icon_color, size=64))

    def update_theme(self) -> None:
        """Dipanggil saat tema aplikasi berubah."""
        self._update_icon()

