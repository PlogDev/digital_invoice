"""
Repository für Lieferschein-Operationen (extern)
Ersetzt die alten SQLite-basierten Lieferschein-Models
"""

import logging
from typing import List, Optional

from app.database.postgres_connection import get_db_session
from app.models.database import ChargenEinkauf, Dokument, LieferscheinExtern
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

class LieferscheinExternRepository:
    """Repository für externe Lieferscheine"""
    
    @staticmethod
    def get_all() -> List[LieferscheinExtern]:
        """Ruft alle externen Lieferscheine ab."""
        try:
            with get_db_session() as session:
                lieferscheine = session.query(LieferscheinExtern)\
                    .options(joinedload(LieferscheinExtern.dokument))\
                    .order_by(LieferscheinExtern.erstellt_am.desc())\
                    .all()
                
                session.expunge_all()
                return lieferscheine
                
        except Exception as e:
            logger.error(f"Fehler beim Laden aller externen Lieferscheine: {e}")
            return []
    
    @staticmethod
    def get_by_id(lieferschein_id: int) -> Optional[LieferscheinExtern]:
        """Ruft einen externen Lieferschein anhand seiner ID ab."""
        try:
            with get_db_session() as session:
                lieferschein = session.query(LieferscheinExtern)\
                    .options(joinedload(LieferscheinExtern.dokument))\
                    .filter(LieferscheinExtern.id == lieferschein_id)\
                    .first()
                
                if lieferschein:
                    session.expunge(lieferschein)
                return lieferschein
                
        except Exception as e:
            logger.error(f"Fehler beim Laden des Lieferscheins {lieferschein_id}: {e}")
            return None
    
    @staticmethod
    def get_by_lieferscheinnummer(lieferscheinnummer: str) -> Optional[LieferscheinExtern]:
        """Ruft einen Lieferschein anhand der Lieferscheinnummer ab."""
        try:
            with get_db_session() as session:
                lieferschein = session.query(LieferscheinExtern)\
                    .filter(LieferscheinExtern.lieferscheinnummer == lieferscheinnummer)\
                    .first()
                
                if lieferschein:
                    session.expunge(lieferschein)
                return lieferschein
                
        except Exception as e:
            logger.error(f"Fehler beim Laden des Lieferscheins {lieferscheinnummer}: {e}")
            return None
    
    @staticmethod
    def create(lieferscheinnummer: str, dokument_id: int) -> Optional[LieferscheinExtern]:
        """Erstellt einen neuen externen Lieferschein."""
        try:
            with get_db_session() as session:
                lieferschein = LieferscheinExtern(
                    lieferscheinnummer=lieferscheinnummer,
                    dokument_id=dokument_id,
                    csv_importiert=False
                )
                
                session.add(lieferschein)
                session.flush()
                session.refresh(lieferschein)
                session.expunge(lieferschein)
                
                logger.info(f"Externer Lieferschein erstellt: {lieferscheinnummer}")
                return lieferschein
                
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Lieferscheins {lieferscheinnummer}: {e}")
            return None
    
    @staticmethod
    def mark_csv_imported(lieferschein_id: int) -> bool:
        """Markiert einen Lieferschein als CSV-importiert."""
        try:
            with get_db_session() as session:
                lieferschein = session.query(LieferscheinExtern)\
                    .filter(LieferscheinExtern.id == lieferschein_id)\
                    .first()
                
                if not lieferschein:
                    return False
                
                lieferschein.csv_importiert = True
                return True
                
        except Exception as e:
            logger.error(f"Fehler beim Markieren des Lieferscheins {lieferschein_id}: {e}")
            return False
    
    @staticmethod
    def delete(lieferschein_id: int) -> bool:
        """Löscht einen Lieferschein (inkl. aller Chargen-Datensätze)."""
        try:
            with get_db_session() as session:
                lieferschein = session.query(LieferscheinExtern)\
                    .filter(LieferscheinExtern.id == lieferschein_id)\
                    .first()
                
                if not lieferschein:
                    return False
                
                # Cascade delete entfernt automatisch die ChargenEinkauf-Datensätze
                session.delete(lieferschein)
                return True
                
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Lieferscheins {lieferschein_id}: {e}")
            return False
    
    @staticmethod
    def to_dict(lieferschein: LieferscheinExtern) -> dict:
        """Konvertiert einen Lieferschein in ein Dictionary."""
        return {
            "id": lieferschein.id,
            "lieferscheinnummer": lieferschein.lieferscheinnummer,
            "dokument_id": lieferschein.dokument_id,
            "csv_importiert": lieferschein.csv_importiert,
            "erstellt_am": lieferschein.erstellt_am.isoformat() if lieferschein.erstellt_am else None
        }

