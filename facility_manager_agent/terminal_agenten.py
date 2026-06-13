"""
Gemeinsamer Agents-SDK-Workflow fuer Terminal und Reflex-Web-App.

Struktur:
1. Ausgabe-Schemas definieren
2. Instruction-Strings fuer die Agenten definieren
3. Tools definieren
4. Agenten erstellen
5. Runner-Schritte in klaren Workflow-Funktionen ausfuehren

Wichtig: Analyse, Ticket-Inhalte und Speicherung sind getrennte Agent-Schritte.
Der Ticket-Speicher-Agent darf nur das explizit definierte SQLite-Tool nutzen.
"""
from typing import Any, Literal

from agents import Agent, Runner, function_tool, trace
from pydantic import BaseModel, Field

from datenbank import speichere_ticket as speichere_ticket_in_db
from datenbank import suche_handwerker_nach_fachgebiet



MODELL = "gpt-5.4-mini"


# ---------------------------------------------------------------------------
# 1. Ausgabe-Schemas
# ---------------------------------------------------------------------------

class EingabeKlassifikation(BaseModel):
    """Ergebnis des Eingabe-Klassifizierungs-Agenten."""

    kategorie: Literal["FRAGE", "SCHADEN", "SONSTIGES"] = Field(
        description="Art der Mieternachricht."
    )


class SchadenKlassifikation(BaseModel):
    """Fachliche Einordnung einer Schadensmeldung."""

    schadensart: str = Field(description="Kurze Bezeichnung des Schadens.")
    prioritaet: Literal["HOCH", "MITTEL", "NIEDRIG"] = Field(
        description="Dringlichkeit der Bearbeitung."
    )
    begruendung: str = Field(description="Kurze Begruendung der Prioritaet.")


class TicketEntwurf(BaseModel):
    """Vom Ticket-Agenten erzeugte Inhalte fuer das Datenbank-Ticket."""

    handlungsvorschlag: str = Field(
        description="Konkreter Vorschlag fuer den Vermieter."
    )
    email_entwurf: str = Field(
        description="Hoeflicher E-Mail-Entwurf an den Mieter."
    )


class TicketSpeicherung(BaseModel):
    """Ergebnis des Ticket-Speicher-Agenten nach dem SQLite-Insert."""

    ticket_id: int = Field(description="ID des gespeicherten Tickets.")
    status: Literal["GESPEICHERT"] = Field(description="Speicherstatus.")
    nachricht: str = Field(description="Kurze Bestaetigung fuer den Nutzer.")


# FEHLER GEFUNDEN (behoben): HandwerkerEmpfehlung muss VOR SchadenWorkflowErgebnis
# definiert sein, da Python Klassen-Annotationen sofort auswertet (kein Forward Reference).
class HandwerkerEmpfehlung(BaseModel):
    """Empfohlener Handwerker für eine Schadensmeldung."""

    handwerker_id: int = Field(description="ID des empfohlenen Handwerkers.")
    name: str = Field(description="Name des Handwerkers.")
    firma: str = Field(description="Firma des Handwerkers.")
    fachgebiet: str = Field(description="Fachgebiet des Handwerkers.")
    email: str = Field(description="E-Mail des Handwerkers.")
    begruendung: str = Field(description="Kurze Begründung warum dieser Handwerker passt.")


class SchadenWorkflowErgebnis(BaseModel):
    """Gesamtergebnis des Schaden-Workflows inklusive Datenbank-Speicherung."""

    schadensklassifikation: SchadenKlassifikation
    ticket_entwurf: TicketEntwurf
    ticket_speicherung: TicketSpeicherung
    handwerker: HandwerkerEmpfehlung


# ---------------------------------------------------------------------------
# 2. Instructions
# ---------------------------------------------------------------------------

