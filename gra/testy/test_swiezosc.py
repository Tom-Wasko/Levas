"""Menu i świeżość (F3a.5): partie z terminem, FIFO, kosz, pojemność chłodni, zamienniki, wyłączanie dań, gra, dane."""

from datetime import date

import pytest
from test_dane import _kopia, _zmien
from test_lokale import _gra, _lokal, _runda

from silnik import menu
from silnik import popyt as pp
from silnik import swiezosc as sw
from silnik.dane import KUCHNIA, dane_domyslne, sprawdz
from silnik.model import Firma, Stanowisko
from silnik.operacje import _zuzyj

PN, WT, SR = date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14)
DOSTAWCA = "Makro"


def _partia(dane, zasob, ilosc, dostawa, jakosc=2, cena=10.0, runda=2):
    return sw.nowa_partia(dane, zasob, jakosc, ilosc, cena, dostawa, DOSTAWCA, runda)


def test_termin_fifo_i_kosz():
    dane = dane_domyslne()
    f = Firma(nazwa="A")
    stara, nowa = _partia(dane, "Bułka", 2, PN), _partia(dane, "Bułka", 1, WT)
    assert (stara.termin, nowa.termin) == ("2026-10-13", "2026-10-14")   # bułka z poniedziałku – do wtorku
    f.partie = [nowa, stara]
    sw.przyjmij(dane, f, PN.isoformat())
    assert sw.ilosc(f.magazyn, "Bułka") == pytest.approx(2)               # wtorkowej dostawy jeszcze nie ma
    sw.przyjmij(dane, f, WT.isoformat())
    zuzyte = sw.zuzyj(dane, f, {"Bułka": 1.5}, WT.isoformat())
    assert zuzyte["Bułka"]["ilosc"] == pytest.approx(1.5) and zuzyte["Bułka"]["wartosc"] == pytest.approx(15)
    assert stara.ilosc == pytest.approx(0.5) and nowa.ilosc == pytest.approx(1)   # najpierw krótszy termin
    straty = sw.wyrzuc(f, WT.isoformat())
    assert [(s["zasob"], s["ilosc"], s["powod"], s["wartosc"]) for s in straty] == [("Bułka", 0.5, "termin", 5.0)]
    assert sw.ilosc(f.magazyn, "Bułka") == pytest.approx(1) and f.partie == [nowa]


def test_pojemnosc_chlodni():
    dane = dane_domyslne()
    f = Firma(nazwa="A", stanowiska=[Stanowisko(nr=1, typ=KUCHNIA, sprzet={"Szafa chłodnicza": 1})])
    assert sw.pojemnosc(dane, f) == {"chlodnia": 600.0, "zamrazarka": 0.0}
    f.partie = [_partia(dane, "Mięso kebab", 50, PN), _partia(dane, "Frytki mrożone", 1, PN), _partia(dane, "Tortilla", 100, PN)]
    _, straty = sw.przyjmij(dane, f, PN.isoformat())
    po = {s["zasob"]: s for s in straty}
    assert po["Mięso kebab"]["ilosc"] == pytest.approx(10) and po["Mięso kebab"]["powod"] == "miejsce"   # 750 l do 600 l
    assert po["Frytki mrożone"]["ilosc"] == pytest.approx(1)              # bez zamrażarki
    assert "Tortilla" not in po                                           # suche – bez limitu
    assert sw.zajete(dane, f, PN.isoformat())["chlodnia"] == pytest.approx(600)
    # ostrzeżenie na liście błędów (zamówienie ponad pojemność)
    f2 = Firma(nazwa="B", stanowiska=f.stanowiska, partie=[_partia(dane, "Mięso kebab", 50, PN, runda=2)])
    assert [p for p, _ in sw.ostrzezenia(dane, f2, 2)] == ["pomaranczowy"]
    f3 = Firma(nazwa="C", partie=[_partia(dane, "Mięso kebab", 1, PN, runda=2)])
    assert [p for p, _ in sw.ostrzezenia(dane, f3, 2)] == ["czerwony"]


