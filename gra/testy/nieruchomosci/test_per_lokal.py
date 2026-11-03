"""Lokal jako osobna jednostka (Z2 przebudowy 2.11.2026): menu i ceny, magazyn, wyposażenie osobno w każdym lokalu,
przewozy towaru między lokalami, stary zapis (pola lokalu None) i podział zamówień botów."""

import copy
from datetime import date, timedelta

import pytest
from pomocnicze import _gra

from silnik.dane import KUCHNIA, dane_domyslne
from silnik.decyzje import lista_bledow, zastosuj
from silnik.ksiegowosc import rozliczenie as rz
from silnik.ksiegowosc.finanse import Ksiega, Rachunek
from silnik.kuchnia import swiezosc as sw
from silnik.kuchnia.dostawcy import ceny_rundy
from silnik.ludzie import czas_wlasciciela as cw
from silnik.model import Cena, Firma, Lokal, Stanowisko
from silnik.nieruchomosci import per_lokal as pl
from silnik.rynek import popyt as pp

PN = date(2026, 10, 12)
DRUGI = "centrum_1"


def _partia(dane, zasob, ilosc, dostawa=PN, lokal=None, cena=10.0):
    return sw.nowa_partia(dane, zasob, 2, ilosc, cena, dostawa, "Makro", 2, lokal=lokal)


@pytest.fixture(scope="module")
def gra_bota():
    g = _gra(("Tani", "tani"), ("Zrown", "zrownowazony"), rund=4)
    for _ in range(3):
        s = g.przelicz(wymus=True)
    return g, s


def _dwa_lokale(gra_bota):
    """Firma bota z drugim działającym lokalem – kopia stanowisk pierwszego (ci sami ludzie, ten sam sprzęt)."""
    g, s = gra_bota
    f = copy.deepcopy(s.firmy["Zrown"])
    r = s.runda
    pierwszy = f.lokale[0].id
    f.lokale.append(Lokal(id=DRUGI, forma="najem", od_rundy=r - 1, dziala_od=r))
    for st in [x for x in f.stanowiska if x.lokal == pierwszy]:
        f.stanowiska.append(st.model_copy(update={"nr": f.nowy_nr(st.typ), "lokal": DRUGI}))
    return g.dane, f, r, pierwszy


def test_stary_zapis_utrwal_i_synchronizuj():
    """Pola lokali None: menu i ceny – kopia firmy w każdym lokalu, wyposażenie i partie – w pierwszym lokalu."""
    dane = dane_domyslne()
    f = Firma(nazwa="A", oferta={"frytki": 10}, ceny={"frytki": Cena(cena=9)}, wyposazenie=["Stojak na rowery"],
              lokale=[Lokal(id="politechnika_1", forma="najem", od_rundy=1, dziala_od=2),
                      Lokal(id=DRUGI, forma="najem", od_rundy=1, dziala_od=2)])
    f.partie = [_partia(dane, "Bułka", 3)]
    a, b = f.lokale
    assert pl.lista(f, a, "wyposazenie") == ["Stojak na rowery"] and pl.lista(f, b, "wyposazenie") == []
    pl.utrwal(f)
    assert a.menu == b.menu == {"frytki": 10} and b.ceny["frytki"].cena == 9 and b.ceny["frytki"] is not f.ceny["frytki"]
    assert (a.wyposazenie, b.wyposazenie, b.udogodnienia) == (["Stojak na rowery"], [], [])
    assert f.partie[0].lokal == "politechnika_1"
    b.menu, b.wyposazenie = {"frytki": 4, "napoj": 6}, ["Stojak na rowery"]
    b.ceny["napoj"] = Cena(cena=5)
    pl.synchronizuj(f)
    assert f.oferta == {"frytki": 14, "napoj": 6} and f.ceny["napoj"].cena == 5
    assert f.wyposazenie == ["Stojak na rowery", "Stojak na rowery"]   # każdy lokal ma swój stojak (utrzymanie × 2)
    # lokal dokupiony do podzielonej firmy: dania firmy bez prognozy, bez wyposażenia
    f.lokale.append(Lokal(id="centrum_2", forma="najem", od_rundy=2, dziala_od=3))
    pl.utrwal(f)
    assert f.lokale[2].menu == {"frytki": 0, "napoj": 0} and f.lokale[2].wyposazenie == []


