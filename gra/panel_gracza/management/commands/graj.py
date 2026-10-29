"""`python manage.py graj` – migracje bazy, serwer na 127.0.0.1:8765 i przeglądarka (start.bat)."""

import socket
import threading
import webbrowser

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


def port_zajety(port: int) -> bool:
    """Czy na 127.0.0.1:port już ktoś słucha. Windows pozwala dwóm serwerom słuchać na tym samym
    porcie i rozdziela między nie zapytania – stary serwer (nieaktualny kod na bazie po nowych
    migracjach) psuje wtedy np. tworzenie gier."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


class Command(BaseCommand):
    help = "Uruchamia grę lokalnie: migracje, serwer i przeglądarka."

    def add_arguments(self, parser):
        parser.add_argument("--port", type=int, default=8765)
        parser.add_argument("--bez-przegladarki", action="store_true")

    def handle(self, *args, port, bez_przegladarki, **opcje):
        if port_zajety(port):
            raise CommandError(
                f"Port {port} jest zajęty – Levas już działa w innym oknie. Zamknij wszystkie "
                "okna serwera gry (start.bat) i uruchom start.bat ponownie.")
        call_command("migrate", interactive=False, verbosity=0)
        settings.LEVAS_LOKALNIE = True  # bez logowania: lokalne konto mistrza gry (konta/)
        adres = f"http://127.0.0.1:{port}/"
        if not bez_przegladarki:
            threading.Timer(1.5, webbrowser.open, [adres]).start()
        # /static/ przez levas/statyczne.py (wersja w adresie), nie przez runserver
        call_command("runserver", f"127.0.0.1:{port}", use_reloader=False, use_static_handler=False)
