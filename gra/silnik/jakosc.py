"""Mnożniki jakości i wyposażenia (wspólne dla popytu strefowego, menu i planowania; parametry w dane/zalozenia.yaml)."""
from __future__ import annotations

import numpy as np

from .dane import Dane


def wspolczynnik_gwiazdek(gwiazdki: float, wsp: dict) -> float:
    """1–3★ (także ułamkowe) → mnożnik jakości; liniowo między 1★, 2★ i 3★."""
    g = min(3.0, max(1.0, gwiazdki))
    return float(np.interp(g, [1, 2, 3], [wsp["1"], wsp["2"], wsp["3"]]))


def mnoznik_jakosci(dane: Dane, pracownicy: float, sprzet: float, zasoby: float, wagi: dict | None = None) -> float:
    p = dane.z["popyt"]
    w, wsp = wagi or p["wagi_jakosci"], p["wspolczynniki_jakosci"]
    return (w["pracownicy"] * wspolczynnik_gwiazdek(pracownicy, wsp) + w["sprzet"] * wspolczynnik_gwiazdek(sprzet, wsp)
            + w["zasoby"] * wspolczynnik_gwiazdek(zasoby, wsp)) / sum(w.values())


def mnoznik_wyposazenia(dane: Dane, wyposazenie: list[str]) -> float:
    pozycje = dane.pozycje("wyposazenie")
    return 1 + dane.z["popyt"]["wyposazenie_na_procent_klientow"] * sum(pozycje[n]["procent"] / 100 for n in wyposazenie)
