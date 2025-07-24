/**
 * API-Service für die Kommunikation mit dem Backend
 */

import axios, { AxiosResponse } from 'axios';
import { 
  Dokument, 
  DokumentListResponse, 
  MetadatenFeld,
  MetadatenFeldListResponse,
  OcrTextResponse,
  SuccessResponse
} from '../types';

// API-Basis-URL
const API_BASE_URL = 'http://:8081/api';

// Axios-Instanz mit Basis-URL
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dokument-Service
export const dokumentService = {
  /**
   * Alle Dokumente abrufen
   * @returns Promise mit Dokumentenliste
   */
  getAllDokumente: async (): Promise<DokumentListResponse> => {
    try {
      const response: AxiosResponse<DokumentListResponse> = await apiClient.get('/dokumente');
      return response.data;
    } catch (error) {
      console.error('Fehler beim Abrufen der Dokumente:', error);
      throw error;
    }
  },

  /**
   * Ein einzelnes Dokument abrufen
   * @param id Dokument-ID
   * @returns Promise mit Dokumentdetails
   */
  getDokument: async (id: number): Promise<Dokument> => {
    try {
      const response: AxiosResponse<Dokument> = await apiClient.get(`/dokumente/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Fehler beim Abrufen des Dokuments ${id}:`, error);
      throw error;
    }
  },

  /**
   * OCR-Text eines Dokuments abrufen
   * HINWEIS: Dieser Endpunkt wird nach der OCRmyPDF-Integration nicht mehr benötigt,
   * da der OCR-Text direkt in die PDF eingebettet wird.
   * @param id Dokument-ID
   * @returns Promise mit OCR-Text
   */
  getDokumentText: async (id: number): Promise<OcrTextResponse> => {
    try {
      // Warnung: Dieser Endpunkt ist mit OCRmyPDF nicht mehr verfügbar
      console.warn('getDokumentText wird mit OCRmyPDF-Integration nicht mehr benötigt');
      return { text: 'OCR-Text ist nun direkt in der PDF eingebettet und über den PDF-Viewer zugänglich.' };
    } catch (error) {
      console.error(`Fehler beim Abrufen des OCR-Textes für Dokument ${id}:`, error);
      throw error;
    }
  },

  /**
   * Dokument hochladen
   * @param file PDF-Datei
   * @returns Promise mit hochgeladenem Dokument
   */
  uploadDokument: async (file: File): Promise<Dokument> => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response: AxiosResponse<Dokument> = await apiClient.post('/dokumente/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Fehler beim Hochladen des Dokuments:', error);
      throw error;
    }
  },

  /**
   * Dokument kategorisieren und Metadaten aktualisieren
   * @param id Dokument-ID
   * @param kategorie Kategorie (berta, kosten, irrlaeufer)
   * @param metadaten Metadaten-Objekt
   * @returns Promise mit aktualisiertem Dokument
   */
  kategorisiereDokument: async (
    id: number, 
    kategorie: string, 
    metadaten: Record<string, string> = {}
  ): Promise<Dokument> => {
    try {
      const response: AxiosResponse<Dokument> = await apiClient.put(`/dokumente/${id}/kategorisieren`, {
        kategorie,
        metadaten,
      });
      return response.data;
    } catch (error) {
      console.error(`Fehler beim Kategorisieren des Dokuments ${id}:`, error);
      throw error;
    }
  },

  /**
   * Dokument löschen
   * @param id Dokument-ID
   * @returns Promise mit Erfolgs-/Fehlermeldung
   */
  deleteDokument: async (id: number): Promise<SuccessResponse> => {
    try {
      const response: AxiosResponse<SuccessResponse> = await apiClient.delete(`/dokumente/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Fehler beim Löschen des Dokuments ${id}:`, error);
      throw error;
    }
  },
};

// Metadatenfeld-Service
export const metadatenService = {
  /**
   * Alle Metadatenfelder abrufen
   * @returns Promise mit Metadatenfeldern
   */
  getAllFelder: async (): Promise<MetadatenFeldListResponse> => {
    try {
      const response: AxiosResponse<MetadatenFeldListResponse> = await apiClient.get('/dokumente/metadaten/felder');
      return response.data;
    } catch (error) {
      console.error('Fehler beim Abrufen der Metadatenfelder:', error);
      throw error;
    }
  },

  /**
   * Neues Metadatenfeld erstellen
   * @param feldname Name des Feldes
   * @param beschreibung Beschreibung des Feldes
   * @returns Promise mit Erfolgs-/Fehlermeldung
   */
  createFeld: async (feldname: string, beschreibung: string): Promise<SuccessResponse> => {
    try {
      const response: AxiosResponse<SuccessResponse> = await apiClient.post('/dokumente/metadaten/felder', {
        feldname,
        beschreibung,
      });
      return response.data;
    } catch (error) {
      console.error('Fehler beim Erstellen des Metadatenfelds:', error);
      throw error;
    }
  },

  /**
   * Metadatenfeld löschen
   * @param id Feld-ID
   * @returns Promise mit Erfolgs-/Fehlermeldung
   */
  deleteFeld: async (id: number): Promise<SuccessResponse> => {
    try {
      const response: AxiosResponse<SuccessResponse> = await apiClient.delete(`/dokumente/metadaten/felder/${id}`);
      return response.data;
    } catch (error) {
      console.error(`Fehler beim Löschen des Metadatenfelds ${id}:`, error);
      throw error;
    }
  },
};

