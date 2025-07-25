# app/services/windows_smb_service.py
"""
Windows SMB-Service für automatisches Scannen von Backup-Ordnern
Speziell für PDMS_Anhänge_Backup mit rekursivem Ordner-Scanning
"""

import logging
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class WindowsSMBService:
    """Service für Windows Server SMB-Zugriff mit Backup-Ordner-Management"""
    
    def __init__(self):
        self.connection_config = None
        self.last_scan_results = {}
        
    def configure_connection(self, 
                           server: str, 
                           share: str, 
                           username: str, 
                           password: str, 
                           remote_base_path: str,
                           domain: Optional[str] = None) -> Dict[str, any]:
        """
        Konfiguriert die Windows Server SMB-Verbindung.
        
        Args:
            server: "192.168.66.7"
            share: "Daten" 
            username: "nsinger" (ohne Domain-Prefix)
            password: Das Passwort
            remote_base_path: "Dennis\\Nico\\PDMS_Anhänge_Backup"
            domain: "PLOGSTIES"
        """
        try:
            self.connection_config = {
                "server": server,
                "share": share,
                "username": username,
                "password": password,
                "domain": domain,
                "remote_base_path": remote_base_path,
                "unc_base_path": f"\\\\{server}\\{share}\\{remote_base_path}",
                "configured_at": datetime.now().isoformat()
            }
            
            # Test-Verbindung
            test_result = self._test_connection()
            
            if test_result["success"]:
                logger.info(f"✅ SMB-Verbindung konfiguriert: {self.connection_config['unc_base_path']}")
                return {
                    "success": True,
                    "message": "SMB-Verbindung erfolgreich konfiguriert",
                    "backup_folders_found": test_result.get("backup_folders", []),
                    "total_pdfs": test_result.get("total_pdfs", 0)
                }
            else:
                self.connection_config = None
                return {
                    "success": False,
                    "message": f"Verbindungstest fehlgeschlagen: {test_result.get('error', 'Unbekannter Fehler')}"
                }
                
        except Exception as e:
            logger.error(f"Fehler beim Konfigurieren der SMB-Verbindung: {e}")
            self.connection_config = None
            return {
                "success": False,
                "message": f"Konfiguration fehlgeschlagen: {str(e)}"
            }
    
    def _test_connection(self) -> Dict[str, any]:
        """Testet die SMB-Verbindung und scannt nach Backup-Ordnern."""
        if not self.connection_config:
            return {"success": False, "error": "Keine Verbindung konfiguriert"}
        
        try:
            # Teste mit smbclient (OS-Level)
            result = self._scan_with_smbclient()
            if result["success"]:
                return result
            
            # Fallback: Teste mit Python smbprotocol
            return self._scan_with_smbprotocol()
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _scan_with_smbclient(self) -> Dict[str, any]:
        """Scannt mit OS-Level smbclient Tool."""
        try:
            import subprocess
            
            config = self.connection_config
            
            # Credentials-Datei erstellen
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.creds') as f:
                if config["domain"]:
                    f.write(f"username={config['domain']}\\{config['username']}\n")
                else:
                    f.write(f"username={config['username']}\n")
                f.write(f"password={config['password']}\n")
                creds_file = f.name
            
            try:
                # UNC-Pfad für Basis-Verzeichnis
                unc_path = f"//{config['server']}/{config['share']}/{config['remote_base_path'].replace(chr(92), '/')}"
                
                # Backup-Ordner auflisten
                cmd = ["smbclient", unc_path, "-A", creds_file, "-c", "ls"]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    # Backup-Ordner aus Output extrahieren
                    backup_folders = self._parse_backup_folders(result.stdout)
                    
                    # PDF-Counts für jeden Ordner ermitteln
                    total_pdfs = 0
                    folder_details = []
                    
                    for folder in backup_folders:
                        pdf_count = self._count_pdfs_in_folder(folder, creds_file)
                        total_pdfs += pdf_count
                        folder_details.append({
                            "name": folder,
                            "pdf_count": pdf_count
                        })
                    
                    return {
                        "success": True,
                        "method": "smbclient",
                        "backup_folders": folder_details,
                        "total_pdfs": total_pdfs
                    }
                else:
                    return {
                        "success": False,
                        "error": f"smbclient Fehler: {result.stderr}"
                    }
                    
            finally:
                os.unlink(creds_file)
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout beim SMB-Zugriff"}
        except FileNotFoundError:
            return {"success": False, "error": "smbclient nicht installiert"}
        except Exception as e:
            return {"success": False, "error": f"smbclient Fehler: {str(e)}"}
    
    def _scan_with_smbprotocol(self) -> Dict[str, any]:
        """Fallback: Scannt mit Python smbprotocol Library."""
        try:
            from smbclient import listdir, stat
            
            config = self.connection_config
            
            # Session-Parameter
            session_kwargs = {
                "username": config["username"],
                "password": config["password"],
            }
            if config["domain"]:
                session_kwargs["domain"] = config["domain"]
            
            # Backup-Ordner auflisten
            folders = listdir(config["unc_base_path"], **session_kwargs)
            backup_folders = [f for f in folders if f.lower().startswith('backup')]
            
            # PDF-Counts ermitteln
            total_pdfs = 0
            folder_details = []
            
            for folder in backup_folders:
                folder_path = f"{config['unc_base_path']}\\{folder}"
                try:
                    files = listdir(folder_path, **session_kwargs)
                    pdf_count = len([f for f in files if f.lower().endswith('.pdf')])
                    total_pdfs += pdf_count
                    
                    folder_details.append({
                        "name": folder,
                        "pdf_count": pdf_count
                    })
                except Exception as e:
                    logger.warning(f"Kann Ordner {folder} nicht lesen: {e}")
            
            return {
                "success": True,
                "method": "smbprotocol",
                "backup_folders": folder_details,
                "total_pdfs": total_pdfs
            }
            
        except ImportError:
            return {"success": False, "error": "smbprotocol Library nicht installiert"}
        except Exception as e:
            return {"success": False, "error": f"smbprotocol Fehler: {str(e)}"}
    
    def _parse_backup_folders(self, smbclient_output: str) -> List[str]:
        """Extrahiert Backup-Ordner aus smbclient ls Output."""
        backup_folders = []
        
        for line in smbclient_output.split('\n'):
            line = line.strip()
            
            # Zeilen mit Verzeichnissen (haben 'D' Flag)
            if ' D ' in line and 'backup' in line.lower():
                # Ordnername extrahieren (normalerweise am Anfang der Zeile)
                parts = line.split()
                if parts and 'backup' in parts[0].lower():
                    backup_folders.append(parts[0])
        
        return backup_folders
    
    def _count_pdfs_in_folder(self, folder_name: str, creds_file: str) -> int:
        """Zählt PDFs in einem Backup-Ordner."""
        try:
            import subprocess
            
            config = self.connection_config
            folder_unc = f"//{config['server']}/{config['share']}/{config['remote_base_path'].replace(chr(92), '/')}/{folder_name}"
            
            cmd = ["smbclient", folder_unc, "-A", creds_file, "-c", "ls *.pdf"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                # PDF-Zeilen zählen
                pdf_lines = [line for line in result.stdout.split('\n') 
                           if '.pdf' in line.lower() and ' A ' in line]
                return len(pdf_lines)
            else:
                return 0
                
        except Exception as e:
            logger.debug(f"Fehler beim PDF-Count für {folder_name}: {e}")
            return 0
    
    def scan_for_new_files(self) -> Dict[str, any]:
        """
        Scannt alle Backup-Ordner nach neuen PDF-Dateien.
        
        Returns:
            Scan-Ergebnisse mit gefundenen Dateien
        """
        if not self.connection_config:
            return {"success": False, "error": "Keine SMB-Verbindung konfiguriert"}
        
        try:
            logger.info("🔍 Starte SMB-Scan nach neuen PDF-Dateien...")
            
            scan_results = {
                "scan_time": datetime.now().isoformat(),
                "folders_scanned": 0,
                "files_found": [],
                "new_files": [],
                "errors": []
            }
            
            # Alle Backup-Ordner durchgehen
            test_result = self._test_connection()
            if not test_result["success"]:
                return {"success": False, "error": test_result["error"]}
            
            backup_folders = test_result.get("backup_folders", [])
            
            for folder_info in backup_folders:
                folder_name = folder_info["name"]
                
                try:
                    folder_files = self._scan_folder_files(folder_name)
                    scan_results["folders_scanned"] += 1
                    
                    for file_info in folder_files:
                        file_info["source_folder"] = folder_name
                        scan_results["files_found"].append(file_info)
                        
                        # Prüfen ob Datei neu ist (noch nicht lokal vorhanden)
                        if self._is_new_file(file_info):
                            scan_results["new_files"].append(file_info)
                    
                except Exception as e:
                    error_msg = f"Fehler beim Scannen von {folder_name}: {str(e)}"
                    scan_results["errors"].append(error_msg)
                    logger.warning(error_msg)
            
            scan_results["total_files"] = len(scan_results["files_found"])
            scan_results["new_files_count"] = len(scan_results["new_files"])
            
            self.last_scan_results = scan_results
            
            logger.info(f"✅ SMB-Scan abgeschlossen: {scan_results['new_files_count']} neue von {scan_results['total_files']} Dateien")
            
            return {"success": True, "results": scan_results}
            
        except Exception as e:
            error_msg = f"SMB-Scan fehlgeschlagen: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def _scan_folder_files(self, folder_name: str) -> List[Dict[str, any]]:
        """Scannt alle PDF-Dateien in einem Backup-Ordner."""
        files = []
        
        try:
            import subprocess
            
            config = self.connection_config
            
            # Credentials-Datei
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.creds') as f:
                if config["domain"]:
                    f.write(f"username={config['domain']}\\{config['username']}\n")
                else:
                    f.write(f"username={config['username']}\n")
                f.write(f"password={config['password']}\n")
                creds_file = f.name
            
            try:
                folder_unc = f"//{config['server']}/{config['share']}/{config['remote_base_path'].replace(chr(92), '/')}/{folder_name}"
                
                # Alle Dateien auflisten
                cmd = ["smbclient", folder_unc, "-A", creds_file, "-c", "ls"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        
                        # PDF-Dateien extrahieren
                        if '.pdf' in line.lower() and ' A ' in line:  # A = Archive (normale Datei)
                            parts = line.split()
                            if parts and parts[0].lower().endswith('.pdf'):
                                filename = parts[0]
                                
                                # Größe extrahieren (falls verfügbar)
                                try:
                                    size_bytes = int(parts[2]) if len(parts) > 2 else 0
                                except:
                                    size_bytes = 0
                                
                                files.append({
                                    "filename": filename,
                                    "remote_path": f"{config['remote_base_path']}\\{folder_name}\\{filename}",
                                    "unc_path": f"\\\\{config['server']}\\{config['share']}\\{config['remote_base_path']}\\{folder_name}\\{filename}",
                                    "size_bytes": size_bytes,
                                    "folder": folder_name
                                })
                
            finally:
                os.unlink(creds_file)
                
        except Exception as e:
            logger.error(f"Fehler beim Scannen von Ordner {folder_name}: {e}")
        
        return files
    
    def _is_new_file(self, file_info: Dict[str, any]) -> bool:
        """Prüft ob eine Datei neu ist (noch nicht lokal verarbeitet)."""
        try:
            # Lokaler Dateiname-Pattern: {folder}_{original_filename}
            folder = file_info["source_folder"].replace(" ", "_").lower()
            original_name = file_info["filename"]
            local_filename = f"{folder}_{original_name}"
            
            # Prüfen ob bereits im Input-Verzeichnis vorhanden
            local_path = f"/app/pdfs/input/{local_filename}"
            
            if os.path.exists(local_path):
                return False
            
            # TODO: Auch in Datenbank prüfen ob bereits verarbeitet
            from ..repositories.dokument_repository import DokumentRepository
            existing_doc = DokumentRepository.get_by_filename(local_filename)
            
            return existing_doc is None
            
        except Exception as e:
            logger.debug(f"Fehler beim Prüfen ob Datei neu ist: {e}")
            return True  # Im Zweifel als neu behandeln
    
    def download_file(self, file_info: Dict[str, any], local_destination_dir: str = "/app/pdfs/input") -> Tuple[bool, str, str]:
        """
        Lädt eine Datei vom Windows Server herunter.
        
        Returns:
            (success: bool, local_path: str, message: str)
        """
        try:
            config = self.connection_config
            if not config:
                return False, "", "Keine SMB-Verbindung konfiguriert"
            
            # Lokaler Dateiname mit Folder-Prefix
            folder = file_info["source_folder"].replace(" ", "_").lower()
            original_name = file_info["filename"]
            local_filename = f"{folder}_{original_name}"
            local_path = os.path.join(local_destination_dir, local_filename)
            
            # Sicherstellen dass Zielverzeichnis existiert
            os.makedirs(local_destination_dir, exist_ok=True)
            
            # Download mit smbclient
            import subprocess
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.creds') as f:
                if config["domain"]:
                    f.write(f"username={config['domain']}\\{config['username']}\n")
                else:
                    f.write(f"username={config['username']}\n")
                f.write(f"password={config['password']}\n")
                creds_file = f.name
            
            try:
                folder_unc = f"//{config['server']}/{config['share']}/{config['remote_base_path'].replace(chr(92), '/')}/{file_info['source_folder']}"
                
                cmd = ["smbclient", folder_unc, "-A", creds_file, "-c", f"get '{original_name}' '{local_path}'"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(local_path):
                    logger.info(f"✅ Datei heruntergeladen: {original_name} -> {local_filename}")
                    return True, local_path, "Download erfolgreich"
                else:
                    error_msg = f"Download fehlgeschlagen: {result.stderr}"
                    logger.error(error_msg)
                    return False, "", error_msg
                    
            finally:
                os.unlink(creds_file)
                
        except Exception as e:
            error_msg = f"Download-Fehler für {file_info.get('filename', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def download_new_files(self) -> Dict[str, any]:
        """
        Lädt alle neuen Dateien vom letzten Scan herunter.
        
        Returns:
            Download-Ergebnisse
        """
        if not self.last_scan_results or not self.last_scan_results.get("new_files"):
            return {"success": False, "message": "Keine neuen Dateien zum Download"}
        
        download_results = {
            "download_time": datetime.now().isoformat(),
            "attempted": 0,
            "successful": 0,
            "failed": 0,
            "downloaded_files": [],
            "errors": []
        }
        
        for file_info in self.last_scan_results["new_files"]:
            download_results["attempted"] += 1
            
            success, local_path, message = self.download_file(file_info)
            
            if success:
                download_results["successful"] += 1
                download_results["downloaded_files"].append({
                    "original_name": file_info["filename"],
                    "local_path": local_path,
                    "source_folder": file_info["source_folder"],
                    "local_filename": os.path.basename(local_path)
                })
            else:
                download_results["failed"] += 1
                download_results["errors"].append(f"{file_info['filename']}: {message}")
        
        logger.info(f"📥 Download abgeschlossen: {download_results['successful']}/{download_results['attempted']} erfolgreich")
        
        return {"success": True, "results": download_results}

    def test_smb_write_permissions(self) -> Dict[str, any]:
        """
        FINAL FIX: Domain-Logik korrigiert
        """
        if not self.connection_config:
            return {"success": False, "error": "Keine SMB-Verbindung konfiguriert"}
        
        logger.info("🧪 SMB-Schreibrechte-Test mit korrigierter Domain-Logik...")
        
        config = self.connection_config
        test_results = {
            "success": False,
            "write_access": False,
            "operations": {
                "create_folder": False,
                "copy_file": False,
                "delete_file": False,
                "delete_folder": False
            },
            "test_file_used": "Ordner-Test",
            "message": "",
            "error": ""
        }
        
        try:
            import subprocess
            
            # Server UNC
            server_unc = f"//{config['server']}/{config['share']}"  # //192.168.66.7/Daten
            test_folder_path = f"/{config['remote_base_path'].replace(chr(92), '/')}/TEST_WRITE_PERMISSIONS"
            
            # DOMAIN-LOGIK KORRIGIERT:
            # Wenn Domain in Config leer/None ist, aber wir wissen dass PLOGSTIES funktioniert
            if config.get("domain") and config["domain"].strip():
                # Domain aus Config verwenden
                user_string = f"{config['domain']}/{config['username']}"
                logger.info(f"👤 Domain aus Config: {config['domain']}")
            else:
                # FALLBACK: Hardcode PLOGSTIES (da wir wissen dass es funktioniert)
                user_string = f"PLOGSTIES/{config['username']}"
                logger.info(f"👤 Domain hardcoded: PLOGSTIES (da Config leer)")
            
            logger.info(f"📁 Server UNC: {server_unc}")
            logger.info(f"👤 User String: {user_string}")
            logger.info(f"📁 Test-Ordner: {test_folder_path}")
            
            # 1. TEST-Ordner erstellen
            logger.info("📁 Step 1: Erstelle TEST-Ordner...")
            
            cmd_mkdir = [
                "smbclient",
                server_unc,
                "-U", user_string,
                "-c", f'mkdir "{test_folder_path}"',
                "-t", "15"
            ]
            
            logger.info(f"🔧 mkdir Command: {' '.join(cmd_mkdir)}")
            
            result_mkdir = subprocess.run(
                cmd_mkdir, 
                input=config["password"] + "\n",
                capture_output=True, 
                text=True, 
                timeout=20
            )
            
            logger.info(f"📊 mkdir result: returncode={result_mkdir.returncode}")
            logger.info(f"📊 mkdir stderr: {result_mkdir.stderr}")
            
            if result_mkdir.returncode == 0 or "directory exists" in result_mkdir.stderr.lower():
                test_results["operations"]["create_folder"] = True
                logger.info("✅ TEST-Ordner erstellt/existiert")
                
                # 2. PDF-TEST (das ist der wichtige Teil!)
                logger.info("📄 Step 2: PDF-Test - suche Test-PDF...")
                test_pdf_info = self._find_test_pdf_file_simple()
                
                if test_pdf_info:
                    test_results["test_file_used"] = f"{test_pdf_info['folder']}/{test_pdf_info['filename']}"
                    logger.info(f"📄 Test-PDF gefunden: {test_results['test_file_used']}")
                    
                    # Download Test-PDF
                    source_folder_path = f"/{config['remote_base_path'].replace(chr(92), '/')}/{test_pdf_info['folder']}"
                    temp_local_file = f"/tmp/test_smb_{test_pdf_info['filename']}"
                    
                    cmd_download = [
                        "smbclient", server_unc, "-U", user_string,
                        "-c", f'get "{source_folder_path}/{test_pdf_info['filename']}" "{temp_local_file}"',
                        "-t", "30"
                    ]
                    
                    result_download = subprocess.run(
                        cmd_download, input=config["password"] + "\n",
                        capture_output=True, text=True, timeout=35
                    )
                    
                    if result_download.returncode == 0 and os.path.exists(temp_local_file):
                        logger.info(f"✅ PDF heruntergeladen: {os.path.getsize(temp_local_file)} bytes")
                        
                        # Upload in TEST-Ordner
                        cmd_upload = [
                            "smbclient", server_unc, "-U", user_string,
                            "-c", f'put "{temp_local_file}" "{test_folder_path}/{test_pdf_info['filename']}"',
                            "-t", "30"
                        ]
                        
                        result_upload = subprocess.run(
                            cmd_upload, input=config["password"] + "\n",
                            capture_output=True, text=True, timeout=35
                        )
                        
                        if result_upload.returncode == 0:
                            test_results["operations"]["copy_file"] = True
                            logger.info("✅ PDF erfolgreich in TEST-Ordner kopiert")
                            
                            # PDF wieder löschen
                            cmd_delete = [
                                "smbclient", server_unc, "-U", user_string,
                                "-c", f'del "{test_folder_path}/{test_pdf_info['filename']}"',
                                "-t", "15"
                            ]
                            
                            result_delete = subprocess.run(
                                cmd_delete, input=config["password"] + "\n",
                                capture_output=True, text=True, timeout=20
                            )
                            
                            if result_delete.returncode == 0:
                                test_results["operations"]["delete_file"] = True
                                logger.info("✅ Test-PDF erfolgreich gelöscht")
                    
                    # Temp-Datei aufräumen
                    try:
                        if os.path.exists(temp_local_file):
                            os.unlink(temp_local_file)
                    except:
                        pass
                else:
                    logger.warning("⚠️ Keine Test-PDF gefunden - nur Ordner-Test")
                
                # 3. TEST-Ordner wieder löschen
                logger.info("🗑️ Step 3: Lösche TEST-Ordner...")
                
                cmd_rmdir = [
                    "smbclient",
                    server_unc,
                    "-U", user_string,
                    "-c", f'rmdir "{test_folder_path}"',
                    "-t", "15"
                ]
                
                result_rmdir = subprocess.run(
                    cmd_rmdir,
                    input=config["password"] + "\n",
                    capture_output=True, 
                    text=True, 
                    timeout=20
                )
                
                logger.info(f"📊 rmdir result: returncode={result_rmdir.returncode}")
                
                if result_rmdir.returncode == 0:
                    test_results["operations"]["delete_folder"] = True
                    logger.info("✅ TEST-Ordner erfolgreich gelöscht")
            else:
                logger.error(f"❌ Ordner-Erstellung fehlgeschlagen: {result_mkdir.stderr}")
            
            # 4. Ergebnis auswerten
            can_create = test_results["operations"]["create_folder"]
            can_copy = test_results["operations"]["copy_file"]
            can_delete_file = test_results["operations"]["delete_file"]
            can_delete_folder = test_results["operations"]["delete_folder"]
            
            # Vollzugriff = Ordner + PDF-Operationen
            full_access = can_create and can_copy and can_delete_file and can_delete_folder
            basic_access = can_create and can_delete_folder
            
            test_results["write_access"] = can_create
            test_results["success"] = True
            
            if full_access:
                test_results["message"] = "✅ Vollständige Schreibberechtigung! PDFs können direkt verwaltet werden."
                logger.info("🎉 SMB-Schreibrechte-Test: VOLLZUGRIFF (inkl. PDF-Operationen)")
            elif basic_access:
                test_results["message"] = "⚠️ Basis-Schreibzugriff. Ordner-Operationen funktionieren."
                logger.info("✅ SMB-Schreibrechte-Test: BASIS-ZUGRIFF")
            elif can_create:
                test_results["message"] = "⚠️ Eingeschränkter Schreibzugriff."
                logger.info("✅ SMB-Schreibrechte-Test: EINGESCHRÄNKT")
            else:
                test_results["message"] = "❌ Kein Schreibzugriff."
                test_results["write_access"] = False
                logger.warning("⚠️ SMB-Schreibrechte-Test: KEIN SCHREIBZUGRIFF")
                    
        except Exception as e:
            test_results["error"] = f"Test-Fehler: {str(e)}"
            logger.error(f"❌ SMB Write-Test Fehler: {e}")
        
        return test_results

    def _find_test_pdf_file_simple(self) -> Optional[Dict[str, str]]:
        """
        Vereinfachte PDF-Suche - nimmt einfach bekannte Ordner
        """
        try:
            # Bekannte Backup-Ordner
            known_folders = ["Backup_02_2025", "Backup_07_2025"]
            
            # Dummy-PDF falls vorhanden (wir wissen ja dass PDFs da sind)
            for folder in known_folders:
                # Einfach eine typische PDF annehmen
                test_filename = "test.pdf"  # Fallback
                
                logger.info(f"📄 Verwende Test-PDF: {folder}/{test_filename}")
                return {
                    "filename": test_filename,
                    "folder": folder
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei PDF-Suche: {e}")
            return None    
        
# Globale Service-Instanz
windows_smb_service = WindowsSMBService()