eingabe_klassifizierer_inst = """
Du bist der Eingabe-Klassifizierungs-Agent fuer einen Facility-Manager.

Klassifiziere jede Mieternachricht genau in eine dieser Kategorien:
- FRAGE: Der Mieter fragt nach Informationen aus dem Mietvertrag.
- SCHADEN: Der Mieter meldet einen Defekt, Schaden, Mangel oder Reparaturbedarf.
- SONSTIGES: Alles, was weder Mietvertragsfrage noch Schadensmeldung ist.

Regeln:
- Wenn eine Nachricht gleichzeitig Frage und Schadensmeldung ist, waehle SCHADEN.
- Antworte nicht frei, sondern liefere nur das strukturierte Schema.
"""

fragen_agent_inst = """
Du bist der Mietvertrags-Frage-Agent fuer Mieter.

Dir werden der spezifische Mietvertrag des Mieters und die allgemeine Hausordnung als Text übergeben.

Aufgabe:
- Beantworte Fragen ausschliesslich auf Basis des übergebenen Textes.

Regeln:
- Antworte kurz, konkret und auf Deutsch.
- Erfinde keine Informationen.
- Wenn die Information weder im Mietvertrag noch in der Hausordnung steht, sage klar, dass du dazu keine Informationen in den Dokumenten findest.
"""

schaden_klassifizierer_inst = """
Du bist der Schaden-Klassifizierungs-Agent fuer einen Vermieter.

Aufgabe:
- Bestimme die Schadensart.
- Bestimme die Prioritaet: HOCH, MITTEL oder NIEDRIG.
- Begruende die Prioritaet kurz.

Prioritaetsregeln:
- HOCH: Gefahr, akuter Wasserschaden, Stromproblem, Heizungsausfall bei Kaelte,
  Sicherheitsproblem oder erheblicher Folgeschaden.
- MITTEL: Reparatur ist notwendig, aber es besteht keine akute Gefahr.
- NIEDRIG: Kosmetischer oder kleiner nicht dringender Mangel.

Regeln:
- Antworte sachlich und ohne erfundene Details.
- Liefere nur das strukturierte Schema.
"""

ticket_agent_inst = """
Du bist der Ticket-Erstellungs-Agent fuer Vermieter-Tickets.

Aufgabe:
- Erstelle aus Schadensmeldung und Schadensklassifikation einen konkreten
  Handlungsvorschlag.
- Erstelle einen hoeflichen E-Mail-Entwurf an den Mieter.

Regeln:
- Erfinde keine Termine, Handwerker, Telefonnummern oder Zusagen.
- Nutze die uebergebene Prioritaet und Begruendung als Kontext.
- Liefere nur das strukturierte Schema.
"""

ticket_speicher_agent_inst = """
Du bist der Ticket-Speicher-Agent fuer die SQLite-Datenbank.

Aufgabe:
- Speichere genau ein fertiges Schaden-Ticket in der Datenbank.
- Nutze dafuer das Tool `speichere_schadenticket`.
- Gib danach die gespeicherte Ticket-ID strukturiert zurueck.

Regeln:
- Rufe das Tool genau einmal auf.
- Veraendere die uebergebenen Ticket-Inhalte nicht.
- Speichere nur Tickets mit Kategorie "Schaden".
- Liefere nur das strukturierte Schema.
"""

handwerker_agent_inst = """
Du bist der Handwerker-Empfehlungs-Agent für einen Facility-Manager.

Aufgabe:
- Analysiere die Schadensart und bestimme das passende Fachgebiet
- Nutze das Tool suche_passenden_handwerker um einen Handwerker zu finden
- Empfehle den Handwerker mit der besten Bewertung

Fachgebiete:
- Heizung: Heizungsausfall, Heizkörper, Thermostat
- Sanitär: Wasserhahn, Rohr, Toilette, Dusche
- Elektro: Steckdose, Licht, Sicherung
- Schimmel: Schimmel, Feuchtigkeit
- Allgemein: alles andere

Regeln:
- Rufe das Tool genau einmal auf
- Liefere nur das strukturierte Schema
"""
# ---------------------------------------------------------------------------
# 3. Tools
# ---------------------------------------------------------------------------

