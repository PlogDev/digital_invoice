import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config.settings import API_PREFIX, CORS_ORIGINS

# GEÄNDERT: PostgreSQL statt SQLite
from .database.postgres_connection import init_database
from .routes.dokumente import router as dokumente_router
from .services.ocr_scheduler import ocr_scheduler

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# OCRmyPDF-Logs dämpfen (weniger Spam)
logging.getLogger('ocrmypdf').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan-Manager für Startup/Shutdown-Events."""
    # Startup
    logger.info("Anwendung wird gestartet...")
    
    # GEÄNDERT: PostgreSQL-Datenbank initialisieren
    try:
        init_database()
        logger.info("PostgreSQL-Datenbank initialisiert")
    except Exception as e:
        logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
        # Trotzdem weitermachen für Development
        logger.warning("Starte ohne Datenbank-Verbindung (nur für Development!)")
    
    # OCR-Scheduler starten
    try:
        await ocr_scheduler.start()
        logger.info("OCR-Scheduler gestartet")
    except Exception as e:
        logger.error(f"Fehler beim Starten des OCR-Schedulers: {e}")
    
    logger.info("Anwendung ist bereit")
    
    yield
    
    # Shutdown
    logger.info("Anwendung wird heruntergefahren...")
    try:
        await ocr_scheduler.stop()
        logger.info("OCR-Scheduler gestoppt")
    except Exception as e:
        logger.error(f"Fehler beim Stoppen des OCR-Schedulers: {e}")


# FastAPI-App erstellen
app = FastAPI(
    title="OCR-Dokumentenverwaltungssystem",
    description="API für das OCR-basierte Dokumentenverwaltungssystem",
    version="0.2.0",  # Version erhöht für PostgreSQL
    lifespan=lifespan
)

# CORS-Middleware hinzufügen
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stelle sicher, dass der Pfad existiert
PDF_DIR = Path(__file__).resolve().parent.parent / "pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

# Statische Dateien bereitstellen
app.mount("/pdfs", StaticFiles(directory=str(PDF_DIR)), name="pdfs")

# Routen registrieren
app.include_router(dokumente_router, prefix=API_PREFIX)


@app.get("/")
async def root():
    """Basisroute für die API."""
    return {
        "message": "OCR-Dokumentenverwaltungssystem API",
        "version": "0.2.0",
        "database": "PostgreSQL",
        "docs": "/docs",
        "ocr_scheduler": {
            "running": ocr_scheduler.running,
            "processed_files": len(ocr_scheduler.processed_files)
        }
    }


@app.post("/api/ocr/force-check")
async def force_ocr_check():
    """Löst eine manuelle OCR-Prüfung aus."""
    ocr_scheduler.force_check()
    return {
        "success": True,
        "message": "OCR-Prüfung wurde ausgelöst"
    }


# Für die direkte Ausführung
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)