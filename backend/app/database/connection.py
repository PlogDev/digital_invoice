"""
Datenbankverbindung und Initialisierungsfunktionen.
Erweitert um Lieferschein-Tabellen.
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
    - lieferscheine: Speichert Lieferschein-Grunddaten
    - lieferschein_datensaetze: Speichert CSV-Daten zu Lieferscheinen
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bestehende Tabelle für Dokumente
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
    
    # Bestehende Tabelle für Metadatenfelder
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS metadaten_felder (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feldname TEXT NOT NULL UNIQUE,
        beschreibung TEXT,
        erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # NEU: Tabelle für Lieferscheine
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lieferscheine (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lieferscheinnummer TEXT NOT NULL UNIQUE,
        dokument_id INTEGER NOT NULL,
        csv_importiert BOOLEAN DEFAULT 0,
        erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dokument_id) REFERENCES dokumente (id) ON DELETE CASCADE
    )
    ''')
    
    # NEU: Tabelle für Lieferschein-Datensätze (alle CSV-Spalten)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lieferschein_datensaetze (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lieferschein_id INTEGER NOT NULL,
        linr TEXT,
        liname TEXT,
        name1 TEXT,
        belfd TEXT,
        tlnr TEXT,
        auart TEXT,
        aftnr TEXT,
        aps TEXT,
        absn TEXT,
        atnr TEXT,
        artikel TEXT,
        materialnr TEXT,
        urlnd TEXT,
        wartarnr TEXT,
        menge TEXT,
        erfmenge TEXT,
        gebindeme TEXT,
        snnr TEXT,
        snnralt TEXT,
        einzelek TEXT,
        lieferscheinnr TEXT,
        lieferdatum TEXT,
        renrex TEXT,
        redat TEXT,
        bidser TEXT,
        bid TEXT,
        erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lieferschein_id) REFERENCES lieferscheine (id) ON DELETE CASCADE
    )
    ''')
    
    # Index für bessere Performance bei Lieferscheinnummer-Suchen
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_lieferscheinnummer 
    ON lieferscheine (lieferscheinnummer)
    ''')
    
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_csv_lieferscheinnr 
    ON lieferschein_datensaetze (lieferscheinnr)
    ''')
    
    # Standard-Metadatenfelder einfügen (bestehend)
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