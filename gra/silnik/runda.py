"""Przeliczenie jednej rundy dla wszystkich firm.

Runda r = miesiąc r (1 = styczeń). Kolejność jak w KPiR i banku gry:
 1. decyzje: lokal (gra z lokalami: wspólna pula, pierwszeństwo wg kolejności rundy), stanowiska, sprzęt, kadry, zasoby, udogodnienia, wyposażenie, reklama, szkolenia (każda firma
    widzi pełną listę kandydatów – ta sama osoba może pracować w kilku firmach, jak w grze A/B/C),
 2. bank: nowe lokaty i kredyty, zerwania, spłaty,
 3. od rundy 2: popyt rynku → obsługa klientów → przychody,
 4. koszty miesiąca: pensje + ZUS, utrzymanie (klub, sprzęt, udogodnienia, wyposażenie, internet), zwroty,
    magazynowanie, bank (opłaty, odsetki, lokaty), biuro rachunkowe,
 5. podatek, kredyt odnawialny przy braku gotówki,
 6. karta wyników (od rundy 2; w grze widoczna od rundy 3).
"""
from __future__ import annotations

import math
from copy import deepcopy

import numpy as np

from . import karta as kw
from . import lokale as lk
from . import popyt as pp
from .dane import KUCHNIA, Dane
from .decyzje import lista_bledow, zastosuj
from .dostawcy import ceny_rundy
from .finanse import (
    Ksiega,
    Rachunek,
    bank_koniec_miesiaca,
    bank_poczatek_miesiaca,
    ksieguj,
    uruchom_odnawialny,
    wyrownaj_gotowke,
    zadluzenie,
)
from .kandydaci import dodaj_nowych
from .losowosc import strumien
from .model import Firma, StanGry, do_slownika, grosze
from .operacje import jakosc_uslugi, kasjerzy, obsluz
from .rynek import (
    mnoznik_firmy,
    mnoznik_jakosci,
    mnoznik_wyposazenia,
    popyt_rynku,
    wzrost_reklamy_internetowej,
    wzrost_reklamy_tradycyjnej,
)

EPS = 1e-9


