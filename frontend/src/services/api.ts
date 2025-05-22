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
const API_BASE_URL = 'http://localhost:8000/api';

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
   * @param id Dokument-ID
   * @returns Promise mit OCR-Text
   */
  getDokumentText: async (id: number): Promise<OcrTextResponse> => {
    try {
      const response: AxiosResponse<OcrTextResponse> = await apiClient.get(`/dokumente/ocr/${id}`);
      return response.data;
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

export default {
  dokument: dokumentService,
  metadaten: metadatenService,
};