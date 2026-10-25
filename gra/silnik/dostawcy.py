"""Ceny dostawców w miesiącu.

Miesiące z danymi (luty–czerwiec) – prawdziwe ceny z gry (chyba że gra ma ustawione ceny losowe).
Pozostałe – baza serii (średnia z danych) × (1 + odchylenie), odchylenie losowe z ziarnem gry
(analiza: ceny wahają się wokół stałej bazy, odchylenie std ≈ 5,7%, zmiana m/m ≤ 17%).
Dostępni dostawcy: do marca trzech (FullService, InterShop, OfficeShop), od kwietnia sześciu.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .dane import MIESIACE, Dane
from .losowosc import generator

PIERWSI = ("FullService", "InterShop", "OfficeShop")
OD_KWIETNIA = 3  # indeks miesiąca, od którego są wszyscy dostawcy


@lru_cache(maxsize=4)
def _serie(dane: Dane) -> dict[tuple[str, str, str], dict]:
    """{(dostawca, zasób, jakość): {"baza", "calkowite"}} z miesięcy z danymi."""
    serie = {}
    for ceny in dane.dostawcy.values():
        for d, zasoby in ceny.items():
            for z, jak in zasoby.items():
                for q, c in jak.items():
                    serie.setdefault((d, z, q), []).append(c)
    return {k: {"baza": float(np.mean(v)), "calkowite": all(float(c).is_integer() for c in v)} for k, v in serie.items()}


def ceny_miesiaca(dane: Dane, ziarno, miesiac: int, tryb: str = "dane") -> dict:
    """{dostawca: {zasób: {"1": cena, "2": …, "3": …}}} dla miesiąca (indeks 0 = styczeń)."""
    nazwa = MIESIACE[miesiac]
    if tryb == "dane" and nazwa in dane.dostawcy:
        return dane.dostawcy[nazwa]
    if miesiac == 0:
        return {}
    odch = dane.z["losowosc"]["ceny_dostawcow"]
    rng = generator(ziarno, "dostawcy", miesiac)
    wynik = {}
    for (d, z, q), s in sorted(_serie(dane).items()):
        if miesiac < OD_KWIETNIA and d not in PIERWSI:
            continue
        e = float(np.clip(rng.normal(0, odch["odchylenie"] * 1.3), -odch["max_zmiana"], odch["max_zmiana"]))
        cena = s["baza"] * (1 + e)
        wynik.setdefault(d, {}).setdefault(z, {})[q] = float(round(cena)) if s["calkowite"] else round(cena, 2)
    return wynik


def najtansze(ceny: dict) -> dict[tuple[str, str], tuple[float, str]]:
    """{(zasób, jakość): (cena, dostawca)} – najtańsza oferta."""
    wynik = {}
    for d, zasoby in ceny.items():
        for z, jak in zasoby.items():
            for q, c in jak.items():
                if (z, q) not in wynik or c < wynik[(z, q)][0]:
                    wynik[(z, q)] = (c, d)
    return wynik
