"""Auto-dostawca (Z4, przebudowa 2.11.2026, archiwum/plany/przebudowa_zakladek.md).

Lokal albo jest na auto-dostawach, albo zaopatruje się sam – całość naraz. Decyzja: "auto_dostawy": {"pozycje":
[{"zasob", "jakosc", "ilosc"}]} w `w_lokalu[lokal]` (decyzja główna – lokal główny); brak klucza / None – lokal
zaopatrywany samemu, zamówienia od dostawców do lokalu na auto-dostawach są odrzucane.

Zasady (zalozenia.yaml magazyn.auto_dostawca):
- gracz płaci od razu za całą wpisaną ilość: cena hipermarketu (Auchan – silnik/kuchnia/dostawcy.py: hipermarkety;
  bez niego najdroższa oferta) + prowizja, do tego abonament tygodniowy za lokal,
- towar leży u dostawcy (`Partia.u_dostawcy`) i co rano przyjeżdża tyle, ile lokal zużyje: nie zajmuje chłodni lokalu,
  w tygodniu zakupu się nie psuje (dostawca dokupuje świeży – partia bez terminu),
- co zostanie po tygodniu, zostaje u dostawcy: termin liczy się od ostatniego dnia tygodnia (`koniec_tygodnia`),
  a każdy następny dzień kosztuje przechowanie (zł za litr dziennie, `przechowanie`); przeterminowane wyrzuca
  dostawca (strata z powodem „u_dostawcy” – bez sanepidu),
- za mało towaru – dania wypadają z menu i sprzedaż jest stracona jak przy pustym magazynie.
"""
from __future__ import annotations

from datetime import date

from ..dane import Dane
from ..ksiegowosc import rozliczenie as rz
from ..ksiegowosc.finanse import Ksiega, Rachunek, ksieguj
from ..model import Firma, grosze
from ..nieruchomosci import per_lokal as pl
from . import swiezosc as sw

EPS = 1e-9
NAZWA = "Auto-dostawca"


def zasady(dane: Dane) -> dict | None:
    """{"od_rundy", "dostawca", "abonament", "prowizja", "przechowanie_zl_za_litr_dzien"}; None – dane bez niego."""
    return (dane.z.get("magazyn") or {}).get("auto_dostawca")


def cena(dane: Dane, ceny: dict, zasob: str, jakosc: int) -> float | None:
    """Cena zakupu bez prowizji: w hipermarkecie z założeń, a gdy go nie ma – najdroższa oferta („nienajlepsza cena”)."""
    zas = zasady(dane) or {}
    c = ceny.get(zas.get("dostawca"), {}).get(zasob, {}).get(str(jakosc))
    if c is not None:
        return c
    oferty = [z[zasob][str(jakosc)] for z in ceny.values() if str(jakosc) in z.get(zasob, {})]
    return max(oferty) if oferty else None


def zlecenia(firma: Firma, d: dict, w_lokalu: dict, runda: int) -> dict[str, dict]:
    """{lokal: decyzja auto-dostaw} – lokale, które w tej rundzie są na auto-dostawach."""
    wynik = {}
    gl = pl.glowny(firma, runda)
    if gl is not None and d.get("auto_dostawy") is not None:
        wynik[gl.id] = d["auto_dostawy"]
    for k, v in w_lokalu.items():
        if "auto_dostawy" in v:
            wynik[k] = v["auto_dostawy"]
    return {k: v for k, v in wynik.items() if v is not None and v is not False}


def lokale_na_auto(dane: Dane, firma: Firma, d: dict, w_lokalu: dict, runda: int) -> set[str]:
    zas = zasady(dane)
    if not zas or runda < zas["od_rundy"]:
        return set()
    return {k for k in zlecenia(firma, d, w_lokalu, runda) if (lok := pl.lokal(firma, k)) and lok.dziala_od <= runda}


