"""Dane dla interfejsu: wszystko, czego potrzebuje strona firmy w danej rundzie (jeden słownik JSON)."""
from __future__ import annotations

from copy import deepcopy

from silnik import czas_wlasciciela as cw
from silnik import rynek_pracy as rp
from silnik import swiezosc
from silnik.dane import Dane
from silnik.decyzje import (
    cena_sprzedazy_sprzetu,
    gotowe_uslugi,
    kandydaci_firmy,
    lista_bledow,
    zastosuj,
)
from silnik.dostawcy import ceny_rundy, oferta_rundy
from silnik.dostawcy import info as info_dostawcy
from silnik.finanse import Ksiega, Rachunek
from silnik.gra import Gra
from silnik.lokale import (
    dostepne,
    koszt_wejscia,
    runda_nowego_lokalu,
    stan_lokali,
    tryb_lokali,
    wybierz,
    zajete,
)
from silnik.model import Firma, do_slownika
from silnik.popyt import widok_popytu
from silnik.srodki_trwale import ewidencja


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
    lokale = tryb_lokali(gra.dane, gra.konfiguracja)
    # lokal: pula po poprzedniej rundzie (o lokal wybrany w tej rundzie przez kilka drużyn rozstrzyga przeliczenie)
    lokal = wybierz(gra.dane, f, d.get("lokal"), r, zajete(stan.firmy), ks, rach) if lokale else None
    uwagi_rp = []
    if lokale:  # limit nowych i ważność ofert podkupienia (licytacje i odpowiedzi pracowników – dopiero w przeliczeniu)
        dd, _, raport = rp.przed_decyzjami(gra.dane, deepcopy(stan), {firma: d}, r, gra.konfiguracja["ziarno"])
        d, uwagi_rp = dd[firma], raport[firma]["uwagi"]
    info = zastosuj(gra.dane, f, d, r, stan.kandydaci, ceny_rundy(gra.dane, gra.konfiguracja["ziarno"], r,
                                                                  gra.konfiguracja.get("ceny_dostawcow", "dane")), ks, rach,
                    lokale)
    info["lokal"] = lokal
    bledy = lista_bledow(gra.dane, f, d, r, poprzednia_oferta, gra.konfiguracja.get("kredyt_odnawialny", "jednoczesnie"),
                         lokal, info)
    bledy += [{"poziom": "czerwony", "zakladka": "rynek_pracy", "tekst": t} for t in uwagi_rp]
    return stan, f, ks, info, bledy


def kalendarz(dane: Dane, liczba_rund: int) -> dict:
    """Nazwy rund dla strony: okres („tydzień”/„miesiąc” w przypadkach), nazwy i skróty rund 1…liczba_rund."""
    rundy = range(1, liczba_rund + 1)
    return {"okres": dane.okres, "tygodniowe": dane.tygodniowe, "rund_w_roku": dane.rund_w_roku,
            "nazwy": [dane.nazwa_rundy(r) for r in rundy], "skroty": [dane.skrot_rundy(r) for r in rundy],
            "miesiace": [dane.miesiac_rundy(r) for r in rundy]}


