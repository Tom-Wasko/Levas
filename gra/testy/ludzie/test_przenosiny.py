"""UF20: obsada stanowisk i przenosiny pracowników między lokalami (zgoda zależna od zadowolenia, odległości i dodatku)."""

import pytest

from silnik.dane import KUCHNIA, dane_domyslne
from silnik.ksiegowosc import rozliczenie as rz
from silnik.ksiegowosc.finanse import Ksiega, Rachunek
from silnik.ludzie import przenosiny as pz
from silnik.ludzie import rynek_pracy as rp
from silnik.model import Firma, Lokal, Odejscie, Pracownik, StanGry, Stanowisko

pytestmark = pytest.mark.dane_gry   # parametry zgody są tylko w dane/ (zamrożona kopia – zawsze zgoda)

A, B = "politechnika_1", "centrum_1"


def _p(id_, nr, zadowolenie=None):
    return Pracownik(id=id_, imie_nazwisko=id_, zawod="kucharz", gwiazdki=3, pensja_preferowana=5300,
                     koszt_rekrutacji=400, koszt_odprawy=2650, zadowolenie_klientow=0.95, ryzyko_reklamacji=0.0,
                     pensja=5300, stanowisko=nr, zadowolenie=zadowolenie)


def _firma():
    """Lokal A: kuchnia 1 (Ala), kuchnia 2 (wolna), kasa 1 (wolna); lokal B: kuchnia 3 (wolna), kuchnia 4 (Ola)."""
    f = Firma(nazwa="F", lokale=[Lokal(id=A, forma="najem", od_rundy=1, dziala_od=2),
                                 Lokal(id=B, forma="najem", od_rundy=1, dziala_od=2)],
              stanowiska=[Stanowisko(nr=1, typ=KUCHNIA, lokal=A, pracownik="ala"), Stanowisko(nr=2, typ=KUCHNIA, lokal=A),
                          Stanowisko(nr=1, typ="kasa", lokal=A), Stanowisko(nr=3, typ=KUCHNIA, lokal=B),
                          Stanowisko(nr=4, typ=KUCHNIA, lokal=B, pracownik="ola")])
    f.pracownicy = {"ala": _p("ala", 1, 0.95), "ola": _p("ola", 4)}
    return f


def _ksiega(dane):
    return Ksiega(vat=rz.reguly_vat(dane)), Rachunek()


def test_szansa_rosnie_z_zadowoleniem_i_dodatkiem_maleje_z_odlegloscia():
    dane = dane_domyslne()
    p = _p("x", 1, 0.95)
    odl = pz.odleglosc(dane, A, B)
    assert odl > 0 and pz.odleglosc(dane, A, A) == 0
    s = pz.szansa(dane, p, odl, 0)
    assert pz.szansa(dane, p, odl, 2000) > s > pz.szansa(dane, p.model_copy(update={"zadowolenie": 0.8}), odl, 0)
    assert pz.szansa(dane, p, odl + 10, 0) < s
    u = pz.ustawienia(dane)
    assert u["szansa_min"] <= pz.szansa(dane, p.model_copy(update={"zadowolenie": 0.0}), 30, 0) == u["szansa_min"]


def test_obsada_w_tym_samym_lokalu_i_odmowy():
    dane = dane_domyslne()
    f = _firma()
    ks, rach = _ksiega(dane)
    w = pz.zastosuj(dane, f, [{"pracownik": "ala", "typ": KUCHNIA, "nr": 2},
                              {"pracownik": "ola", "typ": KUCHNIA, "nr": 2},      # zajęte – Ala już przeszła
                              {"pracownik": "ola", "typ": "kasa", "nr": 1},       # kucharz nie stanie na kasie
                              {"pracownik": "nikt", "typ": KUCHNIA, "nr": 3}], ks, rach)
    assert [x["wynik"] for x in w] == ["przeniesiony", "nieudane", "nieudane", "nieudane"]
    assert f.stanowisko(KUCHNIA, 2).pracownik == "ala" and f.stanowisko(KUCHNIA, 1).pracownik is None
    assert f.pracownicy["ala"].stanowisko == 2 and "szansa" not in w[0] and w[0]["dodatek"] == 0
    assert "zajęte" in w[1]["powod"] and "zawodu" in w[2]["powod"]


def test_przenosiny_do_innego_lokalu_z_dodatkiem_i_wypowiedzeniem():
    dane = dane_domyslne()
    f = _firma()
    ks, rach = _ksiega(dane)
    przed = f.gotowka
    w = pz.zastosuj(dane, f, [{"pracownik": "ala", "typ": KUCHNIA, "nr": 3, "dodatek": 500, "zgoda": True}], ks, rach)
    assert w[0]["wynik"] == "przeniesiony" and w[0]["dodatek"] == 500 and w[0]["do_lokalu"] == B
    assert f.stanowisko(KUCHNIA, 3).pracownik == "ala" and round(przed - f.gotowka, 2) == 500
    f.pracownicy["ola"].odchodzi = Odejscie(do="", runda=9, pensja_gr=0, od_rundy=3)
    w = pz.zastosuj(dane, f, [{"pracownik": "ola", "typ": KUCHNIA, "nr": 2}], ks, rach)
    assert w[0]["wynik"] == "nieudane" and "wypowiedzenia" in w[0]["powod"]
    # bez rozstrzygnięcia (podgląd) – wpis z szansą zgody do listy błędów
    w = pz.zastosuj(dane, _firma(), [{"pracownik": "ala", "typ": KUCHNIA, "nr": 3}], *_ksiega(dane))
    assert 0 < w[0]["szansa"] < 1


def test_zgoda_losowana_w_przeliczeniu_a_w_podgladzie_nie():
    dane = dane_domyslne()
    s = StanGry(runda=3, firmy={"F": _firma()}, kandydaci=[])
    d = {"F": {"przenosiny": [{"pracownik": "ala", "typ": KUCHNIA, "nr": 3}, {"pracownik": "ala", "typ": KUCHNIA, "nr": 2}]}}
    dd, _, raport = rp.przed_decyzjami(dane, s.kopia(), {"F": dict(d["F"])}, 3, 11, podglad=True)
    assert dd["F"]["przenosiny"] == d["F"]["przenosiny"] and raport["F"]["przenosiny"] == []
    wyniki = set()
    for ziarno in range(40):
        dd, _, raport = rp.przed_decyzjami(dane, s.kopia(), {"F": dict(d["F"])}, 3, ziarno)
        (x,) = raport["F"]["przenosiny"]   # tylko przejście do innego lokalu wymaga zgody
        assert x["do_lokalu"] == B and 0 < x["szansa"] < 1
        assert len(dd["F"]["przenosiny"]) == (2 if x["zgoda"] else 1)
        assert (not x["zgoda"]) == any("nie zgodził" in u for u in raport["F"]["uwagi"])
        wyniki.add(x["zgoda"])
    assert wyniki == {True, False}
    a = rp.przed_decyzjami(dane, s.kopia(), {"F": dict(d["F"])}, 3, 5)[2]["F"]["przenosiny"]
    assert a == rp.przed_decyzjami(dane, s.kopia(), {"F": dict(d["F"])}, 3, 5)[2]["F"]["przenosiny"]
