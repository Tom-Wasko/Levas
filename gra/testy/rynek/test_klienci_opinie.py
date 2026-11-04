"""U24: grupy klientów z koszykiem (silnik/rynek/klienci.py) i opinie klientów o lokalach (silnik/rynek/opinie.py)."""
from __future__ import annotations

import numpy as np
import pytest
from pomocnicze import _gra

from silnik.dane import dane_domyslne
from silnik.model import Lokal
from silnik.rynek import klienci as kl
from silnik.rynek import opinie as op
from silnik.rynek import popyt as pp

dane_gry = pytest.mark.dane_gry
BULKA, BOX, FALAFEL = "kebab_w_bulce", "kebab_box", "falafel"


def _oferta(dane, strefa, danie=BULKA, cena_proc=1.0, jakosc=(2, 2, 2)):
    cena = dane.uslugi[danie]["cena_preferowana"] * dane.mapa["popyt"]["strefy"][strefa]["cena"] * cena_proc
    return {"strefa": strefa, "cena": cena, "jakosc": jakosc}


@dane_gry
def test_wegetarianie_przechodza_na_falafel():
    dane = dane_domyslne()
    g = kl.ustawienia(dane)["grupy"]["studenci"]
    k = kl.koszyk_grupy(dane, "studenci")
    assert k[BULKA] == pytest.approx(g["koszyk"][BULKA] * (1 - g["wegetarianie"]))
    assert k[FALAFEL] > g["koszyk"][FALAFEL]
    roczny = {u: dane.uslugi[u]["popyt_roczny"] for u in k}
    assert sum(roczny[u] * k[u] for u in k) == pytest.approx(sum(roczny[u] * g["koszyk"][u] for u in k))


@dane_gry
def test_koszyk_przesuwa_popyt_miedzy_strefami_a_miasto_bez_zmian(monkeypatch):
    dane = dane_domyslne()
    z_grupami = pp.pule(dane, 5)
    monkeypatch.setattr(kl, "ustawienia", lambda d: None)
    bez = pp.pule(dane, 5)
    for u in dane.uslugi:
        miasto = sum(float(z_grupami[z][u].sum()) for z in bez)
        assert miasto == pytest.approx(sum(float(bez[z][u].sum()) for z in bez), rel=0.03)   # kalendarz stref – drobne różnice
    assert any(abs(float(z_grupami[z][u].sum()) / float(bez[z][u].sum()) - 1) > 0.05 for z in bez for u in dane.uslugi)


@dane_gry
def test_wrazliwosc_grup_srednio_jak_strefa_i_udzialy_sumuja_sie_do_1():
    dane = dane_domyslne()
    k = kl.ustawienia(dane)
    dni = pp.dni_rundy(dane, 5)
    u = kl.udzialy(dane, dni)
    for z, udz in k["strefy"].items():
        c = kl.wrazliwosc(dane, z)
        assert sum(s * c[g] for g, s in udz.items()) == pytest.approx(1.0)
        for d, (grupy, m) in u[z].items():
            assert grupy[-1] == k["wydarzenia"]
            assert np.allclose(m.sum(axis=0), 1.0), (z, d)
    sklad = kl.sklad_stref(dane, dni)
    assert sum(sklad["akademickie"].values()) == pytest.approx(1.0, abs=0.01)
    assert sklad["akademickie"]["studenci"] > sklad["stare_miasto"].get("studenci", 0)


@dane_gry
def test_drogi_lokal_traci_najpierw_oszczedne_grupy():
    dane = dane_domyslne()
    grupy = kl.udzialy(dane, pp.dni_rundy(dane, 5))
    pod = pp.podzial(dane, pp.pule(dane, 5), {BULKA: {("T", "x"): _oferta(dane, "akademickie", cena_proc=0.8),
                                                      ("D", "x"): _oferta(dane, "akademickie", cena_proc=1.3)}}, grupy)
    tani, drogi = pod[("T", "x")][BULKA]["grupy"], pod[("D", "x")][BULKA]["grupy"]
    assert sum(tani.values()) == pytest.approx(pod[("T", "x")][BULKA]["dni"].sum())
    # studenci (wrażliwi na cenę) wolą tani lokal bardziej niż turyści
    assert tani["studenci"] / drogi["studenci"] > tani["turysci"] / drogi["turysci"]


@dane_gry
def test_lokal_bez_dania_sprzedaje_zamiennik(monkeypatch):
    dane = dane_domyslne()
    pr, grupy = pp.pule(dane, 5), kl.udzialy(dane, pp.dni_rundy(dane, 5))
    oferty = {BULKA: {("A", "x"): _oferta(dane, "centrum")}}
    z_zam = pp.podzial(dane, pr, oferty, grupy)[("A", "x")]
    monkeypatch.setattr(kl, "zamienniki", lambda d: ({}, 0.0))
    bez_zam = pp.podzial(dane, pr, oferty, grupy)[("A", "x")]
    assert set(z_zam) == {BULKA}   # sprzedaż zamiennika liczy się jako bułka
    assert z_zam[BULKA]["dni"].sum() > 1.1 * bez_zam[BULKA]["dni"].sum()


