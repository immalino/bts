"""
Photo Rename Studio - Pengujian Unit & Integrasi Dynamic Workspace & Project Manager (Sesi 11)

Memverifikasi:
1. DynamicPhotoRow: inisialisasi, rendering nomor urut, label field, badge info, status Kosong/Terisi, thumbnail.
2. NewProjectDialog: validasi form (nama site kosong, pilihan template), pembuatan project baru.
3. ProjectManagerDialog: daftar site tersimpan, pemilihan site aktif, dan penghapusan site.
4. MainWindow Dynamic Rendering: me-render DynamicPhotoRow sesuai template aktif dan update info header.
5. Auto-persistence: perubahan foto pada dynamic row otomatis tersimpan ke data project aktif di disk.
6. Pergantian project/site yang mulus pada MainWindow.
"""

from pathlib import Path
from PIL import Image
import pytest
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from src.core.models import PhotoFieldConfig, ProjectData, TemplateConfig
from src.core.storage import StorageManager
from src.ui.dynamic_row import DynamicPhotoRow, DynamicRowStatus
from src.ui.main_window import MainWindow
from src.ui.project_dialog import NewProjectDialog, ProjectManagerDialog


@pytest.fixture(scope="session")
def qapp():
    """Fixture QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def dummy_image_file(tmp_path: Path) -> str:
    """Fixture membuat file gambar dummy."""
    img_path = tmp_path / "dummy_antenna.jpg"
    img = Image.new("RGB", (200, 200), color="blue")
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def dummy_template_and_project(tmp_path: Path) -> tuple[StorageManager, TemplateConfig, ProjectData]:
    """Fixture menyiapkan StorageManager, TemplateConfig, dan ProjectData dummy."""
    storage = StorageManager(base_dir=tmp_path / "data_storage")

    fields = [
        PhotoFieldConfig(
            field_id="fld_ant_1",
            label="Foto Antenna Sector 1",
            sheet_name="Antenna",
            cell_anchor="B5",
            sizing_mode="fit_to_cell",
        ),
        PhotoFieldConfig(
            field_id="fld_eq_1",
            label="Foto BBU & Rectifier",
            sheet_name="Equipment",
            cell_anchor="C10",
            sizing_mode="custom",
            custom_width=400,
            custom_height=300,
        ),
        PhotoFieldConfig(
            field_id="fld_tow_1",
            label="Foto Menara Tower",
            sheet_name="Tower",
            cell_anchor="D15",
            sizing_mode="fit_to_cell",
        ),
    ]

    template = TemplateConfig(
        template_id="tpl_telkom_bts",
        name="Template BTS Standar Telkom",
        template_file_path=str(tmp_path / "sample_template.xlsx"),
        fields=fields,
    )
    storage.save_template(template)

    project = ProjectData(
        project_id="proj_jkt_042",
        site_name="JKT-042 Pasar Minggu",
        template_id="tpl_telkom_bts",
        photo_assignments={},
    )
    storage.save_project(project)

    return storage, template, project


# =====================================================================
# 1. Pengujian DynamicPhotoRow
# =====================================================================

def test_dynamic_photo_row_init_and_status(qapp, dummy_image_file: str):
    """Verifikasi inisialisasi awal, badge info, thumbnail, dan status DynamicPhotoRow."""
    field_cfg = PhotoFieldConfig(
        field_id="fld_sector1",
        label="Foto Antenna Sector 1",
        sheet_name="Antenna",
        cell_anchor="B5",
        sizing_mode="fit_to_cell",
    )

    row = DynamicPhotoRow(field_config=field_cfg, row_index=1)
    assert row.lbl_index.text() == "01"
    assert row.lbl_field_name.text() == "Foto Antenna Sector 1"
    assert "Sheet: Antenna" in row.lbl_badge.text()
    assert "Sel: B5" in row.lbl_badge.text()
    assert "Auto-Fit" in row.lbl_badge.text()
    assert row.lbl_status.text() == DynamicRowStatus.EMPTY
    assert row.get_photo() is None
    assert row.get_field_id() == "fld_sector1"

    # Pasang foto valid
    row.set_photo(dummy_image_file)
    assert row.get_photo() == dummy_image_file
    assert row.lbl_status.text() == DynamicRowStatus.FILLED
    assert row.lbl_thumbnail.text() == ""  # Text kosong karena pixmap terpasang

    # Hapus / kosongkan foto
    row.clear_photo()
    assert row.get_photo() is None
    assert row.lbl_status.text() == DynamicRowStatus.EMPTY
    assert row.lbl_thumbnail.text() == "No Img"
    row.close()


def test_dynamic_photo_row_custom_sizing_badge(qapp):
    """Verifikasi tampilan badge info pada field dengan mode ukuran kustom."""
    field_cfg = PhotoFieldConfig(
        field_id="fld_custom",
        label="Foto Rack Perangkat",
        sheet_name="Equipment",
        cell_anchor="C8",
        sizing_mode="custom",
        custom_width=450,
        custom_height=350,
    )

    row = DynamicPhotoRow(field_config=field_cfg, row_index=3)
    assert "Kustom 450x350" in row.lbl_badge.text()
    assert row.lbl_index.text() == "03"
    row.close()


# =====================================================================
# 2. Pengujian NewProjectDialog & ProjectManagerDialog
# =====================================================================

def test_new_project_dialog_validation_and_creation(qapp, dummy_template_and_project, monkeypatch):
    """Memverifikasi validasi form dan pembuatan proyek baru di NewProjectDialog."""
    storage, template, _ = dummy_template_and_project

    warning_count = 0
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: warning_count + 1)

    dlg = NewProjectDialog(storage=storage)

    # 1. Nama site kosong
    dlg.edit_site_name.setText("")
    dlg._on_create_clicked()
    assert dlg.get_created_project() is None

    # 2. Nama site valid dan template terpilih
    dlg.edit_site_name.setText("BDG-012 Dago Telkom")
    dlg._on_create_clicked()

    created = dlg.get_created_project()
    assert created is not None
    assert created.site_name == "BDG-012 Dago Telkom"
    assert created.template_id == template.template_id

    # Pastikan tersimpan di storage
    saved_proj = storage.load_project(created.project_id)
    assert saved_proj.site_name == "BDG-012 Dago Telkom"
    dlg.close()


def test_project_manager_dialog_workflow(qapp, dummy_template_and_project, monkeypatch):
    """Memverifikasi tampilan daftar project, pemilihan project, dan hapus project di ProjectManagerDialog."""
    storage, template, project = dummy_template_and_project

    manager = ProjectManagerDialog(storage=storage)
    assert manager.table_projects.rowCount() >= 1
    assert manager.btn_open.isEnabled() is False

    # Pilih baris proyek
    manager.table_projects.selectRow(0)
    assert manager.btn_open.isEnabled() is True
    assert manager.btn_delete.isEnabled() is True

    # Buka site terpilih
    manager._on_open_project_clicked()
    selected = manager.get_selected_project()
    assert selected is not None
    assert selected.project_id == project.project_id

    # Hapus project dengan konfirmasi
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
    manager.table_projects.selectRow(0)
    manager._on_delete_project_clicked()

    # Pastikan project terhapus dari storage
    with pytest.raises(FileNotFoundError):
        storage.load_project(project.project_id)
    assert manager.table_projects.rowCount() == 0
    manager.close()


# =====================================================================
# 3. Pengujian MainWindow Dynamic Workspace & Auto-Persistence
# =====================================================================

def test_main_window_render_dynamic_workspace(qapp, dummy_template_and_project, dummy_image_file: str):
    """Memverifikasi render area kerja foto dinamis di MainWindow sesuai template aktif."""
    storage, template, project = dummy_template_and_project

    # Pre-assign foto ke field pertama
    project.photo_assignments["fld_ant_1"] = dummy_image_file
    storage.save_project(project)

    window = MainWindow(storage=storage)
    window.set_project(project)

    # Verifikasi header
    assert project.site_name in window.lbl_active_site.text()
    assert template.name in window.lbl_active_template.text()

    # Verifikasi render dynamic rows (3 field sesuai template)
    assert len(window.dynamic_rows) == 3
    assert window.dynamic_rows[0].get_field_id() == "fld_ant_1"
    assert window.dynamic_rows[0].get_photo() == dummy_image_file
    assert window.dynamic_rows[0].lbl_status.text() == DynamicRowStatus.FILLED

    assert window.dynamic_rows[1].get_field_id() == "fld_eq_1"
    assert window.dynamic_rows[1].get_photo() is None
    assert window.dynamic_rows[1].lbl_status.text() == DynamicRowStatus.EMPTY

    # Verifikasi statistik footer
    assert "Total: 3 field" in window.lbl_stats.text()
    assert "Foto Terisi: 1 / 3" in window.lbl_stats.text()
    window.close()


def test_main_window_auto_save_on_photo_changed(
    qapp,
    dummy_template_and_project,
    dummy_image_file: str,
    tmp_path: Path,
):
    """Memverifikasi fitur auto-save: setiap kali foto diubah/dihapus, langsung dicatat ke JSON project."""
    storage, template, project = dummy_template_and_project

    window = MainWindow(storage=storage)
    window.set_project(project)

    # 1. Pasang foto di field ke-2 (fld_eq_1)
    img2_path = str(tmp_path / "dummy_rack.jpg")
    Image.new("RGB", (100, 100), color="green").save(img2_path)

    window.dynamic_rows[1].set_photo(img2_path)

    # Verifikasi tersimpan langsung di ProjectData memory
    assert window.current_project.photo_assignments["fld_eq_1"] == img2_path

    # Verifikasi persistensi tersimpan di JSON lokal disk
    reloaded_project = storage.load_project(project.project_id)
    assert reloaded_project.photo_assignments.get("fld_eq_1") == img2_path
    assert "Foto Terisi: 1 / 3" in window.lbl_stats.text()

    # 2. Hapus foto dari field ke-2
    window.dynamic_rows[1].clear_photo()

    # Verifikasi foto terhapus dari persistensi disk
    reloaded_after_clear = storage.load_project(project.project_id)
    assert "fld_eq_1" not in reloaded_after_clear.photo_assignments
    assert "Foto Terisi: 0 / 3" in window.lbl_stats.text()
    window.close()


def test_main_window_switch_project(qapp, tmp_path: Path, dummy_image_file: str):
    """Memverifikasi perpindahan antar site/project secara mulus di MainWindow."""
    storage = StorageManager(base_dir=tmp_path / "switch_storage")

    # Template 1: 1 field
    t1 = TemplateConfig(
        template_id="t1",
        name="Template Ringkas",
        template_file_path=str(tmp_path / "t1.xlsx"),
        fields=[PhotoFieldConfig("f_only", "Foto Utama", "Sheet1", "A1")],
    )
    storage.save_template(t1)

    # Template 2: 2 field
    t2 = TemplateConfig(
        template_id="t2",
        name="Template Lengkap",
        template_file_path=str(tmp_path / "t2.xlsx"),
        fields=[
            PhotoFieldConfig("f_a", "Foto Sektor A", "Antenna", "B2"),
            PhotoFieldConfig("f_b", "Foto Sektor B", "Antenna", "B4"),
        ],
    )
    storage.save_template(t2)

    # Project 1 & Project 2
    p1 = ProjectData("p1", "Site Alpha", "t1")
    p2 = ProjectData("p2", "Site Beta", "t2")
    storage.save_project(p1)
    storage.save_project(p2)

    window = MainWindow(storage=storage)

    # Buka Project 1
    window.set_project(p1)
    assert "Site Alpha" in window.lbl_active_site.text()
    assert len(window.dynamic_rows) == 1
    assert window.dynamic_rows[0].lbl_field_name.text() == "Foto Utama"

    # Ganti ke Project 2
    window.set_project(p2)
    assert "Site Beta" in window.lbl_active_site.text()
    assert len(window.dynamic_rows) == 2
    assert window.dynamic_rows[0].lbl_field_name.text() == "Foto Sektor A"
    assert window.dynamic_rows[1].lbl_field_name.text() == "Foto Sektor B"
    window.close()

