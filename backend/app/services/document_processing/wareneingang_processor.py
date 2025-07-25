"""
Wareneingang Document Processor.
Verarbeitet PDFs mit "Wareneingang" und importiert zugehörige CSV-Daten.
Aktualisiert für PostgreSQL-Repository-Pattern mit DB-basierter Dateiverwaltung.
"""

import csv
import os
import re
import shutil
from pathlib import Path
from typing import List, Optional

from ...config.settings import CSV_LIST_DIR, PDF_PROCESSED_DIR
from ...database.postgres_connection import get_db_session
from ...models.database import Kategorie, Unterkategorie
from ...repositories.dokument_repository import DokumentRepository
from ...repositories.lieferschein_repository import (
    ChargenEinkaufRepository,
    LieferscheinExternRepository,
)
from .base_processor import BaseDocumentProcessor


class WareneingangProcessor(BaseDocumentProcessor):
    """
    Processor für Wareneingang-Dokumente.
    
    Workflow:
    1. Prüft PDF-Text auf "Wareneingang"
    2. Extrahiert Lieferscheinnummer (nächste Zeile)
    3. Kategorisiert als "Lieferschein_extern"
    4. Sucht in CSV-Dateien nach der Lieferscheinnummer
    5. Importiert gefundene Datensätze in die Datenbank
    6. Verschiebt Datei in entsprechendes Verzeichnis
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
        2. Kategorisiert Dokument
        3. Lädt CSV-Dateien
        4. Sucht passende Datensätze
        5. Importiert in Datenbank
        6. Verschiebt Datei in Zielverzeichnis
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
            dokument_dict = self._find_document_by_path(pdf_path)
            if not dokument_dict:
                self._log_processing_error(pdf_path, "Dokument nicht in Datenbank gefunden")
                return False
            
            # 3. Dokument als Lieferschein_extern kategorisieren
            updated_dokument = self._categorize_document(dokument_dict["id"])
            if not updated_dokument:
                self._log_processing_error(pdf_path, "Fehler beim Kategorisieren")
                return False
            
            # 4. Prüfen ob Lieferschein bereits existiert
            existing_lieferschein = LieferscheinExternRepository.get_by_lieferscheinnummer(lieferscheinnummer)
            if existing_lieferschein:
                self.logger.info(f"Lieferschein bereits vorhanden: {lieferscheinnummer}")
                # Trotzdem Datei verschieben falls noch nicht geschehen
                await self._move_document_to_category(updated_dokument, lieferscheinnummer)
                return True
            
            # 5. Neuen externen Lieferschein erstellen
            lieferschein = LieferscheinExternRepository.create(lieferscheinnummer, dokument_dict["id"])
            if not lieferschein:
                self._log_processing_error(pdf_path, "Fehler beim Erstellen des Lieferscheins")
                return False
                
            self.logger.info(f"📋 Externer Lieferschein erstellt: ID {lieferschein.id}")
            
            # 6. CSV-Daten laden und importieren
            csv_import_count = await self._import_csv_data(lieferschein, lieferscheinnummer)
            
            if csv_import_count > 0:
                # Als importiert markieren
                LieferscheinExternRepository.mark_csv_imported(lieferschein.id)
                
            # 7. Dokument ins Lieferschein_extern-Verzeichnis verschieben
            move_success = await self._move_document_to_category(updated_dokument, lieferscheinnummer)
            if move_success:
                self.logger.info(f"📁 Wareneingang erfolgreich als Lieferschein_extern abgelegt")
            else:
                self.logger.warning(f"⚠️  Wareneingang konnte nicht verschoben werden, bleibt im Input-Verzeichnis")
            
            # 8. Erfolgsmeldung
            if csv_import_count > 0:
                self._log_processing_success(
                    pdf_path, 
                    f"Lieferschein {lieferscheinnummer}, {csv_import_count} CSV-Datensätze importiert"
                )
            else:
                self._log_processing_success(
                    pdf_path,
                    f"Lieferschein {lieferscheinnummer} verarbeitet (keine CSV-Daten gefunden)"
                )
                
            return True
            
        except Exception as e:
            self._log_processing_error(pdf_path, str(e))
            return False
    
    def _extract_lieferscheinnummer(self, pdf_path: str) -> Optional[str]:
        """
        Extrahiert die Lieferscheinnummer aus dem PDF.
        
        Sucht nach "Wareneingang" und nimmt die nächste Zeile als Lieferscheinnummer.
        BEHÄLT ALLE Zeichen bei (auch Sonderzeichen wie /, -, etc.)
        """
        try:
            lines = self._extract_text_from_pdf(pdf_path, max_lines=30)
            
            for i, line in enumerate(lines):
                if "wareneingang" in line.lower():
                    # Nächste Zeile als Lieferscheinnummer
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        
                        # MINIMAL bereinigen - nur Whitespace und Steuerzeichen entfernen
                        # Alle anderen Zeichen (/, -, etc.) BEIBEHALTEN
                        lieferscheinnummer = ''.join(char for char in next_line 
                                                   if char.isprintable() and not char.isspace())
                        
                        # Validierung: Mindestlänge und nicht nur Sonderzeichen
                        if lieferscheinnummer and len(lieferscheinnummer) >= 3:
                            # Prüfen ob mindestens ein alphanumerisches Zeichen vorhanden
                            if any(char.isalnum() for char in lieferscheinnummer):
                                self.logger.debug(f"Extrahierte Lieferscheinnummer: '{lieferscheinnummer}'")
                                return lieferscheinnummer
                            else:
                                self.logger.warning(f"Lieferscheinnummer enthält nur Sonderzeichen: '{lieferscheinnummer}'")
                        else:
                            self.logger.warning(f"Lieferscheinnummer zu kurz oder leer: '{lieferscheinnummer}'")
            
            self.logger.warning("Keine gültige Lieferscheinnummer gefunden")
            return None
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren der Lieferscheinnummer: {e}")
            return None
    
    def _find_document_by_path(self, pdf_path: str) -> Optional[dict]:
        """Findet das Dokument in der Datenbank anhand des Pfads."""
        try:
            # Dateiname aus Pfad extrahieren
            filename = os.path.basename(pdf_path)
            
            # Alle Dokumente durchsuchen (gibt bereits Dictionaries zurück)
            all_dokumente = DokumentRepository.get_all()
            for dok_dict in all_dokumente:
                if dok_dict["dateiname"] == filename or dok_dict["pfad"] == pdf_path:
                    return dok_dict
            
            self.logger.warning(f"Dokument nicht gefunden: {filename}")
            return None
            
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen des Dokuments: {e}")
            return None
    
    def _categorize_document(self, dokument_id: int) -> Optional[dict]:
        """Kategorisiert Dokument als Lieferscheine/Lieferschein_extern (= Wareneingang)."""
        try:
            # Dokument als "Lieferscheine/Lieferschein_extern" kategorisieren
            updated_dokument = DokumentRepository.update_kategorie(
                dokument_id, 
                "Lieferscheine", 
                "Lieferschein_extern"
            )
            
            if updated_dokument:
                self.logger.info(f"📂 Dokument {dokument_id} als Lieferschein_extern (Wareneingang) kategorisiert")
                return updated_dokument
            else:
                self.logger.error(f"Fehler beim Kategorisieren von Dokument {dokument_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Fehler beim Kategorisieren: {e}")
            return None
    
    async def _move_document_to_category(self, dokument_dict: dict, lieferscheinnummer: str = None) -> bool:
        """
        Verschiebt das Dokument ins Lieferschein_extern-Verzeichnis mit eindeutiger Benennung.
        Format: lief_ext_[Lieferscheinnummer]_[DDMMYY_hhmmss]_[DB_ID].pdf
        """
        try:
            # Zielverzeichnis aus DB ermitteln
            target_dir = self._get_category_path("Lieferscheine", "Lieferschein_extern")
            if not target_dir:
                self.logger.error("Zielverzeichnis konnte nicht ermittelt werden")
                return False
            
            # Verzeichnis erstellen falls nicht vorhanden
            os.makedirs(target_dir, exist_ok=True)
            
            # Aktueller Pfad prüfen
            alter_pfad = dokument_dict["pfad"]
            
            # Prüfen ob Datei existiert
            if not os.path.exists(alter_pfad):
                self.logger.warning(f"Quelldatei nicht gefunden, möglicherweise bereits verschoben: {alter_pfad}")
                return True  # Als erfolgreich betrachten
            
            # Prüfen ob bereits im Zielverzeichnis
            if str(target_dir) in alter_pfad:
                self.logger.debug(f"Datei bereits im Zielverzeichnis: {os.path.basename(alter_pfad)}")
                return True
            
            # Eindeutigen Dateinamen generieren
            from datetime import datetime
            
            db_id = dokument_dict["id"]
            
            # Zeitstempel generieren
            timestamp = datetime.now().strftime("%d%m%y_%H%M%S")
            
            # Lieferscheinnummer für Dateinamen bereinigen (nur alphanumerisch + - und _)
            safe_lieferscheinnummer = "unbekannt"
            if lieferscheinnummer:
                safe_lieferscheinnummer = ''.join(c for c in lieferscheinnummer if c.isalnum() or c in '-_')
                if not safe_lieferscheinnummer:  # Falls nach Bereinigung leer
                    safe_lieferscheinnummer = "unbekannt"
            
            # Neuen Dateinamen erstellen
            neuer_dateiname = f"lief_ext_{safe_lieferscheinnummer}_{timestamp}_{db_id}.pdf"
            neuer_pfad = target_dir / neuer_dateiname
            
            # Datei verschieben und umbenennen
            shutil.move(alter_pfad, str(neuer_pfad))
            
            # Marker-Dateien auch aufräumen
            self._cleanup_marker_files(alter_pfad)
            
            # Pfad UND Dateiname in DB aktualisieren
            DokumentRepository.update_pfad_und_dateiname(
                dokument_dict["id"], 
                str(neuer_pfad),
                neuer_dateiname
            )
            
            self.logger.info(f"📂 Wareneingang verschoben und umbenannt: {os.path.basename(alter_pfad)} → {neuer_dateiname}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verschieben des Wareneingangs: {e}")
            return False
    
    def _get_category_path(self, kategorie_name: str, unterkategorie_name: str) -> Optional[Path]:
        """
        Ermittelt den Dateipfad für eine Kategorie/Unterkategorie aus der DB.
        """
        try:
            with get_db_session() as session:
                unterkategorie = session.query(Unterkategorie)\
                    .join(Kategorie)\
                    .filter(Kategorie.name == kategorie_name)\
                    .filter(Unterkategorie.name == unterkategorie_name)\
                    .first()
                
                if unterkategorie:
                    # Verzeichnisstruktur: processed/kategorie/unterkategorie
                    # z.B.: processed/lieferscheine/lieferschein_extern
                    category_path = PDF_PROCESSED_DIR / kategorie_name.lower() / unterkategorie_name.lower()
                    return category_path
                else:
                    self.logger.error(f"Kategorie/Unterkategorie nicht gefunden: {kategorie_name}/{unterkategorie_name}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Fehler beim Ermitteln des Kategoriepfads: {e}")
            return None
    
    def _cleanup_marker_files(self, original_path: str):
        """Räumt Marker-Dateien auf."""
        try:
            # OCR-Marker entfernen
            ocr_marker = original_path + '.ocr_processed'
            if os.path.exists(ocr_marker):
                os.remove(ocr_marker)
            
            # Document Processing Marker entfernen
            doc_marker = original_path + '.doc_processed'
            if os.path.exists(doc_marker):
                os.remove(doc_marker)
                
        except Exception as e:
            self.logger.warning(f"Fehler beim Aufräumen der Marker-Dateien: {e}")
    
    async def _import_csv_data(self, lieferschein, lieferscheinnummer: str) -> int:
        """
        Importiert CSV-Daten für die gegebene Lieferscheinnummer.
        """
        try:
            # CSV-Dateien laden (mit Cache)
            csv_data = await self._load_csv_files()
            
            if not csv_data:
                self.logger.warning("Keine CSV-Daten verfügbar")
                return 0
            
            import_count = 0
            found_similar = []  # Für Debugging bei nicht gefundenen Nummern
            
            self.logger.info(f"🔍 Suche nach Lieferscheinnummer: '{lieferscheinnummer}' in {len(csv_data)} CSV-Datensätzen")
            
            # In allen CSV-Datensätzen nach der Lieferscheinnummer suchen
            for csv_row in csv_data:
                csv_lieferscheinnr = str(csv_row.get('LIEFERSCHEINNR', '')).strip()
                
                # Exakter Match
                if csv_lieferscheinnr == lieferscheinnummer:
                    # Datensatz importieren
                    charge = ChargenEinkaufRepository.create_from_csv_row(lieferschein.id, csv_row)
                    if charge:
                        import_count += 1
                        artikel = csv_row.get('ARTIKEL', 'N/A')
                        self.logger.debug(f"✅ CSV-Datensatz importiert: {artikel}")
                
                # Für Debugging: ähnliche Nummern sammeln
                elif (csv_lieferscheinnr and 
                      len(csv_lieferscheinnr) >= 3 and
                      (lieferscheinnummer in csv_lieferscheinnr or csv_lieferscheinnr in lieferscheinnummer)):
                    found_similar.append(csv_lieferscheinnr)
            
            if import_count > 0:
                self.logger.info(f"📊 {import_count} CSV-Datensätze für Lieferschein '{lieferscheinnummer}' importiert")
            else:
                self.logger.warning(f"❌ Keine CSV-Datensätze für '{lieferscheinnummer}' gefunden")
                
                # Debug: ähnliche Nummern anzeigen
                if found_similar:
                    similar_unique = list(set(found_similar[:5]))  # Erste 5 unique
                    self.logger.info(f"🔍 Ähnliche Lieferscheinnummern gefunden: {similar_unique}")
            
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
        Lädt eine einzelne CSV-Datei mit robustem Delimiter-Detection.
        """
        try:
            csv_data = []
            
            # Encoding detection
            with open(csv_path, 'rb') as f:
                raw_data = f.read(1024)
            
            # UTF-8 BOM prüfen
            if raw_data.startswith(b'\xef\xbb\xbf'):
                encoding = 'utf-8-sig'
            else:
                encoding = 'utf-8'
            
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
                                # Whitespace entfernen
                                cleaned_row = {key.strip(): value.strip() for key, value in row.items()}
                                csv_data.append(cleaned_row)
                            
                            self.logger.info(f"✅ CSV erfolgreich mit Delimiter '{delimiter}' geladen: {csv_path}")
                            break
                            
                except Exception:
                    continue  # Nächsten Delimiter versuchen
            
            if not csv_data:
                self.logger.error(f"❌ CSV konnte mit keinem Delimiter geladen werden: {csv_path}")
            
            return csv_data
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der CSV-Datei {csv_path}: {e}")
            return []
    
    def clear_cache(self):
        """Leert den CSV-Cache (für Tests oder manuelle Aktualisierung)."""
        self._csv_cache = {}
        self.logger.info("CSV-Cache geleert")