def test_zamiennik_mrozona_pita():
    dane = dane_domyslne()
    assert sw.zamienniki(dane, "Pita") == ["Pita mrożona"]
    f = Firma(nazwa="A", magazyn={"Pita mrożona|2": 2.0}, wartosc_magazynu_gr={"Pita mrożona|2": 8000})
    assert sw.dostepne(dane, f.magazyn, "Pita") == pytest.approx(2 * 50 / dane.zasoby["Pita"]["opakowanie"])
    assert sw.jakosc_skladnika(dane, f.magazyn, "Pita") == pytest.approx(1)   # 2★ − kara 1
    f.magazyn["Pita|3"] = 1.0
    assert sw.jakosc_skladnika(dane, f.magazyn, "Pita") == pytest.approx((3 * 1 + 1 * 2 * 50 / dane.zasoby["Pita"]["opakowanie"])
                                                                          / sw.dostepne(dane, f.magazyn, "Pita"))
    # bez partii (gra bez lokali): najpierw świeża, potem mrożona
    zuzyte = _zuzyj(dane, f, {"Pita": 1.5})
    assert f.magazyn["Pita|3"] == pytest.approx(0) and zuzyte["Pita"]["ilosc"] == pytest.approx(1)
    assert zuzyte["Pita mrożona"]["ilosc"] == pytest.approx(0.5 / sw.przelicznik(dane, "Pita mrożona"))
    # danie z mrożoną pitą ma niższą jakość składników niż ze świeżą
    assert sw.jakosc_skladnika(dane, {"Pita mrożona|3": 5.0}, "Pita") < sw.jakosc_skladnika(dane, {"Pita|3": 5.0}, "Pita")


def test_wylaczone_danie_klienci_przechodza():
    dane = dane_domyslne()
    popyt = {"a": 10, "b": 30, "c": 10}
    nowy, przeszli = menu.przenies(dane, popyt, {"a": "Bułka"})
    assert przeszli == {"a": 5} and nowy == {"a": 5, "b": 34, "c": 11}   # połowa klientów, proporcjonalnie do popytu
    nowy, przeszli = menu.przenies(dane, {"a": 10}, {"a": "Bułka"})
    assert nowy == {"a": 10} and przeszli == {"a": 0}                      # nie ma innego dania
    assert menu.wylaczone(dane, {"Bułka|2": 1.0}, ["kebab_w_bulce"]) == {"kebab_w_bulce": "Mięso kebab"}


def test_gra_dostawy_na_dni_kosz_i_zwrot():
    g = _gra(("A", None), ("B", None))
    _runda(g, A=_lokal("centrum_3"))
    dni = pp.dni_rundy(g.dane, 2)
    s = _runda(g, A={"zamowienia": [{"dostawca": DOSTAWCA, "zasob": "Bułka", "jakosc": 2, "ilosc": 2, "dzien": 0},
                                    {"dostawca": DOSTAWCA, "zasob": "Tortilla", "jakosc": 2, "ilosc": 3, "dzien": 3},
                                    {"dostawca": DOSTAWCA, "zasob": "Sos", "jakosc": 2, "ilosc": 1, "dzien": 3}]})
    w = s.wyniki[2]["A"]
    straty = [(x["zasob"], x["data"], x["powod"]) for x in w["swiezosc"]["straty"]]
    assert straty == [("Bułka", dni[1].isoformat(), "termin")]           # bułka z poniedziałku – kosz we wtorek
    bulka = next(x for x in w["zasoby"] if x["zasob"] == "Bułka")
    assert bulka["straty"] == pytest.approx(2) and bulka["wykorzystane"] == pytest.approx(0) and bulka["koniec"] == 0
    f = s.firmy["A"]
    assert {p.zasob: p.dostawa for p in f.partie} == {"Tortilla": dni[3].isoformat(), "Sos": dni[3].isoformat()}
    assert w["swiezosc"]["zasoby"]["Tortilla"]["dostawy"][3] == pytest.approx(3)
    # zwrot nadmiaru: całe opakowania z partii tej rundy
    s = _runda(g, A={"zamowienia": [{"dostawca": DOSTAWCA, "zasob": "Napój", "jakosc": 2, "ilosc": 2, "dzien": 0}],
                     "zwrot_nadmiaru": {DOSTAWCA: True}})
    assert not [p for p in s.firmy["A"].partie if p.zasob == "Napój"]
    assert next(x for x in s.wyniki[3]["A"]["zasoby"] if x["zasob"] == "Napój")["zwroty"] == pytest.approx(2)


def test_sprawdz_wykrywa_zly_zamiennik(tmp_path):
    kat = _kopia(tmp_path)

    def zmien(d):
        d["zasoby"]["Pita mrożona"]["zamiennik_dla"] = "Atlantyda"
        d["zasoby"]["Mięso kebab mrożone"]["jednostka"] = "szt."

    _zmien(kat, "zasoby.yaml", zmien)
    bledy = sprawdz(kat)
    assert any("Atlantyda" in b for b in bledy), bledy
    assert any("tę samą jednostkę" in b for b in bledy), bledy
