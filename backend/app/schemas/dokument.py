"""
Pydantic-Schemas für API-Anfragen und -Antworten.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DokumentBase(BaseModel):
    """Basis-Schema für Dokumente."""
    dateiname: str


class DokumentCreate(DokumentBase):
    """Schema für das Erstellen eines Dokuments."""
    pass


class DokumentUpdate(BaseModel):
    """Schema für das Aktualisieren eines Dokuments."""
    kategorie: Optional[str] = None
    metadaten: Optional[Dict[str, Any]] = None


class DokumentResponse(DokumentBase):
    """Schema für die Dokumentantwort."""
    id: int
    kategorie: Optional[str] = None
    pfad: str
    inhalt_vorschau: Optional[str] = None
    erstellt_am: str
    metadaten: Optional[Dict[str, Any]] = {}
    
    class Config:
        """Pydantic-Konfiguration."""
        orm_mode = True


class DokumentList(BaseModel):
    """Schema für eine Liste von Dokumenten."""
    dokumente: List[DokumentResponse]
    total: int


class MetadatenFeldBase(BaseModel):
    """Basis-Schema für Metadatenfelder."""
    feldname: str
    beschreibung: str


class MetadatenFeldCreate(MetadatenFeldBase):
    """Schema für das Erstellen eines Metadatenfelds."""
    pass


class MetadatenFeldResponse(MetadatenFeldBase):
    """Schema für die Metadatenfeld-Antwort."""
    id: int
    erstellt_am: Optional[str] = None


class MetadatenFeldList(BaseModel):
    """Schema für eine Liste von Metadatenfeldern."""
    felder: List[MetadatenFeldResponse]


class ErrorResponse(BaseModel):
    """Schema für Fehlerantworten."""
    detail: str


class SuccessResponse(BaseModel):
    """Schema für Erfolgsantworten."""
    success: bool
    message: str
    data: Optional[Any] = None