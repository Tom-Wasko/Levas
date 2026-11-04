"""Opinie klientów o lokalach (U24, decyzja autora 4.11.2026; dane: `dane/mapa/klienci.yaml`: opinie, komentarze).

Ocena tygodnia lokalu (1–5★) bierze się z przeżyć jego klientów:

    ocena = start + jakość (gwiazdki dań ponad 2 × waga jakości grup) ± cena wobec ceny strefy (z limitem)
            − kolejka (udział odesłanych z kolejki × waga czekania grup) − brak dań − reklamacje + wyposażenie

Opinie wystawia ułamek obsłużonych klientów (pojedyncza opinia ma rozrzut, średnia tygodnia – rozrzut / √n), a ocena
lokalu to średnia krocząca: waga starych opinii co tydzień × zanik. Ocena działa na popyt zamiast dawnego zadowolenia
klientów z karty: mnożnik atrakcyjności = 1 + zaufanie × ((ocena / odniesienie)^wykładnik − 1), zaufanie = W / (W + n0)
(nowy lokal bez opinii – 1). Ocenę, liczbę opinii i żartobliwe komentarze widzą na mapie wszyscy.
"""
from __future__ import annotations

import math

import numpy as np

from ..dane import Dane
from ..losowosc import Strumien, strumien
from ..model import Firma, Lokal
from . import klienci as kl

KOLEJKA = ("pracownicy/sprzęt", "kasa")   # przyczyny utraty z operacje.obsluz – klient nie doczekał się obsługi


def ustawienia(dane: Dane) -> dict | None:
    k = kl.ustawienia(dane)
    return k["opinie"] if k else None


def rodzaj_utraty(przyczyna: str) -> str:
    """Utracona sprzedaż: "kolejka" (za mało rąk, sprzętu albo kasy) albo "brak" (brak składnika lub stanowiska)."""
    return "kolejka" if przyczyna in KOLEJKA else "brak"


def zaufanie(dane: Dane, lok: Lokal) -> float:
    u = ustawienia(dane)
    return lok.waga_opinii / (lok.waga_opinii + u["n0"]) if u and lok.ocena is not None else 0.0


def mnoznik(dane: Dane, lok: Lokal) -> float:
    """Mnożnik atrakcyjności lokalu z jego oceny (bez opinii albo bez mechaniki – 1)."""
    u = ustawienia(dane)
    if not u or lok.ocena is None:
        return 1.0
    return 1 + zaufanie(dane, lok) * ((lok.ocena / u["odniesienie"]) ** u["wykladnik"] - 1)


def gwiazdki_jakosci(dane: Dane, jakosc: tuple[float, float, float]) -> float:
    """(gwiazdki kucharzy, sprzętu, składników) → średnia ważona wagami jakości dania (mapa/menu.yaml)."""
    w = dane.mapa["menu"]["jakosc"]
    p, s, z = jakosc
    return (w["kucharze"] * p + w["sprzet"] * s + w["skladniki"] * z) / (w["kucharze"] + w["sprzet"] + w["skladniki"])


def ocena_tygodnia(dane: Dane, lokal: str, wynik: dict, oferty: dict[str, dict]) -> tuple[float, dict] | None:
    """(ocena 1–5, powody {jakosc, cena, kolejka, brak, reklamacje, wyposazenie: gwiazdki}) z wyniku lokalu
    (popyt.rynek_lokali: klienci.lokale[…]) i ofert jego dań; bez sprzedaży – None."""
    u = ustawienia(dane)
    ob = wynik["obsluga"]
    sprzedane = {d: n for d, n in ob["obsluzeni"].items() if n and d in oferty}
    n = sum(sprzedane.values())
    if not u or not n:
        return None
    cena_strefy = dane.mapa["popyt"]["strefy"][dane.lokale[lokal]["strefa"]]["cena"]
    gw = sum(k * gwiazdki_jakosci(dane, oferty[d]["jakosc"]) for d, k in sprzedane.items()) / n
    r = sum(k * oferty[d]["cena"] / (dane.uslugi[d]["cena_preferowana"] * cena_strefy) for d, k in sprzedane.items()) / n
    wyp = sum(k * oferty[d].get("wyposazenie", 1.0) for d, k in sprzedane.items()) / n
    popyt = max(wynik["popyt"], n)
    wagi = kl.wagi_oceny(dane, wynik.get("grupy") or {})
    powody = {"jakosc": u["jakosc"] * wagi["jakosc"] * (gw - 2),
              "cena": max(-u["cena_limit"], min(u["cena_limit"], -u["cena"] * (r - 1))),
              "kolejka": -u["kolejka"] * wagi["czekanie"] * ob["kolejka"] / popyt,
              "brak": -u["brak"] * ob["brak"] / popyt,
              "reklamacje": -u["reklamacje"] * ob["reklamacje"] / n,
              "wyposazenie": u["wyposazenie"] * (wyp - 1)}
    return max(1.0, min(u["skala"], u["start"] + sum(powody.values()))), powody


