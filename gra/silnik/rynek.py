"""Popyt firm na usługi (model skalibrowany w kalibracja/kalibracja_popytu.py, parametry w dane/zalozenia.yaml).

popyt = popyt roczny / 12 × sezonowość × korekta miesiąca × mnożnik bazowy
        × jakość (0,4 pracownicy + 0,4 sprzęt + 0,2 zasoby)
        × exp(−E1·(r − 1)) × exp(−E2·(r − r̄)) × n^(−K)          r = cena po rabacie / cena preferowana
        × (1 + 0,06·Σ % klientów oczekujących posiadanego wyposażenia)
        × (1 + wzrost z reklamy tradycyjnej + wzrost z reklamy internetowej)
        × szum (log-normalny, ziarno gry)  → zaokrąglenie do całych klientów
"""
from __future__ import annotations

import math

import numpy as np

from .dane import MIESIACE, Dane
from .losowosc import strumien


def wspolczynnik_gwiazdek(gwiazdki: float, wsp: dict) -> float:
    """1–3★ (także ułamkowe) → mnożnik jakości; liniowo między 1★, 2★ i 3★."""
    g = min(3.0, max(1.0, gwiazdki))
    return float(np.interp(g, [1, 2, 3], [wsp["1"], wsp["2"], wsp["3"]]))


def mnoznik_jakosci(dane: Dane, pracownicy: float, sprzet: float, zasoby: float) -> float:
    p = dane.z["popyt"]
    w, wsp = p["wagi_jakosci"], p["wspolczynniki_jakosci"]
    return (w["pracownicy"] * wspolczynnik_gwiazdek(pracownicy, wsp) + w["sprzet"] * wspolczynnik_gwiazdek(sprzet, wsp)
            + w["zasoby"] * wspolczynnik_gwiazdek(zasoby, wsp)) / sum(w.values())


def koszt_emisji(medium: dict, emisje: int) -> float:
    """Cena za `emisje` emisji z progową zniżką (np. 14 emisji w dzienniku: −25%)."""
    znizka = 0
    for od, proc in medium["znizki"]:
        if emisje >= od:
            znizka = proc
    return round(emisje * medium["cena"] * (1 - znizka / 100), 2)


def wzrost_reklamy_tradycyjnej(dane: Dane, emisje: dict[str, int]) -> float:
    """Każde medium osobno, malejący przyrost z każdą emisją: Σ A_kategorii · zasięg · ln(1 + k · emisje) (postać
    „log”, analiza_od_nowa.py: walidacja „zostaw miesiąc” 3,0 pkt proc. wobec 4,3 dla nasycenia wykładniczego;
    gra ATH maj–grudzień: 60 ulotek +4,1%, 20 ulotek +3,5%, 2 × Fitness TV +6,8%). Postać „wykl”:
    Σ A · zasięg · (1 − e^(−k · emisje)). Reklama działa tylko w miesiącu emisji."""
    r = dane.z["reklama"]
    media = dane.pozycje("media_tradycyjne")
    A, k = r["tradycyjna_maks_kategorii"], r["tradycyjna_nasycenie_k"]
    if r.get("tradycyjna_postac") == "log":
        return sum(A[media[n]["kategoria"]] * media[n]["zasieg"] * math.log1p(k * e)
                   for n, e in emisje.items() if e > 0 and n in media)
    return sum(A[media[n]["kategoria"]] * media[n]["zasieg"] * (1 - math.exp(-k * e))
               for n, e in emisje.items() if e > 0 and n in media)


def wzrost_reklamy_internetowej(dane: Dane, narzedzia: dict[str, int], runda: int, narzedzia_rynku: int | None = None) -> float:
    """a · (n / (n + c·(N − n)))^b, n – aktywne narzędzia firmy, N – aktywne narzędzia wszystkich firm (narzedzia_rynku),
    c – waga narzędzia konkurenta (gra ATH czerwiec–grudzień: c ≈ 0,4; 5 z 7 narzędzi +12,7%, 1 z 11 +0,14%).
    Wyłączenie narzędzia zeruje jego efekt od razu; spadek efektu w czasie wynikał z dokładania narzędzi przez konkurentów."""
    r = dane.z["reklama"]
    n = sum(1 for od in narzedzia.values() if od <= runda)
    if n == 0:
        return 0.0
    rynek = max(n, narzedzia_rynku or n)
    # narzędzia konkurentów ważą mniej niż własne (waga c; analiza_od_nowa.py: walidacja 0,21 pkt proc. wobec 0,46 przy c = 1)
    c = r.get("internetowa_waga_konkurencji", 1.0)
    return r["internetowa_a"] * (n / (n + c * (rynek - n))) ** r["internetowa_b"]


