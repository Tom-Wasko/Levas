"""Menu w grze z lokalami (krok F3a.5; dane: dane/mapa/menu.yaml, notatki/Menu i składniki.md).

- jakość dania = średnia ważona współczynników gwiazdek składników, kucharzy i sprzętu (wagi z menu.yaml; w grze
  bez lokali – wagi Revasa z zalozenia.yaml),
- danie, któremu rano brakuje składnika (razem z zamiennikiem), jest wyłączone do następnej dostawy: część jego
  klientów (zmiana_dania) bierze inne danie z menu lokalu – proporcjonalnie do popytu na nie – reszta odchodzi.
"""
from __future__ import annotations

import math

from . import swiezosc as sw
from .dane import Dane
from .rynek import mnoznik_jakosci

EPS = 1e-9


def jakosc_dania(dane: Dane, jakosc: tuple[float, float, float]) -> float:
    """(gwiazdki kucharzy, sprzętu, składników) → mnożnik jakości dania."""
    w = (dane.mapa or {}).get("menu", {}).get("jakosc")
    if not w:
        return mnoznik_jakosci(dane, *jakosc)
    return mnoznik_jakosci(dane, *jakosc, wagi={"pracownicy": w["kucharze"], "sprzet": w["sprzet"], "zasoby": w["skladniki"]})


def wylaczone(dane: Dane, magazyn: dict, dania) -> dict[str, str]:
    """Dania bez składnika na stanie: {danie: brakujący składnik}."""
    wynik = {}
    for u in dania:
        brak = next((z for z in dane.uslugi[u]["zasoby"] if sw.dostepne(dane, magazyn, z) <= EPS), None)
        if brak:
            wynik[u] = brak
    return wynik


def przenies(dane: Dane, popyt: dict[str, int], wyl: dict[str, str]) -> tuple[dict[str, int], dict[str, int]]:
    """Klienci wyłączonych dań: część przechodzi na dania dostępne (proporcjonalnie do ich popytu, metodą największych
    reszt). Zwraca (nowy popyt dnia, {wyłączone danie: ilu przeszło})."""
    dostepne = [u for u in popyt if u not in wyl]
    nowy, przeszli = dict(popyt), {}
    if not dostepne:
        return nowy, {u: 0 for u in wyl}
    udzial = dane.mapa["menu"]["zmiana_dania"]
    wagi = {u: popyt[u] for u in dostepne} if sum(popyt[u] for u in dostepne) else {u: 1 for u in dostepne}
    suma = sum(wagi.values())
    for u in wyl:
        n = math.floor(popyt[u] * udzial + EPS)
        przeszli[u] = n
        nowy[u] -= n
        czesci = {v: n * w / suma for v, w in wagi.items()}
        cale = {v: math.floor(x + EPS) for v, x in czesci.items()}
        reszta = n - sum(cale.values())
        for v in sorted(czesci, key=lambda v: cale[v] - czesci[v])[:reszta]:
            cale[v] += 1
        for v, k in cale.items():
            nowy[v] += k
    return nowy, przeszli


__all__ = ["jakosc_dania", "przenies", "wylaczone"]
