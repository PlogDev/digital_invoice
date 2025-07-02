"""
Seed-Daten für die Datenbank-Initialisierung
"""

import logging

from app.database.postgres_connection import get_db_session
from app.models.database import Kategorie, MetadatenFeld, Unterkategorie

logger = logging.getLogger(__name__)

# Kategorien-Struktur mit Unterkategorien
KATEGORIEN_SEED = [
    {
        "name": "Rechnungen",
        "beschreibung": "Eingangs- und Ausgangsrechnungen",
        "unterkategorien": [
            {"name": "Berta-Rechnung", "beschreibung": "Berta-System Rechnungen"},
            {"name": "Kostenrechnung", "beschreibung": "Kostenstellenrechnungen"},
            {"name": "Irrläufer", "beschreibung": "Fehlgeleitete Rechnungen"}
        ]
    },
    {
        "name": "Lieferscheine", 
        "beschreibung": "Lieferscheine intern und extern",
        "unterkategorien": [
            {"name": "Lieferschein_extern", "beschreibung": "Externe Lieferscheine (Wareneingang)"},
            {"name": "Lieferschein_intern", "beschreibung": "Interne Lieferscheine"}
        ]
    },
    {
        "name": "Zolldokumente",
        "beschreibung": "Zoll- und Ursprungsdokumente", 
        "unterkategorien": [
            {"name": "Ursprungszeugnis", "beschreibung": "Ursprungszeugnisse"},
            {"name": "EUR1", "beschreibung": "EUR.1 Präferenznachweis"},
            {"name": "ATR", "beschreibung": "ATR-Dokumente"},
            {"name": "Ausfuhrbegleitdokument", "beschreibung": "Ausfuhrbegleitdokumente"}
        ]
    },
    {
        "name": "Ladescheine",
        "beschreibung": "Ladescheine und Versanddokumente",
        "unterkategorien": [
            {"name": "Ladeschein_intern", "beschreibung": "Interne Ladescheine"}
        ]
    },
    {
        "name": "Werkszeugnis",
        "beschreibung": "Werkszeugnisse und Qualitätsdokumente",
        "unterkategorien": [
            {"name": "Werkszeugnis_3_1", "beschreibung": "Werkszeugnis 3.1"}
        ]
    },
    {
        "name": "Sonstiges",
        "beschreibung": "Nicht kategorisierte Dokumente",
        "unterkategorien": [
            {"name": "Sonstiges", "beschreibung": "Verschiedene Dokumente"}
        ]
    }
]

# Standard-Metadatenfelder
METADATEN_SEED = [
    {"feldname": "rechnungsnummer", "beschreibung": "Rechnungsnummer des Dokuments"},
    {"feldname": "kundennummer", "beschreibung": "Kundennummer oder Kundenreferenz"},
    {"feldname": "datum", "beschreibung": "Rechnungsdatum im Format TT.MM.JJJJ"},
    {"feldname": "betrag", "beschreibung": "Rechnungsbetrag in Euro"},
    {"feldname": "lieferant", "beschreibung": "Name des Lieferanten"},
    {"feldname": "auftragsnummer", "beschreibung": "Interne Auftragsnummer"}
]

def insert_seed_data():
    """
    Fügt Standard-Kategorien und Metadatenfelder in die Datenbank ein.
    Wird nur einmal beim ersten Start ausgeführt.
    """
    try:
        with get_db_session() as session:
            # 1. Kategorien und Unterkategorien einfügen
            kategorien_count = session.query(Kategorie).count()
            
            if kategorien_count == 0:
                logger.info("📋 Füge Standard-Kategorien hinzu...")
                
                for kat_data in KATEGORIEN_SEED:
                    # Kategorie erstellen
                    kategorie = Kategorie(
                        name=kat_data["name"],
                        beschreibung=kat_data["beschreibung"]
                    )
                    session.add(kategorie)
                    session.flush()  # Um ID zu bekommen
                    
                    # Unterkategorien hinzufügen
                    for unter_data in kat_data["unterkategorien"]:
                        unterkategorie = Unterkategorie(
                            kategorie_id=kategorie.id,
                            name=unter_data["name"],
                            beschreibung=unter_data["beschreibung"]
                        )
                        session.add(unterkategorie)
                    
                    logger.info(f"   ✅ Kategorie '{kategorie.name}' mit {len(kat_data['unterkategorien'])} Unterkategorien")
                
                session.commit()
                logger.info("✅ Alle Kategorien erfolgreich eingefügt")
            else:
                logger.info(f"📋 Kategorien bereits vorhanden ({kategorien_count} Stück)")
            
            # 2. Metadatenfelder einfügen
            metadaten_count = session.query(MetadatenFeld).count()
            
            if metadaten_count == 0:
                logger.info("🏷️  Füge Standard-Metadatenfelder hinzu...")
                
                for meta_data in METADATEN_SEED:
                    metafeld = MetadatenFeld(
                        feldname=meta_data["feldname"],
                        beschreibung=meta_data["beschreibung"]
                    )
                    session.add(metafeld)
                    logger.info(f"   ✅ Metadatenfeld '{metafeld.feldname}'")
                
                session.commit()
                logger.info("✅ Alle Metadatenfelder erfolgreich eingefügt")
            else:
                logger.info(f"🏷️  Metadatenfelder bereits vorhanden ({metadaten_count} Stück)")
            
        logger.info("🎉 Seed-Daten-Import abgeschlossen!")
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Einfügen der Seed-Daten: {e}")
        raise

def get_unterkategorie_by_name(kategorie_name: str, unterkategorie_name: str) -> int:
    """
    Hilfsfunktion: Findet Unterkategorie-ID anhand der Namen.
    
    Args:
        kategorie_name: Name der Hauptkategorie (z.B. "Lieferscheine")
        unterkategorie_name: Name der Unterkategorie (z.B. "Lieferschein_extern")
        
    Returns:
        ID der Unterkategorie oder None wenn nicht gefunden
    """
    try:
        with get_db_session() as session:
            unterkategorie = session.query(Unterkategorie)\
                .join(Kategorie)\
                .filter(Kategorie.name == kategorie_name)\
                .filter(Unterkategorie.name == unterkategorie_name)\
                .first()
            
            return unterkategorie.id if unterkategorie else None
            
    except Exception as e:
        logger.error(f"Fehler beim Suchen der Unterkategorie: {e}")
        return None