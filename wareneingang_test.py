#!/usr/bin/env python3
"""
Kombinierter Test: PDF-Extraktion + CSV-Matching + Full Workflow.
Testet den kompletten Wareneingang-Prozess von A bis Z.
"""

import csv
import logging
import os
import re
import sys
from pathlib import Path

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("combined_test.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class WareneingangFullTester:
    """Vollständiger Test des Wareneingang-Systems."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.csv_list_dir = Path("backend/pdfs/csv_lists")
    
    def test_full_workflow(self, pdf_path: str):
        """
        Testet den kompletten Workflow:
        1. PDF-Text-Extraktion  
        2. Wareneingang-Erkennung
        3. Lieferscheinnummer-Extraktion
        4. CSV-Loading
        5. Matching-Test
        6. Simulierter DB-Import
        """
        self.logger.info("🚀 Starte VOLLSTÄNDIGEN Wareneingang-Test")
        self.logger.info("=" * 80)
        
        if not os.path.exists(pdf_path):
            self.logger.error(f"❌ PDF nicht gefunden: {pdf_path}")
            return False
        
        # 1. PDF-Analyse
        wareneingang_found, extracted_nummer = self._test_pdf_extraction(pdf_path)
        
        if not wareneingang_found:
            self.logger.error("❌ Workflow gestoppt - Kein Wareneingang erkannt")
            return False
        
        if not extracted_nummer:
            self.logger.error("❌ Workflow gestoppt - Keine Lieferscheinnummer extrahiert")
            return False
        
        # 2. CSV-Analyse 
        csv_data = self._load_csv_data()
        
        if not csv_data:
            self.logger.error("❌ Workflow gestoppt - Keine CSV-Daten")
            return False
        
        # 3. Matching-Test
        matches = self._test_csv_matching(csv_data, extracted_nummer)
        
        # 4. Ergebnis-Simulation
        self._simulate_db_import(extracted_nummer, matches)
        
        # 5. Zusammenfassung
        self._final_summary(pdf_path, extracted_nummer, len(matches))
        
        return len(matches) > 0
    
    def _test_pdf_extraction(self, pdf_path: str) -> tuple[bool, str]:
        """Testet PDF-Text-Extraktion und Lieferscheinnummer-Erkennung."""
        self.logger.info("📄 SCHRITT 1: PDF-Analyse")
        self.logger.info("-" * 40)
        
        # Text extrahieren
        lines = self._extract_text_from_pdf(pdf_path, max_lines=30)
        
        if not lines:
            self.logger.error("❌ Keine Textzeilen aus PDF extrahiert")
            return False, ""
        
        # Erste 50 Zeichen
        full_text = " ".join(lines)
        first_50 = full_text[:50]
        self.logger.info(f"📝 Erste 50 Zeichen: '{first_50}...'")
        
        # Wareneingang suchen
        wareneingang_found = False
        extracted_nummer = ""
        
        for i, line in enumerate(lines):
            self.logger.info(f"   {i+1:2d}: '{line}'")
            
            if "wareneingang" in line.lower():
                wareneingang_found = True
                self.logger.info(f"✅ 'Wareneingang' gefunden in Zeile {i+1}")
                
                # Nächste Zeile
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    self.logger.info(f"📦 Nächste Zeile (roh): '{next_line}'")
                    
                    # Bereinigung
                    cleaned = re.sub(r'[^A-Za-z0-9\-_]', '', next_line)
                    
                    if cleaned and len(cleaned) >= 3:
                        extracted_nummer = cleaned
                        self.logger.info(f"✅ Extrahierte Lieferscheinnummer: '{extracted_nummer}'")
                    else:
                        self.logger.warning(f"⚠️  Lieferscheinnummer ungültig: '{cleaned}'")
                break
        
        if not wareneingang_found:
            self.logger.error("❌ 'Wareneingang' nicht gefunden!")
        
        self.logger.info("-" * 40)
        return wareneingang_found, extracted_nummer
    
    def _extract_text_from_pdf(self, pdf_path: str, max_lines: int = 30) -> list[str]:
        """Extrahiert Text aus PDF."""
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                return []
            
            page = doc[0]
            text = page.get_text()
            doc.close()
            
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return lines[:max_lines]
            
        except Exception as e:
            self.logger.error(f"PDF-Extraktion fehlgeschlagen: {e}")
            return []
    
    def _load_csv_data(self) -> list:
        """Lädt CSV-Daten wie im WareneingangProcessor."""
        self.logger.info("📊 SCHRITT 2: CSV-Daten laden")
        self.logger.info("-" * 40)
        
        if not self.csv_list_dir.exists():
            self.logger.error(f"❌ CSV-Verzeichnis nicht gefunden: {self.csv_list_dir}")
            return []
        
        all_csv_data = []
        
        for csv_file in self.csv_list_dir.glob("*.csv"):
            try:
                csv_data = self._load_single_csv(csv_file)
                if csv_data:
                    all_csv_data.extend(csv_data)
                    self.logger.info(f"✅ {csv_file.name}: {len(csv_data)} Datensätze")
            except Exception as e:
                self.logger.error(f"❌ Fehler beim Laden von {csv_file.name}: {e}")
        
        self.logger.info(f"📋 Gesamt: {len(all_csv_data)} CSV-Datensätze geladen")
        self.logger.info("-" * 40)
        return all_csv_data
    
    def _load_single_csv(self, csv_path: Path) -> list:
        """Lädt eine CSV-Datei wie im WareneingangProcessor."""
        try:
            csv_data = []
            
            # Encoding detection
            with open(csv_path, 'rb') as f:
                raw = f.read(1024)
            
            encoding = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
            
            # Robuster CSV-Loading mit mehreren Delimiter-Versuchen
            delimiters_to_try = [';', ',', '\t', '|']
            
            for delimiter in delimiters_to_try:
                try:
                    with open(csv_path, 'r', encoding=encoding, errors='ignore') as csvfile:
                        reader = csv.DictReader(csvfile, delimiter=delimiter)
                        
                        # Test: Ersten Datensatz lesen
                        first_row = next(reader, None)
                        if first_row and len(first_row) > 10:  # Mind. 10 Spalten erwarten
                            # Reset und alle Daten laden
                            csvfile.seek(0)
                            reader = csv.DictReader(csvfile, delimiter=delimiter)
                            
                            for row in reader:
                                # Whitespace entfernen (wie im Original)
                                cleaned_row = {key.strip(): value.strip() for key, value in row.items()}
                                csv_data.append(cleaned_row)
                            
                            self.logger.info(f"✅ CSV erfolgreich mit Delimiter '{delimiter}' geladen")
                            break
                            
                except Exception:
                    continue  # Nächsten Delimiter versuchen
            
            if not csv_data:
                self.logger.error("❌ CSV konnte mit keinem Delimiter geladen werden")
            
            return csv_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der CSV: {e}")
            return []
    
    def _test_csv_matching(self, csv_data: list, lieferscheinnummer: str) -> list:
        """Testet das CSV-Matching wie im WareneingangProcessor."""
        self.logger.info(f"🎯 SCHRITT 3: CSV-Matching für '{lieferscheinnummer}'")
        self.logger.info("-" * 40)
        
        matches = []
        
        for i, row in enumerate(csv_data):
            csv_lieferscheinnr = row.get('LIEFERSCHEINNR', '').strip()
            
            # Exaktes Matching (wie im Original)
            if csv_lieferscheinnr == lieferscheinnummer:
                matches.append(row)
                artikel = row.get('ARTIKEL', 'N/A')
                self.logger.info(f"✅ Match {len(matches)}: '{artikel}'")
        
        if matches:
            self.logger.info(f"🎉 {len(matches)} Treffer gefunden!")
        else:
            self.logger.error(f"❌ Keine Treffer für '{lieferscheinnummer}'")
            
            # Debug: Ähnliche suchen
            self.logger.info("🔍 Suche nach ähnlichen Lieferscheinnummern...")
            similar_found = 0
            for row in csv_data[:100]:  # Nur erste 100 prüfen
                csv_nr = row.get('LIEFERSCHEINNR', '').strip()
                if csv_nr and (
                    lieferscheinnummer in csv_nr or 
                    csv_nr in lieferscheinnummer or
                    abs(len(csv_nr) - len(lieferscheinnummer)) <= 2
                ):
                    self.logger.info(f"💡 Ähnlich: '{csv_nr}'")
                    similar_found += 1
                    if similar_found >= 5:
                        break
            
            if similar_found == 0:
                self.logger.info("💡 Keine ähnlichen Nummern gefunden")
        
        self.logger.info("-" * 40)
        return matches
    
    def _simulate_db_import(self, lieferscheinnummer: str, matches: list):
        """Simuliert den DB-Import."""
        self.logger.info("💾 SCHRITT 4: Simulierter DB-Import")
        self.logger.info("-" * 40)
        
        if matches:
            self.logger.info(f"📋 Würde Lieferschein erstellen: '{lieferscheinnummer}'")
            self.logger.info(f"📊 Würde {len(matches)} Datensätze importieren:")
            
            for i, match in enumerate(matches[:3], 1):  # Nur erste 3 zeigen
                artikel = match.get('ARTIKEL', 'N/A')
                menge = match.get('MENGE', 'N/A')
                self.logger.info(f"   {i}. {artikel} (Menge: {menge})")
            
            if len(matches) > 3:
                self.logger.info(f"   ... und {len(matches) - 3} weitere")
                
        else:
            self.logger.info("❌ Kein Import - keine Matches")
        
        self.logger.info("-" * 40)
    
    def _final_summary(self, pdf_path: str, lieferscheinnummer: str, match_count: int):
        """Finale Zusammenfassung."""
        filename = os.path.basename(pdf_path)
        
        self.logger.info("📋 FINALE ZUSAMMENFASSUNG")
        self.logger.info("=" * 50)
        self.logger.info(f"📄 PDF: {filename}")
        self.logger.info(f"📦 Extrahierte Lieferscheinnummer: '{lieferscheinnummer}'")
        self.logger.info(f"🎯 CSV-Treffer: {match_count}")
        
        if match_count > 0:
            self.logger.info("✅ WORKFLOW ERFOLGREICH! 🎉")
            self.logger.info("💡 Das System würde funktionieren")
        else:
            self.logger.info("❌ WORKFLOW FEHLGESCHLAGEN")
            self.logger.info("💡 Problem beim CSV-Matching oder PDF-Extraktion")
        
        self.logger.info("=" * 50)


def main():
    """Hauptfunktion."""
    
    logger.info("🚀 Kombinierter Wareneingang-Test")
    
    # PDF-Pfad
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Standard: Nach PDFs im Input-Verzeichnis suchen
        input_dir = Path("backend/pdfs/input")
        
        if input_dir.exists():
            pdf_files = list(input_dir.glob("*.pdf"))
            
            if pdf_files:
                pdf_path = str(pdf_files[0])
                logger.info(f"🎯 Teste erste PDF: {pdf_path}")
            else:
                logger.error("❌ Keine PDFs im Input-Verzeichnis")
                logger.info("💡 Verwendung: python combined_test.py <pfad_zur_pdf>")
                return
        else:
            logger.error("❌ Input-Verzeichnis nicht gefunden")
            return
    
    # Test durchführen
    tester = WareneingangFullTester()
    success = tester.test_full_workflow(pdf_path)
    
    if success:
        logger.info("🎉 GESAMTERGEBNIS: SUCCESS")
    else:
        logger.info("❌ GESAMTERGEBNIS: FAILED")


if __name__ == "__main__":
    main()