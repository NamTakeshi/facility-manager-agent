# Facility Manager Agent

Ein KI-gestützter Assistent für private Vermieter. Mieter können Fragen stellen oder Schäden melden – der Agent beantwortet Fragen automatisch aus dem Mietvertrag und erstellt bei Schäden ein Ticket mit Handlungsvorschlag und E-Mail Entwurf für den Vermieter.

---

## Projektstruktur

```
facility-manager-agent/
│
├── facility_manager_agent/         ← Reflex Web-App (Haupt-Interface)
│   ├── __init__.py
│   ├── terminal_agenten.py          ← Gemeinsamer Agents-SDK-Workflow
│   └── facility_manager_agent.py
│
├── terminal/                       ← Terminal-Versionen (zum Testen)
│   ├── mieter.py
│   ├── vermieter.py
│   └── zeige_tickets.py
│   └── zeige_handwerker.py
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
python3 -m pip install -r requirements.txt

# API Key in .env Datei eintragen
OPENAI_API_KEY=dein-api-key-hier

# Web-App starten
reflex run
```

Dann im Browser öffnen:
- **Mieter:** http://localhost:3000
- **Vermieter:** http://localhost:3000/vermieter

---

## Dateien erklärt

### `datenbank.py`
Enthält alle Funktionen die mit der SQLite Datenbank kommunizieren. Wird von allen anderen Dateien importiert.

| Funktion                             | Was sie macht                                                 |
|--------------------------------------|---------------------------------------------------------------|
| `erstelle_datenbank()`               | Erstellt die Tickets + Handwerker Tabelle                     |
| `speichere_ticket()`                 | Speichert eine neue Schadensmeldung als Ticket                |
| `hole_alle_tickets()`                | Gibt alle Tickets zurück                                      |
| `hole_offene_tickets()`              | Gibt nur offene und in Bearbeitung befindliche Tickets zurück |
| `hole_archiv_tickets()`              | Gibt nur geschlossene Tickets zurück                          |
| `hole_alle_handwerker()`             | Gibt alle Handwerker zurück                                   |
| `aktualisiere_ticket_status()`       | Ändert den Status eines Tickets                               |
| `aktualisiere_ticket_handwerker()`   | Fügt Handwerker-Infos zu Ticket hinzu                         |
| `fuege_dummy_handwerker_ein()`       | Fügt Beispiel-Handwerker ein                                  |
| `suche_handwerker_nach_fachgebiet()` | Sucht Handwerker nach Fachgebiet                              |


---

### `facility.db – Die Datenbank`

Eine SQLite Datenbankdatei die alle Tickets speichert. Kein extra Datenbankserver nötig – alles in einer einzigen Datei.
Jedes Ticket enthält: ID, Mieter, Beschreibung, Kategorie, Priorität, Handlungsvorschlag, E-Mail Entwurf, Status und Datum.

---

### `facility_manager_agent/facility_manager_agent.py`
Die Haupt-Datei der Web-App. Enthält die gesamte Logik und das UI.
Die Mieter-Seite nutzt den gemeinsamen Agents-SDK-Workflow aus
`facility_manager_agent/terminal_agenten.py`. Direkte
`client.chat.completions.create(...)` Aufrufe werden in der Web-App nicht mehr
verwendet.

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

Terminal und Web-App nutzen denselben OpenAI Agents SDK Workflow. Der Ablauf ist
bewusst wie ein klarer Agents-Workflow aufgebaut:

```
Mieternachricht
  → Eingabe-Klassifizierungs-Agent
  → bei FRAGE: Mietvertrags-Frage-Agent
  → bei SCHADEN: Schaden-Klassifizierungs-Agent
                 → Ticket-Erstellungs-Agent
                 → Ticket-Speicher-Agent
                 → SQLite speichert Ticket
  → bei SONSTIGES: Standardantwort
```

Die Agenten sind in `facility_manager_agent/terminal_agenten.py` definiert.
Dort ist die Struktur:

1. Ausgabe-Schemas
2. Instruction-Strings
3. Tool-Definition fuer den SQLite-Insert
4. Agent-Definitionen
5. Workflow-Funktionen mit `Runner.run(...)` und `trace(...)`

Der Agents SDK nutzt intern weiterhin die OpenAI API, aber Terminal und Web-App
machen keine direkten `client.chat.completions.create(...)` Aufrufe mehr.

#### Unterschied zur frueheren direkten API-Nutzung

Frueher lagen Prompt, Modellaufruf und Parsing direkt in `terminal/mieter.py`.
Der Code hat mehrfach direkt die Chat-Completions-API aufgerufen:

