"""Wypadki w lokalu i ubezpieczyciel (gra z lokalami, F3b.5; notatka „Zdarzenia i historie”).

Dane: `dane/zdarzenia/losowe.yaml`. Od rundy `zasady.od_rundy` drużyna z działającym lokalem ma co rundę szansę
(`szansa_wypadku`: `zasady.szansa` + `zasady.przyrost` za każdą rundę bez wypadku, najwyżej `zasady.szansa_max`; po
wypadku od nowa – P11; strumień „wypadki”), że zacznie się u niej wypadek – historia w kilku scenach rozgrywana jak eventy
w parkach (silnik/swiat/zdarzenia.py), ale tylko w tej jednej drużynie. Naraz najwyżej jeden otwarty wypadek, żaden się nie
powtarza (`Firma.wypadki`: id → runda początku). Ok. 80% historii jest komicznych, reszta (`powazna`) – bez żartów.

Skutek `szkoda`: koszt w KPiR (pozostałe, bez VAT; najwyżej `zasady.max_strata`). Gdy firma ma polisę rodzaju
`polisa` i ochrona trwała już w rundzie początku wypadku, ubezpieczyciel zwraca (szkoda − franszyza) × pokrycie jako
przychód pozostały. Polisy – decyzja `polisy: [rodzaj, ...]` (pełna lista; bez klucza – bez zmian), trwają, dopóki
drużyna ich nie wypowie (`Firma.polisy`: rodzaj → runda początku ochrony, po `karencja_rund`). Składka co rundę od
zakupu: stala + za_lokal × liczba lokali + od_majatku × majątek (kwoty miesięczne, ubezpieczenia – zwolnione z VAT).
"""
from __future__ import annotations

from ..dane import Dane
from ..ksiegowosc.finanse import Ksiega, Rachunek, ksieguj
from ..losowosc import strumien
from ..model import Firma

ZAKLADKA = "ubezpieczenia"
SKLADKA = "Składka ubezpieczeniowa"
ODSZKODOWANIE = "Odszkodowanie"


def dane_wypadkow(dane: Dane) -> dict | None:
    return (dane.zdarzenia or {}).get("losowe")


def zasady(dane: Dane) -> dict:
    return dane_wypadkow(dane)["zasady"]


def ubezpieczyciel(dane: Dane) -> dict:
    return dane_wypadkow(dane)["ubezpieczyciel"]


def historie(dane: Dane) -> dict[str, dict]:
    w = dane_wypadkow(dane)
    return {h["id"]: h for h in w["historie"]} if w else {}


def _dziala(f: Firma, runda: int) -> bool:
    return any(lok.dziala_od <= runda for lok in f.lokale)


def rundy_bez_wypadku(dane: Dane, f: Firma, runda: int) -> int:
    """Ile rund przed tą minęło bez nowego wypadku – od ostatniego wypadku, a bez wypadków od rundy, w której
    wypadki mogą się zacząć (i działa już lokal)."""
    otwarcie = min((lok.dziala_od for lok in f.lokale), default=runda)
    poczatek = max(zasady(dane)["od_rundy"], otwarcie)
    wczesniej = [r + 1 for r in f.wypadki.values() if r < runda]
    return max(0, runda - max([poczatek, *wczesniej]))


def szansa_wypadku(dane: Dane, f: Firma, runda: int) -> float:
    z = zasady(dane)
    sufit = max(z.get("szansa_max", 1.0), z["szansa"])   # sufit nie obniża szansy bazowej
    return min(sufit, z["szansa"] + z.get("przyrost", 0.0) * rundy_bez_wypadku(dane, f, runda))


def startuje(dane: Dane, f: Firma, runda: int, ziarno) -> str | None:
    """Wypadek, który zaczyna się w tej rundzie u firmy (None – żaden). Wynik nie zależy od tego, czy runda została już
    rozegrana (wypadek z tej rundy w `Firma.wypadki` nie blokuje)."""
    if not dane_wypadkow(dane) or runda < zasady(dane)["od_rundy"] or not _dziala(f, runda):
        return None
    wczesniej = {h for h, r in f.wypadki.items() if r < runda}
    if any(oh.zrodlo == "wypadek" and oh.historia in wczesniej for oh in f.historie):
        return None   # poprzedni wypadek jeszcze trwa
    kandydaci = [h for h in historie(dane) if h not in wczesniej]
    los = strumien(ziarno, runda, "wypadki", f.nazwa)
    if not kandydaci or los.random() >= szansa_wypadku(dane, f, runda):
        return None
    return kandydaci[int(los.integers(len(kandydaci)))]


def skladka(dane: Dane, f: Firma, rodzaj: str) -> float:
    """Składka polisy za rundę dla firmy w obecnym stanie (lokale, majątek)."""
    p = ubezpieczyciel(dane)["polisy"][rodzaj]
    return dane.na_runde(round(p["stala"] + p["za_lokal"] * len(f.lokale) + p["od_majatku"] * f.majatek, 2))


def _polisa(dane: Dane, f: Firma, rodzaj: str) -> dict:
    p = ubezpieczyciel(dane)["polisy"][rodzaj]
    return {"rodzaj": rodzaj, "nazwa": p["nazwa"], "od_rundy": f.polisy[rodzaj], "skladka": skladka(dane, f, rodzaj)}