def katalogi(dane: Dane) -> dict:
    return {"mapa": dane.mapa, "uslugi": dane.uslugi, "sprzet": dane.sprzet, "sprzet_kasy": dane.sprzet_kasy, "zawody": dane.zawody, "zasoby": dane.zasoby,
            "oferty": dane.katalog_ofert, "placa_minimalna": dane.z["finanse"]["placa_minimalna"],
            "parametry": {"kapital": dane.z["finanse"]["kapital_startowy"], "godziny": dane.z["operacje"]["godziny_pracownika"],
                          "cit": dane.z["finanse"]["podatek_cit"], "zus": dane.z["finanse"]["zus_pracodawcy"],
                          "amortyzacja_prog": dane.z["finanse"]["amortyzacja_prog"],
                          "utrzymanie_klubu": dane.z["finanse"]["utrzymanie_klubu"],
                          "na_runde": 12 / dane.rund_w_roku, "rund_w_roku": dane.rund_w_roku,
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
                 "kredyt_odnawialny": gra.konfiguracja.get("kredyt_odnawialny", "jednoczesnie"),
                 "lokale": tryb_lokali(dane, gra.konfiguracja),
                 "kalendarz": kalendarz(dane, gra.konfiguracja["liczba_rund"])},
         "firma": firma, "runda": runda, "miesiac": dane.nazwa_rundy(runda), "edycja": edycja,
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
    v["ceny_dostawcow"], v["gazetki"] = oferta_rundy(dane, gra.konfiguracja["ziarno"], runda,
                                                     gra.konfiguracja.get("ceny_dostawcow", "dane"))
    v["dostawcy_info"] = {d: info_dostawcy(dane, d) for d in v["ceny_dostawcow"]}
    v["ceny_sprzedazy_sprzetu"] = {n: {q: cena_sprzedazy_sprzetu(dane, c) for q, c in s["ceny"].items()}
                                   for n, s in dane.sprzet.items()}

    # wyniki poprzedniej rundy (widoczne w tej rundzie)
    if runda - 1 in poprzedni.wyniki:
        w = poprzedni.wyniki.get(runda - 1, {})
        v["wyniki"] = w.get(firma)
        v["rynek"] = poprzedni.rynek.get(runda - 1)
        v["karta_skumulowana"] = karta_skumulowana(gra, runda - 1) if runda - 1 >= 2 else {}
        v["historia"] = [{"runda": r, "miesiac": dane.nazwa_rundy(r), "skrot": dane.skrot_rundy(r), "karta": poprzedni.wyniki[r][firma].get("karta"),
                          "dochod_netto": poprzedni.wyniki[r][firma]["kpir"]["dochod_netto"],
                          "gotowka": poprzedni.wyniki[r][firma]["gotowka"]}
                         for r in range(1, runda) if r in poprzedni.wyniki]
    v["dashboard"] = _dashboard(gra, firma, runda, poprzedni)
    if tryb_lokali(dane, gra.konfiguracja):
        v["lokale"] = _lokale(gra, firma, runda, f, poprzedni, stan, info if edycja else None)
        zk = ((poprzedni.wyniki.get(runda - 1) or {}).get(firma, {}).get("karta") or {}).get("zadowolenie_klientow")
        v["popyt"] = widok_popytu(dane, poprzedni, f, runda, zk)
        v["swiezosc"] = swiezosc.podsumowanie(dane, f, runda)
        v["dostawy_plan"] = (info or {}).get("dostawy") if edycja else stan.wyniki[runda][firma].get("dostawy")
        v["srodki_trwale"] = ewidencja(f)
        v["czas_wlasciciela"] = ((info or {}).get("czas_wlasciciela") if edycja
                                 else stan.wyniki[runda][firma].get("czas_wlasciciela")) or cw.nowy(dane).podsumowanie()
        v["agencja"] = _agencja(gra, firma, runda, f, stan, edycja)
        v["kandydaci"] = rp.widoczni(dane, v["kandydaci"], runda)
        v["amortyzacja"] = {"prog": dane.z["finanse"]["amortyzacja_prog"], "stawki": dane.z["finanse"]["amortyzacja_roczna"]}
    return v


def _agencja(gra: Gra, firma: str, runda: int, f: Firma, stan, edycja: bool) -> dict:
    """Zakładka Rynek pracy: kanały rekrutacji, pracownicy innych firm (headhunter), oferty dla moich pracowników
    (zapisane decyzje innych firm w tej rundzie – do kontroferty), staż i okres wypowiedzenia moich pracowników."""
    dane = gra.dane
    u = rp.ustawienia(dane)
    return {"kanaly": rp.kanaly(dane, runda), "limit": u["limit_nowych"], "wypowiedzenie": u["wypowiedzenie"],
            "kanaly_kandydatow": {k["id"]: rp.kanaly_kandydata(dane, k, runda) for k in stan.kandydaci},
            "headhunter": rp.headhunter_dostepny(dane, runda),
            "cudzy": rp.pracownicy_rynku(dane, stan, firma, runda) if rp.headhunter_dostepny(dane, runda) else [],
            "oferty_dla_mnie": rp.oferty_dla(gra.decyzje.get(runda, {}), f, firma) if edycja else [],
            "moi": [{"id": p.id, "imie_nazwisko": p.imie_nazwisko, "zawod": p.zawod, "gwiazdki": p.gwiazdki, "pensja": p.pensja,
                     "umowa": p.umowa, "staz": rp.staz(p, runda), "okres": rp.okres_wypowiedzenia(dane, p, runda),
                     "odchodzi": do_slownika(p.odchodzi) if p.odchodzi else None}
                    for p in sorted(f.pracownicy.values(), key=lambda p: p.id)]}


def _lokale(gra: Gra, firma: str, runda: int, f: Firma, poprzedni, stan, info: dict | None) -> dict:
    """Zakładka Lokale i mapa: wolne lokale na początku rundy (z kosztem wejścia), kto zajmuje które lokale,
    lokale firmy po decyzjach i wynik decyzji o lokalu."""
    dane = gra.dane
    zaj = zajete(poprzedni.firmy)
    decyzja = info.get("lokal") if info is not None else stan.wyniki.get(runda, {}).get(firma, {}).get("lokal_decyzja")
    return {"oferta": [{**lok, "wejscie": {fm: koszt_wejscia(dane, lok, fm) for fm in ("najem", "kupno")
                                          if lok.get("czynsz" if fm == "najem" else "cena")}}
                       for lok in dostepne(dane, runda, zaj)],
            "zajete": zajete(stan.firmy) if info is None else zaj,
            "moje": stan_lokali(dane, f, runda),
            "nowy_od": runda_nowego_lokalu(dane, poprzedni.firmy[firma]),
            "decyzja": decyzja}


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


def przeglad_mg(gra: Gra) -> dict:
    """Widok mistrza gry: bieżąca runda, kto wysłał decyzje, wyniki i ranking wszystkich firm, historia rund."""
    dane, konf = gra.dane, gra.konfiguracja
    r = gra.runda
    ostatnia = r - 1  # ostatnia przeliczona runda
    stan = gra.stan(ostatnia)
    wyslane = set(gra.wyslane())
    strategie = dane.boty["strategie"]
    skum = karta_skumulowana(gra, ostatnia)
    karta_ost = stan.rynek.get(ostatnia, {}).get("karta", {}) if ostatnia >= 2 else {}
    rundy = [x for x in range(gra.runda_startowa, ostatnia + 1) if x in stan.wyniki]
    firmy = []
    for f in konf["firmy"]:
        n = f["nazwa"]
        fs = stan.firmy[n]
        wyn = [stan.wyniki[x][n]["kpir"]["dochod_netto"] for x in rundy if n in stan.wyniki[x]]
        firmy.append({
            "nazwa": n, "bot": f["bot"], "strategia": strategie.get(f["bot"], {}).get("nazwa") if f["bot"] else None,
            "wyslane": None if f["bot"] else n in wyslane,
            "gotowka": fs.gotowka,
            "zadluzenie": sum(k.pozostalo for k in fs.kredyty) + fs.kredyt_odnawialny,
            "lokaty": sum(lk.kwota for lk in fs.lokaty),
            "pracownicy": len(fs.pracownicy), "stanowiska": len(fs.stanowiska),
            "dochod_ostatni": wyn[-1] if wyn else None, "dochod_suma": round(sum(wyn), 2),
            "wynik_ostatni": karta_ost.get(n, {}).get("wynik_dzialalnosci"),
            "wynik_skumulowany": skum.get(n, {}).get("wynik_dzialalnosci"),
        })
    ranking = sorted((f for f in firmy if f["wynik_skumulowany"] is not None), key=lambda f: -f["wynik_skumulowany"])
    for i, f in enumerate(ranking):
        f["miejsce"] = i + 1
    return {
        "gra": {"nazwa": konf["nazwa"], "runda": r, "liczba_rund": konf["liczba_rund"], "zakonczona": gra.zakonczona,
                "ziarno": konf["ziarno"], "kapital": gra.kapital_startowy,
                "kredyt_odnawialny": konf.get("kredyt_odnawialny", "jednoczesnie"),
                "ceny_dostawcow": konf.get("ceny_dostawcow", "dane"),
                "lokale": tryb_lokali(dane, konf),
                "brakujace": [] if gra.zakonczona else gra.brakujace(),
                "kalendarz": kalendarz(dane, konf["liczba_rund"])},
        "firmy": firmy,
        "historia": [{"runda": x, "skrot": dane.skrot_rundy(x),
                      "dochod": {n: w["kpir"]["dochod_netto"] for n, w in stan.wyniki[x].items()},
                      "gotowka": {n: w["gotowka"] for n, w in stan.wyniki[x].items()}} for x in rundy],
    }
