"""Popyt strefowy (F3a.4): pule stref, wybór lokalu, dni tygodnia, kalendarz, obsługa dzień po dniu, boty, dane."""

import time
from datetime import date

import pytest
from pomocnicze import KEBAB, _gra, _kopia, _lokal, _oferta, _runda, _zmien

from silnik import boty
from silnik.dane import Dane, dane_domyslne, sprawdz
from silnik.gra import Gra
from silnik.model import Lokal
from silnik.rynek import popyt as pp


def _podzial(dane, runda, *lokale):
    return pp.podzial(dane, pp.pule(dane, runda), {KEBAB: {(f"F{i}", z): o for i, (z, o) in enumerate(lokale)}})


def test_dwa_lokale_w_jednej_strefie_dziela_klientow():
    dane = dane_domyslne()
    sam = _podzial(dane, 5, ("centrum", _oferta("centrum")))[("F0", "centrum")][KEBAB]
    dwa = _podzial(dane, 5, ("centrum", _oferta("centrum")), ("centrum", _oferta("centrum")))
    a, b = (dwa[(f, "centrum")][KEBAB] for f in ("F0", "F1"))
    assert a["strefy"]["centrum"] == pytest.approx(b["strefy"]["centrum"])
    assert a["strefy"]["centrum"] < sam["strefy"]["centrum"] < a["strefy"]["centrum"] + b["strefy"]["centrum"]
    # tańszy lokal zabiera klientów droższemu
    tani = _podzial(dane, 5, ("centrum", _oferta("centrum", 0.85)), ("centrum", _oferta("centrum", 1.15)))
    assert tani[("F0", "centrum")][KEBAB]["dni"].sum() > 1.5 * tani[("F1", "centrum")][KEBAB]["dni"].sum()



def test_rozruch_nowego_lokalu(tmp_path):
    """B5: nowy lokal dopiero zdobywa klientów – mnożnik popytu od `start` w pierwszym tygodniu sprzedaży
    (najwcześniej runda 2) rośnie o `przyrost` co tydzień do 1; bez klucza w danych – 1."""
    stary, nowy = Lokal(id="centrum_1", forma="najem", od_rundy=1, dziala_od=1),         Lokal(id="centrum_1", forma="najem", od_rundy=5, dziala_od=6)
    assert pp.rozruch(_bez_rozruchu(tmp_path), stary, 2) == 1.0
    kat = _kopia(tmp_path / "z")
    _zmien(kat, "mapa/popyt.yaml", lambda d: d["model"].update(rozruch={"start": 0.5, "przyrost": 0.2}))
    dane = Dane(kat)
    assert [pp.rozruch(dane, stary, r) for r in (1, 2, 3, 4, 5, 9)] == pytest.approx([0.5, 0.5, 0.7, 0.9, 1, 1])
    assert [pp.rozruch(dane, nowy, r) for r in (6, 7)] == pytest.approx([0.5, 0.7])   # drugi lokal też od zera
    o = _oferta("centrum")
    assert pp.atrakcyjnosc(dane, "centrum", KEBAB, {**o, "rozruch": 0.5}) == pytest.approx(
        0.5 * pp.atrakcyjnosc(dane, "centrum", KEBAB, o))
    # w grze: popyt pierwszego tygodnia sprzedaży mniejszy niż bez rozruchu (ta sama gra botów)
    def popyt_r2(d):
        g = Gra.nowa("rozruch", [("A", "zrownowazony"), ("B", "premium")], 2, 3, dane=d)
        g.przelicz(wymus=True)
        return sum(v["popyt"] for v in g.przelicz(wymus=True).wyniki[2]["A"]["sprzedaz"].values())
    assert popyt_r2(dane) < 0.7 * popyt_r2(_bez_rozruchu(tmp_path / "g"))


def _bez_rozruchu(tmp_path):
    kat = _kopia(tmp_path / "bez")
    _zmien(kat, "mapa/popyt.yaml", lambda d: d["model"].pop("rozruch", None))
    return Dane(kat)


def test_pula_strefy_i_odleglosc():
    dane = dane_domyslne()
    pule = pp.pule(dane, 5)
    lokale = [(z, _oferta(z)) for z in ("centrum", "centrum", "dworzec")]
    pod = _podzial(dane, 5, *lokale)
    for z, pz in pule.items():  # klienci lokali ze strefy nie przekraczają jej puli (część idzie poza grę)
        assert sum(x[KEBAB]["strefy"].get(z, 0.0) for x in pod.values()) < pz[KEBAB].sum()
    w = pod[("F0", "centrum")][KEBAB]["strefy"]
    blisko, daleko = pp.odleglosc(dane, "centrum", "stare_miasto"), pp.odleglosc(dane, "centrum", "zemborzyce")
    assert blisko < daleko
    udzial = {z: w[z] / pule[z][KEBAB].sum() for z in ("centrum", "stare_miasto", "zemborzyce")}
    assert udzial["centrum"] > udzial["stare_miasto"] > udzial["zemborzyce"]


