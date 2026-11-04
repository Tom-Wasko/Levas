"""Grupy klientów (U24, decyzja autora 4.11.2026; dane: `dane/mapa/klienci.yaml`).

Klienci strefy to mieszanka grup (studenci, biurowi, rodziny…). Grupa ma:

- koszyk – ile chętniej niż przeciętnie bierze każde danie; wegetarianie grupy nie biorą dań mięsnych, ich część
  przechodzi na dania wege (`koszyk_grupy`). Koszyki stref zmieniają, które dania są popularne gdzie; popyt całego
  miasta na danie zostaje jak w uslugi.yaml (`mnozniki_koszyka` – normalizacja pulami stref),
- wrażliwość na cenę – mnożnik wrażliwości strefy (popyt.yaml), w strefie uśredniony do 1 (`wrazliwosc`), więc
  przeciętny klient strefy reaguje na cenę jak dotąd, a lokal z wysoką ceną traci najpierw grupy oszczędne,
- wagę czekania i jakości – w ocenie lokalu (silnik/rynek/opinie.py).

Goście wydarzeń to nadwyżka klientów z kalendarza miejskiego (mecz, koncert, festyn): w dniu z mnożnikiem kalendarza
m > 1 ich udział to 1 − 1/m. Bez pliku klienci.yaml (dane zamrożone testów) – jedna grupa, jak przed U24.
"""
from __future__ import annotations

from datetime import date

import numpy as np

from ..dane import Dane
from . import kalendarz as kal

BEZ_GRUP = "_"   # jedna grupa – gra bez klienci.yaml


def ustawienia(dane: Dane) -> dict | None:
    return (dane.mapa or {}).get("klienci")


def koszyk_grupy(dane: Dane, grupa: str) -> dict[str, float]:
    """Koszyk grupy po przeniesieniu wegetarian: dania mięsne × (1 − w), ich klienci (w porcjach popytu rocznego)
    przechodzą na dania wege proporcjonalnie do ich popytu w koszyku."""
    k = ustawienia(dane)
    g = k["grupy"][grupa]
    w, kosz = g["wegetarianie"], dict(g["koszyk"])
    roczny = {u: dane.uslugi[u]["popyt_roczny"] for u in kosz}
    wege = {u: roczny[u] * kosz[u] for u in k["wege"] if u in kosz}
    przeszli = w * sum(roczny[u] * kosz[u] for u in k["mieso"] if u in kosz)
    for u in k["mieso"]:
        if u in kosz:
            kosz[u] *= 1 - w
    if wege and sum(wege.values()):
        for u, x in wege.items():
            kosz[u] += przeszli * x / sum(wege.values()) / roczny[u]
    return kosz


def _koszyki(dane: Dane) -> dict[str, dict[str, float]]:
    return {g: koszyk_grupy(dane, g) for g in ustawienia(dane)["grupy"]}


def mnozniki_koszyka(dane: Dane) -> dict[str, dict[str, float]]:
    """{strefa: {danie: mnożnik puli}}: koszyk strefy (udziały grup × koszyki) ÷ średni koszyk miasta (ważony pulami
    stref) – popyt miasta na danie bez zmian. Bez grup – {}."""
    k = ustawienia(dane)
    if not k:
        return {}
    kosze, pule = _koszyki(dane), {z: ps["pula"] for z, ps in dane.mapa["popyt"]["strefy"].items()}
    surowe = {z: {u: sum(s * kosze[g][u] for g, s in k["strefy"][z].items()) for u in dane.uslugi} for z in pule}
    srednie = {u: sum(pule[z] * surowe[z][u] for z in pule) / sum(pule.values()) for u in dane.uslugi}
    return {z: {u: surowe[z][u] / srednie[u] if srednie[u] else 1.0 for u in dane.uslugi} for z in pule}


def wrazliwosc(dane: Dane, strefa: str) -> dict[str, float]:
    """Mnożnik wrażliwości cenowej strefy dla każdej grupy; średnia ważona udziałami grup w strefie = 1."""
    k = ustawienia(dane)
    if not k:
        return {BEZ_GRUP: 1.0}
    udz = k["strefy"][strefa]
    sr = sum(s * k["grupy"][g]["cena"] for g, s in udz.items())
    return {g: x["cena"] / sr for g, x in k["grupy"].items()}


