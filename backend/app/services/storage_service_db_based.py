"""
DB-basierter Storage-Service - ersetzt das statische PDF_CATEGORIES System
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.orm import joinedload

from ..config.settings import PDF_PROCESSED_DIR
from ..database.postgres_connection import get_db_session
from ..models.database import Kategorie, Unterkategorie

logger = logging.getLogger(__name__)

class DBBasedStorageService:
    """DB-basierter Storage-Service für intelligente Dateiverwaltung."""
    
    @staticmethod
    def get_category_path(kategorie_name: str, unterkategorie_name: str) -> Optional[Path]:
        """
        Ermittelt den Dateipfad für eine Kategorie/Unterkategorie aus der DB.
        
        Args:
            kategorie_name: Name der Hauptkategorie (z.B. "Wareneingang")
            unterkategorie_name: Name der Unterkategorie (z.B. "Lieferschein_extern")
            
        Returns:
            Path-Objekt oder None bei Fehler
        """
        try:
            with get_db_session() as session:
                unterkategorie = session.query(Unterkategorie)\
                    .join(Kategorie)\
                    .filter(Kategorie.name == kategorie_name)\
                    .filter(Unterkategorie.name == unterkategorie_name)\
                    .first()
                
                if unterkategorie:
                    # Verzeichnisstruktur: processed/kategorie/unterkategorie
                    # z.B.: processed/wareneingang/lieferschein_extern
                    category_path = PDF_PROCESSED_DIR / kategorie_name.lower() / unterkategorie_name.lower()
                    return category_path
                else:
                    logger.error(f"Kategorie/Unterkategorie nicht gefunden: {kategorie_name}/{unterkategorie_name}")
                    return None
                    
        except Exception as e:
            logger.error(f"Fehler beim Ermitteln des Kategoriepfads: {e}")
            return None
    
    @staticmethod
    def ensure_category_directory(kategorie_name: str, unterkategorie_name: str) -> Optional[Path]:
        """
        Stellt sicher, dass das Verzeichnis für eine Kategorie existiert.
        
        Returns:
            Path-Objekt oder None bei Fehler
        """
        try:
            category_path = DBBasedStorageService.get_category_path(kategorie_name, unterkategorie_name)
            
            if category_path:
                # Verzeichnis erstellen falls nicht vorhanden
                os.makedirs(category_path, exist_ok=True)
                logger.info(f"Verzeichnis sichergestellt: {category_path}")
                return category_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Kategorieverzeichnisses: {e}")
            return None
    
    @staticmethod
    def move_file_to_category(
        source_path: str, 
        kategorie_name: str, 
        unterkategorie_name: str,
        filename: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verschiebt eine Datei in das entsprechende Kategorieverzeichnis.
        
        Args:
            source_path: Aktueller Dateipfad
            kategorie_name: Ziel-Kategorie
            unterkategorie_name: Ziel-Unterkategorie
            filename: Optional - neuer Dateiname
            
        Returns:
            Tuple aus (Erfolg, Neuer Pfad)
        """
        try:
            # Zielverzeichnis sicherstellen
            target_dir = DBBasedStorageService.ensure_category_directory(kategorie_name, unterkategorie_name)
            
            if not target_dir:
                logger.error(f"Zielverzeichnis konnte nicht erstellt werden: {kategorie_name}/{unterkategorie_name}")
                return False, None
            
            # Dateiname ermitteln
            if filename:
                target_filename = filename
            else:
                target_filename = os.path.basename(source_path)
            
            target_path = target_dir / target_filename
            
            # Prüfen ob Quelldatei existiert
            if not os.path.exists(source_path):
                logger.error(f"Quelldatei nicht gefunden: {source_path}")
                return False, None
            
            # Datei verschieben
            shutil.move(source_path, str(target_path))
            
            # OCR-Marker auch verschieben/entfernen
            ocr_marker = source_path + '.ocr_processed'
            if os.path.exists(ocr_marker):
                os.remove(ocr_marker)
            
            # Document Processing Marker auch verschieben/entfernen
            doc_marker = source_path + '.doc_processed'
            if os.path.exists(doc_marker):
                os.remove(doc_marker)
            
            logger.info(f"Datei verschoben: {source_path} -> {target_path}")
            return True, str(target_path)
            
        except Exception as e:
            logger.error(f"Fehler beim Verschieben der Datei: {e}")
            return False, None
    
    @staticmethod
    def get_all_categories() -> list:
        """
        Ruft alle verfügbaren Kategorien und Unterkategorien aus der DB ab.
        
        Returns:
            Liste mit Kategorie-Dictionaries
        """
        try:
            with get_db_session() as session:
                kategorien = session.query(Kategorie)\
                    .options(joinedload(Kategorie.unterkategorien))\
                    .all()
                
                result = []
                for kategorie in kategorien:
                    kat_dict = {
                        "id": kategorie.id,
                        "name": kategorie.name,
                        "beschreibung": kategorie.beschreibung,
                        "unterkategorien": []
                    }
                    
                    for unterkategorie in kategorie.unterkategorien:
                        kat_dict["unterkategorien"].append({
                            "id": unterkategorie.id,
                            "name": unterkategorie.name,
                            "beschreibung": unterkategorie.beschreibung
                        })
                    
                    result.append(kat_dict)
                
                return result
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Kategorien: {e}")
            return []