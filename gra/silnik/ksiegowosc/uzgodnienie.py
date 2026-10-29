"""Uzgodnienie kasy z KPiR co rundę (F3a.12) – rachunek przepływów metodą pośrednią:

    gotówka na koniec = gotówka na początku
                        + przychody − koszty z KPiR + koszty bez wydatku (amortyzacja, niezamortyzowana wartość)
                        + VAT należny − VAT naliczony (bez VAT od inwestycji – jest w kwocie inwestycji)
                        ± operacje poza KPiR wg rodzaju (podatki, inwestycje, kredyty, lokaty, kaucje, Harpagon).

Trzy źródła są niezależne: KPiR (Ksiega.pozycje), rejestr VAT (Ksiega.rejestr_vat) i operacje rachunku z rodzajem
(finanse.RODZAJE_OPERACJI). Dodatkowo saldo: początek + suma operacji = koniec (nikt nie zmienił gotówki obok
rachunku). Różnica ≠ 0 to błąd silnika – sprawdza to test na losowych grach botów (test_uzgodnienie.py).
"""
from __future__ import annotations

from .finanse import KOLUMNY_KOSZTOW, RODZAJE_OPERACJI, Ksiega, Rachunek

Z_KPIR = ("kpir", "korekta")    # operacje, których skutek jest w KPiR (i w rejestrze VAT)


def uzgodnij(poczatek: float, koniec: float, ksiega: Ksiega, rachunek: Rachunek) -> dict:
    bez_gotowki = round(sum(p[k] for p in ksiega.pozycje if p.get("bez_gotowki") for k in KOLUMNY_KOSZTOW), 2)
    nalezny = ksiega.vat_suma("nalezny")
    naliczony = round(sum(w["vat"] for w in ksiega.rejestr_vat
                          if w["rodzaj"] == "naliczony" and not w.get("inwestycja")), 2)
    z_kpir = round(ksiega.przychody - ksiega.koszty + bez_gotowki + nalezny - naliczony, 2)
    poza = {r: round(sum(o["kwota"] for o in rachunek.operacje if o["rodzaj"] == r), 2)
            for r in RODZAJE_OPERACJI if r not in Z_KPIR}
    operacje_kpir = round(sum(o["kwota"] for o in rachunek.operacje if o["rodzaj"] in Z_KPIR), 2)
    obliczona = round(poczatek + z_kpir + sum(poza.values()), 2)
    return {"poczatek": poczatek, "koniec": koniec,
            "przychody": ksiega.przychody, "koszty": ksiega.koszty, "bez_gotowki": bez_gotowki,
            "vat_nalezny": nalezny, "vat_naliczony": naliczony, "z_kpir": z_kpir, "operacje_kpir": operacje_kpir,
            "poza": [{"rodzaj": r, "nazwa": RODZAJE_OPERACJI[r], "kwota": k} for r, k in poza.items() if k],
            "obliczona": obliczona, "roznica": round(koniec - obliczona, 2) + 0.0,
            "roznica_kpir": round(operacje_kpir - z_kpir, 2) + 0.0,
            "roznica_rachunku": round(koniec - poczatek - sum(o["kwota"] for o in rachunek.operacje), 2) + 0.0}   # bez −0,0