def przelicz_runde(dane: Dane, stan: StanGry, decyzje: dict[str, dict], konfiguracja: dict) -> StanGry:
    """Zwraca nowy stan po rundzie stan.runda + 1 (stan wejściowy nie jest zmieniany)."""
    s = deepcopy(stan)
    r = stan.runda + 1
    m = dane.miesiac_rundy(r)  # sezonowość popytu
    ziarno = konfiguracja["ziarno"]
    z = dane.z
    if r >= 2:
        s.kandydaci = dodaj_nowych(dane, s.kandydaci, ziarno, r)
    ceny_dost = ceny_rundy(dane, ziarno, r, konfiguracja.get("ceny_dostawcow", "dane"))
    nazwy = sorted(s.firmy)
    kolejnosc = list(strumien(ziarno, r, "kolejnosc").permutation(nazwy))

    ksiegi, rachunki, info, bledy, start, odnawialny = {}, {}, {}, {}, {}, {}
    # "jednoczesnie" (jak w oficjalnej grze): przychody i wydatki miesiąca rozliczane razem – kredyt odnawialny tylko
    # na niedobór na koniec miesiąca; "na_biezaco": wydatki z decyzji opłacane przed wpływem przychodów
    tryb_kredytu = konfiguracja.get("kredyt_odnawialny", "jednoczesnie")
    tryb_lokali = lk.tryb_lokali(dane, konfiguracja)
    zajete = lk.zajete(s.firmy)
    for nazwa in kolejnosc:
        f = s.firmy[nazwa]
        d = decyzje.get(nazwa, {})
        poprzednia_oferta = list(f.oferta)
        start[nazwa] = {"magazyn": dict(f.magazyn), "gotowka": f.gotowka,
                        "pracownicy": len(f.pracownicy), "uslugi": len(f.oferta)}
        for p in f.pracownicy.values():
            p.premia = 0.0
        ksiegi[nazwa], rachunki[nazwa] = Ksiega(), Rachunek()
        # lokaty i kredyty na początku miesiąca, przed zakupami (historia rachunku ATH, luty: opłata za konto → lokata
        # 30 000 z salda 33 564 → stanowisko, sprzęt, … – saldo w trakcie miesiąca może być ujemne); bank wybrany
        # w tej rundzie działa od razu (ATH maj: zmiana na Gaz Bank i lokata 7%)
        if d.get("bank") and d["bank"] in dane.dostepne("banki", r):
            f.bank = d["bank"]
        bank_info = bank_poczatek_miesiaca(f, dane.pozycje("banki")[f.bank], d, r, ksiegi[nazwa], rachunki[nazwa]) \
            if f.bank else None
        lokal = lk.wybierz(dane, f, d.get("lokal"), r, zajete, ksiegi[nazwa], rachunki[nazwa]) if tryb_lokali else None
        info[nazwa] = zastosuj(dane, f, d, r, s.kandydaci, ceny_dost, ksiegi[nazwa], rachunki[nazwa], tryb_lokali)
        bledy[nazwa] = lista_bledow(dane, f, d, r, poprzednia_oferta, tryb_kredytu, lokal, info[nazwa])
        info[nazwa]["lokal"] = lokal
        if bank_info is not None:
            info[nazwa]["bank"] = bank_info
        odnawialny[nazwa] = uruchom_odnawialny(f, rachunki[nazwa]) if tryb_kredytu == "na_biezaco" else 0.0

    # --- rynek i sprzedaż ----------------------------------------------------------------------
    popyt, obsluga, oferty = {}, {}, {}
    strefowy = None
    if r >= 2:
        oferty_lok = {}
        stali = konfiguracja.get("konkurenci_stali", [])
        narzedzia_rynku = sum(sum(1 for od in s.firmy[n].internet.values() if od <= r) for n in nazwy) \
            + sum(len(k.get("internet", {})) for k in stali)
        for nazwa in nazwy:
            f = s.firmy[nazwa]
            d = decyzje.get(nazwa, {})
            media = dane.dostepne("media_tradycyjne", r)
            emisje = {n: e for n, e in (d.get("reklama_tradycyjna") or {}).items() if n in media}
            reklama = wzrost_reklamy_tradycyjnej(dane, emisje) if "marketing_tradycyjny" in dane.odblokowane(r) else 0.0
            reklama_int = wzrost_reklamy_internetowej(dane, f.internet, r, narzedzia_rynku)
            info[nazwa]["reklama"] = {"tradycyjna": reklama, "internetowa": reklama_int}
            wyp = mnoznik_wyposazenia(dane, f.wyposazenie)
            mn_firmy = mnoznik_firmy(dane, f)
            if tryb_lokali:  # popyt strefowy: oferty lokali (zadowolenie klientów z karty poprzedniej rundy)
                zk = ((s.wyniki.get(r - 1) or {}).get(nazwa, {}).get("karta") or {}).get("zadowolenie_klientow")
                ceny = {u: max(0.01, f.ceny[u].cena - f.ceny[u].rabat) for u in f.oferta if u in f.ceny}
                oferty_lok[nazwa] = pp.oferty_lokali(dane, f, r, ceny, {
                    "wyposazenie": wyp, "reklama": reklama + reklama_int, "mnoznik_firmy": mn_firmy,
                    "zadowolenie": pp.mnoznik_zadowolenia(dane, zk)})
                continue
            rec = kasjerzy(dane, f)
            for u in f.oferta:
                if u not in f.ceny or not rec:
                    continue
                q = jakosc_uslugi(dane, f, u)
                if q is None:
                    continue
                cena = max(0.01, f.ceny[u].cena - f.ceny[u].rabat)
                oferty.setdefault(u, {})[nazwa] = {"cena": cena, "jakosc": q, "wyposazenie": wyp,
                                                   "reklama": reklama + reklama_int, "mnoznik_firmy": mn_firmy}
        for k in ([] if tryb_lokali else stali):
            # konkurenci z prawdziwej gry: stałe ceny i jakość, bez finansów (tryb „co jeśli”, odtworzenie gry ATH);
            # "reklama" = wzrost z reklamy tradycyjnej, "internet" = {narzędzie: runda uruchomienia} (udział liczony tu)
            rekl_k = float(k.get("reklama", 0.0)) + (wzrost_reklamy_internetowej(dane, k["internet"], r, narzedzia_rynku)
                                                     if k.get("internet") else 0.0)
            for u, cena in k.get("ceny", {}).items():
                if cena:
                    oferty.setdefault(u, {})[k["nazwa"]] = {"cena": float(cena), "jakosc": tuple(k.get("jakosc", (2, 2, 2))),
                                                          "wyposazenie": float(k.get("wyposazenie", 1.0)),
                                                          "reklama": rekl_k}
        if tryb_lokali:
            strefowy = pp.rynek_lokali(dane, s.firmy, oferty_lok, r, ziarno)
            popyt, obsluga, rynek = strefowy["popyt"], strefowy["obsluga"], strefowy["rynek"]
            for nazwa, lokale in oferty_lok.items():  # oferta firmy: jakość lokalu z największym popytem dania
                for u in popyt[nazwa]:
                    lok = max((x for x in lokale if u in lokale[x]), key=lambda x: rynek[u][nazwa]["skladniki"]["lokale"][x])
                    oferty.setdefault(u, {})[nazwa] = lokale[lok][u]
        else:
            rynek = popyt_rynku(dane, oferty, m, ziarno, r)
            for nazwa in nazwy:
                popyt[nazwa] = {u: v[nazwa]["popyt"] for u, v in rynek.items() if nazwa in v}
                obsluga[nazwa] = obsluz(dane, s.firmy[nazwa], popyt[nazwa], ziarno, r)
        for nazwa in nazwy:
            for u, k in obsluga[nazwa]["obsluzeni"].items():
                ksieguj(s.firmy[nazwa], ksiegi[nazwa], rachunki[nazwa], f"Sprzedaż: {dane.uslugi[u]['nazwa']}",
                        k * oferty[u][nazwa]["cena"], "przychod")
    else:
        rynek = {}

    # --- koszty rundy, bank, podatek -----------------------------------------------------------
    # pensje, utrzymanie, czynsz i opłaty są w danych miesięczne – dane.na_runde przelicza je na rundę
    wyniki = {}
    for nazwa in nazwy:
        f, ks, rach = s.firmy[nazwa], ksiegi[nazwa], rachunki[nazwa]
        d = decyzje.get(nazwa, {})
        etat = [p for p in f.pracownicy.values() if p.umowa == "prace"]
        # premia: osobna pozycja na pracownika, w kolumnie wynagrodzeń, bez ZUS (KPiR gry A/B/C online, marzec:
        # „Bonus dla pracownika: …” 3 × 500, ZUS 9576 = 19% samych pensji 50 400)
        for p in f.pracownicy.values():
            if p.premia > 0:
                ksieguj(f, ks, rach, f"Bonus dla pracownika: {p.imie_nazwisko}", p.premia, "wynagrodzenia")
        ksieguj(f, ks, rach, "Wynagrodzenia pracowników", dane.na_runde(sum(p.pensja for p in f.pracownicy.values())),
                "wynagrodzenia")
        ksieguj(f, ks, rach, "Składki ZUS pracodawcy",
                dane.na_runde(sum(p.pensja for p in etat)) * z["finanse"]["zus_pracodawcy"])
        utrz_sprzetu = sum(dane.sprzet[n]["utrzymanie"][str(q)] for st in f.stanowiska for n, q in st.sprzet.items())
        ksieguj(f, ks, rach, "Koszty utrzymania sprzętu", dane.na_runde(utrz_sprzetu))
        ud, wy = dane.pozycje("udogodnienia"), dane.pozycje("wyposazenie")
        ksieguj(f, ks, rach, "Koszty utrzymania udogodnień i benefitów",
                dane.na_runde(sum(ud[n]["utrzymanie"] for n in f.udogodnienia)
                              + sum(wy[n]["utrzymanie"] for n in f.wyposazenie)))
        narz = dane.pozycje("narzedzia_internetowe")
        for n in f.internet:
            ksieguj(f, ks, rach, f"Utrzymanie reklamy internetowej: {n}", dane.na_runde(narz[n]["utrzymanie"]))
        if tryb_lokali:
            lk.koszty_rundy(dane, f, r, ks, rach)
        else:
            ksieguj(f, ks, rach, f"{dane.okres['przymiotnik']} koszt utrzymania lokalu",
                    dane.na_runde(z["finanse"]["utrzymanie_klubu"]))

        zwroty = _zwroty(dane, f, d, info[nazwa], ks, rach)
        if sum(f.magazyn.values()) > 1e-6:
            ksieguj(f, ks, rach, "Koszt magazynowania", dane.na_runde(z["finanse"]["koszt_magazynowania"]))
        if f.bank:
            bank_koniec_miesiaca(f, dane.pozycje("banki")[f.bank], r, ks, rach, dane.rund_w_roku)
        if f.biuro:
            b = dane.pozycje("biura_rachunkowe")[f.biuro]
            ksieguj(f, ks, rach, "Koszt biura rachunkowego", (len(ks.pozycje) + 1) * b["ksiegowanie"])
            ksieguj(f, ks, rach, "Obsługa kadrowo-płacowa",
                    dane.na_runde(len(etat) * b["etat"] + (len(f.pracownicy) - len(etat)) * b["zlecenie"]))
        podatek = ks.podatek(z["finanse"]["podatek_cit"])
        rach.zapisz(f, "Podatek dochodowy", -podatek)
        wyrownaj_gotowke(f, rach, odnawialny[nazwa])
        netto = round(ks.dochod - podatek, 2)
        f.skumulowany_dochod_netto = round(f.skumulowany_dochod_netto + netto, 2)
        wyniki[nazwa] = _wyniki_firmy(dane, f, r, ks, rach, info[nazwa], popyt.get(nazwa, {}),
                                      obsluga.get(nazwa), oferty, rynek, start[nazwa], zwroty, bledy[nazwa], netto)
        if tryb_lokali:
            wyniki[nazwa]["lokale"] = lk.stan_lokali(dane, f, r)
            wyniki[nazwa]["lokal_decyzja"] = info[nazwa]["lokal"]
            if strefowy:
                wyniki[nazwa]["klienci"] = strefowy["klienci"][nazwa]

    s.runda = r
    s.wyniki[r] = wyniki
    s.rynek[r] = _rynek_publiczny(dane, s, r, oferty, popyt, wyniki,
                                  {"_konkurenci_stali": konfiguracja.get("konkurenci_stali"), "_rynek": rynek})
    if tryb_lokali:  # kto zajmuje który lokal (mapa miasta, zakładka Lokale – wyniki)
        s.rynek[r]["lokale"] = lk.zajete(s.firmy)
        if strefowy:
            s.rynek[r]["strefy"] = strefowy["strefy"]
    return s


