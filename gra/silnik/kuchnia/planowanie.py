"""Planowanie: potrzebne godziny i stanowiska, zamówienia zasobów (prognoza popytu – silnik/rynek/popyt.py).
Używane przez boty i podpowiedzi w interfejsie (bez losowości – wartości oczekiwane).
"""
from __future__ import annotations

import math
from datetime import date, timedelta

from ..dane import Dane
from ..model import Firma
from .dostawcy import info as info_dostawcy
from .dostawcy import najtansze


def godziny_uslugi(dane: Dane, usluga: str, klienci: float) -> float:
    u = dane.uslugi[usluga]
    return math.ceil(klienci / u["grupa"] - 1e-9) * u["godziny_prowadzacego"]


def stanowiska_potrzebne(dane: Dane, usluga: str, klienci: float) -> int:
    return math.ceil(godziny_uslugi(dane, usluga, klienci) / dane.z["operacje"]["godziny_pracownika"] - 1e-9)


def kasjerzy_potrzebni(dane: Dane, klienci: dict[str, float]) -> int:
    h = sum(k * dane.uslugi[u]["godziny_kasy"] for u, k in klienci.items())
    return math.ceil(h / dane.z["operacje"]["godziny_pracownika"] - 1e-9) if h > 0 else 0


def zamowienie_zasobow(dane: Dane, firma: Firma, klienci: dict[str, float], ceny_dostawcow: dict, jakosc: int,
                       zapas: float, dni: list[float] | None = None, start: date | None = None,
                       dyskonty: bool = False) -> list[dict]:
    """Zamówienia (u najtańszych dostawców w danej jakości), żeby starczyło na `klienci` × zapas.
    dni – udziały dni rundy w popycie (gra z lokalami): dostawy rozbite na dni wg terminu przydatności,
    w dni dostaw dostawcy (start – data pierwszego dnia rundy). Z podziałem na dni pomija dyskonty (odbiór osobisty,
    limity) i dostawców, u których któraś dostawa nie osiąga minimalnego zamówienia. dyskonty (B8) – zakupy w jednym
    dyskoncie, który najwięcej oszczędza: składniki tańsze niż u dostawców z dowozem, codziennie do limitu opakowań
    (czas właściciela na odbiór – silnik/kuchnia/dostawcy.py: zasady_dostaw); reszta u dostawców z dowozem."""
    potrzeba = {}
    for u, k in klienci.items():
        for z, ile in dane.uslugi[u]["zasoby"].items():
            potrzeba[z] = potrzeba.get(z, 0.0) + k * zapas * ile / dane.zasoby[z]["opakowanie"]
    pomin = {d for d in ceny_dostawcow if dni and info_dostawcy(dane, d)["odbior_osobisty"]}
    z_dyskontu = []
    if dyskonty and dni:
        z_dyskontu, potrzeba = _z_dyskontu(dane, firma, potrzeba, ceny_dostawcow, jakosc, dni, pomin)
    while True:
        wynik = z_dyskontu + _zamowienia(dane, firma, potrzeba, ceny_dostawcow, jakosc, dni, start, pomin)
        wartosc = {}
        for z in wynik:
            k = (z["dostawca"], z.get("dzien", 0))
            wartosc[k] = wartosc.get(k, 0.0) + z["ilosc"] * ceny_dostawcow[z["dostawca"]][z["zasob"]][str(z["jakosc"])]
        za_male = {d for (d, _), w in wartosc.items() if w < info_dostawcy(dane, d)["minimalne_zamowienie"] - 1e-9}
        if not dni or not za_male:
            return wynik
        pomin |= za_male


def pozycje_auto_dostaw(dane: Dane, firma: Firma, klienci: dict[str, float], ceny_dostawcow: dict,
                        dostawca: str, jakosc: int, zapas: float) -> list[dict]:
    """B8: pozycje auto-dostaw (silnik/kuchnia/auto_dostawca.py) na `klienci` × zapas, bez towaru, który już
    leży w magazynie lokalu albo u dostawcy; jakość – najbliższa niższa, jaką ma `dostawca`."""
    oferty = najtansze({dostawca: ceny_dostawcow.get(dostawca, {})})
    potrzeba: dict[str, float] = {}
    for u, k in klienci.items():
        for z, ile in dane.uslugi[u]["zasoby"].items():
            potrzeba[z] = potrzeba.get(z, 0.0) + k * zapas * ile / dane.zasoby[z]["opakowanie"]
    wynik = []
    for z, p in sorted(potrzeba.items()):
        q = _jakosc_oferty(oferty, z, jakosc)
        if q is None:
            continue
        ile = math.ceil(max(0.0, p - sum(firma.magazyn.get(f"{z}|{x}", 0.0) for x in (1, 2, 3))) - 1e-9)
        if ile > 0:
            wynik.append({"zasob": z, "jakosc": q, "ilosc": ile})
    return wynik


def _jakosc_oferty(oferty: dict, zasob: str, jakosc: int) -> int | None:
    q = jakosc
    while (zasob, str(q)) not in oferty and q > 1:
        q -= 1
    return q if (zasob, str(q)) in oferty else None


