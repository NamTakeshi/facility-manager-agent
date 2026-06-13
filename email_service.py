"""
E-Mail-Service für den Facility Manager Agent.

Versendet E-Mails an Mieter und Handwerker über die Resend API.
Wird aufgerufen wenn der Vermieter ein Ticket auf 'In Bearbeitung' setzt,
oder wenn der Handwerker einen Termin über den Bestätigungs-Link wählt.
"""
import os
import resend


def _initialisiere_resend():
    """Lädt den Resend API-Key aus der Umgebung."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise ValueError("RESEND_API_KEY fehlt. Bitte in der .env Datei eintragen.")
    resend.api_key = api_key


def _html_rahmen(inhalt: str) -> str:
    """Bettet den E-Mail-Inhalt in einen einheitlichen HTML-Rahmen ein."""
    return f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #1A1A1A;">
  <div style="background: #1E3A5F; padding: 24px 32px; border-radius: 8px 8px 0 0;">
    <p style="color: white; margin: 0; font-size: 13px; opacity: 0.8;">Facility Manager Agent</p>
  </div>
  <div style="background: white; padding: 32px; border: 1px solid #E2E8F0; border-top: none; border-radius: 0 0 8px 8px;">
    {inhalt}
    <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 28px 0;">
    <p style="color: #9CA3AF; font-size: 12px; margin: 0;">
      Diese E-Mail wurde automatisch vom Facility Manager Agent versendet.
    </p>
  </div>
</div>
"""


def _kontakt_block(titel: str, name: str, firma: str = "", email: str = "", telefon: str = "") -> str:
    """Erstellt einen einheitlichen Kontakt-Block für E-Mails."""
    zeilen = f"<p style='margin: 0 0 4px 0;'><b>{name}</b></p>"
    if firma:
        zeilen += f"<p style='margin: 0 0 4px 0; color: #4B5563;'>{firma}</p>"
    if email:
        zeilen += f"<p style='margin: 0 0 4px 0;'>📧 <a href='mailto:{email}' style='color: #1E3A5F;'>{email}</a></p>"
    if telefon:
        zeilen += f"<p style='margin: 0;'>📞 <a href='tel:{telefon}' style='color: #1E3A5F;'>{telefon}</a></p>"

    return f"""
<div style="background: #F8FAFC; border-left: 4px solid #1E3A5F;
            padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 16px 0;">
  <p style="margin: 0 0 8px 0; font-size: 12px; text-transform: uppercase;
            letter-spacing: 0.05em; color: #6B7280;">{titel}</p>
  {zeilen}
</div>
"""


