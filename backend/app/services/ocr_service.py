"""
OCR-Service für die Erstellung durchsuchbarer PDF-Dokumente.
Saubere Version ohne problematische Parameter.
"""

import logging
import os
import tempfile
from pathlib import Path

import ocrmypdf

from ..config.settings import OCR_LANGUAGE

# Logger einrichten
logger = logging.getLogger(__name__)

class OCRService:
    """Service für die OCR-Verarbeitung von PDF-Dokumenten mit OCRmyPDF."""
    
    @staticmethod
    def create_searchable_pdf(input_pdf_path: str, output_pdf_path: str) -> bool:
        """
        Erstellt eine durchsuchbare PDF-Datei mit eingebetteter OCR-Textebene.
        
        Args:
            input_pdf_path: Pfad zur Eingabe-PDF
            output_pdf_path: Pfad zur Ausgabe-PDF (durchsuchbar)
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            # Überprüfe, ob die Eingabedatei existiert
            if not os.path.isfile(input_pdf_path):
                logger.error(f"PDF-Datei nicht gefunden: {input_pdf_path}")
                return False
            
            logger.info(f"Starte OCR-Verarbeitung für: {input_pdf_path}")
            
            # Stelle sicher, dass das Ausgabeverzeichnis existiert
            output_dir = Path(output_pdf_path).parent
            os.makedirs(output_dir, exist_ok=True)
            
            # Saubere OCRmyPDF Konfiguration - nur bewährte Parameter
            ocrmypdf.ocr(
                input_pdf_path,
                output_pdf_path,
                language='deu',          # Deutsche Sprache
                deskew=False,           # Deaktiviert - benötigt zusätzliche Tools
                remove_vectors=False,    # Vektorgrafiken beibehalten
                force_ocr=False,        # Nur OCR wenn noch nicht vorhanden
                skip_text=False,        # Bestehenden Text nicht überspringen
                clean=False,            # Deaktiviert - benötigt 'unpaper'
                optimize=0,             # Keine Optimierung
                color_conversion_strategy='LeaveColorUnchanged',  # Keine Farbkonvertierung
                progress_bar=False,     # Kein Progress Bar im Log
                use_threads=True,       # Multi-Threading aktivieren
                rotate_pages=False,     # Deaktiviert
                tesseract_timeout=300,  # 5 Minuten Timeout
                tesseract_pagesegmode=1,  # Automatische Seitensegmentierung
            )
            
            logger.info(f"OCR-Verarbeitung erfolgreich abgeschlossen: {output_pdf_path}")
            return True
            
        except ocrmypdf.exceptions.PriorOcrFoundError:
            logger.info(f"PDF bereits durchsuchbar, kopiere Original: {input_pdf_path}")
            # Falls PDF bereits OCR-Text hat, einfach kopieren
            import shutil
            shutil.copy2(input_pdf_path, output_pdf_path)
            return True
            
        except ocrmypdf.exceptions.InputFileError as e:
            logger.error(f"Eingabedatei-Fehler bei OCR: {str(e)}")
            return False
            
        except ocrmypdf.exceptions.OutputFileAccessError as e:
            logger.error(f"Ausgabedatei-Fehler bei OCR: {str(e)}")
            return False
            
        except ocrmypdf.exceptions.MissingDependencyError as e:
            logger.error(f"Fehlende Abhängigkeit bei OCR: {str(e)}")
            logger.info("Versuche OCR mit minimaler Konfiguration...")
            
            # Minimaler Fallback
            try:
                ocrmypdf.ocr(
                    input_pdf_path,
                    output_pdf_path,
                    language='deu',
                    force_ocr=False,
                    skip_text=False,
                    progress_bar=False,
                )
                logger.info(f"Fallback-OCR erfolgreich: {output_pdf_path}")
                return True
            except Exception as fallback_error:
                logger.error(f"Auch Fallback-OCR fehlgeschlagen: {str(fallback_error)}")
                return False
            
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei OCR-Verarbeitung: {str(e)}")
            
            # Letzter Fallback: Datei kopieren ohne OCR
            logger.info("Letzte Option: Kopiere PDF ohne OCR-Verarbeitung")
            try:
                import shutil
                shutil.copy2(input_pdf_path, output_pdf_path)
                logger.warning(f"PDF ohne OCR kopiert: {output_pdf_path}")
                return True
            except Exception as copy_error:
                logger.error(f"Auch Kopieren fehlgeschlagen: {str(copy_error)}")
                return False
    
    @staticmethod
    def remove_blank_pages_advanced(pdf_path: str) -> bool:
        """
        Entfernt leere Seiten mit eigener Implementierung (PyMuPDF hat keine is_blank() Methode!).
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            bool: True wenn Seiten entfernt wurden, False sonst
        """
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            pages_to_remove = []
            
            # Jede Seite prüfen
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Text prüfen
                text = page.get_text().strip()
                has_meaningful_text = len(text) > 5 and not text.isspace()
                
                # Bilder prüfen
                images = page.get_images()
                has_images = len(images) > 0
                
                # Zeichnungen prüfen
                has_drawings = False
                try:
                    drawings = page.get_drawings()
                    has_drawings = len(drawings) > 0
                except:
                    pass
                
                # Seite ist leer wenn sie keinen relevanten Inhalt hat
                is_blank = not (has_meaningful_text or has_images or has_drawings)
                
                if is_blank:
                    pages_to_remove.append(page_num)
            
            # Seiten von hinten nach vorne löschen (Index bleibt stabil)
            removed_count = 0
            for page_num in reversed(pages_to_remove):
                doc.delete_page(page_num)
                removed_count += 1
            
            if removed_count > 0:
                # Dokument speichern
                doc.save(pdf_path, incremental=False, deflate=True)
                logger.info(f"Leerseiten-Entfernung: {removed_count} Seiten entfernt aus {pdf_path}")
            else:
                logger.debug(f"Keine leeren Seiten gefunden in {pdf_path}")
            
            doc.close()
            return removed_count > 0
            
        except Exception as e:
            logger.error(f"Fehler bei Leerseiten-Entfernung: {str(e)}")
            return False
    
    @staticmethod
    def extract_preview_text(pdf_path: str, max_chars: int = 200) -> str:
        """
        Extrahiert eine Textvorschau aus einer PDF-Datei.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            max_chars: Maximale Anzahl Zeichen für die Vorschau
            
        Returns:
            str: Textvorschau oder leerer String bei Fehler
        """
        try:
            import fitz  # PyMuPDF für Textextraktion

            # PDF öffnen
            doc = fitz.open(pdf_path)
            
            # Text von der ersten Seite extrahieren
            if len(doc) > 0:
                page = doc[0]
                text = page.get_text()
                
                # Bereinigen und kürzen
                cleaned_text = " ".join(text.split())
                
                if len(cleaned_text) <= max_chars:
                    preview = cleaned_text
                else:
                    # An Wortgrenze kürzen
                    preview = cleaned_text[:max_chars]
                    last_space = preview.rfind(" ")
                    if last_space > 0:
                        preview = preview[:last_space]
                    preview += "..."
                
                doc.close()
                return preview
            
            doc.close()
            return ""
            
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren der Textvorschau: {str(e)}")
            return ""
    
    @staticmethod
    def process_pdf_with_ocr(input_path: str, output_path: str) -> tuple[bool, str]:
        """
        Verarbeitet eine PDF-Datei mit OCR und erstellt eine durchsuchbare Version.
        
        Args:
            input_path: Pfad zur ursprünglichen PDF
            output_path: Pfad für die durchsuchbare PDF
            
        Returns:
            tuple: (Erfolg, Vorschau-Text)
        """
        # 1. OCR-Verarbeitung
        success = OCRService.create_searchable_pdf(input_path, output_path)
        
        if not success:
            logger.error(f"OCR-Verarbeitung fehlgeschlagen für: {input_path}")
            return False, ""
        
        # 2. Vorschau-Text aus der neuen PDF extrahieren
        preview_text = OCRService.extract_preview_text(output_path)
        
        return True, preview_text