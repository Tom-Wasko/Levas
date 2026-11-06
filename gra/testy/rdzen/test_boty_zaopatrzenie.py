"""B8: boty potrafią wybrać każdą opcję zaopatrzenia – gwiazdki składników niezależnie od sprzętu
(`jakosc_zasobow`), zapas w zamówieniach (`zapas_zasobow`) i dostawców (`dostawcy`, `dyskonty`,
`auto_dostawy`); pomiar w balans/warianty.py."""
import copy

import pytest

from silnik import boty
from silnik.gra import Gra

pytestmark = pytest.mark.dane_gry


def _dane_strategii(dane, strategia: dict):
    """Dane gry ze strategią zrównoważoną nadpisaną ustawieniami `strategia`."""
    dane = copy.copy(dane)
    st = dane.boty["strategie"]
    dane.boty = {**dane.boty, "strategie": {**st, "zrownowazony": {**st["zrownowazony"], **strategia}}}
    return dane


def _zamowienia(strategia: dict, rund: int = 3) -> list[dict]:
    """Zamówienia firmy A (zrównoważony z nadpisaną strategią) w rundzie `rund` tej samej gry."""
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5)
    for _ in range(rund - 1):
        g.przelicz(wymus=True)
    return boty.decyzje_bota(_dane_strategii(g.dane, strategia), g.stan(rund - 1), "A", "zrownowazony", rund, g.konfiguracja)["zamowienia"]


def _ilosc(zamowienia: list[dict]) -> float:
    return sum(z["ilosc"] for z in zamowienia)


def test_bot_zamawia_skladniki_w_gwiazdkach_z_jakosc_zasobow():
    baza = _zamowienia({})
    assert baza and {z["jakosc"] for z in baza} == {2}   # bez ustawienia – jak jakość strategii
    wyzsze = _zamowienia({"jakosc_zasobow": 3})
    assert wyzsze and all(z["jakosc"] >= 2 for z in wyzsze) and any(z["jakosc"] == 3 for z in wyzsze)
    assert {z["jakosc"] for z in _zamowienia({"jakosc_zasobow": 1})} == {1}


def test_bot_zamawia_tylko_u_wybranych_dostawcow():
    baza = _zamowienia({})
    assert len({z["dostawca"] for z in baza}) > 1
    makro = _zamowienia({"dostawcy": ["Makro"]})
    assert makro and {z["dostawca"] for z in makro} == {"Makro"}


def test_wiekszy_zapas_to_wieksze_zamowienie():
    assert _ilosc(_zamowienia({"zapas_zasobow": 1.3})) > _ilosc(_zamowienia({"zapas_zasobow": 1.0}))


def test_bot_z_dyskontami_kupuje_w_jednym_dyskoncie_do_limitu():
    """B8: bot domyślnie pomija dyskonty (odbiór osobisty); z `dyskonty` kupuje w jednym – tam, gdzie oszczędza
    najwięcej – codziennie najwyżej limit opakowań składnika, resztę u dostawców z dowozem."""
    from silnik.kuchnia.dostawcy import info
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5)
    dane = g.dane
    baza = _zamowienia({})
    assert not any(info(dane, z["dostawca"])["odbior_osobisty"] for z in baza)
    zam = _zamowienia({"dyskonty": True})
    dysk = [z for z in zam if info(dane, z["dostawca"])["odbior_osobisty"]]
    assert dysk and len({z["dostawca"] for z in dysk}) == 1
    limit = info(dane, dysk[0]["dostawca"])["limit_opakowan"]
    assert all(z["ilosc"] <= limit for z in dysk)
    assert len({(z["zasob"], z["dzien"]) for z in dysk}) == len(dysk)   # jedna pozycja składnika dziennie
    # dyskont zastępuje część dowozu, nie dokłada towaru ponad potrzebę (± zaokrąglenie opakowań)
    for zasob in {z["zasob"] for z in dysk}:
        przed = sum(z["ilosc"] for z in baza if z["zasob"] == zasob)
        po = sum(z["ilosc"] for z in zam if z["zasob"] == zasob)
        assert przed - 1 <= po <= przed + 7


def test_bot_z_auto_dostawami_nie_zamawia_do_lokalu_glownego():
    """B8: z `auto_dostawy` lokal główny bota jest na auto-dostawach (Z4): pozycje u auto-dostawcy zamiast
    zamówień u dostawców; przed rundą auto-dostawcy (od_rundy) – zamówienia jak zwykle."""
    from silnik.kuchnia import auto_dostawca as ad
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5)
    od = ad.zasady(g.dane)["od_rundy"]
    for r in range(1, od + 2):
        d = boty.decyzje_bota(_dane_strategii(g.dane, {"auto_dostawy": True}), g.stan(r - 1), "A", "zrownowazony",
                              r, g.konfiguracja)
        if r >= od:
            assert d["auto_dostawy"]["pozycje"] and not d.get("zamowienia")
            assert all(p["ilosc"] > 0 for p in d["auto_dostawy"]["pozycje"])
        g.ustaw_decyzje("A", d)
        s = g.przelicz(wymus=True)
    assert s.wyniki[od + 1]["A"]["kpir"]["przychody"] > 0
