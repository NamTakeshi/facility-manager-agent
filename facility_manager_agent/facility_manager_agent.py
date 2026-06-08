import os
import sys
from pathlib import Path

import reflex as rx
from dotenv import load_dotenv

# Pfad zum Hauptordner hinzufügen, damit datenbank.py gefunden wird.
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from datenbank import (
    aktualisiere_ticket_status,
    aktualisiere_ticket_handwerker,
    erstelle_datenbank,
    hole_alle_tickets,
    hole_archiv_tickets,
    hole_offene_tickets,
    fuege_dummy_handwerker_ein,
)
from facility_manager_agent.terminal_agenten import (
    beantworte_frage,
    erstelle_schaden_workflow,
    klassifiziere_eingabe,
)

load_dotenv(BASE_DIR / ".env")
erstelle_datenbank()
fuege_dummy_handwerker_ein()

# Mietvertrag laden
with open(BASE_DIR / "mietvertrag.txt", "r", encoding="utf-8") as f:
    mietvertrag = f.read()


class State(rx.State):
    name: str = ""
    nachricht: str = ""
    antwort: str = ""
    kategorie: str = ""
    laden: bool = False

    def set_name(self, value: str):
        self.name = value

    def set_nachricht(self, value: str):
        self.nachricht = value

    async def sende_nachricht(self):
        if not self.name.strip() or not self.nachricht.strip():
            self.antwort = "Bitte Namen und Nachricht eingeben."
            return

        if not os.getenv("OPENAI_API_KEY"):
            self.antwort = "OPENAI_API_KEY fehlt. Bitte .env Datei prüfen."
            return

        self.laden = True
        self.antwort = ""

        try:
            # Schritt 1: Klassifikation durch den gemeinsamen Agents-SDK-Workflow.
            klassifikation = await klassifiziere_eingabe(self.nachricht)
            self.kategorie = klassifikation.kategorie

            if self.kategorie == "FRAGE":
                self.antwort = await beantworte_frage(self.nachricht, mietvertrag)



            elif self.kategorie == "SCHADEN":
                workflow = await erstelle_schaden_workflow(self.nachricht, self.name)
                schadensklassifikation = workflow.schadensklassifikation
                ticket_speicherung = workflow.ticket_speicherung
                handwerker = workflow.handwerker
                # Handwerker-Infos ins Ticket speichern
                aktualisiere_ticket_handwerker(
                    ticket_id=ticket_speicherung.ticket_id,
                    handwerker_name=handwerker.name,
                    handwerker_firma=handwerker.firma,
                    handwerker_email=handwerker.email,
                    handwerker_fachgebiet=handwerker.fachgebiet,
                )
                self.antwort = (
                    "Ihre Schadensmeldung wurde aufgenommen. "
                    f"Ticket #{ticket_speicherung.ticket_id} wurde erstellt. "
                    "Der Vermieter wird sich zeitnah bei Ihnen melden."
                )

            else:
                self.antwort = "Ich kann nur Fragen zum Mietvertrag beantworten oder Schäden aufnehmen."

        except Exception as exc:
            self.antwort = f"Die Anfrage konnte nicht verarbeitet werden: {exc}"
        finally:
            self.laden = False

def index():
    return rx.vstack(
        # Header
        rx.box(
            rx.heading("Facility Manager Agent", size="6", color="white"),
            rx.text("Mieter Portal", color="white", opacity="0.8"),
            background="#1E3A5F",
            width="100%",
            padding="1.5em",
        ),

        # Inhalt
        rx.vstack(
            rx.heading("Wie können wir Ihnen helfen?", size="4"),

            # Name
            rx.vstack(
                rx.text("Ihr Name", font_weight="500"),
                rx.input(
                    placeholder="Max Mustermann",
                    on_change=State.set_name,
                    width="100%",
                    color="#1A1A1A",
                ),
                width="100%",
                align_items="start",
            ),

            # Nachricht
            rx.vstack(
                rx.text("Ihre Nachricht", font_weight="500"),
                rx.text_area(
                    placeholder="Stellen Sie eine Frage oder melden Sie einen Schaden...",
                    on_change=State.set_nachricht,
                    width="100%",
                    height="120px",
                    color="#1A1A1A",
                ),
                width="100%",
                align_items="start",
            ),

            # Button
            rx.button(
                rx.cond(State.laden, "Wird verarbeitet...", "Absenden"),
                on_click=State.sende_nachricht,
                background="#1E3A5F",
                color="white",
                width="100%",
                disabled=State.laden,
            ),

            # Antwort
            rx.cond(
                State.antwort != "",
                rx.box(
                    rx.text("Antwort:", font_weight="bold", margin_bottom="0.5em"),
                    rx.text(State.antwort),
                    background="#F0F4F8",
                    padding="1em",
                    border_radius="8px",
                    width="100%",
                )
            ),

            width="100%",
            max_width="600px",
            padding="2em",
            spacing="4",
        ),

        width="100%",
        min_height="100vh",
        align_items="center",
        background="#FAFAFA",
    )

