"""
Unit tests for data models and StorageManager (Sesi 8).
"""

import json
from pathlib import Path
import pytest

from src.core.models import PhotoFieldConfig, ProjectData, TemplateConfig
from src.core.storage import StorageManager


# =====================================================================
# Model Tests
# =====================================================================

class TestModels:
    def test_photo_field_config_defaults_and_dict(self):
        field = PhotoFieldConfig(
            field_id="antenna_sec1",
            label="Foto Antena Sector 1",
            sheet_name="Antenna",
            cell_anchor="B5",
        )
        assert field.sizing_mode == "fit_to_cell"
        assert field.custom_width == 0
        assert field.custom_height == 0
        assert field.padding == 2
        assert field.alignment == "center"

        d = field.to_dict()
        assert d["field_id"] == "antenna_sec1"
        assert d["label"] == "Foto Antena Sector 1"
        assert d["sheet_name"] == "Antenna"
        assert d["cell_anchor"] == "B5"
        assert d["sizing_mode"] == "fit_to_cell"
        assert d["padding"] == 2
        assert d["alignment"] == "center"

        reconstructed = PhotoFieldConfig.from_dict(d)
        assert reconstructed == field

    def test_photo_field_config_custom_sizing(self):
        data = {
            "field_id": "field_2",
            "label": "Foto RUU",
            "sheet_name": "Equipment",
            "cell_anchor": "C10",
            "sizing_mode": "custom",
            "custom_width": 300,
            "custom_height": 200,
            "padding": 5,
        }
        field = PhotoFieldConfig.from_dict(data)
        assert field.sizing_mode == "custom"
        assert field.custom_width == 300
        assert field.custom_height == 200
        assert field.padding == 5

    def test_template_config_defaults_and_roundtrip(self):
        f1 = PhotoFieldConfig(
            field_id="f1",
            label="Label 1",
            sheet_name="Sheet1",
            cell_anchor="A1",
        )
        template = TemplateConfig(
            template_id="tpl_standard",
            name="Template Standar BTS",
            template_file_path="/templates/bts_report.xlsx",
            fields=[f1],
        )

        assert template.created_at != ""
        assert template.updated_at != ""
        assert template.template_id == "tpl_standard"

        d = template.to_dict()
        assert len(d["fields"]) == 1
        assert d["fields"][0]["field_id"] == "f1"

        loaded = TemplateConfig.from_dict(d)
        assert loaded.template_id == template.template_id
        assert loaded.name == template.name
        assert loaded.template_file_path == template.template_file_path
        assert len(loaded.fields) == 1
        assert loaded.fields[0].field_id == "f1"
        assert loaded.fields[0].label == "Label 1"

    def test_project_data_defaults_and_roundtrip(self):
        project = ProjectData(
            project_id="proj_jkt001",
            site_name="JKT-SEL-001",
            template_id="tpl_standard",
            photo_assignments={"f1": "/photos/pic1.jpg", "f2": "/photos/pic2.jpg"},
            output_dir="/reports/jkt001",
        )

        assert project.created_at != ""
        assert project.last_exported_at is None

        d = project.to_dict()
        assert d["project_id"] == "proj_jkt001"
        assert d["site_name"] == "JKT-SEL-001"
        assert d["photo_assignments"]["f1"] == "/photos/pic1.jpg"
        assert d["last_exported_at"] is None

        # Add export time
        d["last_exported_at"] = "2026-10-18T10:00:00"
        loaded = ProjectData.from_dict(d)
        assert loaded.last_exported_at == "2026-10-18T10:00:00"
        assert loaded.photo_assignments["f2"] == "/photos/pic2.jpg"

    def test_photo_field_config_text_type_and_roundtrip(self):
        field = PhotoFieldConfig(
            field_id="txt_site_id",
            label="ID Site Telkom",
            sheet_name="Site_Info",
            cell_anchor="C3",
            field_type="text",
            default_text="JKT-001",
        )
        assert field.field_type == "text"
        assert field.default_text == "JKT-001"

        d = field.to_dict()
        assert d["field_type"] == "text"
        assert d["default_text"] == "JKT-001"

        reconstructed = PhotoFieldConfig.from_dict(d)
        assert reconstructed == field

    def test_project_data_text_assignments_roundtrip(self):
        project = ProjectData(
            project_id="proj_text_test",
            site_name="BDG-002",
            template_id="tpl_text_std",
            photo_assignments={"p1": "/photos/p1.jpg"},
            text_assignments={"t1": "Teknisi: Ahmad", "t2": "Tinggi: 72M"},
        )
        d = project.to_dict()
        assert d["text_assignments"] == {"t1": "Teknisi: Ahmad", "t2": "Tinggi: 72M"}

        loaded = ProjectData.from_dict(d)
        assert loaded.text_assignments == {"t1": "Teknisi: Ahmad", "t2": "Tinggi: 72M"}


# =====================================================================
# StorageManager Tests
# =====================================================================

@pytest.fixture
def storage(tmp_path: Path) -> StorageManager:
    return StorageManager(base_dir=tmp_path)


