"""
Photo Rename Studio - Data Models untuk Template dan Project Storage
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


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
class SiteDocument:
    """
    Sub-dokumen laporan dalam satu Proyek Site yang mewakili satu konfigurasi template Excel.
    Memungkinkan 1 site memiliki lebih dari 1 template dokumen (misal: ATP, CME, BAST).
    """
    doc_id: str
    template_id: str
    name: str = ""
    photo_assignments: Dict[str, str] = field(default_factory=dict)
    text_assignments: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.doc_id:
            self.doc_id = f"doc_{uuid.uuid4().hex[:6]}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Konversi SiteDocument ke dictionary."""
        return {
            "doc_id": self.doc_id,
            "template_id": self.template_id,
            "name": self.name,
            "photo_assignments": dict(self.photo_assignments),
            "text_assignments": dict(self.text_assignments),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SiteDocument":
        """Buat SiteDocument dari dictionary."""
        return cls(
            doc_id=str(data.get("doc_id", "")),
            template_id=str(data.get("template_id", "")),
            name=str(data.get("name", "")),
            photo_assignments=dict(data.get("photo_assignments", {})),
            text_assignments=dict(data.get("text_assignments", {})),
            created_at=str(data.get("created_at", "")),
        )


@dataclass
class ProjectData:
    """
    State data pengerjaan site yang mengasosiasikan foto dan teks dengan field template.
    Mendukung arsitektur multi-dokumen (1 Site -> banyak template dokumen Excel).
    """
    project_id: str
    site_name: str
    template_id: str
    photo_assignments: Dict[str, str] = field(default_factory=dict)
    text_assignments: Dict[str, str] = field(default_factory=dict)
    output_dir: str = ""
    created_at: str = ""
    last_exported_at: Optional[str] = None
    documents: List[SiteDocument] = field(default_factory=list)
    active_doc_id: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

        # Migrasi/Inisialisasi Multi-Document:
        # Jika belum ada sub-dokumen di list tapi template_id ada, buat dokumen default
        if not self.documents and self.template_id:
            default_doc = SiteDocument(
                doc_id=self.active_doc_id or "doc_default",
                template_id=self.template_id,
                name="",
                photo_assignments=dict(self.photo_assignments),
                text_assignments=dict(self.text_assignments),
                created_at=self.created_at,
            )
            self.documents = [default_doc]
            self.active_doc_id = default_doc.doc_id
        elif self.documents:
            # Pastikan active_doc_id valid
            doc_ids = [d.doc_id for d in self.documents]
            if not self.active_doc_id or self.active_doc_id not in doc_ids:
                self.active_doc_id = self.documents[0].doc_id
            # Sinkronkan active document ke top-level attributes untuk backward compatibility
            self._sync_to_top_level()

    def _sync_to_top_level(self) -> None:
        """Sinkronkan data dokumen aktif ke top-level fields untuk kompatibilitas mundur."""
        active_doc = self.get_active_document()
        if active_doc:
            self.template_id = active_doc.template_id
            self.photo_assignments = active_doc.photo_assignments
            self.text_assignments = active_doc.text_assignments

    def get_active_document(self) -> Optional[SiteDocument]:
        """Mengambil SiteDocument yang sedang aktif."""
        for doc in self.documents:
            if doc.doc_id == self.active_doc_id:
                return doc
        if self.documents:
            return self.documents[0]
        return None

    def get_document_by_id(self, doc_id: str) -> Optional[SiteDocument]:
        """Mencari SiteDocument berdasarkan ID."""
        for doc in self.documents:
            if doc.doc_id == doc_id:
                return doc
        return None

    def add_document(self, template_id: str, name: str = "", doc_id: Optional[str] = None) -> SiteDocument:
        """Menambahkan template dokumen baru ke proyek site ini."""
        new_doc_id = doc_id or f"doc_{uuid.uuid4().hex[:6]}"
        new_doc = SiteDocument(
            doc_id=new_doc_id,
            template_id=template_id,
            name=name,
            photo_assignments={},
            text_assignments={},
            created_at=datetime.now().isoformat(),
        )
        self.documents.append(new_doc)
        return new_doc

    def switch_document(self, doc_id: str) -> bool:
        """Berpindah ke dokumen tertentu dan sinkronkan data aktif."""
        target_doc = self.get_document_by_id(doc_id)
        if not target_doc:
            return False
        self.active_doc_id = doc_id
        self._sync_to_top_level()
        return True

    def remove_document(self, doc_id: str) -> bool:
        """Menghapus sub-dokumen dari site. Dokumen terakhir tidak boleh dihapus."""
        if len(self.documents) <= 1:
            return False
        doc_to_remove = self.get_document_by_id(doc_id)
        if not doc_to_remove:
            return False
        self.documents = [d for d in self.documents if d.doc_id != doc_id]
        if self.active_doc_id == doc_id:
            self.active_doc_id = self.documents[0].doc_id
            self._sync_to_top_level()
        return True

    def rename_document(self, doc_id: str, new_name: str) -> bool:
        """Mengubah nama dokumen."""
        doc = self.get_document_by_id(doc_id)
        if doc:
            doc.name = new_name.strip()
            return True
        return False

    def sync_active_assignments(
        self,
        photo_assignments: Optional[Dict[str, str]] = None,
        text_assignments: Optional[Dict[str, str]] = None,
    ) -> None:
        """Sinkronkan pemetaan foto dan teks aktif ke SiteDocument aktif."""
        active_doc = self.get_active_document()
        if photo_assignments is not None:
            self.photo_assignments = dict(photo_assignments)
            if active_doc:
                active_doc.photo_assignments = dict(photo_assignments)
        if text_assignments is not None:
            self.text_assignments = dict(text_assignments)
            if active_doc:
                active_doc.text_assignments = dict(text_assignments)

    def to_dict(self) -> Dict[str, Any]:
        """Konversi ProjectData ke dictionary."""
        self._sync_to_top_level()
        return {
            "project_id": self.project_id,
            "site_name": self.site_name,
            "template_id": self.template_id,
            "photo_assignments": dict(self.photo_assignments),
            "text_assignments": dict(self.text_assignments),
            "output_dir": self.output_dir,
            "created_at": self.created_at,
            "last_exported_at": self.last_exported_at,
            "active_doc_id": self.active_doc_id,
            "documents": [d.to_dict() for d in self.documents],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectData":
        """Buat ProjectData dari dictionary dengan backward compatibility."""
        last_exp = data.get("last_exported_at")
        raw_docs = data.get("documents", [])
        parsed_docs = [
            SiteDocument.from_dict(item) if isinstance(item, dict) else item
            for item in raw_docs
        ]
        return cls(
            project_id=str(data.get("project_id", "")),
            site_name=str(data.get("site_name", "")),
            template_id=str(data.get("template_id", "")),
            photo_assignments=dict(data.get("photo_assignments", {})),
            text_assignments=dict(data.get("text_assignments", {})),
            output_dir=str(data.get("output_dir", "")),
            created_at=str(data.get("created_at", "")),
            last_exported_at=str(last_exp) if last_exp is not None else None,
            documents=parsed_docs,
            active_doc_id=str(data.get("active_doc_id", "")),
        )

