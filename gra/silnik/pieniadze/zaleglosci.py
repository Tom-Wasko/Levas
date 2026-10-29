"""Skutki zaległości (gra z lokalami): wizyty u dłużnika – szkody w lokalu, odpływ klientów, odejście pracownika.

Na razie wysyła je Harpagon (silnik/pieniadze/lichwiarz.py); te same skutki mogą później dostać inne zaległości (ZUS, urząd).
Wizyta jest losowana z wag (`wizyty` z danych), tak samo historia; odejście pracownika – tylko gdy jest kto
odejść (pracownik w okresie wypowiedzenia i tak odchodzi, więc go pomijamy).
"""
from __future__ import annotations

import numpy as np

from ..dane import Dane
from ..ksiegowosc.finanse import Ksiega, Rachunek, ksieguj
from ..model import Firma, Pracownik


class _Wartosci(dict):
    """Wartości do historii – brakujący znacznik w tekście daje pusty napis zamiast błędu."""

    def __missing__(self, klucz):
        return ""


def zl(x: float) -> str:
    return f"{x:,.2f}".replace(",", " ").replace(".", ",") + " zł"


def procent(x: float) -> str:
    return f"{x * 100:.0f}%"


def _do_odejscia(firma: Firma) -> list[str]:
    return sorted(pid for pid, p in firma.pracownicy.items() if not p.odchodzi)


def odejscie(dane: Dane, firma: Firma, pid: str) -> Pracownik:
    """Pracownik odchodzi od razu – bez wypowiedzenia i odprawy; stanowisko zostaje wolne."""
    p = firma.pracownicy.pop(pid)
    st = firma.stanowisko(dane.typ_zawodu(p.zawod), p.stanowisko)
    if st and st.pracownik == pid:
        st.pracownik = None
    return p


def wizyta(dane: Dane, firma: Firma, wizyty: list[dict], gen, ksiega: Ksiega,
           rachunek: Rachunek, wartosci: dict, opis_kosztu: str) -> tuple[dict, Pracownik | None]:
    """Losuje (`gen` – strumień z silnik/losowosc.py) i wykonuje jedną wizytę. Zwraca (opis do wyników, pracownik, który odszedł – do puli kandydatów)."""
    mozliwe = [w for w in wizyty if w["rodzaj"] != "pracownik" or _do_odejscia(firma)]
    wagi = np.array([w["waga"] for w in mozliwe], dtype=float)
    w = mozliwe[int(gen.choice(len(mozliwe), p=wagi / wagi.sum()))]
    historia = w["historie"][int(gen.integers(len(w["historie"])))]
    wynik = {"rodzaj": w["rodzaj"], "koszt": 0.0, "odplyw": 0.0, "pracownik": None}
    odszedl = None
    if w["rodzaj"] == "szkody":
        od, do = w["koszt"]
        wynik["koszt"] = float(round(gen.uniform(od, do) / 10) * 10)
        ksieguj(firma, ksiega, rachunek, opis_kosztu, wynik["koszt"])   # naprawa jest prawdziwym kosztem
    elif w["rodzaj"] == "klienci":
        wynik["odplyw"] = w["odplyw"]
    else:
        kto = _do_odejscia(firma)
        odszedl = odejscie(dane, firma, kto[int(gen.integers(len(kto)))])
        wynik["pracownik"] = odszedl.imie_nazwisko
    wynik["tekst"] = historia.format_map(_Wartosci(wartosci, koszt=zl(wynik["koszt"]), procent=procent(wynik["odplyw"]),
                                                   pracownik=wynik["pracownik"] or ""))
    return wynik, odszedl
