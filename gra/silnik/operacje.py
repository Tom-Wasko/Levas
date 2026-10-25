"""Obsługa klientów firmy w miesiącu: ilu klientów da się obsłużyć przy danym sprzęcie, pracownikach i zasobach.

Zasady (WIEDZA_O_GRZE.md, rozdz. 5–7):
- stanowisko instruktora/trenera = 1 prowadzący, 160 h; usługę można prowadzić na stanowisku, gdy prowadzący ma
  właściwy zawód, a na stanowisku jest cały sprzęt usługi; sprzęt stanowiska jest wspólny dla jego usług,
- zajęcia = ⌈klienci / osób w grupie⌉ (trening personalny: grupa 1), godziny = zajęcia × godziny zajęć,
- przy braku godzin klienci są obsługiwani proporcjonalnie (najpierw równy odsetek popytu, potem jak najwięcej),
- zasoby: zużycie na klienta z magazynu (opakowania, ułamki); brak zasobu ogranicza sprzedaż,
- recepcja: 0,08 h na klienta, 160 h na recepcjonistę z kompletem sprzętu recepcji; liczona po zużyciu zasobów
  (klienci utraceni przez brak recepcji zużywają zasoby – gra ATH, luty i maj),
- reklamacje: każdy obsłużony klient z prawdopodobieństwem = ryzyko reklamacji prowadzącego × mnożnik (0,15,
  skalibrowany na zużyciu zasobów w grze ATH); reklamacja zużywa
  zasoby jeszcze raz.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import linprog

from .dane import INSTRUKTOR, RECEPCJONISTA, Dane
from .losowosc import generator
from .model import Firma, Stanowisko

EPS = 1e-9


def model_puli(dane: Dane) -> bool:
    """„pula” (oficjalna gra): godziny prowadzących danego zawodu i godziny każdego rodzaju sprzętu są wspólne dla
    całego klubu – sprzęt nie musi stać na stanowisku prowadzącego (gra A/B/C online: Apex w lutym prowadził Step,
    choć zestaw stepów stał na nieobsadzonym stanowisku; obłożenie sprzętu = godziny / (sztuki × 160 h)).
    „stanowisko”: usługa tylko na stanowisku, które ma prowadzącego i cały sprzęt (wcześniejsze założenie)."""
    return dane.z["operacje"].get("model_stanowisk", "pula") == "pula"


def sztuki_sprzetu(firma: Firma, nazwa: str) -> list[int]:
    """Jakości wszystkich sztuk danego sprzętu w klubie (stanowiska instruktorów/trenerów)."""
    return [s.sprzet[nazwa] for s in firma.stanowiska_typu("instruktor") if nazwa in s.sprzet]


def stanowiska_uslugi(dane: Dane, firma: Firma, usluga: str) -> list[Stanowisko]:
    """Stanowiska, których prowadzący mogą prowadzić usługę (prowadzący właściwego zawodu + cały sprzęt:
    w modelu puli – gdziekolwiek w klubie, w modelu stanowisk – na tym samym stanowisku)."""
    u = dane.uslugi[usluga]
    pula = model_puli(dane)
    if pula and not all(sztuki_sprzetu(firma, n) for n in u["sprzet"]):
        return []
    wynik = []
    for s in firma.stanowiska_typu("instruktor"):
        p = firma.pracownik_stanowiska(s)
        if p and p.zawod == u["prowadzacy"] and (pula or all(n in s.sprzet for n in u["sprzet"])):
            wynik.append(s)
    return wynik


def recepcjonisci(dane: Dane, firma: Firma) -> list[Stanowisko]:
    return [s for s in firma.stanowiska_typu("recepcja")
            if (p := firma.pracownik_stanowiska(s)) and p.zawod == RECEPCJONISTA
            and all(n in s.sprzet for n in dane.sprzet_recepcji)]


def jakosc_uslugi(dane: Dane, firma: Firma, usluga: str) -> tuple[float, float, float] | None:
    """(gwiazdki pracowników, sprzętu, zasobów) dla usługi; None, gdy nie da się jej prowadzić."""
    st = stanowiska_uslugi(dane, firma, usluga)
    if not st:
        return None
    u = dane.uslugi[usluga]
    prac = float(np.mean([firma.pracownik_stanowiska(s).gwiazdki for s in st]))
    if model_puli(dane):
        sprz = float(np.mean([q for n in u["sprzet"] for q in sztuki_sprzetu(firma, n)]))
    else:
        sprz = float(np.mean([s.sprzet[n] for s in st for n in u["sprzet"]]))
    zas = []
    for nazwa in u["zasoby"]:
        ilosci = {q: firma.magazyn.get(f"{nazwa}|{q}", 0.0) for q in (1, 2, 3)}
        suma = sum(ilosci.values())
        zas.append(sum(q * v for q, v in ilosci.items()) / suma if suma > EPS else 1.0)
    return prac, sprz, float(np.mean(zas)) if zas else 3.0


def _przydziel_godziny(potrzeby: dict[str, float], mozliwe: dict[str, list[int]], pojemnosc: list[float],
                       wspolne: list[tuple[set[str], float]] = ()):
    """Godziny dla usług przy ograniczonych stanowiskach: najpierw równy odsetek potrzeb, potem maksimum godzin.
    wspolne: dodatkowe limity godzin dla grup usług (model puli: rodzaj sprzętu → jego usługi, sztuki × 160 h).
    Zwraca ({usługa: godziny}, {(usługa, indeks stanowiska): godziny})."""
    uslugi = [u for u in potrzeby if potrzeby[u] > EPS and mozliwe[u]]
    if not uslugi:
        return {u: 0.0 for u in potrzeby}, {}
    zm = [(u, s) for u in uslugi for s in mozliwe[u]]
    n = len(zm)
    A, b = [], []
    for s in range(len(pojemnosc)):            # godziny stanowiska
        A.append([1.0 if zs == s else 0.0 for _, zs in zm] + [0.0])
        b.append(pojemnosc[s])
    for grupa, limit in wspolne:               # godziny sprzętu (wspólne dla klubu)
        A.append([1.0 if zu in grupa else 0.0 for zu, _ in zm] + [0.0])
        b.append(limit)
    for u in uslugi:                            # nie więcej, niż potrzeba
        A.append([1.0 if zu == u else 0.0 for zu, _ in zm] + [0.0])
        b.append(potrzeby[u])
    for u in uslugi:                            # t · potrzeba ≤ przydział
        A.append([-1.0 if zu == u else 0.0 for zu, _ in zm] + [potrzeby[u]])
        b.append(0.0)
    krok1 = linprog(c=[0.0] * n + [-1.0], A_ub=A, b_ub=b, bounds=[(0, None)] * n + [(0, 1)], method="highs")
    t = krok1.x[-1] if krok1.success else 0.0
    krok2 = linprog(c=[-1.0] * n + [0.0], A_ub=A, b_ub=b, bounds=[(0, None)] * n + [(t - 1e-7, t - 1e-7)],
                    method="highs")
    x = krok2.x if krok2.success else krok1.x
    wynik, na_stanowiskach = {u: 0.0 for u in potrzeby}, {}
    for (u, s), v in zip(zm, x[:n]):
        wynik[u] += float(v)
        na_stanowiskach[(u, s)] = float(v)
    return wynik, na_stanowiskach


def obsluz(dane: Dane, firma: Firma, popyt: dict[str, int], ziarno, runda: int) -> dict:
    """Ilu klientów firma obsłuży. Zmienia magazyn (zużycie). Zwraca szczegóły do wyników."""
    godz_prac = dane.z["operacje"]["godziny_pracownika"]
    stanowiska = firma.stanowiska_typu("instruktor")
    indeks = {s.nr: i for i, s in enumerate(stanowiska)}
    mozliwe = {u: [indeks[s.nr] for s in stanowiska_uslugi(dane, firma, u)] for u in popyt}
    zajecia_potrzebne = {u: math.ceil(d / dane.uslugi[u]["grupa"] - EPS) for u, d in popyt.items()}
    potrzeby = {u: zajecia_potrzebne[u] * dane.uslugi[u]["godziny_prowadzacego"] for u in popyt}
    pojemnosc = [godz_prac if firma.pracownik_stanowiska(s) else 0.0 for s in stanowiska]
    pula = model_puli(dane)
    wspolne = []
    if pula:
        godz_sprz = dane.z["operacje"]["godziny_sprzetu"]
        for nazwa in sorted({n for u in popyt for n in dane.uslugi[u]["sprzet"]}):
            wspolne.append(({u for u in popyt if nazwa in dane.uslugi[u]["sprzet"]},
                            len(sztuki_sprzetu(firma, nazwa)) * godz_sprz))
    godziny, na_stanowiskach = _przydziel_godziny(potrzeby, mozliwe, pojemnosc, wspolne)

    obsluzeni, przyczyna = {}, {}
    for u, d in popyt.items():
        h, g = dane.uslugi[u]["godziny_prowadzacego"], dane.uslugi[u]["grupa"]
        zajecia = math.floor(godziny[u] / h + 1e-6) if h else 0
        obsluzeni[u] = min(d, zajecia * g)
        if obsluzeni[u] < d:
            przyczyna[u] = "pracownicy/sprzęt" if mozliwe[u] else "brak stanowiska z prowadzącym i sprzętem"

    # zasoby: ilu klientów wystarczy (wspólne zasoby dzielone proporcjonalnie do potrzeb)
    potrzeba = {}
    for u, k in obsluzeni.items():
        for nazwa, ile in dane.uslugi[u]["zasoby"].items():
            potrzeba[nazwa] = potrzeba.get(nazwa, 0.0) + k * ile / dane.zasoby[nazwa]["opakowanie"]
    # Brak zasobu: gra obsługuje usługi z krótszymi zajęciami w większym odsetku popytu (ATH kwiecień i grudzień:
    # obsłużeni ∝ popyt · godziny^α, α ≈ −1,55, błąd 19% wobec 32% przy podziale proporcjonalnym; α = 0 – proporcjonalnie)
    alfa = dane.z["operacje"].get("braki_wykladnik_godzin", 0.0)
    for nazwa in sorted(potrzeba, key=lambda n: -potrzeba[n]):
        dostepne = sum(firma.magazyn.get(f"{nazwa}|{q}", 0.0) for q in (1, 2, 3))
        na_kl = {u: dane.uslugi[u]["zasoby"][nazwa] / dane.zasoby[nazwa]["opakowanie"] for u in obsluzeni
                 if nazwa in dane.uslugi[u]["zasoby"] and obsluzeni[u] > 0}
        if sum(obsluzeni[u] * x for u, x in na_kl.items()) <= dostepne + EPS:
            continue
        w = {u: dane.uslugi[u]["godziny_prowadzacego"] ** alfa for u in na_kl}

        def zuzycie(lam):
            return sum(min(obsluzeni[u], lam * w[u] * obsluzeni[u]) * na_kl[u] for u in na_kl)
        lo, hi = 0.0, 1.0
        while zuzycie(hi) < dostepne - EPS and hi < 1e6:
            hi *= 2
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if zuzycie(mid) <= dostepne else (lo, mid)
        for u in na_kl:
            nowe = math.floor(min(obsluzeni[u], lo * w[u] * obsluzeni[u]) + EPS)
            if nowe < obsluzeni[u]:
                przyczyna[u] = f"zasoby ({nazwa})"
            obsluzeni[u] = nowe

    # reklamacje (losowo) – ponowne wykonanie usługi zużywa zasoby
    reklamacje = {}
    mnoznik = dane.z["losowosc"].get("reklamacje_mnoznik_ryzyka", 1.0)
    for u, k in obsluzeni.items():
        st = [stanowiska[i] for i in mozliwe[u]]
        ryzyko = mnoznik * float(np.mean([firma.pracownik_stanowiska(s).ryzyko_reklamacji for s in st])) if st else 0.0
        reklamacje[u] = int(generator(ziarno, "reklamacje", runda, firma.nazwa, u).binomial(k, ryzyko)) if k else 0

    zuzycie = {}
    for u in obsluzeni:
        for nazwa, ile in dane.uslugi[u]["zasoby"].items():
            zuzycie[nazwa] = zuzycie.get(nazwa, 0.0) + (obsluzeni[u] + reklamacje[u]) * ile / dane.zasoby[nazwa]["opakowanie"]
    zuzyte = _zuzyj(firma, zuzycie)

    # recepcja – po zużyciu zasobów: klienci utraceni przez brak recepcji zużyli już zasoby
    # (gra ATH: luty i maj – zużycie napoju = popyt + ok. 0,5%, a nie sprzedaż)
    rec = recepcjonisci(dane, firma)
    godz_rec = len(rec) * godz_prac
    potrzebne_rec = sum(obsluzeni[u] * dane.uslugi[u]["godziny_recepcji"] for u in popyt)
    if potrzebne_rec > godz_rec + EPS:
        skala = godz_rec / potrzebne_rec if potrzebne_rec else 0.0
        for u in popyt:
            nowe = math.floor(obsluzeni[u] * skala + EPS)
            if nowe < obsluzeni[u]:
                przyczyna[u] = "recepcja"
            obsluzeni[u] = nowe

    # wykorzystanie czasu i obłożenie sprzętu (godziny zajęć na stanowisku)
    godz_stanowisk = [0.0] * len(stanowiska)
    sprzet_godz = {}
    for u, k in obsluzeni.items():
        if not k or not mozliwe[u]:
            continue
        h, g = dane.uslugi[u]["godziny_prowadzacego"], dane.uslugi[u]["grupa"]
        godz_u = math.ceil(k / g - EPS) * h
        for i in mozliwe[u]:
            w = na_stanowiskach.get((u, i), 0.0) / godziny[u] if godziny[u] > EPS else 0.0
            godz_stanowisk[i] += godz_u * w
            if not pula:
                for nazwa in dane.uslugi[u]["sprzet"]:
                    klucz = f"{stanowiska[i].nr}|{nazwa}"
                    sprzet_godz[klucz] = sprzet_godz.get(klucz, 0.0) + godz_u * w
        if pula:                                  # godziny rodzaju sprzętu po równo na jego sztuki
            for nazwa in dane.uslugi[u]["sprzet"]:
                maja = [s for s in stanowiska if nazwa in s.sprzet]
                for s in maja:
                    klucz = f"{s.nr}|{nazwa}"
                    sprzet_godz[klucz] = sprzet_godz.get(klucz, 0.0) + godz_u / len(maja)
    zajete_rec = sum(obsluzeni[u] * dane.uslugi[u]["godziny_recepcji"] for u in obsluzeni)

    return {
        "obsluzeni": obsluzeni,
        "utracona": {u: popyt[u] - obsluzeni[u] for u in popyt},
        "przyczyna": przyczyna,
        "reklamacje": reklamacje,
        "zuzyte_zasoby": zuzyte,
        "godziny_stanowisk": {s.nr: godz_stanowisk[i] for i, s in enumerate(stanowiska)},
        "godziny_recepcji": zajete_rec,
        "liczba_recepcjonistow": len(rec),
        "godziny_sprzetu": sprzet_godz,
    }


def _zuzyj(firma: Firma, zuzycie: dict[str, float]) -> dict[str, dict]:
    """Zdejmuje zużycie z magazynu (najpierw najwyższa jakość) i zwraca {zasób: {"ilosc", "wartosc"}}."""
    wynik = {}
    for nazwa, ile in zuzycie.items():
        pozostalo, wartosc = ile, 0.0
        for q in (3, 2, 1):
            k = f"{nazwa}|{q}"
            stan = firma.magazyn.get(k, 0.0)
            if stan <= EPS or pozostalo <= EPS:
                continue
            bierz = min(stan, pozostalo)
            cena = firma.wartosc_magazynu.get(k, 0.0) / stan
            firma.magazyn[k] = stan - bierz
            firma.wartosc_magazynu[k] = firma.wartosc_magazynu.get(k, 0.0) - bierz * cena
            wartosc += bierz * cena
            pozostalo -= bierz
        wynik[nazwa] = {"ilosc": ile - max(pozostalo, 0.0), "wartosc": wartosc}
    return wynik


__all__ = ["obsluz", "jakosc_uslugi", "stanowiska_uslugi", "recepcjonisci", "INSTRUKTOR"]
