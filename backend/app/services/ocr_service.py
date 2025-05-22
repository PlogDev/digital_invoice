"""
OCR-Service für die Textextraktion aus PDF-Dokumenten.
"""

import logging
import os
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from ..config.settings import OCR_LANGUAGE, OCR_PREVIEW_LENGTH, TESSERACT_CMD

# Konfiguriere Tesseract-Pfad
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Logger einrichten
logger = logging.getLogger(__name__)

class OCRService:
    """Service für die Texterkennung in PDF-Dokumenten."""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str, max_pages: int = 1) -> str:
        """Extrahiert Text aus einer PDF-Datei mittels OCR.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            max_pages: Maximale Anzahl zu verarbeitender Seiten
            
        Returns:
            Extrahierter Text als String
        """
        try:
            # Überprüfe, ob die Datei existiert
            if not os.path.isfile(pdf_path):
                logger.error(f"PDF-Datei nicht gefunden: {pdf_path}")
                return ""
            
            logger.info(f"Konvertiere PDF zu Bildern: {pdf_path}")
            # PDF zu Bildern konvertieren
            images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)
            
            if not images:
                logger.warning(f"Keine Bilder aus PDF extrahiert: {pdf_path}")
                return ""
            
            text = ""
            # OCR auf jede Seite anwenden
            for i, img in enumerate(images):
                logger.info(f"OCR wird auf Seite {i+1} angewendet")
                page_text = pytesseract.image_to_string(img, lang=OCR_LANGUAGE)
                text += page_text + "\n\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"Fehler bei OCR: {str(e)}")
            return ""
    
    @staticmethod
    def get_preview(text: str, length: int = OCR_PREVIEW_LENGTH) -> str:
        """Erstellt eine Vorschau des extrahierten Textes.
        
        Args:
            text: Der vollständige Text
            length: Maximale Länge der Vorschau
            
        Returns:
            Textvorschau mit max. 'length' Zeichen
        """
        if not text:
            return ""
        
        # Entferne überschüssige Leerzeichen und Zeilenumbrüche
        cleaned_text = " ".join(text.split())
        
        # Kürze auf max. Länge
        if len(cleaned_text) <= length:
            return cleaned_text
        
        # Schneide nach dem letzten vollständigen Wort
        preview = cleaned_text[:length]
        last_space = preview.rfind(" ")
        
        if last_space > 0:
            preview = preview[:last_space]
        
        return preview + "..."