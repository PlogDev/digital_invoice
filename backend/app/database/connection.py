"""
Datenbankverbindung und Initialisierungsfunktionen.
"""

import sqlite3
from pathlib import Path

from ..config.settings import DATABASE_PATH


def get_connection():
    """Stellt eine Verbindung zur SQLite-Datenbank her.
    
    Returns:
        sqlite3.Connection: Eine Datenbankverbindung mit Row-Factory
    """
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialisiert die Datenbankstruktur mit den erforderlichen Tabellen.
    
    Erstellt die folgenden Tabellen, falls sie nicht existieren:
    - dokumente: Speichert Dokumentinformationen
    - metadaten_felder: Speichert verfügbare Metadatenfelder
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabelle für Dokumente
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dokumente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dateiname TEXT NOT NULL,
        kategorie TEXT,
        pfad TEXT NOT NULL,
        inhalt_vorschau TEXT,
        erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadaten TEXT
    )
    ''')
    
    # Tabelle für Metadatenfelder
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS metadaten_felder (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feldname TEXT NOT NULL UNIQUE,
        beschreibung TEXT,
        erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Standard-Metadatenfelder einfügen
    standard_felder = [
        ("rechnungsnummer", "Rechnungsnummer des Dokuments"),
        ("kundennummer", "Kundennummer oder Kundenreferenz"),
        ("datum", "Rechnungsdatum im Format TT.MM.JJJJ"),
        ("betrag", "Rechnungsbetrag in Euro")
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO metadaten_felder (feldname, beschreibung) VALUES (?, ?)",
        standard_felder
    )
    
    conn.commit()
    conn.close()