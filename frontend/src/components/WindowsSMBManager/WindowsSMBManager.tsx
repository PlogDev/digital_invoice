import React, { useState, useEffect } from 'react';
import { 
  Server, 
  Folder, 
  Download, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Info,
  Eye,
  EyeOff,
  Play,
  Pause,
  Settings
} from 'lucide-react';
import { smbService } from '../../services/api';

interface SMBStatus {
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

interface SyncResults {
  phase: string;
  scan_time?: string;
  download_time?: string;
  folders_scanned: number;
  total_files: number;
  new_files: number;
  downloaded: number;
  download_failed?: number;
  processed_for_ocr: number;
  errors?: string[];
}

const WindowsSMBManager: React.FC = () => {
  const [smbStatus, setSmbStatus] = useState<SMBStatus>({ configured: false, connection_active: false });
  const [configForm, setConfigForm] = useState({
    server: '192.168.66.7',
    share: 'Daten',
    username: 'nsinger',
    password: '',
    domain: 'PLOGSTIES',
    remote_base_path: 'Dennis\\Nico\\PDMS_Anhänge_Backup'
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [configuring, setConfiguring] = useState(false);
  const [lastSyncResults, setLastSyncResults] = useState<SyncResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [autoSync, setAutoSync] = useState(false);
  const [autoSyncInterval, setAutoSyncInterval] = useState<number | null>(null);
  const [writeTestResults, setWriteTestResults] = useState<any>(null);
  const [testingWrite, setTestingWrite] = useState(false);

  // const API_BASE_URL = 'http://localhost:8081/api';

  // Status beim Laden abrufen
  useEffect(() => {
    loadSMBStatus();
  }, []);

  // Auto-Sync Timer
  useEffect(() => {
    if (autoSync && smbStatus.configured && smbStatus.connection_active) {
      const interval = setInterval(() => {
        performSync();
      }, 300000); // Alle 5 Minuten
      
      setAutoSyncInterval(interval);
    } else {
      if (autoSyncInterval) {
        clearInterval(autoSyncInterval);
        setAutoSyncInterval(null);
      }
    }
    
    return () => {
      if (autoSyncInterval) {
        clearInterval(autoSyncInterval);
      }
    };
  }, [autoSync, smbStatus.configured, smbStatus.connection_active]);

  const loadSMBStatus = async () => {
    try {
      const data = await smbService.getStatus(); // ✅ Service verwenden
      setSmbStatus(data);
    } catch (err) {
      setError('Fehler beim Laden des SMB-Status');
    }
  };

const configureSMB = async () => {
  setConfiguring(true);
  setError(null);
  setSuccess(null);

  // VALIDATION hinzufügen:
  if (!configForm.server || !configForm.share || !configForm.username || 
      !configForm.password || !configForm.remote_base_path) {
    setError('Bitte fülle alle Pflichtfelder aus (*, password, remote_base_path)');
    setConfiguring(false);
    return;
  }

  try {
    console.log('🔧 Sende SMB-Config:', {
      ...configForm,
      password: '***' // Passwort nicht loggen
    });

    const data = await smbService.configure(configForm);

    if (data.success) {
      setSuccess(`✅ ${data.message} - ${data.total_pdfs || 0} PDFs in ${data.backup_folders?.length || 0} Backup-Ordnern gefunden`);
      setTimeout(() => setSuccess(null), 5000);
      loadSMBStatus();
    } else {
      setError(data.detail || 'Konfiguration fehlgeschlagen');
    }
  } catch (err: any) {
    console.error('❌ SMB Configure Full Error:', err);
    
    const errorMsg = err.response?.data?.detail || 
                     err.response?.data?.message ||
                     err.message || 
                     'Verbindungsfehler beim Konfigurieren';
    setError(errorMsg);
  } finally {
    setConfiguring(false);
  }
};

  const performSync = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await smbService.sync(); // ✅ Service verwenden

      if (data.success) {
        setLastSyncResults(data.sync_results);
        setSuccess(data.message);
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError(data.detail || 'Sync fehlgeschlagen');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Verbindungsfehler beim Sync';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const disconnectSMB = async () => {
    try {
      const data = await smbService.disconnect(); // ✅ Service verwenden

      if (data.success) {
        setSuccess(data.message);
        setTimeout(() => setSuccess(null), 3000);
        setSmbStatus({ configured: false, connection_active: false });
        setLastSyncResults(null);
        setAutoSync(false);
      } else {
        setError('Fehler beim Trennen der Verbindung');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Verbindungsfehler beim Trennen';
      setError(errorMsg);
    }
  };

  const testWritePermissions = async () => {
    setTestingWrite(true);
    setError(null);
    setWriteTestResults(null);

    try {
      const data = await smbService.testWritePermissions();

      if (data.success) {
        setWriteTestResults(data);
        
        if (data.write_access) {
          setSuccess('✅ Vollzugriff bestätigt! Server-seitige Dateiverwaltung möglich.');
        } else {
          setSuccess('⚠️ Nur Lesezugriff. Download-basierte Verarbeitung wird verwendet.');
        }
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError('Test fehlgeschlagen');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Fehler beim Write-Test';
      setError(errorMsg);
    } finally {
      setTestingWrite(false);
    }
  }; 


  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setConfigForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center">
            <Server className="mr-2" />
            Windows Server Integration
          </h1>
          <p className="text-gray-600">Automatische PDF-Synchronisation von deinem Windows Server</p>
        </div>
        
        {smbStatus.configured && (
          <div className="flex items-center space-x-2">
            <div className={`flex items-center px-3 py-1 rounded-full text-sm ${
              smbStatus.connection_active 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {smbStatus.connection_active ? (
                <CheckCircle className="h-4 w-4 mr-1" />
              ) : (
                <XCircle className="h-4 w-4 mr-1" />
              )}
              {smbStatus.connection_active ? 'Verbunden' : 'Getrennt'}
            </div>
            
            <button
              onClick={() => setAutoSync(!autoSync)}
              className={`flex items-center px-3 py-1 rounded-full text-sm ${
                autoSync 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-gray-100 text-gray-600'
              }`}
              title={autoSync ? 'Auto-Sync deaktivieren' : 'Auto-Sync aktivieren (alle 5 Min)'}
            >
              {autoSync ? <Pause className="h-4 w-4 mr-1" /> : <Play className="h-4 w-4 mr-1" />}
              Auto-Sync
            </button>
          </div>
        )}
      </div>

      {/* Status-Nachrichten */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
          <span className="text-red-800">{error}</span>
          <button 
            onClick={() => setError(null)}
            className="ml-auto text-red-600 hover:text-red-800"
          >
            ×
          </button>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center">
          <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
          <span className="text-green-800">{success}</span>
        </div>
      )}

      {/* SMB-Konfiguration */}
      {!smbStatus.configured ? (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <Settings className="h-5 w-5 mr-2" />
            Windows Server konfigurieren
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Server IP/Name *
              </label>
              <input
                type="text"
                name="server"
                value={configForm.server}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="192.168.66.7"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Share-Name *
              </label>
              <input
                type="text"
                name="share"
                value={configForm.share}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Daten"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Benutzername *
              </label>
              <input
                type="text"
                name="username"
                value={configForm.username}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="nsinger"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Passwort *
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  name="password"
                  value={configForm.password}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Domäne (optional)
              </label>
              <input
                type="text"
                name="domain"
                value={configForm.domain}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="PLOGSTIES"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Remote-Pfad *
              </label>
              <input
                type="text"
                name="remote_base_path"
                value={configForm.remote_base_path}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Dennis\\Nico\\PDMS_Anhänge_Backup"
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={configureSMB}
              disabled={configuring}
              className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {configuring ? (
                <>
                  <RefreshCw className="animate-spin h-4 w-4 mr-2" />
                  Teste Verbindung...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Verbindung konfigurieren
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        // SMB-Status und Steuerung
        <div className="space-y-4">
          {/* Aktuelle Konfiguration */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">Aktuelle Konfiguration</h2>
              <button
                onClick={disconnectSMB}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Verbindung trennen
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Server:</span>
                <div className="font-medium">{smbStatus.server}\\{smbStatus.share}</div>
              </div>
              <div>
                <span className="text-gray-500">Benutzer:</span>
                <div className="font-medium">
                  {smbStatus.domain && `${smbStatus.domain}\\`}{smbStatus.username}
                </div>
              </div>
              <div>
                <span className="text-gray-500">Remote-Pfad:</span>
                <div className="font-medium font-mono text-xs">{smbStatus.remote_path}</div>
              </div>
            </div>

            {/* Backup-Ordner */}
            {smbStatus.backup_folders && smbStatus.backup_folders.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Gefundene Backup-Ordner:</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {smbStatus.backup_folders.map((folder, index) => (
                    <div key={index} className="bg-gray-50 rounded-md p-2 text-sm">
                      <div className="font-medium">{folder.name}</div>
                      <div className="text-gray-500">{folder.pdf_count} PDFs</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sync-Steuerung */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900">Synchronisation</h2>
              <button
                onClick={performSync}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <RefreshCw className="animate-spin h-4 w-4 mr-2" />
                    Synchronisiere...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Jetzt synchronisieren
                  </>
                )}
              </button>
            </div>

            {/* Letzte Sync-Ergebnisse */}
            {lastSyncResults && (
              <div className="border rounded-lg p-4 bg-gray-50">
                <h3 className="font-medium text-gray-900 mb-3">Letzte Synchronisation</h3>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Ordner gescannt:</span>
                    <div className="font-medium">{lastSyncResults.folders_scanned}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Dateien gefunden:</span>
                    <div className="font-medium">{lastSyncResults.total_files}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Neue Dateien:</span>
                    <div className="font-medium text-blue-600">{lastSyncResults.new_files}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Heruntergeladen:</span>
                    <div className="font-medium text-green-600">{lastSyncResults.downloaded}</div>
                  </div>
                </div>

                <div className="mt-3 text-xs text-gray-500">
                  {lastSyncResults.scan_time && `Scan: ${new Date(lastSyncResults.scan_time).toLocaleString('de-DE')}`}
                  {lastSyncResults.download_time && ` • Download: ${new Date(lastSyncResults.download_time).toLocaleString('de-DE')}`}
                </div>

                {lastSyncResults.errors && lastSyncResults.errors.length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm text-red-600 font-medium">Fehler:</div>
                    <ul className="text-xs text-red-600 list-disc list-inside">
                      {lastSyncResults.errors.slice(0, 3).map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {smbStatus.configured && smbStatus.connection_active && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Schreibberechtigung testen</h2>
            <button
              onClick={testWritePermissions}
              disabled={testingWrite}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {testingWrite ? (
                <>
                  <RefreshCw className="animate-spin h-4 w-4 mr-2" />
                  Teste...
                </>
              ) : (
                <>
                  <Settings className="h-4 w-4 mr-2" />
                  Schreibrechte testen
                </>
              )}
            </button>
          </div>
          
          <p className="text-sm text-gray-600 mb-4">
            Testet ob PDFs direkt auf dem Server verwaltet oder lokal heruntergeladen werden müssen.
          </p>
          
          {writeTestResults && (
            <div className="border rounded-lg p-4 bg-gray-50">
              <div className="flex items-center mb-3">
                {writeTestResults.write_access ? (
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                )}
                <span className={`font-medium ${
                  writeTestResults.write_access ? 'text-green-800' : 'text-yellow-800'
                }`}>
                  {writeTestResults.write_access ? 'Vollzugriff verfügbar' : 'Nur Lesezugriff'}
                </span>
              </div>
              
              <div className="text-sm text-gray-700 mb-3">
                <strong>Getestete Datei:</strong> {writeTestResults.test_details?.test_file_used}
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs mb-3">
                {Object.entries(writeTestResults.operations).map(([op, success]) => (
                  <div key={op} className={`flex items-center ${success ? 'text-green-600' : 'text-red-600'}`}>
                    {success ? <CheckCircle className="h-3 w-3 mr-1" /> : <XCircle className="h-3 w-3 mr-1" />}
                    {op.replace('_', ' ')}
                  </div>
                ))}
              </div>
              
              <div className="bg-blue-50 rounded p-3">
                <div className="text-sm font-medium text-blue-800 mb-1">
                  📋 Empfohlene Strategie: {writeTestResults.recommendation?.strategy}
                </div>
                <div className="text-sm text-blue-700">
                  {writeTestResults.recommendation?.description}
                </div>
                {writeTestResults.recommendation?.benefits && (
                  <ul className="text-xs text-blue-600 mt-2 list-disc list-inside">
                    {writeTestResults.recommendation.benefits.map((benefit: string, index: number) => (
                      <li key={index}>{benefit}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Info-Box */}
      <div className="bg-blue-50 rounded-lg p-4">
        <div className="flex items-start">
          <Info className="h-4 w-4 text-blue-600 mr-2 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p><strong>So funktioniert es:</strong></p>
            <ul className="mt-1 list-disc list-inside space-y-1">
              <li>System scannt alle Backup-Ordner nach neuen PDF-Dateien</li>
              <li>Neue PDFs werden automatisch heruntergeladen</li>
              <li>OCR-Verarbeitung erfolgt automatisch im Hintergrund</li>
              <li>Auto-Sync prüft alle 5 Minuten nach neuen Dateien</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WindowsSMBManager;