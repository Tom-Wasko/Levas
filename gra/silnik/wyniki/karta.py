"""Karta wyników: 5 wskaźników i wynik działalności (iloczyn). Wzory i parametry: dane/zalozenia.yaml → karta_wynikow.

- wynik ekonomiczny = dochód netto / 20 000 (potwierdzone na 7 rundach gry ATH),
- wynik działalności = iloczyn wskaźników; 0, gdy wynik ekonomiczny < 0,
- zadowolenie pracowników – skalibrowane na 17 kartach (gra A/B/C online z 6 miejscami + ATH; błąd średni 0,0006),
- zadowolenie klientów – skalibrowane na 17 kartach (błąd LOO 0,024): liczba usług (efekt rośnie do 6 usług),
  cena względem średniej rynku, utracona sprzedaż z poprzedniego miesiąca, wyposażenie,
- rozwój firmy – przybliżenie (niska pewność),
- wskaźnik zadłużenia – 1 bez kredytu (założenie dla wzoru z kredytem).
Kalibracja: kalibracja/kalibracja_online.py.

Gra z lokalami (F4.1, `kebab`): wskaźniki Revasa dostają składniki kebabowe z wyników tygodnia (karta_wynikow → kebab):
cena względem ceny preferowanej strefy lokalu, brakujące dania, kolejki, kontrola sanepidu z mandatem i wypadki
(klienci), przepracowanie (pracownicy), kolejne lokale i przyrost menu i załogi (rozwój), dług u Harpagona (zadłużenie).
"""
from __future__ import annotations

import math

from ..dane import Dane

EPS = 1e-9


def zadowolenie_klientow(dane: Dane, liczba_uslug: int, cena_wzgledem_rynku: float, utracona_poprzednio: float,
                         jakosc: float, wyposazenie_procent: float, reklamacje: float) -> float:
    """cena_wzgledem_rynku: średnia (ważona klientami) cena po rabacie / średnia cena firm oferujących usługę;
    utracona_poprzednio: udział utraconej sprzedaży w poprzedniej rundzie (klienci odchodzą z opóźnieniem)."""
    p = dane.z["karta_wynikow"]["zadowolenie_klientow"]
    if liczba_uslug == 0:
        return 0.0
    return round(p["stala"] + p["ln_liczby_uslug"] * math.log(min(liczba_uslug, p["limit_uslug"]))
                 + p["cena_wzgledem_rynku"] * cena_wzgledem_rynku + p["utracona_poprzednio"] * utracona_poprzednio
                 + p["jakosc"] * jakosc + p["wyposazenie_na_procent"] * wyposazenie_procent
                 + p["reklamacje"] * reklamacje, 3)


def zadowolenie_pracownikow(dane: Dane, placa_wzgledna: float, sprzet_gwiazdki: float, udogodnienia_procent: float,
                            szkolenia_procent: float, udzial_zlecen: float, zmiany: float) -> float:
    """placa_wzgledna: średnia (pensja + premia) / preferowana; sprzet_gwiazdki: średnia jakość całego sprzętu klubu."""
    p = dane.z["karta_wynikow"]["zadowolenie_pracownikow"]
    return round(p["stala"] + p["placa_wzgledem_preferowanej"] * (placa_wzgledna - 1)
                 + p["sprzet_na_gwiazdke"] * (sprzet_gwiazdki - 3)
                 + p["udogodnienia_na_procent"] * udogodnienia_procent
                 + p["szkolenia_w_miesiacu_na_procent"] * szkolenia_procent
                 + p.get("szkolenie_w_miesiacu", 0.0) * (szkolenia_procent > 0)
                 + p["udzial_umow_zlecenie"] * udzial_zlecen + p["zmiany_zatrudnienia"] * zmiany, 3)


def rozwoj_firmy(dane: Dane, majatek: float, inwestycje: float, przyrost: int, uslugi_i_pracownicy: int,
                 poprzedni: float | None, sprzedany_majatek: float = 0.0, majatek_przed: float | None = None) -> float:
    """majatek – po cenach zakupu, po odjęciu sprzedanego; inwestycje netto = zakupy − wartość sprzedanego, odniesione do
    majątku sprzed miesiąca (co najmniej skala) – analiza_od_nowa.py: 21 kart (ATH 11 mies., A/B/C), LOO 0,106."""
    p = dane.z["karta_wynikow"]["rozwoj_firmy"]
    if majatek_przed is not None and "inwestycje_netto" in p:
        return round(p["stala"] + p["majatek"] * math.log1p(max(0.0, majatek) / p["majatek_skala"])
                     + p["inwestycje_netto"] * (inwestycje - sprzedany_majatek) / max(majatek_przed, p["majatek_skala"]), 3)
    x = (p["majatek"] * math.log1p(majatek / p["majatek_skala"]) + p["inwestycje_wzgledne"] * inwestycje / max(majatek, 1)
         + p["przyrost_uslug_i_pracownikow"] * przyrost / max(uslugi_i_pracownicy, 1))
    if poprzedni is not None:
        x = p["wygladzanie"] * poprzedni + (1 - p["wygladzanie"]) * x
    return round(x, 3)


def wskaznik_zadluzenia(dlug: float, majatek: float, skumulowany_dochod: float) -> float:
    """Udział kapitału własnego: 1 − dług / (majątek + skumulowany dochód netto + dług). ATH październik: kredyt 199 900,
    wzór 0,912 vs 0,911 w grze (bez „+ dług” w mianowniku byłoby 0,903)."""
    if dlug <= 0:
        return 1.0
    podstawa = majatek + max(0.0, skumulowany_dochod) + dlug
    return round(max(0.0, 1 - dlug / podstawa), 3)


