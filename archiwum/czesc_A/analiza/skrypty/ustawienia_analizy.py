r"""Ustawienia Django do analizy A2: osobna baza w archiwum/czesc_A/analiza/ (poza gitem), żeby partie
analizy nie trafiały na listę gier na komputerze autora. Uruchomienie z katalogu gra/:

    set PYTHONPATH=..\raporty\analiza\skrypty
    .venv\Scripts\python manage.py graj --port 8766 --bez-przegladarki --settings ustawienia_analizy
"""

from pathlib import Path

from levas.settings import *  # noqa: F403

DATABASES["default"]["NAME"] = Path(__file__).resolve().parent.parent / "analiza.sqlite3"  # noqa: F405
