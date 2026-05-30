"""
Schnelle Ticket-Übersicht im Terminal.

Zeigt alle Tickets direkt im Terminal an – nützlich zum Debuggen.
Starten mit: ^R
"""
from datenbank import hole_alle_tickets

tickets = hole_alle_tickets()

if not tickets:
    print("Keine Tickets vorhanden.")
else:
    for ticket in tickets:
        print(f"""
ID:                  {ticket[0]}
Mieter:              {ticket[1]}
Beschreibung:        {ticket[2]}
Kategorie:           {ticket[3]}
Priorität:           {ticket[4]}
Handlungsvorschlag:  {ticket[5]}
E-Mail Entwurf:      {ticket[6]}
Status:              {ticket[7]}
Datum:               {ticket[8]}
─────────────────────────────────
        """)