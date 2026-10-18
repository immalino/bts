"""
Photo Rename Studio - Pengujian Unit Multi-Document per Site & Startup Auto-Load
Menguji:
1. Model SiteDocument (Inisialisasi, Serialisasi, Deserialisasi)
2. Model ProjectData Multi-Dokumen (add_document, switch_document, remove_document, sync_active_assignments)
3. Kompatibilitas Mundur (Backward Compatibility) dengan format JSON project versi lama
4. Isolasi Data Foto & Teks antar sub-dokumen dalam 1 Site
5. Widget DocumentTabBar & AddDocumentDialog
6. Auto-Load Site Terakhir pada Startup MainWindow via QSettings
"""

import os
import tempfile
from pathlib import Path
from PIL import Image
import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from src.core.models import PhotoFieldConfig, ProjectData, SiteDocument, TemplateConfig
from src.core.storage import StorageManager
from src.ui.document_tabs import AddDocumentDialog, DocumentTabBar
from src.ui.main_window import MainWindow


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def sample_templates(tmp_path: Path) -> tuple[StorageManager, TemplateConfig, TemplateConfig]:
    """Fixture menyediakan 2 template dokumen berbeda (contoh: CME & ATP)."""
    storage = StorageManager(base_dir=tmp_path / "data_storage")

    tpl_cme = TemplateConfig(
        template_id="tpl_cme_01",
        name="Template CME & Civil",
        template_file_path=str(tmp_path / "cme.xlsx"),
        fields=[
            PhotoFieldConfig(field_id="cme_f1", label="Foto Pondasi Tower", sheet_name="CME", cell_anchor="B5"),
            PhotoFieldConfig(field_id="cme_f2", label="Foto Pagar & Gerbang", sheet_name="CME", cell_anchor="B15"),
        ],
    )
    storage.save_template(tpl_cme)

    tpl_atp = TemplateConfig(
        template_id="tpl_atp_01",
        name="Template Dokumen ATP",
        template_file_path=str(tmp_path / "atp.xlsx"),
        fields=[
            PhotoFieldConfig(field_id="atp_f1", label="Foto Sektor 1 Azimuth", sheet_name="ATP", cell_anchor="C5"),
            PhotoFieldConfig(field_id="atp_f2", label="Foto Kabel Feeder", sheet_name="ATP", cell_anchor="C15"),
            PhotoFieldConfig(field_id="atp_f3", label="Foto Grounding Bar", sheet_name="ATP", cell_anchor="C25"),
        ],
    )
    storage.save_template(tpl_atp)

    return storage, tpl_cme, tpl_atp


# ==============================================================================
# 1. PENGUJIAN MODEL SITEDOCUMENT
# ==============================================================================

def test_site_document_initialization_and_serialization():
    """Memastikan SiteDocument dapat diinisialisasi, dikonversi ke dict, dan dimuat kembali."""
    doc = SiteDocument(
        doc_id="doc_test_1",
        template_id="tpl_cme_01",
        name="Laporan CME Lapangan",
        photo_assignments={"fld_1": "/path/to/foto1.jpg"},
        text_assignments={"fld_2": "Nilai Parameter"},
    )
    assert doc.doc_id == "doc_test_1"
    assert doc.name == "Laporan CME Lapangan"
    assert doc.photo_assignments["fld_1"] == "/path/to/foto1.jpg"

    doc_dict = doc.to_dict()
    assert doc_dict["doc_id"] == "doc_test_1"
    assert doc_dict["template_id"] == "tpl_cme_01"
    assert doc_dict["name"] == "Laporan CME Lapangan"
    assert doc_dict["photo_assignments"] == {"fld_1": "/path/to/foto1.jpg"}

    loaded_doc = SiteDocument.from_dict(doc_dict)
    assert loaded_doc.doc_id == doc.doc_id
    assert loaded_doc.template_id == doc.template_id
    assert loaded_doc.name == doc.name
    assert loaded_doc.photo_assignments == doc.photo_assignments


# ==============================================================================
# 2. PENGUJIAN PROJECTDATA MULTI-DOKUMEN
# ==============================================================================

