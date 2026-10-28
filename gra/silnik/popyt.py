"""Popyt strefowy (gra z lokalami; dane: `dane/mapa/popyt.yaml`) – zastępuje popyt Revasa z rynek.py.

Każda strefa ma własną pulę klientów na każde danie i każdy dzień rundy:

    pula = popyt roczny / 52 × sezonowość dania × pula strefy × miesiąc strefy × kalendarz (strefa i danie)
           × waga dnia × szum

Sezonowość dania (P14) zmienia się płynnie z dnia na dzień: 12 wartości z uslugi.yaml to środki miesięcy, między
nimi – liniowo (koniec września to już trochę październik).

Klienci strefy wybierają lokal (model logitowy z opcją zewnętrzną A_0 – bary spoza gry, obiad w domu):

    A = jakość × exp(−E · wrażliwość strefy · (cena / (cena preferowana × cena strefy) − 1)) × exp(−odległość / zasięg)
        × zadowolenie klientów firmy × wyposażenie × (1 + reklama) × mnożnik firmy
    udział lokalu w puli strefy = A / (A_0 + Σ A lokali oferujących danie)

Dwa lokale w jednej strefie dzielą tę samą pulę; lokal łapie też klientów sąsiednich stref, słabiej z odległością
(środki stref na siatce mapy). Obsługa – dzień po dniu w każdym lokalu (operacje.obsluz: godziny pracowników
i sprzętu rundy rozłożone równo na dni), więc szczyt w piątek przy zbyt małej obsadzie to utracona sprzedaż.
Dzień firmy (F3a.5): rano dostawy (swiezosc.przyjmij), dania bez składnika wyłączone – część klientów bierze inne
danie (menu.przenies), obsługa w lokalach, wieczorem przeterminowane partie do kosza (swiezosc.wyrzuc).
Reklama: na razie mnożniki Revasa (rynek.py), własny model reklamy – krok F3b.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

import numpy as np

from . import kalendarz as kal
from . import menu
from . import promocje as pm
from . import reklama as rk
from . import swiezosc as sw
from .dane import Dane
from .losowosc import strumien
from .model import Firma
from .operacje import jakosc_uslugi, kasjerzy, obsluz


def dni_rundy(dane: Dane, runda: int) -> list[date]:
    """Dni rundy (tydzień: 7 dni od poniedziałku rundy; runda miesięczna – dni miesiąca)."""
    a, b = dane.data_rundy(runda), dane.data_rundy(runda + 1)
    return [a + timedelta(days=i) for i in range((b - a).days)]


wydarzenia = kal.wydarzenia              # wydarzenia kalendarza miejskiego w dniach rundy (silnik/kalendarz.py)
mnoznik_kalendarza = kal.mnoznik


def _srodek_miesiaca(rok: int, miesiac: int) -> date:
    poczatek = date(rok, miesiac, 1)
    return poczatek + (date(rok + miesiac // 12, miesiac % 12 + 1, 1) - poczatek) / 2


def sezon(wartosci: list[float], dzien: date) -> float:
    """Sezonowość w dniu `dzien`: wartości miesięczne w środku miesiąca, pomiędzy – interpolacja liniowa."""
    srodek = _srodek_miesiaca(dzien.year, dzien.month)
    if dzien >= srodek:
        a, b = srodek, _srodek_miesiaca(dzien.year + dzien.month // 12, dzien.month % 12 + 1)
        wa, wb = wartosci[dzien.month - 1], wartosci[dzien.month % 12]
    else:
        a, b = _srodek_miesiaca(dzien.year - (dzien.month == 1), (dzien.month - 2) % 12 + 1), srodek
        wa, wb = wartosci[(dzien.month - 2) % 12], wartosci[dzien.month - 1]
    return wa + (wb - wa) * (dzien - a).days / (b - a).days


def wagi_dni(dane: Dane, strefa: str, dni: list[date], kalendarz: bool = True) -> np.ndarray:
    """Udział każdego dnia w tygodniowej puli strefy (średnio 1/7 na dzień) × kalendarz miejski."""
    p = dane.mapa["popyt"]
    tydzien = p["strefy"][strefa].get("dni") or p["dni_tygodnia"]["wagi"]
    sr = sum(tydzien) / 7
    return np.array([tydzien[d.weekday()] / sr / 7 * (kal.mnoznik(dane, strefa, d) if kalendarz else 1.0) for d in dni])


def szczyt(dane: Dane, strefa: str, runda: int) -> float:
    """Ile razy najmocniejszy dzień rundy przewyższa średni dzień (do planowania obsady)."""
    w = wagi_dni(dane, strefa, dni_rundy(dane, runda))
    return float(w.max() / w.mean()) if w.sum() > 0 else 1.0


def srodek_strefy(dane: Dane, strefa: str) -> tuple[float, float]:
    r = dane.mapa["strefy"][strefa]["mapa"]
    return r["x"] + r["szer"] / 2, r["y"] + r["gl"] / 2


def odleglosc(dane: Dane, a: str, b: str) -> float:
    """Odległość środków stref w polach siatki (ta sama strefa – 0)."""
    return 0.0 if a == b else math.dist(srodek_strefy(dane, a), srodek_strefy(dane, b))


def pule(dane: Dane, runda: int, ziarno=None, reklama: dict[str, float] | None = None) -> dict[str, dict[str, np.ndarray]]:
    """Pule klientów: strefa → danie → klienci w kolejnych dniach rundy (bez ziarna – bez szumu, wartość oczekiwana).
    reklama: {strefa: ułamek} – poszerzenie puli przez kampanie agencji reklamowych (silnik/reklama.py)."""
    p = dane.mapa["popyt"]
    dni = dni_rundy(dane, runda)
    m = dane.miesiac_rundy(runda)
    szum = p["model"]["szum_proc"]
    sezony = {u: np.array([sezon(du["sezonowosc"], d) for d in dni]) for u, du in dane.uslugi.items()}
    trwajace = [kal.aktywne(dane, d) for d in dni]
    wynik = {}
    for z, ps in p["strefy"].items():
        baza = ps["pula"] * (ps["miesiace"][m] if ps.get("miesiace") else 1.0) * len(dni) / 7
        wagi = wagi_dni(dane, z, dni)
        wynik[z] = {}
        for u, du in dane.uslugi.items():
            tyg = du["popyt_roczny"] / 52 * baza
            dania = np.array([kal.mnoznik_dania(dane, z, u, d, t) for d, t in zip(dni, trwajace, strict=True)])
            dzienne = tyg * 7 / len(dni) * wagi * sezony[u] * dania
            if ziarno is not None and szum > 0:
                dzienne = dzienne * np.exp(strumien(ziarno, runda, "popyt", "strefa", z, u).normal(0, szum, len(dni)))
            wynik[z][u] = dzienne * (1 + (reklama or {}).get(z, 0.0))
    return wynik


def mnoznik_zadowolenia(dane: Dane, zadowolenie: float | None) -> float:
    """Zadowolenie klientów firmy z poprzedniej rundy (karta wyników) → mnożnik atrakcyjności (brak karty – 1)."""
    if not zadowolenie:
        return 1.0
    m = dane.mapa["popyt"]["model"]
    return (zadowolenie / m["zadowolenie_odniesienie"]) ** m["zadowolenie_wykladnik"]


def atrakcyjnosc(dane: Dane, strefa_klienta: str, usluga: str, o: dict) -> float:
    """o: {"strefa", "cena" (po rabacie), "jakosc": (p, s, z), "wyposazenie", "reklama", "mnoznik_firmy", "zadowolenie",
    "reklama_strefy": {strefa klienta: ułamek} – kampanie agencji reklamowych firmy}."""
    p = dane.mapa["popyt"]
    ps = p["strefy"][strefa_klienta]
    r = o["cena"] / (dane.uslugi[usluga]["cena_preferowana"] * ps["cena"])
    return (menu.jakosc_dania(dane, o["jakosc"]) * math.exp(-p["model"]["elastycznosc_ceny"] * ps["wrazliwosc_ceny"] * (r - 1))
            * math.exp(-odleglosc(dane, strefa_klienta, o["strefa"]) / p["model"]["zasieg"])
            * o.get("zadowolenie", 1.0) * o.get("wyposazenie", 1.0) * o.get("mnoznik_firmy", 1.0)
            * (1 + o.get("reklama", 0.0) + (o.get("reklama_strefy") or {}).get(strefa_klienta, 0.0)))


def _promocje_strefy(o: dict, strefa_klienta: str) -> list[dict]:
    return [e for e in o.get("promocje") or () if e["strefy"] is None or strefa_klienta in e["strefy"]]


def podzial(dane: Dane, pule_rundy: dict, oferty: dict[str, dict[tuple[str, str], dict]]) -> dict:
    """Podział pul stref między lokale. oferty: {danie: {(firma, lokal): oferta}} (oferta jak w `atrakcyjnosc`,
    opcjonalnie "promocje" – efekty z promocje.efekty_ofert: przyciąganie objętych klientów w dniach z maski).
    Zwraca {(firma, lokal): {danie: {"dni": np.ndarray, "strefy": {strefa: suma}, "porcje": np.ndarray,
    "objeci": {typ promocji: np.ndarray}}}} – wartości ułamkowe; porcje – klienci + porcje gratis (2 za 1)."""
    a0 = dane.mapa["popyt"]["model"]["opcja_zewnetrzna"]
    wynik: dict = {}
    for u, lokale in oferty.items():
        for z, pz in pule_rundy.items():
            a = {}
            for k, o in lokale.items():
                a[k] = atrakcyjnosc(dane, z, u, o)
                for e in _promocje_strefy(o, z):
                    a[k] = a[k] * (1 + e["przyciaganie"] * e["maska"])
            mianownik = a0 + sum(a.values())
            for k, ak in a.items():
                klienci = pz[u] * ak / mianownik
                w = wynik.setdefault(k, {}).setdefault(u, {"dni": np.zeros(len(pz[u])), "strefy": {},
                                                           "porcje": np.zeros(len(pz[u])), "objeci": {}})
                w["dni"] = w["dni"] + klienci
                w["porcje"] = w["porcje"] + klienci
                w["strefy"][z] = float(klienci.sum())
                for e in _promocje_strefy(lokale[k], z):
                    objeci = klienci * e["maska"]
                    w["objeci"][e["typ"]] = w["objeci"].get(e["typ"], 0.0) + objeci
                    w["porcje"] = w["porcje"] + objeci * (e["porcje"] - 1)
    return wynik


def widok_lokalu(firma: Firma, lokal: str) -> Firma:
    """Firma ograniczona do stanowisk jednego lokalu (magazyn i pracownicy wspólni – zużycie idzie do firmy)."""
    return firma.model_copy(update={"stanowiska": [s for s in firma.stanowiska if s.lokal == lokal]})


def oferty_lokali(dane: Dane, firma: Firma, runda: int, ceny: dict[str, float], wspolne: dict) -> dict[str, dict]:
    """Oferty działających lokali firmy: {lokal: {danie: oferta}} – danie jest w lokalu, gdy lokal ma kasjera
    i stanowisko z pracownikiem i sprzętem dla dania. wspolne: wyposażenie, reklama, mnoznik_firmy, zadowolenie."""
    wynik = {}
    for lok in firma.lokale:
        if lok.dziala_od > runda:
            continue
        v = widok_lokalu(firma, lok.id)
        if not kasjerzy(dane, v):
            continue
        strefa = dane.lokale[lok.id]["strefa"]
        for u, cena in ceny.items():
            q = jakosc_uslugi(dane, v, u)
            if q is not None:
                wynik.setdefault(lok.id, {})[u] = {"strefa": strefa, "cena": cena, "jakosc": q, **wspolne}
    return wynik


def rynek_lokali(dane: Dane, firmy: dict[str, Firma], oferty: dict[str, dict[str, dict]], runda: int, ziarno,
                 reklama: dict[str, float] | None = None) -> dict:
    """Popyt i obsługa w grze z lokalami. oferty: {firma: {lokal: {danie: oferta}}} (z `oferty_lokali`).
    Zwraca {"popyt": {firma: {danie: n}}, "obsluga": {firma: wynik jak operacje.obsluz}, "klienci": {firma: …},
    "rynek": {danie: {firma: {"popyt", "skladniki"}}}, "strefy": {…}, "swiezosc": {firma: …},
    "promocje": {firma z promocjami: {"przychod": {danie: zł brutto}, "doplaty", "koszt_dodatkow", "typy"}}} – dane do
    wyników i zakładek „Klienci” oraz „Magazyn i świeżość”. reklama – poszerzenie pul stref (jak w `pule`).
    Popyt i sprzedaż – w porcjach (2 za 1: dwie porcje na klienta)."""
    dni = dni_rundy(dane, runda)
    pr = pule(dane, runda, ziarno, reklama)
    po_daniach: dict = {}
    for f, lokale in oferty.items():
        for lok, dania in lokale.items():
            for u, o in dania.items():
                po_daniach.setdefault(u, {})[(f, lok)] = o
    pod = podzial(dane, pr, po_daniach)

    popyt, obsluga, klienci, rynek, swiezosc, promocje = {}, {}, {}, {}, {}, {}
    zrodla: dict[str, dict[str, float]] = {}
    for f, lokale in oferty.items():
        firma = firmy[f]
        popyt[f] = {}
        dzienne = {u: {"popyt": [0] * len(dni), "sprzedaz": [0] * len(dni)} for lok in lokale for u in lokale[lok]}
        lokale_wynik, przyczyny = [], {}
        laczna = {"obsluzeni": {}, "utracona": {}, "reklamacje": {}, "zuzyte_zasoby": {}, "godziny_stanowisk": {},
                  "godziny_kasy": 0.0, "liczba_kasjerow": 0, "godziny_sprzetu": {}}
        dzien_popyt = {lok: [{u: int(round(pod[(f, lok)][u]["porcje"][i])) for u in dania} for i in range(len(dni))]
                       for lok, dania in lokale.items()}
        promo = None
        if any(o.get("promocje") for dania in lokale.values() for o in dania.values()):
            promo = promocje[f] = {"przychod": {}, "doplaty": 0.0, "koszt_dodatkow": 0.0, "typy": {}}
        widoki = {lok: widok_lokalu(firma, lok) for lok in lokale}
        sprzedaz_lokalu = {lok: 0 for lok in lokale}
        raport = _raport_swiezosci(dane, firma, dni)
        for i in range(len(dni)):
            dzien = dni[i].isoformat()
            if firma.partie:
                przyjete, straty, wynajete = sw.przyjmij(dane, firma, dzien)
                raport["wynajem"].extend(wynajete)
                for z, ile in przyjete.items():
                    raport["zasoby"].setdefault(z, _wiersz(len(dni)))["dostawy"][i] += ile
                _dodaj_straty(raport, straty, i, len(dni))
            for lok in lokale:
                d = dzien_popyt[lok][i]
                if not any(d.values()):
                    continue
                wyl = menu.wylaczone(dane, firma.magazyn, [u for u in d if d[u]])
                if wyl:
                    d, przeszli = menu.przenies(dane, d, wyl)
                    dzien_popyt[lok][i] = d
                    for u, n in przeszli.items():
                        z = raport["zamiany"].setdefault(u, {"przeszli": 0, "odeszli": 0})
                        z["przeszli"] += n
                        z["odeszli"] += d[u]
                        raport["wylaczone"].append({"data": dzien, "lokal": lok, "danie": u, "skladnik": wyl[u]})
                o = obsluz(dane, widoki[lok], d, ziarno, runda, skala_godzin=1 / len(dni), klucze=(lok, i),
                           dzien=dzien if firma.partie else None)
                for n, z in o["zuzyte_zasoby"].items():
                    raport["zasoby"].setdefault(n, _wiersz(len(dni)))["zuzycie"][i] += z["ilosc"]
                for u, k in o["obsluzeni"].items():
                    laczna["obsluzeni"][u] = laczna["obsluzeni"].get(u, 0) + k
                    laczna["utracona"][u] = laczna["utracona"].get(u, 0) + o["utracona"][u]
                    laczna["reklamacje"][u] = laczna["reklamacje"].get(u, 0) + o["reklamacje"][u]
                    dzienne[u]["popyt"][i] += d[u]
                    dzienne[u]["sprzedaz"][i] += k
                    sprzedaz_lokalu[lok] += k
                    if promo is not None:
                        _rozlicz_promocje(promo, u, k, lokale[lok][u], pod[(f, lok)][u], i)
                    if o["utracona"][u]:
                        p = przyczyny.setdefault(u, {})
                        p[o["przyczyna"][u]] = p.get(o["przyczyna"][u], 0) + o["utracona"][u]
                for n, z in o["zuzyte_zasoby"].items():
                    x = laczna["zuzyte_zasoby"].setdefault(n, {"ilosc": 0.0, "wartosc": 0.0})
                    x["ilosc"] += z["ilosc"]
                    x["wartosc"] += z["wartosc"]
                for klucz in ("godziny_stanowisk", "godziny_sprzetu"):
                    for k, h in o[klucz].items():
                        laczna[klucz][k] = laczna[klucz].get(k, 0.0) + h
                laczna["godziny_kasy"] += o["godziny_kasy"]
            if firma.partie:
                _dodaj_straty(raport, sw.wyrzuc(firma, dzien), i, len(dni))
                raport["zajetosc"].append(sw.zajete(dane, firma, dzien))
        sw.uzgodnij(firma)
        swiezosc[f] = _zakoncz_raport(raport)
        laczna["liczba_kasjerow"] = sum(len(kasjerzy(dane, v)) for v in widoki.values())
        laczna["przyczyna"] = {u: max(p, key=p.get) for u, p in przyczyny.items()}
        for u in dzienne:
            laczna["obsluzeni"].setdefault(u, 0)
            laczna["reklamacje"].setdefault(u, 0)
            popyt[f][u] = sum(dzienne[u]["popyt"])
            laczna["utracona"][u] = popyt[f][u] - laczna["obsluzeni"][u]
        obsluga[f] = laczna
        for lok, dania in lokale.items():
            strefy_lok: dict[str, float] = {}
            for u in dania:
                for z, x in pod[(f, lok)][u]["strefy"].items():
                    strefy_lok[z] = strefy_lok.get(z, 0.0) + x
                    zrodla.setdefault(z, {})[f] = zrodla.get(z, {}).get(f, 0.0) + x
            lokale_wynik.append({"id": lok, "nazwa": dane.lokale[lok]["nazwa"], "strefa": dane.lokale[lok]["strefa"],
                                 "popyt": sum(sum(dd.values()) for dd in dzien_popyt[lok]), "sprzedaz": sprzedaz_lokalu[lok],
                                 "dania": {u: sum(dd[u] for dd in dzien_popyt[lok]) for u in dania},
                                 "strefy": {z: int(round(x)) for z, x in sorted(strefy_lok.items(), key=lambda t: -t[1]) if round(x)}})
        klienci[f] = {"dni": [{"data": dni[i].isoformat(), "dzien": dane.mapa["popyt"]["dni_tygodnia"]["nazwy"][dni[i].weekday()],
                               "popyt": sum(x["popyt"][i] for x in dzienne.values()),
                               "sprzedaz": sum(x["sprzedaz"][i] for x in dzienne.values())} for i in range(len(dni))],
                      "dania": dzienne, "lokale": lokale_wynik}
        for d in klienci[f]["dni"]:
            d["utracona"] = d["popyt"] - d["sprzedaz"]
        for u in dzienne:
            rynek.setdefault(u, {})[f] = {"popyt": popyt[f][u], "skladniki": {
                "lokale": {lok: sum(dd[u] for dd in dzien_popyt[lok]) for lok, dania in lokale.items() if u in dania}}}

    strefy = {}
    for z, pz in pr.items():
        dzien = [int(round(sum(pz[u][i] for u in pz))) for i in range(len(dni))]
        strefy[z] = {"pula": sum(dzien), "dni": dzien,
                     "klienci": {f: int(round(x)) for f, x in sorted(zrodla.get(z, {}).items())}}
    return {"popyt": popyt, "obsluga": obsluga, "klienci": klienci, "rynek": rynek, "swiezosc": swiezosc,
            "strefy": {"strefy": strefy, "dni": [d.isoformat() for d in dni], "wydarzenia": wydarzenia(dane, dni)},
            "promocje": promocje}


def _rozlicz_promocje(promo: dict, u: str, k: int, o: dict, w: dict, i: int) -> None:
    """Sprzedaż dania w lokalu w dniu i: przychód z rabatami promocji, dopłaty, koszt dodatków, liczby objętych."""
    if not o.get("promocje"):
        promo["przychod"][u] = promo["przychod"].get(u, 0.0) + k * o["cena"]
        return
    x = pm.rozlicz(k, o["cena"], float(w["dni"][i]), {t: float(v[i]) for t, v in w["objeci"].items()}, o["promocje"])
    promo["przychod"][u] = promo["przychod"].get(u, 0.0) + x["przychod"]
    promo["doplaty"] += x["doplaty"]
    promo["koszt_dodatkow"] += x["koszt_dodatkow"]
    for t, v in x["typy"].items():
        acc = promo["typy"].setdefault(t, {})
        for kl, n in v.items():
            acc[kl] = acc.get(kl, 0.0) + n


def _wiersz(n: int) -> dict:
    return {"dostawy": [0.0] * n, "zuzycie": [0.0] * n, "straty": [0.0] * n}


def _raport_swiezosci(dane: Dane, firma: Firma, dni: list[date]) -> dict:
    return {"dni": [d.isoformat() for d in dni], "zasoby": {}, "straty": [], "zamiany": {}, "wylaczone": [],
            "pojemnosc": sw.pojemnosc(dane, firma), "zajetosc": [], "wynajem": []}


def _dodaj_straty(raport: dict, straty: list[dict], i: int, n: int) -> None:
    raport["straty"].extend(straty)
    for s in straty:
        raport["zasoby"].setdefault(s["zasob"], _wiersz(n))["straty"][i] += s["ilosc"]


def _zakoncz_raport(raport: dict) -> dict:
    for w in raport["zasoby"].values():
        for k in w:
            w[k] = [round(x, 3) for x in w[k]]
    raport["wartosc_strat"] = round(sum(s["wartosc"] for s in raport["straty"]), 2)
    raport["zajetosc"] = [{k: round(v, 1) for k, v in z.items()} for z in raport["zajetosc"]]
    return raport


def prognoza(dane: Dane, runda: int, oferty: dict[str, dict[str, dict]], firma: str,
             reklama: dict[str, float] | None = None) -> dict:
    """Oczekiwany popyt w porcjach (bez szumu) lokali firmy w rundzie: {"dania": {danie: n}, "lokale": {lokal: {danie: n}},
    "dni": [n …]}. oferty jak w `rynek_lokali` – konkurenci z danych publicznych (ceny z poprzedniej rundy)."""
    po_daniach: dict = {}
    for f, lokale in oferty.items():
        for lok, dania in lokale.items():
            for u, o in dania.items():
                po_daniach.setdefault(u, {})[(f, lok)] = o
    pod = podzial(dane, pule(dane, runda, reklama=reklama), po_daniach)
    dania, lokale, dni = {}, {}, None
    for (f, lok), x in pod.items():
        if f != firma:
            continue
        for u, w in x.items():
            n = float(w["porcje"].sum())
            dania[u] = dania.get(u, 0.0) + n
            lokale.setdefault(lok, {})[u] = round(n, 1)
            dni = w["porcje"] if dni is None else dni + w["porcje"]
    return {"dania": {u: round(n, 1) for u, n in dania.items()}, "lokale": lokale,
            "dni": [round(float(x), 1) for x in dni] if dni is not None else []}


def potencjal_stref(dane: Dane, runda: int, oferty: dict[str, dict[str, dict]], dania: list[str],
                    reklama: dict[str, float] | None = None) -> dict[str, float]:
    """Szacunek popytu na `dania` w nowym lokalu 2★ po cenach preferowanych strefy w każdej strefie, przy obecnych
    lokalach konkurencji (do wyboru miejsca)."""
    pr = pule(dane, runda, reklama=reklama)
    wynik = {}
    for z, ps in dane.mapa["popyt"]["strefy"].items():
        po_daniach: dict = {}
        for f, lokale in oferty.items():
            for lok, ofl in lokale.items():
                for u, o in ofl.items():
                    if u in dania:
                        po_daniach.setdefault(u, {})[(f, lok)] = o
        for u in dania:
            po_daniach.setdefault(u, {})[("_nowy", z)] = {
                "strefa": z, "cena": dane.uslugi[u]["cena_preferowana"] * ps["cena"], "jakosc": (2, 2, 2)}
        pod = podzial(dane, pr, po_daniach)
        wynik[z] = round(sum(float(w["dni"].sum()) for w in pod[("_nowy", z)].values()), 0)
    return wynik


def oferty_konkurencji(dane: Dane, stan, runda: int, firma: str) -> dict[str, dict[str, dict]]:
    """Oferty działających lokali innych firm z danych publicznych (do prognoz): ceny z poprzedniej rundy (bez nich –
    cena preferowana strefy), jakość 2★. Format jak `oferty_lokali` dla `rynek_lokali` / `prognoza`."""
    ceny = (stan.rynek.get(runda - 1) or {}).get("ceny", {})
    wynik: dict = {}
    for n, g in stan.firmy.items():
        if n == firma:
            continue
        dania = [u for u in ceny if n in ceny[u]] or list(g.oferta)
        for lok in g.lokale:
            if lok.dziala_od > runda:
                continue
            strefa = dane.lokale[lok.id]["strefa"]
            for u in dania:
                c = ceny.get(u, {}).get(n) or dane.uslugi[u]["cena_preferowana"] * dane.mapa["popyt"]["strefy"][strefa]["cena"]
                wynik.setdefault(n, {}).setdefault(lok.id, {})[u] = {"strefa": strefa, "cena": c, "jakosc": (2, 2, 2)}
        if n in wynik:
            pm.efekty_ofert(dane, g, wynik[n], runda, dni_rundy(dane, runda))   # promocje są widoczne na mieście
    return wynik


def widok_popytu(dane: Dane, stan, firma: Firma, runda: int, zadowolenie: float | None = None) -> dict:
    """Zakładka „Klienci i strefy” (decyzje): dni rundy sprzedaży z wydarzeniami, pule stref i potencjał nowego lokalu
    (zakładka Lokale; własne lokale – jakość ze stanowisk, bez nich zakładane 2★). Bez gotowej prognozy dla lokali
    firmy – popyt drużyna liczy sama (test gry 28.10). stan – stan na początku rundy (konkurencja)."""
    r = max(runda, 2)
    dni = dni_rundy(dane, r)
    nazwy = dane.mapa["popyt"]["dni_tygodnia"]["nazwy"]
    dania = list(firma.oferta) or list(dane.katalog_ofert["rundy"]["uslugi_startowe"])
    konkurencja = oferty_konkurencji(dane, stan, r, firma.nazwa)
    # kampanie agencji reklamowych: własne (z decyzjami tej rundy) i trwające kampanie konkurencji
    ef = rk.efekty_rundy(dane, {**stan.firmy, firma.nazwa: firma}, r) if rk.zasady(dane) else None
    pula_rekl = ef["pula"] if ef else None
    for n, lokale in konkurencja.items():
        for ofl in lokale.values():
            for o in ofl.values():
                o["reklama_strefy"] = (ef or {}).get("firmy", {}).get(n, {})
    moje = {}
    wspolne = {"zadowolenie": mnoznik_zadowolenia(dane, zadowolenie),
               "reklama_strefy": (ef or {}).get("firmy", {}).get(firma.nazwa, {})}
    for lok in firma.lokale:
        if lok.dziala_od > r:
            continue
        strefa, v = dane.lokale[lok.id]["strefa"], widok_lokalu(firma, lok.id)
        for u in dania:   # własne lokale konkurują z nowym lokalem o klientów strefy
            c = firma.ceny.get(u)
            cena = max(0.01, c.cena - c.rabat) if c else dane.uslugi[u]["cena_preferowana"] * dane.mapa["popyt"]["strefy"][strefa]["cena"]
            q = jakosc_uslugi(dane, v, u) if kasjerzy(dane, v) else None
            moje.setdefault(lok.id, {})[u] = {"strefa": strefa, "cena": cena, "jakosc": q or (2, 2, 2), **wspolne}
    pm.efekty_ofert(dane, firma, moje, r, dni)
    pot = potencjal_stref(dane, r, {**konkurencja, firma.nazwa: moje}, dania, pula_rekl)
    pr = pule(dane, r, reklama=pula_rekl)
    lokale_stref: dict[str, list[str]] = {}
    for n, g in stan.firmy.items():
        for lok in g.lokale:
            lokale_stref.setdefault(dane.lokale[lok.id]["strefa"], []).append(n)
    strefy = {z: {"pula": round(sum(float(pr[z][u].sum()) for u in dania)), "potencjal": pot[z],
                  "cena": ps["cena"], "wrazliwosc_ceny": ps["wrazliwosc_ceny"],
                  "dni": [round(x * 7, 3) for x in wagi_dni(dane, z, dni)] if len(dni) == 7 else [],
                  "firmy": sorted(lokale_stref.get(z, []))}
              for z, ps in dane.mapa["popyt"]["strefy"].items()}
    return {"runda": r, "dni": [{"data": d.isoformat(), "dzien": nazwy[d.weekday()]} for d in dni],
            "wydarzenia": wydarzenia(dane, dni), "dania": dania, "strefy": strefy}
