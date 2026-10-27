"""Magazyn w grze z lokalami (zmiana 26.10; notatka „Ustalenia gry” – Magazyn): bez kosztu magazynowania i zwrotów.

- Wynajęta chłodnia: towar, który przy dostawie nie mieści się w chłodni lub zamrażarce lokalu, jedzie do wynajętej
  chłodni (silnik/swiezosc.py, przyjmij) – koszt za litr nadmiaru (z VAT) księgowany na koniec rundy, termin krótszy.
- Sanepid: co rundę szansa kontroli rośnie z litrami w wynajętej chłodni i wartością przeterminowanego towaru
  (strumień „sanepid”); kontrola z zastrzeżeniami to mandat poza KPiR (rodzaj „kary”) i mniejszy popyt w kolejnych
  rundach (`Firma.efekty`). Teksty kontroli – `dane/zdarzenia/magazyn.yaml`, liczby – zalozenia.yaml magazyn.sanepid.
  Higiena lokalu i skargi z historii (silnik/urzad.py, `modyfikatory`) zmieniają część szansy z problemów i mandat.
- Bank żywności: historia z `dane/zdarzenia/magazyn.yaml` (silnik/zdarzenia.py), gdy w lokalu zostało dużo jedzenia
  z krótkim terminem – `zapas_do_oddania` wybiera te partie, `oddaj` zabiera je z magazynu.
"""
from __future__ import annotations

from datetime import timedelta

from . import swiezosc as sw
from .dane import Dane
from .finanse import Ksiega, Rachunek, ksieguj
from .losowosc import strumien
from .model import Efekt, Firma, Partia

WYNAJEM = "Wynajem chłodni – Mroźnia u Mietka"
MANDAT = "Mandat sanepidu"


def zasady_sanepidu(dane: Dane) -> dict | None:
    """Liczby kontroli (zalozenia.yaml magazyn.sanepid); None – dane bez sanepidu."""
    if not dane.zdarzenia or "magazyn" not in dane.zdarzenia:
        return None
    return (dane.z.get("magazyn") or {}).get("sanepid")


def szansa_kontroli(dane: Dane, litry: float, przeterminowane: float, mod: dict | None = None) -> dict:
    """{"szansa", "problem"}: szansa kontroli w rundzie i jej część z problemów (wynajem, przeterminowany towar,
    higiena i skargi z `mod` – silnik/urzad.py)."""
    z = zasady_sanepidu(dane)
    problem = z["szansa_za_litr_wynajmu"] * litry + z["szansa_za_zl_przeterminowanych"] * przeterminowane
    if mod:
        problem = (problem + mod["dodatek"]) * mod["mnoznik"]
    szansa = min(z["szansa_max"], z["szansa_bazowa"] + problem)
    return {"szansa": round(szansa, 4), "problem": round(problem, 4)}


def mandat(dane: Dane, litry: float, przeterminowane: float, mod: dict | None = None) -> float:
    z = zasady_sanepidu(dane)
    k = z["mandat_min"] + z["mandat_za_litr_wynajmu"] * litry + z["mandat_za_zl_przeterminowanych"] * przeterminowane
    k += mod["mandat"] if mod else 0
    return float(min(z["mandat_max"], max(z["mandat_min"], round(k / 50) * 50)))


def _zl(kwota: float) -> str:
    return f"{kwota:,.0f}".replace(",", " ") + " zł"


def koniec_rundy(dane: Dane, f: Firma, runda: int, ziarno, raport: dict, ks: Ksiega, rach: Rachunek,
                 mod: dict | None = None) -> dict:
    """Koszt wynajętej chłodni i kontrola sanepidu po dniach rundy (raport świeżości z popyt.rynek_lokali).
    Zwraca {"wynajem": {"litry", "koszt"}, "sanepid": {...} | None}."""
    wyn = raport.get("wynajem") or []
    litry = round(sum(w["litry"] for w in wyn), 1)
    koszt = round(sum(w["koszt"] for w in wyn), 2)
    if koszt > 0:
        ksieguj(f, ks, rach, f"{WYNAJEM} ({litry:.0f} l)", koszt, "pozostale")
    wynik = {"wynajem": {"litry": litry, "koszt": koszt}, "sanepid": None}
    if zasady_sanepidu(dane) is None or not f.lokale:
        return wynik
    z = zasady_sanepidu(dane)
    przet = round(sum(s["wartosc"] for s in raport.get("straty", []) if s["powod"] == "termin"), 2)
    sz = szansa_kontroli(dane, litry, przet, mod)
    kontrola = {**sz, "litry": litry, "przeterminowane": przet, "kontrola": False, "mandat": 0.0, "tekst": None,
                **({"higiena": mod["higiena"], "skargi": mod["skargi"]} if mod else {})}
    wynik["sanepid"] = kontrola
    los = strumien(ziarno, runda, "sanepid", f.nazwa)
    if los.random() >= sz["szansa"]:
        return wynik
    kontrola["kontrola"] = True
    teksty = dane.zdarzenia["magazyn"]["sanepid"]
    z_mandatem = sz["problem"] > 0 and los.random() < sz["problem"] / sz["szansa"]
    lista = teksty["kontrole_mandat" if z_mandatem else "kontrole_ok"]
    tekst = lista[int(los.integers(len(lista)))]
    if z_mandatem:
        kwota = mandat(dane, litry, przet, mod)
        rach.zapisz(f, MANDAT, -kwota, "kary")
        f.efekty.append(Efekt(typ="popyt", wartosc=z["popyt_po_mandacie"], od_rundy=runda + 1,
                              do_rundy=runda + z["rund_spadku"], opis="Protokół sanepidu krąży po Lublinie"))
        kontrola.update(mandat=kwota, popyt=z["popyt_po_mandacie"], rund=z["rund_spadku"])
        tekst = tekst.replace("{kwota}", _zl(kwota)).replace("{rund}", str(z["rund_spadku"]))
    kontrola["tekst"] = " ".join(tekst.split())
    return wynik


