"""Majątek netto firmy (Z2): składniki, długi, leasing poza majątkiem, wynik rundy i widok mistrza gry."""

import pytest
from pomocnicze import _gra, _lokal, _runda

from api.prezentacja import przeglad_mg, tabela_wynikow
from silnik.model import Firma, Kredyt, Leasing, Lokal, Lokata, PozyczkaHarpagona, SrodekTrwaly
from silnik.pieniadze.wlasciciel import portfel
from silnik.wyniki.majatek import majatek_netto, z_portfelem


def test_skladniki_i_dlugi():
    f = Firma(nazwa="A", gotowka=10000, kredyt_odnawialny=500, majatek=8000, umorzenie_majatku=1000)
    f.lokaty = [Lokata(id=1, kwota=3000, oprocentowanie=0.05, od_rundy=1, miesiecy=3)]
    f.lokale = [Lokal(id="x", forma="najem", od_rundy=1, dziala_od=1, kaucja=4000),
                Lokal(id="y", forma="kupno", od_rundy=1, dziala_od=1, cena=200000)]
    f.srodki_trwale = [SrodekTrwaly(nazwa="Lokal: y", rodzaj="lokal", wartosc=200000, od_rundy=1, stawka=0.025,
                                    umorzenie=2000)]
    f.rozliczenie.vat_nadwyzka = 700
    f.wartosc_magazynu_gr = {"mieso|2": 150000}
    f.kredyty = [Kredyt(id=2, kwota=20000, oprocentowanie=0.1, od_rundy=1, miesiecy=12, pozostalo=18000)]
    f.harpagon = PozyczkaHarpagona(kwota=5000, dlug=5250, od_rundy=1, termin=4)
    f.leasingi = [Leasing(id=3, bank="ING", typ="kuchnia", nr=1, nazwa="grill", jakosc=2, cena=30000, od_rundy=1,
                          rund=12, pozostalo_rat=10, rata=900, wykup=300, zalegle=1)]
    m = majatek_netto(f)
    aktywa = 10000 + 3000 + 4000 + 700 + 1500 + 198000 + 7000   # bez portfela właściciela
    assert m["razem"] == pytest.approx(aktywa - 18000 - 500 - 900 - 5250)
    assert m["leasing"] == -900          # tylko zaległa rata – przyszłe raty i sprzęt w leasingu poza majątkiem
    assert m["razem"] == pytest.approx(sum(v for k, v in m.items() if k != "razem"))


def test_majatek_netto_w_wynikach_i_panelu():
    g = _gra(("A", None), ("B", "zrownowazony"), rund=4)
    s = _runda(g, A={**_lokal("centrum_3"), "harpagon_wez": 10000})
    m = s.wyniki[1]["A"]["majatek_netto"]
    assert m["gotowka"] == s.wyniki[1]["A"]["gotowka"] and m["harpagon"] < 0
    assert m["kaucje"] == pytest.approx(sum(lk.kaucja for lk in s.firmy["A"].lokale)) and m["kaucje"] > 0
    # pożyczka nie podnosi majątku netto: gotówka rośnie o tyle, o ile dług
    assert m["razem"] < g.kapital_startowy + 1
    assert z_portfelem(s.wyniki[1]["A"]) == pytest.approx(m["razem"] + portfel(g.dane, s.firmy["A"]))
    _runda(g)
    p = przeglad_mg(g)
    a = next(f for f in p["firmy"] if f["nazwa"] == "A")
    assert a["majatek_netto"] == g.stan(2).wyniki[2]["A"]["majatek_netto"]["razem"]
    assert p["historia"][-1]["majatek"]["B"] is not None
    naglowek, wiersze = tabela_wynikow(g)
    assert "majątek netto" in naglowek and all(w[naglowek.index("majątek netto")] != "" for w in wiersze)
    assert "majątek netto" in tabela_wynikow(g, "ranking")[0]
