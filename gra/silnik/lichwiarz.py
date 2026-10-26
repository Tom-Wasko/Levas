"""Lichwiarz Harpagon (gra z lokalami, dane/mapa/harpagon.yaml): pożyczka „na czarno” – od ręki, bez sprawdzania
zdolności kredytowej i poza KPiR: gotówka nie jest przychodem, spłata i odsetki nie są kosztem (na rachunku
operacje z `poza_ksiegami`). Jedna pożyczka naraz.

Kolejność w rundzie:
- początek (przed decyzjami): spłata (`harpagon_splac`: kwota), potem nowa pożyczka (`harpagon_wez`: kwota),
- po decyzjach: presja na dłużnika – w rundzie terminu życzenia, po terminie przypomnienia, od `karne_od`
  odsetki karne, od `wizyty_od` co rundę wizyta (silnik/zaleglosci.py: szkody, odpływ klientów, odejście pracownika),
- koniec rundy: odsetki od całego długu doliczane do długu.
"""
from __future__ import annotations

from . import zaleglosci as zg
from .dane import Dane
from .finanse import Ksiega, Rachunek
from .losowosc import strumien
from .model import Firma, PozyczkaHarpagona, Pracownik

EPS = 1e-6
ETAPY = {"przed": "przed terminem", "termin": "runda terminu", "przypomnienie": "przypomnienia",
         "karne": "odsetki karne", "wizyty": "wizyty"}


def ustawienia(dane: Dane) -> dict:
    return dane.mapa["harpagon"]


def po_terminie(p: PozyczkaHarpagona, runda: int) -> int:
    return runda - p.termin


def etap(dane: Dane, p: PozyczkaHarpagona | None, runda: int) -> str | None:
    if p is None:
        return None
    u, po = ustawienia(dane), po_terminie(p, runda)
    if po < 0:
        return "przed"
    if po == 0:
        return "termin"
    if po >= u["wizyty_od"]:
        return "wizyty"
    return "karne" if po >= u["karne_od"] else "przypomnienie"


def stopa(dane: Dane, p: PozyczkaHarpagona, runda: int) -> float:
    u = ustawienia(dane)
    return u["odsetki_karne_rundy"] if po_terminie(p, runda) >= u["karne_od"] else u["oprocentowanie_rundy"]


def _gotowka(firma: Firma, rachunek: Rachunek, opis: str, kwota: float) -> None:
    n = len(rachunek.operacje)
    rachunek.zapisz(firma, opis, kwota, "harpagon")
    if len(rachunek.operacje) > n:
        rachunek.operacje[-1]["poza_ksiegami"] = True


def poczatek_rundy(dane: Dane, firma: Firma, decyzje: dict, runda: int, rachunek: Rachunek) -> dict:
    u = ustawienia(dane)
    info = {"splata": 0.0, "pozyczka": 0.0, "splacona": False, "odrzucone": []}
    p = firma.harpagon
    if decyzje.get("harpagon_splac") and p:
        kwota = round(min(float(decyzje["harpagon_splac"]), p.dlug), 2)
        if kwota > firma.gotowka + EPS:
            info["odrzucone"].append({"co": f"Spłata {zg.zl(kwota)} u Harpagona",
                                      "powod": "za mało gotówki – Harpagon nie przyjmuje obietnic"})
        elif kwota > 0:
            _gotowka(firma, rachunek, "Spłata pożyczki u Harpagona (poza księgami)", -kwota)
            p.dlug = round(p.dlug - kwota, 2)
            info["splata"] = kwota
            if p.dlug <= EPS:
                firma.harpagon, info["splacona"] = None, True
    if decyzje.get("harpagon_wez"):
        kwota = round(float(decyzje["harpagon_wez"]), 2)
        if firma.harpagon:
            powod = "najpierw trzeba spłacić obecną pożyczkę"
        elif not u["min_kwota"] <= kwota <= u["maks_kwota"]:
            powod = f"Harpagon pożycza od {zg.zl(u['min_kwota'])} do {zg.zl(u['maks_kwota'])}"
        else:
            powod = None
            firma.harpagon = PozyczkaHarpagona(kwota=kwota, dlug=kwota, od_rundy=runda, termin=runda + u["termin_rund"])
            _gotowka(firma, rachunek, "Gotówka od Harpagona (poza księgami)", kwota)
            info["pozyczka"] = kwota
        if powod:
            info["odrzucone"].append({"co": f"Pożyczka {zg.zl(kwota)} od Harpagona", "powod": powod})
    return info


