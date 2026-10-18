"""
Photo Rename Studio - Data Models untuk Template dan Project Storage
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PhotoFieldConfig:
    """
    Konfigurasi field penempatan foto pada sheet Excel.
    """
    field_id: str
    label: str
    sheet_name: str
    cell_anchor: str
    field_type: str = "photo"  # "photo" | "text"
    sizing_mode: str = "fit_to_cell"  # "fit_to_cell" | "custom"
    custom_width: int = 0
    custom_height: int = 0
    padding: int = 2
    alignment: str = "center"  # "center" | "top-left"
    default_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Konversi model konfigurasi field ke dictionary."""
        return {
            "field_id": self.field_id,
            "label": self.label,
            "sheet_name": self.sheet_name,
            "cell_anchor": self.cell_anchor,
            "field_type": self.field_type,
            "sizing_mode": self.sizing_mode,
            "custom_width": self.custom_width,
            "custom_height": self.custom_height,
            "padding": self.padding,
            "alignment": self.alignment,
            "default_text": self.default_text,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhotoFieldConfig":
        """Buat PhotoFieldConfig dari dictionary."""
        return cls(
            field_id=str(data.get("field_id", "")),
            label=str(data.get("label", "")),
            sheet_name=str(data.get("sheet_name", "")),
            cell_anchor=str(data.get("cell_anchor", "")),
            field_type=str(data.get("field_type", "photo")),
            sizing_mode=str(data.get("sizing_mode", "fit_to_cell")),
            custom_width=int(data.get("custom_width", 0)),
            custom_height=int(data.get("custom_height", 0)),
            padding=int(data.get("padding", 2)),
            alignment=str(data.get("alignment", "center")),
            default_text=str(data.get("default_text", "")),
        )


@dataclass
class TemplateConfig:
    """
    Konfigurasi template laporan Excel beserta aturan penempatan field foto atau teks.
    """
    template_id: str
    name: str
    template_file_path: str
    fields: List[PhotoFieldConfig] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        now_iso = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now_iso
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Konversi TemplateConfig ke dictionary."""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "template_file_path": self.template_file_path,
            "fields": [f.to_dict() for f in self.fields],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateConfig":
        """Buat TemplateConfig dari dictionary."""
        raw_fields = data.get("fields", [])
        parsed_fields = [
            PhotoFieldConfig.from_dict(item) if isinstance(item, dict) else item
            for item in raw_fields
        ]
        return cls(
            template_id=str(data.get("template_id", "")),
            name=str(data.get("name", "")),
            template_file_path=str(data.get("template_file_path", "")),
            fields=parsed_fields,
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )


@dataclass
class ProjectData:
    """
    State data pengerjaan site yang mengasosiasikan foto dan teks dengan field template.
    """
    project_id: str
    site_name: str
    template_id: str
    photo_assignments: Dict[str, str] = field(default_factory=dict)
    text_assignments: Dict[str, str] = field(default_factory=dict)
    output_dir: str = ""
    created_at: str = ""
    last_exported_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Konversi ProjectData ke dictionary."""
        return {
            "project_id": self.project_id,
            "site_name": self.site_name,
            "template_id": self.template_id,
            "photo_assignments": dict(self.photo_assignments),
            "text_assignments": dict(self.text_assignments),
            "output_dir": self.output_dir,
            "created_at": self.created_at,
            "last_exported_at": self.last_exported_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectData":
        """Buat ProjectData dari dictionary."""
        last_exp = data.get("last_exported_at")
        return cls(
            project_id=str(data.get("project_id", "")),
            site_name=str(data.get("site_name", "")),
            template_id=str(data.get("template_id", "")),
            photo_assignments=dict(data.get("photo_assignments", {})),
            text_assignments=dict(data.get("text_assignments", {})),
            output_dir=str(data.get("output_dir", "")),
            created_at=str(data.get("created_at", "")),
            last_exported_at=str(last_exp) if last_exp is not None else None,
        )

