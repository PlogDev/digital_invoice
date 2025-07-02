#!/usr/bin/env python3
"""
Test-Script für die neuen Repository-Klassen
"""

import os
import sys

# Path für Imports hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging

# Absolute Imports verwenden
from app.repositories.dokument_repository import DokumentRepository
from app.repositories.lieferschein_repository import LieferscheinExternRepository

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("🧪 Teste Repository-Klassen...")
    
    try:
        # 1. Dokument-Repository testen
        logger.info("1️⃣  Teste DokumentRepository...")
        
        # Dokument erstellen
        dokument = DokumentRepository.create(
            dateiname="test_dokument.pdf",
            pfad="/tmp/test_dokument.pdf",
            inhalt_vorschau="Das ist ein Test-Dokument für PostgreSQL"
        )
        
        if dokument:
            logger.info(f"✅ Dokument erstellt: ID {dokument['id']}")
            
            # Kategorisieren
            updated_dokument = DokumentRepository.update_kategorie(
                dokument['id'],
                "Lieferscheine",
                "Lieferschein_extern"
            )
            
            if updated_dokument:
                logger.info(f"✅ Dokument kategorisiert: {updated_dokument['kategorie']}/{updated_dokument['unterkategorie']}")
            
            # Metadaten hinzufügen
            metadaten_dokument = DokumentRepository.update_metadaten(
                dokument['id'],
                {"test_feld": "test_wert", "nummer": "12345"}
            )
            
            if metadaten_dokument:
                logger.info(f"✅ Metadaten hinzugefügt: {metadaten_dokument['metadaten']}")
            
            # Alle Dokumente abrufen
            alle_dokumente = DokumentRepository.get_all()
            logger.info(f"📊 Anzahl Dokumente: {len(alle_dokumente)}")
            
            # Dictionary-Format prüfen
            if alle_dokumente:
                first_doc = alle_dokumente[0]
                logger.info(f"📋 Dictionary: {first_doc['dateiname']} - {first_doc['kategorie']}")
            
        else:
            logger.error("❌ Dokument konnte nicht erstellt werden")
            return False
        
        # 2. Lieferschein-Repository testen
        logger.info("2️⃣  Teste LieferscheinExternRepository...")
        
        # Lieferschein erstellen
        lieferschein = LieferscheinExternRepository.create(
            lieferscheinnummer="LS-TEST-001",
            dokument_id=dokument['id']  # Dictionary-Zugriff
        )
        
        if lieferschein:
            logger.info(f"✅ Lieferschein erstellt: {lieferschein.lieferscheinnummer}")
            
            # Nach Nummer suchen
            gefunden = LieferscheinExternRepository.get_by_lieferscheinnummer("LS-TEST-001")
            if gefunden:
                logger.info(f"✅ Lieferschein gefunden: ID {gefunden.id}")
            
            # Als importiert markieren
            success = LieferscheinExternRepository.mark_csv_imported(lieferschein.id)
            if success:
                logger.info("✅ Lieferschein als CSV-importiert markiert")
            
        else:
            logger.error("❌ Lieferschein konnte nicht erstellt werden")
            return False
        
        logger.info("🎉 Alle Repository-Tests erfolgreich!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)