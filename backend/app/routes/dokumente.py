"""
API-Routen für die Dokumentenverwaltung mit PostgreSQL-Repository-Pattern.
Aktualisiert von SQLite auf PostgreSQL mit neuer Kategorien-Struktur.
"""

import logging

logger = logging.getLogger(__name__)
logger.info("🔍 dokumente.py wurde neu geladen!")

import logging
import os
import shutil
from pathlib import Path as PathLib
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from ..config.settings import PDF_INPUT_DIR
from ..database.seed_data import get_unterkategorie_by_name
from ..repositories.dokument_repository import DokumentRepository
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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dokumente", tags=["Dokumente"])


@router.get("/", response_model=DokumentList)
async def get_dokumente():
    """
    Ruft alle Dokumente ab und scannt nach neuen Dateien im Eingangsverzeichnis.
    OCR wird automatisch beim Scannen neuer Dateien durchgeführt.
    """
    
    # Neue PDF-Dateien prüfen und mit OCR verarbeiten
    neue_dateien = StorageService.get_input_files()  # OCR wird hier automatisch durchgeführt
    
    for datei in neue_dateien:
        # Prüfen, ob Datei bereits in DB (mit neuem Repository)
        vorhandenes_dokument = DokumentRepository.get_by_filename(datei["dateiname"])
        
        if not vorhandenes_dokument:
            # Bessere Vorschau aus OCR-verarbeiteter PDF erstellen
            vorschau = OCRService.extract_preview_text(datei["pfad"], max_chars=300)
            
            # In DB speichern (mit neuem Repository)
            DokumentRepository.create(
                dateiname=datei["dateiname"],
                pfad=datei["pfad"],
                inhalt_vorschau=vorschau
            )
    
    # Alle Dokumente abrufen (Repository gibt schon Dictionaries zurück)
    dokumente = DokumentRepository.get_all()
    
    # TEMPORÄRES DEBUG
    logger.info(f"🔍 DEBUG: Gefunden {len(dokumente)} Dokumente")
    for doc in dokumente[-2:]:  # Letzte 2 anzeigen
        logger.info(f"🔍 DEBUG: {doc['dateiname']} -> kategorie={doc.get('kategorie')}, unterkategorie={doc.get('unterkategorie')}")
    
    return {
        "dokumente": dokumente,
        "total": len(dokumente)
    }


@router.get("/{dokument_id}", response_model=DokumentResponse)
async def get_dokument(dokument_id: int = Path(..., description="Die ID des Dokuments")):
    """Ruft ein einzelnes Dokument anhand seiner ID ab."""
    dokument = DokumentRepository.get_by_id(dokument_id)
    
    if not dokument:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    # Konvertiere zu Dictionary für API-Response
    return DokumentRepository.to_dict(dokument)


@router.get("/file/{dokument_id}")
async def get_dokument_file(dokument_id: int):
    """Liefert die PDF-Datei eines Dokuments (bereits OCR-verarbeitet)."""
    dokument = DokumentRepository.get_by_id(dokument_id)
    
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
        media_type="application/pdf",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "*"
        }
    )


