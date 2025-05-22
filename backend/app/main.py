import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config.settings import API_PREFIX, CORS_ORIGINS
from .database.connection import init_db
from .routes.dokumente import router as dokumente_router

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# FastAPI-App erstellen
app = FastAPI(
    title="OCR-Dokumentenverwaltungssystem",
    description="API für das OCR-basierte Dokumentenverwaltungssystem",
    version="0.1.0"
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

# Initialisierung beim Start
@app.on_event("startup")
async def startup_event():
    """Wird beim Start der Anwendung ausgeführt."""
    logger.info("Anwendung wird gestartet...")
    
    # Datenbank initialisieren
    init_db()
    
    logger.info("Datenbank initialisiert")
    logger.info("Anwendung ist bereit")


@app.get("/")
async def root():
    """Basisroute für die API."""
    return {
        "message": "OCR-Dokumentenverwaltungssystem API",
        "version": "0.1.0",
        "docs": "/docs"
    }


# Für die direkte Ausführung
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)