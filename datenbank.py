"""
Datenbank-Modul für den Facility Manager Agent.

Diese Datei verwaltet alle Verbindungen zur SQLite Datenbank.
Sie wird von der Web-App und den Terminal-Skripten importiert.
Alle Tickets werden hier gespeichert, abgerufen und aktualisiert.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'facility.db')

def erstelle_datenbank():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mieter TEXT NOT NULL,
            beschreibung TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            prioritaet TEXT DEFAULT 'Mittel',
            handlungsvorschlag TEXT,
            email_entwurf TEXT,
            status TEXT DEFAULT 'Offen',
            datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def speichere_ticket(mieter: str, beschreibung: str, kategorie: str,
                     prioritaet: str, handlungsvorschlag: str, email_entwurf: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tickets (mieter, beschreibung, kategorie, prioritaet, handlungsvorschlag, email_entwurf)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (mieter, beschreibung, kategorie, prioritaet, handlungsvorschlag, email_entwurf))

    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id

def hole_alle_tickets() -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, mieter, beschreibung, kategorie, prioritaet,
               handlungsvorschlag, email_entwurf, status, datum
        FROM tickets
        ORDER BY datum DESC
    """)

    tickets = cursor.fetchall()
    conn.close()
    return [list(ticket) for ticket in tickets]

def aktualisiere_ticket_status(ticket_id: int, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE tickets SET status = ?
        WHERE id = ?
    """, (status, ticket_id))

    conn.commit()
    conn.close()

def hole_offene_tickets() -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, mieter, beschreibung, kategorie, prioritaet,
               handlungsvorschlag, email_entwurf, status, datum
        FROM tickets
        WHERE status != 'Geschlossen'
        ORDER BY datum DESC
    """)
    tickets = cursor.fetchall()
    conn.close()
    return [list(ticket) for ticket in tickets]

def hole_archiv_tickets() -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, mieter, beschreibung, kategorie, prioritaet,
               handlungsvorschlag, email_entwurf, status, datum
        FROM tickets
        WHERE status = 'Geschlossen'
        ORDER BY datum DESC
    """)
    tickets = cursor.fetchall()
    conn.close()
    return [list(ticket) for ticket in tickets]

def loesche_alle_tickets():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets")
    conn.commit()
    conn.close()
    print("Alle Tickets gelöscht.")

def loesche_ticket(ticket_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()
    print(f"Ticket #{ticket_id} gelöscht.")