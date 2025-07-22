"""
Migrations-Skript für bestehende Daten
Erstelle als: backend/migration_fix_filenames.py
"""

import logging
import os
from pathlib import Path

from app.database.postgres_connection import get_db_session
from app.models.database import Dokument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_existing_filenames():
    """
    Korrigiert Dateinamen in der DB für bereits verschobene Dateien.
    """
    logger.info("🔧 Starte Migration: Dateinamen korrigieren")
    
    try:
        with get_db_session() as session:
            # Alle Dokumente mit inkonsistenten Namen finden
            all_dokumente = session.query(Dokument).all()
            
            fixed_count = 0
            
            for dokument in all_dokumente:
                # Dateiname aus Pfad extrahieren
                if dokument.pfad and os.path.exists(dokument.pfad):
                    actual_filename = os.path.basename(dokument.pfad)
                    
                    # Prüfen ob Dateiname inkonsistent ist
                    if dokument.dateiname != actual_filename:
                        logger.info(f"📝 Korrigiere: {dokument.dateiname} → {actual_filename}")
                        
                        # Dateiname aktualisieren
                        dokument.dateiname = actual_filename
                        fixed_count += 1
                
                # Falls Pfad nicht existiert, aber Datei im processed-Verzeichnis liegt
                elif dokument.dateiname and not os.path.exists(dokument.pfad):
                    # Suche nach möglichen neuen Pfaden
                    new_path = find_moved_file(dokument.dateiname, dokument.id)
                    if new_path:
                        actual_filename = os.path.basename(new_path)
                        logger.info(f"📁 Datei gefunden und korrigiert: {dokument.dateiname} → {actual_filename}")
                        logger.info(f"   Neuer Pfad: {new_path}")
                        
                        dokument.dateiname = actual_filename
                        dokument.pfad = new_path
                        fixed_count += 1
            
            # Änderungen speichern
            session.commit()
            
            logger.info(f"✅ Migration abgeschlossen: {fixed_count} Dateinamen korrigiert")
            return fixed_count
            
    except Exception as e:
        logger.error(f"❌ Fehler bei Migration: {e}")
        return 0

def find_moved_file(original_filename: str, dokument_id: int) -> str:
    """
    Sucht nach verschobenen Dateien basierend auf Dokument-ID.
    """
    try:
        from app.config.settings import PDF_PROCESSED_DIR

        # Nach Dateien mit der Dokument-ID im Namen suchen
        for root, dirs, files in os.walk(PDF_PROCESSED_DIR):
            for file in files:
                # Prüfe ob Datei die Dokument-ID enthält
                if f"_{dokument_id}.pdf" in file:
                    full_path = os.path.join(root, file)
                    logger.debug(f"Gefunden: {full_path}")
                    return full_path
        
        return None
        
    except Exception as e:
        logger.error(f"Fehler beim Suchen der Datei: {e}")
        return None

def list_inconsistent_data():
    """
    Zeigt inkonsistente Daten an (zur Überprüfung vor Migration).
    """
    logger.info("🔍 Prüfe auf inkonsistente Dateinamen...")
    
    try:
        with get_db_session() as session:
            all_dokumente = session.query(Dokument).all()
            
            inconsistent = []
            
            for dokument in all_dokumente:
                if dokument.pfad and os.path.exists(dokument.pfad):
                    actual_filename = os.path.basename(dokument.pfad)
                    
                    if dokument.dateiname != actual_filename:
                        inconsistent.append({
                            "id": dokument.id,
                            "db_name": dokument.dateiname,
                            "actual_name": actual_filename,
                            "path": dokument.pfad
                        })
            
            if inconsistent:
                logger.info(f"📋 {len(inconsistent)} inkonsistente Einträge gefunden:")
                for item in inconsistent[:5]:  # Erste 5 anzeigen
                    logger.info(f"   ID {item['id']}: '{item['db_name']}' → '{item['actual_name']}'")
                
                if len(inconsistent) > 5:
                    logger.info(f"   ... und {len(inconsistent) - 5} weitere")
            else:
                logger.info("✅ Keine inkonsistenten Dateinamen gefunden")
            
            return inconsistent
            
    except Exception as e:
        logger.error(f"Fehler beim Prüfen: {e}")
        return []

if __name__ == "__main__":
    print("🔧 Dateiname-Migration für OCR-Dokumentenverwaltung")
    print()
    
    # 1. Inkonsistente Daten anzeigen
    inconsistent = list_inconsistent_data()
    
    if inconsistent:
        print()
        response = input(f"Möchtest du {len(inconsistent)} inkonsistente Dateinamen korrigieren? (y/N): ")
        
        if response.lower() in ['y', 'yes', 'j', 'ja']:
            # 2. Migration durchführen
            fixed = fix_existing_filenames()
            print(f"\n✅ {fixed} Dateinamen wurden korrigiert!")
        else:
            print("❌ Migration abgebrochen")
    else:
        print("✅ Keine Migration nötig - alle Dateinamen sind konsistent!")