def presja(dane: Dane, firma: Firma, nazwa: str, runda: int, ziarno, ksiega: Ksiega,
           rachunek: Rachunek) -> tuple[dict, Pracownik | None]:
    """Presja na dłużnika w tej rundzie. Zwraca (opis do wyników, pracownik, który odszedł)."""
    u, p = ustawienia(dane), firma.harpagon
    e = etap(dane, p, runda)
    wynik = {"etap": e, "teksty": [], "wizyta": None, "odplyw": 0.0}
    if e in (None, "przed"):
        return wynik, None
    po = po_terminie(p, runda)
    wartosci = {"dlug": zg.zl(p.dlug), "kwota": zg.zl(p.kwota), "termin": str(p.termin),
                "procent": zg.procent(u["odsetki_karne_rundy"])}
    if e == "termin":
        wynik["teksty"].append(u["przed_terminem"].format_map(zg._Wartosci(wartosci)))
    elif po < u["wizyty_od"]:
        wynik["teksty"].append(u["przypomnienia"][min(po, len(u["przypomnienia"])) - 1].format_map(zg._Wartosci(wartosci)))
    if po == u["karne_od"]:
        wynik["teksty"].append(u["karne"].format_map(zg._Wartosci(wartosci)))
    odszedl = None
    if e == "wizyty":
        gen = strumien(ziarno, runda, "harpagon", nazwa)
        wynik["wizyta"], odszedl = zg.wizyta(dane, firma, u["wizyty"], gen, ksiega, rachunek, wartosci,
                                             "Naprawa szkód w lokalu")
        wynik["odplyw"] = wynik["wizyta"]["odplyw"]
        p.wizyty += 1
    return wynik, odszedl


def koniec_rundy(dane: Dane, firma: Firma, runda: int) -> dict | None:
    """Odsetki doliczane do długu (bez ruchu gotówki i bez KPiR)."""
    p = firma.harpagon
    if p is None:
        return None
    s = stopa(dane, p, runda)
    odsetki = round(p.dlug * s, 2)
    p.dlug = round(p.dlug + odsetki, 2)
    p.odsetki = round(p.odsetki + odsetki, 2)
    return {"odsetki": odsetki, "stopa": s, "dlug": p.dlug, "termin": p.termin, "po_terminie": po_terminie(p, runda)}


def stan(dane: Dane, firma: Firma, runda: int) -> dict | None:
    """Pożyczka widziana w rundzie `runda` (do widoku i wyników)."""
    p = firma.harpagon
    if p is None:
        return None
    e = etap(dane, p, runda)
    return {"kwota": p.kwota, "dlug": p.dlug, "odsetki": p.odsetki, "od_rundy": p.od_rundy, "termin": p.termin,
            "wizyty": p.wizyty, "po_terminie": po_terminie(p, runda), "etap": e, "etap_nazwa": ETAPY[e],
            "stopa": stopa(dane, p, runda)}


def bledy(dane: Dane, firma: Firma, info: dict | None, runda: int) -> list[dict]:
    wynik = [{"poziom": "czerwony", "zakladka": "harpagon", "tekst": f"{o['co']}: {o['powod']}."}
             for o in (info or {}).get("odrzucone", [])]
    p = firma.harpagon
    if p and po_terminie(p, runda) >= 0:
        wynik.append({"poziom": "pomaranczowy", "zakladka": "harpagon",
                      "tekst": f"Dług u Harpagona: {zg.zl(p.dlug)} – termin spłaty: runda {p.termin}."})
    return wynik
