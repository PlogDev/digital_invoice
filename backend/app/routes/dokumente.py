"""
API-Routen für die Dokumentenverwaltung mit OCR-Integration beim Scannen.
"""

import logging
import os
import shutil
from pathlib import Path as PathLib
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from ..config.settings import PDF_CATEGORIES, PDF_INPUT_DIR
from ..models.dokument import Dokument, MetadatenFeld
from ..schemas.dokument import (
    DokumentList,
    DokumentResponse,
    DokumentUpdate,
    ErrorResponse,
    MetadatenFeldCreate,
    MetadatenFeldList,
    MetadatenFeldResponse,
    SuccessResponse,
)
from ..services.ocr_service import OCRService
from ..services.storage_service import StorageService

# Logger einrichten
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dokumente", tags=["Dokumente"])


@router.get("/", response_model=DokumentList)
async def get_dokumente():
    """
    Ruft alle Dokumente ab. OCR wird automatisch im Background verarbeitet.
    """
    # Einfach alle Dokumente aus der DB abrufen
    # OCR läuft im Background-Scheduler
    dokumente = Dokument.get_all()
    
    return {
        "dokumente": [d.to_dict() for d in dokumente],
        "total": len(dokumente)
    }


@router.get("/{dokument_id}", response_model=DokumentResponse)
async def get_dokument(dokument_id: int = Path(..., description="Die ID des Dokuments")):
    """Ruft ein einzelnes Dokument anhand seiner ID ab."""
    dokument = Dokument.get_by_id(dokument_id)
    
    if not dokument:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    return dokument.to_dict()


@router.get("/file/{dokument_id}")
async def get_dokument_file(dokument_id: int):
    """Liefert die PDF-Datei eines Dokuments (bereits OCR-verarbeitet)."""
    dokument = Dokument.get_by_id(dokument_id)
    
    if not dokument:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    file_path = dokument.pfad
    
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404, 
            detail=f"PDF-Datei nicht gefunden: {file_path}"
        )
    
    return FileResponse(
        path=file_path, 
        filename=dokument.dateiname,
        media_type="application/pdf"
    )


@router.post("/upload", response_model=DokumentResponse)
async def upload_dokument(file: UploadFile = File(...)):
    """
    Lädt ein neues PDF-Dokument hoch. OCR wird automatisch im Background verarbeitet.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien werden unterstützt")
    
    # Datei speichern
    file_path = os.path.join(PDF_INPUT_DIR, file.filename)
    
    try:
        # Datei ins Input-Verzeichnis speichern
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        logger.info(f"Datei hochgeladen: {file.filename} - OCR wird im Background verarbeitet")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Datei: {str(e)}")
    
    # Einfache Vorschau ohne OCR (wird später vom Scheduler aktualisiert)
    try:
        basic_preview = OCRService.extract_preview_text(file_path, max_chars=100)
    except:
        basic_preview = f"Hochgeladen: {file.filename} - OCR wird verarbeitet..."
    
    # In DB speichern
    dokument = Dokument.create(
        dateiname=file.filename,
        pfad=file_path,
        inhalt_vorschau=basic_preview
    )
    
    return dokument.to_dict()


@router.put("/{dokument_id}/kategorisieren", response_model=DokumentResponse)
async def kategorisiere_dokument(
    update_data: DokumentUpdate,
    dokument_id: int = Path(..., description="Die ID des Dokuments")
):
    """
    Kategorisiert ein Dokument und verschiebt es (ohne weitere OCR-Verarbeitung).
    """
    dokument = Dokument.get_by_id(dokument_id)
    
    if not dokument:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    if update_data.kategorie and update_data.kategorie not in PDF_CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Ungültige Kategorie: {update_data.kategorie}")
    
    # Wenn Kategorie geändert wird, PDF verschieben (OCR bereits durchgeführt)
    if update_data.kategorie and update_data.kategorie != dokument.kategorie:
        success, neuer_pfad = StorageService.move_file_only(
            dokument.pfad, 
            update_data.kategorie
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Fehler beim Verschieben der Datei")
        
        dokument.kategorie = update_data.kategorie
        dokument.pfad = neuer_pfad
        
        # Vorschau aus der bereits OCR-verarbeiteten PDF kann aktualisiert werden
        aktualisierte_vorschau = OCRService.extract_preview_text(neuer_pfad, max_chars=300)
        if aktualisierte_vorschau:
            dokument.inhalt_vorschau = aktualisierte_vorschau
    
    # Metadaten aktualisieren, falls vorhanden
    if update_data.metadaten:
        dokument.metadaten = update_data.metadaten
    
    # DB aktualisieren
    dokument.update()
    
    return dokument.to_dict()


@router.delete("/{dokument_id}", response_model=SuccessResponse)
async def delete_dokument(dokument_id: int = Path(..., description="Die ID des Dokuments")):
    """Löscht ein Dokument aus der Datenbank und die Datei."""
    dokument = Dokument.get_by_id(dokument_id)
    
    if not dokument:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    # Datei und OCR-Marker löschen
    StorageService.delete_file(dokument.pfad)
    
    # Aus DB löschen
    success = dokument.delete()
    
    if not success:
        raise HTTPException(status_code=500, detail="Fehler beim Löschen des Dokuments")
    
    return {
        "success": True,
        "message": f"Dokument {dokument.dateiname} wurde gelöscht",
        "data": {"id": dokument_id}
    }


# Metadatenfelder-Routen (unverändert)
@router.get("/metadaten/felder", response_model=MetadatenFeldList)
async def get_metadatenfelder():
    """Ruft alle verfügbaren Metadatenfelder ab."""
    felder = MetadatenFeld.get_all()
    
    return {"felder": felder}


@router.post("/metadaten/felder", response_model=SuccessResponse)
async def create_metadatenfeld(feld: MetadatenFeldCreate):
    """Erstellt ein neues Metadatenfeld."""
    success = MetadatenFeld.create(feld.feldname, feld.beschreibung)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Feld '{feld.feldname}' existiert bereits")
    
    return {
        "success": True,
        "message": f"Metadatenfeld '{feld.feldname}' wurde erstellt",
        "data": {"feldname": feld.feldname}
    }


@router.delete("/metadaten/felder/{feld_id}", response_model=SuccessResponse)
async def delete_metadatenfeld(feld_id: int = Path(..., description="Die ID des Metadatenfelds")):
    """Löscht ein Metadatenfeld."""
    success = MetadatenFeld.delete(feld_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Metadatenfeld nicht gefunden")
    
    return {
        "success": True,
        "message": "Metadatenfeld wurde gelöscht",
        "data": {"id": feld_id}
    }