import os
import sys
from pathlib import Path

import reflex as rx
from dotenv import load_dotenv

# Pfad zum Hauptordner hinzufügen, damit datenbank.py gefunden wird.
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

import secrets

from datenbank import (
    aktualisiere_ticket_status,
    aktualisiere_ticket_handwerker,
    aktualisiere_ticket_mieter_email,
    aktualisiere_ticket_mieter_telefon,
    speichere_terminoptionen,
    bestatige_termin,
    hole_ticket_nach_token,
    erstelle_datenbank,
    hole_alle_tickets,
    hole_neue_tickets,
    hole_laufende_tickets,
    hole_archiv_tickets,
    zaehle_neue_tickets,
    fuege_dummy_handwerker_ein,
)
from email_service import sende_email_an_mieter, sende_email_an_handwerker, sende_terminbestaetigung

# NEU: Importiert die neuen Funktionen
from dokumente import lade_dokumente_in_cache, hole_kontext_fuer_mieter

load_dotenv(BASE_DIR / ".env")
erstelle_datenbank()
fuege_dummy_handwerker_ein()

# NEU: Lädt alle PDFs in den Arbeitsspeicher beim Serverstart
lade_dokumente_in_cache()

from facility_manager_agent.terminal_agenten import (
    beantworte_frage,
    erstelle_schaden_workflow,
    klassifiziere_eingabe,
)