def test_magazyn_lokalu_widok_i_scal():
    dane = dane_domyslne()
    f = Firma(nazwa="A", lokale=[Lokal(id="politechnika_1", forma="najem", od_rundy=1, dziala_od=2),
                                 Lokal(id=DRUGI, forma="najem", od_rundy=1, dziala_od=2)],
              stanowiska=[Stanowisko(nr=1, typ=KUCHNIA, lokal="politechnika_1", sprzet={"Szafa chłodnicza": 1}),
                          Stanowisko(nr=2, typ=KUCHNIA, lokal=DRUGI)])
    f.partie = [_partia(dane, "Bułka", 3, lokal="politechnika_1"), _partia(dane, "Bułka", 2, lokal=DRUGI)]
    sw.uzgodnij(f)
    assert sw.ilosc(f.magazyn, "Bułka") == pytest.approx(5)
    w = pl.widoki(f)
    assert sw.ilosc(w["politechnika_1"].magazyn, "Bułka") == pytest.approx(3)
    assert sw.ilosc(w[DRUGI].magazyn, "Bułka") == pytest.approx(2)
    # chłodnia – ze sprzętu stanowisk lokalu
    assert sw.pojemnosc(dane, w["politechnika_1"])["chlodnia"] == pytest.approx(600)
    assert sw.pojemnosc(dane, w[DRUGI])["chlodnia"] == 0
    sw.zuzyj(dane, w[DRUGI], {"Bułka": 2}, PN.isoformat())   # zużycie w drugim lokalu nie rusza pierwszego
    w[DRUGI].partie.append(_partia(dane, "Sos", 1, lokal=None))
    pl.scal(f, w)
    assert sw.ilosc(f.magazyn, "Bułka") == pytest.approx(3) and sw.ilosc(f.magazyn, "Sos") == pytest.approx(1)
    assert {p.zasob: p.lokal for p in f.partie if p.ilosc > 0} == {"Bułka": "politechnika_1", "Sos": DRUGI}
    # przegląd magazynu: osobno dla lokali
    pod = sw.podsumowanie(dane, f, 2)
    assert set(pod["lokale"]) == {"politechnika_1", DRUGI}


def test_przewozy_czas_koszt_i_termin():
    dane = dane_domyslne()
    zas = pl.zasady_przewozu(dane)
    assert zas["czas_wlasciciela"] > 0 and zas["koszt_kursu"] > 0
    f = Firma(nazwa="A", lokale=[Lokal(id="politechnika_1", forma="najem", od_rundy=1, dziala_od=2),
                                 Lokal(id=DRUGI, forma="najem", od_rundy=1, dziala_od=2)])
    f.partie = [_partia(dane, "Mięso kebab", 4, lokal="politechnika_1"),
                _partia(dane, "Mięso kebab", 2, dostawa=date(2026, 10, 10), lokal="politechnika_1")]
    zadane = [{"z": "politechnika_1", "do": DRUGI, "zasob": "Mięso kebab", "ilosc": 3, "dzien": 1},
              {"z": "politechnika_1", "do": DRUGI, "zasob": "Bułka", "ilosc": 1, "dzien": 1},   # ten sam kurs
              {"z": DRUGI, "do": DRUGI, "zasob": "Bułka", "ilosc": 1}]                        # błędny
    info, czas = {}, cw.nowy(dane)
    wolne = czas.wolne
    przew = pl.przewozy(dane, f, zadane, 2, czas, info)
    assert len(przew) == 2 and [x.get("koszt") for x in przew] == [zas["koszt_kursu"], None]   # jeden kurs
    assert len(info["uwagi_przewozow"]) == 1
    assert czas.wolne == pytest.approx(wolne - zas["czas_wlasciciela"])
    assert pl.przewozy(dane, f, zadane[:1], zas["od_rundy"] - 1, cw.nowy(dane), {}) == []   # za wcześnie
    w = pl.widoki(f)
    wyk = pl.wykonaj_przewozy(dane, f, w, przew, 1, "2026-10-13")
    assert [x["przewiezione"] for x in wyk] == [3, 0]   # bułki nie ma w magazynie
    nowe = list(w[DRUGI].partie)
    assert sum(p.ilosc for p in nowe) == pytest.approx(3) and {p.dostawa for p in nowe} == {"2026-10-13"}
    stara = min(f.partie, key=lambda p: p.dostawa)   # najpierw najkrótszy termin (FIFO), termin krótszy o dzień
    przewieziona = next(p for p in nowe if p.ilosc == pytest.approx(2))
    skr = (date.fromisoformat(stara.termin) - timedelta(days=zas["skrocenie_terminu_dni"])).isoformat()
    assert przewieziona.termin == max("2026-10-13", skr)
    pl.scal(f, w)
    assert sum(p.ilosc for p in f.partie if p.lokal == DRUGI) == pytest.approx(3)
    assert sum(p.ilosc for p in f.partie if p.lokal == "politechnika_1") == pytest.approx(3)
    assert sum(p.wartosc for p in f.partie) == pytest.approx(60)   # wartość jedzie z towarem


