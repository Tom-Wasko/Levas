"""Dane dla interfejsu: wszystko, czego potrzebuje strona firmy w danej rundzie (jeden słownik JSON)."""
from __future__ import annotations

from copy import deepcopy

from silnik.dane import MIESIACE_NAZWY, Dane
from silnik.decyzje import (
    cena_sprzedazy_sprzetu,
    gotowe_uslugi,
    kandydaci_firmy,
    lista_bledow,
    zastosuj,
)
from silnik.dostawcy import ceny_miesiaca
from silnik.finanse import Ksiega, Rachunek
from silnik.gra import Gra
from silnik.model import Firma, do_slownika


def _firma_slownik(f: Firma) -> dict:
    d = do_slownika(f)
    d["pracownicy"] = list(d["pracownicy"].values())
    return d


def stan_po_szkicu(gra: Gra, firma: str):
    """Stan firmy po zastosowaniu roboczych decyzji bieżącej rundy (bez sprzedaży) + koszty tych decyzji."""
    r = gra.runda
    stan = deepcopy(gra.stan(r - 1))
    f = stan.firmy[firma]
    d = gra.szkic(firma)
    ks, rach = Ksiega(), Rachunek()
    poprzednia_oferta = list(f.oferta)
    info = zastosuj(gra.dane, f, d, r, stan.kandydaci, ceny_miesiaca(gra.dane, gra.konfiguracja["ziarno"], r - 1,
                                                                     gra.konfiguracja.get("ceny_dostawcow", "dane")), ks, rach)
    bledy = lista_bledow(gra.dane, f, d, r, poprzednia_oferta, gra.konfiguracja.get("kredyt_odnawialny", "jednoczesnie"))
    return stan, f, ks, info, bledy


def katalogi(dane: Dane) -> dict:
    return {"uslugi": dane.uslugi, "sprzet": dane.sprzet, "sprzet_kasy": dane.sprzet_kasy, "zawody": dane.zawody, "zasoby": dane.zasoby,
            "oferty": dane.katalog_ofert, "placa_minimalna": dane.z["finanse"]["placa_minimalna"],
            "parametry": {"kapital": dane.z["finanse"]["kapital_startowy"], "godziny": dane.z["operacje"]["godziny_pracownika"],
                          "cit": dane.z["finanse"]["podatek_cit"], "zus": dane.z["finanse"]["zus_pracodawcy"],
                          "amortyzacja_prog": dane.z["finanse"]["amortyzacja_prog"],
                          "utrzymanie_klubu": dane.z["finanse"]["utrzymanie_klubu"],
                          "koszt_zwrotu": dane.z["finanse"]["koszt_zwrotu"], "koszt_magazynowania": dane.z["finanse"]["koszt_magazynowania"],
                          "sprzedaz_sprzetu": dane.z["finanse"]["sprzedaz_sprzetu"]}}


def karta_skumulowana(gra: Gra, do_rundy: int) -> dict:
    """Średnia kart wyników z rund 2…do_rundy (dla każdej firmy)."""
    if do_rundy < 2:
        return {}
    stan = gra.stan(do_rundy)
    wynik = {}
    for f in stan.firmy:
        karty = [stan.wyniki[r][f]["karta"] for r in range(2, do_rundy + 1)
                 if r in stan.wyniki and f in stan.wyniki[r] and "karta" in stan.wyniki[r][f]]
        if karty:
            wynik[f] = {k: round(sum(c[k] for c in karty) / len(karty), 3) for k in karty[0]}
    return wynik


