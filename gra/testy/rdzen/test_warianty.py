"""Narzędzie porównań par gier (balans/warianty.py, B2): wymuszanie decyzji bota, pomiar ze wznawianiem
i statystyki par."""

import pytest

from balans import warianty as wr
from silnik.boty import decyzje_bota
from silnik.dane import dane_domyslne
from silnik.gra import Gra

D = dane_domyslne()
K = wr.Kontekst(rund=4, firm=4)


def test_wariant_bez_zmian_daje_gre_bota():
    fs = wr.firmy(K, 3, list(D.boty["strategie"]))
    g = Gra.nowa("warianty", fs, K.rund, 3, poziomy={n: K.poziom for n, _ in fs})
    for _ in range(K.rund):
        s = g.przelicz(wymus=True)
    czysta = wr.miary(s, K.rund)
    baza = wr.rozegraj(wr.Zadanie(K, 3))
    nic = wr.rozegraj(wr.Zadanie(K, 3, wr.Wariant("nic")))
    for w in (baza, nic):
        w.pop("czas_s")
    assert baza == nic == czysta


def test_wymuszona_decyzja_tylko_gdy_bot_ja_podejmuje():
    w = wr.Wariant("x", decyzje=(("bank", "ING"), ("kampanie", [])), zatrudnienie=(("umowa", "zlecenie"),))
    d = wr._wymus(w, {"bank": "mBank", "zatrudnij": [{"zawod": "kucharz", "umowa": "prace"}]})
    assert d == {"bank": "ING", "zatrudnij": [{"zawod": "kucharz", "umowa": "zlecenie"}]}


def test_wariant_zmienia_wynik_badanej_firmy():
    kat = wr.katalog_wariantow(D)
    assert {"bank:ING", "umowa:zlecenie", "jakosc:3", "lokale:drugi"} <= set(kat)
    baza = wr.rozegraj(wr.Zadanie(K, 3))
    assert wr.rozegraj(wr.Zadanie(K, 3, kat["bank:ING"]))["karta"] != baza["karta"]


def test_nadpisanie_strategii_nie_zmienia_danych_gry():
    st = D.boty["strategie"]["zrownowazony"]
    db = wr._dane_badanej(D, "zrownowazony", "sredni", {"strefy": ["felin"], "jakosc": 3}, {})
    assert db.boty["strategie"]["zrownowazony"]["jakosc"] == 3 and st["jakosc"] != 3
    assert "strefy" not in st
    g = Gra.nowa("strefa", [(wr.BADANA, "zrownowazony"), ("Rywal", "tani")], 4, 5)
    d = decyzje_bota(db, g.stan(0), wr.BADANA, "zrownowazony", 1, g.konfiguracja)
    assert D.lokale[d["lokal"]["id"]]["strefa"] == "felin"


def test_wybor_wariantow_po_przedrostku():
    banki = wr.wybierz_warianty(D, ["bank"])
    assert banki and all(w.nazwa.startswith("bank:") for w in banki)
    assert [w.nazwa for w in wr.wybierz_warianty(D, ["jakosc:3"])] == ["jakosc:3"]
    try:
        wr.wybierz_warianty(D, ["nie_ma"])
    except ValueError as e:
        assert "nie_ma" in str(e)
    else:
        raise AssertionError("nieznany wariant przeszedł")


def test_pomiar_zapisuje_gry_i_wznawia_sie(tmp_path):
    kat = wr.katalog_wariantow(D)
    lista = wr.zadania([K], [1, 2], [kat["bank:ING"], kat["kampanie:brak"]])
    assert wr.mierz(tmp_path, lista) == 6
    assert wr.mierz(tmp_path, lista) == 0                       # wznowienie nie powtarza gier
    tekst = wr.raport(tmp_path)
    assert "bank:ING" in tekst and "kampanie:brak" in tekst and K.klucz() in tekst
    assert len(wr.pary(wr._wczytaj_gry(tmp_path / "gry.csv"))) == 4
    assert (tmp_path / "pary.csv").exists()


def _para(d: float) -> dict:
    return {"d_karta": d, "d_majatek": 100 * d, "pierwszy_plus_baza": 2, "pierwszy_plus_wariant": 3,
            "alarmy_baza": 0, "alarmy_wariant": 1}


def test_ocena_par():
    assert wr.podsumuj([_para(d) for d in (1.0, 1.2, 0.9, 1.1, 0.8)])["ocena"] == "lepszy"
    assert wr.podsumuj([_para(d) for d in (-1.0, -1.2, -0.9, -1.1)])["ocena"] == "gorszy"
    assert wr.podsumuj([_para(d) for d in (1.0, -1.0, 0.5, -0.4)])["ocena"] == "szum"
    s = wr.podsumuj([_para(0.0)] * 3)
    assert s["ocena"] == "= baza" and s["wygrane"] == 0.5
    assert wr.podsumuj([_para(1.0)])["p_karta"] == float("inf")   # jedna para – bez przedziału


@pytest.mark.dane_gry   # poziomy „jak człowiek” są tylko w dane/
def test_badana_jak_czlowiek_wsrod_rywali_innego_poziomu():
    """Z5: pomiar trudności – badana firma „jak człowiek”, rywale na swoim poziomie (Kontekst.rywale)."""
    sami = wr.Kontekst(rund=4, firm=4, poziom="czlowiek_sredni")
    wsrod = wr.Kontekst(rund=4, firm=4, poziom="czlowiek_sredni", rywale="sredni")
    assert wsrod.klucz() == sami.klucz() + "/rywale_sredni"
    assert wr.rozegraj(wr.Zadanie(wsrod, 3))["karta"] != wr.rozegraj(wr.Zadanie(sami, 3))["karta"]
    assert wr.wybierz_warianty(D, [wr.BAZA]) == []