def _klucz(powod: str, v: float) -> str | None:
    if powod in ("jakosc", "cena"):
        return f"{powod}_{'plus' if v > 0 else 'minus'}"
    return powod if powod != "wyposazenie" or v > 0 else None


def komentarze(dane: Dane, rng: Strumien, ocena: float, powody: dict, grupy: dict[str, float]) -> list[dict]:
    """Krótkie komentarze klientów do najważniejszych powodów oceny (szablony z klienci.yaml: komentarze)."""
    k = kl.ustawienia(dane)
    u = k["opinie"]
    ile, teksty = u["komentarze"], k["komentarze"]
    wybrane = [(_klucz(p, v), v) for p, v in sorted(powody.items(), key=lambda t: -abs(t[1])) if abs(v) >= u["prog_komentarza"]]
    wybrane = [(x, v) for x, v in wybrane if x and teksty.get(x)][:ile]
    while len(wybrane) < ile:
        wybrane.append(("ogolnie_plus" if ocena >= u["ocena_dobra"] else "ogolnie_srednio", 0.0))
    nazwy = [g for g, n in grupy.items() if n > 0 and g in k["grupy"]]
    wagi = np.array([grupy[g] for g in nazwy], dtype=float)
    uzyte: set[str] = set()
    wynik = []
    for klucz, v in wybrane:
        wolne = [t for t in teksty.get(klucz, []) if t not in uzyte]
        if not wolne:
            continue
        tekst = wolne[int(rng.integers(len(wolne)))]
        uzyte.add(tekst)
        podpis = "klient"
        if nazwy:
            g = nazwy[int(rng.choice(len(nazwy), p=wagi / wagi.sum()))]
            podpisy = k["grupy"][g]["podpisy"]
            podpis = podpisy[int(rng.integers(len(podpisy)))]
        wynik.append({"tekst": tekst, "gwiazdki": int(max(1, min(u["skala"], round(ocena + v)))), "podpis": podpis,
                      "powod": klucz})
    return wynik


def po_rundzie(dane: Dane, firmy: dict[str, Firma], strefowy: dict, oferty: dict[str, dict[str, dict]], runda: int,
               ziarno) -> dict[str, dict[str, dict]]:
    """Nowe opinie o lokalach po tygodniu sprzedaży: aktualizuje ocenę, liczbę opinii i komentarze lokali.
    Zwraca {firma: {lokal: {"ocena_tygodnia", "powody", "nowe", "ocena", "liczba", "mnoznik"}}} (wyniki firmy)."""
    u = ustawienia(dane)
    if not u:
        return {}
    wynik: dict = {}
    for f, lokale in oferty.items():
        firma = firmy[f]
        for lw in strefowy["klienci"][f]["lokale"]:
            lok = next((x for x in firma.lokale if x.id == lw["id"]), None)
            t = ocena_tygodnia(dane, lw["id"], lw, lokale.get(lw["id"], {})) if lok else None
            if t is None:
                continue
            ocena, powody = t
            n = round(sum(lw["obsluga"]["obsluzeni"].values()) * u["udzial_opinii"])
            if n:
                rng = strumien(ziarno, runda, "opinie", f, lok.id)
                obserwowana = max(1.0, min(u["skala"], ocena + float(rng.normal(0, u["rozrzut"] / math.sqrt(n)))))
                w = lok.waga_opinii * u["zanik"] if lok.ocena is not None else 0.0
                lok.ocena = ((lok.ocena or 0.0) * w + obserwowana * n) / (w + n)
                lok.waga_opinii = w + n
                lok.opinie += n
                lok.komentarze = komentarze(dane, rng, obserwowana, powody, lw.get("grupy") or {})
            wynik.setdefault(f, {})[lok.id] = {
                "ocena_tygodnia": round(ocena, 2), "powody": {p: round(v, 2) for p, v in powody.items()}, "nowe": n,
                "ocena": round(lok.ocena, 2) if lok.ocena is not None else None, "liczba": lok.opinie,
                "mnoznik": round(mnoznik(dane, lok), 3)}
    return wynik


def publiczne(firmy: dict[str, Firma]) -> dict[str, dict]:
    """Opinie widoczne na mieście: {lokal: {"firma", "ocena", "liczba", "komentarze"}} – lokale z opiniami."""
    return {lok.id: {"firma": n, "ocena": round(lok.ocena, 2), "liczba": lok.opinie, "komentarze": lok.komentarze}
            for n, f in firmy.items() for lok in f.lokale if lok.ocena is not None}


__all__ = ["gwiazdki_jakosci", "komentarze", "mnoznik", "ocena_tygodnia", "po_rundzie", "publiczne", "rodzaj_utraty",
           "ustawienia", "zaufanie"]
