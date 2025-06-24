"""
Document Processing Package.
Modulares System für die Verarbeitung verschiedener Dokumenttypen.
"""

from .base_processor import (
    BaseDocumentProcessor,
    DocumentProcessorManager,
    document_processor_manager,
)
from .wareneingang_processor import WareneingangProcessor

# Wareneingang Processor automatisch registrieren
wareneingang_processor = WareneingangProcessor()
document_processor_manager.register_processor(wareneingang_processor)

__all__ = [
    'BaseDocumentProcessor',
    'DocumentProcessorManager', 
    'document_processor_manager',
    'WareneingangProcessor',
    'wareneingang_processor'
]