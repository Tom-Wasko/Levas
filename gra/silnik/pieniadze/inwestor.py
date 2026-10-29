"""Debet ponad limit i inwestor ratunkowy (Z3, warunki w dane/zalozenia.yaml → finanse.inwestor_ratunkowy).

Debet ponad limit konta na koniec rundy (silnik/pieniadze/banki.py) to alarm u mistrza gry (`w["alarm"]`). W następnej
rundzie firma nie inwestuje i nie bierze kredytów, leasingu ani lokat (BLOKOWANE); zostają Harpagon, sprzedaż majątku
i spłaty. Nowych kar nie ma – zostają tylko odsetki karne banku od debetu ponad limit.

Mistrz gry może wtedy przysłać inwestora (`Gra.ustaw_inwestora`, jeden na grę): wpłata na początku rundy najpierw
spłaca debet, reszta zostaje w kasie. Przez `rund` rund inwestor bierze `udzial` dodatniego dochodu netto rundy (poza
KPiR, przed wyrównaniem gotówki). Niezwrócona część wpłaty liczy się jak dług (karta – wskaźnik zadłużenia, majątek
netto), więc ratunek pozwala grać dalej, ale nie poprawia miejsca w rankingu.
"""
from __future__ import annotations

from ..dane import Dane
from ..ksiegowosc.finanse import Rachunek
from ..model import Firma, Inwestor
from . import banki as bk
from . import zaleglosci as zg

BLOKOWANE = {"lokal": "Nowy lokal", "przejecie": "Kupno budynku", "stanowiska": "Nowe stanowiska",
             "sprzet_kup": "Zakup sprzętu", "udogodnienia_kup": "Zakup udogodnień",
             "wyposazenie_kup": "Zakup wyposażenia", "kredyty_wez": "Nowy kredyt", "leasing_wez": "Nowy leasing",
             "lokaty_zaloz": "Nowa lokata"}


def warunki(dane: Dane) -> dict:
    return dane.z["finanse"]["inwestor_ratunkowy"]


def sprawdz(dane: Dane, f: Firma, kwota: float) -> None:
    """Czy mistrz gry może przysłać inwestora (stan po ostatniej rundzie); ValueError z powodem."""
    if f.inwestor:
        raise ValueError("Ta firma miała już inwestora ratunkowego – jeden na grę.")
    if bk.debet_ponad_limit(dane, f) <= 0:
        raise ValueError("Inwestor ratuje tylko firmę z debetem ponad limit konta.")
    if not 0 < kwota <= warunki(dane)["max_kwota"]:
        raise ValueError(f"Wpłata inwestora: najwyżej {zg.zl(warunki(dane)['max_kwota'])}.")


def przyznany(konfiguracja: dict, nazwa: str, runda: int) -> float | None:
    """Wpłata przysłana przez mistrza gry na tę rundę (konfiguracja["inwestorzy"]: {firma: {"runda", "kwota"}})."""
    p = (konfiguracja.get("inwestorzy") or {}).get(nazwa)
    return p["kwota"] if p and p["runda"] == runda else None


def poczatek_rundy(dane: Dane, f: Firma, kwota: float | None, runda: int, rachunek: Rachunek) -> dict | None:
    """Wpłata inwestora (przed decyzjami): najpierw spłata debetu, reszta w kasie."""
    if not kwota or f.inwestor:
        return None
    w = warunki(dane)
    f.inwestor = Inwestor(kwota=kwota, od_rundy=runda, do_rundy=runda + w["rund"] - 1, udzial=w["udzial"])
    rachunek.zapisz(f, "Wpłata inwestora ratunkowego (poza KPiR)", kwota, "inwestor")
    splata = round(min(f.kredyt_odnawialny, kwota), 2)
    if splata > 0:
        f.kredyt_odnawialny = round(f.kredyt_odnawialny - splata, 2)
        rachunek.zapisz(f, "Spłata kredytu odnawialnego", -splata, "kredyty")
    return {"wplata": round(kwota, 2), "splata_debetu": splata}


def blokada(dane: Dane, f: Firma, decyzje: dict) -> tuple[dict, list[dict]]:
    """Debet ponad limit na początku rundy: decyzje bez inwestycji i kredytów oraz czerwone błędy za każdą odrzuconą."""
    debet = bk.debet_ponad_limit(dane, f)
    zablokowane = [k for k in BLOKOWANE if decyzje.get(k)] if debet > 0 else []
    if not zablokowane:
        return decyzje, []
    bledy = [{"poziom": "czerwony", "zakladka": "finanse_bank",
              "tekst": f"{BLOKOWANE[k]}: zablokowane – debet ponad limit konta ({zg.zl(debet)}). Spłać debet "
                       "albo poproś mistrza gry o inwestora."} for k in zablokowane]
    return {k: v for k, v in decyzje.items() if k not in zablokowane}, bledy


def koniec_rundy(f: Firma, runda: int, dochod_netto: float, rachunek: Rachunek) -> float:
    """Udział inwestora w dodatnim dochodzie netto rundy (poza KPiR). Zwraca wypłaconą kwotę."""
    i = f.inwestor
    if i is None or runda > i.do_rundy:
        return 0.0
    udzial = round(max(0.0, dochod_netto) * i.udzial, 2)
    if udzial > 0:
        rachunek.zapisz(f, "Udział inwestora w dochodzie netto (poza KPiR)", -udzial, "inwestor")
        i.wyplacone = round(i.wyplacone + udzial, 2)
    return udzial


def raport(f: Firma, poczatek: dict | None, wyplata: float) -> dict | None:
    """Inwestor w wynikach rundy: warunki, wypłaty i niezwrócona część wpłaty (dług)."""
    i = f.inwestor
    if i is None:
        return None
    return {"kwota": i.kwota, "od_rundy": i.od_rundy, "do_rundy": i.do_rundy, "udzial": i.udzial,
            "wyplacone": i.wyplacone, "dlug": i.dlug, "wyplata": wyplata, **(poczatek or {})}


def bledy(f: Firma, poczatek: dict | None) -> list[dict]:
    """Informacja dla drużyny w rundzie wpłaty."""
    if not poczatek:
        return []
    i = f.inwestor
    splata = f", z tego {zg.zl(poczatek['splata_debetu'])} spłaciło debet" if poczatek["splata_debetu"] else ""
    return [{"poziom": "niebieski", "zakladka": "finanse_bank",
             "tekst": f"Inwestor ratunkowy wpłacił {zg.zl(i.kwota)}{splata}. Do rundy {i.do_rundy} bierze "
                      f"{i.udzial:.0%} dodatniego dochodu netto; dopóki wpłata nie wróci, liczy się jak dług."}]
