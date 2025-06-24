"""
Konfigurationseinstellungen für die Anwendung.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# Basispfade
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PDF_DIR = BASE_DIR / "pdfs"

# PDF-Verzeichnisse
PDF_INPUT_DIR = PDF_DIR / "input"
PDF_PROCESSED_DIR = PDF_DIR / "processed"
CSV_LIST_DIR = PDF_DIR / "csv_lists"


# Kategorien und deren Verzeichnisse
PDF_CATEGORIES = {
    "berta": PDF_PROCESSED_DIR / "berta",
    "kosten": PDF_PROCESSED_DIR / "kosten",
    "irrlaeufer": PDF_PROCESSED_DIR / "irrlaeufer"
}

# Datenbank
DATABASE_PATH = BASE_DIR / "dokumente.db"

# OCR-Einstellungen
TESSERACT_CMD = r"tesseract"  # Pfad zu tesseract.exe unter Windows anpassen
OCR_LANGUAGE = "deu"  # OCR-Sprache: Deutsch
OCR_PREVIEW_LENGTH = 100  # Anzahl der Zeichen für die Vorschau

# API
API_PREFIX = "/api"
CORS_ORIGINS = ["*"]  # Für Produktivbetrieb einschränken

# Stellen sicher, dass alle Verzeichnisse existieren
for path in [PDF_INPUT_DIR] + list(PDF_CATEGORIES.values()):
    os.makedirs(path, exist_ok=True)

class Settings:
    """Einstellungsklasse zum einfachen Zugriff auf Konfigurationswerte."""
    
    @classmethod
    def load_config(cls) -> dict:
        """Lädt Konfiguration aus Datei oder verwendet Standardwerte."""
        config_path = BASE_DIR / "config.json"
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Standardkonfiguration
        return {
            "pdf_dirs": {
                "input": str(PDF_INPUT_DIR),
                "categories": {
                    "berta": str(PDF_CATEGORIES["berta"]),
                    "kosten": str(PDF_CATEGORIES["kosten"]),
                    "irrlaeufer": str(PDF_CATEGORIES["irrlaeufer"])
                }
            },
            "ocr": {
                "language": OCR_LANGUAGE,
                "preview_length": OCR_PREVIEW_LENGTH
            },
            "tesseract_path": TESSERACT_CMD
        }
    
    @classmethod
    def save_config(cls, config: dict) -> bool:
        """Speichert Konfiguration in Datei."""
        config_path = BASE_DIR / "config.json"
        
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            return True
        except IOError:
            return False

# Globale Einstellungsinstanz
settings = Settings()