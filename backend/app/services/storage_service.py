"""
Storage-Service für die Verwaltung von PDF-Dateien mit OCR-Integration.
OCR wird bereits beim Scannen der Eingangsdokumente durchgeführt.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config.settings import PDF_CATEGORIES, PDF_INPUT_DIR
from .ocr_service import OCRService

# Logger einrichten
logger = logging.getLogger(__name__)

class StorageService:
    """Service für die Dateiverwaltung von PDFs mit OCR-Verarbeitung."""
    
    @staticmethod
    def get_input_files() -> List[Dict[str, str]]:
        """
        Ruft alle PDF-Dateien im Eingangsverzeichnis ab und führt OCR durch.
        
        Returns:
            Liste von Dictionaries mit Dateinamen und Pfaden
        """
        files = []
        
        try:
            for filename in os.listdir(PDF_INPUT_DIR):
                if filename.lower().endswith('.pdf'):
                    file_path = os.path.join(PDF_INPUT_DIR, filename)
                    
                    # Prüfen ob bereits OCR-verarbeitet (Marker-Datei oder Zeitstempel)
                    ocr_marker_path = file_path + '.ocr_processed'
                    
                    if not os.path.exists(ocr_marker_path):
                        logger.info(f"Führe OCR für neue Datei durch: {filename}")
                        success = StorageService._process_pdf_with_ocr_inplace(file_path)
                        
                        if success:
                            # Marker-Datei erstellen
                            with open(ocr_marker_path, 'w') as marker:
                                marker.write(f"OCR processed at: {os.path.getmtime(file_path)}")
                            logger.info(f"OCR erfolgreich für: {filename}")
                        else:
                            logger.warning(f"OCR fehlgeschlagen für: {filename}")
                    
                    files.append({
                        "dateiname": filename,
                        "pfad": str(file_path)
                    })
        except Exception as e:
            logger.error(f"Fehler beim Lesen des Eingangsverzeichnisses: {str(e)}")
        
        return files
    
    @staticmethod
    def _process_pdf_with_ocr_inplace(pdf_path: str) -> bool:
        """
        Verarbeitet eine PDF-Datei mit OCR und ersetzt sie durch die durchsuchbare Version.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            # Temporäre Datei für OCR-Output
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # OCR-Verarbeitung
                success = OCRService.create_searchable_pdf(pdf_path, temp_path)
                
                if success:
                    # Original durch OCR-Version ersetzen
                    shutil.move(temp_path, pdf_path)
                    logger.info(f"PDF erfolgreich mit OCR verarbeitet: {pdf_path}")
                    return True
                else:
                    logger.error(f"OCR-Verarbeitung fehlgeschlagen: {pdf_path}")
                    return False
                    
            finally:
                # Temporäre Datei aufräumen, falls sie noch existiert
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"Fehler beim OCR-Processing: {str(e)}")
            return False
    
    @staticmethod
    def move_file_only(source_path: str, kategorie: str) -> Tuple[bool, Optional[str]]:
        """
        Verschiebt eine bereits OCR-verarbeitete Datei in das entsprechende Kategorie-Verzeichnis.
        Keine weitere OCR-Verarbeitung nötig.
        
        Args:
            source_path: Pfad zur Quelldatei
            kategorie: Zielkategorie (berta, kosten, irrlaeufer)
            
        Returns:
            Tuple aus (Erfolg, Neuer Pfad)
        """
        if kategorie not in PDF_CATEGORIES:
            logger.error(f"Ungültige Kategorie: {kategorie}")
            return False, None
        
        try:
            # Dateipfade aufbereiten
            source_path = Path(source_path)
            filename = source_path.name
            target_dir = PDF_CATEGORIES[kategorie]
            target_path = target_dir / filename
            
            # Sicherstellen, dass das Zielverzeichnis existiert
            os.makedirs(target_dir, exist_ok=True)
            
            # Datei verschieben
            shutil.move(str(source_path), str(target_path))
            logger.info(f"Datei verschoben: {source_path} -> {target_path}")
            
            # OCR-Marker-Datei auch verschieben/löschen
            ocr_marker = str(source_path) + '.ocr_processed'
            if os.path.exists(ocr_marker):
                os.remove(ocr_marker)
            
            return True, str(target_path)
            
        except Exception as e:
            logger.error(f"Fehler beim Verschieben der Datei: {str(e)}")
            return False, None
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Löscht eine Datei und ihre OCR-Marker-Datei.
        
        Args:
            file_path: Pfad zur zu löschenden Datei
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Datei gelöscht: {file_path}")
                
                # OCR-Marker-Datei auch löschen
                ocr_marker = file_path + '.ocr_processed'
                if os.path.exists(ocr_marker):
                    os.remove(ocr_marker)
                    
                return True
            else:
                logger.warning(f"Datei existiert nicht: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Datei: {str(e)}")
            return False
    
    @staticmethod
    def get_file_path(kategorie: str, filename: str) -> Optional[str]:
        """Erstellt einen vollständigen Dateipfad basierend auf Kategorie und Dateinamen.
        
        Args:
            kategorie: Kategorie des Dokuments
            filename: Name der Datei
            
        Returns:
            Vollständiger Dateipfad oder None bei ungültiger Kategorie
        """
        if kategorie not in PDF_CATEGORIES:
            return None
        
        return str(PDF_CATEGORIES[kategorie] / filename)
    
    # Backward compatibility - die alte Methode als deprecated markieren
    @staticmethod
    def process_and_move_file(source_path: str, kategorie: str, filename: Optional[str] = None) -> Tuple[bool, Optional[str], str]:
        """
        DEPRECATED: Verwende move_file_only() da OCR bereits beim Scannen durchgeführt wird.
        
        Diese Methode ist nur noch für Kompatibilität vorhanden.
        """
        logger.warning("process_and_move_file() ist deprecated. Verwende move_file_only()")
        
        # Einfach verschieben, da OCR bereits durchgeführt wurde
        success, new_path = StorageService.move_file_only(source_path, kategorie)
        
        # Vorschau-Text aus der bereits OCR-verarbeiteten PDF extrahieren
        preview_text = ""
        if success and new_path:
            preview_text = OCRService.extract_preview_text(new_path)
        
        return success, new_path, preview_text