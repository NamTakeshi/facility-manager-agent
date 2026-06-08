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

Die Terminal-Version nutzt den OpenAI Agents SDK. Der Ablauf ist bewusst wie ein
klarer Agents-Workflow aufgebaut:

```
Mieternachricht
  → Eingabe-Klassifizierungs-Agent
  → bei FRAGE: Mietvertrags-Frage-Agent
  → bei SCHADEN: Schaden-Klassifizierungs-Agent
                 → Ticket-Erstellungs-Agent
                 → Python speichert Ticket in SQLite
  → bei SONSTIGES: Standardantwort
```

Die Agenten sind in `facility_manager_agent/terminal_agenten.py` definiert.
Dort ist die Struktur:

1. Ausgabe-Schemas
2. Instruction-Strings
3. Agent-Definitionen
4. Workflow-Funktionen mit `Runner.run(...)` und `trace(...)`

Der Agents SDK nutzt intern weiterhin die OpenAI API, aber der Terminal-Code
macht keine direkten `client.chat.completions.create(...)` Aufrufe mehr.

#### Unterschied zur frueheren direkten API-Nutzung

Frueher lagen Prompt, Modellaufruf und Parsing direkt in `terminal/mieter.py`.
Der Code hat mehrfach direkt die Chat-Completions-API aufgerufen:

```python
client.chat.completions.create(...)
```

Danach musste die Textantwort manuell ausgewertet werden, z. B. durch Suchen nach
`PRIORITÄT:`, `VORSCHLAG:`, `EMAIL_START` und `EMAIL_END`. Das war fehleranfaellig,
weil kleine Formatabweichungen des Modells das Parsing brechen konnten.

Jetzt spricht `terminal/mieter.py` nicht mehr direkt mit `chat.completions`.
Stattdessen ruft es Funktionen aus `facility_manager_agent/terminal_agenten.py` auf.
Dort sind die Agenten klar getrennt definiert:

| Agent | Aufgabe |
|---|---|
| `eingabe_klassifizierer` | Entscheidet, ob die Nachricht `FRAGE`, `SCHADEN` oder `SONSTIGES` ist |
| `fragen_agent` | Beantwortet Mietvertragsfragen nur mit Kontext aus `mietvertrag.txt` |
| `schaden_klassifizierer` | Bestimmt Schadensart, Prioritaet und Begruendung |
| `ticket_agent` | Erstellt Handlungsvorschlag und E-Mail-Entwurf |

Die Agenten werden mit dem Agents SDK ausgefuehrt:

```python
result = await Runner.run(agent, eingabe)
```

Fuer Klassifikation, Schadenanalyse und Ticket-Inhalte werden Pydantic-Schemas
verwendet. Dadurch kommen strukturierte Python-Objekte zurueck, nicht frei zu
parsende Textbloecke.

Beispiel:

```python
schadensklassifikation.prioritaet
ticket_entwurf.email_entwurf
```

Das Speichern in SQLite bleibt bewusst in normalem Python-Code in
`terminal/mieter.py`. Der Agent erzeugt also die Inhalte, aber Python entscheidet,
wann `speichere_ticket(...)` aufgerufen wird. Dadurch bleibt der Datenbankzugriff
kontrolliert und nachvollziehbar.

Kurz gesagt:

```text
Frueher:
terminal/mieter.py -> direkter Chat-Completions-Call -> Text parsen -> Ticket speichern

Jetzt:
terminal/mieter.py -> Agents-SDK-Workflow -> strukturierte Ergebnisse -> Ticket speichern
```


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
| Agent Framework | Terminal: OpenAI Agents SDK / Web-App: Direkte OpenAI API |
| Datenbank | SQLite                |
| Web-App | Reflex                |
| Sprache | Python                |

---

## Wichtige Hinweise

- Die `.env` Datei niemals in Git einchecken – sie enthält den API Key
- Die `facility.db` wird automatisch erstellt beim ersten Start
- Beim Ändern der Datenbankstruktur muss `facility.db` gelöscht und neu erstellt werden
- Die Terminal-Version nutzt bereits den OpenAI Agents SDK. Die Web-App ist noch nicht migriert.



## Agents-SDK Setup fuer die Terminal-Version

Nach dem Pull:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

In der `.env` Datei muss ein OpenAI API-Key stehen:

```env
OPENAI_API_KEY=dein-api-key
```

Terminal-Agent starten:

```bash
python terminal/mieter.py
```

Pruefen, dass der Terminal-Code ueber den Agents SDK laeuft:

```bash
rg "from agents|Runner.run|trace" facility_manager_agent/terminal_agenten.py terminal
rg "chat.completions|OpenAI\\(" terminal facility_manager_agent/terminal_agenten.py
```
Agents SDK = Logik / KI-Workflow
mieter.py = Terminal-Eingabe und Speichern
vermieter.py = Terminal-Dashboard