/**
 * Datenmodelle für das Frontend
 */

// Dokument-Modell
export interface Dokument {
  id: number;
  dateiname: string;
  kategorie?: string;
  pfad: string;
  inhalt_vorschau?: string;
  erstellt_am: string;
  metadaten: Record<string, string>;
}

// Metadatenfeld-Modell
export interface MetadatenFeld {
  id: number;
  feldname: string;
  beschreibung: string;
  erstellt_am?: string;
}

// API-Antwort für Dokumentenliste
export interface DokumentListResponse {
  dokumente: Dokument[];
  total: number;
}

// API-Antwort für Metadatenfelder
export interface MetadatenFeldListResponse {
  felder: MetadatenFeld[];
}

// API-Antwort für OCR-Text
export interface OcrTextResponse {
  text: string;
}

// API-Erfolgsantwort
export interface SuccessResponse {
  success: boolean;
  message: string;
  data?: any;
}

// Kategorie-Optionen
export interface KategorieOption {
  value: string;
  label: string;
}

// Definierte Kategorien
export const KATEGORIEN: KategorieOption[] = [
  { value: 'berta', label: 'Berta-Rechnung' },
  { value: 'kosten', label: 'Kostenrechnung' },
  { value: 'irrlaeufer', label: 'Irrläufer' }
];