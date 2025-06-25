#!/usr/bin/env python3
"""
Debug-Script für CSV-Lieferscheinnummer-Matching
Analysiert warum '131/25' nicht gefunden wird
"""

import csv
import os
import sys
from pathlib import Path

# Projekt-Pfad hinzufügen
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

# Settings importieren
from backend.app.config.settings import CSV_LIST_DIR

def analyze_csv_for_lieferscheinnummer(target_nummer: str = "131/25"):
    """
    Detailanalyse der CSV-Dateien für eine bestimmte Lieferscheinnummer.
    """
    print(f"🔍 Analysiere CSV-Dateien für Lieferscheinnummer: '{target_nummer}'")
    print(f"📁 CSV-Verzeichnis: {CSV_LIST_DIR}")
    print("=" * 70)
    
    if not os.path.exists(CSV_LIST_DIR):
        print(f"❌ CSV-Verzeichnis nicht gefunden: {CSV_LIST_DIR}")
        return
    
    csv_files = [f for f in os.listdir(CSV_LIST_DIR) if f.lower().endswith('.csv')]
    
    if not csv_files:
        print("❌ Keine CSV-Dateien gefunden")
        return
    
    print(f"📄 Gefundene CSV-Dateien: {csv_files}")
    print()
    
    for csv_file in csv_files:
        csv_path = os.path.join(CSV_LIST_DIR, csv_file)
        print(f"🔎 Analysiere: {csv_file}")
        print("-" * 50)
        
        analyze_single_csv(csv_path, target_nummer)
        print()

def analyze_single_csv(csv_path: str, target_nummer: str):
    """Analysiert eine einzelne CSV-Datei."""
    
    # 1. Datei-Infos
    try:
        file_size = os.path.getsize(csv_path)
        print(f"📏 Dateigröße: {file_size:,} bytes")
    except Exception as e:
        print(f"❌ Fehler beim Lesen der Dateigröße: {e}")
        return
    
    # 2. Encoding-Detection
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    working_encoding = None
    
    for encoding in encodings_to_try:
        try:
            with open(csv_path, 'r', encoding=encoding, errors='ignore') as f:
                f.read(1024)  # Test-read
            working_encoding = encoding
            print(f"✅ Funktionierendes Encoding: {encoding}")
            break
        except Exception:
            continue
    
    if not working_encoding:
        print("❌ Kein funktionierendes Encoding gefunden")
        return
    
    # 3. Delimiter-Detection und Header-Analyse
    delimiters = [';', ',', '\t', '|']
    best_delimiter = None
    headers = []
    
    for delimiter in delimiters:
        try:
            with open(csv_path, 'r', encoding=working_encoding, errors='ignore') as f:
                reader = csv.reader(f, delimiter=delimiter)
                first_row = next(reader, [])
                
                if len(first_row) > 5:  # Mindestens 5 Spalten
                    best_delimiter = delimiter
                    headers = [h.strip() for h in first_row]
                    print(f"✅ Delimiter: '{delimiter}' ({len(headers)} Spalten)")
                    break
        except Exception:
            continue
    
    if not best_delimiter:
        print("❌ Kein funktionierender Delimiter gefunden")
        return
    
    # 4. Header-Analyse
    print(f"📋 Header ({len(headers)} Spalten):")
    lieferschein_columns = []
    
    for i, header in enumerate(headers):
        print(f"  {i:2d}: '{header}'")
        
        # Suche nach Lieferschein-relevanten Spalten
        if any(keyword in header.upper() for keyword in ['LIEFERSCHEIN', 'LIEFER', 'SCHEIN', 'LFN', 'LF']):
            lieferschein_columns.append((i, header))
            print(f"      ^-- 🎯 POTENTIELLE LIEFERSCHEIN-SPALTE!")
    
    print(f"\n🎯 Gefundene Lieferschein-Spalten: {len(lieferschein_columns)}")
    for idx, col_name in lieferschein_columns:
        print(f"   {idx}: '{col_name}'")
    
    # 5. Daten-Analyse für Ziel-Lieferscheinnummer
    print(f"\n🔍 Suche nach '{target_nummer}' in den Daten...")
    
    matches_found = []
    similar_found = []
    total_rows = 0
    
    try:
        with open(csv_path, 'r', encoding=working_encoding, errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=best_delimiter)
            
            for row_num, row in enumerate(reader, 1):
                total_rows += 1
                
                # Alle Spalten nach der Ziel-Nummer durchsuchen
                for col_name, cell_value in row.items():
                    if not cell_value:
                        continue
                    
                    cell_clean = str(cell_value).strip()
                    
                    # Exakter Match
                    if cell_clean == target_nummer:
                        matches_found.append({
                            'row': row_num,
                            'column': col_name,
                            'value': repr(cell_clean),
                            'raw_value': repr(cell_value)
                        })
                    
                    # Ähnliche Matches (enthält Ziel-Nummer)
                    elif target_nummer in cell_clean or cell_clean in target_nummer:
                        if len(similar_found) < 10:  # Nur erste 10 sammeln
                            similar_found.append({
                                'row': row_num,
                                'column': col_name,
                                'value': repr(cell_clean),
                                'raw_value': repr(cell_value)
                            })
    
    except Exception as e:
        print(f"❌ Fehler beim Durchsuchen der Daten: {e}")
        return
    
    print(f"📊 Insgesamt {total_rows} Datenzeilen durchsucht")
    
    # 6. Ergebnisse
    if matches_found:
        print(f"✅ EXAKTE MATCHES GEFUNDEN: {len(matches_found)}")
        for match in matches_found:
            print(f"   Zeile {match['row']}, Spalte '{match['column']}': {match['value']}")
            if match['value'] != match['raw_value']:
                print(f"   Raw: {match['raw_value']}")
    else:
        print(f"❌ KEINE EXAKTEN MATCHES für '{target_nummer}' gefunden")
    
    if similar_found:
        print(f"🔍 ÄHNLICHE MATCHES: {len(similar_found)}")
        for match in similar_found[:5]:  # Nur erste 5 anzeigen
            print(f"   Zeile {match['row']}, Spalte '{match['column']}': {match['value']}")
    
    # 7. Spezielle Analyse für LIEFERSCHEINNR-Spalte
    if any('LIEFERSCHEINNR' in col for _, col in lieferschein_columns):
        print(f"\n🎯 Spezial-Analyse für LIEFERSCHEINNR-Spalte:")
        analyze_lieferscheinnr_column(csv_path, working_encoding, best_delimiter, target_nummer)

