"""Harmonogram odblokowań w grze z lokalami (F4.3).

Element harmonogramu to zakładka (katalog.yaml: rundy.harmonogram_lokali.zakladki) albo element mapy z własnym
terminem w danych: kanały rekrutacji, późniejsi dostawcy, licytacje i przejęcia lokali, promocje, kanały agencji
reklamowych, eventy w parkach, wypadki, handel między drużynami, detektyw (bez klubu z kasynem – mistrz gry o nim nie wie,
silnik/pieniadze/kasyno.py). Mistrz gry może zmienić
tydzień każdego elementu (konfiguracja gry: `odblokowanie` – {element: tydzień}, tylko zmiany względem danych) – poza
tygodniem 1 (P15): to tydzień przygotowawczy, jego zakładek nie da się przesunąć ani przenieść niczego do niego.

Gra liczy się na widoku danych (`dla_gry`): płytkiej kopii wspólnych danych z harmonogramem zakładek i z tygodniami
mistrza gry wpisanymi tam, skąd czytają je moduły (kopiowane są tylko słowniki na drodze do zmienionego pola) –
wspólne dane się nie zmieniają, a moduły silnika nie muszą wiedzieć o nadpisaniach.
"""
from __future__ import annotations

import copy

from .dane import Dane
from .kuchnia import dostawcy as dw
from .nieruchomosci.lokale import tryb_lokali

Sciezka = tuple[str, ...]   # (atrybut danych, klucze…) do pola z numerem pierwszej rundy
PRZYGOTOWAWCZY = 1          # tydzień przygotowań – poza władzą mistrza gry


def baza(dane: Dane) -> Dane:
    """Wspólne dane, z których powstał widok gry (dla wspólnych danych – one same)."""
    return getattr(dane, "_baza", dane)


def _wez(dane: Dane, s: Sciezka) -> int:
    x = getattr(dane, s[0])
    for k in s[1:]:
        x = x[k]
    return x


def _zmien(d: dict, klucze: Sciezka, wartosc: int) -> dict:
    """Kopia słownika z nową wartością pod ścieżką kluczy (kopiowane tylko słowniki po drodze)."""
    k, *reszta = klucze
    return {**d, k: _zmien(d[k], tuple(reszta), wartosc) if reszta else wartosc}


def elementy(dane: Dane) -> dict[str, dict]:
    """Elementy harmonogramu z tygodniem z danych: {klucz: {"nazwa", "grupa", "tydzien", "sciezki"}} (zakładki –
    bez ścieżek). Pusty słownik – dane bez mapy miasta albo bez harmonogramu zakładek."""
    dane = baza(dane)
    h = dane.katalog_ofert["rundy"].get("harmonogram_lokali")
    if not h or not dane.mapa:
        return {}
    el = {k: {"nazwa": z["nazwa"], "grupa": "Zakładki", "tydzien": z["tydzien"], "sciezki": []}
          for k, z in h["zakladki"].items()}

    def dodaj(klucz: str, nazwa: str, grupa: str, sciezki: list[Sciezka]) -> None:
        if sciezki:
            el[klucz] = {"nazwa": nazwa, "grupa": grupa, "tydzien": min(_wez(dane, s) for s in sciezki), "sciezki": sciezki}

    dodaj("licytacje", "Licytacje lokali (przebijanie ceny wywoławczej)", "Lokale", [("mapa", "zasady", "licytacje_od_rundy")])
    dodaj("przejecia", "Kupno budynku z najemcą", "Lokale", [("mapa", "zasady", "przejecia_od_rundy")])
    for n, k in dane.rynek_pracy["agencja"]["kanaly"].items():
        dodaj(f"rekrutacja_{n}", k["nazwa"], "HR", [("rynek_pracy", "agencja", "kanaly", n, "od_rundy")])
    pozniejsi: dict[str, list[str]] = {}
    for d, i in dane.dostawcy_info.items():
        if i.get("od_rundy", dw.DOMYSLNE["od_rundy"]) > 1:
            pozniejsi.setdefault(i.get("rodzaj", dw.DOMYSLNE["rodzaj"]), []).append(d)
    for rodzaj, ds in pozniejsi.items():
        dodaj(f"dostawcy_{rodzaj}", ", ".join(ds), "Dostawcy", [("dostawcy_info", d, "od_rundy") for d in ds])
    if dane.mapa.get("promocje"):
        dodaj("promocje", "Promocje", "Marketing", [("mapa", "promocje", "od_rundy")])
    kanaly = [("mapa", "reklama", "agencje", a, "kanaly", k, "od_rundy")
              for a, ag in ((dane.mapa.get("reklama") or {}).get("agencje") or {}).items() for k in ag["kanaly"]]
    if kanaly:
        pierwsze = min(_wez(dane, s) for s in kanaly)
        dodaj("reklama", "Agencje reklamowe – pierwsze kanały", "Marketing", [s for s in kanaly if _wez(dane, s) == pierwsze])
        dodaj("reklama_wszystkie", "Agencje reklamowe – pozostałe kanały", "Marketing",
              [s for s in kanaly if _wez(dane, s) > pierwsze])
    z = dane.zdarzenia or {}
    for klucz, nazwa, sciezka in (("parki", "Eventy w parkach", ("parki", "zasady")),
                                  ("wypadki", "Wypadki w lokalu", ("losowe", "zasady")),
                                  ("handel", "Handel między drużynami", ("handel", "handel")),
                                  ("detektyw", "Detektyw – dokładne dane konkurencji", ("detektyw", "detektyw"))):
        if sciezka[0] in z:
            dodaj(klucz, nazwa, "Zdarzenia" if klucz != "handel" else "Handel", [("zdarzenia", *sciezka, "od_rundy")])
    return el


