"""UF17: gra pokazowa – pełna gra rozegrana przez boty, do obejrzenia w „Twoich grach”.

`python manage.py gra_pokazowa` usuwa starą grę „Pokazowa”, zakłada nową (domyślnie 18 rund,
4 boty i drużyna „Pokazowa”, za którą decyduje dobry bot), przypisuje do drużyny konta mistrzów
gry (albo `--konto LOGIN`) i rozgrywa wszystkie rundy tak jak zamykanie rundy
(gry/harmonogram.py: `serwisy.zmiana` + `przelicz`). Decyzje drużyny „Pokazowa” idą tą samą drogą
co decyzje graczy (`ustaw_decyzje` + `wyslij`). Odtwarzać po każdej większej zmianie gry
albo danych.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from gry import serwisy
from gry.models import Druzyna, Gra
from konta.role import MISTRZ_GRY
from silnik import Gra as GraSilnika
from silnik.boty import decyzje_bota
from silnik.dane import dane_domyslne

NAZWA = "Pokazowa"
RYWALE = ("zrownowazony", "tani", "premium", "agresywny")
# UF17 (pomiar 4 ziarna, rywale średni): zrównoważony trudny – średnio 1,75 miejsca, premium 2,0,
# „jak człowiek – dobry” 2,5
STRATEGIA, POZIOM, POZIOM_RYWALI = "zrownowazony", "trudny", "sredni"
REFLEKSJA = "Gra pokazowa – decyzje podjął bot."


def konfiguracja_bota(konf: dict, firma: str, poziom: str) -> dict:
    """Konfiguracja, w której drużyna `firma` ma poziom bota – tylko do policzenia jej decyzji."""
    firmy = [{**f, "poziom": poziom} if f["nazwa"] == firma else f for f in konf["firmy"]]
    return {**konf, "firmy": firmy}


def zaloz(rund: int, ziarno: int | None, strategia: str = STRATEGIA, poziom: str = POZIOM,
          rywale: str = POZIOM_RYWALI) -> GraSilnika:
    dane = dane_domyslne()
    st = dane.boty["strategie"]
    if strategia not in st:
        raise CommandError(f"Nie ma strategii {strategia} (są: {', '.join(st)}).")
    for p in (poziom, rywale):
        if p not in (dane.boty.get("poziomy") or {}):
            raise CommandError(f"Nie ma poziomu botów {p}.")
    boty = [(st[k]["nazwa"], k) for k in RYWALE]
    return GraSilnika.nowa(NAZWA, [(NAZWA, None), *boty], rund, ziarno,
                           poziomy={n: rywale for n, _ in boty})


def runda_bota(g: GraSilnika, strategia: str = STRATEGIA, poziom: str = POZIOM) -> int:
    """Decyzje drużyny „Pokazowa” od bota, wysłanie i przeliczenie rundy; zwraca numer rundy."""
    r = g.runda
    konf = konfiguracja_bota(g.konfiguracja, NAZWA, poziom)
    g.ustaw_decyzje(NAZWA, decyzje_bota(g.dane, g.stan(r - 1), NAZWA, strategia, r, konf))
    g.wyslij(NAZWA, refleksja=REFLEKSJA)
    g.przelicz()
    return r


def rozegraj(id_: str, strategia: str, poziom: str, wypisz=lambda t: None) -> None:
    """Rundy po kolei, każda w osobnej zmianie gry – jak przy zamykaniu rundy."""
    while True:
        with serwisy.zmiana(id_) as g:
            if g.zakonczona:
                return
            r = runda_bota(g, strategia, poziom)
        wypisz(f"runda {r} rozegrana")


class Command(BaseCommand):
    help = ("Zakłada od nowa grę „Pokazowa” (boty + drużyna grana przez dobrego bota) "
            "i rozgrywa wszystkie rundy.")

    def add_arguments(self, parser):
        dodaj = parser.add_argument
        dodaj("--rund", type=int, default=18, help="liczba rund (domyślnie 18)")
        dodaj("--ziarno", type=int, default=None, help="ziarno losowania (domyślnie losowe)")
        dodaj("--strategia", default=STRATEGIA, help="strategia drużyny Pokazowa")
        dodaj("--poziom", default=POZIOM, help="poziom bota drużyny Pokazowa")
        dodaj("--rywale", default=POZIOM_RYWALI, help="poziom pozostałych botów")
        dodaj("--konto", action="append", metavar="LOGIN",
              help="konto w drużynie Pokazowa (można kilka; domyślnie wszyscy mistrzowie gry)")

    def handle(self, *args, rund, ziarno, strategia, poziom, rywale, konto, **opcje):
        Uzytkownik = get_user_model()
        if konto:
            konta = list(Uzytkownik.objects.filter(username__in=konto))
            brak = set(konto) - {u.username for u in konta}
            if brak:
                raise CommandError(f"Nie ma kont: {', '.join(sorted(brak))}.")
        else:
            mg = Q(groups__name=MISTRZ_GRY) | Q(is_superuser=True)
            konta = list(Uzytkownik.objects.filter(mg).distinct())
        g = zaloz(rund, ziarno, strategia, poziom, rywale)
        for stara in Gra.objects.filter(nazwa=NAZWA).values_list("pk", flat=True):
            serwisy.usun(stara)
            self.stdout.write(f"usunięta stara gra {stara}")
        id_ = serwisy.utworz(g)
        Druzyna.objects.create(gra_id=id_, firma=NAZWA).czlonkowie.set(konta)
        loginy = ", ".join(u.username for u in konta) or "brak"
        self.stdout.write(f"gra {id_}: {rund} rund, ziarno {g.konfiguracja['ziarno']}, "
                          f"drużyna {NAZWA} ({strategia}, {poziom}) – konta: {loginy}")
        rozegraj(id_, strategia, poziom, self.stdout.write)
        self.stdout.write(self.style.SUCCESS(f"Gra pokazowa gotowa: {id_}"))
