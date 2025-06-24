#!/usr/bin/env python3
"""
CSV Debug Script für Wareneingang-System.
Analysiert CSV-Dateien und testet das Matching ausführlich.
"""

import csv
import logging
import os
import sys
from pathlib import Path

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("csv_debug.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class CSVDebugger:
    """Debug-Klasse für CSV-Analyse und Matching-Tests."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.csv_list_dir = Path("backend/pdfs/csv_lists")
    
    def debug_csv_system(self, test_lieferscheinnummer: str = None):
        """
        Vollständige CSV-System-Analyse.
        
        Args:
            test_lieferscheinnummer: Lieferscheinnummer zum Testen (optional)
        """
        self.logger.info("🔍 Starte CSV-System-Debug")
        self.logger.info("=" * 80)
        
        # 1. CSV-Verzeichnis prüfen
        if not self._check_csv_directory():
            return
        
        # 2. CSV-Dateien auflisten
        csv_files = self._list_csv_files()
        if not csv_files:
            return
        
        # 3. Jede CSV-Datei analysieren
        all_csv_data = []
        for csv_file in csv_files:
            csv_data = self._analyze_csv_file(csv_file)
            if csv_data:
                all_csv_data.extend(csv_data)
        
        # 4. Lieferscheinnummern-Übersicht
        self._analyze_lieferscheinnummern(all_csv_data)
        
        # 5. Test-Matching (falls Lieferscheinnummer gegeben)
        if test_lieferscheinnummer:
            self._test_matching(all_csv_data, test_lieferscheinnummer)
        
        self.logger.info("✅ CSV-Debug abgeschlossen")
        self.logger.info("=" * 80)
    
    def _check_csv_directory(self) -> bool:
        """Prüft ob das CSV-Verzeichnis existiert."""
        self.logger.info(f"📂 Prüfe CSV-Verzeichnis: {self.csv_list_dir}")
        
        if not self.csv_list_dir.exists():
            self.logger.error(f"❌ CSV-Verzeichnis nicht gefunden: {self.csv_list_dir}")
            self.logger.info("💡 Erstelle das Verzeichnis und lege CSV-Dateien hinein:")
            self.logger.info(f"   mkdir -p {self.csv_list_dir}")
            return False
        
        self.logger.info(f"✅ CSV-Verzeichnis gefunden: {self.csv_list_dir}")
        return True
    
    def _list_csv_files(self) -> list:
        """Listet alle CSV-Dateien im Verzeichnis auf."""
        self.logger.info("📄 Suche nach CSV-Dateien...")
        
        csv_files = []
        for file_path in self.csv_list_dir.iterdir():
            if file_path.suffix.lower() == '.csv':
                csv_files.append(file_path)
                self.logger.info(f"   ✅ Gefunden: {file_path.name} ({file_path.stat().st_size} Bytes)")
        
        if not csv_files:
            self.logger.error("❌ Keine CSV-Dateien gefunden!")
            self.logger.info("💡 Lege CSV-Dateien in das Verzeichnis:")
            self.logger.info(f"   {self.csv_list_dir}/gelieferte_chargen_einkauf.csv")
            return []
        
        self.logger.info(f"📊 {len(csv_files)} CSV-Datei(en) gefunden")
        self.logger.info("-" * 60)
        return csv_files
    
    def _analyze_csv_file(self, csv_path: Path) -> list:
        """Analysiert eine einzelne CSV-Datei ausführlich."""
        self.logger.info(f"🔍 Analysiere CSV: {csv_path.name}")
        
        try:
            # 1. Datei-Encoding testen
            encoding = self._detect_encoding(csv_path)
            self.logger.info(f"   📝 Encoding: {encoding}")
            
            # 2. Delimiter erkennen
            delimiter = self._detect_delimiter(csv_path, encoding)
            self.logger.info(f"   🔗 Delimiter: '{delimiter}'")
            
            # 3. CSV laden
            csv_data = self._load_csv_with_details(csv_path, encoding, delimiter)
            
            if csv_data:
                self.logger.info(f"   ✅ {len(csv_data)} Datensätze geladen")
            else:
                self.logger.error(f"   ❌ Keine Daten geladen")
            
            self.logger.info("-" * 40)
            return csv_data
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Analysieren von {csv_path.name}: {e}")
            return []
    
    def _detect_encoding(self, csv_path: Path) -> str:
        """Erkennt das Encoding der CSV-Datei."""
        try:
            # Erste Bytes lesen um Encoding zu erraten
            with open(csv_path, 'rb') as f:
                raw_data = f.read(1024)
            
            # UTF-8 BOM prüfen
            if raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            
            # UTF-8 versuchen
            try:
                raw_data.decode('utf-8')
                return 'utf-8'
            except:
                pass
            
            # Fallback auf Windows-Encoding
            return 'cp1252'
            
        except:
            return 'utf-8'
    
    def _detect_delimiter(self, csv_path: Path, encoding: str) -> str:
        """Erkennt den CSV-Delimiter."""
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                sample = f.read(1024)
            
            # CSV-Sniffer verwenden
            dialect = csv.Sniffer().sniff(sample, delimiters=';,\t|')
            return dialect.delimiter
            
        except:
            # Fallback: Semikolon (deutsche Konvention)
            return ';'
    
    def _load_csv_with_details(self, csv_path: Path, encoding: str, delimiter: str) -> list:
        """Lädt CSV mit detailliertem Logging."""
        try:
            csv_data = []
            
            with open(csv_path, 'r', encoding=encoding) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                # Header anzeigen
                if reader.fieldnames:
                    self.logger.info(f"   📋 Spalten ({len(reader.fieldnames)}):")
                    for i, field in enumerate(reader.fieldnames, 1):
                        self.logger.info(f"      {i:2d}. '{field.strip()}'")
                    
                    # LIEFERSCHEINNR prüfen
                    lieferschein_columns = [f for f in reader.fieldnames if 'LIEFERSCHEIN' in f.upper()]
                    if lieferschein_columns:
                        self.logger.info(f"   ✅ Lieferschein-Spalte gefunden: {lieferschein_columns}")
                    else:
                        self.logger.warning("   ⚠️  Keine 'LIEFERSCHEINNR'-Spalte gefunden!")
                        self.logger.info("   💡 Verfügbare Spalten durchsuchen...")
                
                # Daten laden
                row_count = 0
                for row in reader:
                    # Whitespace von allen Werten entfernen
                    cleaned_row = {key.strip(): value.strip() for key, value in row.items()}
                    csv_data.append(cleaned_row)
                    row_count += 1
                    
                    # Erste 3 Zeilen als Beispiel anzeigen
                    if row_count <= 3:
                        lieferschein_wert = cleaned_row.get('LIEFERSCHEINNR', 'N/A')
                        self.logger.info(f"   📦 Zeile {row_count} - LIEFERSCHEINNR: '{lieferschein_wert}'")
            
            return csv_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der CSV: {e}")
            return []
    
    def _analyze_lieferscheinnummern(self, all_csv_data: list):
        """Analysiert alle Lieferscheinnummern in den CSV-Daten."""
        self.logger.info("📦 LIEFERSCHEINNUMMER-ANALYSE:")
        
        if not all_csv_data:
            self.logger.error("❌ Keine CSV-Daten zum Analysieren")
            return
        
        # Alle Lieferscheinnummern sammeln
        lieferscheinnummern = []
        for row in all_csv_data:
            lieferschein_nr = row.get('LIEFERSCHEINNR', '').strip()
            if lieferschein_nr:
                lieferscheinnummern.append(lieferschein_nr)
        
        if not lieferscheinnummern:
            self.logger.error("❌ Keine Lieferscheinnummern in den CSV-Daten gefunden!")
            self.logger.info("💡 Prüfe:")
            self.logger.info("   - Ist die Spalte 'LIEFERSCHEINNR' vorhanden?")
            self.logger.info("   - Haben die Zeilen Werte in dieser Spalte?")
            return
        
        # Statistiken
        unique_nummern = list(set(lieferscheinnummern))
        self.logger.info(f"   📊 Gesamt: {len(lieferscheinnummern)} Einträge")
        self.logger.info(f"   🎯 Eindeutig: {len(unique_nummern)} verschiedene Lieferscheinnummern")
        
        # Erste 10 Lieferscheinnummern anzeigen
        self.logger.info("   📋 Beispiel-Lieferscheinnummern:")
        for i, nummer in enumerate(unique_nummern[:10], 1):
            count = lieferscheinnummern.count(nummer)
            self.logger.info(f"      {i:2d}. '{nummer}' ({count}x)")
        
        if len(unique_nummern) > 10:
            self.logger.info(f"      ... und {len(unique_nummern) - 10} weitere")
        
        self.logger.info("-" * 60)
    
    def _test_matching(self, all_csv_data: list, test_lieferscheinnummer: str):
        """Testet das Matching für eine spezifische Lieferscheinnummer."""
        self.logger.info(f"🎯 MATCHING-TEST für Lieferscheinnummer: '{test_lieferscheinnummer}'")
        
        matches = []
        for i, row in enumerate(all_csv_data):
            csv_lieferscheinnr = row.get('LIEFERSCHEINNR', '').strip()
            
            # Exaktes Matching
            if csv_lieferscheinnr == test_lieferscheinnummer:
                matches.append((i, row))
                artikel = row.get('ARTIKEL', 'N/A')
                self.logger.info(f"   ✅ Match {len(matches)}: Zeile {i+1} - Artikel: '{artikel}'")
        
        if matches:
            self.logger.info(f"   🎉 {len(matches)} Treffer gefunden!")
        else:
            self.logger.warning(f"   ❌ Keine Treffer für '{test_lieferscheinnummer}' gefunden")
            
            # Ähnliche Lieferscheinnummern suchen
            self.logger.info("   🔍 Suche nach ähnlichen Nummern...")
            similar = []
            for row in all_csv_data[:20]:  # Nur erste 20 prüfen
                csv_nr = row.get('LIEFERSCHEINNR', '').strip()
                if csv_nr and test_lieferscheinnummer.lower() in csv_nr.lower():
                    similar.append(csv_nr)
            
            if similar:
                self.logger.info("   💡 Ähnliche gefunden:")
                for sim in similar[:5]:
                    self.logger.info(f"      - '{sim}'")
            else:
                self.logger.info("   💡 Keine ähnlichen Nummern gefunden")
        
        self.logger.info("-" * 60)


def main():
    """Hauptfunktion des CSV-Debug-Scripts."""
    
    logger.info("🚀 CSV-Debug gestartet")
    logger.info("=" * 80)
    
    # Test-Lieferscheinnummer aus Command-Line oder Interactive
    test_lieferscheinnummer = None
    
    if len(sys.argv) > 1:
        test_lieferscheinnummer = sys.argv[1]
        logger.info(f"🎯 Test-Lieferscheinnummer aus Argument: '{test_lieferscheinnummer}'")
    else:
        logger.info("💡 Verwendung: python csv_debug.py <test_lieferscheinnummer>")
        logger.info("   Oder ohne Argument für allgemeine CSV-Analyse")
    
    # Debug durchführen
    debugger = CSVDebugger()
    debugger.debug_csv_system(test_lieferscheinnummer)
    
    logger.info(f"📝 Detaillierte Logs gespeichert in: csv_debug.log")


if __name__ == "__main__":
    main()