```python
client.chat.completions.create(...)
```

Danach musste die Textantwort manuell ausgewertet werden, z. B. durch Suchen nach
`PRIORITÄT:`, `VORSCHLAG:`, `EMAIL_START` und `EMAIL_END`. Das war fehleranfaellig,
weil kleine Formatabweichungen des Modells das Parsing brechen konnten.

Jetzt sprechen `terminal/mieter.py` und `facility_manager_agent/facility_manager_agent.py`
nicht mehr direkt mit `chat.completions`. Stattdessen rufen sie Funktionen aus
`facility_manager_agent/terminal_agenten.py` auf.
Dort sind die Agenten klar getrennt definiert:

| Agent | Aufgabe |
|---|---|
| `eingabe_klassifizierer` | Entscheidet, ob die Nachricht `FRAGE`, `SCHADEN` oder `SONSTIGES` ist |
| `fragen_agent` | Beantwortet Mietvertragsfragen nur mit Kontext aus `mietvertrag.txt` |
| `schaden_klassifizierer` | Bestimmt Schadensart, Prioritaet und Begruendung |
| `ticket_agent` | Erstellt Handlungsvorschlag und E-Mail-Entwurf |
| `ticket_speicher_agent` | Speichert das fertige Schaden-Ticket ueber ein Tool in SQLite |

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

Das Speichern in SQLite laeuft jetzt ebenfalls ueber einen Agenten-Schritt:
Der `ticket_speicher_agent` nutzt das Tool `speichere_schadenticket`. Dieses Tool
ist die einzige Stelle im Agents-SDK-Workflow, die den SQLite-Insert ausfuehrt.
Dadurch bleibt der Datenbankzugriff weiterhin klar begrenzt und nachvollziehbar.

Kurz gesagt:

```text
Frueher:
terminal/mieter.py -> direkter Chat-Completions-Call -> Text parsen -> Ticket speichern

Jetzt:
Terminal/Web-App -> Agents-SDK-Workflow -> Ticket-Speicher-Agent -> SQLite
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
  → Handwerker-Agent sucht passenden Handwerker
  → Speicher-Agent übernimmt Ticket in SQLite

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
| Agent Framework | OpenAI Agents SDK |
| Datenbank | SQLite                |
| Web-App | Reflex                |
| Sprache | Python                |

---

## Wichtige Hinweise

- Die `.env` Datei niemals in Git einchecken – sie enthält den API Key
- Die `facility.db` wird automatisch erstellt beim ersten Start
- Beim Ändern der Datenbankstruktur muss `facility.db` gelöscht und neu erstellt werden
- Terminal und Web-App nutzen den gemeinsamen OpenAI Agents SDK Workflow.



## Agents-SDK Setup fuer Terminal und Web-App

Nach dem Pull die Abhaengigkeiten in der jeweils genutzten Python-Umgebung
installieren. Das kann eine virtuelle Umgebung, eine Conda-Umgebung oder eine
andere aktive Umgebung sein. Wichtig ist nur, dass der Python-Interpreter und
`pip` auf dieselbe Umgebung zeigen.

```bash
python3 -m pip install -r requirements.txt
```

Falls die eigene Umgebung einen anderen Interpreter-Namen verwendet, den Befehl
entsprechend anpassen, z. B. `python -m pip ...`.

-falls eine virtuelle Umgebung genutzt wird:
```bash
source .venv/bin/activate
```


In der `.env` Datei muss ein OpenAI API-Key stehen:

```env
OPENAI_API_KEY=dein-api-key
```

Terminal-Agent starten:

```bash
python3 terminal/mieter.py
```

Web-App starten:

```bash
reflex run
```

Pruefen, dass Terminal und Web-App ueber den Agents SDK laufen:

```bash
rg "from agents|Runner.run|trace" facility_manager_agent/terminal_agenten.py
rg "chat.completions|OpenAI\\(" terminal facility_manager_agent
```

Der zweite Befehl sollte fuer `terminal/` und `facility_manager_agent/` keine
Treffer liefern. Das bestaetigt, dass der App-Code nicht mehr direkt
`chat.completions` oder `OpenAI(...)` verwendet.

Rollen der Dateien:

```text
facility_manager_agent/terminal_agenten.py = gemeinsamer Agents-SDK-Workflow
terminal/mieter.py = Terminal-Eingabe und Speichern
terminal/vermieter.py = Terminal-Dashboard
facility_manager_agent/facility_manager_agent.py = Reflex-Web-App und Speichern
```
