"""Ceny dostawców w miesiącu.

Miesiące z danymi (luty–czerwiec) – prawdziwe ceny z gry (chyba że gra ma ustawione ceny losowe).
Pozostałe – baza serii (średnia z danych) × (1 + odchylenie), odchylenie losowe z ziarnem gry
(analiza: ceny wahają się wokół stałej bazy, odchylenie std ≈ 5,7%, zmiana m/m ≤ 17%).
Dostępni dostawcy: do marca trzech (dostawcy.yaml: pierwsi), od kwietnia wszyscy (wszyscy_od_miesiaca).

Levas (F3a.6, dostawcy.yaml: dostawcy): dostawca może wejść później (od_rundy), dyskonty mają co tydzień gazetkę
(kilka składników taniej – losowo z ziarnem gry). W grze z lokalami zamówienie ma dzień dostawy: dostawca dowozi tylko
w swoje dni, dostawa poniżej progu kosztuje, producent ma minimalne zamówienie, a w dyskoncie właściciel kupuje sam
(limit opakowań na składnik dziennie, godziny właściciela).
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache

import numpy as np

from . import czas_wlasciciela as cw
from .dane import MIESIACE, Dane
from .losowosc import strumien


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


DOMYSLNE = {"rodzaj": "hurtownia", "opis": "", "dni_dostaw": list(range(7)), "koszt_dostawy": 0, "darmowa_od": None,
            "minimalne_zamowienie": 0, "odbior_osobisty": False, "godziny_odbioru": 0, "limit_opakowan": None,
            "od_rundy": 0, "gazetka": None}
DNI = ("poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela")
W_DZIEN = ("w poniedziałek", "we wtorek", "w środę", "w czwartek", "w piątek", "w sobotę", "w niedzielę")


def info(dane: Dane, dostawca: str) -> dict:
    """Zasady dostawcy (dostawcy.yaml: dostawcy) z domyślnymi – dane bez tej sekcji: dowóz codziennie, bez opłat."""
    return {**DOMYSLNE, **dane.dostawcy_info.get(dostawca, {})}


def ceny_rundy(dane: Dane, ziarno, runda: int, tryb: str = "dane") -> dict:
    """Ceny dostawców w rundzie (z rabatami z gazetek). Runda 1 to przygotowanie lokalu (bez sprzedaży i zakupów) –
    brak ofert. Rundy tygodniowe: ceny z danych dla miesiąca rundy, poza nimi losowanie co tydzień."""
    return oferta_rundy(dane, ziarno, runda, tryb)[0]


def oferta_rundy(dane: Dane, ziarno, runda: int, tryb: str = "dane") -> tuple[dict, dict]:
    """(ceny po rabatach, gazetki {dostawca: {zasób: rabat}})."""
    if runda <= 1:
        return {}, {}
    bazowe = ceny_miesiaca(dane, ziarno, dane.miesiac_rundy(runda), tryb, runda if dane.tygodniowe else None)
    bazowe = {d: z for d, z in bazowe.items() if info(dane, d)["od_rundy"] <= runda}
    rabaty = gazetki(dane, ziarno, runda, bazowe)
    ceny = {d: {z: ({q: round(c * (1 - rabaty[d][z]), 2) for q, c in jak.items()} if z in rabaty.get(d, {}) else jak)
                for z, jak in zasoby.items()} for d, zasoby in bazowe.items()}
    return ceny, rabaty


def gazetki(dane: Dane, ziarno, runda: int, ceny: dict) -> dict[str, dict[str, float]]:
    """{dostawca: {zasób: rabat}} – co rundę kilka składników z oferty dostawcy z gazetką taniej."""
    wynik = {}
    for d in sorted(ceny):
        g = info(dane, d)["gazetka"]
        if not g or not ceny[d]:
            continue
        rng = strumien(ziarno, runda, "gazetki", d)
        zasoby = sorted(ceny[d])
        wybrane = sorted(int(i) for i in rng.choice(len(zasoby), size=min(g["pozycji"], len(zasoby)), replace=False))
        wynik[d] = {zasoby[i]: round(float(rng.uniform(g["rabat_min"], g["rabat_max"])), 2) for i in wybrane}
    return wynik


def zasady_dostaw(dane: Dane, zamowienia: list[dict], start: date, dni: int, czas=None) -> tuple[list[dict], dict]:
    """Zamówienia (z polem "cena") po zasadach dostaw gry z lokalami → (przyjęte, podsumowanie).

    Kolejno: dzień poza dniami dostaw dostawcy – zamówienie odrzucone; ponad limit opakowań dyskontu (na składnik
    na dzień) – ilość obcięta; dostawa (dostawca, dzień) poniżej minimalnego zamówienia – odrzucona w całości;
    dzień zakupów w dyskoncie, na który nie starcza czasu właściciela (`czas` – silnik/czas_wlasciciela.py) – odrzucony.
    Podsumowanie: {"uwagi": [tekst], "oplaty": {dostawca: zł}, "czas_wlasciciela": {dostawca: godziny},
    "dostawy": [{dostawca, dzien, data, wartosc, oplata, godziny}]}."""
    uwagi, przyjete, uzyte = [], [], {}
    for z in zamowienia:
        inf = info(dane, z["dostawca"])
        dzien = min(max(0, int(z.get("dzien") or 0)), dni - 1)
        dzien_tyg = (start + timedelta(days=dzien)).weekday()
        if dzien_tyg not in inf["dni_dostaw"]:
            dni_d = ", ".join(DNI[i] for i in inf["dni_dostaw"])
            uwagi.append(f"{z['dostawca']} nie dowozi {W_DZIEN[dzien_tyg]} – zamówienie „{z['zasob']}” odrzucone"
                         f" (dni dostaw: {dni_d}).")
            continue
        ilosc = float(z["ilosc"])
        if inf["limit_opakowan"]:
            k = (z["dostawca"], z["zasob"], dzien)
            wolne = max(0.0, inf["limit_opakowan"] - uzyte.get(k, 0.0))
            if ilosc > wolne + 1e-9:
                uwagi.append(f"{z['dostawca']}: najwyżej {inf['limit_opakowan']} opak. „{z['zasob']}” dziennie na klienta"
                             f" – {W_DZIEN[dzien_tyg]} kupiono {wolne:g} zamiast {ilosc:g}.")
                ilosc = wolne
            uzyte[k] = uzyte.get(k, 0.0) + ilosc
            if ilosc <= 0:
                continue
        przyjete.append({**z, "dzien": dzien, "ilosc": ilosc})
    wartosc = {}
    for z in przyjete:
        k = (z["dostawca"], z["dzien"])
        wartosc[k] = wartosc.get(k, 0.0) + z["ilosc"] * z["cena"]
    za_male = set()
    for (d, dz), w in sorted(wartosc.items()):
        minimum = info(dane, d)["minimalne_zamowienie"]
        if w < minimum - 1e-9:
            za_male.add((d, dz))
            dzien_tyg = (start + timedelta(days=dz)).weekday()
            uwagi.append(f"{d}: dostawa {W_DZIEN[dzien_tyg]} za {w:.2f} zł – poniżej minimalnego zamówienia"
                         f" {minimum:g} zł, odrzucona.")
    przyjete = [z for z in przyjete if (z["dostawca"], z["dzien"]) not in za_male]
    wynik = {"uwagi": uwagi, "oplaty": {}, "czas_wlasciciela": {}, "dostawy": []}
    bez_czasu = set()
    for (d, dz), w in sorted(wartosc.items(), key=lambda x: (x[0][1], x[0][0])):
        if (d, dz) in za_male:
            continue
        inf = info(dane, d)
        oplata = inf["koszt_dostawy"] if inf["darmowa_od"] is None or w < inf["darmowa_od"] - 1e-9 else 0
        godziny = inf["godziny_odbioru"] if inf["odbior_osobisty"] else 0
        data = start + timedelta(days=dz)
        if godziny and czas is not None and not czas.wez(godziny, f"Odbiór osobisty: {d} ({DNI[data.weekday()]} {data:%d.%m})",
                                                         "dostawcy"):
            bez_czasu.add((d, dz))
            uwagi.append(f"{d}: brak czasu właściciela na zakupy {W_DZIEN[data.weekday()]} ({cw.godziny(godziny)} h,"
                         f" wolne {cw.godziny(czas.wolne)} h z {cw.godziny(czas.pula)} h) – zakupy odrzucone.")
            continue
        if oplata:
            wynik["oplaty"][d] = wynik["oplaty"].get(d, 0) + oplata
        if godziny:
            wynik["czas_wlasciciela"][d] = wynik["czas_wlasciciela"].get(d, 0) + godziny
        wynik["dostawy"].append({"dostawca": d, "dzien": dz, "data": (start + timedelta(days=dz)).isoformat(),
                                 "wartosc": round(w, 2), "oplata": oplata, "godziny": godziny})
    return [z for z in przyjete if (z["dostawca"], z["dzien"]) not in bez_czasu], wynik


def ceny_miesiaca(dane: Dane, ziarno, miesiac: int, tryb: str = "dane", klucz: int | None = None) -> dict:
    """{dostawca: {zasób: {"1": cena, "2": …, "3": …}}} dla miesiąca (indeks 0 = styczeń).
    klucz – numer losowania (rundy tygodniowe: runda); brak = miesiąc, a styczeń (runda 1 Revasa) bez ofert."""
    nazwa = MIESIACE[miesiac]
    if tryb == "dane" and nazwa in dane.dostawcy:
        return dane.dostawcy[nazwa]
    if miesiac == 0 and klucz is None:
        return {}
    odch = dane.z["losowosc"]["ceny_dostawcow"]
    rng = strumien(ziarno, miesiac if klucz is None else klucz, "dostawcy")
    wynik = {}
    for (d, z, q), s in sorted(_serie(dane).items()):
        if miesiac < dane.dostawcy_wszyscy_od and d not in dane.dostawcy_pierwsi:
            continue
        e = float(np.clip(rng.normal(0, odch["odchylenie"] * odch["mnoznik_odchylenia"]), -odch["max_zmiana"], odch["max_zmiana"]))
        cena = s["baza"] * (1 + e)
        wynik.setdefault(d, {}).setdefault(z, {})[q] = float(round(cena)) if s["calkowite"] else round(cena, 2)
    return wynik


def najtansze(ceny: dict, pomin: set[str] | frozenset = frozenset()) -> dict[tuple[str, str], tuple[float, str]]:
    """{(zasób, jakość): (cena, dostawca)} – najtańsza oferta (bez dostawców z `pomin`)."""
    wynik = {}
    for d, zasoby in ceny.items():
        if d in pomin:
            continue
        for z, jak in zasoby.items():
            for q, c in jak.items():
                if (z, q) not in wynik or c < wynik[(z, q)][0]:
                    wynik[(z, q)] = (c, d)
    return wynik