def test_dni_tygodnia_i_kalendarz():
    dane = dane_domyslne()
    r = next(r for r in range(1, 30) if dane.data_rundy(r) == date(2025, 11, 10))   # tydzień z 11 listopada (wtorek)
    dni = pp.dni_rundy(dane, r)
    assert len(dni) == 7 and dni[0].weekday() == 0
    w = pp.wagi_dni(dane, "dworzec", dni)
    assert w[4] > w[0]                                      # piątek > poniedziałek
    assert dni[1] == date(2025, 11, 11)
    assert [x["nazwa"] for x in pp.wydarzenia(dane, dni)] == ["Święto Niepodległości"]
    c = pp.wagi_dni(dane, "centrum", dni)
    assert c[1] / c[2] == pytest.approx(1.5 * 1.1 / 1.1)    # święto: Centrum ×1,5 (klucz strefy wygrywa z „wszystkie”)
    assert w[1] / w[2] == pytest.approx(0.8 * 0.9 / 0.95)    # reszta miasta ×0,8
    # wydarzenie przez Nowy Rok
    swieta = pp.dni_rundy(dane, next(r for r in range(1, 30) if dane.data_rundy(r) == date(2025, 12, 29)))
    assert any(x["nazwa"] == "Przerwa świąteczna na uczelniach" for x in pp.wydarzenia(dane, swieta))
    assert pp.szczyt(dane, "stare_miasto", r) > 1.2


def test_gra_obsluga_dzien_po_dniu_i_wyniki_klientow(monkeypatch):
    # dwa boty w Centrum: dzielą klientów strefy, obsługa dzień po dniu
    monkeypatch.setattr(boty, "_wybierz_lokal", lambda dane, stan, nazwa, *a: _lokal({"A": "centrum_3", "B": "centrum_1"}[nazwa])["lokal"])
    g = _gra(("A", "zrownowazony"), ("B", "zrownowazony"))
    g.przelicz(wymus=True)
    s = g.przelicz(wymus=True)
    for n in ("A", "B"):
        w = s.wyniki[2][n]
        k = w["klienci"]
        assert len(k["dni"]) == 7 and [lok["strefa"] for lok in k["lokale"]] == ["centrum"]
        assert sum(d["popyt"] for d in k["dni"]) == sum(v["popyt"] for v in w["sprzedaz"].values())
        assert sum(d["sprzedaz"] for d in k["dni"]) == sum(v["sprzedaz"] for v in w["sprzedaz"].values())
        assert sum(d["sprzedaz"] for d in k["dni"]) > 0
        pt, pn = k["dni"][4], k["dni"][0]
        assert pt["dzien"] == "pt" and pt["popyt"] > pn["popyt"]
    strefy = s.rynek[2]["strefy"]
    assert set(strefy["strefy"]) == set(g.dane.mapa["strefy"]) and len(strefy["dni"]) == 7
    assert set(strefy["strefy"]["centrum"]["klienci"]) == {"A", "B"}


def test_boty_w_strefach_sprzedaja_i_gra_jest_szybka():
    g = _gra(("Tani", "tani"), ("Premium", "premium"), ("Zrown", "zrownowazony"), ("Agr", "agresywny"), rund=10)
    t = time.perf_counter()
    for _ in range(10):
        s = g.przelicz(wymus=True)
    assert time.perf_counter() - t < 15
    for n in s.firmy:
        w = s.wyniki[10][n]
        sprzedaz = sum(v["sprzedaz"] for v in w["sprzedaz"].values())
        popyt = sum(v["popyt"] for v in w["sprzedaz"].values())
        assert sprzedaz > 300 and sprzedaz <= popyt, n
        assert w["sprzedaz"][KEBAB]["prognoza"] > 0, n
    # kalibracja: lokal 2★ po cenie strefy w Centrum, bez konkurencji – rząd wielkości firmy z Revasa
    dane = g.dane
    pod = _podzial(dane, 5, ("centrum", _oferta("centrum")))
    assert 400 < pod[("F0", "centrum")][KEBAB]["dni"].sum() < 1500


def test_widok_popytu_pule_bez_gotowej_prognozy():
    from api.prezentacja import widok
    g = _gra()
    v = widok(g, "A")
    p = v["popyt"]
    assert p["runda"] == 2 and len(p["dni"]) == 7
    assert all(s["potencjal"] > 0 and s["pula"] > 0 for s in p["strefy"].values())
    _runda(g, A=_lokal("centrum_3"))
    p = widok(g, "A")["popyt"]
    assert "prognoza" not in p and "szczyt" not in p      # popyt drużyna liczy sama (test gry 28.10)
    assert len(p["strefy"]["centrum"]["dni"]) == 7 and "A" in p["strefy"]["centrum"]["firmy"]


def test_sprawdz_wykrywa_bledy_popytu(tmp_path):
    kat = _kopia(tmp_path)

    def zmien(d):
        d["strefy"].pop("felin")

    _zmien(kat, "mapa/popyt.yaml", zmien)
    bledy = sprawdz(kat)
    assert any("felin" in b and "bez popytu" in b for b in bledy), bledy