def dla_gry(dane: Dane, konfiguracja: dict) -> Dane:
    """Dane, na których liczy się gra: w grze z lokalami – widok z harmonogramem (zakładki z harmonogramu lokali,
    tygodnie mistrza gry), w grze bez lokali – wspólne dane."""
    dane = baza(dane)
    el = elementy(dane)
    if not el or not tryb_lokali(dane, konfiguracja):
        return dane
    zmiany = {k: int(t) for k, t in (konfiguracja.get("odblokowanie") or {}).items() if k in el}
    w = copy.copy(dane)
    w._baza = dane
    w.nadpisane_rundy = zmiany
    w.odblokowanie_rund = {}
    for k, e in el.items():
        if not e["sciezki"]:
            w.odblokowanie_rund.setdefault(str(zmiany.get(k, e["tydzien"])), []).append(k)
    for k, t in zmiany.items():
        for s in el[k]["sciezki"]:
            setattr(w, s[0], _zmien(getattr(w, s[0]), s[1:], t))
    return w


def sprawdz_zmiany(dane: Dane, zmiany: dict, obecne: dict, runda: int, liczba_rund: int) -> dict[str, int]:
    """Nadpisania po zmianach mistrza gry (tylko różne od danych). Tydzień liczba_rund + 1 – element wyłączony.
    Zmienić można tylko element, który jeszcze się nie odblokował, i tylko na tydzień nie wcześniejszy niż bieżący –
    przeliczone rundy zostają takie, jak były. Niedozwolona zmiana – ValueError z opisem."""
    el = elementy(dane)
    if not el:
        raise ValueError("Harmonogram odblokowań jest tylko w grze z lokalami.")
    nowe = {k: t for k, t in obecne.items() if k in el}
    for k, t in zmiany.items():
        if k not in el:
            raise ValueError(f"Nie ma takiego elementu harmonogramu: {k}.")
        try:
            t = int(t)
        except (TypeError, ValueError):
            raise ValueError(f"{el[k]['nazwa']}: tydzień musi być liczbą.") from None
        teraz = nowe.get(k, el[k]["tydzien"])
        if t == teraz:
            continue
        if el[k]["tydzien"] <= PRZYGOTOWAWCZY:
            raise ValueError(f"{el[k]['nazwa']}: tydzień {PRZYGOTOWAWCZY} jest przygotowawczy – tego nie zmienisz.")
        if teraz < runda:
            raise ValueError(f"{el[k]['nazwa']}: już odblokowane (tydzień {teraz}) – przeliczonych tygodni nie zmieniam.")
        od = max(runda, PRZYGOTOWAWCZY + 1)
        if not od <= t <= liczba_rund + 1:
            raise ValueError(f"{el[k]['nazwa']}: tydzień od {od} do {liczba_rund} ({liczba_rund + 1} – wyłączone; "
                             f"tydzień {PRZYGOTOWAWCZY} jest przygotowawczy).")
        if t == el[k]["tydzien"]:
            nowe.pop(k, None)
        else:
            nowe[k] = t
    return nowe


def widok(dane: Dane, runda: int) -> list[dict]:
    """Harmonogram gry: [{"klucz", "nazwa", "grupa", "tydzien", "domyslny", "odblokowany", "staly"}] (pusty – gra bez
    lokali; staly – zakładka tygodnia przygotowawczego, mistrz gry jej nie przesuwa)."""
    if baza(dane) is dane:
        return []
    z = dane.nadpisane_rundy
    return [{"klucz": k, "nazwa": e["nazwa"], "grupa": e["grupa"], "tydzien": z.get(k, e["tydzien"]),
             "domyslny": e["tydzien"], "odblokowany": z.get(k, e["tydzien"]) <= runda,
             "staly": e["tydzien"] <= PRZYGOTOWAWCZY} for k, e in elementy(dane).items()]
