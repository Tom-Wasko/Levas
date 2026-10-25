"""Boty – firmy komputerowe. Decydują tym samym formatem co gracz (silnik/decyzje.py), na podstawie stanu
po poprzedniej rundzie i danych publicznych rynku. Deterministyczne (ziarno gry), więc w grze przez GitHub
każdy komputer liczy je sam.

Strategie (dane/boty.yaml: strategie): cena w % ceny preferowanej, jakość (gwiazdki sprzętu, zasobów, pracowników),
docelowa liczba usług, pokrycie popytu, inwestycje w wyposażenie i udogodnienia, reklama, szkolenia.
"""
from __future__ import annotations

from .dane import INSTRUKTOR, RECEPCJONISTA, TRENER, Dane
from .decyzje import kandydaci_firmy
from .dostawcy import ceny_miesiaca
from .losowosc import generator
from .model import Firma, StanGry
from .planowanie import (
    oczekiwany_popyt,
    recepcjonisci_potrzebni,
    stanowiska_potrzebne,
    zamowienie_zasobow,
)
from .rynek import mnoznik_wyposazenia

ZAWOD_STANOWISKA = {INSTRUKTOR: "instruktor", TRENER: "instruktor", RECEPCJONISTA: "recepcja"}


def _ranking_uslug(dane: Dane) -> list[str]:
    """Usługi od najwyższego przychodu na godzinę prowadzącego (cena × grupa / godziny)."""
    return sorted(dane.uslugi, key=lambda u: -dane.uslugi[u]["cena_preferowana"] * dane.uslugi[u]["grupa"]
                  / dane.uslugi[u]["godziny_prowadzacego"])


def _cena(dane: Dane, strategia: dict, stan: StanGry, u: str, runda: int) -> float:
    pref = dane.uslugi[u]["cena_preferowana"]
    wsp = strategia["cena"]
    if wsp is None:  # naśladowca: średnia cen rynku z poprzedniej rundy
        ceny = stan.rynek.get(runda - 1, {}).get("ceny", {}).get(u, {})
        wsp = (sum(ceny.values()) / len(ceny) / pref) if ceny else dane.boty["ustawienia"]["cena_nasladowcy_bez_danych"]
    krok = dane.boty["ustawienia"]["krok_ceny"]
    return round(pref * wsp / krok) * krok