def ryzyko(dane: Dane, f: Firma, runda: int, przeterminowane_poprzednio: float = 0.0, mod: dict | None = None) -> dict | None:
    """Szacunek do decyzji: wynajem z planu dostaw rundy i przeterminowany towar jak w poprzedniej rundzie."""
    if zasady_sanepidu(dane) is None or not f.lokale:
        return None
    plan = sw.plan_wynajmu(dane, f, runda)
    litry = round(sum(x["litry"] for x in plan), 1)
    return {**szansa_kontroli(dane, litry, przeterminowane_poprzednio, mod), "litry": litry,
            "przeterminowane": round(przeterminowane_poprzednio, 2),
            "mandat": mandat(dane, litry, przeterminowane_poprzednio, mod)}


# --- bank żywności ------------------------------------------------------------------------------------------------

def bank(dane: Dane) -> dict | None:
    return dane.zdarzenia["magazyn"]["bank_zywnosci"] if dane.zdarzenia and "magazyn" in dane.zdarzenia else None


def zapas_do_oddania(dane: Dane, f: Firma, runda: int) -> list[Partia]:
    """Partie z poprzednich rund z terminem do zasady.dni_do_terminu dni od początku rundy (jeszcze dobre)."""
    b = bank(dane)
    if not b:
        return []
    start = dane.data_rundy(runda)
    do = (start + timedelta(days=b["zasady"]["dni_do_terminu"])).isoformat()
    return [p for p in f.partie if p.runda < runda and p.termin and start.isoformat() <= p.termin <= do
            and p.ilosc > sw.EPS]


def wartosc_zapasu(dane: Dane, f: Firma, runda: int) -> float:
    return round(sum(p.wartosc_gr for p in zapas_do_oddania(dane, f, runda)) / 100, 2)


def startuje(dane: Dane, f: Firma, runda: int, ziarno) -> bool:
    """Czy w tej rundzie zaczyna się historia banku żywności (dużo jedzenia z krótkim terminem, z szansą)."""
    b = bank(dane)
    if not b or not f.lokale or any(h.historia == b["historia"]["id"] for h in f.historie):
        return False
    if wartosc_zapasu(dane, f, runda) < b["zasady"]["prog_zl"]:
        return False
    return strumien(ziarno, runda, "zdarzenia", f.nazwa, b["historia"]["id"]).random() < b["zasady"]["szansa"]


def oddaj(dane: Dane, f: Firma, runda: int) -> list[dict]:
    """Zabiera zapas z krótkim terminem (bez zapisu w KPiR – był kosztem przy zakupie). Zwraca straty (powód „bank”)."""
    dzien = dane.data_rundy(runda).isoformat()
    oddane = [sw._strata(p, p.ilosc, p.wartosc_gr, "bank", dzien) for p in zapas_do_oddania(dane, f, runda)]
    for p in zapas_do_oddania(dane, f, runda):
        p.ilosc, p.wartosc_gr = 0.0, 0
    sw.uzgodnij(f)
    return oddane


def dolicz_oddane(raport: dict, oddane: list[dict]) -> None:
    """Oddane do banku żywności – w raporcie świeżości jak straty pierwszego dnia rundy."""
    if not oddane:
        return
    raport["straty"][:0] = oddane
    n = len(raport["dni"])
    for s in oddane:
        w = raport["zasoby"].setdefault(s["zasob"], {k: [0.0] * n for k in ("dostawy", "zuzycie", "straty")})
        w.setdefault("straty", [0.0] * n)[0] = round(w["straty"][0] + s["ilosc"], 3)
    raport["wartosc_strat"] = round(sum(s["wartosc"] for s in raport["straty"]), 2)


__all__ = ["bank", "dolicz_oddane", "koniec_rundy", "mandat", "oddaj", "ryzyko", "startuje", "szansa_kontroli",
           "wartosc_zapasu", "zapas_do_oddania", "zasady_sanepidu"]
