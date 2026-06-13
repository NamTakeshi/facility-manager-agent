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
            mieter_email TEXT DEFAULT '',
            beschreibung TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            prioritaet TEXT DEFAULT 'Mittel',
            handlungsvorschlag TEXT,
            email_entwurf TEXT,
            status TEXT DEFAULT 'Offen',
            datum TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            handwerker_name TEXT,
            handwerker_firma TEXT,
            handwerker_email TEXT,
            handwerker_fachgebiet TEXT
        )
    """)
    # Tabelle für Handwerker erstellen
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS handwerker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                firma TEXT,
                fachgebiet TEXT NOT NULL,
                email TEXT,
                telefon TEXT,
                bewertung INTEGER DEFAULT 5
            )
        """)


    conn.commit()
    conn.close()

def speichere_ticket(
    mieter: str,
    beschreibung: str,
    kategorie: str,
    prioritaet: str,
    handlungsvorschlag: str,
    email_entwurf: str,
    mieter_email: str = "",
    handwerker_name: str = "",
    handwerker_firma: str = "",
    handwerker_email: str = "",
    handwerker_fachgebiet: str = "",
) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tickets (
            mieter, mieter_email, beschreibung, kategorie, prioritaet,
            handlungsvorschlag, email_entwurf,
            handwerker_name, handwerker_firma,
            handwerker_email, handwerker_fachgebiet
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        mieter, mieter_email, beschreibung, kategorie, prioritaet,
        handlungsvorschlag, email_entwurf,
        handwerker_name, handwerker_firma,
        handwerker_email, handwerker_fachgebiet
    ))
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id

def hole_alle_tickets() -> list:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # FEHLER GEFUNDEN (behoben): handwerker_* Spalten fehlten im SELECT.
    # ticket[9..12] wurden im Dashboard referenziert, existierten aber nicht.
    cursor.execute("""
        SELECT id, mieter, mieter_email, beschreibung, kategorie, prioritaet,
               handlungsvorschlag, email_entwurf, status, datum,
               handwerker_name, handwerker_firma, handwerker_email,
               handwerker_fachgebiet
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
        SELECT id, mieter, mieter_email, beschreibung, kategorie, prioritaet,
               handlungsvorschlag, email_entwurf, status, datum,
               handwerker_name, handwerker_firma, handwerker_email,
               handwerker_fachgebiet
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
        SELECT id, mieter, mieter_email, beschreibung, kategorie, prioritaet,
               handlungsvorschlag, email_entwurf, status, datum,
               handwerker_name, handwerker_firma, handwerker_email,
               handwerker_fachgebiet
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

# Handwerker Management
def fuege_dummy_handwerker_ein():
    """Fügt Beispiel-Handwerker ein falls Tabelle leer ist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Nur einfügen wenn Tabelle leer
    cursor.execute("SELECT COUNT(*) FROM handwerker")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    handwerker = [
        ("Klaus Müller", "Heizung & Sanitär GmbH", "Heizung", "mueller@heizung.de", "030-111111", 5),
        ("Anna Weber", "Weber Sanitär", "Sanitär", "weber@sanitaer.de", "030-222222", 4),
        ("Tom Fischer", "Fischer Elektro", "Elektro", "fischer@elektro.de", "030-333333", 5),
        ("Maria Schmidt", "Schmidt Bau", "Schimmel", "schmidt@bau.de", "030-444444", 4),
        ("Peter Klein", "Klein Reparatur", "Allgemein", "klein@reparatur.de", "030-555555", 3),
    ]

    cursor.executemany("""
        INSERT INTO handwerker (name, firma, fachgebiet, email, telefon, bewertung)
        VALUES (?, ?, ?, ?, ?, ?)
    """, handwerker)

    conn.commit()
    conn.close()
    print("Dummy Handwerker eingefügt.")


def suche_handwerker_nach_fachgebiet(fachgebiet: str) -> list:
    """Sucht Handwerker nach Fachgebiet, sortiert nach Bewertung."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, firma, fachgebiet, email, telefon, bewertung
        FROM handwerker
        WHERE fachgebiet LIKE ?
        ORDER BY bewertung DESC
        LIMIT 3
    """, (f"%{fachgebiet}%",))

    handwerker = cursor.fetchall()
    conn.close()
    return [list(h) for h in handwerker]


def hole_alle_handwerker() -> list:
    """Gibt alle Handwerker zurück."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, firma, fachgebiet, email, telefon, bewertung
        FROM handwerker
        ORDER BY fachgebiet, bewertung DESC
    """)

    handwerker = cursor.fetchall()
    conn.close()
    return [list(h) for h in handwerker]

def aktualisiere_ticket_mieter_email(ticket_id: int, mieter_email: str):
    """Trägt die E-Mail-Adresse des Mieters nachträglich ins Ticket ein."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tickets SET mieter_email = ? WHERE id = ?
    """, (mieter_email, ticket_id))
    conn.commit()
    conn.close()

def aktualisiere_ticket_handwerker(
    ticket_id: int,
    handwerker_name: str,
    handwerker_firma: str,
    handwerker_email: str,
    handwerker_fachgebiet: str,
):
    """Fügt Handwerker-Infos zu einem bestehenden Ticket hinzu."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE tickets
        SET handwerker_name = ?,
            handwerker_firma = ?,
            handwerker_email = ?,
            handwerker_fachgebiet = ?
        WHERE id = ?
    """, (handwerker_name, handwerker_firma, handwerker_email, handwerker_fachgebiet, ticket_id))
    conn.commit()
    conn.close()