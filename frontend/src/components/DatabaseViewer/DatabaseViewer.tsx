import React, { useState, useEffect } from 'react';
import { Database, Table, BarChart3, RefreshCw } from 'lucide-react';
import { databaseService } from '../../services/api'; // ✅ Zentraler Service

interface TableData {
  table_name: string;
  count: number;
  data: any[];
}

interface DatabaseStats {
  dokumente_count: number;
  kategorien_count: number;
  unterkategorien_count: number;
  metadaten_felder_count: number;
  lieferscheine_extern_count: number;
  lieferscheine_intern_count: number;
  chargen_einkauf_count: number;
  chargen_verkauf_count: number;
}

const DatabaseViewer: React.FC = () => {
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [tableData, setTableData] = useState<TableData | null>(null);
  const [stats, setStats] = useState<DatabaseStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const availableTables = {
    dokumente: 'Dokumente',
    kategorien: 'Kategorien',
    unterkategorien: 'Unterkategorien',
    metadaten_felder: 'Metadatenfelder',
    lieferscheine_extern: 'Externe Lieferscheine',
    lieferscheine_intern: 'Interne Lieferscheine',
    chargen_einkauf: 'Chargen Einkauf',
    chargen_verkauf: 'Chargen Verkauf'
  };

  // Statistiken beim Laden abrufen
  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await databaseService.getStats(); // ✅ Nutzt zentralen Service
      setStats(data.stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unbekannter Fehler');
      console.error('Database Stats Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadTableData = async (tableName: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await databaseService.getTableData(tableName); // ✅ Nutzt zentralen Service
      setTableData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fehler beim Laden der Tabellendaten');
      console.error('Table Data Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTableSelect = (tableName: string) => {
    setSelectedTable(tableName);
    loadTableData(tableName);
  };

  const renderTableData = () => {
    if (!tableData || !tableData.data.length) return null;

    // Spalten aus dem ersten Datensatz ermitteln
    const columns = Object.keys(tableData.data[0]);

    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              {availableTables[selectedTable as keyof typeof availableTables]}
            </h3>
            <span className="text-sm text-gray-500">
              {tableData.count} Einträge
            </span>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {columns.map(column => (
                  <th
                    key={column}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {tableData.data.map((row, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  {columns.map(column => (
                    <td
                      key={column}
                      className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                    >
                      {typeof row[column] === 'object' && row[column] !== null
                        ? JSON.stringify(row[column])
                        : String(row[column] || '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center">
            <Database className="mr-2" />
            Datenbankansicht
          </h1>
          <p className="text-gray-600">Überblick über alle PostgreSQL-Tabellen</p>
        </div>
        <button
          onClick={loadStats}
          disabled={loading}
          className="flex items-center px-4 py-2 bg-[#004f7c] text-white rounded-lg hover:bg-[#004f7c]/90 disabled:opacity-50"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Aktualisieren
        </button>
      </div>

      {/* Statistiken */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm text-blue-600">Dokumente</p>
                <p className="text-2xl font-bold text-blue-800">{stats.dokumente_count}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center">
              <Table className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm text-green-600">Externe Lieferscheine</p>
                <p className="text-2xl font-bold text-green-800">{stats.lieferscheine_extern_count}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center">
              <Table className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm text-purple-600">Chargen Einkauf</p>
                <p className="text-2xl font-bold text-purple-800">{stats.chargen_einkauf_count}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-yellow-50 rounded-lg p-4">
            <div className="flex items-center">
              <Table className="h-8 w-8 text-yellow-600" />
              <div className="ml-3">
                <p className="text-sm text-yellow-600">Kategorien</p>
                <p className="text-2xl font-bold text-yellow-800">{stats.kategorien_count}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabellen-Übersicht */}
      <div className="bg-white rounded-lg shadow">
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900 flex items-center">
            <Table className="mr-2" />
            Verfügbare Tabellen
          </h2>
        </div>
        <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(availableTables).map(([key, label]) => (
            <button
              key={key}
              onClick={() => handleTableSelect(key)}
              className={`p-4 rounded-lg border-2 transition-colors ${
                selectedTable === key
                  ? 'bg-[#004f7c]/10 border-[#004f7c]/20 text-[#004f7c]'
                  : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="font-medium">{label}</div>
              {stats && (
                <div className="text-sm text-gray-500 mt-1">
                  {stats[`${key}_count` as keyof DatabaseStats]} Einträge
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Fehleranzeige */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-800">{error}</div>
          <div className="text-sm text-red-600 mt-2">
            Prüfe ob das Backend auf Port 8081 läuft und die Database-Routes verfügbar sind.
          </div>
        </div>
      )}

      {/* Lade-Anzeige */}
      {loading && (
        <div className="flex justify-center p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#004f7c]"></div>
        </div>
      )}

      {/* Tabellendaten */}
      {renderTableData()}
    </div>
  );
};

export default DatabaseViewer;