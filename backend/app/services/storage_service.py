"""
Storage-Service für die Verwaltung von PDF-Dateien.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config.settings import PDF_CATEGORIES, PDF_INPUT_DIR

# Logger einrichten
logger = logging.getLogger(__name__)

class StorageService:
    """Service für die Dateiverwaltung von PDFs."""
    
    @staticmethod
    def get_input_files() -> List[Dict[str, str]]:
        """Ruft alle PDF-Dateien im Eingangsverzeichnis ab.
        
        Returns:
            Liste von Dictionaries mit Dateinamen und Pfaden
        """
        files = []
        
        try:
            for filename in os.listdir(PDF_INPUT_DIR):
                if filename.lower().endswith('.pdf'):
                    file_path = os.path.join(PDF_INPUT_DIR, filename)
                    
                    files.append({
                        "dateiname": filename,
                        "pfad": str(file_path)
                    })
        except Exception as e:
            logger.error(f"Fehler beim Lesen des Eingangsverzeichnisses: {str(e)}")
        
        return files
    
    @staticmethod
    def move_file(source_path: str, kategorie: str) -> Tuple[bool, Optional[str]]:
        """Verschiebt eine Datei in das entsprechende Kategorie-Verzeichnis.
        
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
            
            return True, str(target_path)
        except Exception as e:
            logger.error(f"Fehler beim Verschieben der Datei: {str(e)}")
            return False, None
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """Löscht eine Datei.
        
        Args:
            file_path: Pfad zur zu löschenden Datei
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Datei gelöscht: {file_path}")
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