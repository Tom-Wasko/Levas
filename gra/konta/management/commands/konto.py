"""`python manage.py konto <login> [--mg] [--imie ...]` – zakłada albo zmienia konto.

Hasło: opcja --haslo albo pytanie w konsoli. Adres e-mail zamiast loginu wskazuje istniejące konto
(np. założone pierwszym logowaniem kontem Microsoft) – tak nadaje się mu rolę mistrza gry."""

from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from konta.role import nadaj_mg


class Command(BaseCommand):
    help = "Zakłada konto ucznia albo mistrza gry (--mg) z własnym loginem i hasłem."

    def add_arguments(self, parser):
        parser.add_argument("login")
        parser.add_argument("--mg", action="store_true", help="rola mistrza gry")
        parser.add_argument("--uczen", action="store_true", help="odbiera rolę mistrza gry")
        parser.add_argument("--imie", default="", help="imię i nazwisko widoczne w grze")
        parser.add_argument("--haslo", help="hasło (bez tej opcji – pytanie w konsoli)")

    def handle(self, *args, login, mg, uczen, imie, haslo, **opcje):
        uzytkownicy = get_user_model().objects
        po_mailu = uzytkownicy.filter(email__iexact=login).first() if "@" in login else None
        user, nowe = (po_mailu, False) if po_mailu else uzytkownicy.get_or_create(username=login)
        if imie:
            user.first_name, _, user.last_name = imie.partition(" ")
        if nowe or haslo is not None:
            haslo = haslo if haslo is not None else getpass("Hasło: ")
            if len(haslo) < 6:
                raise CommandError("Hasło musi mieć co najmniej 6 znaków.")
            user.set_password(haslo)
        user.save()
        if mg or uczen:
            nadaj_mg(user, mg)
        self.stdout.write(f"{'Założono' if nowe else 'Zmieniono'} konto {user.username}.")