class ChargenEinkaufRepository:
    """Repository für Chargen-Einkauf-Datensätze"""
    
    @staticmethod
    def get_by_lieferschein_id(lieferschein_id: int) -> List[ChargenEinkauf]:
        """Ruft alle Chargen-Datensätze für einen Lieferschein ab."""
        try:
            with get_db_session() as session:
                chargen = session.query(ChargenEinkauf)\
                    .filter(ChargenEinkauf.lieferschein_extern_id == lieferschein_id)\
                    .order_by(ChargenEinkauf.id)\
                    .all()
                
                session.expunge_all()
                return chargen
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Chargen für Lieferschein {lieferschein_id}: {e}")
            return []
    
    @staticmethod
    def create_from_csv_row(lieferschein_id: int, csv_row: dict) -> Optional[ChargenEinkauf]:
        """Erstellt einen Chargen-Datensatz aus einer CSV-Zeile."""
        try:
            with get_db_session() as session:
                charge = ChargenEinkauf(
                    lieferschein_extern_id=lieferschein_id,
                    linr=csv_row.get('LINR'),
                    liname=csv_row.get('LINAME'),
                    name1=csv_row.get('NAME1'),
                    belfd=csv_row.get('BELFD'),
                    tlnr=csv_row.get('TLNR'),
                    auart=csv_row.get('AUART'),
                    aftnr=csv_row.get('AFTNR'),
                    aps=csv_row.get('APS'),
                    absn=csv_row.get('ABSN'),
                    atnr=csv_row.get('ATNR'),
                    artikel=csv_row.get('ARTIKEL'),
                    materialnr=csv_row.get('MATERIALNR'),
                    urlnd=csv_row.get('URLND'),
                    wartarnr=csv_row.get('WARTARNR'),
                    menge=csv_row.get('MENGE'),
                    erfmenge=csv_row.get('ERFMENGE'),
                    gebindeme=csv_row.get('GEBINDEME'),
                    snnr=csv_row.get('SNNR'),
                    snnralt=csv_row.get('SNNRALT'),
                    einzelek=csv_row.get('EINZELEK'),
                    lieferscheinnr=csv_row.get('LIEFERSCHEINNR'),
                    lieferdatum=csv_row.get('LIEFERDATUM'),
                    renrex=csv_row.get('RENREX'),
                    redat=csv_row.get('REDAT'),
                    bidser=csv_row.get('BIDSER'),
                    bid=csv_row.get('BID')
                )
                
                session.add(charge)
                session.flush()
                session.refresh(charge)
                session.expunge(charge)
                
                return charge
                
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Chargen-Datensatzes: {e}")
            return None
    
    @staticmethod
    def to_dict(charge: ChargenEinkauf) -> dict:
        """Konvertiert einen Chargen-Datensatz in ein Dictionary."""
        return {
            "id": charge.id,
            "lieferschein_extern_id": charge.lieferschein_extern_id,
            "linr": charge.linr,
            "liname": charge.liname,
            "name1": charge.name1,
            "belfd": charge.belfd,
            "tlnr": charge.tlnr,
            "auart": charge.auart,
            "aftnr": charge.aftnr,
            "aps": charge.aps,
            "absn": charge.absn,
            "atnr": charge.atnr,
            "artikel": charge.artikel,
            "materialnr": charge.materialnr,
            "urlnd": charge.urlnd,
            "wartarnr": charge.wartarnr,
            "menge": charge.menge,
            "erfmenge": charge.erfmenge,
            "gebindeme": charge.gebindeme,
            "snnr": charge.snnr,
            "snnralt": charge.snnralt,
            "einzelek": charge.einzelek,
            "lieferscheinnr": charge.lieferscheinnr,
            "lieferdatum": charge.lieferdatum,
            "renrex": charge.renrex,
            "redat": charge.redat,
            "bidser": charge.bidser,
            "bid": charge.bid,
            "erstellt_am": charge.erstellt_am.isoformat() if charge.erstellt_am else None
        }