def mnoznik_wyposazenia(dane: Dane, wyposazenie: list[str]) -> float:
    pozycje = dane.pozycje("wyposazenie")
    return 1 + dane.z["popyt"]["wyposazenie_na_procent_klientow"] * sum(pozycje[n]["procent"] / 100 for n in wyposazenie)


def mnoznik_firmy(dane: Dane, firma) -> float:
    """Czynniki całej firmy poza reklamą i wyposażeniem – oba wyłączone w dane/zalozenia.yaml (analiza_od_nowa.py):
    - baza klientów: trwała utrata klientów po utraconej sprzedaży (utrata_klientow; hipoteza odrzucona – 0),
    - sprzęt recepcji: cały 1★ → × recepcja_1gw_mnoznik (1,0), wartości pośrednie liniowo."""
    p = dane.z["popyt"]
    jak = [q for st in firma.stanowiska_typu("recepcja") for q in st.sprzet.values()]
    sr = sum(jak) / len(jak) if jak else 3.0
    rec = 1 - (1 - p["recepcja_1gw_mnoznik"]) * (3 - min(3.0, max(1.0, sr))) / 2
    return firma.baza_klientow * rec


def popyt_bazowy(dane: Dane, usluga: str, miesiac: int) -> float:
    u = dane.uslugi[usluga]
    return u["popyt_roczny"] / 12 * u["sezonowosc"][miesiac]


def popyt_rynku(dane: Dane, oferty: dict[str, dict[str, dict]], miesiac: int, ziarno, runda: int) -> dict[str, dict[str, dict]]:
    """oferty: {usługa: {firma: {"cena": po rabacie, "jakosc": (p, s, z), "wyposazenie": mnożnik, "reklama": wzrost}}}
    → {usługa: {firma: {"popyt", "r", "r_sr", "n", "skladniki"}}}"""
    p = dane.z["popyt"]
    E1, E2, K = p["elastycznosc_ceny"], p["elastycznosc_wzgledem_rynku"], p["wykladnik_liczby_firm"]
    korekta = p["korekta_miesiaca"].get(MIESIACE[miesiac], 1.0)
    wynik = {}
    for usluga, firmy in oferty.items():
        if not firmy:
            continue
        u = dane.uslugi[usluga]
        baza = popyt_bazowy(dane, usluga, miesiac)
        r = {f: o["cena"] / u["cena_preferowana"] for f, o in firmy.items()}
        r_sr, n = float(np.mean(list(r.values()))), len(firmy)
        wynik[usluga] = {}
        for f, o in firmy.items():
            q = mnoznik_jakosci(dane, *o["jakosc"])
            # postać „potega”: r^−E1 (analiza_od_nowa.py – walidacja krzyżowa 6,3% wobec 8,8% dla e^(−E1(r−1)))
            wlasna = r[f] ** (-E1) if p.get("postac_ceny") == "potega" else math.exp(-E1 * (r[f] - 1))
            cena = wlasna * math.exp(-E2 * (r[f] - r_sr)) * n ** (-K)
            szum = 1.0
            if p["szum_proc"] > 0:
                szum = float(np.exp(strumien(ziarno, runda, "popyt", f, usluga).normal(0, p["szum_proc"])))
            firma = o.get("mnoznik_firmy", 1.0)
            wartosc = baza * korekta * p["mnoznik_bazowy"] * q * cena * o["wyposazenie"] * (1 + o["reklama"]) * firma * szum
            wynik[usluga][f] = {
                "popyt": int(round(wartosc)), "r": r[f], "r_sr": r_sr, "n": n,
                "skladniki": {"baza": baza, "korekta_miesiaca": korekta, "jakosc": q, "cena": cena,
                              "wyposazenie": o["wyposazenie"], "reklama": 1 + o["reklama"], "firma": firma, "szum": szum},
            }
    return wynik
