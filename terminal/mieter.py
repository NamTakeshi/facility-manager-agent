"""
Terminal-Version des Mieter-Interfaces.

Zum Testen ohne Reflex zu starten.
Mieter können Fragen stellen oder Schäden melden – direkt im Terminal.
Starten mit: ^R
"""
import os
import sys

sys.path.append('..')  # einen Ordner höher schauen – damit datenbank.py gefunden wird

from openai import OpenAI
from dotenv import load_dotenv
from datenbank import erstelle_datenbank, speichere_ticket

# API Key aus .env Datei laden
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Datenbank beim Start erstellen
erstelle_datenbank()

# Mietvertrag aus Datei laden statt hardcoded
with open("../mietvertrag.txt", "r", encoding="utf-8") as f:
    mietvertrag = f.read()

# Funktionen

def klassifiziere(frage: str) -> str:
    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {
                "role": "system",
                "content": """Klassifiziere die folgende Nachricht eines Mieters.
                Antworte NUR mit einem dieser Wörter:
                - FRAGE (Mieter hat eine Frage zum Mietvertrag)
                - SCHADEN (Mieter meldet einen Schaden oder ein Problem)
                - SONSTIGES (alles andere)"""
            },
            {
                "role": "user",
                "content": frage
            }
        ]
    )
    return response.choices[0].message.content.strip()

def beantworte_frage(frage: str) -> str:
    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {
                "role": "system",
                "content": f"""Du bist ein hilfreicher Assistent für Mieter.
                Beantworte Fragen ausschließlich basierend auf dem Mietvertrag.
                Wenn die Antwort nicht im Mietvertrag steht, sage das ehrlich.

                Mietvertrag:
                {mietvertrag}"""
            },
            {
                "role": "user",
                "content": frage
            }
        ]
    )
    return response.choices[0].message.content.strip()

def erstelle_handlungsvorschlag(beschreibung: str, mieter: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {
                "role": "system",
                "content": """Du bist ein Assistent für Vermieter.
                Analysiere die Schadensmeldung und erstelle:
                1. Eine Priorität: nur HOCH, MITTEL oder NIEDRIG
                2. Einen kurzen Handlungsvorschlag (1-2 Sätze)
                3. Einen höflichen E-Mail Entwurf an den Mieter

                Antworte NUR in diesem Format ohne Abweichungen:
                PRIORITÄT: [HOCH/MITTEL/NIEDRIG]
                VORSCHLAG: [dein Vorschlag]
                EMAIL_START
                [dein E-Mail Entwurf]
                EMAIL_END"""
            },
            {
                "role": "user",
                "content": f"Mieter: {mieter}\nSchadensmeldung: {beschreibung}"
            }
        ]
    )

    antwort = response.choices[0].message.content.strip()

    # Priorität und Vorschlag auslesen
    prioritaet = "MITTEL"
    vorschlag = ""
    email = ""

    zeilen = antwort.split("\n")
    for zeile in zeilen:
        if zeile.startswith("PRIORITÄT:"):
            prioritaet = zeile.replace("PRIORITÄT:", "").strip()
        elif zeile.startswith("VORSCHLAG:"):
            vorschlag = zeile.replace("VORSCHLAG:", "").strip()

    # E-Mail zwischen EMAIL_START und EMAIL_END auslesen
    if "EMAIL_START" in antwort and "EMAIL_END" in antwort:
        email = antwort.split("EMAIL_START")[1].split("EMAIL_END")[0].strip()

    return {
        "prioritaet": prioritaet,
        "vorschlag": vorschlag,
        "email": email
    }

def verarbeite_schaden(beschreibung: str, mieter: str) -> str:
    # Handlungsvorschlag und E-Mail Entwurf generieren
    vorschlag = erstelle_handlungsvorschlag(beschreibung, mieter)

    # Ticket mit allen Infos speichern
    ticket_id = speichere_ticket(
        mieter=mieter,
        beschreibung=beschreibung,
        kategorie="Schaden",
        prioritaet=vorschlag["prioritaet"],
        handlungsvorschlag=vorschlag["vorschlag"],
        email_entwurf=vorschlag["email"]
    )

    return f"""Ticket #{ticket_id} wurde erstellt.
    Priorität: {vorschlag['prioritaet']}
    Der Vermieter wurde benachrichtigt."""

print("Willkommen beim Facility Manager Agent!")
print("Stellen Sie Fragen oder melden Sie Schäden.")
print("Zum Beenden 'exit' eingeben.\n")

# Mietername einmalig abfragen
mieter_name = input("Bitte geben Sie Ihren Namen ein: ")
print()

# Schleife damit der Nutzer mehrere Fragen stellen kann
while True:
    eingabe = input("Ihre Nachricht: ")

    if eingabe.lower() == "exit":
        print("Auf Wiedersehen!")
        break

    if eingabe.strip() == "":
        continue

    # Klassifikation
    kategorie = klassifiziere(eingabe)
    print(f"[Erkannt: {kategorie}]")

    # Je nach Kategorie unterschiedlich reagieren
    if kategorie == "FRAGE":
        antwort = beantworte_frage(eingabe)
        print("Antwort:", antwort)

    elif kategorie == "SCHADEN":
        antwort = verarbeite_schaden(eingabe, mieter_name)
        print("Antwort:", antwort)

    else:
        print("Antwort: Ich kann nur Fragen zum Mietvertrag beantworten oder Schäden aufnehmen.")

    print()