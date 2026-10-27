"""`python manage.py instrukcja_pdf` – INSTRUKCJA.md → INSTRUKCJA.pdf (strona „Jak grać” drukowana
przeglądarką Edge albo Chrome bez okna; czcionki z Google Fonts, gdy jest internet)."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

from panel_gracza.instrukcja import instrukcja

PRZEGLADARKI = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "msedge", "google-chrome", "chromium", "chrome",
]


def przegladarka() -> str | None:
    for p in PRZEGLADARKI:
        if Path(p).is_file() or shutil.which(p):
            return p
    return None


class Command(BaseCommand):
    help = "Tworzy INSTRUKCJA.pdf z INSTRUKCJA.md (wymaga Edge albo Chrome)."

    def add_arguments(self, parser):
        parser.add_argument("--plik", default=str(Path(settings.BASE_DIR) / "INSTRUKCJA.pdf"))

    def handle(self, *args, plik, **opcje):
        exe = przegladarka()
        if exe is None:
            raise CommandError("Nie znaleziono Edge ani Chrome – PDF drukuje przeglądarka.")
        kontekst = instrukcja() | {"powrot": "/", "powrot_tekst": ""}
        strona = render_to_string("panel_gracza/jak_grac.html", kontekst)
        with tempfile.TemporaryDirectory() as tmp:
            html = Path(tmp) / "instrukcja.html"
            html.write_text(strona, encoding="utf-8")
            wynik = Path(plik).resolve()
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                            f"--user-data-dir={Path(tmp) / 'profil'}", "--virtual-time-budget=8000",
                            f"--print-to-pdf={wynik}", html.as_uri()],
                           check=True, capture_output=True, timeout=120)
        if not wynik.is_file():
            raise CommandError("Przeglądarka nie utworzyła PDF-a.")
        self.stdout.write(f"Zapisano {wynik} ({wynik.stat().st_size // 1024} KB).")
