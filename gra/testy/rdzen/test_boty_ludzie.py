"""B9: boty potrafią wybrać każdą opcję kadrową – pensję (`pensja`), gwiazdki ludzi niezależnie od sprzętu
(`jakosc_ludzi`), kanał rekrutacji (`kanal`), premię (`premia`) i właściciela na stanowisku kasy
(`wlasciciel_godziny`); pomiar w balans/warianty.py."""
import copy

import pytest

from silnik import boty
from silnik.gra import Gra
from silnik.ludzie import rynek_pracy as rp

pytestmark = pytest.mark.dane_gry


def _dane_strategii(dane, strategia: dict):
    dane = copy.copy(dane)
    st = dane.boty["strategie"]
    dane.boty = {**dane.boty, "strategie": {**st, "zrownowazony": {**st["zrownowazony"], **strategia}}}
    return dane


def _gra(strategia: dict, rund: int):
    """Gra, w której firma A (zrównoważony z nadpisaną strategią) rozegrała `rund` rund."""
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5)
    g.dane = _dane_strategii(g.dane, strategia)
    for _ in range(rund):
        g.przelicz(wymus=True)
    return g


def _decyzje(strategia: dict, runda: int = 1) -> dict:
    """Decyzje firmy A w rundzie `runda` gry, w której wcześniejsze rundy grała z tą samą strategią."""
    g = _gra(strategia, runda - 1)
    return boty.decyzje_bota(g.dane, g.stan(runda - 1), "A", "zrownowazony", runda, g.konfiguracja)


def _kandydat(g, kid):
    return next(k for k in g.stan(0).kandydaci if k["id"] == kid)


def test_pensja_bota_wg_strategii():
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5)
    minimum = g.dane.z["finanse"]["placa_minimalna"]
    baza = _decyzje({})["zatrudnij"]
    assert baza and all(z["pensja"] == _kandydat(g, z["kandydat"])["pensja_preferowana"] for z in baza)
    wyzsza = _decyzje({"pensja": 1.25})["zatrudnij"]
    assert all(z["pensja"] == max(minimum, round(1.25 * _kandydat(g, z["kandydat"])["pensja_preferowana"]))
               for z in wyzsza)
    assert {z["pensja"] for z in _decyzje({"pensja": "minimalna"})["zatrudnij"]} == {minimum}


def test_gwiazdki_ludzi_i_kanal_rekrutacji():
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5)
    jedynki = _decyzje({"jakosc_ludzi": 1})["zatrudnij"]
    dwojki = _decyzje({})["zatrudnij"]
    sr = lambda zz: sum(_kandydat(g, z["kandydat"])["gwiazdki"] for z in zz) / len(zz)  # noqa: E731
    assert jedynki and sr(jedynki) < sr(dwojki)
    assert not _decyzje({"kanal": "agencja"})["zatrudnij"]   # agencja działa od rundy 2
    g = _gra({"kanal": "agencja"}, 1)
    agencja = boty.decyzje_bota(g.dane, g.stan(1), "A", "zrownowazony", 2, g.konfiguracja)["zatrudnij"]
    pula = {k["id"]: k for k in g.stan(1).kandydaci}
    assert agencja and all(z["kanal"] == "agencja" for z in agencja)
    assert all("agencja" in rp.kanaly_kandydata(g.dane, pula[z["kandydat"]], 2) for z in agencja)


def test_premia_dla_kazdego_co_runde():
    g = _gra({"premia": 300}, 2)
    s = g.stan(2)
    assert s.firmy["A"].pracownicy and all(p.premia == 300 for p in s.firmy["A"].pracownicy.values())
    assert any(p["opis"].startswith("Bonus dla pracownika") for p in s.wyniki[2]["A"]["rachunek"])


def test_wlasciciel_na_kasie_zamiast_kasjera():
    baza = _decyzje({})
    d = _decyzje({"wlasciciel_godziny": 20})
    w = d["wlasciciel_stanowisko"]
    assert w["typ"] == "kasa" and 0 < w["godziny"] <= 20   # bez godzin na rekrutację (pracuj.pl)
    kasjerzy = lambda d: [z for z in d["zatrudnij"] if z["typ"] == "kasa"]  # noqa: E731
    assert len(kasjerzy(d)) == len(kasjerzy(baza)) - 1
    g = _gra({"wlasciciel_godziny": 20}, 3)
    for r in (1, 2, 3):   # co rundę od nowa, na tym samym pustym stanowisku (bez dokładania kas)
        info = g.stan(r).wyniki[r]["A"]["wlasciciel_stanowisko"]
        assert info["przyjete"] and info["typ"] == "kasa" and info["nr"] == w["nr"]
    f = g.stan(3).firmy["A"]
    assert [s.pracownik for s in f.stanowiska_typu("kasa")] == [None]
