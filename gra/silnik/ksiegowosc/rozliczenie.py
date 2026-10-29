"""Rozliczenie jednoosobowej działalności co rundę (gra z lokalami, dane/podatki_2026.yaml) – zastępuje CIT Revasa.

Na koniec rundy, po wszystkich kosztach (z biurem rachunkowym):
1. składki społeczne właściciela – po uldze na start (`ulga_na_start_rund`) preferencyjny ZUS, koszt w KPiR,
2. składka zdrowotna – `stawka` od dochodu rundy, nie mniej niż minimum; poza KPiR, odliczana od dochodu
   do PIT (narastająco do limitu rocznego),
3. zaliczka na PIT liniowy – narastająco od startu gry: podatek od (dochód − odliczona zdrowotna) minus zaliczki
   już wpłacone; strata pomniejsza dochód, ale zwrotu zaliczek w trakcie gry nie ma,
4. VAT – należny − naliczony − nadwyżka z poprzedniej rundy; nadwyżka przechodzi na następną rundę.
Podstawa i podatki w deklaracjach są w pełnych złotych (silnik/ksiegowosc/finanse.py: do_zlotego), składki – co do grosza.
"""
from __future__ import annotations

from ..dane import Dane
from ..model import Firma
from .finanse import Ksiega, Rachunek, do_grosza, do_zlotego, ksieguj

ZUS_SPOLECZNE = "Składki ZUS właściciela (społeczne)"


def reguly_vat(dane: Dane) -> dict | None:
    return dane.podatki["vat"] if dane.podatki else None


def stawka_sprzedazy(dane: Dane, usluga: str) -> float | None:
    if not dane.podatki:
        return None
    s = dane.podatki["vat"]["sprzedaz"]
    return s["uslugi"].get(usluga, s["domyslna"])


def stawka_zasobu(dane: Dane, zasob: str) -> float | None:
    if not dane.podatki:
        return None
    s = dane.podatki["vat"]["zasoby"]
    return s["zasoby"].get(zasob, s["domyslna"])


def zus_pracodawcy(dane: Dane) -> float:
    return dane.podatki["zus_pracodawcy"] if dane.podatki else dane.z["finanse"]["zus_pracodawcy"]


def ulga_na_start(dane: Dane, runda: int) -> bool:
    return runda <= dane.podatki["zus_wlasciciela"]["ulga_na_start_rund"]


def rozlicz(dane: Dane, firma: Firma, runda: int, ksiega: Ksiega, rachunek: Rachunek, zaplac: bool = True) -> dict:
    """Składki, zaliczka PIT i VAT za rundę: zapłata z rachunku, stan narastający w `firma.rozliczenie`.
    `zaplac=False` – samodzielna księgowość (silnik/ksiegowosc/biuro.py): zdrowotną, zaliczkę i VAT płaci się w następnej
    rundzie z deklaracji drużyny (stan narastający jest już poprawny)."""
    p, roz = dane.podatki, firma.rozliczenie
    ulga = ulga_na_start(dane, runda)
    spoleczne = 0.0 if ulga else do_grosza(dane.na_runde(p["zus_wlasciciela"]["spoleczne_miesieczne"]))
    ksieguj(firma, ksiega, rachunek, ZUS_SPOLECZNE, spoleczne, stawka=0.0)

    dochod = ksiega.dochod
    zd = p["zdrowotna"]
    minimum = do_grosza(dane.na_runde(zd["minimalna_miesieczna"]))
    zdrowotna = max(do_grosza(max(0.0, dochod) * zd["stawka"]), minimum)
    odliczenie = round(max(0.0, min(zdrowotna, zd["limit_odliczenia_roczny"] - roz.zdrowotna_odliczona)), 2)

    roz.dochod = round(roz.dochod + dochod, 2)
    roz.zdrowotna_odliczona = round(roz.zdrowotna_odliczona + odliczenie, 2)
    podstawa = do_zlotego(max(0.0, roz.dochod - roz.zdrowotna_odliczona))
    podatek_narastajaco = do_zlotego(podstawa * p["pit_liniowy"])
    zaliczka = float(max(0, podatek_narastajaco - do_zlotego(roz.zaliczki)))
    roz.zaliczki = round(roz.zaliczki + zaliczka, 2)

    nalezny, naliczony, nadwyzka = ksiega.vat_suma("nalezny"), ksiega.vat_suma("naliczony"), roz.vat_nadwyzka
    saldo = round(nalezny - naliczony - nadwyzka, 2)
    vat = float(do_zlotego(saldo)) if saldo > 0 else 0.0
    roz.vat_nadwyzka = round(-saldo, 2) if saldo < 0 else 0.0

    if zaplac:
        rachunek.zapisz(firma, "Składka zdrowotna właściciela", -zdrowotna, "podatki")
        rachunek.zapisz(firma, "Zaliczka na podatek dochodowy (PIT liniowy)", -zaliczka, "podatki")
        rachunek.zapisz(firma, "VAT do urzędu skarbowego", -vat, "podatki")
    roz.zaplacone = round(roz.zaplacone + spoleczne + ((zdrowotna + zaliczka + vat) if zaplac else 0.0), 2)
    return {"ulga_na_start": ulga, "zaplacone": zaplac, "zus_spoleczne": spoleczne,
            "zdrowotna": zdrowotna, "zdrowotna_minimum": minimum, "zdrowotna_odliczenie": odliczenie,
            "dochod": dochod, "dochod_narastajaco": roz.dochod, "zdrowotna_odliczona": roz.zdrowotna_odliczona,
            "podstawa": podstawa, "stawka_pit": p["pit_liniowy"], "podatek_narastajaco": podatek_narastajaco,
            "zaliczka": zaliczka, "zaliczki_narastajaco": roz.zaliczki,
            "vat_nalezny": nalezny, "vat_naliczony": naliczony, "vat_nadwyzka_poprzednia": nadwyzka,
            "vat_saldo": saldo, "vat_do_zaplaty": vat, "vat_nadwyzka": roz.vat_nadwyzka,
            "razem": round(spoleczne + zdrowotna + zaliczka + vat, 2), "zaplacone_narastajaco": roz.zaplacone,
            "dochod_netto": round(dochod - zaliczka - zdrowotna, 2)}


def rejestr(ksiega: Ksiega) -> dict:
    """Rejestr VAT rundy z podsumowaniem wg stawek (do wyników i widoku decyzji)."""
    stawki: dict[str, dict] = {}
    for w in ksiega.rejestr_vat:
        k = stawki.setdefault(f"{w['rodzaj']}|{w['stawka']}", {"rodzaj": w["rodzaj"], "stawka": w["stawka"],
                                                              "netto": 0.0, "vat": 0.0, "brutto": 0.0})
        for pole in ("netto", "vat", "brutto"):
            k[pole] = round(k[pole] + w[pole], 2)
    return {"pozycje": ksiega.rejestr_vat, "stawki": sorted(stawki.values(), key=lambda x: (x["rodzaj"], x["stawka"])),
            "nalezny": ksiega.vat_suma("nalezny"), "naliczony": ksiega.vat_suma("naliczony")}