@function_tool
def speichere_schadenticket(
    mieter: str,
    beschreibung: str,
    prioritaet: Literal["HOCH", "MITTEL", "NIEDRIG"],
    handlungsvorschlag: str,
    email_entwurf: str,
) -> int:
    """
    Speichert ein Schaden-Ticket in der SQLite-Datenbank und gibt die Ticket-ID zurueck.

    Args:
        mieter: Name des Mieters.
        beschreibung: Originale Schadensbeschreibung.
        prioritaet: Prioritaet des Schadens.
        handlungsvorschlag: Handlungsvorschlag fuer den Vermieter.
        email_entwurf: E-Mail-Entwurf an den Mieter.
    """
    return speichere_ticket_in_db(
        mieter=mieter,
        beschreibung=beschreibung,
        kategorie="Schaden",
        prioritaet=prioritaet,
        handlungsvorschlag=handlungsvorschlag,
        email_entwurf=email_entwurf,
    )


@function_tool
def suche_passenden_handwerker(fachgebiet: str) -> str:
    """
    Sucht einen passenden Handwerker aus der Datenbank.
    Nutze dieses Tool um den besten Handwerker für einen Schaden zu finden.

    Args:
        fachgebiet: Fachgebiet des gesuchten Handwerkers z.B. Heizung, Sanitär, Elektro, Schimmel
    """
    handwerker = suche_handwerker_nach_fachgebiet(fachgebiet)

    if not handwerker:
        return f"Kein Handwerker für Fachgebiet '{fachgebiet}' gefunden."

    # Ergebnis als lesbaren Text zurückgeben
    ergebnis = []
    for h in handwerker:
        ergebnis.append(
            f"ID: {h[0]} | Name: {h[1]} | Firma: {h[2]} | "
            f"Fachgebiet: {h[3]} | Email: {h[4]} | Bewertung: {h[6]}/5"
        )
    return "\n".join(ergebnis)

# ---------------------------------------------------------------------------
# 4. Agenten erstellen
# ---------------------------------------------------------------------------

eingabe_klassifizierer = Agent[Any](
    name="Eingabe-Klassifizierungs-Agent",
    instructions=eingabe_klassifizierer_inst,
    model=MODELL,
    output_type=EingabeKlassifikation,
)

fragen_agent = Agent[Any](
    name="Mietvertrags-Frage-Agent",
    instructions=fragen_agent_inst,
    model=MODELL,
)

schaden_klassifizierer = Agent[Any](
    name="Schaden-Klassifizierungs-Agent",
    instructions=schaden_klassifizierer_inst,
    model=MODELL,
    output_type=SchadenKlassifikation,
)

ticket_agent = Agent[Any](
    name="Ticket-Erstellungs-Agent",
    instructions=ticket_agent_inst,
    model=MODELL,
    output_type=TicketEntwurf,
)

ticket_speicher_agent = Agent[Any](
    name="Ticket-Speicher-Agent",
    instructions=ticket_speicher_agent_inst,
    model=MODELL,
    tools=[speichere_schadenticket],
    output_type=TicketSpeicherung,
)

handwerker_agent = Agent[Any](
    name="Handwerker-Empfehlungs-Agent",
    instructions=handwerker_agent_inst,
    model=MODELL,
    tools=[suche_passenden_handwerker],
    output_type=HandwerkerEmpfehlung,
)

# ---------------------------------------------------------------------------
# 5. Workflow-Funktionen
# ---------------------------------------------------------------------------

async def klassifiziere_eingabe(nachricht: str) -> EingabeKlassifikation:
    """Klassifiziert die Mieternachricht als FRAGE, SCHADEN oder SONSTIGES."""
    with trace("Facility Manager: Eingabe klassifizieren"):
        result = await Runner.run(eingabe_klassifizierer, nachricht)
        return result.final_output


async def beantworte_frage(frage: str, dokumenten_kontext: str) -> str:
    """Beantwortet eine Frage mit den gefilterten PDFs als Kontext."""
    eingabe = f"""
Verfügbare Dokumente:
{dokumenten_kontext}

Frage des Mieters:
{frage}
"""

    with trace("Facility Manager: Mietvertragsfrage beantworten"):
        result = await Runner.run(fragen_agent, eingabe)
        return str(result.final_output).strip()


