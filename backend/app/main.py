# app/main.py
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config.settings import API_PREFIX, CORS_ORIGINS
from .database.postgres_connection import init_database
from .routes.database import router as database_router  # NEU: Database-Routes
from .routes.dokumente import router as dokumente_router
from .routes.smb_routes import router as smb_router
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


# FastAPI-App erstellen - HARDCORE FIX für Swagger UI
app = FastAPI(
    title="OCR-Dokumentenverwaltungssystem",
    description="API für das OCR-basierte Dokumentenverwaltungssystem mit SMB-Integration",
    version="0.2.0",
    lifespan=lifespan,
    docs_url=None,  # ✅ FIX: Deaktivieren, wir erstellen eigene
    redoc_url=None,  # ✅ FIX: Deaktivieren, wir erstellen eigene
    openapi_url="/openapi.json"
)

# CORS-Middleware hinzufügen - VEREINFACHT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ FIX: Alles erlauben für Development
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
@app.get("/debug/routes")
async def debug_routes():
    """Debug: Zeigt alle verfügbaren Routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
    return {"routes": routes}

# Routen registrieren (NACH dem debug endpoint)
app.include_router(dokumente_router, prefix=API_PREFIX)
app.include_router(database_router, prefix=API_PREFIX)
app.include_router(smb_router, prefix=API_PREFIX)  # SMB-Router hinzufügen

# ✅ HARDCORE FIX: Eigene Swagger UI mit funktionierenden CDN-Links
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI mit funktionierenden CDN-Links."""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="OCR-Dokumentenverwaltung API",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Custom ReDoc mit funktionierenden CDN-Links."""
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="OCR-Dokumentenverwaltung API",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.2/bundles/redoc.standalone.js",
    )

@app.get("/")
async def root():
    """Basisroute für die API."""
    return {
        "message": "OCR-Dokumentenverwaltungssystem API",
        "version": "0.2.0",
        "database": "PostgreSQL",
        "docs": "/docs",
        "redoc": "/redoc",
        "debug_routes": "/debug/routes",
        "database_viewer": "/api/database/stats", 
        "smb_status": "/api/dokumente/smb/status",
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


# Für die direkte Ausführung - FIX: Port 8081 wie in Docker
if __name__ == "__main__":
    # ✅ FIX: Port auf 8081 wie in docker-compose
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8081,  # Geändert von 8080 auf 8081
        reload=True,
        # ✅ FIX: Zusätzliche Uvicorn-Konfiguration für bessere Swagger UI
        log_level="info",
        access_log=True
    )