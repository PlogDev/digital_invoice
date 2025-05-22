"""
Datenmodelle für Dokumente und Metadatenfelder.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..database.connection import get_connection


class Dokument:
    """Datenmodell für Dokumente mit Datenbankoperationen."""
    
    def __init__(self, 
                 id: Optional[int] = None, 
                 dateiname: Optional[str] = None, 
                 kategorie: Optional[str] = None, 
                 pfad: Optional[str] = None, 
                 inhalt_vorschau: Optional[str] = None, 
                 erstellt_am: Optional[str] = None, 
                 metadaten: Optional[Dict[str, Any]] = None):
        """Initialisiert ein Dokument-Objekt.
        
        Args:
            id: Eindeutige ID des Dokuments (wird automatisch vergeben)
            dateiname: Name der PDF-Datei
            kategorie: Kategorie des Dokuments (berta, kosten, irrlaeufer)
            pfad: Dateipfad zum Dokument
            inhalt_vorschau: OCR-Vorschau des Dokumentinhalts
            erstellt_am: Zeitstempel der Erstellung
            metadaten: Dictionary mit Metadatenfeldern und Werten
        """
        self.id = id
        self.dateiname = dateiname
        self.kategorie = kategorie
        self.pfad = pfad
        self.inhalt_vorschau = inhalt_vorschau
        self.erstellt_am = erstellt_am or datetime.now().isoformat()
        self.metadaten = metadaten or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert das Dokument-Objekt in ein Dictionary.
        
        Returns:
            Dict mit allen Dokumentattributen
        """
        return {
            "id": self.id,
            "dateiname": self.dateiname,
            "kategorie": self.kategorie,
            "pfad": self.pfad,
            "inhalt_vorschau": self.inhalt_vorschau,
            "erstellt_am": self.erstellt_am,
            "metadaten": self.metadaten
        }
    
    @classmethod
    def get_all(cls) -> List["Dokument"]:
        """Ruft alle Dokumente aus der Datenbank ab.
        
        Returns:
            Liste von Dokument-Objekten
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dokumente ORDER BY erstellt_am DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [cls._row_to_dokument(row) for row in rows]
    
    @classmethod
    def get_by_id(cls, id: int) -> Optional["Dokument"]:
        """Ruft ein Dokument anhand seiner ID ab.
        
        Args:
            id: Die ID des Dokuments
            
        Returns:
            Dokument-Objekt oder None, wenn nicht gefunden
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dokumente WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return cls._row_to_dokument(row)
        return None
    
    @classmethod
    def create(cls, dateiname: str, pfad: str, inhalt_vorschau: Optional[str] = None) -> "Dokument":
        """Erstellt ein neues Dokument in der Datenbank.
        
        Args:
            dateiname: Name der PDF-Datei
            pfad: Dateipfad zum Dokument
            inhalt_vorschau: OCR-Vorschau des Dokumentinhalts
            
        Returns:
            Neues Dokument-Objekt mit ID
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO dokumente (dateiname, pfad, inhalt_vorschau) VALUES (?, ?, ?)",
            (dateiname, pfad, inhalt_vorschau)
        )
        
        dok_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return cls.get_by_id(dok_id)
    
    def update(self) -> "Dokument":
        """Aktualisiert das Dokument in der Datenbank.
        
        Returns:
            Aktualisiertes Dokument-Objekt
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        metadaten_str = json.dumps(self.metadaten) if self.metadaten else None
        
        cursor.execute(
            """UPDATE dokumente SET 
                kategorie = ?, 
                pfad = ?, 
                inhalt_vorschau = ?,
                metadaten = ?
               WHERE id = ?""",
            (self.kategorie, self.pfad, self.inhalt_vorschau, metadaten_str, self.id)
        )
        
        conn.commit()
        conn.close()
        return self
    
    def delete(self) -> bool:
        """Löscht das Dokument aus der Datenbank.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.id:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM dokumente WHERE id = ?", (self.id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    @staticmethod
    def _row_to_dokument(row: sqlite3.Row) -> "Dokument":
        """Konvertiert eine Datenbankzeile in ein Dokument-Objekt.
        
        Args:
            row: SQLite-Row-Objekt
            
        Returns:
            Dokument-Objekt
        """
        metadaten = {}
        if row['metadaten']:
            try:
                metadaten = json.loads(row['metadaten'])
            except json.JSONDecodeError:
                pass
                
        return Dokument(
            id=row['id'],
            dateiname=row['dateiname'],
            kategorie=row['kategorie'],
            pfad=row['pfad'],
            inhalt_vorschau=row['inhalt_vorschau'],
            erstellt_am=row['erstellt_am'],
            metadaten=metadaten
        )


class MetadatenFeld:
    """Datenmodell für Metadatenfelder mit Datenbankoperationen."""
    
    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """Ruft alle verfügbaren Metadatenfelder ab.
        
        Returns:
            Liste von Metadatenfeld-Dictionaries
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM metadaten_felder ORDER BY feldname")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    @classmethod
    def create(cls, feldname: str, beschreibung: str) -> bool:
        """Erstellt ein neues Metadatenfeld.
        
        Args:
            feldname: Name des Feldes (eindeutig)
            beschreibung: Beschreibung des Feldes
            
        Returns:
            True bei Erfolg, False wenn Feld bereits existiert
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO metadaten_felder (feldname, beschreibung) VALUES (?, ?)",
                (feldname, beschreibung)
            )
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            # Feld existiert bereits
            success = False
        
        conn.close()
        return success
    
    @classmethod
    def delete(cls, feld_id: int) -> bool:
        """Löscht ein Metadatenfeld.
        
        Args:
            feld_id: ID des zu löschenden Feldes
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM metadaten_felder WHERE id = ?", (feld_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success