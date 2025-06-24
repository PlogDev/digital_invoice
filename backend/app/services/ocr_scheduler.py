"""
Background-Service für periodische OCR-Verarbeitung neuer PDF-Dateien.
"""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Set

from ..config.settings import PDF_INPUT_DIR
from ..models.dokument import Dokument
from ..services.ocr_service import OCRService

logger = logging.getLogger(__name__)

class OCRScheduler:
    """Background-Service für periodische OCR-Verarbeitung."""
    
    def __init__(self, check_interval: int = 30):
        """
        Args:
            check_interval: Prüfintervall in Sekunden (Standard: 30s)
        """
        self.check_interval = check_interval
        self.running = False
        self.processed_files: Set[str] = set()
        self._task = None
    
    async def start(self):
        """Startet den Background-Scheduler."""
        if self.running:
            logger.warning("OCR-Scheduler läuft bereits")
            return
        
        self.running = True
        logger.info(f"OCR-Scheduler gestartet - Prüfintervall: {self.check_interval}s")
        
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
    
    def _load_processed_files(self):
        """Lädt bereits verarbeitete Dateien beim Start."""
        try:
            for filename in os.listdir(PDF_INPUT_DIR):
                if filename.lower().endswith('.pdf'):
                    file_path = os.path.join(PDF_INPUT_DIR, filename)
                    ocr_marker = file_path + '.ocr_processed'
                    
                    if os.path.exists(ocr_marker):
                        self.processed_files.add(filename)
            
            logger.info(f"Bereits verarbeitete Dateien geladen: {len(self.processed_files)}")
            
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
            
            new_files = []
            
            # Nach neuen PDF-Dateien suchen
            for filename in os.listdir(PDF_INPUT_DIR):
                if (filename.lower().endswith('.pdf') and 
                    filename not in self.processed_files):
                    new_files.append(filename)
            
            if not new_files:
                return  # Keine neuen Dateien
            
            logger.info(f"Neue Dateien gefunden: {new_files}")
            
            # Neue Dateien verarbeiten
            for filename in new_files:
                await self._process_single_file(filename)
        
        except Exception as e:
            logger.error(f"Fehler beim Prüfen der Dateien: {e}")
    
    async def _process_single_file(self, filename: str):
        """Verarbeitet eine einzelne PDF-Datei mit OCR."""
        try:
            file_path = os.path.join(PDF_INPUT_DIR, filename)
            
            logger.info(f"Starte OCR-Verarbeitung: {filename}")
            
            # OCR in separatem Thread ausführen (da CPU-intensiv)
            success = await asyncio.to_thread(
                self._run_ocr_sync, file_path
            )
            
            if success:
                # Leerseiten-Entfernung NACH OCR auf der finalen Datei
                try:
                    await asyncio.to_thread(
                        self._remove_blank_pages_pillow, file_path
                    )
                except Exception as e:
                    logger.warning(f"Leerseiten-Entfernung fehlgeschlagen für {filename}: {e}")
                
                # Marker-Datei erstellen
                ocr_marker = file_path + '.ocr_processed'
                with open(ocr_marker, 'w') as marker:
                    marker.write(f"OCR processed by scheduler: {os.path.getmtime(file_path)}")
                
                # Als verarbeitet markieren
                self.processed_files.add(filename)
                
                # In Datenbank hinzufügen falls noch nicht vorhanden
                await self._add_to_database(filename, file_path)
                
                logger.info(f"OCR erfolgreich abgeschlossen: {filename}")
            else:
                logger.warning(f"OCR fehlgeschlagen: {filename}")
        
        except Exception as e:
            logger.error(f"Fehler bei OCR-Verarbeitung von {filename}: {e}")
    
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
        """
        Entfernt leere Seiten mit Pillow (pixelbasierte Analyse).
        Zuverlässiger als textbasierte Ansätze.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            bool: True wenn Seiten entfernt wurden
        """
        try:
            import io
            import shutil

            import fitz
            from PIL import Image
            
            doc = fitz.open(pdf_path)
            pages_to_remove = []
            original_page_count = len(doc)
            
            logger.info(f"Prüfe {original_page_count} Seiten auf Leerheit: {os.path.basename(pdf_path)}")
            
            doc = fitz.open(pdf_path)
            doc_closed = False
            
            try:
                pages_to_remove = []
                original_page_count = len(doc)
                
                logger.info(f"Prüfe {original_page_count} Seiten auf Leerheit: {os.path.basename(pdf_path)}")
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # Seite als Bild rendern (niedrige Auflösung für Performance)
                    pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))  # 50% Größe
                    img_data = pix.tobytes("png")
                    
                    # Pillow-Image direkt aus Speicher erstellen (Windows-kompatibel)
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Zu Graustufen konvertieren für einfachere Analyse
                    img_gray = img.convert('L')
                    
                    # Histogramm erstellen
                    histogram = img_gray.histogram()
                    
                    # Prüfen ob Seite fast nur weiße Pixel hat
                    total_pixels = img_gray.size[0] * img_gray.size[1]
                    white_pixels = sum(histogram[240:])  # Pixel mit Wert 240-255 (fast weiß)
                    white_ratio = white_pixels / total_pixels
                    
                    # Seite ist leer wenn >98% der Pixel weiß sind
                    is_blank = white_ratio > 0.98
                    
                    if is_blank:
                        pages_to_remove.append(page_num)
                        logger.debug(f"Seite {page_num + 1} ist leer (weiß: {white_ratio:.1%})")
                    else:
                        logger.debug(f"Seite {page_num + 1} hat Inhalt (weiß: {white_ratio:.1%})")
                    
                    # Explizit Speicher freigeben
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
                        
                        logger.info(f"🗑️  Leerseiten entfernt: {removed_count} von {original_page_count} Seiten aus {os.path.basename(pdf_path)}")
                        return True
                        
                    except Exception as save_error:
                        logger.error(f"Fehler beim Speichern der bereinigten PDF: {save_error}")
                        # Temporäre Datei aufräumen
                        if os.path.exists(temp_output_path):
                            os.remove(temp_output_path)
                        return False
                else:
                    logger.info(f"✅ Keine leeren Seiten gefunden in {os.path.basename(pdf_path)}")
                    return False
                    
            finally:
                # Dokument schließen falls noch nicht geschlossen
                if not doc_closed:
                    try:
                        doc.close()
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"Fehler bei pixelbasierter Leerseiten-Entfernung: {e}")
            return False
    
    async def _add_to_database(self, filename: str, file_path: str):
        """Fügt neue Datei zur Datenbank hinzu falls noch nicht vorhanden."""
        try:
            # Prüfen ob bereits in DB
            vorhandene = [d for d in Dokument.get_all() if d.dateiname == filename]
            
            if not vorhandene:
                # Vorschau-Text extrahieren
                preview_text = await asyncio.to_thread(
                    OCRService.extract_preview_text, file_path, 300
                )
                
                # In DB speichern
                Dokument.create(
                    dateiname=filename,
                    pfad=file_path,
                    inhalt_vorschau=preview_text
                )
                
                logger.info(f"Datei zur Datenbank hinzugefügt: {filename}")
        
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen zur DB: {e}")
    
    def force_check(self):
        """Löst eine sofortige Prüfung aus (für manuellen Trigger)."""
        if self.running:
            # Erstelle Task für sofortige Prüfung
            asyncio.create_task(self._check_and_process_files())
            logger.info("Manuelle OCR-Prüfung ausgelöst")


# Globale Scheduler-Instanz
ocr_scheduler = OCRScheduler(check_interval=30)  # Alle 30 Sekunden prüfen