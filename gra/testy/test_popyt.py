"""Popyt strefowy (F3a.4): pule stref, wybór lokalu, dni tygodnia, kalendarz, obsługa dzień po dniu, boty, dane."""

import time
from datetime import date

import pytest
from test_dane import _kopia, _zmien
from test_lokale import _gra, _lokal, _runda

from silnik import boty
from silnik import popyt as pp
from silnik.dane import dane_domyslne, sprawdz

KEBAB = "kebab_w_bulce"


def _oferta(strefa, cena_proc=1.0, jakosc=(2, 2, 2), **inne):
    d = dane_domyslne()
    cena = d.uslugi[KEBAB]["cena_preferowana"] * d.mapa["popyt"]["strefy"][strefa]["cena"] * cena_proc
    return {"strefa": strefa, "cena": cena, "jakosc": jakosc, **inne}


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


def test_widok_popytu_prognoza_i_potencjal():
    from api.prezentacja import widok
    g = _gra()
    v = widok(g, "A")
    p = v["popyt"]
    assert p["runda"] == 2 and p["prognoza"]["lokale"] == {} and len(p["dni"]) == 7
    assert all(s["potencjal"] > 0 for s in p["strefy"].values())
    _runda(g, A=_lokal("centrum_3"))
    p = widok(g, "A")["popyt"]
    assert set(p["prognoza"]["lokale"]) == {"centrum_3"} and p["prognoza"]["dania"][KEBAB] > 0
    assert len(p["prognoza"]["dni"]) == 7 and "centrum_3" in p["szczyt"]


def test_sprawdz_wykrywa_bledy_popytu(tmp_path):
    kat = _kopia(tmp_path)

    def zmien(d):
        d["strefy"].pop("felin")

    _zmien(kat, "mapa/popyt.yaml", zmien)
    bledy = sprawdz(kat)
    assert any("felin" in b and "bez popytu" in b for b in bledy), bledy
