"""Tryby kredytu odnawialnego."""

from silnik import Gra


def _rachunek(tryb):
    # kapitał mniejszy niż kaucja i pierwsze opłaty za lokal – brakującą kwotę pokrywa kredyt odnawialny
    g = Gra.nowa("t", [("A", None)], 3, 1, kredyt_odnawialny=tryb, kapital_startowy=1000)
    g.ustaw_decyzje("A", {"lokal": {"id": "centrum_3", "forma": "najem"}})
    return g.przelicz(wymus=True).wyniki[1]["A"]["rachunek"]


def test_tryby_kredytu_odnawialnego():
    uruch = lambda rach: [o for o in rach if o["opis"] == "Uruchomienie kredytu odnawialnego"]
    jedn, biez = _rachunek("jednoczesnie"), _rachunek("na_biezaco")
    assert len(uruch(jedn)) == 1 and uruch(jedn)[0] is jedn[-1]    # tylko niedobór na koniec rundy
    assert uruch(biez) and uruch(biez)[0] is not biez[-1]          # na bieżąco: od razu po wydatkach z decyzji
