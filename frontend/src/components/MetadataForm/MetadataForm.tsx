import React, { useState, useEffect } from 'react';
import { Dokument, MetadatenFeld, KATEGORIEN } from '../../types';

interface MetadataFormProps {
  document: Dokument;
  metadatenFelder: MetadatenFeld[];
  onSave: (kategorie: string, metadaten: Record<string, string>) => Promise<void>;
  loading: boolean;
}

/**
 * Komponente für das Formular zur Erfassung von Metadaten
 */
const MetadataForm: React.FC<MetadataFormProps> = ({ document, metadatenFelder, onSave, loading }) => {
  const [kategorie, setKategorie] = useState<string>('');
  const [metadaten, setMetadaten] = useState<Record<string, string>>({});
  
  // Formular initialisieren, wenn sich das Dokument ändert
  useEffect(() => {
    if (document) {
      setKategorie(document.kategorie || '');
      setMetadaten(document.metadaten || {});
    }
  }, [document]);
  
  // Metadatenwert aktualisieren
  const handleMetadataChange = (feldname: string, value: string): void => {
    setMetadaten((prevMetadaten) => ({
      ...prevMetadaten,
      [feldname]: value,
    }));
  };
  
  // Formular absenden
  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    
    if (!kategorie) {
      alert('Bitte wähle eine Kategorie aus.');
      return;
    }
    
    onSave(kategorie, metadaten);
  };
  
  if (!document) {
    return null;
  }
  
  return (
    <div className="h-full flex flex-col">
      <div className="bg-muted p-3 border-b border-border">
        <h3 className="font-medium text-card-foreground">Dokument kategorisieren</h3>
      </div>
      
      <form onSubmit={handleSubmit} className="p-4 flex-grow overflow-auto">
        {/* Kategorie-Auswahl */}
        <div className="mb-4">
          <label htmlFor="kategorie" className="block text-sm font-medium text-foreground mb-1">
            Kategorie <span className="text-destructive">*</span>
          </label>
          <select
            id="kategorie"
            value={kategorie}
            onChange={(e) => setKategorie(e.target.value)}
            className="w-full px-3 py-2 border border-input rounded-md shadow-sm focus:outline-none focus:ring-ring focus:border-ring"
            required
          >
            <option value="">-- Kategorie auswählen --</option>
            {KATEGORIEN.map((kat) => (
              <option key={kat.value} value={kat.value}>
                {kat.label}
              </option>
            ))}
          </select>
        </div>
        
        {/* Metadatenfelder */}
        <div className="space-y-4">
          <h4 className="font-medium text-foreground text-sm mb-2">Metadaten</h4>
          
          {metadatenFelder.map((feld) => (
            <div key={feld.id}>
              <label htmlFor={`meta-${feld.feldname}`} className="block text-sm font-medium text-foreground mb-1">
                {feld.beschreibung || feld.feldname}
              </label>
              <input
                id={`meta-${feld.feldname}`}
                type="text"
                value={metadaten[feld.feldname] || ''}
                onChange={(e) => handleMetadataChange(feld.feldname, e.target.value)}
                className="w-full px-3 py-2 border border-input rounded-md shadow-sm focus:outline-none focus:ring-ring focus:border-ring"
                placeholder={`${feld.beschreibung || feld.feldname} eingeben...`}
              />
            </div>
          ))}
          
          {metadatenFelder.length === 0 && (
            <p className="text-sm text-muted-foreground italic">
              Keine Metadatenfelder konfiguriert.
            </p>
          )}
        </div>
        
        {/* Speichern-Button */}
        <div className="mt-6 flex justify-end">
          <button
            type="submit"
            disabled={loading || !kategorie}
            className={`
              px-4 py-2 rounded-md text-primary-foreground 
              ${loading || !kategorie
                ? 'bg-muted text-muted-foreground cursor-not-allowed'
                : 'bg-primary hover:bg-primary/90'}
            `}
          >
            {loading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Wird gespeichert...
              </span>
            ) : (
              'Speichern'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default MetadataForm;