class VermietState(rx.State):
    tickets: list[list] = []
    ansicht: str = "offen"

    def zeige_offene(self):
        self.ansicht = "offen"
        self.tickets = hole_offene_tickets()

    def zeige_archiv(self):
        self.ansicht = "archiv"
        self.tickets = hole_archiv_tickets()

    def zeige_alle(self):
        self.ansicht = "alle"
        self.tickets = hole_alle_tickets()

    def lade_tickets(self):
        if self.ansicht == "offen":
            self.tickets = hole_offene_tickets()
        elif self.ansicht == "archiv":
            self.tickets = hole_archiv_tickets()
        else:
            self.tickets = hole_alle_tickets()

    def setze_status(self, ticket_id: int, status: str):
        aktualisiere_ticket_status(ticket_id, status)
        self.lade_tickets()

def vermieter():
    return rx.vstack(
        # Header
        rx.box(
            rx.heading("Vermieter Dashboard", size="6", color="white"),
            background="#1E3A5F",
            width="100%",
            padding="1.5em",
        ),

        # Navigation – drei Buttons
        rx.hstack(
            rx.button(
                "Alle Tickets",
                on_click=VermietState.zeige_alle,
                background=rx.cond(
                    VermietState.ansicht == "alle",
                    "#1E3A5F", "#E2E8F0"
                ),
                color=rx.cond(
                    VermietState.ansicht == "alle",
                    "white", "#1A1A1A"
                ),
            ),

            rx.button(
                "Offene Tickets",
                on_click=VermietState.zeige_offene,
                background=rx.cond(
                    VermietState.ansicht == "offen",
                    "#1E3A5F", "#E2E8F0"
                ),
                color=rx.cond(
                    VermietState.ansicht == "offen",
                    "white", "#1A1A1A"
                ),
            ),

            rx.button(
                "Archiv",
                on_click=VermietState.zeige_archiv,
                background=rx.cond(
                    VermietState.ansicht == "archiv",
                    "#1E3A5F", "#E2E8F0"
                ),
                color=rx.cond(
                    VermietState.ansicht == "archiv",
                    "white", "#1A1A1A"
                ),
            ),
            margin="1em",
        ),

        # Ticket Liste
        rx.foreach(
            VermietState.tickets,
            lambda ticket: rx.box(
                rx.text(ticket[0], font_weight="bold", color="#1A1A1A"),
                rx.text(f"Mieter: {ticket[1]}", color="#1A1A1A"),
                rx.text(f"Beschreibung: {ticket[2]}", color="#1A1A1A"),
                rx.text(f"Priorität: {ticket[4]}", color="#1A1A1A"),
                rx.text(f"Status: {ticket[7]}", color="#1A1A1A"),
                rx.text(f"Vorschlag: {ticket[5]}", color="#1A1A1A"),
                rx.text(f"E-Mail: {ticket[6]}", color="#1A1A1A"),
                rx.text(f"Handwerker: {ticket[9]}", color="#1A1A1A"),
                rx.text(f"Firma: {ticket[10]}", color="#1A1A1A"),
                rx.text(f"Handwerker Kontakt: {ticket[11]}", color="#1A1A1A"),

                # Status Buttons – immer sichtbar, alle Optionen
                rx.hstack(
                    rx.button(
                        "Offen",
                        on_click=VermietState.setze_status(ticket[0], "Offen"),
                        background="#6B7280",
                        color="white",
                        size="2",
                    ),
                    rx.button(
                        "In Bearbeitung",
                        on_click=VermietState.setze_status(ticket[0], "In Bearbeitung"),
                        background="#2E86AB",
                        color="white",
                        size="2",
                    ),
                    rx.button(
                        "Geschlossen",
                        on_click=VermietState.setze_status(ticket[0], "Geschlossen"),
                        background="#1E3A5F",
                        color="white",
                        size="2",
                    ),
                    margin_top="0.5em",
                ),

                border="1px solid #E2E8F0",
                border_radius="8px",
                padding="1em",
                margin="0.5em",
                width="90%",
                background="white",
            )
        ),

        width="100%",
        min_height="100vh",
        align_items="center",
        background="#FAFAFA",
        on_mount=VermietState.zeige_offene,
    )

app = rx.App(
    style={
        "color": "#1A1A1A",
        "font_family": "Aptos, sans-serif",
    }
)
app.add_page(index, route="/")
app.add_page(vermieter, route="/vermieter")
