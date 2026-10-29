"""„Analiza – co jeśli” (F4.5): podgląd na kopii stanu, inne drużyny powtarzają decyzje z poprzedniej rundy."""

from copy import deepcopy

import pytest

from silnik import co_jesli
from silnik.boty import decyzje_bota
from silnik.gra import Gra


def _gra(rund: int = 2) -> Gra:
    """Gra z lokalami: drużyny H i R (decydują jak boty zrównoważone) i bot; `rund` rund przeliczonych."""
    g = Gra.nowa("t", [("H", None), ("R", None), ("B", "tani")], 6, 5)
    for _ in range(rund):
        for n in ("H", "R"):
            g.ustaw_decyzje(n, decyzje_bota(g.dane, g.stan(), n, "zrownowazony", g.runda, g.konfiguracja))
        g.przelicz(wymus=True)
    return g


@pytest.fixture(scope="module")
def gra() -> Gra:
    return _gra()


def _sprzedaz(s, r: int, n: str) -> dict:
    return {u: (round(v["popyt"], 6), round(v["sprzedaz"], 6)) for u, v in s.wyniki[r][n]["sprzedaz"].items()}


def test_powtarzane_sa_tylko_decyzje_ponawiane_co_runde():
    d = {"zamowienia": [{"dostawca": "x", "zasob": "y", "jakosc": 2, "ilosc": 3}], "sprzedaz": {"frytki": {"cena": 9}},
         "lokal": {"id": "centrum_2", "forma": "najem"}, "zatrudnij": [1], "sprzet_kup": [{"nazwa": "Rożen"}],
         "kredyty_wez": [{"bank": "ING"}], "kampanie": [{"agencja": "a", "kanal": "k"}]}
    p = co_jesli.powtorzone(d)
    assert set(p) == {"zamowienia", "sprzedaz", "kampanie"}
    p["zamowienia"][0]["ilosc"] = 99
    assert d["zamowienia"][0]["ilosc"] == 3   # kopia – podgląd nie zmienia zapisanych decyzji
    assert co_jesli.powtorzone(None) == {}


def test_robocze_decyzje_rywala_nie_wplywaja_na_podglad(gra):
    r = gra.runda
    moje = decyzje_bota(gra.dane, gra.stan(), "H", "zrownowazony", r, gra.konfiguracja)
    przed = co_jesli.przewiduj(gra, "H", [moje])[0]
    rywal = deepcopy(gra.decyzje[r - 1]["R"])
    rywal["sprzedaz"] = {u: {"cena": 1.0} for u in rywal.get("sprzedaz", {})}   # rywal po cichu obniża ceny
    gra.ustaw_decyzje("R", rywal)
    try:
        po = co_jesli.przewiduj(gra, "H", [moje])[0]
    finally:
        gra.ustaw_decyzje("R", {})
    assert _sprzedaz(po, r, "H") == _sprzedaz(przed, r, "H")
    assert po.wyniki[r]["H"]["gotowka"] == przed.wyniki[r]["H"]["gotowka"]


def test_podglad_trafia_gdy_rywal_powtarza_decyzje():
    g = _gra()
    r = g.runda
    moje = decyzje_bota(g.dane, g.stan(), "H", "zrownowazony", r, g.konfiguracja)
    przewidywanie = co_jesli.przewiduj(g, "H", [moje])[0]
    assert g.runda == r and r not in g._stany   # gra się nie zmieniła
    g.ustaw_decyzje("H", moje)
    g.ustaw_decyzje("R", co_jesli.powtorzone(g.decyzje[r - 1]["R"]))
    s = g.przelicz(wymus=True)
    assert _sprzedaz(przewidywanie, r, "H") == _sprzedaz(s, r, "H")
    assert _sprzedaz(przewidywanie, r, "R") == _sprzedaz(s, r, "R")


def test_kilka_wariantow(gra):
    r = gra.runda
    moje = decyzje_bota(gra.dane, gra.stan(), "H", "zrownowazony", r, gra.konfiguracja)
    drozej = deepcopy(moje)
    drozej["sprzedaz"] = {u: {**c, "cena": c["cena"] * 1.5} for u, c in moje["sprzedaz"].items()}
    a, b = co_jesli.przewiduj(gra, "H", [moje, drozej])
    popyt = [sum(v["popyt"] for v in s.wyniki[r]["H"]["sprzedaz"].values()) for s in (a, b)]
    assert popyt[1] < popyt[0]
