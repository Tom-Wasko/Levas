"""Lichwiarz Harpagon (F3a.10): pożyczka od ręki poza KPiR, odsetki od całego długu, po terminie rosnąca presja –
przypomnienia, odsetki karne, wizyty (szkody w lokalu, odpływ klientów, odejście pracownika); spłata kończy presję."""

from copy import deepcopy

import numpy as np
from test_lokale import _gra, _lokal, _rachunek, _runda

from silnik import lichwiarz as lw
from silnik import zaleglosci as zg
from silnik.finanse import Ksiega, Rachunek
from silnik.model import Pracownik


def _harpagon(s, r, firma):
    return s.wyniki[r][firma]["harpagon"]


def _kpir_harpagona(s, r, firma):
    return [p for p in s.wyniki[r][firma]["kpir"]["pozycje"] if "Harpagon" in p["opis"]]


def _bledy(s, r, firma):
    return [b for b in s.wyniki[r][firma]["lista_bledow"] if b["zakladka"] == "harpagon"]


def test_pozyczka_poza_kpir_i_odsetki_od_calego_dlugu():
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "harpagon_wez": 10000}, B=_lokal("dworzec_1"))
    p = s.firmy["A"].harpagon
    assert (p.kwota, p.od_rundy, p.termin) == (10000, 1, 5)
    assert _rachunek(s, 1, "A", "Gotówka od Harpagona") == [10000]
    op = next(o for o in s.wyniki[1]["A"]["rachunek"] if o["opis"].startswith("Gotówka od Harpagona"))
    assert op["poza_ksiegami"]
    assert not _kpir_harpagona(s, 1, "A")
    assert p.dlug == 10500                                  # 5% od długu na koniec rundy
    s = _runda(g)
    assert s.firmy["A"].harpagon.dlug == round(10500 * 1.05, 2)
    assert _harpagon(s, 2, "A")["stan"]["etap"] == "przed"
    s = _runda(g, A={"harpagon_splac": 20000})               # spłata do wysokości długu
    assert s.firmy["A"].harpagon is None and _harpagon(s, 3, "A")["poczatek"]["splacona"]
    assert _rachunek(s, 3, "A", "Spłata pożyczki u Harpagona") == [-round(10500 * 1.05, 2)]   # spłata przed odsetkami rundy
    assert not _kpir_harpagona(s, 3, "A") and not _bledy(s, 3, "A")


def test_odrzucone_pozyczki_i_splata_bez_gotowki():
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "harpagon_wez": 50000}, B=_lokal("dworzec_1"))
    assert s.firmy["A"].harpagon is None
    assert any("od 500,00 zł do 20 000,00 zł" in b["tekst"] for b in _bledy(s, 1, "A"))
    s = _runda(g, A={"harpagon_wez": 5000})
    s = _runda(g, A={"harpagon_wez": 5000})
    assert s.firmy["A"].harpagon.kwota == 5000
    assert any("spłacić obecną" in b["tekst"] for b in _bledy(s, 3, "A"))
    f = deepcopy(s.firmy["A"])
    f.gotowka = 100
    info = lw.poczatek_rundy(g.dane, f, {"harpagon_splac": 1000}, 4, Rachunek())
    assert info["odrzucone"] and f.harpagon.dlug == s.firmy["A"].harpagon.dlug


def test_scenariusz_presji_krok_po_kroku():
    g = _gra(("A", None), ("B", None), rund=12)
    s = _runda(g, A={**_lokal("centrum_3"), "harpagon_wez": 4000}, B=_lokal("dworzec_1"))
    u = lw.ustawienia(g.dane)
    etapy, teksty = {}, {}
    for r in range(2, 10):
        s = _runda(g)
        h = _harpagon(s, r, "A")
        etapy[r], teksty[r] = h["presja"]["etap"], h["presja"]["teksty"]
        if r >= 5:
            assert any(b["poziom"] == "pomaranczowy" for b in _bledy(s, r, "A"))
    assert [etapy[r] for r in range(2, 10)] == ["przed"] * 3 + ["termin", "przypomnienie", "karne", "wizyty", "wizyty"]
    assert not teksty[4] and "życzę zdrowia" in teksty[5][0]
    assert "gęsim piórem" in teksty[6][0]
    assert len(teksty[7]) == 2 and "odsetki karne" in teksty[7][1]
    assert _harpagon(s, 6, "A")["odsetki"]["stopa"] == u["oprocentowanie_rundy"]
    assert _harpagon(s, 7, "A")["odsetki"]["stopa"] == u["odsetki_karne_rundy"]
    for r in (8, 9):
        w = _harpagon(s, r, "A")["presja"]["wizyta"]
        assert w["rodzaj"] in ("szkody", "klienci", "pracownik") and "{" not in w["tekst"]
        if w["rodzaj"] == "szkody":
            assert [p["pozostale"] for p in s.wyniki[r]["A"]["kpir"]["pozycje"]
                    if p["opis"] == "Naprawa szkód w lokalu"] == [w["koszt"]]
    assert s.firmy["A"].harpagon.wizyty == 2
    assert not any(_kpir_harpagona(s, r, "A") for r in range(1, 10))
    s = _runda(g, A={"harpagon_splac": s.firmy["A"].harpagon.dlug})   # spłata kończy presję
    assert s.firmy["A"].harpagon is None
    assert _harpagon(s, 10, "A")["presja"]["etap"] is None and not _bledy(s, 10, "A")


def _wizyta(g, rodzaj, firma):
    wizyty = [w for w in lw.ustawienia(g.dane)["wizyty"] if rodzaj in (None, w["rodzaj"])]
    ks, rach = Ksiega(), Rachunek()
    w, odszedl = zg.wizyta(g.dane, firma, wizyty, np.random.default_rng(1), ks, rach, {"dlug": "1 zł"}, "Naprawa")
    return w, odszedl, ks


def test_wizyty_szkody_klienci_i_odejscie_pracownika():
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 1}}, B=_lokal("dworzec_1"))
    f = deepcopy(s.firmy["A"])
    w, _, ks = _wizyta(g, "szkody", f)
    assert 800 <= w["koszt"] <= 3000 and ks.pozycje[0]["opis"] == "Naprawa" and w["koszt"] > 0
    w, _, _ = _wizyta(g, "klienci", f)
    assert w["odplyw"] == 0.3 and "30%" in w["tekst"]
    st = f.stanowisko("kuchnia", 1)
    f.pracownicy["p1"] = Pracownik(id="p1", imie_nazwisko="Kleant Walerski", zawod="kucharz", gwiazdki=2,
                                   pensja_preferowana=4000, koszt_rekrutacji=0, koszt_odprawy=0,
                                   zadowolenie_klientow=1.0, ryzyko_reklamacji=0.0, stanowisko=1)
    st.pracownik = "p1"
    w, odszedl, _ = _wizyta(g, "pracownik", f)
    assert odszedl.id == "p1" and "Kleant Walerski" in w["tekst"]
    assert "p1" not in f.pracownicy and st.pracownik is None
    w, odszedl, _ = _wizyta(g, None, f)              # nie ma kto odejść – inna wizyta
    assert odszedl is None and w["rodzaj"] != "pracownik"
