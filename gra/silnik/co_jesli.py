"""„Analiza – co jeśli” (F4.5): przewidywany wynik bieżącej rundy dla decyzji drużyny, liczony na kopii stanu.

Rynek jest wspólny, a decyzje innych drużyn w bieżącej rundzie są nieznane (i tajne – podgląd nie może zdradzać
roboczych decyzji rywali). Dlatego boty decydują jak zwykle, a inne drużyny powtarzają swoje decyzje z poprzedniej
rundy – tylko te, które co rundę się ponawia (zamówienia, ceny i prognoza, reklama, promocje, polisy, higiena).
Jednorazowe decyzje (lokal, zatrudnienia, zakupy sprzętu, kredyty, handel…) nie są powtarzane. To przybliżenie:
podgląd nie zna przyszłych decyzji innych drużyn.
"""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from .model import StanGry
from .runda import przelicz_runde

if TYPE_CHECKING:
    from .gra import Gra

# decyzje, które drużyna ponawia co rundę (reszta zostaje w stanie firmy albo jest jednorazowa)
POWTARZANE = ("sprzedaz", "oferta", "zamowienia", "kampanie", "promocje", "polisy",
              "higiena")


def powtorzone(d: dict | None) -> dict:
    """Decyzje z poprzedniej rundy, które drużyna powtórzy w bieżącej."""
    return {k: deepcopy(v) for k, v in (d or {}).items() if k in POWTARZANE}


def decyzje_innych(gra: Gra, firma: str) -> dict[str, dict]:
    """Decyzje pozostałych firm w podglądzie: boty – jak przy przeliczeniu, drużyny – powtórka poprzedniej rundy."""
    from .boty import decyzje_bota
    r, stan = gra.runda, gra.stan(gra.runda - 1)
    poprzednie = gra.decyzje.get(r - 1, {})
    return {f["nazwa"]: (decyzje_bota(gra.dane, stan, f["nazwa"], f["bot"], r, gra.konfiguracja) if f["bot"]
                         else powtorzone(poprzednie.get(f["nazwa"])))
            for f in gra.konfiguracja["firmy"] if f["nazwa"] != firma}


def przewiduj(gra: Gra, firma: str, warianty: list[dict]) -> list[StanGry]:
    """Stan po bieżącej rundzie dla każdego wariantu decyzji firmy (gra się nie zmienia)."""
    inne = decyzje_innych(gra, firma)
    stan = gra.stan(gra.runda - 1)
    return [przelicz_runde(gra.dane, stan, {**deepcopy(inne), firma: deepcopy(d)}, gra.konfiguracja, podglad=True)
            for d in warianty]