def test_podzial_zamowien_botow():
    z = [{"zasob": "Bułka", "ilosc": 5}, {"zasob": "Sos", "ilosc": 1}]
    wynik = pl.podziel_zamowienia(z, {"a": 3.0, "b": 1.0, "c": 0.0})
    assert [(x["zasob"], x["lokal"], x["ilosc"]) for x in wynik] == [("Bułka", "a", 4), ("Bułka", "b", 1), ("Sos", "a", 1)]
    assert pl.podziel_zamowienia(z, {"a": 1.0}) == [{**x, "lokal": "a"} for x in z]


def test_oferty_lokali_ceny_menu_i_wyposazenie(gra_bota):
    dane, f, r, pierwszy = _dwa_lokale(gra_bota)
    pl.utrwal(f)
    u, v = list(f.oferta)[:2]
    drugi = pl.lokal(f, DRUGI)
    drugi.ceny[u] = Cena(cena=f.ceny[u].cena + 1)
    del drugi.menu[v]
    of = pp.oferty_lokali(dane, f, r, {"reklama": 0.0, "mnoznik_firmy": 1.0, "zadowolenie": 1.0, "reklama_strefy": {}})
    assert of[DRUGI][u]["cena"] == pytest.approx(of[pierwszy][u]["cena"] + 1)
    assert v in of[pierwszy] and v not in of[DRUGI]
    assert of[pierwszy][u]["wyposazenie"] >= of[DRUGI][u]["wyposazenie"]   # wyposażenie bota – w pierwszym lokalu


def test_decyzje_w_lokalu(gra_bota):
    dane, f, r, pierwszy = _dwa_lokale(gra_bota)
    u, v = list(f.oferta)[:2]
    ud = "Stojak na rowery"   # udogodnienie bota (w pierwszym lokalu) – drugi lokal kupuje swoje
    d = {"oferta": {u: 10, v: 6}, "sprzedaz": {u: {"cena": f.ceny[u].cena}, v: {"cena": f.ceny[v].cena}},
         "w_lokalu": {DRUGI: {"oferta": {u: 4}, "sprzedaz": {u: {"cena": f.ceny[u].cena + 1}},
                              "udogodnienia_kup": [ud]}},
         "zamowienia": [{"dostawca": "Makro", "zasob": "Bułka", "jakosc": 2, "ilosc": 5, "dzien": 0, "lokal": DRUGI}]}
    ceny_d = ceny_rundy(dane, 1, r, "dane")
    info = zastosuj(dane, f, d, r, [], ceny_d, Ksiega(vat=rz.reguly_vat(dane)), Rachunek())
    a, b = f.lokale
    assert a.menu == {u: 5, v: 3} and b.menu == {u: 4}          # prognoza firmy po równo, w lokalu – jak podano
    assert f.oferta == {u: 9, v: 3}
    assert b.ceny[u].cena == pytest.approx(a.ceny[u].cena + 1) and v not in b.ceny
    assert ud in a.udogodnienia and b.udogodnienia == [ud] and f.udogodnienia.count(ud) == 2
    zam = info["zakupy_zasobow"].get("Makro") or []
    if zam:   # dostawa doszła (zasady dostaw) – partia w drugim lokalu
        assert any(p.lokal == DRUGI and p.zasob == "Bułka" and p.runda == r for p in f.partie)
    # lista błędów: osobno dla lokali, z nazwą lokalu
    lb = lista_bledow(dane, f, d, r, list(f.oferta), lokal={}, info=info)
    nazwa = dane.lokale[DRUGI]["nazwa"]
    assert all(isinstance(x["tekst"], str) for x in lb)
    assert not any(x["tekst"].startswith(nazwa) and dane.uslugi[v]["nazwa"] in x["tekst"] for x in lb)   # v nie ma w menu
    # U1: udogodnienie poniżej progu amortyzacji – koszt tej rundy (bez VAT) i ostrzeżenie o karcie
    cena = dane.pozycje("udogodnienia")[ud]["cena"]
    assert 0 < info["inwestycje_w_koszty"] < cena and any("idą w koszty" in x["tekst"] for x in lb)