class TestStorageManager:
    def test_directory_initialization(self, tmp_path: Path):
        base = tmp_path / "custom_data"
        mgr = StorageManager(base_dir=base)
        assert mgr.templates_dir.is_dir()
        assert mgr.projects_dir.is_dir()
        assert mgr.templates_dir == base / "templates"
        assert mgr.projects_dir == base / "projects"

    def test_save_and_load_template(self, storage: StorageManager):
        f1 = PhotoFieldConfig(
            field_id="field_ant",
            label="Antena",
            sheet_name="Main",
            cell_anchor="B2",
            sizing_mode="fit_to_cell",
            padding=4,
        )
        template = TemplateConfig(
            template_id="tpl_bts_01",
            name="Template BTS 01",
            template_file_path="/templates/bts.xlsx",
            fields=[f1],
        )

        saved_path = storage.save_template(template)
        assert saved_path.is_file()
        assert saved_path.name == "tpl_bts_01.json"

        loaded = storage.load_template("tpl_bts_01")
        assert loaded.template_id == "tpl_bts_01"
        assert loaded.name == "Template BTS 01"
        assert len(loaded.fields) == 1
        assert loaded.fields[0].field_id == "field_ant"
        assert loaded.fields[0].padding == 4

    def test_load_non_existent_template_raises_error(self, storage: StorageManager):
        with pytest.raises(FileNotFoundError):
            storage.load_template("non_existent_id")

    def test_save_template_empty_id_raises_error(self, storage: StorageManager):
        template = TemplateConfig(
            template_id="",
            name="No ID",
            template_file_path="",
        )
        with pytest.raises(ValueError):
            storage.save_template(template)

    def test_list_templates(self, storage: StorageManager):
        assert storage.list_templates() == []

        for i in range(3):
            tpl = TemplateConfig(
                template_id=f"tpl_{i}",
                name=f"Template {i}",
                template_file_path=f"/path/{i}.xlsx",
            )
            storage.save_template(tpl)

        templates = storage.list_templates()
        assert len(templates) == 3
        ids = {t.template_id for t in templates}
        assert ids == {"tpl_0", "tpl_1", "tpl_2"}

    def test_delete_template(self, storage: StorageManager):
        tpl = TemplateConfig(
            template_id="tpl_del",
            name="Delete Me",
            template_file_path="/path/del.xlsx",
        )
        storage.save_template(tpl)
        assert storage.delete_template("tpl_del") is True
        assert storage.delete_template("tpl_del") is False

        with pytest.raises(FileNotFoundError):
            storage.load_template("tpl_del")

    def test_save_and_load_project(self, storage: StorageManager):
        project = ProjectData(
            project_id="proj_alpha",
            site_name="Site Alpha",
            template_id="tpl_bts_01",
            photo_assignments={"f1": "/images/a.jpg"},
            output_dir="/out/alpha",
            last_exported_at="2026-10-18T12:00:00",
        )

        saved_path = storage.save_project(project)
        assert saved_path.is_file()
        assert saved_path.name == "proj_alpha.json"

        loaded = storage.load_project("proj_alpha")
        assert loaded.project_id == "proj_alpha"
        assert loaded.site_name == "Site Alpha"
        assert loaded.template_id == "tpl_bts_01"
        assert loaded.photo_assignments == {"f1": "/images/a.jpg"}
        assert loaded.output_dir == "/out/alpha"
        assert loaded.last_exported_at == "2026-10-18T12:00:00"

    def test_load_non_existent_project_raises_error(self, storage: StorageManager):
        with pytest.raises(FileNotFoundError):
            storage.load_project("non_existent_project")

    def test_save_project_empty_id_raises_error(self, storage: StorageManager):
        project = ProjectData(
            project_id="   ",
            site_name="Site Test",
            template_id="tpl_test",
        )
        with pytest.raises(ValueError):
            storage.save_project(project)

    def test_list_projects(self, storage: StorageManager):
        assert storage.list_projects() == []

        for i in range(2):
            proj = ProjectData(
                project_id=f"proj_{i}",
                site_name=f"Site {i}",
                template_id="tpl_std",
            )
            storage.save_project(proj)

        projects = storage.list_projects()
        assert len(projects) == 2
        ids = {p.project_id for p in projects}
        assert ids == {"proj_0", "proj_1"}

    def test_delete_project(self, storage: StorageManager):
        proj = ProjectData(
            project_id="proj_del",
            site_name="Site Del",
            template_id="tpl_std",
        )
        storage.save_project(proj)
        assert storage.delete_project("proj_del") is True
        assert storage.delete_project("proj_del") is False

        with pytest.raises(FileNotFoundError):
            storage.load_project("proj_del")

    def test_corrupt_template_file_handling(self, storage: StorageManager):
        # Create a corrupt json file in templates_dir
        corrupt_path = storage.templates_dir / "corrupt_tpl.json"
        corrupt_path.write_text("{invalid json content!!!", encoding="utf-8")

        # Loading corrupted directly should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            storage.load_template("corrupt_tpl")
        assert "Gagal memuat template korup" in str(exc_info.value)

        # list_templates should skip the corrupt file without throwing
        tpl_valid = TemplateConfig(
            template_id="valid_tpl",
            name="Valid",
            template_file_path="/valid.xlsx",
        )
        storage.save_template(tpl_valid)

        templates = storage.list_templates()
        assert len(templates) == 1
        assert templates[0].template_id == "valid_tpl"

    def test_corrupt_project_file_handling(self, storage: StorageManager):
        # Create a corrupt json file in projects_dir
        corrupt_path = storage.projects_dir / "corrupt_proj.json"
        corrupt_path.write_text("['not', 'a', 'dictionary']", encoding="utf-8")

        # Loading corrupted directly should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            storage.load_project("corrupt_proj")
        assert "Gagal memuat project korup" in str(exc_info.value)

        # list_projects should skip the corrupt file without throwing
        proj_valid = ProjectData(
            project_id="valid_proj",
            site_name="Valid Site",
            template_id="tpl_valid",
        )
        storage.save_project(proj_valid)

        projects = storage.list_projects()
        assert len(projects) == 1
        assert projects[0].project_id == "valid_proj"

