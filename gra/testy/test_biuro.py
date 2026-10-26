"""Biura rachunkowe i samodzielna księgowość (F3a.13, silnik/biuro.py)."""
import pytest

from api.prezentacja import widok
from silnik import biuro as bo
from silnik.boty import decyzje_bota
from silnik.dane import dane_domyslne
from silnik.gra import Gra
from silnik.runda import przelicz_runde


@pytest.fixture(scope="module")
def dane():
    return dane_domyslne()


def _gra(rund=8, ziarno=3):
    return Gra.nowa("biuro", [("H", None), ("B", "zrownowazony")], rund, ziarno, lokale=True)


def _runda(g, biuro="samodzielnie", ksiegowosc=None, **zmiany):
    d = decyzje_bota(g.dane, g.stan(), "H", "zrownowazony", g.runda, g.konfiguracja)
    d["biuro"] = biuro
    if ksiegowosc is not None:
        d["ksiegowosc"] = ksiegowosc
    d.update(zmiany)
    g.ustaw_decyzje("H", d)
    g.przelicz(wymus=True)
    return g.stan().wyniki[g.runda - 1]["H"]


def _poprawna(dk, **zmiany):
    dek = {**dk["poprawne"], **zmiany}
    return {"zapisy": {x["id"]: dict(x["poprawne"]) for x in dk["dokumenty"]}, "deklaracja": dek}


def _do_deklaracji(g, rund=3):
    """Kilka rund samodzielnie z poprawnymi deklaracjami – zostaje deklaracja z dokumentami do złożenia."""
    for _ in range(rund):
        dk = g.stan().firmy["H"].deklaracja
        _runda(g, ksiegowosc=_poprawna(dk) if dk else None)
    dk = g.stan().firmy["H"].deklaracja
    assert dk and dk["dokumenty"]
    return dk


def test_oplata_ryczalt_limit_minimum_i_kadry(dane):
    b = bo.biura(dane)
    jks = bo.oplata(dane, b["jks"], 30, 5, 1)     # limit 80/mies. → 18/rundę; kadry: 4 w cenie (najpierw etat)
    assert jks["limit"] == 18 and jks["ponad"] == 12
    assert jks["ksiegowanie"] == pytest.approx(dane.na_runde(690) + 12 * 4.92, abs=0.01)
    assert jks["kadry"] == pytest.approx(dane.na_runde(45 + 25), abs=0.01) and jks["osoby_platne"] == 2
    e = bo.oplata(dane, b["eksiegi"], 5, 0, 0)    # 5 × 3,69 < minimum 123/mies.
    assert e["ksiegowanie"] == dane.na_runde(123)
    dk = bo.oplata(dane, b["debet_kredyt"], 500, 0, 0)   # ryczałt bez limitu
    assert dk["ponad"] == 0 and dk["ksiegowanie"] == dane.na_runde(984)


def test_biuro_z_mapy_nalicza_koszt_i_rozlicza_od_razu():
    g = _gra()
    for _ in range(3):
        w = _runda(g, biuro="trybunal")
    assert w["biuro"]["nazwa"] == "Księgowość Pod Trybunałem" and w["biuro"]["razem"] > 0
    assert any(p["opis"].startswith("Koszt biura rachunkowego") for p in w["kpir"]["pozycje"])
    assert w["rozliczenie"]["zaplacone"] and not w["samodzielnie"] and w["uzgodnienie"]["roznica"] == 0


def test_blad_biura_bez_oc_kosztuje_mandat(dane, monkeypatch):
    oferty = bo.biura(dane)
    monkeypatch.setitem(oferty["eksiegi"], "ryzyko_bledu", 1.0)
    monkeypatch.setattr(bo, "biura", lambda _d: oferty)
    g = _gra()
    w = _runda(g, biuro="eksiegi")
    assert w["biuro"]["blad"]["kara"] == 200 and not w["biuro"]["blad"]["oc"]
    assert any(o["opis"].startswith("Mandat karny") for o in w["rachunek"]) and w["uzgodnienie"]["roznica"] == 0


