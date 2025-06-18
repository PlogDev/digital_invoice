# OCR-Dokumentenverwaltungssystem

Ein System zur OCR-basierten Erfassung und Kategorisierung von PDF-Dokumenten.

## Projektstruktur

- `backend/`: Python/FastAPI-Backend mit OCR-Funktionalität
- `frontend/`: React/Tailwind-Frontend

## Erste Schritte

### Backend

1. Wechseln Sie ins Backend-Verzeichnis: `cd backend`
2. Installieren Sie die Abhängigkeiten: `pip install -r requirements.txt`
3. Starten Sie den Server: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

### Frontend

1. Wechseln Sie ins Frontend-Verzeichnis: `cd frontend`
2. Installieren Sie die Abhängigkeiten: `npm install`
3. Starten Sie die Entwicklungsumgebung: `npm run dev`
