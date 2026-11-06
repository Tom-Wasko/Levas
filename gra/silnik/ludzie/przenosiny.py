"""UF20: obsada stanowisk i przenosiny pracowników (gra z lokalami).

Decyzja `przenosiny: [{"pracownik", "typ", "nr", "dodatek"}]` – pracownik przechodzi na wolne stanowisko swojego typu:
- w tym samym lokalu – zawsze (obsada w zakładce Mój lokal);
- do innego lokalu firmy – tylko za zgodą. Szansa zgody (zalozenia.yaml: pracownicy.przenosiny):
  baza + za_zadowolenie × (zadowolenie osoby − próg odejść) − kara_za_pole × odległość lokali na mapie (pola siatki)
  + za_dodatek × min(1, dodatek ÷ pensja), w granicach [szansa_min, szansa_maks]. Dodatek (zł, jednorazowo, bez ZUS –
  jak premia) płaci się tylko po zgodzie. Pracownik w okresie wypowiedzenia nie przechodzi do innego lokalu.
Zgoda losowana przy przeliczeniu rundy (`rozstrzygnij`, z rynek_pracy.przed_decyzjami, strumień „przenosiny”);
w podglądzie decyzji przenosiny wykonują się bez losowania (panel: „czeka na odpowiedź”).
Kolejność w `decyzje.zastosuj`: zwolnienia → zmiany umów → przenosiny → zatrudnienia (zwolnione stanowisko można
od razu obsadzić nowym pracownikiem).
"""
from __future__ import annotations

import math

from ..dane import Dane
from ..ksiegowosc.finanse import Ksiega, Rachunek, ksieguj
from ..losowosc import strumien
from ..model import Firma, Pracownik, Stanowisko


def ustawienia(dane: Dane) -> dict | None:
    """Parametry zgody; None – dane bez UF20 (np. zamrożona kopia testów): pracownik zawsze się zgadza."""
    return (dane.z.get("pracownicy") or {}).get("przenosiny")


def stanowisko_pracownika(dane: Dane, f: Firma, p: Pracownik) -> Stanowisko | None:
    return f.stanowisko(dane.typ_zawodu(p.zawod), p.stanowisko)


def odleglosc(dane: Dane, a: str | None, b: str | None) -> float:
    """Odległość dwóch lokali na mapie miasta w polach siatki (ten sam lokal albo brak danych – 0)."""
    la, lb = (dane.lokale or {}).get(a or ""), (dane.lokale or {}).get(b or "")
    if a == b or not la or not lb:
        return 0.0
    return round(math.dist((la["mapa"]["x"], la["mapa"]["y"]), (lb["mapa"]["x"], lb["mapa"]["y"])), 2)


def szansa(dane: Dane, p: Pracownik, odl: float, dodatek: float) -> float:
    """Szansa, że pracownik zgodzi się przejść do lokalu oddalonego o `odl` pól za jednorazowy `dodatek` zł."""
    u = ustawienia(dane)
    if not u:
        return 1.0
    prog = ((dane.z.get("pracownicy") or {}).get("odejscia") or {}).get("prog_zadowolenia", 0.0)   # jak zadowolenie.py
    z = p.zadowolenie if p.zadowolenie is not None else prog
    za_dodatek = min(1.0, max(0.0, dodatek) / p.pensja) if p.pensja > 0 else 0.0
    x = u["baza"] + u["za_zadowolenie"] * (z - prog) - u["kara_za_pole"] * odl + u["za_dodatek"] * za_dodatek
    return round(min(u["szansa_maks"], max(u["szansa_min"], x)), 3)


def _cel(dane: Dane, f: Firma, x: dict) -> tuple[Pracownik | None, Stanowisko | None, Stanowisko | None]:
    p = f.pracownicy.get(x.get("pracownik") or "")
    if p is None:
        return None, None, None
    typ = dane.typ_zawodu(p.zawod)
    try:
        nr = int(x.get("nr") or 0)
    except (TypeError, ValueError):
        nr = 0
    cel = f.stanowisko(typ, nr) if x.get("typ", typ) == typ else None
    return p, stanowisko_pracownika(dane, f, p), cel