def _z_dyskontu(dane: Dane, firma: Firma, potrzeba: dict[str, float], ceny_dostawcow: dict, jakosc: int,
                dni: list[float], pomin: set[str]) -> tuple[list[dict], dict[str, float]]:
    """B8: (zakupy w dyskoncie, potrzeba po nich). Dyskont – ten, w którym składniki tańsze niż u dostawców
    z dowozem dają największą oszczędność w rundzie (gazetki w cenach); zakupy dzień po dniu na popyt dnia, najwyżej
    limit opakowań składnika, zapas z magazynu i z poprzednich dni (gdy termin dłuższy niż dzień) – zmniejsza zakup."""
    dyskonty = [d for d in ceny_dostawcow if info_dostawcy(dane, d)["odbior_osobisty"]]
    inne = najtansze(ceny_dostawcow, pomin | set(dyskonty))
    plany = {}
    for d in dyskonty:
        oferty = najtansze({d: ceny_dostawcow[d]})
        plan, zysk = {}, 0.0
        for z, p in potrzeba.items():
            q = _jakosc_oferty(oferty, z, jakosc)
            if q is None:
                continue
            c = oferty[(z, str(q))][0]
            alt = inne.get((z, str(q)))
            if alt is not None and alt[0] <= c:
                continue
            plan[z] = q
            zysk += (alt[0] - c if alt else c) * p
        plany[d] = (zysk, plan)
    if not plany or max(plany.values(), key=lambda x: x[0])[0] <= 0:
        return [], potrzeba
    d, (_, plan) = max(plany.items(), key=lambda x: x[1][0])
    limit = info_dostawcy(dane, d)["limit_opakowan"] or math.inf
    suma = sum(dni) or 1.0
    wynik, reszta = [], dict(potrzeba)
    for z, q in plan.items():
        p = potrzeba[z]
        trwaly = (dane.zasoby[z].get("termin_dni") or len(dni)) > 1
        zapas = sum(firma.magazyn.get(f"{z}|{x}", 0.0) for x in (1, 2, 3))
        kupione = 0
        for i, w in enumerate(dni):
            dzis = p * w / suma
            n = int(min(limit, math.ceil(max(0.0, dzis - zapas) - 1e-9)))
            zapas = max(0.0, zapas + n - dzis) if trwaly else 0.0
            if n > 0:
                wynik.append({"dostawca": d, "zasob": z, "jakosc": q, "ilosc": n, "dzien": i})
                kupione += n
        reszta[z] = max(0.0, p - kupione)
    return wynik, reszta


def _zamowienia(dane: Dane, firma: Firma, potrzeba: dict[str, float], ceny_dostawcow: dict, jakosc: int,
                dni: list[float] | None, start: date | None, pomin: set[str]) -> list[dict]:
    oferty = najtansze(ceny_dostawcow, pomin)
    wynik = []
    for z, p in potrzeba.items():
        stan = sum(firma.magazyn.get(f"{z}|{q}", 0.0) for q in (1, 2, 3))
        q = jakosc
        while (z, str(q)) not in oferty and q > 1:
            q -= 1
        if (z, str(q)) not in oferty:
            continue
        dostawca = oferty[(z, str(q))][1]
        dozwolone = None
        if dni and start is not None:
            dni_d = info_dostawcy(dane, dostawca)["dni_dostaw"]
            dozwolone = [i for i in range(len(dni)) if (start + timedelta(days=i)).weekday() in dni_d] or None
        for dzien, brak in _dostawy(dane, z, p, stan, dni, dozwolone):
            wynik.append({"dostawca": dostawca, "zasob": z, "jakosc": q, "ilosc": brak, **({"dzien": dzien} if dni else {})})
    return wynik


def _dostawy(dane: Dane, zasob: str, potrzeba: float, stan: float, dni: list[float] | None,
             dozwolone: list[int] | None = None) -> list[tuple[int, int]]:
    """[(dzień, opakowania)]: bez podziału – jedna dostawa w poniedziałek; z podziałem – co `krok` dni (krótki termin
    albo chłodnia / zamrażarka o ograniczonej pojemności), każda na dni do następnej dostawy. Zapas z magazynu
    zmniejsza pierwszą dostawę; przy krótkim terminie resztka z dostawy nie przechodzi na następną (idzie do kosza).
    dozwolone – dni dostaw dostawcy: dostawa przesuwa się na ostatni dzień dostaw przed planowanym (albo pierwszy)."""
    if not dni:
        brak = math.ceil(max(0.0, potrzeba - stan) - 1e-9)
        return [(0, brak)] if brak > 0 else []
    z = dane.zasoby[zasob]
    termin = z.get("termin_dni") or len(dni)
    krok = min(termin, len(dni))
    if z.get("przechowywanie", "suche") != "suche":
        krok = min(krok, 3)
    przechodzi = krok < termin
    suma = sum(dni) or 1.0
    punkty = list(range(0, len(dni), krok))
    if dozwolone:
        punkty = sorted({max((d for d in dozwolone if d <= j), default=dozwolone[0]) for j in punkty})
    granice = [0, *punkty[1:], len(dni)]
    wynik, zapas = [], stan
    for i, j in enumerate(punkty):
        ile = potrzeba * sum(dni[granice[i]:granice[i + 1]]) / suma - zapas
        n = math.ceil(max(0.0, ile) - 1e-9)
        zapas = max(0.0, n - ile) if przechodzi else 0.0
        if n > 0:
            wynik.append((j, n))
    return wynik
