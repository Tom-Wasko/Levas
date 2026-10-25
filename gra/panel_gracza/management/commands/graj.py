"""`python manage.py graj` – migracje bazy, serwer na 127.0.0.1:8765 i przeglądarka (start.bat)."""

import threading
import webbrowser

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Uruchamia grę lokalnie: migracje, serwer i przeglądarka."

    def add_arguments(self, parser):
        parser.add_argument("--port", type=int, default=8765)
        parser.add_argument("--bez-przegladarki", action="store_true")

    def handle(self, *args, port, bez_przegladarki, **opcje):
        call_command("migrate", interactive=False, verbosity=0)
        settings.LEVAS_LOKALNIE = True  # bez logowania: lokalne konto mistrza gry (konta/)
        adres = f"http://127.0.0.1:{port}/"
        if not bez_przegladarki:
            threading.Timer(1.5, webbrowser.open, [adres]).start()
        call_command("runserver", f"127.0.0.1:{port}", use_reloader=False)
