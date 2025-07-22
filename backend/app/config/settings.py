"""
Konfigurationseinstellungen für das OCR-Dokumentenverwaltungssystem.
Aktualisiert für PostgreSQL statt SQLite.
"""

import os
from pathlib import Path

# Basis-Verzeichnis des Projekts
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ENTFERNT: DATABASE_PATH (war für SQLite)
# Jetzt verwenden wir PostgreSQL über DATABASE_URL

# PDF-Verzeichnisse
PDF_BASE_DIR = BASE_DIR / "pdfs"
PDF_INPUT_DIR = PDF_BASE_DIR / "input"
PDF_PROCESSED_DIR = PDF_BASE_DIR / "processed"

# CSV-Verzeichnis für Lieferschein-Daten
CSV_LIST_DIR = PDF_BASE_DIR / "csv_lists"

# Kategorie-Verzeichnisse (Legacy - könnte später entfernt werden)
PDF_CATEGORIES = {
    "berta": PDF_PROCESSED_DIR / "berta",
    "kosten": PDF_PROCESSED_DIR / "kosten", 
    "irrlaeufer": PDF_PROCESSED_DIR / "irrlaeufer"
}

# Verzeichnisse erstellen
for directory in [PDF_INPUT_DIR, PDF_PROCESSED_DIR, CSV_LIST_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

for category_dir in PDF_CATEGORIES.values():
    category_dir.mkdir(parents=True, exist_ok=True)

# OCR-Einstellungen
OCR_LANGUAGE = "deu"

# API-Einstellungen
API_PREFIX = "/api"
CORS_ORIGINS = [
    "http://localhost:5173",  # Frontend Development
    "http://localhost:8081",  # Backend
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8081",
]

# PostgreSQL-Einstellungen (aus Environment oder Default)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://ocr_user:ocr_secure_2024@localhost:5432/ocr_docs"
)

# Server-Port (für Docker)
PORT = int(os.getenv("PORT", 8081))