"""
Background-Service für periodische OCR-Verarbeitung neuer PDF-Dateien.
Aktualisiert für PostgreSQL-Repository-Pattern.
"""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Set

from ..config.settings import PDF_INPUT_DIR

# GEÄNDERT: Verwende Repository statt alte Models
from ..repositories.dokument_repository import DokumentRepository
from ..services.ocr_service import OCRService

logger = logging.getLogger(__name__)

class OCRScheduler:
    """Background-Service für periodische OCR-Verarbeitung mit Document Processing."""
    
    def __init__(self, check_interval: int = 30):
        """
        Args:
            check_interval: Prüfintervall in Sekunden (Standard: 30s)
        """
        self.check_interval = check_interval
        self.running = False
        self.processed_files: Set[str] = set()
        self._task = None
        self._document_processor_manager = None
    
    async def start(self):
        """Startet den Background-Scheduler."""
        if self.running:
            logger.warning("OCR-Scheduler läuft bereits")
            return
        
        self.running = True
        logger.info(f"OCR-Scheduler gestartet - Prüfintervall: {self.check_interval}s")
        
        # Document Processing System initialisieren
        await self._init_document_processing()
        
        # Initial bereits verarbeitete Dateien laden
        self._load_processed_files()
        
        # Background-Task starten
        self._task = asyncio.create_task(self._background_loop())
    
    async def stop(self):
        """Stoppt den Background-Scheduler."""
        if not self.running:
            return
        
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("OCR-Scheduler gestoppt")
    
    async def _init_document_processing(self):
        """Initialisiert das Document Processing System."""
        try:
            # Lazy Import um Circular Imports zu vermeiden
            from ..services.document_processing import document_processor_manager
            
            self._document_processor_manager = document_processor_manager
            
            processors = self._document_processor_manager.get_registered_processors()
            logger.info(f"📋 Document Processors geladen: {', '.join(processors)}")
            
        except ImportError as e:
            logger.warning(f"Document Processing System nicht verfügbar: {e}")
            self._document_processor_manager = None
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren des Document Processing: {e}")
            self._document_processor_manager = None
    
    def _load_processed_files(self):
        """Lädt bereits verarbeitete Dateien beim Start."""
        try:
            for filename in os.listdir(PDF_INPUT_DIR):
                if filename.lower().endswith('.pdf'):
                    file_path = os.path.join(PDF_INPUT_DIR, filename)
                    ocr_marker = file_path + '.ocr_processed'
                    doc_marker = file_path + '.doc_processed'
                    
                    # Als verarbeitet markieren wenn beide Marker vorhanden sind
                    if os.path.exists(ocr_marker) and os.path.exists(doc_marker):
                        self.processed_files.add(filename)
            
            logger.info(f"Bereits vollständig verarbeitete Dateien geladen: {len(self.processed_files)}")
            
        except Exception as e:
            logger.error(f"Fehler beim Laden verarbeiteter Dateien: {e}")
    
    async def _background_loop(self):
        """Haupt-Background-Loop für periodische Prüfung."""
        while self.running:
            try:
                await self._check_and_process_files()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("OCR-Scheduler wurde abgebrochen")
                break
            except Exception as e:
                logger.error(f"Fehler im OCR-Scheduler: {e}")
                # Bei Fehlern kurz warten und weitermachen
                await asyncio.sleep(5)
    
    async def _check_and_process_files(self):
        """Prüft auf neue Dateien und verarbeitet sie."""
        try:
            if not os.path.exists(PDF_INPUT_DIR):
                return
            
            files_to_process = []
            
            # ALLE PDF-Dateien prüfen (nicht nur unverarbeitete)
            for filename in os.listdir(PDF_INPUT_DIR):
                if filename.lower().endswith('.pdf'):
                    file_path = os.path.join(PDF_INPUT_DIR, filename)
                    
                    # Prüfen ob in DB vorhanden (mit neuem Repository)
                    in_database = self._is_file_in_database(filename)
                    
                    # OCR-Status prüfen
                    ocr_marker = file_path + '.ocr_processed'
                    ocr_done = os.path.exists(ocr_marker)
                    
                    # Document Processing Status prüfen
                    doc_processing_marker = file_path + '.doc_processed'
                    doc_processing_done = os.path.exists(doc_processing_marker)
                    
                    # Verarbeitung nötig wenn:
                    # - Noch nicht in processed_files UND
                    # - (OCR fehlt ODER nicht in DB ODER Document Processing fehlt)
                    if (filename not in self.processed_files and 
                        (not ocr_done or not in_database or not doc_processing_done)):
                        files_to_process.append(filename)
            
            if not files_to_process:
                return  # Nichts zu tun
            
            logger.info(f"Dateien für Verarbeitung: {files_to_process}")
            
            # Dateien verarbeiten
            for filename in files_to_process:
                await self._process_single_file_complete(filename)
        
        except Exception as e:
            logger.error(f"Fehler beim Prüfen der Dateien: {e}")
    
    def _is_file_in_database(self, filename: str) -> bool:
        """Prüft ob Datei bereits in Datenbank ist (mit neuem Repository)."""
        try:
            dokument = DokumentRepository.get_by_filename(filename)
            return dokument is not None
        except Exception as e:
            logger.error(f"Fehler beim DB-Check: {e}")
            return False
    
    async def _process_single_file_complete(self, filename: str):
        """
        Vollständige Verarbeitung - kann mehrfach aufgerufen werden.
        Überspringt bereits erledigte Schritte.
        ROBUSTER: Prüft aktuellen Dateipfad dynamisch.
        """
        try:
            # DYNAMISCHE Pfad-Ermittlung statt statischer Pfad
            current_file_path = self._find_current_file_path(filename)
            if not current_file_path:
                logger.warning(f"Datei nicht gefunden: {filename}")
                return
            
            logger.info(f"🔄 Verarbeite: {filename} (Pfad: {current_file_path})")
            
            # Marker-Pfade basierend auf ORIGINAL Input-Pfad (bleiben konstant)
            original_input_path = os.path.join(PDF_INPUT_DIR, filename)
            ocr_marker = original_input_path + '.ocr_processed'
            doc_processing_marker = original_input_path + '.doc_processed'
            
            # 1. OCR falls nötig
            if not os.path.exists(ocr_marker):
                logger.info(f"📝 Starte OCR: {filename}")
                success = await asyncio.to_thread(self._run_ocr_sync, current_file_path)
                
                if success:
                    # OCR-Marker erstellen
                    with open(ocr_marker, 'w') as marker:
                        marker.write(f"OCR: {os.path.getmtime(current_file_path)}")
                    logger.info(f"✅ OCR abgeschlossen: {filename}")
                else:
                    logger.warning(f"❌ OCR fehlgeschlagen: {filename}")
                    return
            else:
                logger.debug(f"⏭️  OCR bereits vorhanden: {filename}")
            
            # 2. Leerseiten-Entfernung (optional) - nur wenn Datei noch existiert
            current_file_path = self._find_current_file_path(filename)
            if current_file_path:
                try:
                    await asyncio.to_thread(self._remove_blank_pages_pillow, current_file_path)
                except Exception as e:
                    logger.warning(f"⚠️  Leerseiten-Entfernung fehlgeschlagen: {e}")
            
            # 3. DB-Eintrag falls nötig
            if not self._is_file_in_database(filename):
                current_file_path = self._find_current_file_path(filename)
                if current_file_path:
                    logger.info(f"📋 Füge zur DB hinzu: {filename}")
                    await self._add_to_database(filename, current_file_path)
            else:
                logger.debug(f"⏭️  Bereits in DB: {filename}")
            
            # 4. Document Processing falls nötig
            if not os.path.exists(doc_processing_marker):
                # WICHTIG: Aktuellen Pfad vor Document Processing ermitteln
                current_file_path = self._find_current_file_path(filename)
                if not current_file_path:
                    logger.warning(f"Datei für Document Processing nicht gefunden: {filename}")
                    # Trotzdem Marker erstellen um endlose Wiederholung zu vermeiden
                    with open(doc_processing_marker, 'w') as marker:
                        marker.write(f"Doc Processing failed - file not found: {filename}")
                    self.processed_files.add(filename)
                    return
                
                logger.info(f"📄 Starte Document Processing: {filename}")
                
                try:
                    if self._document_processor_manager:
                        doc_processed = await self._document_processor_manager.process_document(
                            current_file_path, filename
                        )
                        
                        # Document Processing Marker erstellen (egal ob erfolgreich oder nicht)
                        with open(doc_processing_marker, 'w') as marker:
                            marker.write(f"Doc Processing: {os.path.getmtime(current_file_path) if os.path.exists(current_file_path) else 'completed'}")
                        
                        if doc_processed:
                            logger.info(f"✅ Document Processing erfolgreich: {filename}")
                        else:
                            logger.debug(f"ℹ️  Kein Processor gefunden: {filename}")
                    else:
                        logger.debug("Document Processing System nicht verfügbar")
                        # Trotzdem Marker erstellen
                        with open(doc_processing_marker, 'w') as marker:
                            marker.write(f"Doc Processing unavailable: {filename}")
                            
                except Exception as e:
                    logger.error(f"Document Processing Fehler für {filename}: {e}")
                    # Marker trotzdem erstellen um endlose Wiederholung zu vermeiden
                    with open(doc_processing_marker, 'w') as marker:
                        marker.write(f"Doc Processing failed: {str(e)}")
            else:
                logger.debug(f"⏭️  Document Processing bereits erledigt: {filename}")
            
            # 5. Als vollständig verarbeitet markieren
            self.processed_files.add(filename)
            
            logger.info(f"✨ Vollständig verarbeitet: {filename}")
            
        except Exception as e:
            logger.error(f"Fehler bei Vollverarbeitung von {filename}: {e}")
            # Bei schweren Fehlern trotzdem als verarbeitet markieren
            self.processed_files.add(filename)

    def _find_current_file_path(self, filename: str) -> str:
        """
        Findet den aktuellen Pfad einer Datei (könnte verschoben worden sein).
        
        Returns:
            Aktueller Pfad oder None wenn nicht gefunden
        """
        try:
            # 1. Zuerst im Input-Verzeichnis schauen
            input_path = os.path.join(PDF_INPUT_DIR, filename)
            if os.path.exists(input_path):
                return input_path
            
            # 2. In der Datenbank nach aktuellem Pfad suchen
            try:
                all_dokumente = DokumentRepository.get_all()
                for dok_dict in all_dokumente:
                    if dok_dict["dateiname"] == filename and os.path.exists(dok_dict["pfad"]):
                        return dok_dict["pfad"]
            except Exception as e:
                logger.debug(f"DB-Suche fehlgeschlagen: {e}")
            
            # 3. In processed-Verzeichnissen suchen (als Fallback)
            from ..config.settings import PDF_PROCESSED_DIR
            
            for root, dirs, files in os.walk(PDF_PROCESSED_DIR):
                for file in files:
                    if file == filename or file.startswith(f"lief_ext_") and file.endswith(f"_{filename}"):
                        full_path = os.path.join(root, file)
                        if os.path.exists(full_path):
                            return full_path
            
            logger.debug(f"Datei {filename} nicht gefunden")
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Suchen der Datei {filename}: {e}")
            return None
            
    def _run_ocr_sync(self, file_path: str) -> bool:
        """Synchrone OCR-Ausführung für asyncio.to_thread."""
        try:
            # Temporäre Datei für OCR-Output
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # OCR-Verarbeitung
                success = OCRService.create_searchable_pdf(file_path, temp_path)
                
                if success:
                    # Original durch OCR-Version ersetzen
                    shutil.move(temp_path, file_path)
                    return True
                else:
                    return False
                    
            finally:
                # Temporäre Datei aufräumen
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"Fehler beim synchronen OCR: {e}")
            return False
    

    def _remove_blank_pages_pillow(self, pdf_path: str) -> bool:

        try:
            import io
            import shutil

            import fitz
            from PIL import Image
            
            doc = fitz.open(pdf_path)
            pages_to_remove = []
            original_page_count = len(doc)
            
            logger.info(f"Prüfe {original_page_count} Seiten auf Leerheit: {os.path.basename(pdf_path)}")
            
            doc_closed = False
            
            try:
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # 1. Pixelbasierte Analyse (wie bisher)
                    pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    img_gray = img.convert('L')
                    
                    # Histogramm erstellen
                    histogram = img_gray.histogram()
                    total_pixels = img_gray.size[0] * img_gray.size[1]
                    
                    # VERSCHÄRFTE Einstellungen für weiße Pixel
                    white_pixels = sum(histogram[250:])  # Nur 250-255 statt 240-255
                    white_ratio = white_pixels / total_pixels
                    
                    # VERSCHÄRFTER Schwellenwert für Leerseiten
                    pixel_based_blank = white_ratio > 0.98  
                    
                    # 2. Textbasierte Zusatzprüfung für Grenzfälle
                    text_based_blank = True
                    if pixel_based_blank:
                        # Bei pixelbasierten Grenzfällen auch Text prüfen
                        page_text = page.get_text().strip()
                        
                        # Seite ist NICHT leer wenn:
                        # - Mehr als 10 Zeichen Text
                        # - Enthält alphanumerische Zeichen
                        # - Enthält typische Dokumentwörter
                        meaningful_text = len(page_text) > 10 and any(c.isalnum() for c in page_text)
                        
                        # Spezielle Prüfung für Wareneingänge
                        wareneingang_keywords = ['wareneingang', 'lieferschein', 'bestellung', 'artikel']
                        contains_keywords = any(keyword in page_text.lower() for keyword in wareneingang_keywords)
                        
                        if meaningful_text or contains_keywords:
                            text_based_blank = False
                            logger.debug(f"Seite {page_num + 1} durch Text-Prüfung gerettet: '{page_text[:50]}...'")
                    
                    # Seite ist nur leer wenn BEIDE Kriterien zutreffen
                    is_blank = pixel_based_blank and text_based_blank
                    
                    if is_blank:
                        pages_to_remove.append(page_num)
                        logger.debug(f"Seite {page_num + 1} ist leer (weiß: {white_ratio:.1%})")
                    elif pixel_based_blank:
                        logger.debug(f"Seite {page_num + 1} fast leer, aber Text gefunden (weiß: {white_ratio:.1%})")
                    
                    # Speicher freigeben
                    img.close()
                    img_gray.close()
                
                # Leere Seiten entfernen (von hinten nach vorne)
                removed_count = 0
                for page_num in reversed(pages_to_remove):
                    doc.delete_page(page_num)
                    removed_count += 1
                
                if removed_count > 0:
                    # In temporäre Datei speichern
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_output:
                        temp_output_path = temp_output.name
                    
                    try:
                        doc.save(temp_output_path, deflate=True)
                        doc.close()
                        doc_closed = True
                        
                        # Original durch bereinigte Version ersetzen
                        shutil.move(temp_output_path, pdf_path)
                        
                        logger.info(f"🗑️  Leerseiten entfernt: {removed_count} von {original_page_count} aus {os.path.basename(pdf_path)}")
                        return True
                        
                    except Exception as save_error:
                        logger.error(f"Fehler beim Speichern der bereinigten PDF: {save_error}")
                        if os.path.exists(temp_output_path):
                            os.remove(temp_output_path)
                        return False
                else:
                    logger.info(f"✅ Keine leeren Seiten in {os.path.basename(pdf_path)}")
                    return False
                    
            finally:
                if not doc_closed:
                    try:
                        doc.close()
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"Fehler bei verbesserter Leerseiten-Entfernung: {e}")
            return False


    # ALTERNATIVE: Konfigurierbare Einstellungen in settings.py
    """
    # Zu settings.py hinzufügen:
    BLANK_PAGE_DETECTION = {
        "enabled": True,
        "white_pixel_threshold": 250,  # 250-255 statt 240-255
        "blank_page_threshold": 0.995,  # 99.5% statt 98%
        "min_text_length": 10,  # Mindest-Textlänge für Nicht-Leer-Erkennung
        "preserve_keywords": ["wareneingang", "lieferschein", "bestellung", "artikel"]
    }
    """    
    async def _add_to_database(self, filename: str, file_path: str):
        """Fügt neue Datei zur Datenbank hinzu falls noch nicht vorhanden (mit neuem Repository)."""
        try:
            # Prüfen ob bereits in DB
            existing_dokument = DokumentRepository.get_by_filename(filename)
            
            if not existing_dokument:
                # Vorschau-Text extrahieren
                preview_text = await asyncio.to_thread(
                    OCRService.extract_preview_text, file_path, 300
                )
                
                # In DB speichern (mit neuem Repository)
                DokumentRepository.create(
                    dateiname=filename,
                    pfad=file_path,
                    inhalt_vorschau=preview_text
                )
                
                logger.info(f"📋 Datei zur Datenbank hinzugefügt: {filename}")
        
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen zur DB: {e}")
    
    def force_check(self):
        """Löst eine sofortige Prüfung aus (für manuellen Trigger)."""
        if self.running:
            # Erstelle Task für sofortige Prüfung
            asyncio.create_task(self._check_and_process_files())
            logger.info("Manuelle OCR-Prüfung mit Document Processing ausgelöst")


# Globale Scheduler-Instanz
ocr_scheduler = OCRScheduler(check_interval=30)  # Alle 30 Sekunden prüfen