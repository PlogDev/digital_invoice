"""
Repository für Dokument-Operationen
Ersetzt die alten SQLite-basierten Model-Methoden
"""

import logging
from typing import List, Optional

from app.database.postgres_connection import get_db_session
from app.models.database import Dokument, Kategorie, Unterkategorie
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class DokumentRepository:
    """Repository für Dokument-CRUD-Operationen"""
    
    @staticmethod
    def get_all() -> List[dict]:
        """
        Ruft alle Dokumente aus der Datenbank ab.
        Lädt auch die Kategorien-Beziehungen mit.
        Returns Liste von Dictionaries statt ORM-Objekten.
        """
        try:
            with get_db_session() as session:
                dokumente = session.query(Dokument)\
                    .options(joinedload(Dokument.unterkategorie).joinedload(Unterkategorie.kategorie))\
                    .order_by(Dokument.erstellt_am.desc())\
                    .all()
                
                # Innerhalb der Session zu Dictionaries konvertieren
                result = []
                for dok in dokumente:
                    # Debug-Output für fehlende Unterkategorien
                    kategorie_name = None
                    unterkategorie_name = None
                    
                    if dok.unterkategorie:
                        unterkategorie_name = dok.unterkategorie.name
                        if dok.unterkategorie.kategorie:
                            kategorie_name = dok.unterkategorie.kategorie.name
                    
                    # Für Legacy-Kompatibilität: Wenn nur kategorie_id gesetzt ist
                    elif dok.kategorie_id:
                        try:
                            kategorie = session.query(Kategorie).filter(Kategorie.id == dok.kategorie_id).first()
                            if kategorie:
                                kategorie_name = kategorie.name
                        except:
                            pass
                    
                    result.append({
                        "id": dok.id,
                        "dateiname": dok.dateiname,
                        "kategorie": kategorie_name,
                        "unterkategorie": unterkategorie_name,
                            # DEBUG: Temporär
                        "debug_kategorie_id": dok.kategorie_id,
                        "debug_unterkategorie_id": dok.unterkategorie_id,
                        "pfad": dok.pfad,
                        "pfad": dok.pfad,
                        "inhalt_vorschau": dok.inhalt_vorschau,
                        "erstellt_am": dok.erstellt_am.isoformat() if dok.erstellt_am else None,
                        "metadaten": dok.metadaten or {}
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Fehler beim Laden aller Dokumente: {e}")
            return []
    
    @staticmethod
    def get_by_id(dokument_id: int) -> Optional[Dokument]:
        """Ruft ein Dokument anhand seiner ID ab."""
        try:
            with get_db_session() as session:
                dokument = session.query(Dokument)\
                    .options(joinedload(Dokument.unterkategorie).joinedload(Unterkategorie.kategorie))\
                    .filter(Dokument.id == dokument_id)\
                    .first()
                
                if dokument:
                    session.expunge(dokument)
                return dokument
                
        except Exception as e:
            logger.error(f"Fehler beim Laden des Dokuments {dokument_id}: {e}")
            return None
    
    @staticmethod
    def get_by_filename(dateiname: str) -> Optional[Dokument]:
        """Ruft ein Dokument anhand des Dateinamens ab."""
        try:
            with get_db_session() as session:
                dokument = session.query(Dokument)\
                    .filter(Dokument.dateiname == dateiname)\
                    .first()
                
                if dokument:
                    session.expunge(dokument)
                return dokument
                
        except Exception as e:
            logger.error(f"Fehler beim Laden des Dokuments {dateiname}: {e}")
            return None
    
    @staticmethod
    def create(dateiname: str, pfad: str, inhalt_vorschau: Optional[str] = None) -> Optional[dict]:
        """Erstellt ein neues Dokument in der Datenbank. Returns Dictionary."""
        try:
            with get_db_session() as session:
                dokument = Dokument(
                    dateiname=dateiname,
                    pfad=pfad,
                    inhalt_vorschau=inhalt_vorschau
                )
                
                session.add(dokument)
                session.flush()  # Um ID zu bekommen
                
                # Refresh und zu Dictionary konvertieren
                session.refresh(dokument)
                
                result = {
                    "id": dokument.id,
                    "dateiname": dokument.dateiname,
                    "kategorie": None,
                    "unterkategorie": None,
                    "pfad": dokument.pfad,
                    "inhalt_vorschau": dokument.inhalt_vorschau,
                    "erstellt_am": dokument.erstellt_am.isoformat() if dokument.erstellt_am else None,
                    "metadaten": dokument.metadaten or {}
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Dokuments {dateiname}: {e}")
            return None
    
    @staticmethod
    def update_kategorie(dokument_id: int, kategorie_name: str, unterkategorie_name: str) -> Optional[dict]:
        """
        Aktualisiert die Kategorie eines Dokuments.
        
        Args:
            dokument_id: ID des Dokuments
            kategorie_name: Name der Hauptkategorie (z.B. "Lieferscheine")
            unterkategorie_name: Name der Unterkategorie (z.B. "Lieferschein_extern")
            
        Returns:
            Dictionary mit Dokumentdaten oder None bei Fehler
        """
        try:
            with get_db_session() as session:
                # Dokument laden
                dokument = session.query(Dokument).filter(Dokument.id == dokument_id).first()
                if not dokument:
                    logger.error(f"Dokument {dokument_id} nicht gefunden")
                    return None
                
                # Unterkategorie finden
                unterkategorie = session.query(Unterkategorie)\
                    .join(Kategorie)\
                    .filter(Kategorie.name == kategorie_name)\
                    .filter(Unterkategorie.name == unterkategorie_name)\
                    .first()
                
                if not unterkategorie:
                    logger.error(f"Unterkategorie {kategorie_name}/{unterkategorie_name} nicht gefunden")
                    return None
                
                # Dokument aktualisieren
                dokument.kategorie_id = unterkategorie.kategorie_id
                dokument.unterkategorie_id = unterkategorie.id
                
                session.flush()
                
                # Dokument mit allen Relationships laden und direkt zu Dict konvertieren
                updated_dokument = session.query(Dokument)\
                    .options(joinedload(Dokument.unterkategorie).joinedload(Unterkategorie.kategorie))\
                    .filter(Dokument.id == dokument_id)\
                    .first()
                
                # Innerhalb der Session zu Dictionary konvertieren
                result = {
                    "id": updated_dokument.id,
                    "dateiname": updated_dokument.dateiname,
                    "kategorie": updated_dokument.unterkategorie.kategorie.name if updated_dokument.unterkategorie else None,
                    "unterkategorie": updated_dokument.unterkategorie.name if updated_dokument.unterkategorie else None,
                    "pfad": updated_dokument.pfad,
                    "inhalt_vorschau": updated_dokument.inhalt_vorschau,
                    "erstellt_am": updated_dokument.erstellt_am.isoformat() if updated_dokument.erstellt_am else None,
                    "metadaten": updated_dokument.metadaten or {}
                }
                
                logger.info(f"Dokument {dokument_id} kategorisiert als {kategorie_name}/{unterkategorie_name}")
                return result
                
        except Exception as e:
            logger.error(f"Fehler beim Kategorisieren des Dokuments {dokument_id}: {e}")
            return None
    
    @staticmethod
    def update_metadaten(dokument_id: int, metadaten: dict) -> Optional[dict]:
        """Aktualisiert die Metadaten eines Dokuments. Returns Dictionary."""
        try:
            with get_db_session() as session:
                dokument = session.query(Dokument)\
                    .options(joinedload(Dokument.unterkategorie).joinedload(Unterkategorie.kategorie))\
                    .filter(Dokument.id == dokument_id)\
                    .first()
                
                if not dokument:
                    return None
                
                # Metadaten aktualisieren (PostgreSQL JSON Support!)
                dokument.metadaten = metadaten
                session.flush()
                
                # Zu Dictionary konvertieren
                result = {
                    "id": dokument.id,
                    "dateiname": dokument.dateiname,
                    "kategorie": dokument.unterkategorie.kategorie.name if dokument.unterkategorie else None,
                    "unterkategorie": dokument.unterkategorie.name if dokument.unterkategorie else None,
                    "pfad": dokument.pfad,
                    "inhalt_vorschau": dokument.inhalt_vorschau,
                    "erstellt_am": dokument.erstellt_am.isoformat() if dokument.erstellt_am else None,
                    "metadaten": dokument.metadaten or {}
                }
                
                return result
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Metadaten für Dokument {dokument_id}: {e}")
            return None
    
    @staticmethod
    def update_pfad(dokument_id: int, neuer_pfad: str) -> Optional[Dokument]:
        """Aktualisiert den Pfad eines Dokuments (nach Verschiebung)."""
        try:
            with get_db_session() as session:
                dokument = session.query(Dokument).filter(Dokument.id == dokument_id).first()
                if not dokument:
                    return None
                
                dokument.pfad = neuer_pfad
                
                session.flush()
                session.refresh(dokument)
                session.expunge(dokument)
                
                return dokument
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Pfads für Dokument {dokument_id}: {e}")
            return None

    @staticmethod
    def update_pfad_und_dateiname(dokument_id: int, neuer_pfad: str, neuer_dateiname: str) -> Optional[Dokument]:
        """
        Aktualisiert sowohl Pfad als auch Dateiname eines Dokuments (nach Verschiebung/Umbenennung).
        
        Args:
            dokument_id: ID des Dokuments
            neuer_pfad: Neuer vollständiger Pfad
            neuer_dateiname: Neuer Dateiname
            
        Returns:
            Aktualisiertes Dokument oder None bei Fehler
        """
        try:
            with get_db_session() as session:
                dokument = session.query(Dokument).filter(Dokument.id == dokument_id).first()
                if not dokument:
                    logger.error(f"Dokument {dokument_id} nicht gefunden für Pfad/Name-Update")
                    return None
                
                # Beide Felder aktualisieren
                dokument.pfad = neuer_pfad
                dokument.dateiname = neuer_dateiname
                
                session.flush()
                session.refresh(dokument)
                session.expunge(dokument)
                
                logger.info(f"Pfad und Dateiname aktualisiert für Dokument {dokument_id}: {neuer_dateiname}")
                return dokument
                
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren von Pfad/Dateiname für Dokument {dokument_id}: {e}")
            return None

    @staticmethod
    def delete(dokument_id: int) -> bool:
        """Löscht ein Dokument aus der Datenbank."""
        try:
            with get_db_session() as session:
                dokument = session.query(Dokument).filter(Dokument.id == dokument_id).first()
                if not dokument:
                    return False
                
                session.delete(dokument)
                return True
                
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Dokuments {dokument_id}: {e}")
            return False
    
    @staticmethod
    def to_dict(dokument: Dokument) -> dict:
        """
        Konvertiert ein Dokument in ein Dictionary für API-Responses.
        Kompatibel mit dem alten Format.
        """
        return {
            "id": dokument.id,
            "dateiname": dokument.dateiname,
            "kategorie": dokument.unterkategorie.kategorie.name if dokument.unterkategorie else None,
            "unterkategorie": dokument.unterkategorie.name if dokument.unterkategorie else None,
            "pfad": dokument.pfad,
            "inhalt_vorschau": dokument.inhalt_vorschau,
            "erstellt_am": dokument.erstellt_am.isoformat() if dokument.erstellt_am else None,
            "metadaten": dokument.metadaten or {}
        }