def decyzje_bota(dane: Dane, stan: StanGry, nazwa: str, strategia_klucz: str, runda: int, konf: dict) -> dict:
    strategie = dane.boty["strategie"]
    st = strategie.get(strategia_klucz, strategie["zrownowazony"])
    ust = dane.boty["ustawienia"]
    f: Firma = stan.firmy[nazwa]
    q = st["jakosc"]
    m = runda - 1
    rundy = dane.katalog_ofert["rundy"]
    odbl = dane.odblokowane(runda)
    d: dict = {"zatrudnij": [], "sprzet_kup": [], "zamowienia": []}
    if not f.bank:
        d["bank"] = min(dane.dostepne("banki", runda).values(), key=lambda b: b["konto"] + b["karta"])["nazwa"]
    if not f.biuro:
        d["biuro"] = min(dane.pozycje("biura_rachunkowe").values(), key=lambda b: b["etat"])["nazwa"]

    # usługi: start z usługami startowymi, potem po 3 nowe aż do celu
    oferta = list(f.oferta) or list(rundy["uslugi_startowe"])
    if runda >= rundy["nowe_uslugi_od_rundy"]:
        for u in _ranking_uslug(dane):
            if len(oferta) >= st["uslugi"] or len([x for x in oferta if x not in f.oferta]) >= rundy["nowe_uslugi_na_runde"]:
                break
            if u not in oferta:
                oferta.append(u)

    # oczekiwany popyt w miesiącu, w którym usługi będą sprzedawane (runda 1 planuje luty)
    m_sprz = max(m, 1)
    pub = stan.rynek.get(runda - 1, {})
    wyp = mnoznik_wyposazenia(dane, f.wyposazenie)
    ceny, klienci = {}, {}
    for u in oferta:
        ceny[u] = _cena(dane, st, stan, u, runda)
        inni = pub.get("ceny", {}).get(u, {})
        n = 1 + len([x for x in inni if x != nazwa])
        r_inni = [c / dane.uslugi[u]["cena_preferowana"] for x, c in inni.items() if x != nazwa]
        r_sr = (sum(r_inni) + ceny[u] / dane.uslugi[u]["cena_preferowana"]) / (len(r_inni) + 1)
        klienci[u] = oczekiwany_popyt(dane, u, m_sprz, ceny[u], (q, q, q), n, r_sr, wyp) * st["pokrycie"]
    d["oferta"] = {u: int(round(klienci[u] / st["pokrycie"])) for u in oferta}
    if "sprzedaz" in odbl:
        d["sprzedaz"] = {u: {"cena": ceny[u], "rabat": 0} for u in oferta}

    # stanowiska prowadzących: osobne dla każdej usługi (komplet sprzętu usługi)
    nowe_inst, nowe_rec = [], 0
    istniejace = f.stanowiska_typu("instruktor")
    wolne = [s for s in istniejace if not s.sprzet]
    nastepny = len(istniejace) + 1
    for u in oferta:
        potrzeba = stanowiska_potrzebne(dane, u, klienci[u])
        maja = [s for s in istniejace if all(n in s.sprzet for n in dane.uslugi[u]["sprzet"])]
        for _ in range(max(0, potrzeba - len(maja))):
            if wolne:
                cel = wolne.pop(0).nr
            elif len(nowe_inst) < dane.maks_nowych_stanowisk:
                cel = nastepny
                nowe_inst.append(u)
                nastepny += 1
            else:
                break
            for n in dane.uslugi[u]["sprzet"]:
                d["sprzet_kup"].append({"typ": "instruktor", "nr": cel, "nazwa": n, "jakosc": q})
            d.setdefault("_obsada", []).append({"nr": cel, "zawod": dane.uslugi[u]["prowadzacy"]})
    # recepcja
    rec = f.stanowiska_typu("recepcja")
    potrzeba_rec = max(1, recepcjonisci_potrzebni(dane, klienci))
    nowe_rec = min(dane.maks_nowych_stanowisk, max(0, potrzeba_rec - len(rec)))
    for s in rec:  # stanowiska kupione wcześniej (np. w rundzie 1, gdy sprzęt był jeszcze niedostępny)
        for n in dane.sprzet_recepcji:
            if n not in s.sprzet:
                d["sprzet_kup"].append({"typ": "recepcja", "nr": s.nr, "nazwa": n, "jakosc": q})
    for i in range(nowe_rec):
        nr = len(rec) + i + 1
        for n in dane.sprzet_recepcji:
            d["sprzet_kup"].append({"typ": "recepcja", "nr": nr, "nazwa": n, "jakosc": q})
    d["stanowiska"] = {"instruktor": len(nowe_inst), "recepcja": nowe_rec}

    # zatrudnienie (od rundy 2): stanowiska bez pracownika, które mają (albo dostają) sprzęt
    if "hr_zatrudnienie" in odbl:
        pula = kandydaci_firmy(stan.kandydaci, stan.firmy[nazwa])
        rng = generator(konf["ziarno"], "bot", runda, nazwa)
        obsada = {o["nr"]: o["zawod"] for o in d.pop("_obsada", [])}
        for s in istniejace:
            if not s.pracownik and s.sprzet and s.nr not in obsada:
                zawod = next((dane.uslugi[u]["prowadzacy"] for u in dane.uslugi
                              if all(n in s.sprzet for n in dane.uslugi[u]["sprzet"])), INSTRUKTOR)
                obsada[s.nr] = zawod
        cele = [("instruktor", nr, zawod) for nr, zawod in sorted(obsada.items())]
        cele += [("recepcja", s.nr, RECEPCJONISTA) for s in rec if not s.pracownik]
        cele += [("recepcja", len(rec) + i + 1, RECEPCJONISTA) for i in range(nowe_rec)]
        for typ, nr, zawod in cele:
            kandydaci = [k for k in pula if k["zawod"] == zawod]
            if not kandydaci:
                continue
            najlepsi = sorted(kandydaci, key=lambda k: (abs(k["gwiazdki"] - q), k["pensja_preferowana"]))[:ust["losuj_z_najlepszych_kandydatow"]]
            k = najlepsi[int(rng.integers(len(najlepsi)))]
            pula.remove(k)
            d["zatrudnij"].append({"kandydat": k["id"], "typ": typ, "nr": nr, "pensja": k["pensja_preferowana"],
                                   "umowa": "prace", "zastepca": True, "wzor": {"zawod": zawod, "gwiazdki": q}})
    else:
        d.pop("_obsada", None)

    # zasoby na przewidywanych klientów
    if "dostawcy" in odbl:
        ceny_d = ceny_miesiaca(dane, konf["ziarno"], m, konf.get("ceny_dostawcow", "dane"))
        d["zamowienia"] = zamowienie_zasobow(dane, f, klienci, ceny_d, q, ust["zapas_zasobow"])

    # inwestycje dodatkowe wg strategii (gdy jest gotówka)
    bufor = f.gotowka > ust["bufor_gotowki"]
    if "inwestycje_wyposazenie" in odbl and bufor:
        d["wyposazenie_kup"] = [p["nazwa"] for p in sorted(dane.pozycje("wyposazenie").values(), key=lambda p: -p["procent"])
                                if p["od_rundy"] <= runda and p["nazwa"] not in f.wyposazenie][:max(0, st["wyposazenie"] - len(f.wyposazenie))]
    if "hr_udogodnienia" in odbl and bufor:
        d["udogodnienia_kup"] = [p["nazwa"] for p in sorted(dane.pozycje("udogodnienia").values(), key=lambda p: p["cena"] / p["procent"])
                                 if p["od_rundy"] <= runda and p["nazwa"] not in f.udogodnienia][:max(0, st["udogodnienia"] - len(f.udogodnienia))]
    if "marketing_tradycyjny" in odbl and bufor:
        d["reklama_tradycyjna"] = {n: e for n, e in st["reklama"].items() if n in dane.dostepne("media_tradycyjne", runda)}
    if "marketing_internetowy" in odbl and bufor:
        d["internet_uruchom"] = [n for n in st["internet"] if n not in f.internet and n in dane.dostepne("narzedzia_internetowe", runda)]
    if "hr_szkolenia" in odbl and bufor and st["szkolenia"]:
        szk = dane.katalog_ofert["szkolenia"]
        najlepsze = sorted(szk["pozycje"], key=lambda p: -p["procent"])[:st["szkolenia"]]
        d["szkolenia"] = [{"firma": szk["firmy"][1]["nazwa"], "szkolenie": p["nazwa"]} for p in najlepsze]
    return d
