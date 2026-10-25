"""Planowanie: oczekiwany popyt, potrzebne godziny i stanowiska, zamówienia zasobów.
Używane przez boty i podpowiedzi w interfejsie (bez losowości – wartości oczekiwane).
"""
from __future__ import annotations

import math

from .dane import MIESIACE, Dane
from .dostawcy import najtansze
from .model import Firma
from .rynek import mnoznik_jakosci, popyt_bazowy


def oczekiwany_popyt(dane: Dane, usluga: str, miesiac: int, cena: float, jakosc: tuple[float, float, float],
                     n_firm: int = 1, r_sr: float | None = None, wyposazenie: float = 1.0, reklama: float = 0.0) -> float:
    import math as m
    p = dane.z["popyt"]
    u = dane.uslugi[usluga]
    r = cena / u["cena_preferowana"]
    r_sr = r if r_sr is None else r_sr
    return (popyt_bazowy(dane, usluga, miesiac) * p["korekta_miesiaca"].get(MIESIACE[miesiac], 1.0) * p["mnoznik_bazowy"]
            * mnoznik_jakosci(dane, *jakosc) * m.exp(-p["elastycznosc_ceny"] * (r - 1))
            * m.exp(-p["elastycznosc_wzgledem_rynku"] * (r - r_sr)) * max(1, n_firm) ** (-p["wykladnik_liczby_firm"])
            * wyposazenie * (1 + reklama))


def godziny_uslugi(dane: Dane, usluga: str, klienci: float) -> float:
    u = dane.uslugi[usluga]
    return math.ceil(klienci / u["grupa"] - 1e-9) * u["godziny_prowadzacego"]


def stanowiska_potrzebne(dane: Dane, usluga: str, klienci: float) -> int:
    return math.ceil(godziny_uslugi(dane, usluga, klienci) / dane.z["operacje"]["godziny_pracownika"] - 1e-9)


def recepcjonisci_potrzebni(dane: Dane, klienci: dict[str, float]) -> int:
    h = sum(k * dane.uslugi[u]["godziny_recepcji"] for u, k in klienci.items())
    return math.ceil(h / dane.z["operacje"]["godziny_pracownika"] - 1e-9) if h > 0 else 0


def zamowienie_zasobow(dane: Dane, firma: Firma, klienci: dict[str, float], ceny_dostawcow: dict, jakosc: int,
                       zapas: float = 1.05) -> list[dict]:
    """Zamówienia (u najtańszych dostawców w danej jakości), żeby starczyło na `klienci` × zapas."""
    potrzeba = {}
    for u, k in klienci.items():
        for z, ile in dane.uslugi[u]["zasoby"].items():
            potrzeba[z] = potrzeba.get(z, 0.0) + k * zapas * ile / dane.zasoby[z]["opakowanie"]
    oferty = najtansze(ceny_dostawcow)
    wynik = []
    for z, p in potrzeba.items():
        stan = sum(firma.magazyn.get(f"{z}|{q}", 0.0) for q in (1, 2, 3))
        brak = math.ceil(max(0.0, p - stan) - 1e-9)
        if brak <= 0:
            continue
        q = jakosc
        while (z, str(q)) not in oferty and q > 1:
            q -= 1
        if (z, str(q)) in oferty:
            wynik.append({"dostawca": oferty[(z, str(q))][1], "zasob": z, "jakosc": q, "ilosc": brak})
    return wynik
