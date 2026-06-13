import os
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOKUMENTE_ORDNER = os.path.join(BASE_DIR, "dokumente")

DOKUMENTE_CACHE = {}


def lade_dokumente_in_cache():
    """Liest alle PDFs einmalig beim Start in den Arbeitsspeicher."""
    if not os.path.exists(DOKUMENTE_ORDNER):
        print(f"WARNUNG: Ordner {DOKUMENTE_ORDNER} fehlt!")
        return

    print("Lade PDFs in den Zwischenspeicher...")
    for datei in os.listdir(DOKUMENTE_ORDNER):
        if datei.lower().endswith(".pdf"):
            pfad = os.path.join(DOKUMENTE_ORDNER, datei)
            reader = PdfReader(pfad)
            text = "".join(page.extract_text() + "\n" for page in reader.pages)
            DOKUMENTE_CACHE[datei] = text
    print(f"{len(DOKUMENTE_CACHE)} Dokumente erfolgreich geladen.")


def hole_kontext_fuer_mieter(mieter_name: str) -> str:
    """Sucht den Vertrag des Mieters und die Hausordnung heraus."""
    if not DOKUMENTE_CACHE:
        lade_dokumente_in_cache()

    hausordnung_text = DOKUMENTE_CACHE.get("Hausordnung.pdf", "")
    relevanter_vertrag = ""
    vertrags_name = ""

    suchname = mieter_name.lower().strip()

    # Durchsuche alle PDFs (außer Hausordnung) nach dem Namen
    for datei, text in DOKUMENTE_CACHE.items():
        if datei.lower() == "hausordnung.pdf":
            continue

        if suchname and suchname in text.lower():
            relevanter_vertrag = text
            vertrags_name = datei
            break

    # NEU: Strikte Blockade, wenn der Mieter nicht gefunden wurde
    if not relevanter_vertrag:
        return (
            f"SYSTEMHINWEIS: Es konnte kein Mietvertrag für den Namen '{mieter_name}' gefunden werden. "
            "Du erhältst KEINEN Zugriff auf die Dokumente. "
            f"Antworte dem Nutzer ausschließlich folgendes: 'Entschuldigung, aber ich konnte keinen Mietvertrag unter dem Namen \"{mieter_name}\" finden. Bitte überprüfen Sie die genaue Schreibweise Ihres Vor- und Nachnamens, wie er im Vertrag steht.'"
        )

    # Wenn der Mieter gefunden wurde, bauen wir den Text ganz normal zusammen
    kontext = f"--- ALLGEMEINE HAUSORDNUNG ---\n{hausordnung_text}\n\n"
    kontext += f"--- SPEZIFISCHER MIETVERTRAG FÜR: {mieter_name.upper()} ({vertrags_name}) ---\n{relevanter_vertrag}\n"

    return kontext