def _zwroty(dane: Dane, f: Firma, d: dict, info: dict, ks: Ksiega, rach: Rachunek) -> dict:
    """Zwrot niezużytych zasobów kupionych w tej rundzie u dostawców z włączonym zwrotem.

    Jak w oficjalnej grze (gra A/B/C online, Vela – luty): wracają tylko całe nienaruszone opakowania z zakupu tej
    rundy (3 kupione, zużyte 0,1 → zwrot 2), pozycja zakupu w KPiR maleje o ich wartość, osobna pozycja „Koszt zwrotu
    zasobów do dostawcy” = 10% tej wartości, a resztka w magazynie nadal kosztuje 50 PLN magazynowania."""
    wynik = {}
    koszt = dane.z["finanse"]["koszt_zwrotu"]
    for dostawca, zakupy in info["zakupy_zasobow"].items():
        if not (d.get("zwrot_nadmiaru") or {}).get(dostawca):
            continue
        wartosc = 0.0
        for zk in zakupy:
            k = f"{zk['zasob']}|{int(zk['jakosc'])}"
            ile = math.floor(min(float(zk["ilosc"]), f.magazyn.get(k, 0.0)) + 1e-9)
            if ile <= 0:
                continue
            f.magazyn[k] -= ile
            f.wartosc_magazynu_gr[k] = max(0, f.wartosc_magazynu_gr.get(k, 0) - grosze(ile * zk["cena"]))
            wartosc += ile * zk["cena"]
            wynik[zk["zasob"]] = wynik.get(zk["zasob"], 0.0) + ile
        if wartosc <= 0:
            continue
        opis_zakupu = f"Zakup zasobu od dostawcy: {dostawca}"
        for p in ks.pozycje:
            if p["opis"] == opis_zakupu:
                p["towary"] = round(p["towary"] - wartosc, 2)
                break
        rach.zapisz(f, f"Zwrot zasobów do dostawcy: {dostawca}", round(wartosc, 2))
        ksieguj(f, ks, rach, f"Koszt zwrotu zasobów do dostawcy:  {dostawca}", wartosc * koszt)
    return wynik


