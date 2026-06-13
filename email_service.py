"""
E-Mail-Service für den Facility Manager Agent.

Versendet E-Mails an Mieter und Handwerker über die Resend API.
Wird aufgerufen wenn der Vermieter ein Ticket auf 'In Bearbeitung' setzt.
"""
import os
import resend


def _initialisiere_resend():
    """Lädt den Resend API-Key aus der Umgebung."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise ValueError("RESEND_API_KEY fehlt. Bitte in der .env Datei eintragen.")
    resend.api_key = api_key


def sende_email_an_mieter(
    mieter_name: str,
    mieter_email: str,
    email_entwurf: str,
) -> bool:
    """
    Sendet den vom Agenten erstellten E-Mail-Entwurf an den Mieter.
    Gibt True zurück wenn erfolgreich, False bei Fehler.
    """
    if not mieter_email:
        print(f"Keine E-Mail-Adresse für Mieter {mieter_name} vorhanden.")
        return False

    _initialisiere_resend()

    absender = os.getenv("ABSENDER_EMAIL", "onboarding@resend.dev")

    params = {
        "from": f"Facility Manager <{absender}>",
        "to": [mieter_email],
        "subject": "Ihre Meldung beim Facility Manager",
        # Zeilenumbrüche in HTML-Absätze umwandeln für lesbare Darstellung
        "html": email_entwurf.replace("\n", "<br>"),
    }

    try:
        resend.Emails.send(params)
        print(f"E-Mail an Mieter {mieter_name} ({mieter_email}) gesendet.")
        return True
    except Exception as fehler:
        print(f"Fehler beim Senden an Mieter: {fehler}")
        return False


def sende_email_an_handwerker(
    handwerker_name: str,
    handwerker_email: str,
    mieter_name: str,
    beschreibung: str,
    prioritaet: str,
) -> bool:
    """
    Sendet eine Auftragsbenachrichtigung an den Handwerker.
    Gibt True zurück wenn erfolgreich, False bei Fehler.
    """
    if not handwerker_email:
        print(f"Keine E-Mail-Adresse für Handwerker {handwerker_name} vorhanden.")
        return False

    _initialisiere_resend()

    absender = os.getenv("ABSENDER_EMAIL", "onboarding@resend.dev")

    inhalt = f"""
Sehr geehrte/r {handwerker_name},<br><br>
Sie wurden für einen neuen Auftrag vorgesehen. Hier sind die Details:<br><br>
<b>Mieter:</b> {mieter_name}<br>
<b>Priorität:</b> {prioritaet}<br>
<b>Schadensbeschreibung:</b><br>
{beschreibung}<br><br>
Bitte melden Sie sich zeitnah beim Vermieter zur Terminabstimmung.<br><br>
Mit freundlichen Grüßen<br>
Ihr Facility Manager Team
"""

    params = {
        "from": f"Facility Manager <{absender}>",
        "to": [handwerker_email],
        "subject": f"Neuer Auftrag – Priorität {prioritaet}",
        "html": inhalt,
    }

    try:
        resend.Emails.send(params)
        print(f"E-Mail an Handwerker {handwerker_name} ({handwerker_email}) gesendet.")
        return True
    except Exception as fehler:
        print(f"Fehler beim Senden an Handwerker: {fehler}")
        return False
