"""
Schnelle Ticket-Übersicht im Terminal.

Zeigt alle Tickets direkt im Terminal an – nützlich zum Debuggen.
Starten mit: ^R
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

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
Handwerker:          {ticket[9] or '–'}
Firma:               {ticket[10] or '–'}
Handwerker E-Mail:   {ticket[11] or '–'}
Fachgebiet:          {ticket[12] or '–'}
─────────────────────────────────
        """)