def udzialy(dane: Dane, dni: list[date]) -> dict[str, dict[str, tuple[list[str], np.ndarray]]] | None:
    """{strefa: {danie: (grupy, udziały [grupa × dzień])}} – kto tworzy pulę dania w strefie każdego dnia (suma
    udziałów w dniu = 1). Bez grup – None."""
    k = ustawienia(dane)
    if not k:
        return None
    kosze, ev = _koszyki(dane), k["wydarzenia"]
    trwajace = [kal.aktywne(dane, d) for d in dni]
    wynik: dict = {}
    for z, udz in k["strefy"].items():
        grupy = list(udz) + [ev]
        mn_strefy = np.array([kal.mnoznik(dane, z, d) for d in dni])
        wynik[z] = {}
        for u in dane.uslugi:
            mn = mn_strefy * np.array([kal.mnoznik_dania(dane, z, u, d, t) for d, t in zip(dni, trwajace, strict=True)])
            e = np.clip(1 - 1 / np.maximum(mn, 1e-9), 0.0, 1.0)
            baza = np.array([s * kosze[g][u] for g, s in udz.items()])
            baza = baza / baza.sum() if baza.sum() else np.full(len(udz), 1 / len(udz))
            wynik[z][u] = (grupy, np.vstack([baza[:, None] * (1 - e)[None, :], e[None, :]]))
    return wynik


def sklad_stref(dane: Dane, dni: list[date]) -> dict[str, dict[str, float]]:
    """{strefa: {grupa: udział}} – kto jest klientem strefy w dniach rundy (wszystkie dania razem, wagi – popyt
    roczny dań × koszyk strefy). Bez grup – {}."""
    u = udzialy(dane, dni)
    if not u:
        return {}
    koszyk = mnozniki_koszyka(dane)
    wynik = {}
    for z, dania in u.items():
        suma: dict[str, float] = {}
        for d, (grupy, m) in dania.items():
            w = dane.uslugi[d]["popyt_roczny"] * koszyk[z][d]
            for g, x in zip(grupy, m.mean(axis=1), strict=True):
                suma[g] = suma.get(g, 0.0) + w * float(x)
        razem = sum(suma.values())
        wynik[z] = {g: round(x / razem, 3) for g, x in sorted(suma.items(), key=lambda t: -t[1]) if round(x / razem, 3) > 0}
    return wynik


def opisy(dane: Dane) -> dict[str, dict[str, str]]:
    """{grupa: {"nazwa", "opis"}} – do zakładki Klienci (żartobliwe opisy grup)."""
    k = ustawienia(dane)
    return {g: {"nazwa": x["nazwa"], "opis": x["opis"]} for g, x in k["grupy"].items()} if k else {}


def zamienniki(dane: Dane) -> tuple[dict[str, list[str]], float]:
    """({danie: inne dania z jego grupy dań}, udział klientów, którzy biorą zamiennik w lokalu bez dania)."""
    k = ustawienia(dane)
    if not k:
        return {}, 0.0
    z: dict[str, list[str]] = {}
    for grupa in k["zastepstwo"]["grupy_dan"]:
        for u in grupa:
            z.setdefault(u, []).extend(v for v in grupa if v != u)
    return z, k["zastepstwo"]["udzial"]


def wagi_oceny(dane: Dane, grupy: dict[str, float]) -> dict[str, float]:
    """Średnie wagi czekania i jakości klientów lokalu (grupy: {grupa: klienci}); bez grup – 1."""
    k = ustawienia(dane)
    razem = sum(n for g, n in grupy.items() if k and g in k["grupy"])
    if not k or not razem:
        return {"czekanie": 1.0, "jakosc": 1.0}
    return {w: sum(n * k["grupy"][g][w] for g, n in grupy.items() if g in k["grupy"]) / razem for w in ("czekanie", "jakosc")}


__all__ = ["BEZ_GRUP", "koszyk_grupy", "mnozniki_koszyka", "opisy", "sklad_stref", "udzialy", "ustawienia", "wagi_oceny",
           "wrazliwosc", "zamienniki"]