def test_project_data_auto_seed_default_document():
    """Memastikan project yang diinisialisasi hanya dengan 1 template otomatis membuat 1 default document."""
    proj = ProjectData(
        project_id="proj_01",
        site_name="JKT-042",
        template_id="tpl_cme_01",
        photo_assignments={"cme_f1": "/path/foto1.jpg"},
    )
    assert len(proj.documents) == 1
    default_doc = proj.documents[0]
    assert default_doc.template_id == "tpl_cme_01"
    assert default_doc.photo_assignments["cme_f1"] == "/path/foto1.jpg"
    assert proj.active_doc_id == default_doc.doc_id


def test_project_data_add_and_switch_documents():
    """Memastikan penambahan dokumen baru dan perpindahan dokumen bekerja dengan sinkronisasi aktif."""
    proj = ProjectData(
        project_id="proj_01",
        site_name="JKT-042",
        template_id="tpl_cme_01",
        photo_assignments={"cme_f1": "/path/cme.jpg"},
    )
    doc_cme_id = proj.active_doc_id

    # Tambah dokumen kedua (ATP)
    doc_atp = proj.add_document(template_id="tpl_atp_01", name="Laporan ATP")
    assert len(proj.documents) == 2
    assert doc_atp.template_id == "tpl_atp_01"
    assert doc_atp.name == "Laporan ATP"

    # Status saat ini masih di CME
    assert proj.active_doc_id == doc_cme_id
    assert proj.template_id == "tpl_cme_01"

    # Berpindah ke dokumen ATP
    switched = proj.switch_document(doc_atp.doc_id)
    assert switched is True
    assert proj.active_doc_id == doc_atp.doc_id
    assert proj.template_id == "tpl_atp_01"
    assert proj.photo_assignments == {}

    # Isi foto di dokumen ATP
    proj.sync_active_assignments(photo_assignments={"atp_f1": "/path/atp.jpg"})
    assert doc_atp.photo_assignments["atp_f1"] == "/path/atp.jpg"
    assert proj.photo_assignments["atp_f1"] == "/path/atp.jpg"

    # Beralih kembali ke CME -> pastikan foto CME tidak tertukar dengan ATP
    proj.switch_document(doc_cme_id)
    assert proj.template_id == "tpl_cme_01"
    assert proj.photo_assignments == {"cme_f1": "/path/cme.jpg"}
    assert "atp_f1" not in proj.photo_assignments


def test_project_data_remove_document():
    """Memastikan penghapusan sub-dokumen berjalan benar dan dokumen terakhir dilindungi."""
    proj = ProjectData(
        project_id="proj_01",
        site_name="JKT-042",
        template_id="tpl_cme_01",
    )
    doc_1_id = proj.active_doc_id

    # Dokumen tunggal tidak boleh dihapus
    assert proj.remove_document(doc_1_id) is False
    assert len(proj.documents) == 1

    # Tambah dokumen kedua lalu hapus dokumen pertama
    doc_2 = proj.add_document(template_id="tpl_atp_01", name="ATP")
    assert len(proj.documents) == 2

    assert proj.remove_document(doc_1_id) is True
    assert len(proj.documents) == 1
    assert proj.active_doc_id == doc_2.doc_id
    assert proj.template_id == "tpl_atp_01"


def test_project_data_rename_document():
    """Memastikan nama sub-dokumen dapat diubah."""
    proj = ProjectData(
        project_id="proj_01",
        site_name="JKT-042",
        template_id="tpl_cme_01",
    )
    doc_id = proj.active_doc_id
    assert proj.rename_document(doc_id, "Laporan CME Revisi") is True
    assert proj.get_active_document().name == "Laporan CME Revisi"


# ==============================================================================
# 3. PENGUJIAN KOMPATIBILITAS MUNDUR (LEGACY JSON MIGRATION)
# ==============================================================================

