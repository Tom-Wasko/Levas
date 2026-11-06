"""Mnożniki jakości i wyposażenia (wspólne dla popytu strefowego, menu i planowania; parametry w dane/zalozenia.yaml)."""
from __future__ import annotations

import math

from ..dane import Dane


def wspolczynnik_gwiazdek(gwiazdki: float, wsp: dict) -> float:
    """1–3★ (także ułamkowe) → mnożnik jakości; liniowo między 1★, 2★ i 3★."""
    g = min(3.0, max(1.0, gwiazdki))
    if g >= 3:
        return float(wsp["3"])
    j = 1 if g < 2 else 2   # przedział [j, j+1]; ten sam wzór co np.interp, bez narzutu numpy na jedną liczbę
    a, b = float(wsp[str(j)]), float(wsp[str(j + 1)])
    return (b - a) * (g - j) + a


def mnoznik_jakosci(dane: Dane, pracownicy: float, sprzet: float, zasoby: float, wagi: dict | None = None) -> float:
    p = dane.z["popyt"]
    w, wsp = wagi or p["wagi_jakosci"], p["wspolczynniki_jakosci"]
    return (w["pracownicy"] * wspolczynnik_gwiazdek(pracownicy, wsp) + w["sprzet"] * wspolczynnik_gwiazdek(sprzet, wsp)
            + w["zasoby"] * wspolczynnik_gwiazdek(zasoby, wsp)) / sum(w.values())


def mnoznik_wyposazenia(dane: Dane, wyposazenie: list[str]) -> float:
    """1 + κ · x, x = Σ % klientów oczekujących wyposażenia / 100; z `wyposazenie_nasycenie` S (B10) przyrost nasyca się:
    1 + κ · S · (1 − e^(−x / S)) – pierwsza sztuka działa jak dawniej, każda kolejna słabiej."""
    p, pozycje = dane.z["popyt"], dane.pozycje("wyposazenie")
    x = sum(pozycje[n]["procent"] / 100 for n in wyposazenie)
    s = p.get("wyposazenie_nasycenie")
    return 1 + p["wyposazenie_na_procent_klientow"] * (s * (1 - math.exp(-x / s)) if s else x)
