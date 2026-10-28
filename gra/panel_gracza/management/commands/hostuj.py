"""`python manage.py hostuj` – gra z kolegami przez internet (hostuj.bat).

Serwer na tym komputerze z logowaniem (bez automatycznego konta mistrza gry z `graj` – przez tunel
każde zapytanie przychodzi z 127.0.0.1) i darmowy tunel Cloudflare: adres
https://<losowe-slowa>.trycloudflare.com, bez konta Cloudflare i bez ustawień routera. Adres zmienia
się przy każdym uruchomieniu. Program `cloudflared.exe` pobiera się raz do `narzedzia/`.
"""

import re
import shutil
import subprocess
import threading
import urllib.request
import webbrowser
from collections import deque
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from konta.role import MISTRZ_GRY

from .graj import port_zajety

POBIERZ_CLOUDFLARED = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-windows-amd64.exe"
)
ADRES_TUNELU = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def adres_tunelu(linia: str) -> str | None:
    """Adres tunelu z linii, którą cloudflared wypisuje po starcie (albo None)."""
    znalezione = ADRES_TUNELU.search(linia)
    return znalezione.group(0) if znalezione else None


def cloudflared() -> str:
    """Ścieżka do cloudflared: z PATH albo pobrany raz do `narzedzia/`."""
    if sciezka := shutil.which("cloudflared"):
        return sciezka
    plik = settings.BASE_DIR / "narzedzia" / "cloudflared.exe"
    if not plik.exists():
        print("Pierwsze uruchomienie: pobieram cloudflared (ok. 60 MB, tylko raz)...")
        plik.parent.mkdir(exist_ok=True)
        czesciowy = plik.with_suffix(".pobieranie")
        urllib.request.urlretrieve(POBIERZ_CLOUDFLARED, czesciowy)
        czesciowy.replace(plik)
    return str(plik)


def mistrzowie_z_haslem() -> list[str]:
    mg = get_user_model().objects.filter(Q(is_superuser=True) | Q(groups__name=MISTRZ_GRY))
    return [u.username for u in mg.distinct() if u.has_usable_password()]


class Command(BaseCommand):
    help = "Gra z kolegami przez internet: serwer z logowaniem i tunel Cloudflare."

    def add_arguments(self, parser):
        parser.add_argument("--port", type=int, default=8765)
        parser.add_argument("--bez-przegladarki", action="store_true")

    def handle(self, *args, port, bez_przegladarki, **opcje):
        if port_zajety(port):
            raise CommandError(
                f"Port {port} jest zajęty – Levas już działa w innym oknie. Zamknij wszystkie "
                "okna serwera gry (start.bat, hostuj.bat) i uruchom hostuj.bat ponownie.")
        call_command("migrate", interactive=False, verbosity=0)
        mistrzowie = mistrzowie_z_haslem()
        if not mistrzowie:
            print("Przez internet trzeba się logować. Załóż swoje konto mistrza gry.")
            login = input("Twój login: ").strip() or "mg"
            call_command("konto", login, mg=True)
            mistrzowie = [login]

        url, tunel = self.tunel(port)
        try:
            # przez tunel: adres z https, formularze z tego adresu, bez stron diagnostycznych Django
            settings.ALLOWED_HOSTS.append(urlparse(url).hostname)
            settings.CSRF_TRUSTED_ORIGINS = [url]
            settings.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
            settings.DEBUG = False
            lokalny = f"http://127.0.0.1:{port}/"
            print(
                "\n" + "=" * 70
                + f"\n  Link dla kolegów:   {url}"
                + f"\n  Ty (na tym komputerze): {lokalny}  – login: {', '.join(mistrzowie)}"
                + "\n\n  Konta kolegów: panel mistrza gry -> gra -> zakładka Drużyny."
                + "\n  Zamknięcie tego okna kończy grę i wyłącza link."
                + "\n" + "=" * 70 + "\n",
                flush=True,
            )
            if not bez_przegladarki:
                threading.Timer(1.5, webbrowser.open, [lokalny]).start()
            call_command(
                "runserver", f"127.0.0.1:{port}", use_reloader=False, insecure_serving=True
            )
        finally:
            tunel.terminate()

    def tunel(self, port: int) -> tuple[str, subprocess.Popen]:
        """Uruchamia tunel i czeka (do minuty), aż cloudflared poda adres."""
        print("Uruchamiam tunel Cloudflare...", flush=True)
        tunel = subprocess.Popen(
            [cloudflared(), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, errors="replace",
        )
        ostatnie, znaleziony = deque(maxlen=15), {}
        gotowy = threading.Event()

        def czytaj():  # czyta do końca, żeby pełny bufor nie zatrzymał cloudflared
            for linia in tunel.stderr:
                ostatnie.append(linia.rstrip())
                if not gotowy.is_set() and (url := adres_tunelu(linia)):
                    znaleziony["url"] = url
                    gotowy.set()
            gotowy.set()

        threading.Thread(target=czytaj, daemon=True).start()
        gotowy.wait(60)
        if "url" not in znaleziony:
            tunel.terminate()
            raise CommandError(
                "Tunel Cloudflare nie wystartował. Ostatnie komunikaty cloudflared:\n"
                + "\n".join(ostatnie))
        return znaleziony["url"], tunel
