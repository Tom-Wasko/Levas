"""Karta wyników: 5 wskaźników i wynik działalności (iloczyn). Wzory i parametry: dane/zalozenia.yaml → karta_wynikow.

- wynik ekonomiczny = dochód netto / 20 000 (potwierdzone na 7 rundach gry ATH),
- wynik działalności = iloczyn wskaźników; 0, gdy wynik ekonomiczny < 0,
- zadowolenie pracowników – skalibrowane na 17 kartach (gra A/B/C online z 6 miejscami + ATH; błąd średni 0,0006),
- zadowolenie klientów – skalibrowane na 17 kartach (błąd LOO 0,024): liczba usług (efekt rośnie do 6 usług),
  cena względem średniej rynku, utracona sprzedaż z poprzedniego miesiąca, wyposażenie,
- rozwój firmy – przybliżenie (niska pewność),
- wskaźnik zadłużenia – 1 bez kredytu (założenie dla wzoru z kredytem).
Kalibracja: kalibracja/kalibracja_online.py.
"""
from __future__ import annotations

import math

from .dane import Dane


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


NAZWY_WSKAZNIKOW = {"wynik_dzialalnosci": "Wynik działalności", "wynik_ekonomiczny": "Wynik ekonomiczny",
                    "zadowolenie_pracownikow": "Zadowolenie pracowników", "zadowolenie_klientow": "Zadowolenie klientów",
                    "rozwoj_firmy": "Rozwój firmy", "wskaznik_zadluzenia": "Wskaźnik zadłużenia"}
