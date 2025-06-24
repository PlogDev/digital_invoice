"""
Wareneingang Document Processor.
Verarbeitet PDFs mit "Wareneingang" und importiert zugehörige CSV-Daten.
"""

import csv
import os
import re
from pathlib import Path
from typing import List, Optional

from ...config.settings import CSV_LIST_DIR
from ...models.dokument import Dokument
from ...models.lieferschein import Lieferschein, LieferscheinDatensatz
from .base_processor import BaseDocumentProcessor


class WareneingangProcessor(BaseDocumentProcessor):
    """
    Processor für Wareneingang-Dokumente.
    
    Workflow:
    1. Prüft PDF-Text auf "Wareneingang"
    2. Extrahiert Lieferscheinnummer (nächste Zeile)
    3. Sucht in CSV-Dateien nach der Lieferscheinnummer
    4. Importiert gefundene Datensätze in die Datenbank
    """
    
    def __init__(self):
        super().__init__("Wareneingang")
        self._csv_cache = {}  # Cache für CSV-Daten
    
    async def can_handle(self, pdf_path: str) -> bool:
        """
        Prüft, ob das PDF ein Wareneingang-Dokument ist.
        
        Sucht nach dem Wort "Wareneingang" in den ersten Zeilen.
        """
        try:
            lines = self._extract_text_from_pdf(pdf_path, max_lines=20)
            
            # Suche nach "Wareneingang" (case-insensitive)
            for line in lines:
                if "wareneingang" in line.lower():
                    self.logger.debug(f"'Wareneingang' gefunden in: {line}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Fehler beim Prüfen des PDF: {e}")
            return False
    
    async def process(self, pdf_path: str, filename: str) -> bool:
        """
        Verarbeitet ein Wareneingang-PDF.
        
        1. Extrahiert Lieferscheinnummer
        2. Lädt CSV-Dateien
        3. Sucht passende Datensätze
        4. Importiert in Datenbank
        """
        self._log_processing_start(pdf_path)
        
        try:
            # 1. Lieferscheinnummer extrahieren
            lieferscheinnummer = self._extract_lieferscheinnummer(pdf_path)
            if not lieferscheinnummer:
                self._log_processing_error(pdf_path, "Keine Lieferscheinnummer gefunden")
                return False
            
            self.logger.info(f"📦 Lieferscheinnummer extrahiert: {lieferscheinnummer}")
            
            # 2. Zugehöriges Dokument in DB finden
            dokument = self._find_document_by_path(pdf_path)
            if not dokument:
                self._log_processing_error(pdf_path, "Dokument nicht in Datenbank gefunden")
                return False
            
            # 3. Prüfen ob Lieferschein bereits existiert
            existing_lieferschein = Lieferschein.get_by_lieferscheinnummer(lieferscheinnummer)
            if existing_lieferschein:
                self.logger.info(f"Lieferschein bereits vorhanden: {lieferscheinnummer}")
                return True
            
            # 4. Neuen Lieferschein erstellen
            lieferschein = Lieferschein.create(lieferscheinnummer, dokument.id)
            self.logger.info(f"📋 Lieferschein erstellt: ID {lieferschein.id}")
            
            # 5. CSV-Daten laden und importieren
            csv_import_count = await self._import_csv_data(lieferschein, lieferscheinnummer)
            
            if csv_import_count > 0:
                # Als importiert markieren
                lieferschein.csv_importiert = True
                lieferschein.update()
                
                self._log_processing_success(
                    pdf_path, 
                    f"Lieferschein {lieferscheinnummer}, {csv_import_count} CSV-Datensätze importiert"
                )
                return True
            else:
                self.logger.warning(f"Keine CSV-Datensätze für Lieferscheinnummer {lieferscheinnummer} gefunden")
                return True  # Trotzdem erfolgreich, nur keine CSV-Daten
            
        except Exception as e:
            self._log_processing_error(pdf_path, str(e))
            return False
    
    def _extract_lieferscheinnummer(self, pdf_path: str) -> Optional[str]:
        """
        Extrahiert die Lieferscheinnummer aus dem PDF.
        
        Sucht nach "Wareneingang" und nimmt die nächste Zeile als Lieferscheinnummer.
        """
        try:
            lines = self._extract_text_from_pdf(pdf_path, max_lines=30)
            
            for i, line in enumerate(lines):
                if "wareneingang" in line.lower():
                    # Nächste Zeile als Lieferscheinnummer
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        
                        # Bereinige die Lieferscheinnummer (nur Buchstaben, Zahlen, Bindestrich)
                        lieferscheinnummer = re.sub(r'[^A-Za-z0-9\-_]', '', next_line)
                        
                        if lieferscheinnummer and len(lieferscheinnummer) >= 3:
                            return lieferscheinnummer
            
            return None
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren der Lieferscheinnummer: {e}")
            return None
    
    def _find_document_by_path(self, pdf_path: str) -> Optional[Dokument]:
        """Findet das Dokument in der Datenbank anhand des Pfads."""
        try:
            documents = Dokument.get_all()
            for doc in documents:
                if doc.pfad == pdf_path:
                    return doc
            return None
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen des Dokuments: {e}")
            return None
    
    async def _import_csv_data(self, lieferschein: Lieferschein, lieferscheinnummer: str) -> int:
        """
        Importiert CSV-Daten für die gegebene Lieferscheinnummer.
        
        Returns:
            Anzahl der importierten Datensätze
        """
        try:
            # CSV-Dateien laden (mit Cache)
            csv_data = await self._load_csv_files()
            
            import_count = 0
            
            # In allen CSV-Datensätzen nach der Lieferscheinnummer suchen
            for csv_row in csv_data:
                csv_lieferscheinnr = csv_row.get('LIEFERSCHEINNR', '').strip()
                
                if csv_lieferscheinnr == lieferscheinnummer:
                    # Datensatz importieren
                    LieferscheinDatensatz.create_from_csv_row(lieferschein.id, csv_row)
                    import_count += 1
                    
                    self.logger.debug(f"CSV-Datensatz importiert: {csv_row.get('ARTIKEL', 'N/A')}")
            
            self.logger.info(f"📊 {import_count} CSV-Datensätze für Lieferschein {lieferscheinnummer} importiert")
            return import_count
            
        except Exception as e:
            self.logger.error(f"Fehler beim Importieren der CSV-Daten: {e}")
            return 0
    
    async def _load_csv_files(self) -> List[dict]:
        """
        Lädt alle CSV-Dateien aus dem csv_lists Verzeichnis.
        
        Verwendet Caching um bei mehreren Aufrufen performant zu bleiben.
        """
        if self._csv_cache:
            return self._csv_cache.get('data', [])
        
        try:
            if not os.path.exists(CSV_LIST_DIR):
                self.logger.warning(f"CSV-Verzeichnis nicht gefunden: {CSV_LIST_DIR}")
                return []
            
            all_csv_data = []
            csv_files_found = 0
            
            # Alle CSV-Dateien im Verzeichnis durchsuchen
            for filename in os.listdir(CSV_LIST_DIR):
                if filename.lower().endswith('.csv'):
                    csv_path = os.path.join(CSV_LIST_DIR, filename)
                    csv_data = self._load_single_csv(csv_path)
                    
                    if csv_data:
                        all_csv_data.extend(csv_data)
                        csv_files_found += 1
                        self.logger.info(f"📄 CSV geladen: {filename} ({len(csv_data)} Datensätze)")
            
            # Cache aktualisieren
            self._csv_cache = {
                'data': all_csv_data,
                'files_count': csv_files_found
            }
            
            self.logger.info(f"📚 Gesamt: {len(all_csv_data)} Datensätze aus {csv_files_found} CSV-Dateien geladen")
            return all_csv_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der CSV-Dateien: {e}")
            return []
    
    def _load_single_csv(self, csv_path: str) -> List[dict]:
        """
        Lädt eine einzelne CSV-Datei.
        
        Args:
            csv_path: Pfad zur CSV-Datei
            
        Returns:
            Liste der CSV-Datensätze als Dictionaries
        """
        try:
            csv_data = []
            
            # CSV mit Semikolon-Delimiter laden (deutsche CSV-Konvention)
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as csvfile:
                # Delimiter automatisch erkennen
                dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=';,\t')
                csvfile.seek(0)
                
                reader = csv.DictReader(csvfile, delimiter=dialect.delimiter)
                
                for row in reader:
                    # Whitespace von allen Werten entfernen
                    cleaned_row = {key.strip(): value.strip() for key, value in row.items()}
                    csv_data.append(cleaned_row)
            
            return csv_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der CSV-Datei {csv_path}: {e}")
            return []
    
    def clear_cache(self):
        """Leert den CSV-Cache (für Tests oder manuelle Aktualisierung)."""
        self._csv_cache = {}
        self.logger.info("CSV-Cache geleert")