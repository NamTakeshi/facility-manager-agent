# Facility Manager Agent – Claude Code Anleitung

## Projektkontext
KI-gestützter Assistent für private Vermieter.
Mieter können Fragen stellen oder Schäden melden.
Stack: Python, OpenAI Agents SDK, Reflex, SQLite.

## Team
Wir sind Python-Anfänger. Erkläre alles Schritt für Schritt.

## Code-Stil
- Kommentiere jeden nicht-offensichtlichen Schritt auf Deutsch
- Erkläre warum etwas so gemacht wird, nicht nur was es macht
- Halte Funktionen kurz und mit einem klaren Zweck
- Nutze sprechende Variablennamen auf Deutsch
- Docstrings für jede Funktion

## Beispiel für guten Kommentar-Stil
# Erst klassifizieren bevor wir die Vollständigkeit prüfen,
# weil die benötigten Infos je nach Kategorie unterschiedlich sind
kategorie = await klassifiziere_eingabe(nachricht)

## Projektstruktur
facility_manager_agent/
├── terminal_agenten.py  ← Gemeinsamer Agents-SDK-Workflow
└── facility_manager_agent.py  ← Reflex Web-App

terminal/
├── mieter.py    ← Terminal-Interface
├── vermieter.py ← Terminal-Dashboard
└── zeige_tickets.py

datenbank.py  ← Alle Datenbankfunktionen
dokumente/    ← PDFs (Mietverträge, Hausordnungen)

## Wichtige Konventionen
- Datenbankzugriff immer in datenbank.py – nie direkt in anderen Dateien
- Agenten-Logik immer in terminal_agenten.py
- UI-Logik immer in facility_manager_agent.py
- Neue Features zuerst im Terminal testen, dann in Reflex einbauen
- async/await für alle Agent-Aufrufe

## Was wir nicht wollen
- Keine langen Funktionen über 30 Zeilen
- Keine direkten client.chat.completions.create() Aufrufe
- Kein hardcoded API Key
- Keine Datenbanklogik außerhalb von datenbank.py

## Modell
MODELL = "gpt-5.4-mini"

## Wenn du neuen Code generierst
1. Erkläre zuerst was du vorhast
2. Zeige den Code mit deutschen Kommentaren
3. Erkläre danach was sich geändert hat
4. Weise auf mögliche Probleme hin