def miedzy_lokalami(dane: Dane, f: Firma, x: dict) -> bool:
    p, skad, cel = _cel(dane, f, x)
    return bool(p and skad and cel and skad.lokal != cel.lokal)


def rozstrzygnij(dane: Dane, f: Firma, nazwa: str, lista: list[dict], runda: int, ziarno) -> tuple[list[dict], list[dict]]:
    """Losuje zgodę na przenosiny do innego lokalu. Zwraca (przenosiny do wykonania, raport odpowiedzi)."""
    zostaja, raport = [], []
    for x in lista or []:
        if not miedzy_lokalami(dane, f, x):
            zostaja.append(x)   # w tym samym lokalu albo błędne – sprawdzi `zastosuj`
            continue
        p, skad, cel = _cel(dane, f, x)
        dodatek = max(0.0, float(x.get("dodatek") or 0))
        s = szansa(dane, p, odleglosc(dane, skad.lokal, cel.lokal), dodatek)
        zgoda = p.odchodzi is None and float(strumien(ziarno, runda, "przenosiny", nazwa, p.id).random()) < s
        raport.append({"pracownik": p.id, "imie_nazwisko": p.imie_nazwisko, "z_lokalu": skad.lokal, "do_lokalu": cel.lokal,
                       "nr": cel.nr, "typ": cel.typ, "dodatek": dodatek, "szansa": s, "zgoda": zgoda,
                       **({"powod": "jest w okresie wypowiedzenia"} if p.odchodzi else {})})
        if zgoda:
            zostaja.append({**x, "zgoda": True})
    return zostaja, raport


def zastosuj(dane: Dane, f: Firma, lista: list[dict], ksiega: Ksiega, rachunek: Rachunek) -> list[dict]:
    """Przesuwa pracowników na wskazane stanowiska (po rozstrzygnięciu zgody). Zwraca wpisy z wynikiem
    („przeniesiony” albo „nieudane” z powodem); dodatek za przejście do innego lokalu – koszt wynagrodzeń."""
    wynik = []
    for x in lista or []:
        p, skad, cel = _cel(dane, f, x)
        wpis = {"pracownik": x.get("pracownik"), "imie_nazwisko": p.imie_nazwisko if p else "?",
                "nr": cel.nr if cel else x.get("nr"), "typ": cel.typ if cel else x.get("typ"),
                "z_lokalu": skad.lokal if skad else None, "do_lokalu": cel.lokal if cel else None, "dodatek": 0.0}
        if p and skad and cel and skad.lokal != cel.lokal and not x.get("zgoda"):   # podgląd: zgoda jeszcze nieznana
            wpis["szansa"] = szansa(dane, p, odleglosc(dane, skad.lokal, cel.lokal), max(0.0, float(x.get("dodatek") or 0)))
        powod = ("pracownika już nie ma" if p is None
                 else "nie ma takiego stanowiska dla jego zawodu" if cel is None
                 else "to jego obecne stanowisko" if cel is skad
                 else "stanowisko jest zajęte" if cel.pracownik
                 else "w okresie wypowiedzenia nie przechodzi do innego lokalu"
                 if p.odchodzi and skad is not None and skad.lokal != cel.lokal else None)
        if powod:
            wynik.append({**wpis, "wynik": "nieudane", "powod": powod})
            continue
        if skad is not None:
            skad.pracownik = None
        cel.pracownik, p.stanowisko = p.id, cel.nr
        dodatek = max(0.0, float(x.get("dodatek") or 0)) if skad is not None and skad.lokal != cel.lokal else 0.0
        if dodatek:
            ksieguj(f, ksiega, rachunek, f"Dodatek za przeniesienie do innego lokalu: {p.imie_nazwisko}", dodatek, "wynagrodzenia")
        wynik.append({**wpis, "dodatek": dodatek, "wynik": "przeniesiony"})
    return wynik
