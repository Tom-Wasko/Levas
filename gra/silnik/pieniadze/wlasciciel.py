"""Prywatny portfel właściciela (gra z lokalami, dane/zdarzenia/wlasciciel.yaml).

Właściciel JDG może wypłacić pieniądze z firmy na swoje potrzeby (`wyplata_wlasna`: kwota) albo dołożyć do firmy
własne pieniądze (`wplata_wlasna`: kwota). Obie operacje są poza KPiR (rodzaj „wlasciciel” na rachunku) – nie są
przychodem ani kosztem. Portfel nie liczy się do wyniku firmy ani do rankingu.

Kolejność na początku rundy (po Harpagonie): wypłata własna → klub (silnik/pieniadze/kasyno.py) → wpłata własna, więc
pieniądze wypłacone z firmy można w tej samej rundzie wydać prywatnie, a wygraną – od razu wpłacić do firmy.
"""
from __future__ import annotations

from ..dane import Dane
from ..ksiegowosc.finanse import Rachunek
from ..model import Firma, grosze
from . import kasyno as kas
from .zaleglosci import zl

ZAKLADKA = "wlasciciel"
RODZAJ = "wlasciciel"
EPS = 1e-6


def dane_portfela(dane: Dane) -> dict | None:
    return (dane.zdarzenia or {}).get("wlasciciel")


def portfel(dane: Dane, f: Firma) -> float:
    """Gotówka w prywatnym portfelu właściciela (zł); przed pierwszą operacją – oszczędności z danych."""
    if f.portfel_gr is not None:
        return f.portfel_gr / 100
    p = dane_portfela(dane)
    return float(p["portfel"]["oszczednosci"]) if p else 0.0


def _kwota(d: dict, klucz: str) -> float:
    try:
        return max(0.0, round(float(d.get(klucz) or 0), 2))
    except (TypeError, ValueError):
        return 0.0


def poczatek_rundy(dane: Dane, f: Firma, d: dict, runda: int, rachunek: Rachunek, ziarno: int | str,
                   podglad: bool = False) -> tuple[dict | None, dict | None]:
    """Wypłata własna, gry w klubie i wpłata własna. Zwraca (info portfela, info klubu – None bez zakładów).
    `podglad` – stawki z portfela schodzą, ale wynik gier jest nieznany do zamknięcia rundy."""
    if not dane_portfela(dane):
        return None, None
    stan = portfel(dane, f)
    info = {"portfel_przed": stan, "wyplata": 0.0, "wplata": 0.0, "odrzucone": []}
    chce = _kwota(d, "wyplata_wlasna")
    if chce > 0:
        kwota = round(min(chce, max(0.0, f.gotowka)), 2)
        if kwota < chce - EPS:
            info["odrzucone"].append({"co": f"Wypłata własna {zl(chce)}",
                                      "powod": f"na koncie firmy było {zl(max(0.0, f.gotowka))} – wypłacono tyle"})
        if kwota > 0:
            rachunek.zapisz(f, "Wypłata własna właściciela (poza KPiR)", -kwota, RODZAJ)
            stan, info["wyplata"] = round(stan + kwota, 2), kwota
    stan, info_kasyna = kas.rozegraj(dane, f, d, runda, ziarno, stan, podglad)
    chce = _kwota(d, "wplata_wlasna")
    if chce > 0:
        kwota = round(min(chce, stan), 2)
        if kwota < chce - EPS:
            info["odrzucone"].append({"co": f"Wpłata własna {zl(chce)}",
                                      "powod": "w prywatnym portfelu było mniej – wpłacono wszystko, co było"})
        if kwota > 0:
            rachunek.zapisz(f, "Wpłata własna właściciela (poza KPiR)", kwota, RODZAJ)
            stan, info["wplata"] = round(stan - kwota, 2), kwota
    f.portfel_gr = grosze(stan)
    info["portfel_po"] = stan
    return info, info_kasyna


def bledy(info: dict | None, info_kasyna: dict | None) -> list[dict]:
    wynik = [{"poziom": "czerwony", "zakladka": ZAKLADKA, "tekst": f"{o['co']}: {o['powod']}."}
             for o in (info or {}).get("odrzucone", [])]
    return wynik + kas.bledy(info_kasyna)


def widok(dane: Dane, fp: Firma, f: Firma, decyzja: dict | None) -> dict | None:
    """Zakładka Portfel właściciela: portfel na początku rundy, po decyzjach (szkic) i gotówka firmy."""
    if not dane_portfela(dane):
        return None
    return {"portfel_przed": portfel(dane, fp), "portfel_po": portfel(dane, f), "gotowka_firmy": fp.gotowka,
            "decyzja": decyzja}
