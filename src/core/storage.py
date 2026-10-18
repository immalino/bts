"""
Photo Rename Studio - Local Storage Manager untuk Template & Project
"""

import json
import logging
import os
from pathlib import Path
import shutil
from typing import List, Optional, Union

from src.config import BASE_DIR, DATA_DIR
from src.core.models import ProjectData, TemplateConfig

logger = logging.getLogger(__name__)


class StorageManager:
    """
    Manajer persistensi data berbasis file JSON lokal untuk Template dan Project.
    """

    def __init__(self, base_dir: Optional[Union[str, Path]] = None) -> None:
        """
        Inisialisasi StorageManager.

        Args:
            base_dir: Direktori dasar penyimpanan. Jika None, default ke `<BASE_DIR>/data`.
        """
        if base_dir is None:
            self.base_dir = DATA_DIR
        else:
            self.base_dir = Path(base_dir)

        self.templates_dir = self.base_dir / "templates"
        self.template_files_dir = self.templates_dir / "files"
        self.projects_dir = self.base_dir / "projects"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Pastikan direktori penyimpanan template dan project tersedia."""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.template_files_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _write_json_atomic(self, file_path: Path, data: dict) -> None:
        """Tulis data dictionary ke file JSON secara atomik menggunakan file sementara."""
        temp_file = file_path.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_file, file_path)
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    # ==================== Template Operations ====================

    def _template_file(self, template_id: str) -> Path:
        clean_id = template_id.strip()
        if not clean_id:
            raise ValueError("template_id tidak boleh kosong.")
        return self.templates_dir / f"{clean_id}.json"

    def save_template(self, template: TemplateConfig) -> Path:
        """
        Simpan atau perbarui TemplateConfig ke disk sebagai file JSON.
        Jika berkas Excel template ada, salin berkas ke subfolder internal 'files/'
        agar template bersifat mandiri dan portabel.

        Args:
            template: Objek konfigurasi template.

        Returns:
            Path file JSON yang tersimpan.
        """
        # Salin file master Excel jika ada di disk dan belum ada di template_files_dir
        if template.template_file_path and os.path.isfile(template.template_file_path):
            try:
                src_path = Path(template.template_file_path).resolve()
                suffix = src_path.suffix or ".xlsx"
                dest_path = (self.template_files_dir / f"{template.template_id}{suffix}").resolve()
                if src_path != dest_path:
                    shutil.copy2(src_path, dest_path)
                    template.template_file_path = str(dest_path)
            except Exception as e:
                logger.warning("Gagal menyalin berkas template Excel ke internal storage: %s", e)

        target_file = self._template_file(template.template_id)
        self._write_json_atomic(target_file, template.to_dict())
        return target_file

    def load_template(self, template_id: str) -> TemplateConfig:
        """
        Muat TemplateConfig dari file JSON berdasarkan ID.

        Args:
            template_id: ID template yang dicari.

        Returns:
            Objek TemplateConfig.

        Raises:
            FileNotFoundError: Jika berkas template tidak ditemukan.
            ValueError: Jika berkas JSON korup atau format tidak sesuai.
        """
        target_file = self._template_file(template_id)
        if not target_file.is_file():
            raise FileNotFoundError(f"Template '{template_id}' tidak ditemukan di {target_file}.")

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Format JSON template tidak valid (harus object/dict).")
            tpl = TemplateConfig.from_dict(data)

            # Jika file template Excel tidak ditemukan pada path yang tercatat (misal path absolut PC lama),
            # cari file cadangan lokal di self.template_files_dir
            if not os.path.isfile(tpl.template_file_path):
                for match in self.template_files_dir.glob(f"{template_id}.*"):
                    if match.is_file():
                        tpl.template_file_path = str(match.resolve())
                        break

            return tpl
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                raise
            raise ValueError(f"Gagal memuat template korup '{template_id}': {e}") from e

    def list_templates(self) -> List[TemplateConfig]:
        """
        Daftar seluruh TemplateConfig yang tersimpan secara lokal.
        Berkas yang korup akan dilewati dan dicatat ke log peringatan.

        Returns:
            Daftar objek TemplateConfig.
        """
        templates: List[TemplateConfig] = []
        if not self.templates_dir.is_dir():
            return templates

        for path in sorted(self.templates_dir.glob("*.json")):
            template_id = path.stem
            try:
                templates.append(self.load_template(template_id))
            except Exception as e:
                logger.warning("Mengabaikan template korup '%s': %s", path.name, e)

        return templates

    def delete_template(self, template_id: str) -> bool:
        """
        Hapus file JSON template dan file master Excel terkait berdasarkan ID.

        Args:
            template_id: ID template yang akan dihapus.

        Returns:
            True jika berhasil dihapus, False jika berkas tidak ditemukan.
        """
        target_file = self._template_file(template_id)
        deleted = False
        if target_file.is_file():
            target_file.unlink()
            deleted = True

        # Hapus juga file master Excel jika ada di template_files_dir
        for match in self.template_files_dir.glob(f"{template_id}.*"):
            try:
                match.unlink()
                deleted = True
            except OSError:
                pass

        return deleted

    # ==================== Project Operations ====================

    def _project_file(self, project_id: str) -> Path:
        clean_id = project_id.strip()
        if not clean_id:
            raise ValueError("project_id tidak boleh kosong.")
        return self.projects_dir / f"{clean_id}.json"

    def save_project(self, project: ProjectData) -> Path:
        """
        Simpan atau perbarui ProjectData ke disk sebagai file JSON.

        Args:
            project: Objek data proyek.

        Returns:
            Path file JSON yang tersimpan.
        """
        target_file = self._project_file(project.project_id)
        self._write_json_atomic(target_file, project.to_dict())
        return target_file

    def load_project(self, project_id: str) -> ProjectData:
        """
        Muat ProjectData dari file JSON berdasarkan ID.

        Args:
            project_id: ID project yang dicari.

        Returns:
            Objek ProjectData.

        Raises:
            FileNotFoundError: Jika berkas project tidak ditemukan.
            ValueError: Jika berkas JSON korup atau format tidak sesuai.
        """
        target_file = self._project_file(project_id)
        if not target_file.is_file():
            raise FileNotFoundError(f"Project '{project_id}' tidak ditemukan di {target_file}.")

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Format JSON project tidak valid (harus object/dict).")
            return ProjectData.from_dict(data)
        except Exception as e:
            if isinstance(e, FileNotFoundError):
                raise
            raise ValueError(f"Gagal memuat project korup '{project_id}': {e}") from e

    def list_projects(self) -> List[ProjectData]:
        """
        Daftar seluruh ProjectData yang tersimpan secara lokal.
        Berkas yang korup akan dilewati dan dicatat ke log peringatan.

        Returns:
            Daftar objek ProjectData.
        """
        projects: List[ProjectData] = []
        if not self.projects_dir.is_dir():
            return projects

        for path in sorted(self.projects_dir.glob("*.json")):
            project_id = path.stem
            try:
                projects.append(self.load_project(project_id))
            except Exception as e:
                logger.warning("Mengabaikan project korup '%s': %s", path.name, e)

        return projects

    def delete_project(self, project_id: str) -> bool:
        """
        Hapus file JSON project berdasarkan ID.

        Args:
            project_id: ID project yang akan dihapus.

        Returns:
            True jika berhasil dihapus, False jika berkas tidak ditemukan.
        """
        target_file = self._project_file(project_id)
        if target_file.is_file():
            target_file.unlink()
            return True
        return False

