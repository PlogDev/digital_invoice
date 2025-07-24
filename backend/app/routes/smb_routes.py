
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..repositories.dokument_repository import DokumentRepository
from ..services.ocr_scheduler import ocr_scheduler
from ..services.ocr_service import OCRService
from ..services.windows_smb_service import windows_smb_service

router = APIRouter(prefix="/dokumente", tags=["Dokumente"])
logger = logging.getLogger(__name__)

# Pydantic Models
class SMBConnectionConfig(BaseModel):
    server: str
    share: str  
    username: str
    password: str
    remote_base_path: str
    domain: Optional[str] = None

# --- SMB-Management Routes ---

@router.post("/smb/configure")
async def configure_smb_connection(config: SMBConnectionConfig):
    """
    Konfiguriert die Windows Server SMB-Verbindung.
    
    Beispiel:
    {
        "server": "192.168.66.7",
        "share": "Daten",
        "username": "nsinger", 
        "password": "****",
        "remote_base_path": "Dennis\\\\Nico\\\\PDMS_Anhänge_Backup",
        "domain": "PLOGSTIES"
    }
    """
    try:
        result = windows_smb_service.configure_connection(
            server=config.server,
            share=config.share,
            username=config.username,
            password=config.password,
            remote_base_path=config.remote_base_path,
            domain=config.domain
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "connection_info": {
                    "server": config.server,
                    "share": config.share,
                    "username": config.username,
                    "domain": config.domain,
                    "remote_path": config.remote_base_path
                },
                "backup_folders": result.get("backup_folders_found", []),
                "total_pdfs": result.get("total_pdfs", 0)
            }
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except Exception as e:
        logger.error(f"Fehler beim Konfigurieren der SMB-Verbindung: {e}")
        raise HTTPException(status_code=500, detail=f"Konfiguration fehlgeschlagen: {str(e)}")


@router.get("/smb/status")
async def get_smb_status():
    """Gibt den aktuellen SMB-Verbindungsstatus zurück."""
    try:
        if windows_smb_service.connection_config:
            config = windows_smb_service.connection_config
            
            # Verbindungstest
            test_result = windows_smb_service._test_connection()
            
            return {
                "configured": True,
                "connection_active": test_result["success"],
                "server": config["server"],
                "share": config["share"],
                "username": config["username"], 
                "domain": config.get("domain"),
                "remote_path": config["remote_base_path"],
                "configured_at": config["configured_at"],
                "last_test": test_result,
                "backup_folders": test_result.get("backup_folders", []) if test_result["success"] else []
            }
        else:
            return {
                "configured": False,
                "connection_active": False,
                "message": "Keine SMB-Verbindung konfiguriert"
            }
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des SMB-Status: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen des Status")


