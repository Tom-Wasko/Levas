"""Zamykanie rund o ustalonej godzinie i pauza gry (F3a.14).

Harmonogram gry to lista terminów tygodniowych {"dzien": 0–6 (0 = poniedziałek),
"godzina": "HH:MM"} w czasie lokalnym (`TIME_ZONE`). Runda zamyka się w pierwszym terminie po
`Gra.termin_od` – zamknięciu poprzedniej rundy, założeniu gry, zmianie harmonogramu albo
wznowieniu gry po pauzie (termin, który minął w czasie pauzy, nie zamyka rundy od razu po
wznowieniu). Komenda `zamykaj_rundy` uruchamiana co kilka minut (Harmonogram zadań Windows,
cron) zamyka rundy, których termin minął – po jednej rundzie gry na uruchomienie.
"""

from __future__ import annotations

import re
from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import Gra

DNI = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
MAKS_TERMINOW = 14


def popraw(terminy) -> list[dict]:
    """Terminy z panelu mistrza gry → posortowana lista bez powtórzeń (błąd: `ValueError`)."""
    if not isinstance(terminy, list):
        raise ValueError("Harmonogram to lista terminów.")
    wynik = set()
    for t in terminy:
        if not isinstance(t, dict):
            raise ValueError("Termin to dzień tygodnia i godzina.")
        dzien, godzina = t.get("dzien"), str(t.get("godzina", "")).strip()
        if not isinstance(dzien, int) or isinstance(dzien, bool) or not 0 <= dzien < len(DNI):
            raise ValueError("Wybierz dzień tygodnia terminu.")
        m = re.fullmatch(r"(\d{1,2}):(\d{2})", godzina)
        if not m or int(m[1]) > 23 or int(m[2]) > 59:
            raise ValueError(f"Godzina „{godzina}” – wpisz ją jako GG:MM, np. 8:00.")
        wynik.add((dzien, f"{int(m[1]):02d}:{m[2]}"))
    if len(wynik) > MAKS_TERMINOW:
        raise ValueError(f"Najwyżej {MAKS_TERMINOW} terminów w tygodniu.")
    return [{"dzien": d, "godzina": g} for d, g in sorted(wynik)]


def nastepny(terminy: list[dict], od: datetime) -> datetime | None:
    """Pierwszy termin z harmonogramu ściśle po `od` (świadomy strefy czasu)."""
    if not terminy:
        return None
    strefa = timezone.get_current_timezone()
    lokalnie = timezone.localtime(od, strefa)
    kandydaci = []
    for przesuniecie in range(8):
        dzien = lokalnie.date() + timedelta(days=przesuniecie)
        for t in terminy:
            if t["dzien"] == dzien.weekday():
                g, m = map(int, t["godzina"].split(":"))
                kiedy = timezone.make_aware(datetime.combine(dzien, time(g, m)), strefa)
                if kiedy > od:
                    kandydaci.append(kiedy)
    return min(kandydaci, default=None)


def termin(obj: Gra) -> datetime | None:
    """Kiedy zamknie się bieżąca runda gry (brak: bez harmonogramu albo w pauzie)."""
    if obj.pauza or not obj.harmonogram:
        return None
    return nastepny(obj.harmonogram, obj.termin_od or obj.utworzono)


def opis(t: dict) -> str:
    return f"{DNI[t['dzien']]} {t['godzina']}"


def do_zamkniecia(teraz: datetime | None = None) -> list[tuple[str, datetime]]:
    """Gry (id, termin), w których minął termin zamknięcia bieżącej rundy."""
    teraz = teraz or timezone.now()
    gry = Gra.objects.filter(pauza=False).exclude(harmonogram=[])
    return [(g.pk, t) for g in gry if (t := termin(g)) is not None and t <= teraz]


def zamknij_spoznione(teraz: datetime | None = None) -> list[dict]:
    """Zamyka rundy po terminie. Wynik do dziennika komendy: [{"gra", "nazwa", "runda"}]
    albo [{"gra", "blad"}]."""
    from . import serwisy

    wynik = []
    for id_, t in do_zamkniecia(teraz):
        try:
            with serwisy.zmiana(id_) as g:
                if g.zakonczona:
                    continue
                r = g.runda
                g.przelicz(wymus=True)
            # następny termin – po tym, który zamknął rundę (też gdy komenda ruszyła z opóźnieniem)
            Gra.objects.filter(pk=id_).update(termin_od=max(timezone.now(), t))
            wynik.append({"gra": id_, "nazwa": g.konfiguracja["nazwa"], "runda": r})
        except Exception as e:  # jedna zepsuta gra nie zatrzymuje pozostałych
            wynik.append({"gra": id_, "blad": f"{type(e).__name__}: {e}"})
    return wynik


def prowadzenie(id_: str) -> dict:
    """Pauza, harmonogram i termin zamknięcia bieżącej rundy – do widoków drużyny i mistrza gry."""
    obj = Gra.objects.only("pauza", "harmonogram", "termin_od", "utworzono").get(pk=id_)
    t = termin(obj)
    return {
        "pauza": obj.pauza,
        "harmonogram": obj.harmonogram,
        "termin": t.isoformat() if t else None,
        "harmonogram_opis": ", ".join(opis(x) for x in obj.harmonogram),
    }


def ustaw(id_: str, pauza: bool | None = None, harmonogram: list | None = None) -> dict:
    """Zmiana pauzy albo harmonogramu. Termin liczony od teraz – runda nie zamknie się
    terminem, który już minął."""
    zmiany: dict = {}
    if harmonogram is not None:
        zmiany["harmonogram"] = popraw(harmonogram)
    if pauza is not None:
        zmiany["pauza"] = bool(pauza)
    if zmiany:
        zmiany["termin_od"] = timezone.now()
        if not Gra.objects.filter(pk=id_).update(**zmiany):
            raise Gra.DoesNotExist(id_)
    return prowadzenie(id_)
