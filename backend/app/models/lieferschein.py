"""
Datenmodelle für Lieferscheine und Lieferschein-Datensätze.
Erweiterung der bestehenden Modelle um Wareneingang-Funktionalität.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database.connection import get_connection


class Lieferschein:
    """Datenmodell für Lieferscheine mit Datenbankoperationen."""
    
    def __init__(self, 
                 id: Optional[int] = None, 
                 lieferscheinnummer: Optional[str] = None, 
                 dokument_id: Optional[int] = None, 
                 csv_importiert: bool = False,
                 erstellt_am: Optional[str] = None):
        """Initialisiert ein Lieferschein-Objekt.
        
        Args:
            id: Eindeutige ID des Lieferscheins (wird automatisch vergeben)
            lieferscheinnummer: Lieferscheinnummer aus dem PDF
            dokument_id: ID des zugehörigen PDF-Dokuments
            csv_importiert: Flag ob CSV-Daten bereits importiert wurden
            erstellt_am: Zeitstempel der Erstellung
        """
        self.id = id
        self.lieferscheinnummer = lieferscheinnummer
        self.dokument_id = dokument_id
        self.csv_importiert = csv_importiert
        self.erstellt_am = erstellt_am or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert das Lieferschein-Objekt in ein Dictionary."""
        return {
            "id": self.id,
            "lieferscheinnummer": self.lieferscheinnummer,
            "dokument_id": self.dokument_id,
            "csv_importiert": self.csv_importiert,
            "erstellt_am": self.erstellt_am
        }
    
    @classmethod
    def get_all(cls) -> List["Lieferschein"]:
        """Ruft alle Lieferscheine aus der Datenbank ab."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lieferscheine ORDER BY erstellt_am DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [cls._row_to_lieferschein(row) for row in rows]
    
    @classmethod
    def get_by_id(cls, id: int) -> Optional["Lieferschein"]:
        """Ruft einen Lieferschein anhand seiner ID ab."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lieferscheine WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls._row_to_lieferschein(row)
        return None
    
    @classmethod
    def get_by_lieferscheinnummer(cls, lieferscheinnummer: str) -> Optional["Lieferschein"]:
        """Ruft einen Lieferschein anhand der Lieferscheinnummer ab."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lieferscheine WHERE lieferscheinnummer = ?", (lieferscheinnummer,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls._row_to_lieferschein(row)
        return None
    
    @classmethod
    def create(cls, lieferscheinnummer: str, dokument_id: int) -> "Lieferschein":
        """Erstellt einen neuen Lieferschein in der Datenbank."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO lieferscheine (lieferscheinnummer, dokument_id, csv_importiert) VALUES (?, ?, ?)",
            (lieferscheinnummer, dokument_id, False)
        )
        
        lieferschein_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return cls.get_by_id(lieferschein_id)
    
    def update(self) -> "Lieferschein":
        """Aktualisiert den Lieferschein in der Datenbank."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE lieferscheine SET 
                lieferscheinnummer = ?, 
                dokument_id = ?, 
                csv_importiert = ?
               WHERE id = ?""",
            (self.lieferscheinnummer, self.dokument_id, self.csv_importiert, self.id)
        )
        
        conn.commit()
        conn.close()
        return self
    
    def delete(self) -> bool:
        """Löscht den Lieferschein aus der Datenbank."""
        if not self.id:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Erst alle zugehörigen Datensätze löschen
        cursor.execute("DELETE FROM lieferschein_datensaetze WHERE lieferschein_id = ?", (self.id,))
        
        # Dann den Lieferschein selbst löschen
        cursor.execute("DELETE FROM lieferscheine WHERE id = ?", (self.id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    @staticmethod
    def _row_to_lieferschein(row: sqlite3.Row) -> "Lieferschein":
        """Konvertiert eine Datenbankzeile in ein Lieferschein-Objekt."""
        return Lieferschein(
            id=row['id'],
            lieferscheinnummer=row['lieferscheinnummer'],
            dokument_id=row['dokument_id'],
            csv_importiert=bool(row['csv_importiert']),
            erstellt_am=row['erstellt_am']
        )


class LieferscheinDatensatz:
    """Datenmodell für CSV-Datensätze zu Lieferscheinen."""
    
    def __init__(self, 
                 id: Optional[int] = None,
                 lieferschein_id: Optional[int] = None,
                 # CSV-Spalten (alle 26 Felder)
                 linr: Optional[str] = None,
                 liname: Optional[str] = None,
                 name1: Optional[str] = None,
                 belfd: Optional[str] = None,
                 tlnr: Optional[str] = None,
                 auart: Optional[str] = None,
                 aftnr: Optional[str] = None,
                 aps: Optional[str] = None,
                 absn: Optional[str] = None,
                 atnr: Optional[str] = None,
                 artikel: Optional[str] = None,
                 materialnr: Optional[str] = None,
                 urlnd: Optional[str] = None,
                 wartarnr: Optional[str] = None,
                 menge: Optional[str] = None,
                 erfmenge: Optional[str] = None,
                 gebindeme: Optional[str] = None,
                 snnr: Optional[str] = None,
                 snnralt: Optional[str] = None,
                 einzelek: Optional[str] = None,
                 lieferscheinnr: Optional[str] = None,
                 lieferdatum: Optional[str] = None,
                 renrex: Optional[str] = None,
                 redat: Optional[str] = None,
                 bidser: Optional[str] = None,
                 bid: Optional[str] = None,
                 erstellt_am: Optional[str] = None):
        """Initialisiert einen Lieferschein-Datensatz."""
        self.id = id
        self.lieferschein_id = lieferschein_id
        self.linr = linr
        self.liname = liname
        self.name1 = name1
        self.belfd = belfd
        self.tlnr = tlnr
        self.auart = auart
        self.aftnr = aftnr
        self.aps = aps
        self.absn = absn
        self.atnr = atnr
        self.artikel = artikel
        self.materialnr = materialnr
        self.urlnd = urlnd
        self.wartarnr = wartarnr
        self.menge = menge
        self.erfmenge = erfmenge
        self.gebindeme = gebindeme
        self.snnr = snnr
        self.snnralt = snnralt
        self.einzelek = einzelek
        self.lieferscheinnr = lieferscheinnr
        self.lieferdatum = lieferdatum
        self.renrex = renrex
        self.redat = redat
        self.bidser = bidser
        self.bid = bid
        self.erstellt_am = erstellt_am or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert den Datensatz in ein Dictionary."""
        return {
            "id": self.id,
            "lieferschein_id": self.lieferschein_id,
            "linr": self.linr,
            "liname": self.liname,
            "name1": self.name1,
            "belfd": self.belfd,
            "tlnr": self.tlnr,
            "auart": self.auart,
            "aftnr": self.aftnr,
            "aps": self.aps,
            "absn": self.absn,
            "atnr": self.atnr,
            "artikel": self.artikel,
            "materialnr": self.materialnr,
            "urlnd": self.urlnd,
            "wartarnr": self.wartarnr,
            "menge": self.menge,
            "erfmenge": self.erfmenge,
            "gebindeme": self.gebindeme,
            "snnr": self.snnr,
            "snnralt": self.snnralt,
            "einzelek": self.einzelek,
            "lieferscheinnr": self.lieferscheinnr,
            "lieferdatum": self.lieferdatum,
            "renrex": self.renrex,
            "redat": self.redat,
            "bidser": self.bidser,
            "bid": self.bid,
            "erstellt_am": self.erstellt_am
        }
    
    @classmethod
    def get_by_lieferschein_id(cls, lieferschein_id: int) -> List["LieferscheinDatensatz"]:
        """Ruft alle Datensätze für einen Lieferschein ab."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lieferschein_datensaetze WHERE lieferschein_id = ? ORDER BY id", (lieferschein_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [cls._row_to_datensatz(row) for row in rows]
    
    @classmethod
    def create_from_csv_row(cls, lieferschein_id: int, csv_row: Dict[str, str]) -> "LieferscheinDatensatz":
        """Erstellt einen neuen Datensatz aus einer CSV-Zeile."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Alle CSV-Felder in die DB einfügen
        cursor.execute(
            """INSERT INTO lieferschein_datensaetze (
                lieferschein_id, linr, liname, name1, belfd, tlnr, auart, aftnr, aps, absn, atnr,
                artikel, materialnr, urlnd, wartarnr, menge, erfmenge, gebindeme, snnr, snnralt,
                einzelek, lieferscheinnr, lieferdatum, renrex, redat, bidser, bid
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                lieferschein_id,
                csv_row.get('LINR'),
                csv_row.get('LINAME'),
                csv_row.get('NAME1'),
                csv_row.get('BELFD'),
                csv_row.get('TLNR'),
                csv_row.get('AUART'),
                csv_row.get('AFTNR'),
                csv_row.get('APS'),
                csv_row.get('ABSN'),
                csv_row.get('ATNR'),
                csv_row.get('ARTIKEL'),
                csv_row.get('MATERIALNR'),
                csv_row.get('URLND'),
                csv_row.get('WARTARNR'),
                csv_row.get('MENGE'),
                csv_row.get('ERFMENGE'),
                csv_row.get('GEBINDEME'),
                csv_row.get('SNNR'),
                csv_row.get('SNNRALT'),
                csv_row.get('EINZELEK'),
                csv_row.get('LIEFERSCHEINNR'),
                csv_row.get('LIEFERDATUM'),
                csv_row.get('RENREX'),
                csv_row.get('REDAT'),
                csv_row.get('BIDSER'),
                csv_row.get('BID')
            )
        )
        
        datensatz_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return cls.get_by_id(datensatz_id)
    
    @classmethod
    def get_by_id(cls, id: int) -> Optional["LieferscheinDatensatz"]:
        """Ruft einen Datensatz anhand seiner ID ab."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lieferschein_datensaetze WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls._row_to_datensatz(row)
        return None
    
    @staticmethod
    def _row_to_datensatz(row: sqlite3.Row) -> "LieferscheinDatensatz":
        """Konvertiert eine Datenbankzeile in ein Datensatz-Objekt."""
        return LieferscheinDatensatz(
            id=row['id'],
            lieferschein_id=row['lieferschein_id'],
            linr=row['linr'],
            liname=row['liname'],
            name1=row['name1'],
            belfd=row['belfd'],
            tlnr=row['tlnr'],
            auart=row['auart'],
            aftnr=row['aftnr'],
            aps=row['aps'],
            absn=row['absn'],
            atnr=row['atnr'],
            artikel=row['artikel'],
            materialnr=row['materialnr'],
            urlnd=row['urlnd'],
            wartarnr=row['wartarnr'],
            menge=row['menge'],
            erfmenge=row['erfmenge'],
            gebindeme=row['gebindeme'],
            snnr=row['snnr'],
            snnralt=row['snnralt'],
            einzelek=row['einzelek'],
            lieferscheinnr=row['lieferscheinnr'],
            lieferdatum=row['lieferdatum'],
            renrex=row['renrex'],
            redat=row['redat'],
            bidser=row['bidser'],
            bid=row['bid'],
            erstellt_am=row['erstellt_am']
        )