@router.post("/smb/scan")
async def scan_smb_files():
    """Scannt die Windows-Share nach neuen PDF-Dateien."""
    try:
        if not windows_smb_service.connection_config:
            raise HTTPException(status_code=400, detail="Keine SMB-Verbindung konfiguriert")
        
        scan_result = windows_smb_service.scan_for_new_files()
        
        if scan_result["success"]:
            results = scan_result["results"]
            
            return {
                "success": True,
                "message": f"Scan abgeschlossen: {results['new_files_count']} neue von {results['total_files']} Dateien gefunden",
                "scan_results": {
                    "scan_time": results["scan_time"],
                    "folders_scanned": results["folders_scanned"],
                    "total_files": results["total_files"],
                    "new_files_count": results["new_files_count"],
                    "new_files": results["new_files"][:10],  # Erste 10 für Preview
                    "errors": results["errors"]
                }
            }
        else:
            raise HTTPException(status_code=500, detail=scan_result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim SMB-Scan: {e}")
        raise HTTPException(status_code=500, detail=f"Scan fehlgeschlagen: {str(e)}")


@router.post("/smb/download")
async def download_smb_files():
    """Lädt alle neuen SMB-Dateien herunter und fügt sie zur OCR-Verarbeitung hinzu."""
    try:
        if not windows_smb_service.connection_config:
            raise HTTPException(status_code=400, detail="Keine SMB-Verbindung konfiguriert")
        
        # Download durchführen
        download_result = windows_smb_service.download_new_files()
        
        if not download_result["success"]:
            raise HTTPException(status_code=500, detail=download_result["message"])
        
        results = download_result["results"]
        processed_count = 0
        
        # Heruntergeladene Dateien zur OCR-Verarbeitung hinzufügen
        for file_info in results["downloaded_files"]:
            try:
                # Vorschau-Text extrahieren
                preview_text = OCRService.extract_preview_text(file_info["local_path"], max_chars=300)
                
                # In Datenbank speichern
                doc_dict = DokumentRepository.create(
                    dateiname=file_info["local_filename"],
                    pfad=file_info["local_path"],
                    inhalt_vorschau=preview_text
                )
                
                if doc_dict:
                    processed_count += 1
                    logger.info(f"✅ SMB-Datei zur Verarbeitung hinzugefügt: {file_info['local_filename']}")
                else:
                    logger.error(f"❌ Fehler beim Speichern in DB: {file_info['local_filename']}")
                    
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von {file_info['local_filename']}: {e}")
                results["errors"].append(f"Verarbeitungsfehler {file_info['local_filename']}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Download abgeschlossen: {results['successful']} Dateien heruntergeladen, {processed_count} zur OCR-Verarbeitung hinzugefügt",
            "download_results": {
                "download_time": results["download_time"],
                "attempted": results["attempted"],
                "successful": results["successful"],
                "failed": results["failed"],
                "processed_for_ocr": processed_count,
                "downloaded_files": results["downloaded_files"],
                "errors": results["errors"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim SMB-Download: {e}")
        raise HTTPException(status_code=500, detail=f"Download fehlgeschlagen: {str(e)}")


@router.post("/smb/sync")
async def sync_smb_files():
    """Führt einen kompletten SMB-Sync durch: Scan + Download + OCR-Vorbereitung."""
    try:
        if not windows_smb_service.connection_config:
            raise HTTPException(status_code=400, detail="Keine SMB-Verbindung konfiguriert")
        
        # 1. Scan durchführen
        logger.info("🔍 Starte SMB-Sync: Scanning...")
        scan_result = windows_smb_service.scan_for_new_files()
        
        if not scan_result["success"]:
            raise HTTPException(status_code=500, detail=f"Scan fehlgeschlagen: {scan_result['error']}")
        
        scan_data = scan_result["results"]
        
        if scan_data["new_files_count"] == 0:
            return {
                "success": True,
                "message": "Sync abgeschlossen: Keine neuen Dateien gefunden",
                "sync_results": {
                    "phase": "scan_only",
                    "folders_scanned": scan_data["folders_scanned"],
                    "total_files": scan_data["total_files"],
                    "new_files": 0,
                    "downloaded": 0,
                    "processed": 0
                }
            }
        
        # 2. Download durchführen
        logger.info(f"📥 Starte SMB-Sync: Download von {scan_data['new_files_count']} Dateien...")
        download_result = windows_smb_service.download_new_files()
        
        if not download_result["success"]:
            raise HTTPException(status_code=500, detail=f"Download fehlgeschlagen: {download_result['message']}")
        
        download_data = download_result["results"]
        
        # 3. OCR-Vorbereitung
        logger.info("🔍 Starte SMB-Sync: OCR-Vorbereitung...")
        processed_count = 0
        
        for file_info in download_data["downloaded_files"]:
            try:
                preview_text = OCRService.extract_preview_text(file_info["local_path"], max_chars=300)
                
                doc_dict = DokumentRepository.create(
                    dateiname=file_info["local_filename"],
                    pfad=file_info["local_path"],
                    inhalt_vorschau=preview_text
                )
                
                if doc_dict:
                    processed_count += 1
                    
            except Exception as e:
                logger.error(f"OCR-Vorbereitung fehlgeschlagen für {file_info['local_filename']}: {e}")
        
        return {
            "success": True,
            "message": f"SMB-Sync erfolgreich: {download_data['successful']} Dateien heruntergeladen, {processed_count} für OCR vorbereitet",
            "sync_results": {
                "phase": "complete",
                "scan_time": scan_data["scan_time"],
                "download_time": download_data["download_time"],
                "folders_scanned": scan_data["folders_scanned"],
                "total_files": scan_data["total_files"],
                "new_files": scan_data["new_files_count"],
                "downloaded": download_data["successful"],
                "download_failed": download_data["failed"],
                "processed_for_ocr": processed_count,
                "errors": scan_data["errors"] + download_data["errors"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim SMB-Sync: {e}")
        raise HTTPException(status_code=500, detail=f"Sync fehlgeschlagen: {str(e)}")


@router.delete("/smb/disconnect")
async def disconnect_smb():
    """Trennt die SMB-Verbindung."""
    try:
        if windows_smb_service.connection_config:
            windows_smb_service.connection_config = None
            windows_smb_service.last_scan_results = {}
            
            return {
                "success": True,
                "message": "SMB-Verbindung getrennt"
            }
        else:
            return {
                "success": True,
                "message": "Keine aktive SMB-Verbindung"
            }
            
    except Exception as e:
        logger.error(f"Fehler beim Trennen der SMB-Verbindung: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Trennen der Verbindung")