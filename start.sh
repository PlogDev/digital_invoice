#!/bin/bash

echo "🚀 OCR-Dokumentenverwaltung Setup"
echo "================================="

# PostgreSQL starten
echo "📊 Starte PostgreSQL..."
docker-compose up -d postgres

# Warten bis PostgreSQL bereit ist
echo "⏳ Warte auf PostgreSQL..."
until docker-compose exec postgres pg_isready -U ocr_user -d ocr_docs >/dev/null 2>&1; do
    echo "   PostgreSQL noch nicht bereit, warte..."
    sleep 2
done

echo "✅ PostgreSQL läuft auf Port 5432"

# Auswahl: Lokal entwickeln oder alles in Docker
echo ""
echo "Wähle Development-Modus:"
echo "1) Lokal entwickeln (empfohlen)"
echo "2) Alles in Docker"
read -p "Eingabe (1/2): " choice

case $choice in
    1)
        echo ""
        echo "🔧 Lokale Entwicklung:"
        echo "Backend:  cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"
        echo "Frontend: cd frontend && npm run dev"
        echo ""
        echo "URLs:"
        echo "- API: http://localhost:8080"
        echo "- Frontend: http://localhost:3000"
        ;;
    2)
        echo "🐳 Starte alle Services in Docker..."
        docker-compose --profile production up -d
        echo ""
        echo "URLs:"
        echo "- API: http://localhost:8080"
        echo "- Frontend: http://localhost:3000"
        ;;
    *)
        echo "❌ Ungültige Eingabe"
        exit 1
        ;;
esac

echo ""
echo "🎉 Setup abgeschlossen!"
echo "🗄️  PostgreSQL: localhost:5432"