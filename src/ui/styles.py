"""
BTS Document Control - Stylesheet & Dual Theme Engine (Light & Dark Mode)
Menyediakan sistem token desain terpusat, palette warna modern, stylesheet global,
serta ThemeManager untuk perpindahan tema instan (Light / Dark mode).
"""

from dataclasses import dataclass
from typing import Optional
from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtWidgets import QApplication

from src.config import ThemeColors


@dataclass
class ThemePalette:
    name: str
    is_dark: bool
    BACKGROUND: str
    SURFACE: str
    SURFACE_ALT: str
    BORDER: str
    BORDER_LIGHT: str
    BORDER_FOCUS: str
    PRIMARY: str
    PRIMARY_HOVER: str
    PRIMARY_ACTIVE: str
    PRIMARY_LIGHT: str
    TEXT: str
    TEXT_MUTED: str
    TEXT_SUBTLE: str
    SUCCESS: str
    SUCCESS_BG: str
    SUCCESS_BORDER: str
    SUCCESS_TEXT: str
    DANGER: str
    DANGER_HOVER: str
    DANGER_BG: str
    DANGER_BORDER: str
    DANGER_TEXT: str
    WARNING: str
    WARNING_BG: str
    WARNING_TEXT: str
    SCROLLBAR_HANDLE: str
    SCROLLBAR_HOVER: str
    TABLE_HEADER_BG: str
    TABLE_ROW_ALT: str


LIGHT_PALETTE = ThemePalette(
    name="light",
    is_dark=False,
    BACKGROUND="#F8FAFC",
    SURFACE="#FFFFFF",
    SURFACE_ALT="#F1F5F9",
    BORDER="#E2E8F0",
    BORDER_LIGHT="#F1F5F9",
    BORDER_FOCUS="#2563EB",
    PRIMARY="#2563EB",
    PRIMARY_HOVER="#1D4ED8",
    PRIMARY_ACTIVE="#1E40AF",
    PRIMARY_LIGHT="#EFF6FF",
    TEXT="#0F172A",
    TEXT_MUTED="#64748B",
    TEXT_SUBTLE="#94A3B8",
    SUCCESS="#10B981",
    SUCCESS_BG="#ECFDF5",
    SUCCESS_BORDER="#A7F3D0",
    SUCCESS_TEXT="#065F46",
    DANGER="#EF4444",
    DANGER_HOVER="#DC2626",
    DANGER_BG="#FEF2F2",
    DANGER_BORDER="#FECACA",
    DANGER_TEXT="#991B1B",
    WARNING="#F59E0B",
    WARNING_BG="#FFFBEB",
    WARNING_TEXT="#92400E",
    SCROLLBAR_HANDLE="#CBD5E1",
    SCROLLBAR_HOVER="#94A3B8",
    TABLE_HEADER_BG="#F8FAFC",
    TABLE_ROW_ALT="#FAFAFA",
)

DARK_PALETTE = ThemePalette(
    name="dark",
    is_dark=True,
    BACKGROUND="#0B0F17",
    SURFACE="#131B2E",
    SURFACE_ALT="#1A243B",
    BORDER="#23304A",
    BORDER_LIGHT="#1E2A40",
    BORDER_FOCUS="#3B82F6",
    PRIMARY="#3B82F6",
    PRIMARY_HOVER="#2563EB",
    PRIMARY_ACTIVE="#1D4ED8",
    PRIMARY_LIGHT="#172554",
    TEXT="#F8FAFC",
    TEXT_MUTED="#94A3B8",
    TEXT_SUBTLE="#64748B",
    SUCCESS="#34D399",
    SUCCESS_BG="#064E3B",
    SUCCESS_BORDER="#047857",
    SUCCESS_TEXT="#D1FAE5",
    DANGER="#F87171",
    DANGER_HOVER="#EF4444",
    DANGER_BG="#450A0A",
    DANGER_BORDER="#991B1B",
    DANGER_TEXT="#FEE2E2",
    WARNING="#FBBF24",
    WARNING_BG="#451A03",
    WARNING_TEXT="#FEF3C7",
    SCROLLBAR_HANDLE="#334155",
    SCROLLBAR_HOVER="#475569",
    TABLE_HEADER_BG="#1A243B",
    TABLE_ROW_ALT="#111827",
)


from typing import Dict, Optional, Union
from dataclasses import dataclass

