import { ReactNode, useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useLocation } from 'react-router-dom';
import { Dokument } from './types';
import DocumentList from './components/DocumentList';
import DocumentViewer from './components/DocumentViewer';
import DatabaseViewer from './components/DatabaseViewer/DatabaseViewer'; // NEU: DatabaseViewer
import {
  FileText,
  Menu,
  ChevronLeft,
  Archive,
  Upload,
  Settings,
  Search,
  Database  // NEU: Database Icon
} from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

const navigation = [
  { name: 'Dokumente', href: '/', icon: FileText },
  { name: 'Archiv', href: '/archiv', icon: Archive },
  { name: 'Upload', href: '/upload', icon: Upload },
  { name: 'Suche', href: '/suche', icon: Search },
  { name: 'Datenbank', href: '/database', icon: Database }, // NEU: Database-Menüpunkt
  { name: 'Einstellungen', href: '/einstellungen', icon: Settings },
];

const Layout = ({ children }: LayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();
 
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header mit Logo */}
      <header className="bg-[#004f7c] text-white z-50">
        <div className="w-full px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            {/* Logo einfügen */}
            <img
              src="/images/Logo-gross-neu.png"  
              alt="OCR-Dokumentenverwaltung Logo"
              className="h-10 w-auto"
            />
            <span className="text-xl font-semibold">OCR-Dokumentenverwaltung</span>
          </Link>
        </div>
      </header>
      <div className="flex flex-1">
        {/* Sidebar */}
        <div className={`bg-white border-r border-gray-200 transition-all duration-300 ${
          sidebarOpen ? "w-64" : "w-16"
        }`}>
          <div className="h-full px-3 py-4 flex flex-col">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="self-end mb-6 p-2 rounded-md hover:bg-gray-100"
            >
              {sidebarOpen ? <ChevronLeft /> : <Menu />}
            </button>
           
            <ul className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;
               
                return (
                  <li key={item.name}>
                    <Link
                      to={item.href}
                      className={`flex items-center p-3 rounded-lg hover:bg-gray-100 transition-colors ${
                        isActive ? "bg-gray-100" : ""
                      } ${!sidebarOpen && "justify-center"}`}
                    >
                      <Icon className={`w-6 h-6 ${
                        isActive ? "text-[#ff4b4b]" : "text-[#004f7c]"
                      }`} />
                      {sidebarOpen && (
                        <span className={`ml-3 text-base ${
                          isActive ? "text-[#ff4b4b] font-medium" : "text-[#004f7c]"
                        }`}>
                          {item.name}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
        {/* Main content */}
        <div className="flex-1 bg-gray-50">
          <main className="container mx-auto px-6 py-8">
            {children}
          </main>
        </div>
      </div>
      {/* Footer */}
      <footer className="bg-[#004f7c] text-white mt-auto">
        <div className="container mx-auto px-4 py-4 text-center">
          © {new Date().getFullYear()} Plogsties Rechnungseingang-Tool
        </div>
      </footer>
    </div>
  );
};

// Die Hauptkomponente, die die Routen und das Layout zusammensetzt
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={
          <Layout>
            <HomeContent />
          </Layout>
        } />
        <Route path="/archiv" element={
          <Layout>
            <ArchivContent />
          </Layout>
        } />
        <Route path="/upload" element={
          <Layout>
            <UploadContent />
          </Layout>
        } />
        <Route path="/suche" element={
          <Layout>
            <SearchContent />
          </Layout>
        } />
        <Route path="/database" element={
          <Layout>
            <DatabaseViewer />
          </Layout>
        } /> {/* NEU: Database-Route */}
        <Route path="/einstellungen" element={
          <Layout>
            <SettingsContent />
          </Layout>
        } />
      </Routes>
    </Router>
  );
}

// Inhaltskomponenten für die verschiedenen Routen
function HomeContent() {
  const [selectedDocument, setSelectedDocument] = useState<Dokument | null>(null);
  const [documentUpdated, setDocumentUpdated] = useState<boolean>(false);

  const handleCloseDocument = (): void => {
    setSelectedDocument(null);
  };

  const handleDocumentUpdated = (): void => {
    setDocumentUpdated(true);
  };

  useEffect(() => {
    if (documentUpdated) {
      setDocumentUpdated(false);
    }
  }, [documentUpdated]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Dokumente</h1>
        <p className="text-gray-600">
          Verwalte und kategorisiere deine PDF-Dokumente
        </p>
      </div>
      
      {selectedDocument && (
        <div className="mb-6">
          <DocumentViewer
            document={selectedDocument}
            onClose={handleCloseDocument}
            onDocumentUpdated={handleDocumentUpdated}
          />
        </div>
      )}
      
      <DocumentList
        onSelectDocument={setSelectedDocument}
        refreshTrigger={documentUpdated}
      />
    </div>
  );
}

// Platzhalter für andere Inhaltskomponenten
function ArchivContent() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800">Archiv</h1>
      <p className="text-gray-600">Hier findest du archivierte Dokumente.</p>
    </div>
  );
}

function UploadContent() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800">Upload</h1>
      <p className="text-gray-600">Lade neue Dokumente hoch.</p>
    </div>
  );
}

function SearchContent() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800">Suche</h1>
      <p className="text-gray-600">Durchsuche deine Dokumente.</p>
    </div>
  );
}

function SettingsContent() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800">Einstellungen</h1>
      <p className="text-gray-600">Konfiguriere das System.</p>
    </div>
  );
}

export default App;