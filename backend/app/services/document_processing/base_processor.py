"""
Basis-Klasse für Document Processors.
Abstraktes System für die Verarbeitung verschiedener Dokumenttypen.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class BaseDocumentProcessor(ABC):
    """
    Abstrakte Basisklasse für Document Processors.
    
    Jeder Processor kann einen bestimmten Dokumenttyp erkennen und verarbeiten.
    Beispiele: Wareneingang, Rechnung, Zolldokument, etc.
    """
    
    def __init__(self, name: str):
        """
        Args:
            name: Name des Processors (für Logging)
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def can_handle(self, pdf_path: str) -> bool:
        """
        Prüft, ob dieser Processor das gegebene PDF verarbeiten kann.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            
        Returns:
            True wenn der Processor das PDF verarbeiten kann
        """
        pass
    
    @abstractmethod
    async def process(self, pdf_path: str, filename: str) -> bool:
        """
        Verarbeitet das PDF-Dokument.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            filename: Name der Datei
            
        Returns:
            True bei erfolgreicher Verarbeitung
        """
        pass
    
    def _extract_text_from_pdf(self, pdf_path: str, max_lines: int = 10) -> list[str]:
        """
        Hilfsmethode: Extrahiert Text aus PDF (erste N Zeilen).
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            max_lines: Maximale Anzahl Zeilen zu extrahieren
            
        Returns:
            Liste der Textzeilen
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                return []
            
            # Text von der ersten Seite extrahieren
            page = doc[0]
            text = page.get_text()
            doc.close()
            
            # In Zeilen aufteilen und bereinigen
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            return lines[:max_lines]
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren des PDF-Texts: {e}")
            return []
    
    def _log_processing_start(self, pdf_path: str):
        """Hilfsmethode: Loggt den Start der Verarbeitung."""
        self.logger.info(f"🔄 Starte {self.name}-Verarbeitung: {pdf_path}")
    
    def _log_processing_success(self, pdf_path: str, details: str = ""):
        """Hilfsmethode: Loggt erfolgreiche Verarbeitung."""
        detail_msg = f" - {details}" if details else ""
        self.logger.info(f"✅ {self.name}-Verarbeitung erfolgreich: {pdf_path}{detail_msg}")
    
    def _log_processing_error(self, pdf_path: str, error: str):
        """Hilfsmethode: Loggt Verarbeitungsfehler."""
        self.logger.error(f"❌ {self.name}-Verarbeitung fehlgeschlagen: {pdf_path} - {error}")


class DocumentProcessorManager:
    """
    Manager für die Verwaltung und Ausführung von Document Processors.
    """
    
    def __init__(self):
        self.processors: list[BaseDocumentProcessor] = []
        self.logger = logging.getLogger(__name__)
    
    def register_processor(self, processor: BaseDocumentProcessor):
        """
        Registriert einen neuen Document Processor.
        
        Args:
            processor: Processor-Instanz
        """
        self.processors.append(processor)
        self.logger.info(f"📋 Document Processor registriert: {processor.name}")
    
    async def process_document(self, pdf_path: str, filename: str) -> bool:
        """
        Verarbeitet ein Dokument mit dem ersten passenden Processor.
        
        Args:
            pdf_path: Pfad zur PDF-Datei
            filename: Name der Datei
            
        Returns:
            True wenn ein Processor das Dokument verarbeitet hat
        """
        if not self.processors:
            self.logger.debug(f"Keine Processors registriert für: {filename}")
            return False
        
        for processor in self.processors:
            try:
                if await processor.can_handle(pdf_path):
                    self.logger.info(f"📄 Verarbeite mit {processor.name}: {filename}")
                    success = await processor.process(pdf_path, filename)
                    
                    if success:
                        self.logger.info(f"✨ Dokument erfolgreich verarbeitet: {filename}")
                        return True
                    else:
                        self.logger.warning(f"⚠️  Processor {processor.name} konnte {filename} nicht verarbeiten")
                        
            except Exception as e:
                self.logger.error(f"Fehler in Processor {processor.name} für {filename}: {e}")
                continue
        
        self.logger.debug(f"Kein passender Processor gefunden für: {filename}")
        return False
    
    def get_registered_processors(self) -> list[str]:
        """Gibt die Namen aller registrierten Processors zurück."""
        return [processor.name for processor in self.processors]


# Globale Manager-Instanz
document_processor_manager = DocumentProcessorManager()