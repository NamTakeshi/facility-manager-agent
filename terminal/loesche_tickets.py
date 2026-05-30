"""
Tool zum Löschen von Tickets aus der Datenbank.

Einzelne Tickets oder alle Tickets können gelöscht werden.
Starten mit: ^R
"""
import sys
sys.path.append('..')

from datenbank import loesche_alle_tickets, loesche_ticket

print("Was möchtest du löschen?")
print("1 → Alle Tickets löschen")
print("2 → Ein bestimmtes Ticket löschen")

auswahl = input("Auswahl: ").strip()

if auswahl == "1":
    bestaetigung = input("Sicher? Alle Tickets werden gelöscht. (ja/nein): ")
    if bestaetigung.lower() == "ja":
        loesche_alle_tickets()
elif auswahl == "2":
    ticket_id = input("Ticket ID eingeben: ").strip()
    if ticket_id.isdigit():
        loesche_ticket(int(ticket_id))