def _wyniki_firmy(dane, f: Firma, r, ks: Ksiega, rach: Rachunek, info, popyt, obsluga, oferty, rynek, start, zwroty,
                  bledy, netto) -> dict:
    z = dane.z
    w = {"runda": r, "miesiac": dane.nazwa_rundy(r), "kpir": ks.do_slownika(z["finanse"]["podatek_cit"]),
         "rachunek": rach.operacje, "gotowka": f.gotowka, "kredyt_odnawialny": f.kredyt_odnawialny,
         "zadluzenie": zadluzenie(f), "lokaty": sum(l.kwota for l in f.lokaty), "lista_bledow": bledy,
         "reklama": info.get("reklama", {})}

    # sprzedaż
    sprzedaz = {}
    if obsluga:
        for u, d in popyt.items():
            o = oferty[u][f.nazwa]
            sprzedaz[u] = {"popyt": d, "prognoza": f.oferta.get(u, 0), "sprzedaz": obsluga["obsluzeni"][u],
                           "utracona": obsluga["utracona"][u], "przyczyna": obsluga["przyczyna"].get(u, ""),
                           "cena": f.ceny[u].cena, "rabat": f.ceny[u].rabat, "cena_po_rabacie": o["cena"],
                           "przychod": round(obsluga["obsluzeni"][u] * o["cena"], 2), "reklamacje": obsluga["reklamacje"][u],
                           "jakosc": o["jakosc"], "skladniki_popytu": rynek[u][f.nazwa]["skladniki"]}
    w["sprzedaz"] = sprzedaz

    # HR – wykorzystanie czasu i wynagrodzenia
    godz = z["operacje"]["godziny_pracownika"]
    prac = []
    for p in f.pracownicy.values():
        if obsluga and dane.typ_zawodu(p.zawod) == KUCHNIA:
            uzycie = obsluga["godziny_stanowisk"].get(p.stanowisko, 0.0) / godz
        elif obsluga:
            n = max(1, obsluga["liczba_recepcjonistow"])
            uzycie = obsluga["godziny_recepcji"] / n / godz if p.stanowisko in [s.nr for s in kasjerzy(dane, f)] else 0.0
        else:
            uzycie = 0.0
        prac.append({**do_slownika(p), "wykorzystanie": round(min(1.0, uzycie), 4)})
    w["pracownicy"] = prac

    # sprzęt – obłożenie
    sprzet = []
    for st in f.stanowiska:
        for n, q in st.sprzet.items():
            if st.typ == KUCHNIA:
                h = obsluga["godziny_sprzetu"].get(f"{st.nr}|{n}", 0.0) if obsluga else 0.0
            else:
                rec = obsluga and st.pracownik and st.nr in [x.nr for x in kasjerzy(dane, f)]
                h = obsluga["godziny_recepcji"] / max(1, obsluga["liczba_recepcjonistow"]) if rec else 0.0
            sprzet.append({"stanowisko": st.nr, "typ": st.typ, "nazwa": n, "jakosc": q,
                           "oblozenie": round(min(1.0, h / z["operacje"]["godziny_sprzetu"]), 4)})
    w["sprzet"] = sprzet

    # zasoby
    zasoby = []
    zamowione = {}
    for zakupy in info["zakupy_zasobow"].values():
        for zk in zakupy:
            k = f"{zk['zasob']}|{int(zk['jakosc'])}"
            zamowione[k] = zamowione.get(k, 0.0) + float(zk["ilosc"])
    kolejnosc_zasobow = list(dane.zasoby)
    klucze = sorted(set(start["magazyn"]) | set(f.magazyn) | set(zamowione),
                    key=lambda k: (kolejnosc_zasobow.index(k.split("|")[0]), k))
    zuzyte = obsluga["zuzyte_zasoby"] if obsluga else {}
    for k in klucze:
        nazwa, q = k.split("|")
        pocz, kon = start["magazyn"].get(k, 0.0), f.magazyn.get(k, 0.0)
        zam = zamowione.get(k, 0.0)
        zw = 0.0  # zwroty po jakościach nie są śledzone osobno – liczone z bilansu
        wykorzystane = max(0.0, pocz + zam - kon)
        if pocz + zam + kon < 1e-9:
            continue
        zasoby.append({"zasob": nazwa, "jakosc": int(q), "poczatek": round(pocz, 3), "zamowione": round(zam, 3),
                       "wykorzystane": round(wykorzystane, 3), "zwroty": round(zw, 3), "koniec": round(kon, 3),
                       "wartosc": f.wartosc_magazynu(k)})
    for nazwa, ile in zwroty.items():
        for row in zasoby:
            if row["zasob"] == nazwa and row["zamowione"] > 0:
                przenies = min(ile, row["wykorzystane"])
                row["zwroty"] = round(row["zwroty"] + przenies, 3)
                row["wykorzystane"] = round(row["wykorzystane"] - przenies, 3)
                ile -= przenies
    w["zasoby"] = zasoby
    w["zuzyte_zasoby"] = zuzyte

    # karta wyników
    if r >= 2:
        w["karta"] = _karta(dane, f, r, sprzedaz, info, start, netto, oferty)
    f.poprzednio_uslug = len(f.oferta)
    f.poprzednio_pracownikow = len(f.pracownicy)
    return w


