import React, { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { dokumentService, metadatenService } from '../../services/api';
import MetadataForm from '../MetadataForm/MetadataForm';
import { Dokument, MetadatenFeld } from '../../types';

// PDF.js Worker-Einrichtung - korrigierter Pfad
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
  const [showOcr, setShowOcr] = useState<boolean>(false);
  const [metadatenFelder, setMetadatenFelder] = useState<MetadatenFeld[]>([]);
  const [csvReimporting, setCsvReimporting] = useState<boolean>(false);

  // Dokumenten-Pfad für PDF-Anzeige
  const documentPath = document?.pfad 
    ? `http://localhost:8081/api/dokumente/file/${document.id}`
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

  // PDF-Dokument erfolgreich geladen
  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }): void => {
    setNumPages(numPages);
    setPageNumber(1);
    setError(null); // Fehler zurücksetzen bei erfolgreichem Laden
  };

  const onDocumentLoadError = (error: Error): void => {
    console.error('PDF-Ladefehler DETAILS:', error);
    console.error('PDF-URL war:', documentPath);
    setError(`Die PDF-Datei konnte nicht geladen werden: ${error.message}`);
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

  // CSV-Reimport Funktion
  const handleCsvReimport = async (): Promise<void> => {
    if (!document || !document.id) return;
    
    const confirmed = window.confirm(
      `CSV-Daten für "${document.dateiname}" neu importieren?\n\n` +
      `Alle vorhandenen Chargen-Datensätze werden gelöscht und neu aus den CSV-Dateien geladen.`
    );
    
    if (!confirmed) return;
    
    try {
      setCsvReimporting(true);
      setError(null);
      
      const response = await fetch(
        `http://localhost:8081/api/dokumente/${document.id}/csv-reimport`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || 'Fehler beim CSV-Reimport');
      }
      
      // Erfolgsmeldung anzeigen
      alert(
        `CSV-Reimport erfolgreich!\n\n` +
        `${result.data.deleted_count} alte Datensätze gelöscht\n` +
        `${result.data.imported_count} neue Datensätze importiert`
      );
      
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unbekannter Fehler';
      setError(`CSV-Reimport fehlgeschlagen: ${errorMsg}`);
      console.error('CSV-Reimport Fehler:', err);
    } finally {
      setCsvReimporting(false);
    }
  };

  // Hilfsfunktion: Prüft ob Dokument ein Wareneingang ist
  const isWareneingangDocument = (): boolean => {
    return document?.unterkategorie === 'Lieferschein_extern' || 
          document?.kategorie === 'berta'; // Falls noch alte Kategorisierung
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
          <div className="mt-2 text-sm">
            <p>Mögliche Lösungen:</p>
            <ul className="list-disc list-inside mt-1">
              <li>Backend-Server läuft auf Port 8081</li>
              <li>PDF-Worker-Datei ist im public/pdf-worker/ Verzeichnis</li>
              <li>Seite neu laden (F5)</li>
            </ul>
          </div>
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
                title={showOcr ? 'PDF anzeigen' : 'OCR-Vorschau anzeigen'}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2h-1.528A6 6 0 004 9.528V4z" />
                  <path fillRule="evenodd" d="M8 10a4 4 0 00-3.446 6.032l-1.261 1.26a1 1 0 101.414 1.415l1.261-1.261A4 4 0 108 10zm-2 4a2 2 0 114 0 2 2 0 01-4 0z" clipRule="evenodd" />
                </svg>
              </button>
              {isWareneingangDocument() && (
                <button
                  onClick={handleCsvReimport}
                  disabled={csvReimporting}
                  className={`p-1 rounded text-foreground hover:bg-accent ${
                    csvReimporting ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                  title="CSV-Daten neu importieren"
                >
                  {csvReimporting ? (
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-current border-t-transparent"></div>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              )}
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
                <div className="text-sm text-foreground">
                  <h3 className="font-medium mb-2">OCR-Vorschau:</h3>
                  <p className="text-muted-foreground italic mb-2">
                    Die vollständige OCR-Texterkennung wird nach der Kategorisierung in die PDF eingebettet.
                  </p>
                  <pre className="whitespace-pre-wrap bg-muted p-3 rounded">
                    {document.inhalt_vorschau || 'Keine Vorschau verfügbar.'}
                  </pre>
                </div>
              </div>
            ) : (
              <Document
                file={documentPath}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading={
                  <div className="flex justify-center items-center h-full">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
                  </div>
                }
                error={
                  <div className="flex flex-col justify-center items-center h-full p-4 text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-destructive mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <p className="text-destructive font-medium">PDF konnte nicht geladen werden</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Prüfe die Netzwerkverbindung und Backend-Erreichbarkeit
                    </p>
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