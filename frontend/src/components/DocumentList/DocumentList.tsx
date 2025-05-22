import { useState, useEffect } from 'react';
import { dokumentService } from '../../services/api';
import DocumentListItem from './DocumentListItem';
import { Dokument } from '../../types';

interface DocumentListProps {
  onSelectDocument: (document: Dokument) => void;
  refreshTrigger?: boolean;
}

/**
 * Komponente für die Anzeige der Dokumentenliste
 */
const DocumentList: React.FC<DocumentListProps> = ({ onSelectDocument, refreshTrigger }) => {
  const [documents, setDocuments] = useState<Dokument[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  // Dokumente beim Laden der Komponente oder bei Aktualisierung abrufen
  useEffect(() => {
    loadDocuments();
  }, [refreshTrigger]);

  // Dokumente vom Backend abrufen
  const loadDocuments = async (): Promise<void> => {
    try {
      setLoading(true);
      const data = await dokumentService.getAllDokumente();
      setDocuments(data.dokumente || []);
      setError(null);
    } catch (err) {
      console.error('Fehler beim Laden der Dokumente:', err);
      setError('Die Dokumente konnten nicht geladen werden. Bitte versuche es später erneut.');
    } finally {
      setLoading(false);
    }
  };

  // Dokument hochladen
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0];
    
    if (!file) return;
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Nur PDF-Dateien werden unterstützt.');
      return;
    }
    
    try {
      setLoading(true);
      await dokumentService.uploadDokument(file);
      await loadDocuments(); // Liste neu laden
      setError(null);
    } catch (err) {
      console.error('Fehler beim Hochladen:', err);
      setError('Das Dokument konnte nicht hochgeladen werden. Bitte versuche es später erneut.');
    } finally {
      setLoading(false);
    }
    
    // Datei-Input zurücksetzen
    event.target.value = '';
  };

  // Dokument löschen
  const handleDelete = async (id: number): Promise<void> => {
    if (!window.confirm('Möchtest du dieses Dokument wirklich löschen?')) {
      return;
    }
    
    try {
      setLoading(true);
      await dokumentService.deleteDokument(id);
      await loadDocuments(); // Liste neu laden
      if (expandedId === id) {
        setExpandedId(null);
      }
    } catch (err) {
      console.error('Fehler beim Löschen:', err);
      setError('Das Dokument konnte nicht gelöscht werden.');
    } finally {
      setLoading(false);
    }
  };

  // Dokument auswählen (für Detailansicht)
  const handleSelect = (document: Dokument): void => {
    if (onSelectDocument) {
      onSelectDocument(document);
    }
  };

  // Dokument ein-/ausklappen
  const toggleExpand = (id: number): void => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="bg-card shadow rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-card-foreground">Dokumente</h2>
        
        <div className="flex items-center">
          <button
            onClick={() => document.getElementById('fileInput')?.click()}
            className="flex items-center bg-primary hover:bg-primary/90 text-primary-foreground px-4 py-2 rounded mr-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
            PDF hochladen
          </button>
          <input
            id="fileInput"
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            className="hidden"
          />
          
          <button
            onClick={loadDocuments}
            className="bg-secondary hover:bg-secondary/80 text-secondary-foreground px-4 py-2 rounded"
            disabled={loading}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
      
      {error && (
        <div className="bg-destructive/10 text-destructive p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {loading && (
        <div className="flex justify-center p-6">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary"></div>
        </div>
      )}
      
      {!loading && documents.length === 0 && (
        <div className="text-center text-muted-foreground p-6">
          <p>Keine Dokumente vorhanden.</p>
          <p className="mt-2">Lade PDF-Dateien hoch, um zu beginnen.</p>
        </div>
      )}
      
      <ul className="divide-y divide-border">
        {documents.map((document) => (
          <DocumentListItem
            key={document.id}
            document={document}
            isExpanded={expandedId === document.id}
            onToggleExpand={() => toggleExpand(document.id)}
            onSelect={() => handleSelect(document)}
            onDelete={() => handleDelete(document.id)}
          />
        ))}
      </ul>
    </div>
  );
};

export default DocumentList;