def analyze_lieferscheinnr_column(csv_path: str, encoding: str, delimiter: str, target_nummer: str):
    """Spezielle Analyse der LIEFERSCHEINNR-Spalte."""
    
    unique_values = set()
    containing_target = []
    
    try:
        with open(csv_path, 'r', encoding=encoding, errors='ignore') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row_num, row in enumerate(reader, 1):
                lieferscheinnr = row.get('LIEFERSCHEINNR', '').strip()
                
                if lieferscheinnr:
                    unique_values.add(lieferscheinnr)
                    
                    # Sammle Werte die Ziel-Nummer enthalten
                    if target_nummer in lieferscheinnr:
                        containing_target.append((row_num, repr(lieferscheinnr)))
    
    except Exception as e:
        print(f"❌ Fehler bei LIEFERSCHEINNR-Analyse: {e}")
        return
    
    print(f"📈 Einzigartige LIEFERSCHEINNR-Werte: {len(unique_values)}")
    
    # Zeige ein paar Beispiele
    sample_values = list(unique_values)[:10]
    print(f"📋 Beispiel-Werte:")
    for val in sample_values:
        print(f"   '{val}'")
    
    if containing_target:
        print(f"\n🎯 Werte die '{target_nummer}' enthalten:")
        for row_num, value in containing_target:
            print(f"   Zeile {row_num}: {value}")
    
    # Suche nach ähnlichen Pattern
    patterns = []
    for val in unique_values:
        if '/' in val and len(val) <= 10:  # Pattern wie "131/25"
            patterns.append(val)
    
    if patterns:
        print(f"\n🔍 Ähnliche Patterns (mit '/'): {len(patterns)} gefunden")
        for pattern in sorted(patterns)[:10]:
            print(f"   '{pattern}'")

def main():
    """Hauptfunktion."""
    
    # Target-Nummer aus Log
    target = "131/25"
    
    if len(sys.argv) > 1:
        target = sys.argv[1]
    
    print(f"🚀 CSV Debug Script gestartet")
    print(f"🎯 Ziel-Lieferscheinnummer: '{target}'")
    print()
    
    analyze_csv_for_lieferscheinnummer(target)
    
    print("\n" + "=" * 70)
    print("✨ Analyse abgeschlossen!")
    print("\n💡 Tips:")
    print("- Prüfe ob die Spalte wirklich 'LIEFERSCHEINNR' heißt")
    print("- Achte auf unsichtbare Zeichen (BOM, Spaces)")
    print("- Prüfe Case-Sensitivity (131/25 vs 131/25)")
    print("- Möglicherweise ist das Format anders (00131/25, 131/2025, etc.)")

if __name__ == "__main__":
    main()