def karta(dane: Dane, dochod_netto: float, zk: float, zp: float, roz: float, zad: float) -> dict:
    we = round(dochod_netto / dane.z["karta_wynikow"]["wynik_ekonomiczny_dzielnik"], 3)
    wd = round(we * zp * zk * roz * zad, 3) if we >= 0 else 0.0
    return {"wynik_dzialalnosci": wd, "wynik_ekonomiczny": we, "zadowolenie_pracownikow": zp,
            "zadowolenie_klientow": zk, "rozwoj_firmy": roz, "wskaznik_zadluzenia": zad}


KOLEJKI = ("pracownicy/sprzęt", "kasa")   # przyczyny utraconej sprzedaży z operacje.obsluz – za mało rąk lub sprzętu


def cena_wzgledem_strefy(dane: Dane, sprzedane: dict) -> float:
    """Średnia (ważona klientami) cena po rabacie / cena preferowana dania w strefie lokalu (lokale ważone popytem)."""
    klienci = sum(v["sprzedaz"] for v in sprzedane.values())
    if not klienci:
        return 1.0
    strefy = dane.mapa["popyt"]["strefy"]
    suma = 0.0
    for u, v in sprzedane.items():
        lok = v["skladniki_popytu"].get("lokale") or {}
        waga = sum(lok.values())
        mn = sum(n * strefy[dane.lokale[x]["strefa"]]["cena"] for x, n in lok.items()) / waga if waga else 1.0
        suma += v["sprzedaz"] * v["cena_po_rabacie"] / (dane.uslugi[u]["cena_preferowana"] * mn)
    return suma / klienci


def miary_kebabu(dane: Dane, f, w: dict) -> dict:
    """Mierniki tygodnia do składników kebabowych karty (z wyników firmy `w` w grze z lokalami)."""
    sprzedaz = w["sprzedaz"]
    popyt = sum(v["popyt"] for v in sprzedaz.values())
    dni = len((w.get("klienci") or {}).get("dni") or [])
    dania_dni = len(f.oferta) * len(f.lokale) * dni
    wyl = (w.get("swiezosc") or {}).get("wylaczone") or []
    prac = w.get("pracownicy") or []
    prog = dane.z["karta_wynikow"]["kebab"]["zadowolenie_pracownikow"]["prog_przepracowania"]
    return {
        "cena_wzgledem_strefy": round(cena_wzgledem_strefy(dane, {u: v for u, v in sprzedaz.items() if v["sprzedaz"] > 0}), 4),
        "brakujace_dania": round(min(1.0, len(wyl) / dania_dni), 4) if dania_dni else 0.0,
        "kolejki": round(sum(v["utracona"] for v in sprzedaz.values() if v["przyczyna"] in KOLEJKI) / popyt, 4) if popyt else 0.0,
        "mandat": float(((w.get("urzad") or {}).get("kontrola") or {}).get("mandat") or 0),
        "wypadki": len((w.get("zdarzenia") or {}).get("szkody") or []),
        "przepracowanie": round(sum(max(0.0, p["wykorzystanie"] - prog) for p in prac) / len(prac), 4) if prac else 0.0,
        "lokale": len(f.lokale),
        "dlug_harpagona": f.harpagon.dlug if f.harpagon else 0.0,
    }


def kebab(dane: Dane, f, w: dict, netto: float, zadluzenie_bankowe: float) -> dict:
    """Karta wyników w grze z lokalami: wskaźniki Revasa z `w["karta"]` + składniki kebabowe; podmienia `w["karta"]`
    (iloczyn liczony od nowa) i zwraca {"miary", "skladniki": {wskaźnik: {miernik: poprawka}}}."""
    p = dane.z["karta_wynikow"]["kebab"]
    m = miary_kebabu(dane, f, w)
    k = w["karta"]
    pc = p["zadowolenie_klientow"]
    sk = {"kolejki": pc["kolejki"] * m["kolejki"], "brakujace_dania": pc["brakujace_dania"] * m["brakujace_dania"],
          "kontrola_z_mandatem": pc["kontrola_z_mandatem"] * (m["mandat"] > 0), "wypadki": pc["wypadek"] * m["wypadki"]}
    sp = {"przepracowanie": p["zadowolenie_pracownikow"]["przepracowanie"] * m["przepracowanie"]}
    sr = {"kolejne_lokale": p["rozwoj_firmy"]["kolejny_lokal"] * max(0, m["lokale"] - 1)}
    skladniki = {"zadowolenie_klientow": sk, "zadowolenie_pracownikow": sp, "rozwoj_firmy": sr}
    # wskaźnik 0 (brak sprzedaży, brak pracowników) zostaje zerem
    zk = max(0.0, k["zadowolenie_klientow"] + sum(sk.values())) if k["zadowolenie_klientow"] else 0.0
    zp = max(0.0, k["zadowolenie_pracownikow"] + sum(sp.values())) if k["zadowolenie_pracownikow"] else 0.0
    roz = max(0.0, k["rozwoj_firmy"] + sum(sr.values()))
    dlug = zadluzenie_bankowe + p["wskaznik_zadluzenia"]["waga_harpagona"] * m["dlug_harpagona"]
    zad = wskaznik_zadluzenia(dlug, f.majatek, f.skumulowany_dochod_netto)
    skladniki["wskaznik_zadluzenia"] = {"dlug_harpagona": zad - k["wskaznik_zadluzenia"]}
    w["karta"] = karta(dane, netto, round(zk, 3), round(zp, 3), round(roz, 3), zad)
    return {"miary": m, "skladniki": {s: {x: round(y, 4) for x, y in d.items() if abs(y) > EPS}
                                      for s, d in skladniki.items()}}
