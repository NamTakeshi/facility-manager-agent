"""
Agenten-Workflow fuer die Terminal-Version des Facility Manager Agent.

Struktur:
1. Ausgabe-Schemas definieren
2. Instruction-Strings fuer die Agenten definieren
3. Agenten erstellen
4. Runner-Schritte in klaren Workflow-Funktionen ausfuehren

Wichtig: Die Agenten erzeugen strukturierte Ergebnisse. Das Speichern in die
SQLite-Datenbank passiert weiterhin kontrolliert im Terminal-Skript, damit ein
Ticket nicht versehentlich mehrfach oder mit falschem Zeitpunkt gespeichert wird.
"""
from typing import Any, Literal

from agents import Agent, Runner, trace
from pydantic import BaseModel, Field


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


class SchadenWorkflowErgebnis(BaseModel):
    """Gesamtergebnis des Schaden-Workflows vor dem Datenbank-Speichern."""

    schadensklassifikation: SchadenKlassifikation
    ticket_entwurf: TicketEntwurf


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

Aufgabe:
- Beantworte Fragen ausschliesslich auf Basis des uebergebenen Mietvertrags.

Regeln:
- Antworte kurz, konkret und auf Deutsch.
- Erfinde keine Informationen.
- Wenn der Mietvertrag keine passende Information enthaelt, sage das klar.
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


# ---------------------------------------------------------------------------
# 3. Agenten erstellen
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


# ---------------------------------------------------------------------------
# 4. Workflow-Funktionen
# ---------------------------------------------------------------------------

async def klassifiziere_eingabe(nachricht: str) -> EingabeKlassifikation:
    """Klassifiziert die Mieternachricht als FRAGE, SCHADEN oder SONSTIGES."""
    with trace("Terminal: Eingabe klassifizieren"):
        result = await Runner.run(eingabe_klassifizierer, nachricht)
        return result.final_output


async def beantworte_frage(frage: str, mietvertrag: str) -> str:
    """Beantwortet eine Mietvertragsfrage mit dem Mietvertrag als Kontext."""
    eingabe = f"""
Mietvertrag:
{mietvertrag}

Frage des Mieters:
{frage}
"""

    with trace("Terminal: Mietvertragsfrage beantworten"):
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

    with trace("Terminal: Schaden klassifizieren"):
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

    with trace("Terminal: Ticket-Inhalte erstellen"):
        result = await Runner.run(ticket_agent, eingabe)
        return result.final_output


async def erstelle_schaden_workflow(
    beschreibung: str,
    mieter: str,
) -> SchadenWorkflowErgebnis:
    """
    Fuehrt den zweistufigen Schaden-Workflow aus:
    1. Schaden klassifizieren
    2. Ticket-Inhalte erstellen
    """
    schadensklassifikation = await klassifiziere_schaden(beschreibung, mieter)
    ticket_entwurf = await erstelle_ticket_entwurf(
        beschreibung,
        mieter,
        schadensklassifikation,
    )

    return SchadenWorkflowErgebnis(
        schadensklassifikation=schadensklassifikation,
        ticket_entwurf=ticket_entwurf,
    )
