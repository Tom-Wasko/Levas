"""Majątek netto firmy (Z2) – miara wyniku obok karty: ile firma jest warta na koniec rundy.

Aktywa: gotówka, lokaty, kaucje za najem, nadwyżka VAT do przeniesienia, zapasy (średni koszt), kupione lokale,
budynki i grunt po amortyzacji (ewidencja środków trwałych), sprzęt i wyposażenie po amortyzacji (jak w karcie, Z1).
Długi: kredyty (z zaległymi ratami), debet (kredyt odnawialny), zaległe raty leasingu, dług
u Harpagona z odsetkami i niezwrócona wpłata inwestora ratunkowego (Z3). Sprzęt w leasingu nie jest majątkiem, a przyszłe raty leasingu i czynsze nie są długiem.

Prywatny portfel właściciela jest poza majątkiem firmy: wynik widzi mistrz gry, a portfel zdradzałby klub
(silnik/pieniadze/kasyno.py). Pomiary balansu doliczają go osobno (`z_portfelem`).
"""
from __future__ import annotations

from ..model import Firma
from .karta import NIERUCHOMOSCI


def majatek_netto(f: Firma) -> dict:
    """Składniki majątku netto (zł) i `razem` = aktywa − długi."""
    nieruchomosci = sum(s.wartosc - s.umorzenie for s in f.srodki_trwale if s.rodzaj in NIERUCHOMOSCI)
    aktywa = {"gotowka": f.gotowka, "lokaty": sum(lo.kwota for lo in f.lokaty),
              "kaucje": sum(lk.kaucja for lk in f.lokale), "vat": f.rozliczenie.vat_nadwyzka,
              "zapasy": sum(f.wartosc_magazynu_gr.values()) / 100, "nieruchomosci": nieruchomosci,
              "sprzet": f.majatek - f.umorzenie_majatku}
    dlugi = {"kredyty": sum(k.pozostalo for k in f.kredyty), "debet": f.kredyt_odnawialny,
             "leasing": sum(lea.rata * lea.zalegle for lea in f.leasingi),
             "harpagon": f.harpagon.dlug if f.harpagon else 0.0,
             "inwestor": f.inwestor.dlug if f.inwestor else 0.0}
    wynik = {k: round(v, 2) for k, v in aktywa.items()} | {k: round(-v, 2) for k, v in dlugi.items()}
    return wynik | {"razem": round(sum(aktywa.values()) - sum(dlugi.values()), 2)}


def z_portfelem(w: dict) -> float:
    """Majątek netto z wyników rundy razem z portfelem właściciela (pomiary balansu: wyjątek kasyna)."""
    return round(w["majatek_netto"]["razem"] + (w.get("wlasciciel") or {}).get("portfel", 0.0), 2)