// SMB-Konfiguration Interface
export interface SMBConnectionConfig {
  server: string;
  share: string;
  username: string;
  password: string;
  remote_base_path: string;
  domain?: string;
}

// SMB-Status Interface  
export interface SMBStatus {
  configured: boolean;
  connection_active: boolean;
  server?: string;
  share?: string;
  username?: string;
  domain?: string;
  remote_path?: string;
  configured_at?: string;
  backup_folders?: Array<{
    name: string;
    pdf_count: number;
  }>;
}

// SMB-Service
export const smbService = {
  configure: async (config: SMBConnectionConfig): Promise<any> => {
    try {
      const url = '/dokumente/smb/configure';
      console.log('🔍 SMB Configure URL:', `${API_BASE_URL}${url}`);
      console.log('🔍 SMB Configure Data:', config);
      
      const response = await apiClient.post(url, config);
      return response.data;
    } catch (error: any) {
      console.error('❌ SMB Configure Error Details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
        fullURL: `${error.config?.baseURL}${error.config?.url}`,
        data: error.response?.data
      });
      throw error;
    }
  },

  getStatus: async (): Promise<SMBStatus> => {
    try {
      const url = '/dokumente/smb/status';
      console.log('🔍 SMB Status URL:', `${API_BASE_URL}${url}`);
      
      const response = await apiClient.get(url);
      return response.data;
    } catch (error: any) {
      console.error('❌ SMB Status Error Details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        fullURL: `${error.config?.baseURL}${error.config?.url}`,
      });
      throw error;
    }
  },

  /**
   * SMB-Dateien scannen
   */
  scan: async (): Promise<any> => {
    try {
      const response = await apiClient.post('/dokumente/smb/scan');
      return response.data;
    } catch (error) {
      console.error('Fehler beim SMB-Scan:', error);
      throw error;
    }
  },

  /**
   * SMB-Dateien herunterladen
   */
  download: async (): Promise<any> => {
    try {
      const response = await apiClient.post('/dokumente/smb/download');
      return response.data;
    } catch (error) {
      console.error('Fehler beim SMB-Download:', error);
      throw error;
    }
  },

  /**
   * Kompletten SMB-Sync durchführen
   */
  sync: async (): Promise<any> => {
    try {
      const response = await apiClient.post('/dokumente/smb/sync');
      return response.data;
    } catch (error) {
      console.error('Fehler beim SMB-Sync:', error);
      throw error;
    }
  },

  /**
   * SMB-Verbindung trennen
   */
  disconnect: async (): Promise<any> => {
    try {
      const response = await apiClient.delete('/dokumente/smb/disconnect');
      return response.data;
    } catch (error) {
      console.error('Fehler beim Trennen der SMB-Verbindung:', error);
      throw error;
    }
  },
};

export const databaseService = {
  /**
   * Database-Statistiken abrufen
   * @returns Promise mit Datenbankstatistiken
   */
  getStats: async () => {
    try {
      const response = await apiClient.get('/database/stats');
      return response.data;
    } catch (error) {
      console.error('Fehler beim Abrufen der Datenbankstatistiken:', error);
      throw error;
    }
  },

  /**
   * Verfügbare Tabellen abrufen
   * @returns Promise mit Tabellenliste
   */
  getTables: async () => {
    try {
      const response = await apiClient.get('/database/tables');
      return response.data;
    } catch (error) {
      console.error('Fehler beim Abrufen der Tabellen:', error);
      throw error;
    }
  },

  /**
   * Daten einer bestimmten Tabelle abrufen
   * @param tableName Name der Tabelle
   * @param limit Maximale Anzahl Datensätze
   * @returns Promise mit Tabellendaten
   */
  getTableData: async (tableName: string, limit: number = 100) => {
    try {
      const response = await apiClient.get(`/database/tables/${tableName}?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error(`Fehler beim Abrufen der Tabellendaten für ${tableName}:`, error);
      throw error;
    }
  }
};

// Export erweitern
export default {
  dokument: dokumentService,
  metadaten: metadatenService,
  smb: smbService, // NEU
};