def ustaw(dane: Dane, f: Firma, d: dict, runda: int, ks: Ksiega, rach: Rachunek) -> dict:
    """Polisy z decyzji i składki rundy (po inwestycjach – składka na sprzęt liczy się od majątku po zakupach).
    Zwraca {"polisy", "nowe", "wypowiedziane", "uwagi", "skladki"}."""
    info = {"polisy": [], "nowe": [], "wypowiedziane": [], "uwagi": [], "skladki": 0.0}
    if not dane_wypadkow(dane):
        return info
    U = ubezpieczyciel(dane)
    if "polisy" in d:
        nowe: dict[str, int] = {}
        for rodzaj in d.get("polisy") or []:
            if rodzaj not in U["polisy"]:
                info["uwagi"].append(f"Nieznana polisa: {rodzaj}.")
            elif not f.lokale:
                info["uwagi"].append(f"{U['polisy'][rodzaj]['nazwa']}: polisy są dla firm z lokalem.")
            elif rodzaj not in nowe:
                nowe[rodzaj] = f.polisy.get(rodzaj, runda + U["karencja_rund"])
        info["nowe"] = [r for r in nowe if r not in f.polisy]
        info["wypowiedziane"] = [r for r in f.polisy if r not in nowe]
        f.polisy = nowe
    for rodzaj in f.polisy:
        p = _polisa(dane, f, rodzaj)
        if p["skladka"] > 0:
            ksieguj(f, ks, rach, f"{SKLADKA} – {U['nazwa']}: {p['nazwa']}", p["skladka"], "pozostale")
        info["polisy"].append(p)
    info["skladki"] = round(sum(p["skladka"] for p in info["polisy"]), 2)
    return info


def szkoda(dane: Dane, f: Firma, s: dict, h: dict, runda: int, ks: Ksiega, rach: Rachunek) -> dict:
    """Skutek szkoda: koszt (z limitem) i odszkodowanie, gdy polisa chroniła od rundy początku wypadku."""
    kwota = round(min(s["kwota"], zasady(dane)["max_strata"]), 2)
    ksieguj(f, ks, rach, f"Szkoda – {h['tytul']}: {s['opis']}", kwota, "pozostale", stawka=0)
    rodzaj, poczatek = s.get("polisa"), f.wypadki.get(h["id"], runda)
    U = ubezpieczyciel(dane)
    chroni = rodzaj is not None and rodzaj in f.polisy and f.polisy[rodzaj] <= poczatek
    odszk = 0.0
    if chroni:
        p = U["polisy"][rodzaj]
        odszk = round(max(0.0, kwota - p["franszyza"]) * p["pokrycie"], 2)
        if odszk > 0:
            ksieguj(f, ks, rach, f"{ODSZKODOWANIE} – {U['nazwa']}: {s['opis']}", odszk, "przychod_pozostaly", stawka=0)
    powod = None
    if rodzaj is None:
        powod = "tej szkody nie pokrywa żadna polisa"
    elif rodzaj not in f.polisy:
        powod = f"brak polisy: {U['polisy'][rodzaj]['nazwa']}"
    elif not chroni:
        powod = f"{U['polisy'][rodzaj]['nazwa']} chroni dopiero od rundy {f.polisy[rodzaj]} (wypadek z rundy {poczatek})"
    return {"historia": h["id"], "tytul": h["tytul"], "opis": s["opis"], "runda": runda, "kwota": kwota,
            "polisa": rodzaj, "ubezpieczona": chroni, "odszkodowanie": odszk, "powod": powod}


def bledy(info: dict | None) -> list[dict]:
    return [{"poziom": "czerwony", "zakladka": ZAKLADKA, "tekst": t} for t in (info or {}).get("uwagi", [])]


def raport(info: dict | None, zdarzenia: dict | None) -> dict:
    """Wyniki rundy: polisy i składki, szkody z wypadków i odszkodowania."""
    info = info or {"polisy": [], "nowe": [], "wypowiedziane": [], "uwagi": [], "skladki": 0.0}
    szkody = (zdarzenia or {}).get("szkody", [])
    return {**info, "szkody": szkody, "szkody_razem": round(sum(x["kwota"] for x in szkody), 2),
            "odszkodowania": round(sum(x["odszkodowanie"] for x in szkody), 2)}


def widok(dane: Dane, f: Firma, runda: int, info: dict | None, wyniki: dict, firma: str) -> dict | None:
    """Zakładka Ubezpieczenia: oferta polis (składka dla firmy po decyzjach), posiadane polisy i historia szkód."""
    if not dane_wypadkow(dane):
        return None
    U = ubezpieczyciel(dane)
    rap = [(r, (wyniki[r].get(firma) or {}).get("ubezpieczenia")) for r in sorted(wyniki) if r < runda]
    rap = [(r, x) for r, x in rap if x]
    z = zasady(dane)
    return {"nazwa": U["nazwa"], "karencja_rund": U["karencja_rund"], "od_rundy": z["od_rundy"],
            "max_strata": z["max_strata"],
            "ryzyko": {"szansa": round(szansa_wypadku(dane, f, runda), 4), "bazowa": z["szansa"],
                       "przyrost": z.get("przyrost", 0.0), "maks": z.get("szansa_max", 1.0),
                       "rundy_bez_wypadku": rundy_bez_wypadku(dane, f, runda)} if runda >= z["od_rundy"] and f.lokale else None,
            "oferta": [{"rodzaj": k, "nazwa": p["nazwa"], "opis": p["opis"], "pokrycie": p["pokrycie"],
                        "franszyza": p["franszyza"], "skladka": skladka(dane, f, k)} for k, p in U["polisy"].items()],
            "posiadane": {k: v for k, v in f.polisy.items()},
            "decyzja": info,
            "szkody": [s for _, x in rap for s in x["szkody"]],
            "skladki_razem": round(sum(x["skladki"] for _, x in rap), 2),
            "odszkodowania_razem": round(sum(x["odszkodowania"] for _, x in rap), 2)}
