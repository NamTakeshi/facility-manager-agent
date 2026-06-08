"""
Terminal-Version des Mieter-Interfaces.

Zum Testen ohne Reflex zu starten.
Mieter können Fragen stellen oder Schäden melden - direkt im Terminal.
Starten mit: ^R
"""
import asyncio
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
from datenbank import erstelle_datenbank, speichere_ticket, fuege_dummy_handwerker_ein
from facility_manager_agent.terminal_agenten import (
    beantworte_frage,
    erstelle_schaden_workflow,
    klassifiziere_eingabe,
)


# API-Key aus .env laden. Der Agents SDK liest OPENAI_API_KEY aus der Umgebung.
load_dotenv(BASE_DIR / ".env")
if not os.getenv("OPENAI_API_KEY"):
    print("OPENAI_API_KEY fehlt. Bitte in der .env Datei eintragen.")
    sys.exit(1)

# Datenbank beim Start erstellen
erstelle_datenbank()
fuege_dummy_handwerker_ein()

# Mietvertrag aus Datei laden statt hardcoded.
with open(BASE_DIR / "mietvertrag.txt", "r", encoding="utf-8") as f:
    mietvertrag = f.read()

async def verarbeite_schaden(beschreibung: str, mieter: str) -> str:
    workflow = await erstelle_schaden_workflow(beschreibung, mieter)
    schadensklassifikation = workflow.schadensklassifikation
    ticket_speicherung = workflow.ticket_speicherung
    handwerker = workflow.handwerker

    # Handwerker-Infos nachträglich ins Ticket speichern
    from datenbank import aktualisiere_ticket_handwerker
    aktualisiere_ticket_handwerker(
        ticket_id=ticket_speicherung.ticket_id,
        handwerker_name=handwerker.name,
        handwerker_firma=handwerker.firma,
        handwerker_email=handwerker.email,
        handwerker_fachgebiet=handwerker.fachgebiet,
    )

    return f"""Ticket #{ticket_speicherung.ticket_id} wurde erstellt.
    Priorität: {schadensklassifikation.prioritaet}
    Der Vermieter wird sich zeitnah bei Ihnen melden."""


async def main():
    """Startet die Terminal-Schleife und ruft den Agents-SDK-Workflow auf."""
    print("Willkommen beim Facility Manager Agent!")
    print("Stellen Sie Fragen oder melden Sie Schäden.")
    print("Zum Beenden 'exit' eingeben.\n")

    # Mietername einmalig abfragen.
    mieter_name = input("Bitte geben Sie Ihren Namen ein: ")
    print()

    # Schleife damit der Nutzer mehrere Fragen stellen kann.
    while True:
        eingabe = input("Ihre Nachricht: ")

        if eingabe.lower() == "exit":
            print("Auf Wiedersehen!")
            break

        if eingabe.strip() == "":
            continue

        # Schritt 1: Klassifikation durch den Eingabe-Klassifizierungs-Agenten.
        kategorie = (await klassifiziere_eingabe(eingabe)).kategorie
        print(f"[Erkannt: {kategorie}]")

        # Schritt 2: Passenden Spezial-Agenten-Workflow ausfuehren.
        if kategorie == "FRAGE":
            antwort = await beantworte_frage(eingabe, mietvertrag)
            print("Antwort:", antwort)

        elif kategorie == "SCHADEN":
            antwort = await verarbeite_schaden(eingabe, mieter_name)
            print("Antwort:", antwort)

        else:
            print("Antwort: Ich kann nur Fragen zum Mietvertrag beantworten oder Schäden aufnehmen.")

        print()


if __name__ == "__main__":
    asyncio.run(main())