def sende_email_an_mieter(
    mieter_name: str,
    mieter_email: str,
    email_entwurf: str,
) -> bool:
    """
    Sendet den vom Agenten erstellten E-Mail-Entwurf an den Mieter.
    Wird aufgerufen wenn der Vermieter das Ticket auf 'In Bearbeitung' setzt.
    """
    if not mieter_email:
        print(f"Keine E-Mail-Adresse für Mieter {mieter_name} vorhanden.")
        return False

    _initialisiere_resend()
    absender = os.getenv("ABSENDER_EMAIL", "onboarding@resend.dev")

    inhalt = f"""
<h2 style="margin: 0 0 20px 0; color: #1E3A5F;">Ihre Meldung wird bearbeitet</h2>
<p>{email_entwurf.replace(chr(10), '<br>')}</p>
"""

    params = {
        "from": f"Facility Manager <{absender}>",
        "to": [mieter_email],
        "subject": "Ihre Meldung wird bearbeitet",
        "html": _html_rahmen(inhalt),
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
    mieter_email: str = "",
    mieter_telefon: str = "",
    termin_option_1: str = "",
    termin_option_2: str = "",
    termin_option_3: str = "",
    termin_token: str = "",
) -> bool:
    """
    Sendet eine Auftragsbenachrichtigung an den Handwerker.
    Enthält die 3 Terminoptionen als Buttons und die Kontaktdaten des Mieters.
    """
    if not handwerker_email:
        print(f"Keine E-Mail-Adresse für Handwerker {handwerker_name} vorhanden.")
        return False

    _initialisiere_resend()
    absender = os.getenv("ABSENDER_EMAIL", "onboarding@resend.dev")
    basis_url = os.getenv("BASIS_URL", "http://localhost:3000")

    # Priorität farblich hervorheben
    prioritaet_farbe = {"HOCH": "#DC2626", "MITTEL": "#D97706", "NIEDRIG": "#16A34A"}.get(prioritaet, "#6B7280")

    # Terminoptionen als klickbare Buttons
    termin_buttons = ""
    for text, nummer in [(termin_option_1, "1"), (termin_option_2, "2"), (termin_option_3, "3")]:
        if text.strip():
            link = f"{basis_url}/termin/{termin_token}/{nummer}"
            termin_buttons += f"""
<a href="{link}" style="display:block; margin: 8px 0; padding: 12px 20px;
   background: #1E3A5F; color: white; text-decoration: none;
   border-radius: 6px; font-size: 14px;">
  ✓ &nbsp; {text}
</a>"""

    if not termin_buttons:
        termin_buttons = "<p style='color: #6B7280;'>Keine Terminoptionen angegeben – bitte direkt Kontakt aufnehmen.</p>"

    inhalt = f"""
<h2 style="margin: 0 0 20px 0; color: #1E3A5F;">Neuer Reparaturauftrag</h2>
<p>Guten Tag {handwerker_name},</p>
<p>Sie wurden für einen neuen Auftrag eingeplant. Bitte bestätigen Sie einen der vorgeschlagenen Termine.</p>

<div style="background: #FEF2F2; border: 1px solid {prioritaet_farbe};
            padding: 12px 16px; border-radius: 6px; margin: 20px 0;">
  <span style="color: {prioritaet_farbe}; font-weight: bold;">Priorität: {prioritaet}</span>
</div>

<p><b>Schadensbeschreibung:</b></p>
<p style="background: #F8FAFC; padding: 12px 16px; border-radius: 6px;">{beschreibung}</p>

<p style="margin-top: 24px;"><b>Bitte wählen Sie einen Termin:</b></p>
{termin_buttons}

{_kontakt_block(
    titel="Kontakt Mieter – falls kein Termin passt",
    name=mieter_name,
    email=mieter_email,
    telefon=mieter_telefon,
)}

<p style="color: #6B7280; font-size: 13px; margin-top: 20px;">
  Nach Ihrer Bestätigung erhalten Sie und der Mieter automatisch eine Terminbestätigung per E-Mail.
</p>
"""

    params = {
        "from": f"Facility Manager <{absender}>",
        "to": [handwerker_email],
        "subject": f"Neuer Auftrag [{prioritaet}] – Bitte Termin bestätigen",
        "html": _html_rahmen(inhalt),
    }

    try:
        resend.Emails.send(params)
        print(f"E-Mail an Handwerker {handwerker_name} ({handwerker_email}) gesendet.")
        return True
    except Exception as fehler:
        print(f"Fehler beim Senden an Handwerker: {fehler}")
        return False


def sende_terminbestaetigung(
    mieter_name: str,
    mieter_email: str,
    handwerker_name: str,
    handwerker_firma: str,
    handwerker_email: str,
    termin: str,
) -> bool:
    """
    Sendet eine Terminbestätigung mit Handwerker-Kontaktdaten an den Mieter.
    Wird aufgerufen sobald der Handwerker einen Termin über den Link bestätigt.
    """
    if not mieter_email:
        print(f"Keine E-Mail für Terminbestätigung an {mieter_name}.")
        return False

    _initialisiere_resend()
    absender = os.getenv("ABSENDER_EMAIL", "onboarding@resend.dev")

    inhalt = f"""
<h2 style="margin: 0 0 20px 0; color: #16A34A;">✓ Termin bestätigt</h2>
<p>Guten Tag {mieter_name},</p>
<p>Ihr Handwerkertermin wurde bestätigt. Bitte sorgen Sie dafür, dass jemand zu diesem Zeitpunkt in der Wohnung ist.</p>

<div style="background: #F0FDF4; border: 2px solid #16A34A;
            padding: 16px 20px; border-radius: 8px; margin: 24px 0; text-align: center;">
  <p style="margin: 0; font-size: 13px; color: #6B7280;">Bestätigter Termin</p>
  <p style="margin: 8px 0 0 0; font-size: 20px; font-weight: bold; color: #15803D;">{termin}</p>
</div>

{_kontakt_block(
    titel="Ihr Handwerker",
    name=handwerker_name,
    firma=handwerker_firma,
    email=handwerker_email,
)}

<p style="color: #6B7280; font-size: 13px;">
  Falls Sie den Termin nicht wahrnehmen können, wenden Sie sich bitte rechtzeitig
  direkt an den Handwerker.
</p>
"""

    params = {
        "from": f"Facility Manager <{absender}>",
        "to": [mieter_email],
        "subject": f"✓ Terminbestätigung: {termin}",
        "html": _html_rahmen(inhalt),
    }

    try:
        resend.Emails.send(params)
        print(f"Terminbestätigung an {mieter_name} ({mieter_email}) gesendet.")
        return True
    except Exception as fehler:
        print(f"Fehler beim Senden der Terminbestätigung: {fehler}")
        return False
