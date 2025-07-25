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

# ✅ KORRIGIERTE Swagger UI und ReDoc
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Korrigierte Swagger UI."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>OCR-Dokumentenverwaltung API</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin:0; background: #fafafa; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script>
        try {
            SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            });
        } catch(error) {
            document.getElementById('swagger-ui').innerHTML = `
                <div style="padding: 2rem; text-align: center; font-family: Arial;">
                    <h1>⚠️ Swagger UI Fehler</h1>
                    <p>JavaScript-Fehler: ${error.message}</p>
                    <p><a href="/docs-simple">Zur einfachen API-Übersicht</a></p>
                    <p><a href="/openapi.json">OpenAPI JSON herunterladen</a></p>
                </div>
            `;
        }
    </script>
</body>
</html>
    """)

@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """Korrigierte ReDoc."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>OCR-Dokumentenverwaltung API - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; }
        redoc { display: block; }
    </style>
</head>
<body>
    <redoc spec-url='/openapi.json'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    <script>
        // Fallback falls ReDoc nicht lädt
        setTimeout(function() {
            if (!document.querySelector('redoc').innerHTML.trim()) {
                document.body.innerHTML = `
                    <div style="padding: 2rem; text-align: center; font-family: Arial;">
                        <h1>⚠️ ReDoc konnte nicht geladen werden</h1>
                        <p>Alternativen:</p>
                        <ul style="text-align: left; display: inline-block;">
                            <li><a href="/docs">Swagger UI</a></li>
                            <li><a href="/docs-simple">Einfache API-Übersicht</a></li>
                            <li><a href="/openapi.json">OpenAPI JSON</a></li>
                        </ul>
                    </div>
                `;
            }
        }, 3000);
    </script>
</body>
</html>
    """)

# Alternative: Vollständig lokale Lösung
@app.get("/docs-simple", include_in_schema=False)
async def simple_api_docs():
    """Einfache API-Dokumentation ohne externe Dependencies."""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>OCR-Dokumentenverwaltung API</title>
    <style>
        body { font-family: Arial; margin: 2rem; line-height: 1.6; }
        .endpoint { margin: 1rem 0; padding: 1rem; border: 1px solid #ddd; }
        .method { font-weight: bold; color: #fff; padding: 0.2rem 0.5rem; border-radius: 3px; }
        .get { background: #61affe; }
        .post { background: #49cc90; }
        .put { background: #fca130; }
        .delete { background: #f93e3e; }
    </style>
</head>
<body>
    <h1>🔧 OCR-Dokumentenverwaltung API</h1>
    <p><strong>OpenAPI Schema:</strong> <a href="/openapi.json">/openapi.json</a></p>
    
    <h2>📁 Hauptendpunkte:</h2>
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/dokumente/</code> - Alle Dokumente
    </div>
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/dokumente/{id}</code> - Einzelnes Dokument
    </div>
    <div class="endpoint">
        <span class="method post">POST</span> <code>/api/dokumente/smb/configure</code> - SMB konfigurieren
    </div>
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/dokumente/smb/status</code> - SMB Status
    </div>
    <div class="endpoint">
        <span class="method post">POST</span> <code>/api/dokumente/smb/sync</code> - SMB Sync
    </div>
    
    <h2>🗄️ Datenbank:</h2>
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/database/stats</code> - DB Statistiken
    </div>
    <div class="endpoint">
        <span class="method get">GET</span> <code>/api/database/tables/{table}</code> - Tabellendaten
    </div>
    
    <p><em>Für vollständige API-Tests nutze das OpenAPI JSON Schema mit einem externen Tool wie Postman.</em></p>
</body>
</html>
    """)

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