def widok(gra: Gra, firma: str, runda: int | None = None) -> dict:
    """Widok firmy w rundzie `runda` (domyślnie bieżąca). Decyzje: bieżąca runda – edytowalne, wcześniejsze – podgląd.
    Wyniki w rundzie r: skutki decyzji z rundy r−1 (jak w REVAS)."""
    dane = gra.dane
    biezaca = gra.runda
    runda = min(runda or biezaca, biezaca) if not gra.zakonczona else min(runda or biezaca - 1, biezaca - 1)
    runda = max(runda, gra.runda_startowa)
    edycja = runda == biezaca and not gra.zakonczona
    v = {"gra": {"nazwa": gra.konfiguracja["nazwa"], "runda": biezaca, "liczba_rund": gra.konfiguracja["liczba_rund"],
                 "zakonczona": gra.zakonczona, "firmy": gra.konfiguracja["firmy"], "wyslane": gra.wyslane(),
                 "brakujace": gra.brakujace(), "ziarno": gra.konfiguracja["ziarno"], "runda_startowa": gra.runda_startowa,
                 "konkurenci_stali": gra.konfiguracja.get("konkurenci_stali", []),
                 "kredyt_odnawialny": gra.konfiguracja.get("kredyt_odnawialny", "jednoczesnie")},
         "firma": firma, "runda": runda, "miesiac": MIESIACE_NAZWY[runda - 1], "edycja": edycja,
         "odblokowane": sorted(dane.odblokowane(runda))}

    if edycja:
        stan, f, ks, info, bledy = stan_po_szkicu(gra, firma)
        v["decyzje"] = gra.szkic(firma)
        v["wyslane"] = firma in gra.wyslane()
        v["warianty"] = sorted(gra.decyzje.get(biezaca, {}).get("_warianty", {}).get(firma, {}))
    else:
        stan = gra.stan(runda)
        f = stan.firmy[firma]
        ks = Ksiega(stan.wyniki[runda][firma]["kpir"]["pozycje"])
        info, bledy = {}, stan.wyniki[runda][firma]["lista_bledow"]
        v["decyzje"] = {k: w for k, w in gra.decyzje.get(runda, {}).get(firma, {}).items()}
        v["wyslane"] = True
    poprzedni = gra.stan(runda - 1)
    v["stan"] = _firma_slownik(f)
    v["stan"]["gotowe_uslugi"] = gotowe_uslugi(dane, f)
    v["stan_przed"] = _firma_slownik(poprzedni.firmy[firma])
    v["koszty_decyzji"] = ks.pozycje
    v["nieudane_zatrudnienia"] = info.get("nieudane_zatrudnienia", [])
    v["lista_bledow"] = bledy
    v["kandydaci"] = (kandydaci_firmy(stan.kandydaci, f) if edycja
                      else kandydaci_firmy(poprzedni.kandydaci, poprzedni.firmy[firma]))
    v["ceny_dostawcow"] = ceny_miesiaca(dane, gra.konfiguracja["ziarno"], runda - 1, gra.konfiguracja.get("ceny_dostawcow", "dane"))
    v["ceny_sprzedazy_sprzetu"] = {n: {q: cena_sprzedazy_sprzetu(dane, c) for q, c in s["ceny"].items()}
                                   for n, s in dane.sprzet.items()}

    # wyniki poprzedniej rundy (widoczne w tej rundzie)
    if runda - 1 in poprzedni.wyniki:
        w = poprzedni.wyniki.get(runda - 1, {})
        v["wyniki"] = w.get(firma)
        v["rynek"] = poprzedni.rynek.get(runda - 1)
        v["karta_skumulowana"] = karta_skumulowana(gra, runda - 1) if runda - 1 >= 2 else {}
        v["historia"] = [{"runda": r, "miesiac": MIESIACE_NAZWY[r - 1], "karta": poprzedni.wyniki[r][firma].get("karta"),
                          "dochod_netto": poprzedni.wyniki[r][firma]["kpir"]["dochod_netto"],
                          "gotowka": poprzedni.wyniki[r][firma]["gotowka"]}
                         for r in range(1, runda) if r in poprzedni.wyniki]
    v["dashboard"] = _dashboard(gra, firma, runda, poprzedni)
    return v


def _dashboard(gra: Gra, firma: str, runda: int, poprzedni) -> dict:
    f = poprzedni.firmy[firma]
    d = {"nazwa": f.nazwa_wyswietlana or firma, "saldo": f.gotowka, "dochod_netto": 0.0, "miejsce": None,
         "liczba_firm": len(poprzedni.firmy), "lokaty": sum(l.kwota for l in f.lokaty),
         "zadluzenie": sum(k.pozostalo for k in f.kredyty) + f.kredyt_odnawialny}
    if runda - 1 in poprzedni.wyniki:
        d["dochod_netto"] = poprzedni.wyniki[runda - 1][firma]["kpir"]["dochod_netto"]
    if runda >= 3 and runda - 1 in poprzedni.rynek:
        karty = poprzedni.rynek[runda - 1]["karta"]
        ranking = sorted(karty, key=lambda n: -karty[n]["wynik_dzialalnosci"])
        d["miejsce"] = ranking.index(firma) + 1 if firma in ranking else None
    return d