@router.post("/upload", response_model=DokumentResponse)
async def upload_dokument(file: UploadFile = File(...)):
    """
    Lädt ein neues PDF-Dokument hoch und führt sofort OCR durch.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien werden unterstützt")
    
    # Datei speichern
    file_path = os.path.join(PDF_INPUT_DIR, file.filename)
    
    try:
        # Datei ins Input-Verzeichnis speichern
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Sofort OCR durchführen
        success = StorageService._process_pdf_with_ocr_inplace(file_path)
        
        if not success:
            # Fallback: Datei bleibt, aber ohne OCR
            logger.warning(f"OCR fehlgeschlagen für hochgeladene Datei: {file.filename}")
        
        # OCR-Marker erstellen
        ocr_marker_path = file_path + '.ocr_processed'
        with open(ocr_marker_path, 'w') as marker:
            marker.write(f"OCR processed at upload: {os.path.getmtime(file_path)}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Datei: {str(e)}")
    
    # Vorschau-Text aus OCR-verarbeiteter PDF erstellen
    vorschau = OCRService.extract_preview_text(file_path, max_chars=300)
    
    # In DB speichern (mit neuem Repository)
    dokument_dict = DokumentRepository.create(
        dateiname=file.filename,
        pfad=file_path,
        inhalt_vorschau=vorschau
    )
    
    if not dokument_dict:
        raise HTTPException(status_code=500, detail="Fehler beim Speichern in der Datenbank")
    
    return dokument_dict


@router.put("/{dokument_id}/kategorisieren", response_model=DokumentResponse)
async def kategorisiere_dokument(
    update_data: DokumentUpdate,
    dokument_id: int = Path(..., description="Die ID des Dokuments")
):
    """
    Kategorisiert ein Dokument und verschiebt es (ohne weitere OCR-Verarbeitung).
    Verwendet jetzt die neue Kategorien-Struktur mit Haupt- und Unterkategorien.
    """
    dokument = DokumentRepository.get_by_id(dokument_id)
    
    if not dokument:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    # Kategorie-Mapping von alten Namen auf neue Struktur
    kategorie_mapping = {
        "berta": ("Rechnungen", "Berta-Rechnung"),
        "kosten": ("Rechnungen", "Kostenrechnung"),
        "irrlaeufer": ("Rechnungen", "Irrläufer"),
        # Neue Kategorien direkt unterstützen
        "Lieferschein_extern": ("Lieferscheine", "Lieferschein_extern"),
        "Lieferschein_intern": ("Lieferscheine", "Lieferschein_intern"),
    }
    
    if update_data.kategorie:
        # Mapping auflösen
        if update_data.kategorie in kategorie_mapping:
            kategorie_name, unterkategorie_name = kategorie_mapping[update_data.kategorie]
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Ungültige Kategorie: {update_data.kategorie}. "
                       f"Verfügbar: {list(kategorie_mapping.keys())}"
            )
        
        # Unterkategorie-ID ermitteln
        unterkategorie_id = get_unterkategorie_by_name(kategorie_name, unterkategorie_name)
        if not unterkategorie_id:
            raise HTTPException(
                status_code=500, 
                detail=f"Unterkategorie {kategorie_name}/{unterkategorie_name} nicht gefunden"
            )
        
        # Kategorie in Repository aktualisieren
        updated_dokument = DokumentRepository.update_kategorie(
            dokument_id, 
            kategorie_name, 
            unterkategorie_name
        )
        
        if not updated_dokument:
            raise HTTPException(status_code=500, detail="Fehler beim Kategorisieren")
        
        # Datei verschieben (falls Kategorie geändert wurde)
        # TODO: Storage-Service für neue Struktur anpassen
        # Erstmal nur DB-Update
        logger.info(f"Dokument {dokument_id} kategorisiert als {kategorie_name}/{unterkategorie_name}")
        
        dokument = updated_dokument
    
    # Metadaten aktualisieren, falls vorhanden
    if update_data.metadaten:
        updated_dokument = DokumentRepository.update_metadaten(dokument_id, update_data.metadaten)
        if updated_dokument:
            dokument = updated_dokument
    
    return dokument


@router.delete("/{dokument_id}", response_model=SuccessResponse)
async def delete_dokument(dokument_id: int = Path(..., description="Die ID des Dokuments")):
    """Löscht ein Dokument aus der Datenbank und die Datei."""
    dokument = DokumentRepository.get_by_id(dokument_id)
    
    if not dokument:
        raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
    
    # Datei und OCR-Marker löschen
    StorageService.delete_file(dokument.pfad)
    
    # Aus DB löschen (mit neuem Repository)
    success = DokumentRepository.delete(dokument_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Fehler beim Löschen des Dokuments")
    
    return {
        "success": True,
        "message": f"Dokument {dokument.dateiname} wurde gelöscht",
        "data": {"id": dokument_id}
    }


# Metadatenfelder-Routen (erstmal unverändert, später auch auf Repository umstellen)
@router.get("/metadaten/felder", response_model=MetadatenFeldList)
async def get_metadatenfelder():
    """Ruft alle verfügbaren Metadatenfelder ab."""
    # TODO: Auch auf Repository-Pattern umstellen
    from ..database.postgres_connection import get_db_session
    from ..models.database import MetadatenFeld
    
    try:
        with get_db_session() as session:
            felder = session.query(MetadatenFeld).order_by(MetadatenFeld.feldname).all()
            
            felder_dict = []
            for feld in felder:
                felder_dict.append({
                    "id": feld.id,
                    "feldname": feld.feldname,
                    "beschreibung": feld.beschreibung,
                    "erstellt_am": feld.erstellt_am.isoformat() if feld.erstellt_am else None
                })
            
            return {"felder": felder_dict}
    except Exception as e:
        logger.error(f"Fehler beim Laden der Metadatenfelder: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Metadatenfelder")


@router.post("/metadaten/felder", response_model=SuccessResponse)
async def create_metadatenfeld(feld: MetadatenFeldCreate):
    """Erstellt ein neues Metadatenfeld."""
    # TODO: Auch auf Repository-Pattern umstellen
    from sqlalchemy.exc import IntegrityError

    from ..database.postgres_connection import get_db_session
    from ..models.database import MetadatenFeld
    
    try:
        with get_db_session() as session:
            neues_feld = MetadatenFeld(
                feldname=feld.feldname,
                beschreibung=feld.beschreibung
            )
            session.add(neues_feld)
            # Commit erfolgt automatisch durch get_db_session()
            
            return {
                "success": True,
                "message": f"Metadatenfeld '{feld.feldname}' wurde erstellt",
                "data": {"feldname": feld.feldname}
            }
    except IntegrityError:
        raise HTTPException(status_code=400, detail=f"Feld '{feld.feldname}' existiert bereits")
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Metadatenfelds: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Erstellen des Metadatenfelds")


@router.delete("/metadaten/felder/{feld_id}", response_model=SuccessResponse)
async def delete_metadatenfeld(feld_id: int = Path(..., description="Die ID des Metadatenfelds")):
    """Löscht ein Metadatenfeld."""
    # TODO: Auch auf Repository-Pattern umstellen
    from ..database.postgres_connection import get_db_session
    from ..models.database import MetadatenFeld
    
    try:
        with get_db_session() as session:
            feld = session.query(MetadatenFeld).filter(MetadatenFeld.id == feld_id).first()
            
            if not feld:
                raise HTTPException(status_code=404, detail="Metadatenfeld nicht gefunden")
            
            session.delete(feld)
            # Commit erfolgt automatisch durch get_db_session()
            
            return {
                "success": True,
                "message": "Metadatenfeld wurde gelöscht",
                "data": {"id": feld_id}
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Metadatenfelds: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Löschen des Metadatenfelds")
    
    """