def zamow(dane: Dane, firma: Firma, d: dict, w_lokalu: dict, runda: int, ceny: dict, ksiega: Ksiega,
          rachunek: Rachunek) -> dict:
    """Zakupy auto-dostawcy na rundę: partie u dostawcy, koszt towaru, prowizja i abonament w KPiR.
    Zwraca {"lokale": {lokal: {"pozycje", "towar", "prowizja", "abonament"}}, "uwagi": [tekst]}."""
    wynik: dict = {"lokale": {}, "uwagi": []}
    zas = zasady(dane)
    zl = zlecenia(firma, d, w_lokalu, runda) if firma.lokale else {}
    if not zas or not zl:
        return wynik
    if runda < zas["od_rundy"]:
        wynik["uwagi"].append(f"{NAZWA} – od rundy {zas['od_rundy']}.")
        return wynik
    start = dane.data_rundy(runda)
    towar, stawki = 0.0, {}
    for lok_id in sorted(zl):
        lok = pl.lokal(firma, lok_id)
        if lok is None or lok.dziala_od > runda:
            wynik["uwagi"].append(f"{NAZWA}: lokal {pl.nazwa(dane, lok_id)} jeszcze nie działa – bez auto-dostaw.")
            continue
        x = wynik["lokale"][lok_id] = {"pozycje": [], "towar": 0.0, "prowizja": 0.0, "abonament": zas["abonament"]}
        pozycje = zl[lok_id].get("pozycje") if isinstance(zl[lok_id], dict) else None
        for p in pozycje or []:
            zasob, ilosc, q = p.get("zasob"), float(p.get("ilosc") or 0), int(p.get("jakosc") or 2)
            if ilosc <= EPS or zasob not in dane.zasoby:
                continue
            c = cena(dane, ceny, zasob, q)
            if c is None:
                wynik["uwagi"].append(f"{NAZWA} ({pl.nazwa(dane, lok_id)}): nikt nie sprzedaje „{zasob}” {q}★ – pominięte.")
                continue
            partia = sw.nowa_partia(dane, zasob, q, ilosc, c, start, NAZWA, runda, lokal=lok_id)
            partia.termin, partia.u_dostawcy = None, True
            firma.partie.append(partia)
            k = f"{zasob}|{q}"
            firma.magazyn[k] = firma.magazyn.get(k, 0.0) + ilosc
            firma.wartosc_magazynu_gr[k] = firma.wartosc_magazynu_gr.get(k, 0) + grosze(ilosc * c)
            wartosc = round(ilosc * c, 2)
            x["pozycje"].append({"zasob": zasob, "jakosc": q, "ilosc": ilosc, "cena": c, "wartosc": wartosc})
            x["towar"] = round(x["towar"] + wartosc, 2)
            towar += ilosc * c
            sv = rz.stawka_zasobu(dane, zasob) or 0.0
            stawki[sv] = stawki.get(sv, 0.0) + ilosc * c
        x["prowizja"] = round(x["towar"] * zas["prowizja"], 2)
        ksieguj(firma, ksiega, rachunek, f"{NAZWA}: abonament – {pl.nazwa(dane, lok_id)}", zas["abonament"])
    if towar > 0:
        ksieguj(firma, ksiega, rachunek, f"Zakup zasobu od dostawcy: {zas['dostawca']} ({NAZWA.lower()})", towar,
                "towary", stawki=stawki)
        ksieguj(firma, ksiega, rachunek, f"{NAZWA}: prowizja {zas['prowizja']:.0%}",
                sum(x["prowizja"] for x in wynik["lokale"].values()))
    return wynik


def przechowanie(dane: Dane, firma: Firma, dzien: str, runda: int) -> list[dict]:
    """Wieczorem: towar u dostawcy z poprzednich tygodni (po zużyciu i koszu) – koszt przechowania tego dnia."""
    zas = zasady(dane)
    if not zas:
        return []
    wynik = []
    for p in sw.na_stanie(firma, dzien):
        if p.u_dostawcy and p.runda < runda and p.ilosc > EPS:
            litry = sw.miejsce(dane, p)
            wynik.append({"data": dzien, "lokal": p.lokal, "zasob": p.zasob, "jakosc": p.jakosc, "ilosc": round(p.ilosc, 3),
                          "litry": round(litry, 2), "koszt": round(litry * zas["przechowanie_zl_za_litr_dzien"], 4)})
    return wynik


def koniec_tygodnia(dane: Dane, firma: Firma, runda: int, ostatni: date) -> list[dict]:
    """Po ostatnim dniu rundy: niezużyty towar z tego tygodnia zostaje u dostawcy z terminem od ostatniego dnia.
    Zwraca [{"lokal", "zasob", "jakosc", "ilosc", "termin"}]."""
    wynik = []
    for p in firma.partie:
        if p.u_dostawcy and p.runda == runda and p.termin is None and p.ilosc > EPS:
            t = sw.termin(dane, p.zasob, ostatni)
            p.termin = t.isoformat() if t else None
            wynik.append({"lokal": p.lokal, "zasob": p.zasob, "jakosc": p.jakosc, "ilosc": round(p.ilosc, 3),
                          "termin": p.termin})
    return wynik


__all__ = ["NAZWA", "cena", "koniec_tygodnia", "lokale_na_auto", "przechowanie", "zamow", "zasady", "zlecenia"]