def generate_stylesheet(palette_or_theme: Union[ThemePalette, str] = LIGHT_PALETTE) -> str:
    """Menghasilkan QSS Stylesheet lengkap berdasarkan ThemePalette atau nama tema ('light'/'dark')."""
    if isinstance(palette_or_theme, str):
        p = DARK_PALETTE if palette_or_theme == "dark" else LIGHT_PALETTE
    else:
        p = palette_or_theme
    return f"""
/* ==========================================================================
   Global Window & Base Settings
   ========================================================================== */
QWidget {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: {p.TEXT};
    font-size: 13px;
}}

QMainWindow, QDialog {{
    background-color: {p.BACKGROUND};
    color: {p.TEXT};
}}

/* ==========================================================================
   ScrollArea & ScrollBars Minimalis Modern
   ========================================================================== */
QScrollArea {{
    background-color: transparent;
    border: 1px solid {p.BORDER};
    border-radius: 8px;
}}

QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

QScrollBar:vertical {{
    border: none;
    background-color: transparent;
    width: 8px;
    margin: 4px 2px 4px 0px;
}}

QScrollBar::handle:vertical {{
    background-color: {p.SCROLLBAR_HANDLE};
    min-height: 36px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {p.SCROLLBAR_HOVER};
}}

QScrollBar::sub-line:vertical,
QScrollBar::add-line:vertical {{
    height: 0px;
    background: none;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    border: none;
    background-color: transparent;
    height: 8px;
    margin: 0px 4px 2px 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: {p.SCROLLBAR_HANDLE};
    min-width: 36px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {p.SCROLLBAR_HOVER};
}}

QScrollBar::sub-line:horizontal,
QScrollBar::add-line:horizontal {{
    width: 0px;
    background: none;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ==========================================================================
   Card Panels (Header, Toolbar, Footer, Container)
   ========================================================================== */
QFrame#HeaderCard,
QFrame#ToolbarCard,
QFrame#FooterCard,
QFrame#CardPanel {{
    background-color: {p.SURFACE};
    border: 1px solid {p.BORDER};
    border-radius: 10px;
}}

/* ==========================================================================
   Inputs (QLineEdit, QSpinBox, QComboBox)
   ========================================================================== */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {p.SURFACE};
    border: 1px solid {p.BORDER};
    border-radius: 6px;
    padding: 7px 12px;
    color: {p.TEXT};
    font-size: 12px;
    selection-background-color: {p.PRIMARY};
    selection-color: #FFFFFF;
}}

QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{
    border-color: {p.BORDER_FOCUS};
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1.5px solid {p.BORDER_FOCUS};
    background-color: {p.SURFACE};
}}

QLineEdit:read-only {{
    background-color: {p.SURFACE_ALT};
    color: {p.TEXT_MUTED};
    border-color: {p.BORDER};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {p.SURFACE};
    color: {p.TEXT};
    border: 1px solid {p.BORDER};
    selection-background-color: {p.PRIMARY_LIGHT};
    selection-color: {p.PRIMARY};
    border-radius: 6px;
    outline: none;
}}

/* ==========================================================================
   Buttons
   ========================================================================== */
QPushButton {{
    font-size: 12px;
    font-weight: 500;
    border-radius: 6px;
    padding: 7px 14px;
    border: 1px solid {p.BORDER};
    background-color: {p.SURFACE};
    color: {p.TEXT};
}}

QPushButton:hover {{
    background-color: {p.SURFACE_ALT};
    border-color: {p.BORDER_FOCUS};
}}

QPushButton:pressed {{
    background-color: {p.BORDER};
}}

QPushButton:disabled {{
    background-color: {p.SURFACE_ALT};
    color: {p.TEXT_SUBTLE};
    border-color: {p.BORDER_LIGHT};
}}

/* Primary Buttons */
QPushButton#PrimaryButton {{
    background-color: {p.PRIMARY};
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {p.PRIMARY_HOVER};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {p.PRIMARY_ACTIVE};
}}

/* Danger Buttons */
QPushButton#DangerButton {{
    background-color: {p.DANGER_BG};
    border: 1px solid {p.DANGER_BORDER};
    color: {p.DANGER_TEXT};
}}

QPushButton#DangerButton:hover {{
    background-color: {p.DANGER_HOVER};
    border-color: {p.DANGER};
    color: #FFFFFF;
}}

QPushButton#DangerButton:pressed {{
    background-color: {p.DANGER_TEXT};
}}

/* Icon / Ghost Button */
QPushButton#GhostButton {{
    background-color: transparent;
    border: 1px solid transparent;
    padding: 6px 10px;
}}

QPushButton#GhostButton:hover {{
    background-color: {p.SURFACE_ALT};
    border-color: {p.BORDER};
}}

/* Export Action Button */
QPushButton#ExportButton {{
    background-color: {p.PRIMARY};
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    padding: 10px 22px;
}}

QPushButton#ExportButton:hover {{
    background-color: {p.PRIMARY_HOVER};
}}

QPushButton#ExportButton:pressed {{
    background-color: {p.PRIMARY_ACTIVE};
}}

QPushButton#ExportButton:disabled {{
    background-color: {p.TEXT_SUBTLE};
    color: {p.SURFACE_ALT};
}}

/* ==========================================================================
   Checkboxes & Radios
   ========================================================================== */
QCheckBox, QRadioButton {{
    spacing: 8px;
    font-size: 12px;
    font-weight: 500;
    color: {p.TEXT};
}}

QCheckBox:hover, QRadioButton:hover {{
    color: {p.PRIMARY};
}}

/* ==========================================================================
   Progress Bar
   ========================================================================== */
QProgressBar {{
    background-color: {p.SURFACE_ALT};
    border: 1px solid {p.BORDER};
    border-radius: 4px;
    height: 8px;
    text-align: center;
    font-size: 9px;
    font-weight: 600;
    color: {p.TEXT};
}}

QProgressBar::chunk {{
    background-color: {p.PRIMARY};
    border-radius: 3px;
}}

/* ==========================================================================
   Table Widget & Headers
   ========================================================================== */
QTableWidget {{
    background-color: {p.SURFACE};
    border: 1px solid {p.BORDER};
    border-radius: 8px;
    gridline-color: {p.BORDER_LIGHT};
    font-size: 12px;
    color: {p.TEXT};
    outline: none;
}}

QTableWidget::item {{
    padding: 4px 10px;
    border-bottom: 1px solid {p.BORDER_LIGHT};
    outline: none;
}}

QTableWidget::item:focus {{
    outline: none;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {p.PRIMARY_LIGHT};
    color: {p.PRIMARY};
    outline: none;
}}

QTableWidget::item:selected:focus {{
    background-color: {p.PRIMARY_LIGHT};
    color: {p.PRIMARY};
    outline: none;
}}

QHeaderView::section {{
    background-color: {p.TABLE_HEADER_BG};
    color: {p.TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {p.BORDER};
    min-height: 26px;
}}

/* ==========================================================================
   Tooltips & Dialogs
   ========================================================================== */
QToolTip {{
    background-color: {p.TEXT};
    color: {p.SURFACE};
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 11px;
}}

QMessageBox {{
    background-color: {p.SURFACE};
}}

QMessageBox QLabel {{
    color: {p.TEXT};
    font-size: 12px;
}}

/* Group Box */
QGroupBox {{
    font-size: 12px;
    font-weight: 600;
    color: {p.TEXT};
    border: 1px solid {p.BORDER};
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 14px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: {p.TEXT};
}}
"""