NEU: CSV-Reimport Route für dokumente.py
Füge diese Route zu backend/app/routes/dokumente.py hinzu
"""

@router.post("/{dokument_id}/csv-reimport", response_model=SuccessResponse)
async def csv_reimport_wareneingang(dokument_id: int = Path(..., description="Die ID des Dokuments")):
    """
    Führt einen CSV-Reimport für ein Wareneingangs-Dokument durch.
    Löscht vorhandene Chargen-Datensätze und importiert sie neu aus den CSV-Dateien.
    """
    try:
        # 1. Dokument-Dictionary statt ORM-Objekt verwenden (vermeidet Session-Probleme)
        dokument_dict = None
        all_dokumente = DokumentRepository.get_all()
        
        for dok in all_dokumente:
            if dok["id"] == dokument_id:
                dokument_dict = dok
                break
        
        if not dokument_dict:
            raise HTTPException(status_code=404, detail="Dokument nicht gefunden")
        
        # 2. Prüfen ob es ein Wareneingangs-Dokument ist (mit Dictionary)
        is_wareneingang = (
            dokument_dict.get("unterkategorie") == "Lieferschein_extern" or 
            dokument_dict.get("kategorie") == "berta"  # Legacy
        )
        
        if not is_wareneingang:
            raise HTTPException(
                status_code=400, 
                detail=f"CSV-Reimport nur für Wareneingangs-Dokumente möglich. "
                       f"Aktuell: kategorie='{dokument_dict.get('kategorie')}', "
                       f"unterkategorie='{dokument_dict.get('unterkategorie')}'"
            )
        
        # 3. Zugehörigen externen Lieferschein finden
        from ..repositories.lieferschein_repository import (
            ChargenEinkaufRepository,
            LieferscheinExternRepository,
        )
        
        lieferscheine = LieferscheinExternRepository.get_all()
        lieferschein = None
        for ls in lieferscheine:
            if ls.dokument_id == dokument_id:
                lieferschein = ls
                break
        
        if not lieferschein:
            raise HTTPException(
                status_code=404, 
                detail="Kein externer Lieferschein für dieses Dokument gefunden. "
                       "Möglicherweise wurde das Dokument noch nicht als Wareneingang verarbeitet."
            )
        
        # 4. Lieferscheinnummer validieren
        if not lieferschein.lieferscheinnummer:
            raise HTTPException(
                status_code=400, 
                detail="Lieferscheinnummer nicht verfügbar"
            )
        
        # 5. Vorhandene Chargen-Datensätze löschen (in neuer Session)
        from ..database.postgres_connection import get_db_session
        from ..models.database import ChargenEinkauf
        
        deleted_count = 0
        with get_db_session() as session:
            existing_chargen = session.query(ChargenEinkauf)\
                .filter(ChargenEinkauf.lieferschein_extern_id == lieferschein.id)\
                .all()
            
            for charge in existing_chargen:
                session.delete(charge)
                deleted_count += 1
        
        logger.info(f"🗑️  {deleted_count} vorhandene Chargen-Datensätze für Lieferschein {lieferschein.lieferscheinnummer} gelöscht")
        
        # 6. CSV-Reimport durchführen
        from ..services.document_processing.wareneingang_processor import (
            WareneingangProcessor,
        )
        
        processor = WareneingangProcessor()
        
        # CSV-Cache leeren für frische Daten
        processor.clear_cache()
        
        # CSV-Import durchführen
        import_count = await processor._import_csv_data(lieferschein, lieferschein.lieferscheinnummer)
        
        # 7. Lieferschein als importiert markieren
        if import_count > 0:
            LieferscheinExternRepository.mark_csv_imported(lieferschein.id)
        
        # 8. Erfolgsantwort
        success_message = (
            f"CSV-Reimport abgeschlossen für Lieferschein '{lieferschein.lieferscheinnummer}': "
            f"{deleted_count} alte Datensätze gelöscht, {import_count} neue importiert"
        )
        
        logger.info(f"✅ {success_message}")
        
        return {
            "success": True,
            "message": success_message,
            "data": {
                "dokument_id": dokument_id,
                "dokument_name": dokument_dict["dateiname"],
                "lieferscheinnummer": lieferschein.lieferscheinnummer,
                "deleted_count": deleted_count,
                "imported_count": import_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim CSV-Reimport für Dokument {dokument_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Interner Fehler beim CSV-Reimport: {str(e)}"
        )