def _wynik(obsluzeni=100, kolejka=0, brak=0, reklamacje=0, grupy=None):
    return {"popyt": obsluzeni + kolejka + brak, "grupy": grupy or {"studenci": obsluzeni},
            "obsluga": {"obsluzeni": {BULKA: obsluzeni}, "kolejka": kolejka, "brak": brak, "reklamacje": reklamacje}}


@dane_gry
def test_ocena_tygodnia_z_przezyc_klientow():
    dane = dane_domyslne()
    lok = next(i for i, x in dane.lokale.items() if x["strefa"] == "centrum")
    o = {BULKA: _oferta(dane, "centrum")}

    def ocena(wynik=None, **oferta):
        return op.ocena_tygodnia(dane, lok, wynik or _wynik(), {BULKA: {**o[BULKA], **oferta}})[0]

    baza = ocena()
    assert ocena(jakosc=(3, 3, 3)) > baza > ocena(jakosc=(1, 1, 1))
    assert ocena(cena=o[BULKA]["cena"] * 0.8) > baza > ocena(cena=o[BULKA]["cena"] * 1.3)
    assert ocena(_wynik(kolejka=40)) < baza
    assert ocena(_wynik(brak=40)) < baza
    assert ocena(_wynik(reklamacje=10)) < baza
    # biurowi bardziej nie znoszą czekania niż imprezowicze
    assert ocena(_wynik(kolejka=40, grupy={"biurowi": 100})) < ocena(_wynik(kolejka=40, grupy={"imprezowicze": 100}))
    assert op.ocena_tygodnia(dane, lok, _wynik(obsluzeni=0), o) is None


@dane_gry
def test_mnoznik_oceny_rosnie_z_ocena_i_zaufaniem():
    dane = dane_domyslne()
    u = op.ustawienia(dane)
    nowy = Lokal(id="x", forma="najem", od_rundy=1, dziala_od=2)
    assert op.mnoznik(dane, nowy) == 1.0
    sredni = nowy.model_copy(update={"ocena": u["odniesienie"], "waga_opinii": 50})
    assert op.mnoznik(dane, sredni) == pytest.approx(1.0)
    dobry = nowy.model_copy(update={"ocena": 4.5, "waga_opinii": 5})
    pewny = dobry.model_copy(update={"waga_opinii": 100})
    assert 1 < op.mnoznik(dane, dobry) < op.mnoznik(dane, pewny)
    assert op.mnoznik(dane, nowy.model_copy(update={"ocena": 1.5, "waga_opinii": 100})) < 1


def _opinie_gry():
    g = _gra(("Tani", "tani"), ("Premium", "premium"), rund=5)
    for _ in range(4):
        s = g.przelicz(wymus=True)
    return s


@dane_gry
def test_opinie_w_grze_deterministyczne_i_publiczne():
    s = _opinie_gry()
    assert s.rynek[4]["opinie"] == _opinie_gry().rynek[4]["opinie"]
    pub = s.rynek[4]["opinie"]
    assert pub, "lokale z opiniami widać na mapie"
    for o in pub.values():
        assert 1 <= o["ocena"] <= 5 and o["liczba"] > 0
        assert o["komentarze"] and all(k["tekst"] and k["podpis"] and 1 <= k["gwiazdki"] <= 5 for k in o["komentarze"])
    # liczba opinii rośnie ze sprzedażą
    assert sum(o["liczba"] for o in pub.values()) > sum(o["liczba"] for o in s.rynek[3]["opinie"].values())
    w = s.wyniki[4]["Premium"]["opinie"]
    assert all(set(x["powody"]) == {"jakosc", "cena", "kolejka", "brak", "reklamacje", "wyposazenie"} for x in w.values())


def test_dane_zamrozone_bez_grup_i_opinii():
    """Bez klienci.yaml (zamrożona kopia testów) popyt jak przed U24: jedna grupa, mnożnik karty zadowolenia."""
    dane = dane_domyslne()
    assert kl.ustawienia(dane) is None and op.ustawienia(dane) is None
    assert kl.mnozniki_koszyka(dane) == {} and kl.udzialy(dane, []) is None
    lok = Lokal(id="x", forma="najem", od_rundy=1, dziala_od=2, ocena=5.0, waga_opinii=100)
    assert pp.zadowolenie_lokalu(dane, lok, 0.93) == 0.93
