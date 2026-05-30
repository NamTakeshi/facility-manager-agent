# Facility Manager Agent

Ein KI-gestützter Assistent für private Vermieter. Mieter können Fragen stellen oder Schäden melden – der Agent beantwortet Fragen automatisch aus dem Mietvertrag und erstellt bei Schäden ein Ticket mit Handlungsvorschlag und E-Mail Entwurf für den Vermieter.

---

## Projektstruktur

```
facility-manager-agent/
│
├── facility_manager_agent/         ← Reflex Web-App (Haupt-Interface)
│   ├── __init__.py
│   └── facility_manager_agent.py
│
├── terminal/                       ← Terminal-Versionen (zum Testen)
│   ├── mieter.py
│   ├── vermieter.py
│   └── zeige_tickets.py
│
├── datenbank.py                    ← Alle Datenbankfunktionen
├── mietvertrag.txt                 ← Beispiel Mietvertrag
├── facility.db                     ← SQLite Datenbank (automatisch erstellt)
├── .env                            ← API Keys (nicht in Git einchecken)
├── requirements.txt                ← Benötigte Bibliotheken
├── rxconfig.py                     ← Reflex Konfiguration
└── reflex.lock                     ← Reflex Abhängigkeiten
```

---

## Installation

```bash
# Bibliotheken installieren
pip3 install openai python-dotenv reflex

# API Key in .env Datei eintragen
OPENAI_API_KEY=dein-api-key-hier

# App starten
reflex run
```

Dann im Browser öffnen:
- **Mieter:** http://localhost:3000
- **Vermieter:** http://localhost:3000/vermieter

---

## Dateien erklärt

### `datenbank.py`
Enthält alle Funktionen die mit der SQLite Datenbank kommunizieren. Wird von allen anderen Dateien importiert.

| Funktion | Was sie macht |
|---|---|
| `erstelle_datenbank()` | Erstellt die Tickets-Tabelle beim ersten Start |
| `speichere_ticket()` | Speichert eine neue Schadensmeldung als Ticket |
| `hole_alle_tickets()` | Gibt alle Tickets zurück |
| `hole_offene_tickets()` | Gibt nur offene und in Bearbeitung befindliche Tickets zurück |
| `hole_archiv_tickets()` | Gibt nur geschlossene Tickets zurück |
| `aktualisiere_ticket_status()` | Ändert den Status eines Tickets |

---

### `facility.db – Die Datenbank`

Eine SQLite Datenbankdatei die alle Tickets speichert. Kein extra Datenbankserver nötig – alles in einer einzigen Datei.
Jedes Ticket enthält: ID, Mieter, Beschreibung, Kategorie, Priorität, Handlungsvorschlag, E-Mail Entwurf, Status und Datum.

---

### `facility_manager_agent/facility_manager_agent.py`
Die Haupt-Datei der Web-App. Enthält die gesamte Logik und das UI.

#### Klassen (Für die Logik)

**`State`** – Verwaltet den Zustand der Mieter-Seite
| Variable / Methode | Was sie macht |
|---|---|
| `name` | Speichert den Namen des Mieters |
| `nachricht` | Speichert die Eingabe des Mieters |
| `antwort` | Speichert die Antwort des Agents |
| `laden` | Zeigt an ob der Agent gerade verarbeitet |
| `set_name()` | Aktualisiert den Namen wenn Mieter tippt |
| `set_nachricht()` | Aktualisiert die Nachricht wenn Mieter tippt |
| `sende_nachricht()` | Hauptfunktion – klassifiziert die Nachricht und reagiert |

**`VermietState`** – Verwaltet den Zustand der Vermieter-Seite
| Variable / Methode | Was sie macht |
|---|---|
| `tickets` | Liste aller aktuell angezeigten Tickets |
| `ansicht` | Aktuelle Ansicht: offen / alle / archiv |
| `zeige_offene()` | Lädt nur offene Tickets |
| `zeige_alle()` | Lädt alle Tickets |
| `zeige_archiv()` | Lädt nur geschlossene Tickets |
| `lade_tickets()` | Aktualisiert die Ticket-Liste je nach Ansicht |
| `setze_status()` | Ändert den Status eines Tickets |

#### Funktionen (Fürs UI-Design)

| Funktion | Was sie macht |
|---|---|
| `index()` | Baut die Mieter-Seite (http://localhost:3000) |
| `vermieter()` | Baut die Vermieter-Seite (http://localhost:3000/vermieter) |

---

### `terminal/mieter.py`
Terminal-Version des Mieter-Interfaces. Zum Testen ohne Reflex zu starten.


### `terminal/vermieter.py`
Terminal-Version des Vermieter-Dashboards. Zeigt Tickets als Text im Terminal.


### `terminal/zeige_tickets.py`
Schnelle Übersicht aller Tickets direkt im Terminal. Nützlich zum Debuggen.


---

## Ablauf erklärt

```
MIETER (http://localhost:3000)
  → Gibt Namen und Nachricht ein
  → Agent klassifiziert: FRAGE oder SCHADEN

  Bei FRAGE:
  → Agent durchsucht Mietvertrag (mietvertrag.txt)
  → Gibt spezifische Antwort zurück

  Bei SCHADEN:
  → Agent bewertet Priorität (HOCH / MITTEL / NIEDRIG)
  → Erstellt Handlungsvorschlag
  → Erstellt E-Mail Entwurf
  → Speichert Ticket in SQLite

VERMIETER (http://localhost:3000/vermieter)
  → Sieht alle Tickets mit Details
  → Kann zwischen Offen / Alle / Archiv wechseln
  → Kann Status eines Tickets ändern
```

---

## Technologie Stack

| Komponente | Technologie           |
|---|-----------------------|
| LLM | GPT-5.4 mini (OpenAI) |
| Agent Framework | Direkte OpenAI API    |
| Datenbank | SQLite                |
| Web-App | Reflex                |
| Sprache | Python                |

---

## Wichtige Hinweise

- Die `.env` Datei niemals in Git einchecken – sie enthält den API Key
- Die `facility.db` wird automatisch erstellt beim ersten Start
- Beim Ändern der Datenbankstruktur muss `facility.db` gelöscht und neu erstellt werden