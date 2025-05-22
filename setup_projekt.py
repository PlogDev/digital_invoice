#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skript zum Anlegen der Projektstruktur für das OCR-Dokumentenverwaltungssystem.
Erstellt die Ordnerstruktur und leere Dateien für Backend und Frontend.
"""

import os
import platform
import subprocess


def create_directory(path):
    """Erstellt ein Verzeichnis, falls es nicht existiert."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Verzeichnis erstellt: {path}")
    else:
        print(f"Verzeichnis existiert bereits: {path}")

def create_file(path):
    """Erstellt eine leere Datei, falls sie nicht existiert."""
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            pass
        print(f"Datei erstellt: {path}")
    else:
        print(f"Datei existiert bereits: {path}")

def setup_backend():
    """Backend-Struktur erstellen."""
    # Hauptverzeichnisse
    create_directory("backend")
    create_directory("backend/app")
    create_directory("backend/tests")
    
    # App-Unterverzeichnisse
    subdirs = [
        "config", "database", "models", 
        "routes", "schemas", "services", "utils"
    ]
    
    for subdir in subdirs:
        create_directory(f"backend/app/{subdir}")
        create_file(f"backend/app/{subdir}/__init__.py")
    
    # PDF-Verzeichnisse
    create_directory("backend/pdfs/input")
    create_directory("backend/pdfs/processed/berta")
    create_directory("backend/pdfs/processed/kosten")
    create_directory("backend/pdfs/processed/irrlaeufer")
    
    # Hauptdateien
    create_file("backend/app/__init__.py")
    create_file("backend/app/main.py")
    create_file("backend/app/config/settings.py")
    create_file("backend/app/database/connection.py")
    create_file("backend/app/models/dokument.py")
    create_file("backend/app/routes/dokumente.py")
    create_file("backend/app/schemas/dokument.py")
    create_file("backend/app/services/ocr_service.py")
    create_file("backend/app/services/storage_service.py")
    create_file("backend/app/utils/helpers.py")
    
    # Projektdateien
    create_file("backend/.gitignore")
    create_file("backend/requirements.txt")
    create_file("backend/README.md")
    
    print("Backend-Struktur erfolgreich erstellt.")

def setup_frontend():
    """Frontend-Struktur erstellen."""
    # Hauptverzeichnisse
    create_directory("frontend")
    create_directory("frontend/public")
    create_directory("frontend/src")
    
    # src-Unterverzeichnisse
    create_directory("frontend/src/assets")
    create_directory("frontend/src/components")
    create_directory("frontend/src/hooks")
    create_directory("frontend/src/pages")
    create_directory("frontend/src/services")
    create_directory("frontend/src/utils")
    
    # Komponenten-Unterverzeichnisse
    create_directory("frontend/src/components/DocumentList")
    create_directory("frontend/src/components/DocumentViewer")
    create_directory("frontend/src/components/MetadataForm")
    
    # Hauptdateien
    create_file("frontend/src/App.jsx")
    create_file("frontend/src/main.jsx")
    create_file("frontend/src/services/api.js")
    
    # Projektdateien
    create_file("frontend/.gitignore")
    create_file("frontend/package.json")
    create_file("frontend/README.md")
    
    print("Frontend-Struktur erfolgreich erstellt.")

