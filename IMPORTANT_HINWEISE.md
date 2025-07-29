# WICHTIGE HINWEISE ZUR NUTZUNG

## 🔴 ID-Matching Problem

Das Tool wurde erfolgreich installiert und ausgeführt, aber es gibt ein wichtiges Problem:

**Die HubSpot Deal IDs stimmen NICHT mit den SalesCookie Unique IDs überein!**

- HubSpot verwendet IDs wie: `270402053362`, `258784439510`
- SalesCookie verwendet IDs wie: `20351301806`, `20351234678`

Dies führt dazu, dass **0 von 251 Deals** gematcht werden konnten.

## 📊 Aktuelle Ergebnisse

- **HubSpot**: 251 Closed & Won Deals gefunden (€8,698,792.54)
- **SalesCookie**: 183 Transaktionen gefunden (€291,283.22 Commission)
- **Matches**: 0 (wegen unterschiedlicher ID-Systeme)
- **Fehlende Deals**: 251 (alle!)

## 🛠️ Lösungsansätze

### Option 1: Name-basiertes Matching
Anpassen des Codes um Deals über den Deal-Namen statt über IDs zu matchen:
- Nur 2 Deals konnten über Namen gematcht werden
- Namen sind nicht eindeutig genug

### Option 2: Mapping-Tabelle
Erstellen einer Mapping-Tabelle zwischen HubSpot IDs und SalesCookie IDs:
- Manueller einmaliger Aufwand
- Danach automatisches Matching möglich

### Option 3: Gemeinsames Feld
Prüfen ob es ein gemeinsames Feld gibt (z.B. Company Name + Close Date):
- Könnte automatisiert werden
- Fehleranfälliger als direkte IDs

## 📁 Generierte Reports

Trotz des Matching-Problems wurden Reports generiert:

1. **Excel Report**: `reports/commission_reconciliation_20250729_232336.xlsx`
   - Summary Sheet mit Übersicht
   - Discrepancies Sheet mit allen 251 "fehlenden" Deals
   - Matched Deals Sheet (leer)

2. **Text Summary**: `reports/reconciliation_summary_20250729_232336.txt`
   - Schnellübersicht und Empfehlungen

3. **CSV Export**: `reports/discrepancies_20250729_232336.csv`
   - Alle Diskrepanzen für weitere Analyse

## 🚀 Nächste Schritte

1. **Klären Sie das ID-Mapping** zwischen HubSpot und SalesCookie
2. **Passen Sie den Code an** basierend auf dem gewählten Lösungsansatz
3. **Führen Sie das Tool erneut aus** nach der Anpassung

## 💡 Temporäre Lösung

Bis das ID-Problem gelöst ist, können Sie:
- Die Excel-Reports nutzen um manuell zu prüfen
- Die generierten Listen als Basis für manuelle Reconciliation verwenden
- Die Provisionsberechnungen in den Reports sind korrekt (basierend auf Ihren Commission Plans)