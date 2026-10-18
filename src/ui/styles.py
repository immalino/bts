"""
Photo Rename Studio - Stylesheet & Desain Tema Modern
"""

from src.config import ThemeColors

APP_STYLESHEET = f"""
/* ==========================================================================
   Global Window & Base Settings
   ========================================================================== */
QWidget {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: {ThemeColors.TEXT};
    font-size: 13px;
}}

QMainWindow {{
    background-color: {ThemeColors.BACKGROUND};
}}

/* ==========================================================================
   Modern Minimalist ScrollArea & ScrollBars
   ========================================================================== */
QScrollArea {{
    background-color: transparent;
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 8px;
}}

QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

QScrollBar:vertical {{
    border: none;
    background-color: transparent;
    width: 10px;
    margin: 4px 2px 4px 0px;
}}

QScrollBar::handle:vertical {{
    background-color: #CBD5E1;
    min-height: 36px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #94A3B8;
}}

QScrollBar::handle:vertical:pressed {{
    background-color: #64748B;
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
    height: 10px;
    margin: 0px 4px 2px 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: #CBD5E1;
    min-width: 36px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: #94A3B8;
}}

QScrollBar::handle:horizontal:pressed {{
    background-color: #64748B;
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
   Card Panels (Header, Toolbar, Footer)
   ========================================================================== */
QFrame#HeaderCard,
QFrame#ToolbarCard,
QFrame#FooterCard {{
    background-color: {ThemeColors.SURFACE};
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 8px;
}}

/* ==========================================================================
   Line Edit & Inputs
   ========================================================================== */
QLineEdit {{
    background-color: {ThemeColors.SURFACE};
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 6px;
    padding: 7px 12px;
    color: {ThemeColors.TEXT};
    font-size: 12px;
    selection-background-color: {ThemeColors.PRIMARY};
    selection-color: #FFFFFF;
}}

QLineEdit:hover {{
    border-color: #CBD5E1;
}}

QLineEdit:focus {{
    border: 1.5px solid {ThemeColors.BORDER_FOCUS};
    background-color: #FFFFFF;
}}

QLineEdit:read-only {{
    background-color: #F8FAFC;
    color: {ThemeColors.TEXT_MUTED};
    border-color: {ThemeColors.BORDER};
}}

/* ==========================================================================
   Buttons
   ========================================================================== */
QPushButton {{
    font-size: 12px;
    font-weight: 500;
    border-radius: 6px;
    padding: 7px 14px;
    border: 1px solid {ThemeColors.BORDER};
    background-color: {ThemeColors.SURFACE};
    color: {ThemeColors.TEXT};
}}

QPushButton:hover {{
    background-color: #F1F5F9;
    border-color: #CBD5E1;
}}

QPushButton:pressed {{
    background-color: #E2E8F0;
}}

QPushButton:disabled {{
    background-color: #F8FAFC;
    color: #94A3B8;
    border-color: {ThemeColors.BORDER};
}}

/* Primary Buttons */
QPushButton#PrimaryButton {{
    background-color: {ThemeColors.PRIMARY};
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {ThemeColors.PRIMARY_HOVER};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: #1E40AF;
}}

/* Danger Buttons */
QPushButton#DangerButton {{
    background-color: {ThemeColors.SURFACE};
    border: 1px solid {ThemeColors.BORDER};
    color: {ThemeColors.TEXT};
}}

QPushButton#DangerButton:hover {{
    background-color: #FEF2F2;
    border-color: #FCA5A5;
    color: {ThemeColors.ERROR};
}}

QPushButton#DangerButton:pressed {{
    background-color: #FEE2E2;
}}

/* ==========================================================================
   CheckBoxes
   ========================================================================== */
QCheckBox {{
    spacing: 8px;
    font-size: 12px;
    font-weight: 500;
    color: {ThemeColors.TEXT};
}}

QCheckBox:hover {{
    color: {ThemeColors.PRIMARY};
}}

/* ==========================================================================
   ToolTips & Dialogs
   ========================================================================== */
QToolTip {{
    background-color: #1E293B;
    color: #FFFFFF;
    border: none;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 11px;
}}

QMessageBox {{
    background-color: {ThemeColors.SURFACE};
}}

QMessageBox QLabel {{
    color: {ThemeColors.TEXT};
    font-size: 12px;
}}
"""