class State(rx.State):
    name: str = ""
    email: str = ""
    telefon: str = ""
    nachricht: str = ""
    antwort: str = ""
    kategorie: str = ""
    laden: bool = False
    termin_1: str = ""
    termin_2: str = ""
    termin_3: str = ""

    def set_name(self, value: str):
        self.name = value

    def set_email(self, value: str):
        self.email = value

    def set_telefon(self, value: str):
        self.telefon = value

    def set_nachricht(self, value: str):
        self.nachricht = value

    def set_termin_1(self, value: str):
        self.termin_1 = value

    def set_termin_2(self, value: str):
        self.termin_2 = value

    def set_termin_3(self, value: str):
        self.termin_3 = value

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
                # NEU: Wir holen NUR den relevanten Text für diesen speziellen Mieter
                gefilterter_kontext = hole_kontext_fuer_mieter(self.name)

                # Und übergeben diesen reduzierten Text an den Agenten (Fehler korrigiert: nur 2 Zutaten)
                self.antwort = await beantworte_frage(self.nachricht, gefilterter_kontext)



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
                # Mieter-Kontaktdaten ins Ticket speichern
                aktualisiere_ticket_mieter_email(
                    ticket_id=ticket_speicherung.ticket_id,
                    mieter_email=self.email,
                )
                aktualisiere_ticket_mieter_telefon(
                    ticket_id=ticket_speicherung.ticket_id,
                    mieter_telefon=self.telefon,
                )
                # Terminoptionen + eindeutiger Token ins Ticket speichern
                token = secrets.token_urlsafe(16)
                speichere_terminoptionen(
                    ticket_id=ticket_speicherung.ticket_id,
                    option_1=self.termin_1,
                    option_2=self.termin_2,
                    option_3=self.termin_3,
                    token=token,
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

            # E-Mail
            rx.vstack(
                rx.text("Ihre E-Mail-Adresse", font_weight="500"),
                rx.input(
                    placeholder="max.mustermann@email.de",
                    on_change=State.set_email,
                    width="100%",
                    color="#1A1A1A",
                ),
                width="100%",
                align_items="start",
            ),

            # Telefon
            rx.vstack(
                rx.text("Ihre Telefonnummer", font_weight="500"),
                rx.input(
                    placeholder="z.B. 0176 12345678",
                    on_change=State.set_telefon,
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

            # Terminoptionen – nur bei Schadensmeldungen relevant
            rx.vstack(
                rx.text("Wann sind Sie erreichbar? (optional, bei Schäden)", font_weight="500"),
                rx.text(
                    "Falls Sie einen Schaden melden: Geben Sie 3 Zeitfenster an, wann ein Handwerker vorbeikommen kann.",
                    font_size="0.85em",
                    color="#6B7280",
                ),
                rx.input(
                    placeholder="z.B. Montag 17.06. zwischen 10-14 Uhr",
                    on_change=State.set_termin_1,
                    width="100%",
                    color="#1A1A1A",
                ),
                rx.input(
                    placeholder="z.B. Mittwoch 19.06. ab 15 Uhr",
                    on_change=State.set_termin_2,
                    width="100%",
                    color="#1A1A1A",
                ),
                rx.input(
                    placeholder="z.B. Freitag 21.06. ganztags",
                    on_change=State.set_termin_3,
                    width="100%",
                    color="#1A1A1A",
                ),
                width="100%",
                align_items="start",
                spacing="2",
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
    ansicht: str = "neu"
    neue_anzahl: int = 0

    def zeige_neue(self):
        self.ansicht = "neu"
        self.tickets = hole_neue_tickets()

    def zeige_laufende(self):
        self.ansicht = "laufend"
        self.tickets = hole_laufende_tickets()

    def zeige_archiv(self):
        self.ansicht = "archiv"
        self.tickets = hole_archiv_tickets()

    def zeige_alle(self):
        self.ansicht = "alle"
        self.tickets = hole_alle_tickets()

    def lade_tickets(self):
        # Immer den Zähler für neue Tickets aktualisieren
        self.neue_anzahl = zaehle_neue_tickets()
        if self.ansicht == "neu":
            self.tickets = hole_neue_tickets()
        elif self.ansicht == "laufend":
            self.tickets = hole_laufende_tickets()
        elif self.ansicht == "archiv":
            self.tickets = hole_archiv_tickets()
        else:
            self.tickets = hole_alle_tickets()

    def setze_status(self, ticket_id: int, status: str):
        aktualisiere_ticket_status(ticket_id, status)

        # E-Mails nur versenden wenn der Vermieter das Ticket freigibt
        if status == "Freigegeben":
            # Ticket aus der aktuellen Liste heraussuchen
            ticket = next((t for t in self.tickets if t[0] == ticket_id), None)
            if ticket:
                sende_email_an_mieter(
                    mieter_name=ticket[1],
                    mieter_email=ticket[2],
                    email_entwurf=ticket[7],
                )
                sende_email_an_handwerker(
                    handwerker_name=ticket[10],
                    handwerker_email=ticket[12],
                    mieter_name=ticket[1],
                    beschreibung=ticket[3],
                    prioritaet=ticket[5],
                    mieter_email=ticket[2],
                    mieter_telefon=ticket[19],
                    termin_option_1=ticket[14],
                    termin_option_2=ticket[15],
                    termin_option_3=ticket[16],
                    termin_token=ticket[18],
                )

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

        # Navigation – vier Filter-Buttons
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.text("Neu"),
                    rx.cond(
                        VermietState.neue_anzahl > 0,
                        rx.badge(
                            VermietState.neue_anzahl,
                            background="#EF4444",
                            color="white",
                            border_radius="999px",
                            padding="0 6px",
                            font_size="0.75em",
                        ),
                    ),
                    spacing="1",
                    align="center",
                ),
                on_click=VermietState.zeige_neue,
                background=rx.cond(VermietState.ansicht == "neu", "#1E3A5F", "#E2E8F0"),
                color=rx.cond(VermietState.ansicht == "neu", "white", "#1A1A1A"),
            ),
            rx.button(
                "Laufend",
                on_click=VermietState.zeige_laufende,
                background=rx.cond(VermietState.ansicht == "laufend", "#1E3A5F", "#E2E8F0"),
                color=rx.cond(VermietState.ansicht == "laufend", "white", "#1A1A1A"),
            ),
            rx.button(
                "Archiv",
                on_click=VermietState.zeige_archiv,
                background=rx.cond(VermietState.ansicht == "archiv", "#1E3A5F", "#E2E8F0"),
                color=rx.cond(VermietState.ansicht == "archiv", "white", "#1A1A1A"),
            ),
            rx.button(
                "Alle",
                on_click=VermietState.zeige_alle,
                background=rx.cond(VermietState.ansicht == "alle", "#1E3A5F", "#E2E8F0"),
                color=rx.cond(VermietState.ansicht == "alle", "white", "#1A1A1A"),
            ),
            margin="1em",
        ),

        # Ticket Liste
        rx.foreach(
            VermietState.tickets,
            lambda ticket: rx.box(
                rx.text(ticket[0], font_weight="bold", color="#1A1A1A"),
                rx.text(f"Mieter: {ticket[1]}", color="#1A1A1A"),
                rx.text(f"E-Mail Mieter: {ticket[2]}", color="#1A1A1A"),
                rx.text(f"Beschreibung: {ticket[3]}", color="#1A1A1A"),
                rx.text(f"Priorität: {ticket[5]}", color="#1A1A1A"),
                rx.text(f"Status: {ticket[8]}", color="#1A1A1A"),
                rx.text(f"Vorschlag: {ticket[6]}", color="#1A1A1A"),
                rx.text(f"E-Mail: {ticket[7]}", color="#1A1A1A"),
                rx.text(f"Handwerker: {ticket[10]}", color="#1A1A1A"),
                rx.text(f"Firma: {ticket[11]}", color="#1A1A1A"),
                rx.text(f"Fachgebiet: {ticket[13]}", color="#1A1A1A"),
                rx.text(f"Handwerker Kontakt: {ticket[12]}", color="#1A1A1A"),

                # Bestätigten Termin anzeigen – nur wenn vorhanden
                rx.cond(
                    ticket[17] != "",
                    rx.box(
                        rx.text("✓ Termin vereinbart:", font_weight="bold", color="#16A34A"),
                        rx.text(ticket[17], color="#16A34A"),
                        background="#F0FDF4",
                        border="1px solid #86EFAC",
                        border_radius="6px",
                        padding="0.5em 1em",
                        margin_top="0.5em",
                    ),
                ),

                # Aktions-Buttons je nach aktuellem Status
                rx.hstack(
                    rx.cond(
                        ticket[8] == "Neu",
                        rx.button(
                            "Freigeben & E-Mails senden",
                            on_click=VermietState.setze_status(ticket[0], "Freigegeben"),
                            background="#2E86AB",
                            color="white",
                            size="2",
                        ),
                        rx.box(),  # leerer Platzhalter wenn Status nicht 'Neu'
                    ),
                    rx.button(
                        "Abschließen",
                        on_click=VermietState.setze_status(ticket[0], "Abgeschlossen"),
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
        on_mount=VermietState.zeige_neue,
    )

class TerminState(rx.State):
    """Verwaltet die Terminbestätigungs-Seite für den Handwerker."""
    meldung: str = ""
    erfolgreich: bool = False

    def bestatige(self):
        """
        Wird beim Laden der Seite aufgerufen.
        Liest Token und Nummer aus der URL, speichert den Termin und sendet E-Mails.
        """
        token = self.router.page.params.get("token", "")
        nummer = self.router.page.params.get("nummer", "")

        if not token or not nummer:
            self.meldung = "Ungültiger Link."
            return

        ticket = hole_ticket_nach_token(token)
        if not ticket:
            self.meldung = "Dieser Link ist nicht gültig oder bereits abgelaufen."
            return

        # ticket: [0]id [1]mieter [2]mieter_email [3]beschreibung [4]prioritaet
        #         [5]handwerker_name [6]option_1 [7]option_2 [8]option_3
        #         [9]termin_bestaetigt [10]token

        # Wenn bereits bestätigt, nochmaligen Klick abfangen
        if ticket[9]:
            self.meldung = f"Dieser Termin wurde bereits bestätigt: {ticket[9]}"
            self.erfolgreich = True
            return

        # Gewählte Option anhand der Nummer auslesen
        optionen = {"1": ticket[6], "2": ticket[7], "3": ticket[8]}
        gewaehlt = optionen.get(nummer, "")

        if not gewaehlt:
            self.meldung = "Diese Terminoption existiert nicht."
            return

        # Termin in der DB speichern und Status aktualisieren
        bestatige_termin(token=token, termin=gewaehlt)
        aktualisiere_ticket_status(ticket_id=ticket[0], status="Termin vereinbart")

        # Bestätigungs-E-Mail mit Handwerker-Kontaktdaten an den Mieter senden
        # ticket: [5]handwerker_name [11]mieter_telefon [12]handwerker_firma [13]handwerker_email
        sende_terminbestaetigung(
            mieter_name=ticket[1],
            mieter_email=ticket[2],
            handwerker_name=ticket[5],
            handwerker_firma=ticket[12],
            handwerker_email=ticket[13],
            termin=gewaehlt,
        )

        self.erfolgreich = True
        self.meldung = f"Termin bestätigt: {gewaehlt}"


def termin_bestaetigen():
    """Seite die der Handwerker über den Link in der E-Mail öffnet."""
    return rx.vstack(
        rx.box(
            rx.heading("Facility Manager Agent", size="6", color="white"),
            rx.text("Terminbestätigung", color="white", opacity="0.8"),
            background="#1E3A5F",
            width="100%",
            padding="1.5em",
        ),
        rx.vstack(
            rx.cond(
                TerminState.erfolgreich,
                rx.vstack(
                    rx.icon("circle-check", size=48, color="#22C55E"),
                    rx.heading("Termin bestätigt!", size="5"),
                    rx.text(TerminState.meldung, color="#1A1A1A"),
                    rx.text(
                        "Der Mieter wurde automatisch per E-Mail informiert.",
                        color="#6B7280",
                        font_size="0.9em",
                    ),
                    align_items="center",
                    spacing="3",
                ),
                rx.vstack(
                    rx.cond(
                        TerminState.meldung != "",
                        rx.text(TerminState.meldung, color="#EF4444"),
                        rx.text("Einen Moment...", color="#6B7280"),
                    ),
                    align_items="center",
                ),
            ),
            padding="3em",
            align_items="center",
        ),
        width="100%",
        min_height="100vh",
        align_items="center",
        background="#FAFAFA",
        on_mount=TerminState.bestatige,
    )


app = rx.App(
    style={
        "color": "#1A1A1A",
        "font_family": "Aptos, sans-serif",
    }
)
app.add_page(index, route="/")
app.add_page(vermieter, route="/vermieter")
app.add_page(termin_bestaetigen, route="/termin/[token]/[nummer]")