def test_poprawna_deklaracja_bez_kary_i_kasa_sie_zgadza():
    g = _gra()
    dk = _do_deklaracji(g)
    w = _runda(g, ksiegowosc=_poprawna(dk))
    k = w["ksiegowosc"]
    assert k["tryb"] == "deklaracja" and k["kara"] == 0 and all(not p["blad"] for p in k["pozycje"])
    assert k["zapisy"]["dobre"] == k["zapisy"]["liczba"] == len(dk["dokumenty"])
    assert w["uzgodnienie"]["roznica"] == 0 and w["uzgodnienie"]["roznica_kpir"] == 0


def test_bledna_deklaracja_korekta_i_mandat_bledny_zapis_opisany():
    g = _gra()
    dk = _do_deklaracji(g)
    ks = _poprawna(dk, vat=dk["poprawne"]["vat"] + 50)
    sprzedaz = next(x for x in dk["dokumenty"] if x["poprawne"]["kolumna"] == "przychod")
    ks["zapisy"][sprzedaz["id"]] = {"kolumna": "towary", "stawka": 0.23}
    w = _runda(g, ksiegowosc=ks)
    k = w["ksiegowosc"]
    vat = next(p for p in k["pozycje"] if p["pole"] == "vat")
    assert vat["blad"] and vat["korekta"] == -50 and k["kara"] == 200
    zly = next(x for x in k["zapisy"]["dokumenty"] if x["id"] == sprzedaz["id"])
    assert not zly["ok"] and "przychód ze sprzedaży" in zly["bledy"][0].lower() and any("stawka VAT" in b for b in zly["bledy"])
    assert any("mandat 200" in b["tekst"] for b in w["lista_bledow"])
    assert w["uzgodnienie"]["roznica"] == 0


def test_brak_deklaracji_rozliczenie_z_urzedu_i_mandat():
    g = _gra()
    dk = _do_deklaracji(g)
    k = _runda(g)["ksiegowosc"]
    assert k["tryb"] == "brak" and k["kara"] == 500
    assert [p["zadeklarowano"] for p in k["pozycje"]] == [dk["poprawne"][p] for p in ("vat", "pit", "zdrowotna")]


def test_zmiana_na_biuro_skladka_deklaracje_bez_kary():
    g = _gra()
    _do_deklaracji(g)
    w = _runda(g, biuro="jks")
    assert w["ksiegowosc"]["tryb"] == "biuro" and w["ksiegowosc"]["kara"] == 0 and not w["samodzielnie"]
    assert g.stan().firmy["H"].deklaracja is None


def test_ostatnia_runda_rozlicza_urzad():
    g = _gra(rund=3)
    for _ in range(3):
        dk = g.stan().firmy["H"].deklaracja
        w = _runda(g, ksiegowosc=_poprawna(dk) if dk else None)
    assert g.stan().firmy["H"].deklaracja is None and w["rozliczenie"]["zaplacone"]


def test_widok_ukrywa_poprawne_odpowiedzi():
    g = _gra()
    _do_deklaracji(g)
    v = widok(g, "H")
    K = v["ksiegowosc"]
    assert K["ukryte"] and K["deklaracja"]["dokumenty"]
    assert all("poprawne" not in x and "vat" not in x for x in K["deklaracja"]["dokumenty"])
    assert v["wyniki"]["kpir"]["ukryte"] and v["wyniki"]["rozliczenie"] is None and v["wyniki"]["vat"] is None
    assert v["dashboard"]["dochod_netto"] is None and v["historia"][-1]["dochod_netto"] is None
    assert v["podatki"]["stan_przed_deklaracja"]
    assert any(b["zakladka"] == "finanse_biuro" for b in v["lista_bledow"])   # niezłożona deklaracja


def test_podglad_nie_sprawdza_deklaracji():
    g = _gra()
    _do_deklaracji(g)
    d = {"H": decyzje_bota(g.dane, g.stan(), "H", "zrownowazony", g.runda, g.konfiguracja),
         "B": decyzje_bota(g.dane, g.stan(), "B", "zrownowazony", g.runda, g.konfiguracja)}
    d["H"]["biuro"] = "samodzielnie"
    s = przelicz_runde(g.dane, g.stan(), d, g.konfiguracja, podglad=True)
    assert s.wyniki[g.runda]["H"]["ksiegowosc"] == {"za_runde": g.runda - 1, "tryb": "podglad"}
    w = bo.ukryj(s.wyniki[g.runda]["H"], podglad=True)
    assert w["kpir"]["dochod_netto"] is None and w["kpir"]["przychody"] is not None and w["rozliczenie"] is None