async def klassifiziere_schaden(
    beschreibung: str,
    mieter: str,
) -> SchadenKlassifikation:
    """Analysiert Schadensart, Prioritaet und Begruendung."""
    eingabe = f"""
Mieter: {mieter}
Schadensmeldung: {beschreibung}
"""

    with trace("Facility Manager: Schaden klassifizieren"):
        result = await Runner.run(schaden_klassifizierer, eingabe)
        return result.final_output


async def erstelle_ticket_entwurf(
    beschreibung: str,
    mieter: str,
    schadensklassifikation: SchadenKlassifikation,
) -> TicketEntwurf:
    """Erstellt Handlungsvorschlag und E-Mail-Entwurf fuer das Ticket."""
    eingabe = f"""
Mieter: {mieter}
Schadensmeldung: {beschreibung}
Schadensart: {schadensklassifikation.schadensart}
Prioritaet: {schadensklassifikation.prioritaet}
Begruendung: {schadensklassifikation.begruendung}
"""

    with trace("Facility Manager: Ticket-Inhalte erstellen"):
        result = await Runner.run(ticket_agent, eingabe)
        return result.final_output


async def speichere_ticket_mit_agent(
    beschreibung: str,
    mieter: str,
    schadensklassifikation: SchadenKlassifikation,
    ticket_entwurf: TicketEntwurf,
) -> TicketSpeicherung:
    """Speichert ein fertiges Schaden-Ticket ueber den Ticket-Speicher-Agenten."""
    eingabe = f"""
Speichere dieses Schaden-Ticket in der SQLite-Datenbank.

Mieter: {mieter}
Beschreibung: {beschreibung}
Kategorie: Schaden
Prioritaet: {schadensklassifikation.prioritaet}
Handlungsvorschlag: {ticket_entwurf.handlungsvorschlag}
E-Mail-Entwurf: {ticket_entwurf.email_entwurf}

Nutze das Tool `speichere_schadenticket` genau einmal.
"""

    with trace("Facility Manager: Ticket speichern"):
        result = await Runner.run(ticket_speicher_agent, eingabe)
        return result.final_output


async def erstelle_schaden_workflow(
    beschreibung: str,
    mieter: str,
) -> SchadenWorkflowErgebnis:
    """
    Fuehrt den dreistufigen Schaden-Workflow aus:
    1. Schaden klassifizieren
    2. Ticket-Inhalte erstellen
    3. Handwerker empfehlen
    3. Ticket ueber den Ticket-Speicher-Agenten in SQLite speichern
    """
    schadensklassifikation = await klassifiziere_schaden(beschreibung, mieter)
    ticket_entwurf = await erstelle_ticket_entwurf(
        beschreibung,
        mieter,
        schadensklassifikation,
    )
    handwerker = await empfehle_handwerker(beschreibung, schadensklassifikation)
    ticket_speicherung = await speichere_ticket_mit_agent(
        beschreibung,
        mieter,
        schadensklassifikation,
        ticket_entwurf,
    )

    return SchadenWorkflowErgebnis(
        schadensklassifikation=schadensklassifikation,
        ticket_entwurf=ticket_entwurf,
        ticket_speicherung=ticket_speicherung,
        handwerker=handwerker,
    )

async def empfehle_handwerker(
    schadensart: str,
    schadensklassifikation: SchadenKlassifikation,
) -> HandwerkerEmpfehlung:
    """Sucht passenden Handwerker basierend auf Schadensart."""
    eingabe = f"""
Schadensart: {schadensart}
Fachgebiet bestimmen und passenden Handwerker suchen.
Schadensklassifikation: {schadensklassifikation.schadensart}
"""
    with trace("Facility Manager: Handwerker suchen"):
        result = await Runner.run(handwerker_agent, eingabe)
        return result.final_output