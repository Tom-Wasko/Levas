"""Bójka o falafel (UF8; pomysł autora: „jak wybierzesz do oferty falafel, to ktoś cię pobije kolejnego dnia”).

Dane: `dane/zdarzenia/falafel.yaml` (plik opcjonalny – bez niego historii nie ma). Od rundy `zasady.od_rundy` drużyna,
która w poprzedniej rundzie miała w ofercie danie `zasady.usluga`, ma szansę `zasady.szansa` (strumień „falafel”), że
w lokalu zacznie się historia bójki – najwyżej raz na grę. Historia jak inne sprawy w lokalu (silnik/swiat/zdarzenia.py):
opcje kosztują czas właściciela albo gotówkę, skutki – plastry (gotówka) albo mniej godzin właściciela.

Warunek zależy tylko od stanu sprzed decyzji rundy (`Firma.falafel_runda` – zapisywana na koniec rozegrania zdarzeń),
więc zakładka przed decyzjami i przeliczenie rundy widzą tę samą historię.
"""
from __future__ import annotations

from ..dane import Dane
from ..losowosc import strumien
from ..model import Firma

ZRODLO = "falafel"


def dane_falafela(dane: Dane) -> dict | None:
    return (dane.zdarzenia or {}).get("falafel")


def historie(dane: Dane) -> dict[str, dict]:
    f = dane_falafela(dane)
    return {f["historia"]["id"]: f["historia"]} if f else {}


def w_ofercie(dane: Dane, f: Firma) -> bool:
    """Czy danie z bójki jest teraz w ofercie firmy albo któregoś lokalu."""
    u = dane_falafela(dane)["zasady"]["usluga"]
    return u in f.oferta or any(u in lok.menu for lok in f.lokale)


def startuje(dane: Dane, f: Firma, runda: int, ziarno) -> str | None:
    """Id historii bójki, gdy zaczyna się w tej rundzie (None – nie). Wynik nie zależy od tego, czy runda została już
    rozegrana (bójka z tej rundy w `Firma.bojka_falafel` nie blokuje)."""
    b = dane_falafela(dane)
    if not b or runda < b["zasady"]["od_rundy"] or not f.lokale:
        return None
    if f.bojka_falafel is not None and f.bojka_falafel < runda:
        return None   # raz na grę
    if f.falafel_runda != runda - 1:
        return None   # „kolejnego dnia” – tylko po tygodniu z falafelem w ofercie
    if strumien(ziarno, runda, ZRODLO, f.nazwa).random() >= b["zasady"]["szansa"]:
        return None
    return b["historia"]["id"]


def koniec_rundy(dane: Dane, f: Firma, runda: int) -> None:
    """Po rozegraniu zdarzeń rundy (nie w podglądzie): zapamiętuje, czy falafel był w ofercie."""
    if dane_falafela(dane) and w_ofercie(dane, f):
        f.falafel_runda = runda
