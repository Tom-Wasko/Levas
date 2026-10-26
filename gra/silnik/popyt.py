"""Popyt strefowy (gra z lokalami; dane: `dane/mapa/popyt.yaml`) – zastępuje popyt Revasa z rynek.py.

Każda strefa ma własną pulę klientów na każde danie i każdy dzień rundy:

    pula = popyt roczny / 52 × sezonowość dania × pula strefy × miesiąc strefy × kalendarz × waga dnia × szum

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

from . import menu
from . import swiezosc as sw
from .dane import Dane
from .losowosc import strumien
from .model import Firma
from .operacje import jakosc_uslugi, kasjerzy, obsluz

WSZYSTKIE = "wszystkie"   # klucz kalendarza: każda strefa


def dni_rundy(dane: Dane, runda: int) -> list[date]:
    """Dni rundy (tydzień: 7 dni od poniedziałku rundy; runda miesięczna – dni miesiąca)."""
    a, b = dane.data_rundy(runda), dane.data_rundy(runda + 1)
    return [a + timedelta(days=i) for i in range((b - a).days)]


def _w_zakresie(dzien: date, od: str, do: str) -> bool:
    md = dzien.strftime("%m-%d")
    return od <= md <= do if od <= do else (md >= od or md <= do)  # zakres przez Nowy Rok


def wydarzenia(dane: Dane, dni: list[date]) -> list[dict]:
    """Wydarzenia kalendarza w podanych dniach: {"nazwa", "opis", "dni": [ISO], "strefy": {strefa: mnożnik}}."""
    wynik = []
    for w in dane.mapa["popyt"].get("kalendarz", []):
        trafione = [d.isoformat() for d in dni if _w_zakresie(d, w["od"], w["do"])]
        if trafione:
            wynik.append({"nazwa": w["nazwa"], "opis": w["opis"], "dni": trafione, "strefy": w["strefy"]})
    return wynik


def mnoznik_kalendarza(dane: Dane, strefa: str, dzien: date) -> float:
    m = 1.0
    for w in dane.mapa["popyt"].get("kalendarz", []):
        if _w_zakresie(dzien, w["od"], w["do"]):
            m *= w["strefy"].get(strefa, w["strefy"].get(WSZYSTKIE, 1.0))
    return m


def wagi_dni(dane: Dane, strefa: str, dni: list[date]) -> np.ndarray:
    """Udział każdego dnia w tygodniowej puli strefy (średnio 1/7 na dzień) × kalendarz."""
    p = dane.mapa["popyt"]
    tydzien = p["strefy"][strefa].get("dni") or p["dni_tygodnia"]["wagi"]
    sr = sum(tydzien) / 7
    return np.array([tydzien[d.weekday()] / sr / 7 * mnoznik_kalendarza(dane, strefa, d) for d in dni])


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


def pule(dane: Dane, runda: int, ziarno=None) -> dict[str, dict[str, np.ndarray]]:
    """Pule klientów: strefa → danie → klienci w kolejnych dniach rundy (bez ziarna – bez szumu, wartość oczekiwana)."""
    p = dane.mapa["popyt"]
    dni = dni_rundy(dane, runda)
    m = dane.miesiac_rundy(runda)
    szum = p["model"]["szum_proc"]
    wynik = {}
    for z, ps in p["strefy"].items():
        baza = ps["pula"] * (ps["miesiace"][m] if ps.get("miesiace") else 1.0) * len(dni) / 7
        wagi = wagi_dni(dane, z, dni)
        wynik[z] = {}
        for u, du in dane.uslugi.items():
            tyg = du["popyt_roczny"] / 52 * du["sezonowosc"][m] * baza
            dzienne = tyg * 7 / len(dni) * wagi
            if ziarno is not None and szum > 0:
                dzienne = dzienne * np.exp(strumien(ziarno, runda, "popyt", "strefa", z, u).normal(0, szum, len(dni)))
            wynik[z][u] = dzienne
    return wynik


def mnoznik_zadowolenia(dane: Dane, zadowolenie: float | None) -> float:
    """Zadowolenie klientów firmy z poprzedniej rundy (karta wyników) → mnożnik atrakcyjności (brak karty – 1)."""
    if not zadowolenie:
        return 1.0
    m = dane.mapa["popyt"]["model"]
    return (zadowolenie / m["zadowolenie_odniesienie"]) ** m["zadowolenie_wykladnik"]


def atrakcyjnosc(dane: Dane, strefa_klienta: str, usluga: str, o: dict) -> float:
    """o: {"strefa", "cena" (po rabacie), "jakosc": (p, s, z), "wyposazenie", "reklama", "mnoznik_firmy", "zadowolenie"}."""
    p = dane.mapa["popyt"]
    ps = p["strefy"][strefa_klienta]
    r = o["cena"] / (dane.uslugi[usluga]["cena_preferowana"] * ps["cena"])
    return (menu.jakosc_dania(dane, o["jakosc"]) * math.exp(-p["model"]["elastycznosc_ceny"] * ps["wrazliwosc_ceny"] * (r - 1))
            * math.exp(-odleglosc(dane, strefa_klienta, o["strefa"]) / p["model"]["zasieg"])
            * o.get("zadowolenie", 1.0) * o.get("wyposazenie", 1.0) * (1 + o.get("reklama", 0.0)) * o.get("mnoznik_firmy", 1.0))


def podzial(dane: Dane, pule_rundy: dict, oferty: dict[str, dict[tuple[str, str], dict]]) -> dict:
    """Podział pul stref między lokale. oferty: {danie: {(firma, lokal): oferta}} (oferta jak w `atrakcyjnosc`).
    Zwraca {(firma, lokal): {danie: {"dni": np.ndarray, "strefy": {strefa: suma}}}} – wartości ułamkowe."""
    a0 = dane.mapa["popyt"]["model"]["opcja_zewnetrzna"]
    wynik: dict = {}
    for u, lokale in oferty.items():
        for z, pz in pule_rundy.items():
            a = {k: atrakcyjnosc(dane, z, u, o) for k, o in lokale.items()}
            mianownik = a0 + sum(a.values())
            for k, ak in a.items():
                klienci = pz[u] * ak / mianownik
                w = wynik.setdefault(k, {}).setdefault(u, {"dni": np.zeros(len(pz[u])), "strefy": {}})
                w["dni"] = w["dni"] + klienci
                w["strefy"][z] = float(klienci.sum())
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


def rynek_lokali(dane: Dane, firmy: dict[str, Firma], oferty: dict[str, dict[str, dict]], runda: int, ziarno) -> dict:
    """Popyt i obsługa w grze z lokalami. oferty: {firma: {lokal: {danie: oferta}}} (z `oferty_lokali`).
    Zwraca {"popyt": {firma: {danie: n}}, "obsluga": {firma: wynik jak operacje.obsluz}, "klienci": {firma: …},
    "rynek": {danie: {firma: {"popyt", "skladniki"}}}, "strefy": {…}, "swiezosc": {firma: …}} – dane do wyników
    i zakładek „Klienci” oraz „Magazyn i świeżość”."""
    dni = dni_rundy(dane, runda)
    pr = pule(dane, runda, ziarno)
    po_daniach: dict = {}
    for f, lokale in oferty.items():
        for lok, dania in lokale.items():
            for u, o in dania.items():
                po_daniach.setdefault(u, {})[(f, lok)] = o
    pod = podzial(dane, pr, po_daniach)

    popyt, obsluga, klienci, rynek, swiezosc = {}, {}, {}, {}, {}
    zrodla: dict[str, dict[str, float]] = {}
    for f, lokale in oferty.items():
        firma = firmy[f]
        popyt[f] = {}
        dzienne = {u: {"popyt": [0] * len(dni), "sprzedaz": [0] * len(dni)} for lok in lokale for u in lokale[lok]}
        lokale_wynik, przyczyny = [], {}
        laczna = {"obsluzeni": {}, "utracona": {}, "reklamacje": {}, "zuzyte_zasoby": {}, "godziny_stanowisk": {},
                  "godziny_recepcji": 0.0, "liczba_recepcjonistow": 0, "godziny_sprzetu": {}}
        dzien_popyt = {lok: [{u: int(round(pod[(f, lok)][u]["dni"][i])) for u in dania} for i in range(len(dni))]
                       for lok, dania in lokale.items()}
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
                laczna["godziny_recepcji"] += o["godziny_recepcji"]
            if firma.partie:
                _dodaj_straty(raport, sw.wyrzuc(firma, dzien), i, len(dni))
                raport["zajetosc"].append(sw.zajete(dane, firma, dzien))
        sw.uzgodnij(firma)
        swiezosc[f] = _zakoncz_raport(raport)
        laczna["liczba_recepcjonistow"] = sum(len(kasjerzy(dane, v)) for v in widoki.values())
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
            "strefy": {"strefy": strefy, "dni": [d.isoformat() for d in dni], "wydarzenia": wydarzenia(dane, dni)}}


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


def prognoza(dane: Dane, runda: int, oferty: dict[str, dict[str, dict]], firma: str) -> dict:
    """Oczekiwany popyt (bez szumu) lokali firmy w rundzie: {"dania": {danie: n}, "lokale": {lokal: {danie: n}},
    "dni": [n …]}. oferty jak w `rynek_lokali` – konkurenci z danych publicznych (ceny z poprzedniej rundy)."""
    po_daniach: dict = {}
    for f, lokale in oferty.items():
        for lok, dania in lokale.items():
            for u, o in dania.items():
                po_daniach.setdefault(u, {})[(f, lok)] = o
    pod = podzial(dane, pule(dane, runda), po_daniach)
    dania, lokale, dni = {}, {}, None
    for (f, lok), x in pod.items():
        if f != firma:
            continue
        for u, w in x.items():
            n = float(w["dni"].sum())
            dania[u] = dania.get(u, 0.0) + n
            lokale.setdefault(lok, {})[u] = round(n, 1)
            dni = w["dni"] if dni is None else dni + w["dni"]
    return {"dania": {u: round(n, 1) for u, n in dania.items()}, "lokale": lokale,
            "dni": [round(float(x), 1) for x in dni] if dni is not None else []}


def potencjal_stref(dane: Dane, runda: int, oferty: dict[str, dict[str, dict]], dania: list[str]) -> dict[str, float]:
    """Szacunek popytu na `dania` w nowym lokalu 2★ po cenach preferowanych strefy w każdej strefie, przy obecnych
    lokalach konkurencji (do wyboru miejsca)."""
    pr = pule(dane, runda)
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
    return wynik


def widok_popytu(dane: Dane, stan, firma: Firma, runda: int, zadowolenie: float | None = None) -> dict:
    """Zakładka „Klienci i strefy” (decyzje): dni rundy sprzedaży z wydarzeniami, prognoza dla lokali firmy (jakość
    ze stanowisk lokalu, bez nich – zakładane 2★), pule i potencjał stref. stan – stan na początku rundy (konkurencja)."""
    r = max(runda, 2)
    dni = dni_rundy(dane, r)
    nazwy = dane.mapa["popyt"]["dni_tygodnia"]["nazwy"]
    dania = list(firma.oferta) or list(dane.katalog_ofert["rundy"]["uslugi_startowe"])
    konkurencja = oferty_konkurencji(dane, stan, r, firma.nazwa)
    moje, zalozone = {}, []
    wspolne = {"zadowolenie": mnoznik_zadowolenia(dane, zadowolenie)}
    for lok in firma.lokale:
        if lok.dziala_od > r:
            continue
        strefa, v = dane.lokale[lok.id]["strefa"], widok_lokalu(firma, lok.id)
        for u in dane.uslugi:  # prognoza każdego dania (także jeszcze nie w menu – do decyzji w Ofercie)
            c = firma.ceny.get(u)
            cena = max(0.01, c.cena - c.rabat) if c else dane.uslugi[u]["cena_preferowana"] * dane.mapa["popyt"]["strefy"][strefa]["cena"]
            q = jakosc_uslugi(dane, v, u) if kasjerzy(dane, v) else None
            if q is None:
                zalozone.append(f"{lok.id}|{u}")
            moje.setdefault(lok.id, {})[u] = {"strefa": strefa, "cena": cena, "jakosc": q or (2, 2, 2), **wspolne}
    prog = prognoza(dane, r, {**konkurencja, firma.nazwa: moje}, firma.nazwa)
    w_menu = {lok: {u: o for u, o in x.items() if u in dania} for lok, x in moje.items()}
    prog["dni"] = prognoza(dane, r, {**konkurencja, firma.nazwa: w_menu}, firma.nazwa)["dni"]  # dni – tylko dania menu
    pot = potencjal_stref(dane, r, {**konkurencja, firma.nazwa: w_menu}, dania)
    pr = pule(dane, r)
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
            "wydarzenia": wydarzenia(dane, dni), "prognoza": prog, "zalozone": zalozone, "dania": dania,
            "szczyt": {lok: round(szczyt(dane, dane.lokale[lok]["strefa"], r), 3) for lok in moje},
            "strefy": strefy}