def _karta(dane: Dane, f: Firma, r: int, sprzedaz: dict, info: dict, start: dict, netto: float,
           oferty: dict | None = None) -> dict:
    sprzedane = {u: v for u, v in sprzedaz.items() if v["sprzedaz"] > 0}
    klienci = sum(v["sprzedaz"] for v in sprzedane.values())
    popyt = sum(v["popyt"] for v in sprzedaz.values())
    utracona = sum(v["utracona"] for v in sprzedaz.values()) / popyt if popyt else 0.0
    if klienci:
        def srednia_rynku(u, v):
            ceny = [o["cena"] for o in (oferty or {}).get(u, {}).values()]
            return float(np.mean(ceny)) if ceny else v["cena_po_rabacie"]
        r_rynek = sum(v["sprzedaz"] * v["cena_po_rabacie"] / srednia_rynku(u, v) for u, v in sprzedane.items()) / klienci
        q_sr = sum(v["sprzedaz"] * mnoznik_jakosci(dane, *v["jakosc"]) for v in sprzedane.values()) / klienci
        reklamacje = sum(v["reklamacje"] for v in sprzedane.values()) / klienci
    else:
        r_rynek, q_sr, reklamacje = 1.0, 0.0, 0.0
    wyp = sum(dane.pozycje("wyposazenie")[n]["procent"] / 100 for n in f.wyposazenie)
    zk = kw.zadowolenie_klientow(dane, len(sprzedane), r_rynek, f.utracona_poprzednio, q_sr, wyp, reklamacje)
    f.utracona_poprzednio = utracona
    f.baza_klientow *= 1 - dane.z["popyt"]["utrata_klientow"] * utracona   # klienci nieobsłużeni częściowo nie wracają

    prac = list(f.pracownicy.values())
    if prac:
        placa = float(np.mean([(p.pensja + p.premia) / p.pensja_preferowana for p in prac]))
        zlecenia = sum(p.umowa == "zlecenie" for p in prac) / len(prac)
    else:
        placa, zlecenia = 1.0, 0.0
    jakosci = [q for st in f.stanowiska for q in st.sprzet.values()]
    sprzet_gw = float(np.mean(jakosci)) if jakosci else 2.0
    udog = sum(dane.pozycje("udogodnienia")[n]["procent"] / 100 for n in f.udogodnienia)
    zmiany = (len(info["zatrudnieni"]) + len(info["zwolnieni"])) / max(1, len(prac))
    zp = kw.zadowolenie_pracownikow(dane, placa, sprzet_gw, udog, info["szkolenia_procent"], zlecenia,
                                    zmiany if r > 2 else 0.0) if prac else 0.0

    przyrost = max(0, len(f.oferta) - f.poprzednio_uslug) + max(0, len(f.pracownicy) - f.poprzednio_pracownikow)
    roz = kw.rozwoj_firmy(dane, f.majatek, info["inwestycje"], przyrost, len(f.oferta) + len(f.pracownicy),
                          f.rozwoj_poprzedni, info.get("sprzedany_majatek", 0.0), info.get("majatek_przed"))
    f.rozwoj_poprzedni = roz
    zad = kw.wskaznik_zadluzenia(zadluzenie(f), f.majatek, f.skumulowany_dochod_netto)
    return kw.karta(dane, netto, zk, zp, roz, zad)


