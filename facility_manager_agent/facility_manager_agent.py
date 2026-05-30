import reflex as rx
from openai import OpenAI
from dotenv import load_dotenv
from datenbank import erstelle_datenbank, speichere_ticket, hole_alle_tickets, aktualisiere_ticket_status, hole_offene_tickets, hole_archiv_tickets
import os
import sys

# Pfad zum Hauptordner hinzufügen damit datenbank.py gefunden wird
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
erstelle_datenbank()

# Mietvertrag laden
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE_DIR, "mietvertrag.txt"), "r", encoding="utf-8") as f:
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

    def sende_nachricht(self):
        if not self.name.strip() or not self.nachricht.strip():
            self.antwort = "Bitte Namen und Nachricht eingeben."
            return

        self.laden = True
        self.antwort = ""

        # Klassifikation
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Klassifiziere die Nachricht.
                    Antworte NUR mit: FRAGE, SCHADEN oder SONSTIGES"""
                },
                {"role": "user", "content": self.nachricht}
            ]
        )
        self.kategorie = response.choices[0].message.content.strip()

        if self.kategorie == "FRAGE":
            # Mietvertrag durchsuchen
            response = client.chat.completions.create(
                model="gpt-5.4-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Du bist ein hilfreicher Assistent für Mieter.
                        Beantworte Fragen nur basierend auf dem Mietvertrag.
                        Mietvertrag: {mietvertrag}"""
                    },
                    {"role": "user", "content": self.nachricht}
                ]
            )
            self.antwort = response.choices[0].message.content.strip()

        elif self.kategorie == "SCHADEN":
            # Handlungsvorschlag generieren
            response = client.chat.completions.create(
                model="gpt-5.4-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Analysiere die Schadensmeldung.
                        Format:
                        PRIORITÄT: [HOCH/MITTEL/NIEDRIG]
                        VORSCHLAG: [Vorschlag]
                        EMAIL_START
                        [E-Mail Entwurf]
                        EMAIL_END"""
                    },
                    {"role": "user", "content": f"Mieter: {self.name}\nSchaden: {self.nachricht}"}
                ]
            )

            antwort_text = response.choices[0].message.content.strip()
            prioritaet = "MITTEL"
            vorschlag = ""
            email = ""

            for zeile in antwort_text.split("\n"):
                if zeile.startswith("PRIORITÄT:"):
                    prioritaet = zeile.replace("PRIORITÄT:", "").strip()
                elif zeile.startswith("VORSCHLAG:"):
                    vorschlag = zeile.replace("VORSCHLAG:", "").strip()

            if "EMAIL_START" in antwort_text and "EMAIL_END" in antwort_text:
                email = antwort_text.split("EMAIL_START")[1].split("EMAIL_END")[0].strip()

            speichere_ticket(self.name, self.nachricht, "Schaden", prioritaet, vorschlag, email)
            self.antwort = f"Ihre Schadensmeldung wurde aufgenommen. Ticket wurde erstellt. Priorität: {prioritaet}"

        else:
            self.antwort = "Ich kann nur Fragen zum Mietvertrag beantworten oder Schäden aufnehmen."

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