class ThemeManager(QObject):
    """
    Singleton Manager untuk mengelola tema visual aplikasi (Light & Dark mode).
    Memancarkan sinyal theme_changed saat tema berganti dan menyimpan preferensi ke QSettings.
    """

    theme_changed = Signal(str)  # "light" atau "dark"

    _instance: Optional["ThemeManager"] = None

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("BTSDocumentControl", "ThemeSettings")
        saved_theme = self._settings.value("theme", "light")
        self._current_theme: str = saved_theme if saved_theme in ("light", "dark") else "light"

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "ThemeManager":
        """Alias untuk instance()."""
        return cls.instance()

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def is_dark(self) -> bool:
        return self._current_theme == "dark"

    def is_dark_mode(self) -> bool:
        """Helper boolean mengecek apakah dark mode aktif."""
        return self.is_dark

    def get_palette(self) -> ThemePalette:
        return DARK_PALETTE if self.is_dark else LIGHT_PALETTE

    def set_theme(self, theme_name: str) -> None:
        if theme_name not in ("light", "dark"):
            return
        if self._current_theme != theme_name:
            self._current_theme = theme_name
            self._settings.setValue("theme", theme_name)
            self.apply_theme()
            self.theme_changed.emit(self._current_theme)

    def toggle_theme(self) -> str:
        """Beralih antara mode light dan dark."""
        new_theme = "dark" if self._current_theme == "light" else "light"
        self.set_theme(new_theme)
        return new_theme

    def apply_theme(self) -> None:
        """Menerapkan stylesheet ke QApplication global."""
        app = QApplication.instance()
        if app:
            qss = generate_stylesheet(self.get_palette())
            app.setStyleSheet(qss)


# Stylesheet default saat aplikasi baru dimulai (Light Palette)
APP_STYLESHEET = generate_stylesheet(LIGHT_PALETTE)
