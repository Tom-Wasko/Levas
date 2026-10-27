"""Poziomy botów (F4.4, P19): łatwy, średni, trudny i niemożliwy różnią się sposobem planowania (niemożliwy – oszukuje)."""
import pytest

from balans.symuluj import rozegraj
from silnik import boty
from silnik.dane import dane_domyslne
from silnik.gra import Gra

RUND = 12   # trudny bot otwiera drugi lokal dopiero z zapasem gotówki


@pytest.fixture(scope="module")
def poziomy() -> dict[str, dict[str, dict]]:
    return {p: rozegraj(RUND, p, 7) for p in ("latwy", "sredni", "trudny")}


def _srednia(w: dict[str, dict], co: str) -> float:
    return sum(x[co] for x in w.values()) / len(w)


def test_wyzszy_poziom_zarabia_srednio_wiecej(poziomy):
    assert _srednia(poziomy["latwy"], "gotowka") < _srednia(poziomy["sredni"], "gotowka")
    assert _srednia(poziomy["sredni"], "gotowka") < _srednia(poziomy["trudny"], "gotowka")


def test_planujacy_bot_marnuje_mniej_towaru(poziomy):
    # łatwy zamawia na cały przewidywany popyt – towar psuje się, gdy kuchnia nie nadąża
    assert _srednia(poziomy["sredni"], "przeterminowane") < _srednia(poziomy["latwy"], "przeterminowane") / 2
    assert _srednia(poziomy["trudny"], "przeterminowane") < _srednia(poziomy["latwy"], "przeterminowane") / 2


def test_trudny_bot_otwiera_kolejny_lokal(poziomy):
    zasady = dane_domyslne().boty["poziomy"]["trudny"]["kolejny_lokal"]
    assert any(x["lokale"] > 1 for x in poziomy["trudny"].values())
    assert all(x["lokale"] <= zasady["maks_lokali"] for x in poziomy["trudny"].values())
    assert all(x["lokale"] == 1 for p in ("latwy", "sredni") for x in poziomy[p].values())


def test_poziom_z_konfiguracji_gry():
    dane = dane_domyslne()
    konf = {"firmy": [{"nazwa": "A", "bot": "tani", "poziom": "trudny"}, {"nazwa": "B", "bot": "tani"}]}
    assert boty.poziom(dane, konf, "A") is dane.boty["poziomy"]["trudny"]
    assert boty.poziom(dane, konf, "B") is dane.boty["poziomy"][boty.DOMYSLNY_POZIOM]


def test_latwy_bot_nie_reklamuje_sie_i_nie_daje_promocji():
    g = Gra.nowa("t", [("A", "agresywny"), ("B", "premium")], 6, 3, poziomy={"A": "latwy", "B": "latwy"})
    for _ in range(6):
        g.przelicz(wymus=True)
    for r in range(1, 7):
        for n in ("A", "B"):
            assert not g.decyzje[r].get(n, {}).get("kampanie")
            assert not g.decyzje[r].get(n, {}).get("promocje")


def test_niemozliwy_bot_oszukuje_popytem():
    """Poziom niemożliwy (P19): przy tej samej strategii klienci wolą jego lokale; drużyn graczy to nie dotyczy."""
    dane = dane_domyslne()
    konf = {"firmy": [{"nazwa": "A", "bot": "tani", "poziom": "niemozliwy"}, {"nazwa": "B", "bot": "tani", "poziom": "trudny"},
                      {"nazwa": "C", "bot": None, "poziom": "niemozliwy"}]}
    assert boty.przewaga_popytu(dane, konf, "A") == dane.boty["poziomy"]["niemozliwy"]["przewaga_popytu"] > 1
    assert boty.przewaga_popytu(dane, konf, "B") == boty.przewaga_popytu(dane, konf, "C") == 1
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "zrownowazony")], 6, 5, poziomy={"A": "niemozliwy", "B": "trudny"})
    for _ in range(6):
        s = g.przelicz(wymus=True)
    sprzedaz = {n: sum(v["sprzedaz"] for r in range(2, 7) for v in s.wyniki[r][n]["sprzedaz"].values()) for n in "AB"}
    assert sprzedaz["A"] > sprzedaz["B"]
