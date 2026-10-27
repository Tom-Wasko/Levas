"""Środki trwałe i amortyzacja (F3a.6): kupiony lokal, działka i budynek, zakupy od progu, sprzedaż, gra Revas bez zmian."""

import pytest
from test_lokale import _gra, _lokal, _runda

from silnik import srodki_trwale as st
from silnik.dane import dane_domyslne
from silnik.finanse import Ksiega, Rachunek
from silnik.model import Firma


def _kpir(s, r, firma, poczatek):
    return [p["pozostale"] for p in s.wyniki[r][firma]["kpir"]["pozycje"] if p["opis"].startswith(poczatek)]


def test_kupiony_lokal_amortyzuje_sie_od_nastepnej_rundy():
    g = _gra()
    cena = g.dane.lokale["zygmuntowskie_1"]["cena"]
    s = _runda(g, B=_lokal("zygmuntowskie_1", "kupno"))
    assert _kpir(s, 1, "B", "Amortyzacja") == [] and not _kpir(s, 1, "B", "Zakup lokalu")
    [e] = s.wyniki[1]["B"]["srodki_trwale"]
    assert e["rodzaj"] == "lokal" and e["wartosc"] == pytest.approx(cena) and e["stawka"] == pytest.approx(0.025)
    s = _runda(g)
    odpis = round(cena * 0.025 / g.dane.rund_w_roku, 2)
    assert _kpir(s, 2, "B", "Amortyzacja: Lokal") == [pytest.approx(odpis)]
    assert s.wyniki[2]["B"]["srodki_trwale"][0]["netto"] == pytest.approx(cena - odpis)
    assert s.wyniki[2]["A"]["srodki_trwale"] == []                    # wynajęty lokal nie jest środkiem trwałym


def test_dzialka_grunt_bez_amortyzacji_budynek_po_budowie():
    g = _gra()
    lok = g.dane.lokale["czechow_3"]
    n = lok["budowa_rund"]
    for _ in range(n + 1):
        s = _runda(g, **({"A": _lokal("czechow_3", "kupno")} if not g.stan().wyniki else {}))
    ew = {e["rodzaj"]: e for e in s.wyniki[n + 1]["A"]["srodki_trwale"]}
    assert ew["grunt"]["umorzenie"] == 0 and ew["budynek"]["wartosc"] == pytest.approx(lok["koszt_budowy"])
    assert ew["budynek"]["od_rundy"] == n and ew["budynek"]["umorzenie"] > 0


def test_zakup_od_progu_i_sprzedaz():
    dane = dane_domyslne()
    f, ks, rach = Firma(nazwa="A", gotowka=50000), Ksiega(), Rachunek()
    st.zakup(dane, f, ks, rach, "Koszt zakupu: Piec", "Piec", "sprzet", 12000, 3)
    st.zakup(dane, f, ks, rach, "Koszt zakupu: Krzesło", "Krzesło", "wyposazenie", 300, 3)   # poniżej progu
    assert [p["opis"] for p in ks.pozycje] == ["Koszt zakupu: Krzesło"]
    assert f.gotowka == pytest.approx(50000 - 12300) and [s.nazwa for s in f.srodki_trwale] == ["Piec"]
    st.amortyzuj(dane, f, 3, ks)
    assert len(ks.pozycje) == 1                                         # w rundzie zakupu bez odpisu
    st.amortyzuj(dane, f, 4, ks)
    assert ks.pozycje[-1]["pozostale"] == pytest.approx(round(12000 * 0.2 / dane.rund_w_roku, 2))
    assert st.sprzedaj(f, "Piec", ks) and not st.sprzedaj(f, "Piec", ks)
    assert ks.pozycje[-1]["pozostale"] == pytest.approx(12000 - round(12000 * 0.2 / dane.rund_w_roku, 2))
    assert f.srodki_trwale == []


def test_odpisy_nie_przekraczaja_wartosci():
    dane = dane_domyslne()
    f, ks = Firma(nazwa="A"), Ksiega()
    st.przyjmij(dane, f, "Laptop", "sprzet", 10400, 1)
    for r in range(2, 2 + 6 * dane.rund_w_roku):
        st.amortyzuj(dane, f, r, ks)
    assert ks.suma("pozostale") == pytest.approx(10400) and f.srodki_trwale[0].umorzenie == pytest.approx(10400)
