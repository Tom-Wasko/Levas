"""`python manage.py staly_link` – ustawia stały link do gry z hostuj.bat (staly_link.bat).

Pyta o adres strony (np. https://levas.szkola.pl) i dane konta FTP hostingu, na którym ten adres
stoi, zapisuje je w `lokalne.json` (poza gitem) i sprawdza połączenie, wgrywając stronę „gra
wyłączona”. Potem hostuj.bat przy każdym starcie kieruje ten adres na bieżący tunel.
"""

import ftplib
from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from panel_gracza import staly_link


def zapytaj(pytanie: str, domyslnie: str = "") -> str:
    podpowiedz = f" [{domyslnie}]" if domyslnie else ""
    return input(f"{pytanie}{podpowiedz}: ").strip() or domyslnie


class Command(BaseCommand):
    help = "Ustawia stały link (adres na zwykłym hostingu WWW) do gry z hostuj.bat."

    def add_arguments(self, parser):
        parser.add_argument("--usun", action="store_true", help="wyłącza stały link")

    def handle(self, *args, usun, **opcje):
        if usun:
            staly_link.zapisz_konfiguracje(None)
            print("Stały link wyłączony (dane FTP usunięte z lokalne.json).")
            return
        stary = staly_link.konfiguracja() or {}
        print("Stały link: adres Twojej strony będzie przekierowywał na grę z hostuj.bat.\n"
              "Potrzebne konto FTP, którego katalog to katalog tej strony na hostingu.\n")
        adres = zapytaj("Adres strony (np. https://levas.szkola.pl)", stary.get("adres", ""))
        if adres and not adres.startswith(("http://", "https://")):
            adres = "https://" + adres
        konfig = {
            "adres": adres.rstrip("/"),
            "host": zapytaj("Serwer FTP (np. serwer12345.lh.pl)", stary.get("host", "")),
            "login": zapytaj("Login FTP", stary.get("login", "")),
            "haslo": getpass("Hasło FTP (nie widać go przy pisaniu; Enter = bez zmian): ")
            or stary.get("haslo", ""),
            "katalog": zapytaj("Katalog na serwerze (Enter = katalog startowy konta)",
                               stary.get("katalog", "")),
        }
        if not (konfig["host"] and konfig["login"] and konfig["haslo"]):
            raise CommandError("Podaj serwer, login i hasło FTP.")
        print("Sprawdzam połączenie i wgrywam stronę „gra wyłączona”...", flush=True)
        try:
            staly_link.wgraj(konfig, None)
        except (OSError, ftplib.Error) as blad:
            raise CommandError(
                f"Nie udało się połączyć z {konfig['host']}: {blad}\n"
                "Sprawdź serwer, login, hasło i katalog (dane niezapisane).") from blad
        staly_link.zapisz_konfiguracje(konfig)
        print(f"Gotowe. {konfig['adres'] or konfig['host']} pokazuje teraz „gra wyłączona”;\n"
              "po uruchomieniu hostuj.bat będzie prowadzić do gry.")
