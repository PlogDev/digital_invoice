import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { dokumentService, metadatenService } from '../../services/api';
import MetadataForm from '../MetadataForm/MetadataForm';
import { Dokument, MetadatenFeld } from '../../types';

// PDF.js Worker-Einrichtung mit lokalem Worker
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf-worker/pdf.worker.min.mjs';

interface DocumentViewerProps {
  document: Dokument;
  onClose: () => void;
  onDocumentUpdated: () => void;
}

/**
 * Komponente für die Anzeige und Bearbeitung eines Dokuments
 */
const DocumentViewer: React.FC<DocumentViewerProps> = ({ document, onClose, onDocumentUpdated }) => {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [ocrText, setOcrText] = useState<string>('');
  const [showOcr, setShowOcr] = useState<boolean>(false);
  const [metadatenFelder, setMetadatenFelder] = useState<MetadatenFeld[]>([]);

  // Dokumenten-Pfad für PDF-Anzeige
  const documentPath = document?.pfad 
    ? `http://localhost:8000/api/dokumente/file/${document.id}`
    : '';

  // Debug: Pfad zur PDF-Datei anzeigen
  useEffect(() => {
    if (document?.pfad) {
      console.log("Original PDF-Pfad:", document.pfad);
      console.log("Generierter API-URL:", documentPath);
    }
  }, [document, documentPath]);

  // Metadatenfelder beim Laden der Komponente abrufen
  useEffect(() => {
    loadMetadatenFelder();
    
    // OCR-Text laden, wenn ein Dokument vorhanden ist
    if (document?.id) {
      loadOcrText(document.id);
    }
  }, [document]);

  // Metadatenfelder vom Backend abrufen
  const loadMetadatenFelder = async (): Promise<void> => {
    try {
      const response = await metadatenService.getAllFelder();
      setMetadatenFelder(response.felder || []);
    } catch (error) {
      console.error('Fehler beim Laden der Metadatenfelder:', error);
      setError('Die Metadatenfelder konnten nicht geladen werden.');
    }
  };

  // OCR-Text eines Dokuments abrufen
  const loadOcrText = async (documentId: number): Promise<void> => {
    try {
      setLoading(true);
      const response = await dokumentService.getDokumentText(documentId);
      setOcrText(response.text || '');
    } catch (error) {
      console.error('Fehler beim Laden des OCR-Textes:', error);
      setError('Der OCR-Text konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  // PDF-Dokument erfolgreich geladen
  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }): void => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  // Zur nächsten Seite blättern
  const goToNextPage = (): void => {
    if (pageNumber < (numPages || 0)) {
      setPageNumber(pageNumber + 1);
    }
  };

  // Zur vorherigen Seite blättern
  const goToPrevPage = (): void => {
    if (pageNumber > 1) {
      setPageNumber(pageNumber - 1);
    }
  };

  // Vergrößern
  const zoomIn = (): void => {
    setScale(Math.min(scale + 0.2, 3.0));
  };

  // Verkleinern
  const zoomOut = (): void => {
    setScale(Math.max(scale - 0.2, 0.5));
  };

  // Dokument kategorisieren und Metadaten aktualisieren
  const handleSaveDocument = async (kategorie: string, metadaten: Record<string, string>): Promise<void> => {
    if (!document || !document.id) return;
    
    try {
      setLoading(true);
      await dokumentService.kategorisiereDokument(document.id, kategorie, metadaten);
      
      if (onDocumentUpdated) {
        onDocumentUpdated();
      }
      
      setError(null);
    } catch (error) {
      console.error('Fehler beim Speichern des Dokuments:', error);
      setError('Das Dokument konnte nicht gespeichert werden.');
    } finally {
      setLoading(false);
    }
  };

  // Keine Dokumentanzeige, wenn kein Dokument ausgewählt ist
  if (!document) {
    return (
      <div className="p-8 text-center">
        <p className="text-muted-foreground">Bitte wähle ein Dokument aus der Liste aus.</p>
      </div>
    );
  }

  return (
    <div className="bg-card shadow rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-muted px-4 py-3 flex justify-between items-center border-b border-border">
        <h2 className="text-lg font-semibold text-card-foreground truncate">
          {document.dateiname}
        </h2>
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground"
          aria-label="Schließen"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      {/* Fehleranzeige */}
      {error && (
        <div className="bg-destructive/10 text-destructive p-3 m-4 rounded">
          {error}
        </div>
      )}

      {/* Hauptinhalt */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
        {/* PDF-Viewer */}
        <div className="border border-border rounded-lg overflow-hidden">
          {/* PDF-Steuerelemente */}
          <div className="bg-muted p-2 flex justify-between items-center border-b border-border">
            <div className="flex items-center space-x-2">
              <button
                onClick={goToPrevPage}
                disabled={pageNumber <= 1}
                className={`p-1 rounded ${
                  pageNumber <= 1 
                    ? 'text-muted-foreground cursor-not-allowed' 
                    : 'text-foreground hover:bg-accent'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </button>
              
              <span className="text-sm text-foreground">
                Seite {pageNumber} von {numPages || '--'}
              </span>
              
              <button
                onClick={goToNextPage}
                disabled={!numPages || pageNumber >= numPages}
                className={`p-1 rounded ${
                  !numPages || pageNumber >= numPages 
                    ? 'text-muted-foreground cursor-not-allowed' 
                    : 'text-foreground hover:bg-accent'
                }`}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={zoomOut}
                className="p-1 rounded text-foreground hover:bg-accent"
                title="Verkleinern"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5 10a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
              </button>
              
              <span className="text-sm text-foreground">{Math.round(scale * 100)}%</span>
              
              <button
                onClick={zoomIn}
                className="p-1 rounded text-foreground hover:bg-accent"
                title="Vergrößern"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
              </button>
              
              <button
                onClick={() => setShowOcr(!showOcr)}
                className={`p-1 rounded ${
                  showOcr ? 'bg-primary/20 text-primary' : 'text-foreground hover:bg-accent'
                }`}
                title={showOcr ? 'PDF anzeigen' : 'OCR-Text anzeigen'}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2h-1.528A6 6 0 004 9.528V4z" />
                  <path fillRule="evenodd" d="M8 10a4 4 0 00-3.446 6.032l-1.261 1.26a1 1 0 101.414 1.415l1.261-1.261A4 4 0 108 10zm-2 4a2 2 0 114 0 2 2 0 01-4 0z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
          
          {/* PDF/OCR-Anzeige */}
          <div className="bg-background min-h-96 flex justify-center">
            {loading ? (
              <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
              </div>
            ) : showOcr ? (
              <div className="p-4 w-full overflow-auto">
                <pre className="whitespace-pre-wrap text-sm text-foreground">{ocrText || 'Kein OCR-Text verfügbar.'}</pre>
              </div>
            ) : (
              <Document
                file={documentPath}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={(error) => {
                  console.error('PDF-Ladefehler:', error);
                  setError("Die PDF-Datei konnte nicht geladen werden. " + 
                           (error instanceof Error ? error.message : String(error)));
                }}
                loading={
                  <div className="flex justify-center items-center h-full">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
                  </div>
                }
              >
                <Page 
                  pageNumber={pageNumber} 
                  scale={scale}
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                />
              </Document>
            )}
          </div>
        </div>
        
        {/* Metadaten-Formular */}
        <div className="border border-border rounded-lg overflow-hidden">
          <MetadataForm
            document={document}
            metadatenFelder={metadatenFelder}
            onSave={handleSaveDocument}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