def _rynek_publiczny(dane: Dane, s: StanGry, r: int, oferty, popyt, wyniki, decyzje) -> dict:
    """Dane widoczne dla wszystkich firm w zakładkach „Wyniki” (zestawienia konkurencji)."""
    firmy = sorted(s.firmy)
    stali = [k["nazwa"] for k in (decyzje.get("_konkurenci_stali") or [])]
    pub = {"firmy": {**{n: s.firmy[n].nazwa_wyswietlana or n for n in firmy}, **{n: f"{n} (stałe ceny)" for n in stali}},
           "popyt": {u: {n: v["popyt"] for n, v in rynek_u.items()} for u, rynek_u in decyzje.get("_rynek", {}).items()},
           "ceny": {u: {n: round(o["cena"], 2) for n, o in v.items()} for u, v in oferty.items()},
           "pracownicy": {}, "wynagrodzenia": {}, "wykorzystanie": {}, "sprzet": {}, "jakosc_zasobow": {},
           "udogodnienia": {}, "wyposazenie": {}, "reklama_tradycyjna": {}, "reklama_internetowa": {}, "karta": {}}
    for n in firmy:
        f, w = s.firmy[n], wyniki[n]
        for zawod in dane.zawody:
            ps = [p for p in w["pracownicy"] if p["zawod"] == zawod]
            pub["pracownicy"].setdefault(n, {})[zawod] = {g: sum(p["gwiazdki"] == g for p in ps) for g in (1, 2, 3)}
            pub["wynagrodzenia"].setdefault(n, {})[zawod] = round(float(np.mean([p["pensja"] for p in ps])), 0) if ps else None
            pub["wykorzystanie"].setdefault(n, {})[zawod] = round(float(np.mean([p["wykorzystanie"] for p in ps])), 4) if ps else None
        pub["sprzet"][n] = {g: sum(x["jakosc"] == g for x in w["sprzet"]) for g in (1, 2, 3)}
        pub["jakosc_zasobow"][n] = {g: round(sum(x["zamowione"] for x in w["zasoby"] if x["jakosc"] == g), 3) for g in (1, 2, 3)}
        pub["udogodnienia"][n] = len(f.udogodnienia)
        pub["wyposazenie"][n] = len(f.wyposazenie)
        pub["reklama_tradycyjna"][n] = round(sum(p["pozostale"] for p in w["kpir"]["pozycje"]
                                                 if p["opis"].startswith("Reklama tradycyjna")), 2)
        pub["reklama_internetowa"][n] = round(sum(p["pozostale"] for p in w["kpir"]["pozycje"]
                                                  if "reklamy internetowej" in p["opis"]), 2)
        if "karta" in w:
            pub["karta"][n] = w["karta"]
    return pub
