"""Kalendarz miejski (F3b.9, gra z lokalami; dane: `dane/kalendarz/kalendarz.yaml`).

Święta, rok akademicki (sesja, przerwy), ferie, okazje handlowe i wydarzenia w Lublinie w kolejnych tygodniach gry.
Wydarzenie mnoży dzienną pulę klientów strefy (popyt.wagi_dni): klucz strefy wygrywa z „wszystkie”, mnożniki kilku
wydarzeń tego samego dnia się mnożą. Daty stałe co roku ('MM-DD', zakres może przechodzić przez Nowy Rok) albo
ruchome – przesunięcie w dniach od daty z `ruchome` na dany rok (Wielkanoc, Black Friday, ferie).
"""
from __future__ import annotations

from datetime import date, timedelta

from .dane import Dane

WSZYSTKIE = "wszystkie"   # klucz strefy: każda strefa bez własnego mnożnika
EPS = 1e-6


def dane_kalendarza(dane: Dane) -> dict | None:
    """Kalendarz miejski (tylko w grze z mapą miasta)."""
    return dane.kalendarz_miasta if dane.mapa else None


def _w_zakresie(dzien: date, od: str, do: str) -> bool:
    md = dzien.strftime("%m-%d")
    return od <= md <= do if od <= do else (md >= od or md <= do)  # zakres przez Nowy Rok


def _baza(k: dict, klucz: str, rok: int) -> date | None:
    md = k["ruchome"][klucz].get(rok)
    return date.fromisoformat(f"{rok}-{md}") if md else None


def trwa(k: dict, w: dict, dzien: date) -> bool:
    """Czy wydarzenie `w` trwa w dniu `dzien` (data ruchoma bez daty na ten rok – nie ma wydarzenia)."""
    if w["wzgledem"] is None:
        return _w_zakresie(dzien, w["od"], w["do"])
    for rok in (dzien.year - 1, dzien.year, dzien.year + 1):   # przesunięcie może przejść na sąsiedni rok
        b = _baza(k, w["wzgledem"], rok)
        if b and b + timedelta(days=w["od"]) <= dzien <= b + timedelta(days=w["do"]):
            return True
    return False


def mnoznik(dane: Dane, strefa: str, dzien: date) -> float:
    """Mnożnik puli klientów strefy w danym dniu (1 – zwykły dzień)."""
    k = dane_kalendarza(dane)
    m = 1.0
    for w in (k["wydarzenia"] if k else []):
        if trwa(k, w, dzien):
            m *= w["strefy"].get(strefa, w["strefy"].get(WSZYSTKIE, 1.0))
    return m


def wydarzenia(dane: Dane, dni: list[date]) -> list[dict]:
    """Wydarzenia w podanych dniach: {"nazwa", "rodzaj", "rodzaj_nazwa", "opis", "dni": [ISO], "strefy": {strefa: ×}}."""
    k = dane_kalendarza(dane)
    wynik = []
    for w in (k["wydarzenia"] if k else []):
        trafione = [d.isoformat() for d in dni if trwa(k, w, d)]
        if trafione:
            wynik.append({"nazwa": w["nazwa"], "rodzaj": w["rodzaj"], "rodzaj_nazwa": k["rodzaje"][w["rodzaj"]],
                          "opis": w["opis"], "dni": trafione, "strefy": w["strefy"]})
    return wynik


def tydzien(dane: Dane, runda: int) -> dict:
    """Runda w kalendarzu: dni, wydarzenia i zmiana tygodniowej puli klientów każdej strefy przez kalendarz
    (np. 0,12 = +12% klientów; waga dnia tygodnia uwzględniona – sobotnie święto waży więcej niż poniedziałkowe)."""
    from . import popyt as pp  # popyt korzysta z kalendarza – import w funkcji
    dni = pp.dni_rundy(dane, runda)
    zmiany = {}
    for s in dane.mapa["strefy"]:
        z = pp.wagi_dni(dane, s, dni).sum() / pp.wagi_dni(dane, s, dni, kalendarz=False).sum() - 1
        if abs(z) > EPS:
            zmiany[s] = round(float(z), 4)
    return {"runda": runda, "od": dni[0].isoformat(), "do": dni[-1].isoformat(), "wydarzenia": wydarzenia(dane, dni),
            "strefy": zmiany}


def widok(dane: Dane, runda: int, liczba_rund: int) -> dict | None:
    """Zakładka Kalendarz miejski: bieżący tydzień, poprzedni (wyniki) i przegląd wszystkich tygodni gry."""
    k = dane_kalendarza(dane)
    if not k:
        return None
    tygodnie = [tydzien(dane, r) for r in range(1, liczba_rund + 1)]
    for t in tygodnie:   # przegląd: bez opisów (są w bieżącym tygodniu i w szczegółach)
        t["wydarzenia"] = [{x: w[x] for x in ("nazwa", "rodzaj", "dni")} for w in t["wydarzenia"]]
    return {"rodzaje": k["rodzaje"], "biezacy": tydzien(dane, runda),
            "poprzedni": tydzien(dane, runda - 1) if runda > 1 else None, "tygodnie": tygodnie}
