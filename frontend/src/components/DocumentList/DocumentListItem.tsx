import React from 'react';
import { Dokument } from '../../types';

interface DocumentListItemProps {
  document: Dokument;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onSelect: () => void;
  onDelete: () => void;
}

/**
 * Komponente für ein einzelnes Element in der Dokumentenliste
 */
const DocumentListItem: React.FC<DocumentListItemProps> = ({ 
  document, 
  isExpanded, 
  onToggleExpand, 
  onSelect, 
  onDelete 
}) => {
  // Kategorie-Badge anzeigen
  const renderKategorieBadge = (kategorie?: string) => {
    if (!kategorie) return null;
    
    const badgeClasses = {
      berta: 'bg-green-100 text-green-800',
      kosten: 'bg-blue-100 text-blue-800',
      irrlaeufer: 'bg-yellow-100 text-yellow-800'
    };
    
    const badgeClass = badgeClasses[kategorie as keyof typeof badgeClasses] || 'bg-muted text-muted-foreground';
    
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${badgeClass}`}>
        {kategorie}
      </span>
    );
  };

  return (
    <li className="py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={onToggleExpand}
            className="mr-2 text-muted-foreground hover:text-foreground"
            aria-label={isExpanded ? 'Einklappen' : 'Ausklappen'}
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className={`h-5 w-5 transition-transform ${isExpanded ? 'transform rotate-90' : ''}`} 
              viewBox="0 0 20 20" 
              fill="currentColor"
            >
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>
          
          <div>
            <h3 className="text-sm md:text-base font-medium text-foreground truncate max-w-xs md:max-w-md">
              {document.dateiname}
            </h3>
            <p className="text-xs text-muted-foreground">
              {new Date(document.erstellt_am).toLocaleDateString('de-DE')}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {renderKategorieBadge(document.kategorie)}
          
          <button
            onClick={onSelect}
            className="text-primary hover:text-primary/80"
            title="Dokument öffnen"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
            </svg>
          </button>
          
          <button
            onClick={onDelete}
            className="text-destructive hover:text-destructive/80"
            title="Dokument löschen"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Ausgeklappter Inhalt */}
      {isExpanded && document.inhalt_vorschau && (
        <div className="mt-3 ml-7 p-3 bg-muted rounded-md text-sm text-foreground">
          <p className="font-medium mb-1">Vorschau:</p>
          <p className="whitespace-pre-line">{document.inhalt_vorschau}</p>
        </div>
      )}
    </li>
  );
};

export default DocumentListItem;