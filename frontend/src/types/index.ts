/**
 * Datenmodelle für das Frontend
 */

// Dokument-Modell
export interface Dokument {
  id: number;
  dateiname: string;
  kategorie?: string;
  unterkategorie?: string; // NEU: Unterkategorie hinzugefügt
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

// Unterkategorie-Optionen
export interface UnterkategorieOption {
  value: string;
  label: string;
}

// Definierte Kategorien (Legacy)
export const KATEGORIEN: KategorieOption[] = [
  { value: 'berta', label: 'Berta-Rechnung' },
  { value: 'kosten', label: 'Kostenrechnung' },
  { value: 'irrlaeufer', label: 'Irrläufer' }
];

// Neue Unterkategorien (basierend auf PostgreSQL-Struktur)
export const UNTERKATEGORIEN: UnterkategorieOption[] = [
  { value: 'Berta-Rechnung', label: 'Berta-Rechnung' },
  { value: 'Kostenrechnung', label: 'Kostenrechnung' },
  { value: 'Irrläufer', label: 'Irrläufer' },
  { value: 'Lieferschein_extern', label: 'Externe Lieferscheine (Wareneingang)' },
  { value: 'Lieferschein_intern', label: 'Interne Lieferscheine' },
  { value: 'Ursprungszeugnis', label: 'Ursprungszeugnisse' },
  { value: 'EUR1', label: 'EUR.1 Präferenznachweis' },
  { value: 'ATR', label: 'ATR-Dokumente' },
  { value: 'Ausfuhrbegleitdokument', label: 'Ausfuhrbegleitdokumente' }
];