"""Środki trwałe i amortyzacja (gra z lokalami, F3a.6).

Kupiony lokal i wybudowany budynek oraz inwestycje od progu `amortyzacja_prog` (sprzęt, wyposażenie, stanowiska)
trafiają do ewidencji środków trwałych: zakup to ruch na rachunku, a koszt w KPiR rozkłada się liniowo – co rundę
odpis amortyzacyjny według rocznej stawki (`amortyzacja_roczna`). Tańsze zakupy od razu w koszty (jak w Revasie).
Grunt (działka) jest w ewidencji, ale się nie amortyzuje. Przy sprzedaży niezamortyzowana wartość idzie w koszty.
Z VAT (F3a.11): zakup sprzętu, wyposażenia i stanowisk daje VAT naliczony, a do ewidencji trafia wartość netto.
"""

from __future__ import annotations

from ..dane import Dane
from ..model import Firma, SrodekTrwaly
from .finanse import Ksiega, Rachunek, ksieguj


def stawka(dane: Dane, rodzaj: str) -> float:
    return dane.z["finanse"]["amortyzacja_roczna"][rodzaj]


def przyjmij(dane: Dane, firma: Firma, nazwa: str, rodzaj: str, wartosc: float, runda: int) -> None:
    """Nowy środek trwały w ewidencji (amortyzacja od następnej rundy)."""
    firma.srodki_trwale.append(SrodekTrwaly(nazwa=nazwa, rodzaj=rodzaj, wartosc=wartosc, od_rundy=runda,
                                            stawka=stawka(dane, rodzaj)))


def zakup(dane: Dane, firma: Firma, ksiega: Ksiega, rachunek: Rachunek, opis: str, nazwa: str, rodzaj: str,
          cena: float, runda: int) -> None:
    """Zakup inwestycji: od progu – środek trwały (amortyzacja), poniżej progu – koszt od razu."""
    if cena >= dane.z["finanse"]["amortyzacja_prog"]:
        rachunek.zapisz(firma, opis, -cena, "inwestycje")
        vat = ksiega.zarejestruj(opis, {dane.podatki["vat"]["srodki_trwale"]: cena}, False, inwestycja=True) if ksiega.vat is not None else 0.0
        przyjmij(dane, firma, nazwa, rodzaj, round(cena - vat, 2), runda)
    else:
        ksieguj(firma, ksiega, rachunek, opis, cena)


def sprzedaj(firma: Firma, nazwa: str, ksiega: Ksiega) -> bool:
    """Usuwa środek trwały z ewidencji; niezamortyzowana wartość – koszt w KPiR. False – nie było go w ewidencji."""
    st = next((s for s in firma.srodki_trwale if s.nazwa == nazwa), None)
    if st is None:
        return False
    firma.srodki_trwale.remove(st)
    ksiega.dodaj(f"Niezamortyzowana wartość sprzedanego środka trwałego: {nazwa}", st.wartosc - st.umorzenie,
                 bez_gotowki=True)
    return True


def amortyzuj(dane: Dane, firma: Firma, runda: int, ksiega: Ksiega) -> None:
    """Odpisy amortyzacyjne rundy (koszt w KPiR bez ruchu na rachunku)."""
    for st in firma.srodki_trwale:
        if st.od_rundy >= runda or st.stawka <= 0:
            continue
        odpis = min(round(st.wartosc * st.stawka / dane.rund_w_roku, 2), round(st.wartosc - st.umorzenie, 2))
        if odpis > 0:
            ksiega.dodaj(f"Amortyzacja: {st.nazwa}", odpis, bez_gotowki=True)
            st.umorzenie = round(st.umorzenie + odpis, 2)


def amortyzuj_majatek(dane: Dane, firma: Firma, majatek_przed: float) -> None:
    """Amortyzacja sumy inwestycji do karty (Z1): tańsze zakupy są od razu w kosztach, więc do rozwoju firmy
    majątek traci na wartości jak sprzęt – liniowo od sumy sprzed rundy (zakupy rundy od następnej)."""
    odpis = round(min(firma.majatek, majatek_przed) * stawka(dane, "sprzet") / dane.rund_w_roku, 2)
    firma.umorzenie_majatku = round(min(firma.majatek, firma.umorzenie_majatku + odpis), 2)


def zmniejsz_majatek(firma: Firma, wartosc: float) -> None:
    """Sprzedaż (albo utrata) części majątku po cenie zakupu: umorzenie maleje w tej samej proporcji."""
    if firma.majatek > 0:
        firma.umorzenie_majatku = round(firma.umorzenie_majatku * max(0.0, 1 - wartosc / firma.majatek), 2)
    firma.majatek -= wartosc


def ewidencja(firma: Firma) -> list[dict]:
    """Tabela ewidencji środków trwałych (zakładka Inwestycje)."""
    return [{"nazwa": s.nazwa, "rodzaj": s.rodzaj, "od_rundy": s.od_rundy, "stawka": s.stawka, "wartosc": s.wartosc,
             "umorzenie": s.umorzenie, "netto": round(s.wartosc - s.umorzenie, 2)} for s in firma.srodki_trwale]
