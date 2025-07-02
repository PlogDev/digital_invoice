# PostgreSQL Setup für OCR-Dokumentenverwaltung

## Was ist PostgreSQL?
PostgreSQL ist eine richtige Datenbank (im Gegensatz zu SQLite). Sie kann:
- Mehrere Benutzer gleichzeitig verwalten
- Komplexe Transaktionen
- JSON-Daten speichern (perfekt für unsere Metadaten)
- Mit Paperless NGX kommunizieren

## Schritt 1: PostgreSQL starten

```bash
# Im Hauptverzeichnis des Projekts
docker-compose up -d postgres
```

**Was passiert:**
- Docker lädt PostgreSQL herunter
- Erstellt Datenbank "ocr_docs" 
- Benutzer "ocr_user" mit Passwort "ocr_secure_2024"
- Läuft auf Port 5432

## Schritt 2: Prüfen ob es läuft

```bash
# Status prüfen
docker-compose ps

# Logs anschauen
docker-compose logs postgres

# Sollte sowas zeigen:
# "database system is ready to accept connections"
```

## Schritt 3: In die Datenbank reinschauen (optional)

```bash
# Mit PostgreSQL verbinden
docker exec -it ocr_postgres psql -U ocr_user -d ocr_docs

# Dann kannst du SQL-Befehle ausführen:
# \dt     - Tabellen anzeigen
# \q      - Beenden
```

## Schritt 4: Datenbank stoppen/starten

```bash
# Stoppen
docker-compose down

# Nur PostgreSQL stoppen
docker-compose stop postgres

# Wieder starten
docker-compose up -d postgres

# Alles löschen und neu starten (ACHTUNG: Daten weg!)
docker-compose down -v
docker-compose up -d postgres
```

## Connection String für Python

```python
DATABASE_URL = "postgresql://ocr_user:ocr_secure_2024@localhost:5432/ocr_docs"
```

## Services und Ports

- **PostgreSQL:** localhost:5432
- **Backend API:** localhost:8080 (nicht 8000 wegen Paperless NGX!)
- **Frontend:** localhost:3000

## Development Workflow

```bash
# Nur PostgreSQL starten (für lokale Entwicklung)
docker-compose up -d postgres

# Oder alles starten (Production-ähnlich)
docker-compose --profile production up -d

# Backend lokal entwickeln
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Frontend lokal entwickeln  
cd frontend
npm run dev
```

## Troubleshooting

**Problem:** Port 5432 schon belegt
```bash
# Anderen Service stoppen oder Port ändern in docker-compose.yml
ports:
  - "5433:5432"  # Dann localhost:5433 verwenden
```

**Problem:** Datenbank zurücksetzen
```bash
docker-compose down -v  # ACHTUNG: Löscht alle Daten!
docker-compose up -d postgres
