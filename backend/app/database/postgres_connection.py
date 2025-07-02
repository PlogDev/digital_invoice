"""
PostgreSQL Datenbankverbindung mit SQLAlchemy
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator

from app.models.database import Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# Database URL aus Environment oder Default
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://ocr_user:ocr_secure_2024@localhost:5432/ocr_docs"
)

# SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Überprüft Verbindung vor Verwendung
    pool_recycle=300,    # Verbindungen nach 5 Minuten erneuern
    echo=False           # SQL-Queries loggen (für Development auf True setzen)
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def create_tables():
    """
    Erstellt alle Tabellen in der Datenbank.
    Wird beim ersten Start aufgerufen.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Alle Tabellen erfolgreich erstellt/aktualisiert")
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen der Tabellen: {e}")
        raise

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager für DB-Sessions mit automatischem Commit/Rollback.
    
    Usage:
        with get_db_session() as session:
            dokument = session.query(Dokument).first()
            # ... operations
            # session.commit() automatisch am Ende
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency für DB-Sessions.
    
    Usage in FastAPI:
        @app.get("/")
        def get_data(db: Session = Depends(get_db)):
            return db.query(Dokument).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection() -> bool:
    """
    Testet die Datenbankverbindung.
    Returns True wenn erfolgreich, False bei Fehler.
    """
    try:
        # Alternative: Engine direkt testen
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("✅ Datenbankverbindung erfolgreich getestet")
        return True
    except Exception as e:
        logger.error(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
        return False

def init_database():
    """
    Initialisiert die Datenbank komplett:
    1. Testet Verbindung
    2. Erstellt Tabellen
    3. Fügt Seed-Daten hinzu
    """
    logger.info("🔄 Initialisiere PostgreSQL-Datenbank...")
    
    # 1. Verbindung testen
    if not test_connection():
        raise Exception("Datenbankverbindung fehlgeschlagen!")
    
    # 2. Tabellen erstellen
    create_tables()
    
    # 3. Seed-Daten einfügen
    from app.database.seed_data import insert_seed_data
    insert_seed_data()
    
    logger.info("✅ Datenbank-Initialisierung abgeschlossen")

# Für Backward Compatibility - falls alte SQLite-Funktionen noch verwendet werden
def get_connection():
    """
    DEPRECATED: Für Kompatibilität mit altem SQLite-Code.
    Verwende stattdessen get_db_session() oder get_db().
    """
    logger.warning("get_connection() ist deprecated. Verwende get_db_session()")
    return SessionLocal()