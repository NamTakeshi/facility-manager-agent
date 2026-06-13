"""
Terminal-Version des Vermieter-Dashboards.

Zum Testen ohne Reflex zu starten.
Vermieter können Tickets anzeigen und Status ändern – direkt im Terminal.
Starten mit: ^R
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from datenbank import hole_alle_tickets, aktualisiere_ticket_status

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
  Beschreibung: {ticket[3]}
  Priorität:    {ticket[5]}
  Status:       {ticket[8]}
  Datum:        {ticket[9]}
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
E-Mail Mieter:       {ticket[2]}
Beschreibung:        {ticket[3]}
Kategorie:           {ticket[4]}
Priorität:           {ticket[5]}
Status:              {ticket[8]}
Datum:               {ticket[9]}

Handlungsvorschlag:
{ticket[6]}

E-Mail Entwurf:
{ticket[7]}

Handwerker:          {ticket[10]}
Firma:               {ticket[11]}
Fachgebiet:          {ticket[13]}
Kontakt:             {ticket[12]}
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
