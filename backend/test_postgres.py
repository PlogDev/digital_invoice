#!/usr/bin/env python3
"""
Test-Script für PostgreSQL-Verbindung
"""

import os
import sys

# Path für Imports hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

from app.database.postgres_connection import init_database, test_connection

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🧪 Teste PostgreSQL-Verbindung...")
    
    try:
        # 1. Verbindung testen
        logger.info("1️⃣  Teste Datenbankverbindung...")
        if test_connection():
            logger.info("✅ Verbindung erfolgreich!")
        else:
            logger.error("❌ Verbindung fehlgeschlagen!")
            return False
        
        # 2. Datenbank initialisieren
        logger.info("2️⃣  Initialisiere Datenbank...")
        init_database()
        
        # 3. Tabellen prüfen
        logger.info("3️⃣  Prüfe erstellte Tabellen...")
        from app.database.postgres_connection import get_db_session
        from app.models.database import Kategorie, MetadatenFeld, Unterkategorie
        
        with get_db_session() as session:
            kategorien_count = session.query(Kategorie).count()
            unterkategorien_count = session.query(Unterkategorie).count() 
            metadaten_count = session.query(MetadatenFeld).count()
            
            logger.info(f"📊 Kategorien: {kategorien_count}")
            logger.info(f"📊 Unterkategorien: {unterkategorien_count}")
            logger.info(f"📊 Metadatenfelder: {metadaten_count}")
        
        logger.info("🎉 PostgreSQL-Setup erfolgreich abgeschlossen!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)