# PowerShell Script fuer Windows (ohne Emojis)
Write-Host "OCR-Dokumentenverwaltung Setup" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green

# PostgreSQL starten
Write-Host "Starte PostgreSQL..." -ForegroundColor Yellow
docker-compose up -d postgres

# Warten bis PostgreSQL bereit ist
Write-Host "Warte auf PostgreSQL..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0

do {
    $attempt++
    Write-Host "   Versuch $attempt/$maxAttempts..." -ForegroundColor Gray
    
    $result = docker-compose exec postgres pg_isready -U ocr_user -d ocr_docs 2>$null
    if ($LASTEXITCODE -eq 0) {
        break
    }
    
    Start-Sleep -Seconds 2
} while ($attempt -lt $maxAttempts)

if ($attempt -ge $maxAttempts) {
    Write-Host "PostgreSQL konnte nicht gestartet werden!" -ForegroundColor Red
    exit 1
}

Write-Host "PostgreSQL laeuft auf Port 5432" -ForegroundColor Green

# Auswahl: Lokal entwickeln oder alles in Docker
Write-Host ""
Write-Host "Waehle Development-Modus:" -ForegroundColor Cyan
Write-Host "1) Lokal entwickeln (empfohlen)" -ForegroundColor White
Write-Host "2) Alles in Docker" -ForegroundColor White
$choice = Read-Host "Eingabe (1/2)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Lokale Entwicklung:" -ForegroundColor Cyan
        Write-Host "Backend:  cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload" -ForegroundColor White
        Write-Host "Frontend: cd frontend && npm run dev" -ForegroundColor White
        Write-Host ""
        Write-Host "URLs:" -ForegroundColor Yellow
        Write-Host "- API: http://localhost:8080" -ForegroundColor White
        Write-Host "- Frontend: http://localhost:3000" -ForegroundColor White
    }
    "2" {
        Write-Host "Starte alle Services in Docker..." -ForegroundColor Yellow
        docker-compose --profile production up -d
        Write-Host ""
        Write-Host "URLs:" -ForegroundColor Yellow
        Write-Host "- API: http://localhost:8080" -ForegroundColor White
        Write-Host "- Frontend: http://localhost:3000" -ForegroundColor White
    }
    default {
        Write-Host "Ungueltinge Eingabe" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Setup abgeschlossen!" -ForegroundColor Green
Write-Host "PostgreSQL: localhost:5432" -ForegroundColor Cyan