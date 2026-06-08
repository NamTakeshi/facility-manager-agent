import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from datenbank import hole_alle_handwerker, fuege_dummy_handwerker_ein

fuege_dummy_handwerker_ein()
handwerker = hole_alle_handwerker()

for h in handwerker:
    print(f"""
ID:         {h[0]}
Name:       {h[1]}
Firma:      {h[2]}
Fachgebiet: {h[3]}
Email:      {h[4]}
Telefon:    {h[5]}
Bewertung:  {h[6]}/5
─────────────────
    """)