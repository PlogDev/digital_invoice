# Python 3.11
FROM python:3.11-slim

# System-Updates und OCR-Dependencies installieren
RUN apt-get update && apt-get install -y \
    # Tesseract OCR + deutsche Sprache
    tesseract-ocr \
    tesseract-ocr-deu \
    # PDF-Tools
    poppler-utils \
    ghostscript \
    # OCRmyPDF Dependencies
    unpaper \
    qpdf \
    # Tesseract-Libraries
    liblept5 \
    libtesseract5 \
    # Build-Tools (falls nötig)
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Python-Dependencies zuerst (für besseres Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# Tesseract-Pfad für pytesseract setzen
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV PYTHONPATH=/app

# Port freigeben (8081 statt 8080)
EXPOSE 8081

# Health-Check (korrigierter Port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8081/ || exit 1

# Startup-Command mit Port 8081 (wie in settings.py)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]