def create_readme():
    """README.md für das Hauptverzeichnis erstellen."""
    readme_content = """# OCR-Dokumentenverwaltungssystem

Ein System zur OCR-basierten Erfassung und Kategorisierung von PDF-Dokumenten.

## Projektstruktur

- `backend/`: Python/FastAPI-Backend mit OCR-Funktionalität
- `frontend/`: React/Tailwind-Frontend

## Erste Schritte

### Backend

1. Wechseln Sie ins Backend-Verzeichnis: `cd backend`
2. Installieren Sie die Abhängigkeiten: `pip install -r requirements.txt`
3. Starten Sie den Server: `python -m app.main`

### Frontend

1. Wechseln Sie ins Frontend-Verzeichnis: `cd frontend`
2. Installieren Sie die Abhängigkeiten: `npm install`
3. Starten Sie die Entwicklungsumgebung: `npm run dev`
"""
    
    with open("README.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("README.md erstellt")

def create_requirements():
    """Requirements.txt für das Backend erstellen."""
    requirements = """fastapi>=0.68.0
uvicorn>=0.15.0
python-multipart>=0.0.5
pytesseract>=0.3.8
pdf2image>=1.16.0
Pillow>=8.3.1
pydantic>=1.8.2
python-dotenv>=0.19.0
"""
    
    with open("backend/requirements.txt", 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    print("requirements.txt erstellt")

def create_package_json():
    """Package.json für das Frontend erstellen."""
    package_json = """{
  "name": "dokument-ocr-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.3.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-pdf": "^6.2.2",
    "react-router-dom": "^6.8.2"
  },
  "devDependencies": {
    "@types/react": "^18.0.27",
    "@types/react-dom": "^18.0.10",
    "@vitejs/plugin-react": "^3.1.0",
    "autoprefixer": "^10.4.13",
    "postcss": "^8.4.21",
    "tailwindcss": "^3.2.7",
    "vite": "^4.1.0"
  }
}
"""
    
    with open("frontend/package.json", 'w', encoding='utf-8') as f:
        f.write(package_json)
    
    print("package.json erstellt")

def create_gitignore():
    """Gitignore-Dateien erstellen."""
    backend_gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtuelle Umgebung
venv/
ENV/

# SQLite Datenbank
*.db
*.sqlite3

# PDF-Dateien
pdfs/input/*
pdfs/processed/*
!pdfs/input/.gitkeep
!pdfs/processed/.gitkeep
!pdfs/processed/berta/.gitkeep
!pdfs/processed/kosten/.gitkeep
!pdfs/processed/irrlaeufer/.gitkeep

# IDE
.idea/
.vscode/
*.swp
*.swo
"""
    
    frontend_gitignore = """# Abhängigkeiten
/node_modules
/.pnp
.pnp.js

# Testing
/coverage

# Produktion
/build
/dist

# Verschiedenes
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

npm-debug.log*
yarn-debug.log*
yarn-error.log*
"""
    
    with open("backend/.gitignore", 'w', encoding='utf-8') as f:
        f.write(backend_gitignore)
    
    with open("frontend/.gitignore", 'w', encoding='utf-8') as f:
        f.write(frontend_gitignore)
    
    print("Gitignore-Dateien erstellt")

def create_gitkeep_files():
    """Erstellt .gitkeep-Dateien in leeren Verzeichnissen."""
    paths = [
        "backend/pdfs/input",
        "backend/pdfs/processed/berta",
        "backend/pdfs/processed/kosten",
        "backend/pdfs/processed/irrlaeufer"
    ]
    
    for path in paths:
        create_file(f"{path}/.gitkeep")
    
    print(".gitkeep-Dateien erstellt")

def setup_react_project():
    """React-Projekt mit Vite initialisieren."""
    try:
        # Prüfen, ob npm installiert ist
        subprocess.run(["npm", "--version"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE,
                      check=True)
        
        print("Möchtest du das React-Projekt mit Vite initialisieren? (j/n)")
        choice = input().lower()
        
        if choice == 'j':
            print("React-Projekt wird initialisiert (das kann einen Moment dauern)...")
            
            # Wechsle ins Frontend-Verzeichnis
            current_dir = os.getcwd()
            os.chdir("frontend")
            
            # Initialisiere React-Projekt mit Vite
            subprocess.run(["npm", "create", "vite@latest", ".", "--", "--template", "react"], check=True)
            
            # Installiere Tailwind CSS
            subprocess.run(["npm", "install", "-D", "tailwindcss", "postcss", "autoprefixer"], check=True)
            subprocess.run(["npx", "tailwindcss", "init", "-p"], check=True)
            
            # Installiere weitere Abhängigkeiten
            subprocess.run(["npm", "install", "axios", "react-router-dom", "react-pdf"], check=True)
            
            # Zurück zum ursprünglichen Verzeichnis
            os.chdir(current_dir)
            
            print("React-Projekt erfolgreich initialisiert!")
        else:
            print("React-Projekt wurde nicht initialisiert. Du kannst es später manuell einrichten.")
    
    except subprocess.CalledProcessError:
        print("HINWEIS: npm ist nicht installiert oder nicht im PATH. React-Projekt muss manuell initialisiert werden.")
    except Exception as e:
        print(f"Fehler beim Initialisieren des React-Projekts: {str(e)}")

def main():
    """Hauptfunktion zum Ausführen des Skripts."""
    print("OCR-Dokumentenverwaltungssystem - Projektstruktur-Setup")
    print("=" * 60)
    
    # Verwende aktuelles Verzeichnis als Projektwurzel
    print(f"Verwende aktuelles Verzeichnis als Projektwurzel: {os.path.abspath('.')}")
    
    # Backend und Frontend einrichten
    setup_backend()
    setup_frontend()
    
    # Zusätzliche Dateien erstellen
    create_readme()
    create_requirements()
    create_package_json()
    create_gitignore()
    create_gitkeep_files()
    
    # React-Projekt einrichten
    setup_react_project()
    
    print("\nProjektstruktur wurde erfolgreich erstellt!")
    print(f"Speicherort: {os.path.abspath('.')}")

if __name__ == "__main__":
    main()