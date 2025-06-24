#!/usr/bin/env python3
"""
Test-Script für Wareneingang-Erkennung und Text-Extraktion.
Testet die PDF-Text-Extraktion und Lieferscheinnummer-Erkennung.
"""

import logging
import os
import re
import sys
from pathlib import Path

# Logging konfigurieren für ausführliche Ausgabe
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("wareneingang_test.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class WareneingangTester:
    """Test-Klasse für Wareneingang-PDF-Analyse."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def test_pdf_file(self, pdf_path: str):
        """
        Testet eine PDF-Datei auf Wareneingang-Erkennung.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
        """
        self.logger.info(f"🔍 Starte Test für PDF: {pdf_path}")
        self.logger.info("=" * 80)
        
        if not os.path.exists(pdf_path):
            self.logger.error(f"❌ PDF-Datei nicht gefunden: {pdf_path}")
            return False
        
        try:
            # 1. Text aus PDF extrahieren
            lines = self._extract_text_from_pdf(pdf_path, max_lines=30)
            
            if not lines:
                self.logger.error("❌ Keine Textzeilen aus PDF extrahiert")
                return False
            
            # 2. Erste 50 Zeichen loggen
            self._log_first_characters(lines)
            
            # 3. Alle Zeilen ausgeben (für Debug)
            self._log_all_lines(lines)
            
            # 4. Wareneingang-Test
            wareneingang_found, lieferscheinnummer = self._test_wareneingang_detection(lines)
            
            # 5. Zusammenfassung
            self._log_summary(pdf_path, wareneingang_found, lieferscheinnummer)
            
            return wareneingang_found
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Testen der PDF: {e}")
            return False
    
    def _extract_text_from_pdf(self, pdf_path: str, max_lines: int = 30) -> list[str]:
        """
        Extrahiert Text aus PDF (erste N Zeilen).
        """
        try:
            import fitz  # PyMuPDF
            
            self.logger.info(f"📖 Öffne PDF mit PyMuPDF: {os.path.basename(pdf_path)}")
            
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                self.logger.warning("⚠️  PDF hat keine Seiten")
                return []
            
            self.logger.info(f"📄 PDF hat {len(doc)} Seite(n)")
            
            # Text von der ersten Seite extrahieren
            page = doc[0]
            text = page.get_text()
            doc.close()
            
            if not text.strip():
                self.logger.warning("⚠️  Keine Textdaten auf erster Seite gefunden")
                self.logger.info("💡 Möglicherweise ist OCR-Verarbeitung erforderlich")
                return []
            
            # In Zeilen aufteilen und bereinigen
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            self.logger.info(f"📝 {len(lines)} Textzeilen extrahiert (davon ersten {max_lines} verwendet)")
            
            return lines[:max_lines]
            
        except ImportError:
            self.logger.error("❌ PyMuPDF (fitz) nicht installiert. Bitte installieren: pip install PyMuPDF")
            return []
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Extrahieren des PDF-Texts: {e}")
            return []
    
    def _log_first_characters(self, lines: list[str]):
        """Loggt die ersten 50 Zeichen der PDF."""
        if not lines:
            return
        
        # Alle Zeilen zu einem String zusammenfügen
        full_text = " ".join(lines)
        
        # Erste 50 Zeichen
        first_50 = full_text[:50]
        
        self.logger.info("📋 ERSTE 50 ZEICHEN DER PDF:")
        self.logger.info(f"   '{first_50}{'...' if len(full_text) > 50 else ''}'")
        self.logger.info(f"   (Gesamtlänge: {len(full_text)} Zeichen)")
        self.logger.info("-" * 60)
    
    def _log_all_lines(self, lines: list[str]):
        """Loggt alle extrahierten Zeilen für Debug-Zwecke."""
        self.logger.info("📄 ALLE EXTRAHIERTEN ZEILEN:")
        
        for i, line in enumerate(lines, 1):
            # Zeile mit Zeilennummer ausgeben
            self.logger.info(f"   {i:2d}: '{line}'")
        
        self.logger.info("-" * 60)
    
    def _test_wareneingang_detection(self, lines: list[str]) -> tuple[bool, str]:
        """
        Testet die Wareneingang-Erkennung und Lieferscheinnummer-Extraktion.
        
        Returns:
            (wareneingang_gefunden, lieferscheinnummer)
        """
        self.logger.info("🔍 WARENEINGANG-ERKENNUNG:")
        
        wareneingang_found = False
        lieferscheinnummer = ""
        
        for i, line in enumerate(lines):
            # Case-insensitive Suche nach "Wareneingang"
            if "wareneingang" in line.lower():
                wareneingang_found = True
                
                self.logger.info(f"✅ 'Wareneingang' gefunden in Zeile {i+1}:")
                self.logger.info(f"   '{line}'")
                
                # Nächste Zeile als potenzielle Lieferscheinnummer
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    
                    self.logger.info(f"📦 Nächste Zeile (potenzielle Lieferscheinnummer):")
                    self.logger.info(f"   Zeile {i+2}: '{next_line}'")
                    
                    # Bereinige die Lieferscheinnummer (nur Buchstaben, Zahlen, Bindestrich)
                    cleaned_number = re.sub(r'[^A-Za-z0-9\-_]', '', next_line)
                    
                    if cleaned_number and len(cleaned_number) >= 3:
                        lieferscheinnummer = cleaned_number
                        self.logger.info(f"✅ Bereinigte Lieferscheinnummer: '{lieferscheinnummer}'")
                    else:
                        self.logger.warning(f"⚠️  Lieferscheinnummer zu kurz oder ungültig: '{cleaned_number}'")
                else:
                    self.logger.warning("⚠️  Keine nächste Zeile für Lieferscheinnummer verfügbar")
                
                break  # Nur die erste Occurrence verwenden
        
        if not wareneingang_found:
            self.logger.info("❌ 'Wareneingang' NICHT gefunden")
            self.logger.info("💡 Überprüfe ob:")
            self.logger.info("   - PDF bereits OCR-verarbeitet ist")
            self.logger.info("   - Text korrekt extrahiert wurde")
            self.logger.info("   - 'Wareneingang' tatsächlich im Dokument steht")
        
        self.logger.info("-" * 60)
        return wareneingang_found, lieferscheinnummer
    
    def _log_summary(self, pdf_path: str, wareneingang_found: bool, lieferscheinnummer: str):
        """Loggt eine Zusammenfassung der Testergebnisse."""
        filename = os.path.basename(pdf_path)
        
        self.logger.info("📊 ZUSAMMENFASSUNG:")
        self.logger.info(f"   📄 Datei: {filename}")
        self.logger.info(f"   🔍 Wareneingang erkannt: {'✅ JA' if wareneingang_found else '❌ NEIN'}")
        
        if lieferscheinnummer:
            self.logger.info(f"   📦 Lieferscheinnummer: '{lieferscheinnummer}'")
        else:
            self.logger.info(f"   📦 Lieferscheinnummer: ❌ Nicht gefunden")
        
        self.logger.info("=" * 80)


def main():
    """Hauptfunktion des Test-Scripts."""
    
    logger.info("🚀 Wareneingang PDF-Test gestartet")
    logger.info("=" * 80)
    
    # Command-line Argument oder Standard-Pfad
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Standard: Nach PDFs im Input-Verzeichnis suchen
        input_dir = Path("backend/pdfs/input")
        
        if input_dir.exists():
            pdf_files = list(input_dir.glob("*.pdf"))
            
            if pdf_files:
                pdf_path = str(pdf_files[0])
                logger.info(f"🎯 Teste erste gefundene PDF: {pdf_path}")
            else:
                logger.error("❌ Keine PDF-Dateien im Input-Verzeichnis gefunden")
                logger.info("💡 Verwendung: python wareneingang_test.py <pfad_zur_pdf>")
                return
        else:
            logger.error("❌ Input-Verzeichnis nicht gefunden: backend/pdfs/input")
            logger.info("💡 Verwendung: python wareneingang_test.py <pfad_zur_pdf>")
            return
    
    # Test durchführen
    tester = WareneingangTester()
    success = tester.test_pdf_file(pdf_path)
    
    # Endergebnis
    if success:
        logger.info("🎉 Test erfolgreich - Wareneingang erkannt!")
    else:
        logger.info("❌ Test fehlgeschlagen - Wareneingang nicht erkannt")
    
    logger.info(f"📝 Detaillierte Logs gespeichert in: wareneingang_test.log")


if __name__ == "__main__":
    main()