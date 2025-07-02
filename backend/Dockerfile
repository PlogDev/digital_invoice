# Python 3.10 als Basis
FROM python:3.10-slim

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

# Port freigeben
EXPOSE 8080

# Health-Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Startup-Command mit Port 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]