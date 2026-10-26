"""Zamyka rundy gier, których termin z harmonogramu minął (gry/harmonogram.py).

Raz: `python manage.py zamykaj_rundy` – np. z Harmonogramu zadań Windows co 5 minut.
W pętli: `python manage.py zamykaj_rundy --petla 60` – sprawdza co 60 s, aż do Ctrl+C.
"""

import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from gry.harmonogram import zamknij_spoznione


class Command(BaseCommand):
    help = "Zamyka rundy gier, których termin zamknięcia z harmonogramu minął."

    def add_arguments(self, parser):
        parser.add_argument(
            "--petla", type=int, metavar="SEKUNDY", help="sprawdzaj w pętli co SEKUNDY"
        )

    def handle(self, *args, petla=None, **opcje):
        while True:
            for w in zamknij_spoznione():
                kiedy = timezone.localtime().strftime("%Y-%m-%d %H:%M")
                if "blad" in w:
                    self.stderr.write(f"{kiedy} {w['gra']}: błąd – {w['blad']}")
                else:
                    gra = f"{w['nazwa']} ({w['gra']})"
                    self.stdout.write(f"{kiedy} {gra}: runda {w['runda']} zamknięta")
            if not petla:
                return
            time.sleep(max(petla, 5))
