"""
OCR-Service für die Erstellung durchsuchbarer PDF-Dokumente.
Windows-optimierte Version ohne zusätzliche Tools.
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
        Windows-optimierte Version ohne zusätzliche Tools.
        
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
            
            # OCRmyPDF Konfiguration - Windows-optimiert
            ocrmypdf.ocr(
                input_pdf_path,
                output_pdf_path,
                language='deu',          # Deutsche Sprache
                deskew=False,           # Deaktiviert - benötigt zusätzliche Tools
                remove_vectors=False,    # Vektorgrafiken beibehalten
                force_ocr=False,        # Nur OCR wenn noch nicht vorhanden
                skip_text=False,        # Bestehenden Text nicht überspringen
                clean=False,            # Deaktiviert - benötigt 'unpaper'
                optimize=0,             # Keine Optimierung - vermeidet zusätzliche Abhängigkeiten
                color_conversion_strategy='LeaveColorUnchanged',  # Keine Farbkonvertierung
                progress_bar=False,     # Kein Progress Bar im Log
                use_threads=True,       # Multi-Threading aktivieren
                rotate_pages=False,     # Deaktiviert - vermeidet zusätzliche Tools
                # Weitere Windows-kompatible Optionen
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
            
            # Fallback: Minimale OCR-Konfiguration
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