def test_backward_compatibility_load_legacy_project_json():
    """Memastikan format JSON proyek lama (tanpa field documents) termigrasi otomatis saat dimuat."""
    legacy_json_dict = {
        "project_id": "legacy_site_99",
        "site_name": "BDG-101",
        "template_id": "tpl_legacy",
        "photo_assignments": {
            "fld_antena": "/images/antena.jpg",
            "fld_rectifier": "/images/rectifier.jpg",
        },
        "text_assignments": {
            "fld_site_id": "BDG-101",
        },
        "output_dir": "/output/legacy",
        "created_at": "2026-01-01T00:00:00",
        "last_exported_at": None,
    }

    project = ProjectData.from_dict(legacy_json_dict)
    assert len(project.documents) == 1
    assert project.active_doc_id == project.documents[0].doc_id
    assert project.template_id == "tpl_legacy"
    assert project.photo_assignments["fld_antena"] == "/images/antena.jpg"
    assert project.text_assignments["fld_site_id"] == "BDG-101"

    # Serialisasi ulang kini menyertakan documents
    saved_dict = project.to_dict()
    assert "documents" in saved_dict
    assert len(saved_dict["documents"]) == 1
    assert saved_dict["documents"][0]["photo_assignments"]["fld_antena"] == "/images/antena.jpg"


# ==============================================================================
# 4. PENGUJIAN WIDGET DOCUMENT TAB BAR
# ==============================================================================

def test_document_tab_bar_ui(qapp, sample_templates):
    """Memastikan DocumentTabBar me-render tombol tab sesuai documents di ProjectData."""
    storage, tpl_cme, tpl_atp = sample_templates

    proj = ProjectData(
        project_id="proj_tabs",
        site_name="JKT-TABS",
        template_id="tpl_cme_01",
    )
    doc_atp = proj.add_document("tpl_atp_01", name="ATP Dokumen")

    tab_bar = DocumentTabBar()
    tab_bar.update_documents(proj, storage)

    assert tab_bar.isVisible() is True
    assert len(tab_bar.tab_buttons) == 2

    # Verifikasi klik tab memancarkan sinyal document_selected
    selected_docs = []
    tab_bar.document_selected.connect(lambda d: selected_docs.append(d))

    btn_atp = tab_bar.tab_buttons[doc_atp.doc_id]
    btn_atp.clicked.emit(btn_atp.doc_id)
    assert doc_atp.doc_id in selected_docs


# ==============================================================================
# 5. PENGUJIAN STARTUP AUTO-LOAD VIA QSETTINGS
# ==============================================================================

def test_mainwindow_auto_load_last_project(qapp, sample_templates):
    """Memastikan MainWindow dengan auto_load_last_project=True membuka proyek terakhir dari QSettings."""
    storage, tpl_cme, tpl_atp = sample_templates

    # Simpan proyek dummy ke storage
    proj = ProjectData(
        project_id="proj_startup_test",
        site_name="SUB-999 Surabaya",
        template_id="tpl_cme_01",
    )
    storage.save_project(proj)

    # Set preferensi last_project_id ke QSettings
    settings = QSettings("BTSDocumentControl", "WorkspaceSettings")
    settings.setValue("last_project_id", proj.project_id)

    # Inisialisasi MainWindow dengan storage dummy dan auto_load aktif
    window = MainWindow(storage=storage, auto_load_last_project=True)
    window.show()
    qapp.processEvents()

    # Verifikasi bahwa proyek otomatis termuat
    assert window.current_project is not None
    assert window.current_project.project_id == "proj_startup_test"
    assert "SUB-999 Surabaya" in window.lbl_active_site.text()
    assert window.document_tab_bar.isVisible() is True

    window.close()


def test_mainwindow_fallback_to_empty_state_when_no_last_project(qapp, sample_templates):
    """Memastikan jika tidak ada last_project_id dan default_rows=0, MainWindow menampilkan empty state."""
    storage, _, _ = sample_templates

    # Kosongkan setting
    settings = QSettings("BTSDocumentControl", "WorkspaceSettings")
    settings.remove("last_project_id")

    window = MainWindow(default_rows=0, storage=storage, auto_load_last_project=True)
    window.show()
    qapp.processEvents()

    assert window.current_project is None
    assert window.empty_state.isVisible() is True
    assert window.document_tab_bar.isVisible() is False

    window.close()
