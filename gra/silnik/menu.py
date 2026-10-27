"""Menu w grze z lokalami (krok F3a.5; dane: dane/mapa/menu.yaml, notatki/Menu i składniki.md).

- jakość dania = średnia ważona współczynników gwiazdek składników, kucharzy i sprzętu (wagi z menu.yaml; w grze
  bez lokali – wagi Revasa z zalozenia.yaml),
- danie, któremu rano brakuje składnika (razem z zamiennikiem), jest wyłączone do następnej dostawy: część jego
  klientów (zmiana_dania) bierze inne danie z menu lokalu – proporcjonalnie do popytu na nie – reszta odchodzi.
"""
from __future__ import annotations

import math

from . import swiezosc as sw
from .dane import KUCHNIA, Dane
from .model import Firma
from .operacje import sztuki_sprzetu
from .rynek import mnoznik_jakosci

EPS = 1e-9


def jakosc_dania(dane: Dane, jakosc: tuple[float, float, float]) -> float:
    """(gwiazdki kucharzy, sprzętu, składników) → mnożnik jakości dania."""
    w = (dane.mapa or {}).get("menu", {}).get("jakosc")
    if not w:
        return mnoznik_jakosci(dane, *jakosc)
    return mnoznik_jakosci(dane, *jakosc, wagi={"pracownicy": w["kucharze"], "sprzet": w["sprzet"], "zasoby": w["skladniki"]})


def wylaczone(dane: Dane, magazyn: dict, dania) -> dict[str, str]:
    """Dania bez składnika na stanie: {danie: brakujący składnik}."""
    wynik = {}
    for u in dania:
        brak = next((z for z in dane.uslugi[u]["zasoby"] if sw.dostepne(dane, magazyn, z) <= EPS), None)
        if brak:
            wynik[u] = brak
    return wynik


def przenies(dane: Dane, popyt: dict[str, int], wyl: dict[str, str]) -> tuple[dict[str, int], dict[str, int]]:
    """Klienci wyłączonych dań: część przechodzi na dania dostępne (proporcjonalnie do ich popytu, metodą największych
    reszt). Zwraca (nowy popyt dnia, {wyłączone danie: ilu przeszło})."""
    dostepne = [u for u in popyt if u not in wyl]
    nowy, przeszli = dict(popyt), {}
    if not dostepne:
        return nowy, {u: 0 for u in wyl}
    udzial = dane.mapa["menu"]["zmiana_dania"]
    wagi = {u: popyt[u] for u in dostepne} if sum(popyt[u] for u in dostepne) else {u: 1 for u in dostepne}
    suma = sum(wagi.values())
    for u in wyl:
        n = math.floor(popyt[u] * udzial + EPS)
        przeszli[u] = n
        nowy[u] -= n
        czesci = {v: n * w / suma for v, w in wagi.items()}
        cale = {v: math.floor(x + EPS) for v, x in czesci.items()}
        reszta = n - sum(cale.values())
        for v in sorted(czesci, key=lambda v: cale[v] - czesci[v])[:reszta]:
            cale[v] += 1
        for v, k in cale.items():
            nowy[v] += k
    return nowy, przeszli


__all__ = ["jakosc_dania", "przenies", "wylaczone"]


def koszt_porcji(dane: Dane, firma: Firma, danie: str) -> float:
    """Koszt składników jednej porcji (zł): po średniej cenie zapasu składnika (partie, także zamówione w tej rundzie),
    a bez zapasu – po najniższej średniej cenie z danych (dane/zasoby)."""
    koszt = 0.0
    for z, ile in dane.uslugi[danie]["zasoby"].items():
        partie = [p for p in firma.partie if p.zasob == z and p.ilosc > EPS]
        ilosc = sum(p.ilosc for p in partie)
        cena = (sum(p.wartosc_gr for p in partie) / 100 / ilosc if ilosc > EPS
                else min(dane.zasoby[z]["srednie_ceny"].values()))
        koszt += ile / dane.zasoby[z]["opakowanie"] * cena
    return koszt


def _zl(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def bledy(dane: Dane, firma: Firma, runda: int) -> list[dict]:
    """Lista błędów (F4.2) – dania w sprzedaży, gdy działa któryś lokal: brak sprzętu, brak kucharza, cena poniżej
    kosztu składników (czerwone) albo składniki ponad `lista_bledow.udzial_skladnikow` ceny (pomarańczowe)."""
    if not any(lok.dziala_od <= runda for lok in firma.lokale):
        return []
    wynik = []
    kucharze = {p.zawod for s in firma.stanowiska_typu(KUCHNIA) if (p := firma.pracownik_stanowiska(s))}
    prog = dane.z["lista_bledow"]["udzial_skladnikow"]
    for u in firma.oferta:
        if u not in firma.ceny:
            continue
        du = dane.uslugi[u]
        brak = [n for n in du["sprzet"] if not sztuki_sprzetu(firma, n)]
        if brak:
            wynik.append({"poziom": "czerwony", "zakladka": "sprzet", "danie": u, "tekst":
                          f"{du['nazwa']}: brak sprzętu ({', '.join(brak)}) – bez niego danie można najwyżej pokazać "
                          "klientom na zdjęciu. Kup sprzęt albo zdejmij danie z menu."})
        if du["prowadzacy"] not in kucharze:
            wynik.append({"poziom": "czerwony", "zakladka": "zatrudnienie", "danie": u, "tekst":
                          f"{du['nazwa']}: w kuchni nie ma nikogo z zawodem „{du['prowadzacy'].lower()}” – klienci sami "
                          "sobie tego nie zrobią (próbowali, sanepid był przeciw). Zatrudnij kogoś na stanowisko kuchni."})
        c = firma.ceny[u]
        cena, koszt = c.cena - c.rabat, koszt_porcji(dane, firma, u)
        if cena < koszt - EPS:
            wynik.append({"poziom": "czerwony", "zakladka": "oferta", "danie": u, "tekst":
                          f"{du['nazwa']}: cena {_zl(cena)} zł jest niższa niż sam koszt składników (ok. {_zl(koszt)} zł) "
                          "– każda sprzedana porcja dokłada do interesu."})
        elif cena > EPS and koszt / cena > prog:
            wynik.append({"poziom": "pomaranczowy", "zakladka": "oferta", "danie": u, "tekst":
                          f"{du['nazwa']}: składniki to ok. {koszt / cena:.0%} ceny ({_zl(koszt)} zł z {_zl(cena)} zł) – "
                          "na pensje, czynsz i zysk zostaje niewiele."})
    return wynik
