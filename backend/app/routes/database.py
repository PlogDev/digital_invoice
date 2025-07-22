"""
Neue Datei: app/routes/database.py
API-Routen für die Datenbankansicht im Frontend
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import joinedload

from ..database.postgres_connection import get_db_session
from ..models.database import (
    ChargenEinkauf,
    ChargenVerkauf,
    Dokument,
    Kategorie,
    LieferscheinExtern,
    LieferscheinIntern,
    MetadatenFeld,
    Unterkategorie,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/tables")
async def get_tables():
    """Liste aller verfügbaren Tabellen."""
    tables = {
        "dokumente": "Dokumente",
        "kategorien": "Kategorien", 
        "unterkategorien": "Unterkategorien",
        "metadaten_felder": "Metadatenfelder",
        "lieferscheine_extern": "Externe Lieferscheine",
        "lieferscheine_intern": "Interne Lieferscheine",
        "chargen_einkauf": "Chargen Einkauf",
        "chargen_verkauf": "Chargen Verkauf"
    }
    return {"tables": tables}


@router.get("/tables/{table_name}")
async def get_table_data(table_name: str, limit: int = 100):
    """Daten einer bestimmten Tabelle abrufen."""
    
    try:
        with get_db_session() as session:
            if table_name == "dokumente":
                query = session.query(Dokument)\
                    .options(joinedload(Dokument.unterkategorie))\
                    .limit(limit)
                items = query.all()
                data = []
                for item in items:
                    data.append({
                        "id": item.id,
                        "dateiname": item.dateiname,
                        "kategorie_id": item.kategorie_id,
                        "unterkategorie_id": item.unterkategorie_id,
                        "unterkategorie_name": item.unterkategorie.name if item.unterkategorie else None,
                        "pfad": item.pfad,
                        "inhalt_vorschau": item.inhalt_vorschau[:100] + "..." if item.inhalt_vorschau and len(item.inhalt_vorschau) > 100 else item.inhalt_vorschau,
                        "erstellt_am": item.erstellt_am.isoformat() if item.erstellt_am else None,
                        "metadaten": item.metadaten
                    })
                    
            elif table_name == "kategorien":
                items = session.query(Kategorie).limit(limit).all()
                data = [{"id": item.id, "name": item.name, "beschreibung": item.beschreibung, 
                        "erstellt_am": item.erstellt_am.isoformat() if item.erstellt_am else None} for item in items]
                        
            elif table_name == "unterkategorien":
                query = session.query(Unterkategorie)\
                    .options(joinedload(Unterkategorie.kategorie))\
                    .limit(limit)
                items = query.all()
                data = []
                for item in items:
                    data.append({
                        "id": item.id,
                        "kategorie_id": item.kategorie_id,
                        "kategorie_name": item.kategorie.name if item.kategorie else None,
                        "name": item.name,
                        "beschreibung": item.beschreibung,
                        "erstellt_am": item.erstellt_am.isoformat() if item.erstellt_am else None
                    })
                    
            elif table_name == "metadaten_felder":
                items = session.query(MetadatenFeld).limit(limit).all()
                data = [{"id": item.id, "feldname": item.feldname, "beschreibung": item.beschreibung,
                        "erstellt_am": item.erstellt_am.isoformat() if item.erstellt_am else None} for item in items]
                        
            elif table_name == "lieferscheine_extern":
                query = session.query(LieferscheinExtern)\
                    .options(joinedload(LieferscheinExtern.dokument))\
                    .limit(limit)
                items = query.all()
                data = []
                for item in items:
                    data.append({
                        "id": item.id,
                        "lieferscheinnummer": item.lieferscheinnummer,
                        "dokument_id": item.dokument_id,
                        "dokument_name": item.dokument.dateiname if item.dokument else None,
                        "csv_importiert": item.csv_importiert,
                        "erstellt_am": item.erstellt_am.isoformat() if item.erstellt_am else None
                    })
                    
            elif table_name == "lieferscheine_intern":
                query = session.query(LieferscheinIntern)\
                    .options(joinedload(LieferscheinIntern.dokument))\
                    .limit(limit)
                items = query.all()
                data = []
                for item in items:
                    data.append({
                        "id": item.id,
                        "lieferscheinnummer": item.lieferscheinnummer,
                        "dokument_id": item.dokument_id,
                        "dokument_name": item.dokument.dateiname if item.dokument else None,
                        "csv_importiert": item.csv_importiert,
                        "erstellt_am": item.erstellt_am.isoformat() if item.erstellt_am else None
                    })
                    
            elif table_name == "chargen_einkauf":
                query = session.query(ChargenEinkauf)\
                    .options(joinedload(ChargenEinkauf.lieferschein_extern))\
                    .limit(limit)
                items = query.all()
                data = []
                for item in items:
                    data.append({
                        "id": item.id,
                        "lieferschein_extern_id": item.lieferschein_extern_id,
                        "lieferscheinnummer": item.lieferschein_extern.lieferscheinnummer if item.lieferschein_extern else None,
                        "artikel": item.artikel,
                        "materialnr": item.materialnr,
                        "menge": item.menge,
                        "lieferdatum": item.lieferdatum,
                        "erstellt_am": item.erstellt_am.isoformat() if item.erstellt_am else None
                    })
                    
            elif table_name == "chargen_verkauf":
                query = session.query(ChargenVerkauf)\
                    .options(joinedload(ChargenVerkauf.lieferschein_intern))\
                    .limit(limit)
                items = query.all()
                data = []
                for item in items:
                    data.append({
                        "id": item.id,
                        "lieferschein_intern_id": item.lieferschein_intern_id,
                        "lieferscheinnummer": item.lieferschein_intern.lieferscheinnummer if item.lieferschein_intern else None,
                        "artikel": item.artikel,
                        "materialnr": item.materialnr,
                        "menge": item.menge,
                        "charge": item.charge,
                        "lieferdatum": item.lieferdatum,
                        "erstellt_am": item.erstellt_am.isoformat() if item.erstellt_am else None
                    })
                    
            else:
                raise HTTPException(status_code=404, detail=f"Tabelle '{table_name}' nicht gefunden")
                
            return {
                "table_name": table_name,
                "count": len(data),
                "data": data
            }
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tabellendaten: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Daten: {str(e)}")


@router.get("/stats")
async def get_database_stats():
    """Allgemeine Datenbankstatistiken."""
    try:
        with get_db_session() as session:
            stats = {
                "dokumente_count": session.query(Dokument).count(),
                "kategorien_count": session.query(Kategorie).count(),
                "unterkategorien_count": session.query(Unterkategorie).count(),
                "metadaten_felder_count": session.query(MetadatenFeld).count(),
                "lieferscheine_extern_count": session.query(LieferscheinExtern).count(),
                "lieferscheine_intern_count": session.query(LieferscheinIntern).count(),
                "chargen_einkauf_count": session.query(ChargenEinkauf).count(),
                "chargen_verkauf_count": session.query(ChargenVerkauf).count()
            }
            
            return {"stats": stats}
            
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Statistiken: {str(e)}")