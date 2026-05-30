"""
Terminal-Version des Vermieter-Dashboards.

Zum Testen ohne Reflex zu starten.
Vermieter können Tickets anzeigen und Status ändern – direkt im Terminal.
Starten mit: ^R
"""
import os
import sys

sys.path.append('..')  # einen Ordner höher schauen

from openai import OpenAI
from dotenv import load_dotenv
from datenbank import hole_alle_tickets, aktualisiere_ticket_status

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def zeige_tickets():
    tickets = hole_alle_tickets()

    if not tickets:
        print("Keine Tickets vorhanden.")
        return

    for ticket in tickets:
        print(f"""
┌─────────────────────────────────────┐
  ID:           {ticket[0]}
  Mieter:       {ticket[1]}
  Beschreibung: {ticket[2]}
  Priorität:    {ticket[4]}
  Status:       {ticket[7]}
  Datum:        {ticket[8]}
└─────────────────────────────────────┘""")

def zeige_ticket_detail(ticket_id: int):
    tickets = hole_alle_tickets()
    ticket = next((t for t in tickets if t[0] == ticket_id), None)

    if not ticket:
        print("Ticket nicht gefunden.")
        return

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ID:                  {ticket[0]}
Mieter:              {ticket[1]}
Beschreibung:        {ticket[2]}
Kategorie:           {ticket[3]}
Priorität:           {ticket[4]}
Status:              {ticket[7]}
Datum:               {ticket[8]}

Handlungsvorschlag:
{ticket[5]}

E-Mail Entwurf:
{ticket[6]}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""")

    return ticket

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  Willkommen im Vermieter Dashboard")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

while True:
    print("""
Was möchten Sie tun?
1 → Alle Tickets anzeigen
2 → Ticket Details anzeigen
3 → Ticket Status ändern
4 → Beenden
    """)

    auswahl = input("Ihre Auswahl: ").strip()

    # ── Alle Tickets anzeigen ──
    if auswahl == "1":
        zeige_tickets()

    # ── Ticket Details anzeigen ──
    elif auswahl == "2":
        ticket_id = input("Ticket ID eingeben: ").strip()
        if ticket_id.isdigit():
            zeige_ticket_detail(int(ticket_id))
        else:
            print("Bitte eine gültige ID eingeben.")

    # ── Ticket Status ändern ──
    elif auswahl == "3":
        ticket_id = input("Ticket ID eingeben: ").strip()
        if ticket_id.isdigit():
            ticket = zeige_ticket_detail(int(ticket_id))
            if ticket:
                print("""
                Neuer Status:
                1 → In Bearbeitung
                2 → Geschlossen
                                """)
                status_auswahl = input("Ihre Auswahl: ").strip()
                if status_auswahl == "1":
                    aktualisiere_ticket_status(int(ticket_id), "In Bearbeitung")
                    print("Status auf 'In Bearbeitung' gesetzt.")
                elif status_auswahl == "2":
                    aktualisiere_ticket_status(int(ticket_id), "Geschlossen")
                    print("Status auf 'Geschlossen' gesetzt.")
                else:
                    print("Ungültige Auswahl.")
        else:
            print("Bitte eine gültige ID eingeben.")

    # ── Beenden ──
    elif auswahl == "4":
        print("Auf Wiedersehen!")
        break

    else:
        print("Ungültige Auswahl – bitte 1, 2, 3 oder 4 eingeben.")