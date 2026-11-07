"""Bójka o falafel (UF8): w tygodniu po falafelu w ofercie, z małą szansą, najwyżej raz na grę."""

import pytest
from pomocnicze import _gra, _lokal, _runda

from silnik.dane import dane_domyslne
from silnik.model import Firma, Lokal
from silnik.swiat import falafel as fl
from silnik.swiat import zdarzenia as zd

pytestmark = pytest.mark.dane_gry   # falafel.yaml jest tylko w danych gry (w zamrożonej kopii – nie)


@pytest.fixture
def pewna_bojka(monkeypatch):
    oryginal = fl.dane_falafela
    monkeypatch.setattr(fl, "dane_falafela", lambda dane: (lambda b: b and {**b, "zasady": {**b["zasady"], "szansa": 1.0}})(oryginal(dane)))


def _firma(**pola):
    return Firma(nazwa="X", gotowka=0, lokale=[Lokal(id="centrum_3", forma="najem", od_rundy=1, dziala_od=1)], **pola)


def test_dane_bojki():
    dane = dane_domyslne()
    b = fl.dane_falafela(dane)
    assert b["zasady"]["usluga"] in dane.uslugi and 0 < b["zasady"]["szansa"] <= 0.1   # mała szansa
    h = b["historia"]
    assert h["id"] in zd.historie(dane) and h["park"] is None and not h["powazna"]
    # mały skutek: plastry albo kilka godzin właściciela
    skutki = [s for sc in h["sceny"].values() for o in sc["opcje"] for s in o["skutki"]]
    assert {s["typ"] for s in skutki} >= {"gotowka", "czas"}
    assert all(-100 <= s["kwota"] < 0 for s in skutki if s["typ"] == "gotowka")
    assert all(s["godziny"] <= 3 for s in skutki if s["typ"] == "czas")


def test_warunki_startu(pewna_bojka):
    dane = dane_domyslne()
    od = fl.dane_falafela(dane)["zasady"]["od_rundy"]
    assert fl.startuje(dane, _firma(falafel_runda=od - 1), od, 1) == "bojka_o_falafel"
    assert fl.startuje(dane, _firma(falafel_runda=od - 2), od, 1) is None        # falafel nie w ostatnim tygodniu
    assert fl.startuje(dane, _firma(), od, 1) is None                              # nigdy falafela
    assert fl.startuje(dane, _firma(falafel_runda=od - 2), od - 1, 1) is None    # za wcześnie
    assert fl.startuje(dane, _firma(falafel_runda=od, bojka_falafel=od - 1), od + 1, 1) is None   # raz na grę
    assert fl.startuje(dane, _firma(falafel_runda=od, bojka_falafel=od + 1), od + 1, 1)   # bójka z tej rundy nie blokuje
    bez_lokalu = Firma(nazwa="X", gotowka=0, falafel_runda=od - 1)
    assert fl.startuje(dane, bez_lokalu, od, 1) is None


def test_szansa_z_danych():
    """Bez podmiany szansy bójka zdarza się rzadko (strumień „falafel”, różne drużyny i rundy)."""
    dane = dane_domyslne()
    od = fl.dane_falafela(dane)["zasady"]["od_rundy"]
    proby = [fl.startuje(dane, _firma(falafel_runda=r - 1).model_copy(update={"nazwa": f"F{i}"}), r, 7)
             for i in range(40) for r in range(od, od + 10)]
    assert 0 < sum(p is not None for p in proby) / len(proby) < 0.1


def test_bojka_w_grze(pewna_bojka):
    """Drużyna z falafelem w ofercie dostaje bójkę raz, drużyna bez falafela – nigdy; skutek plastrów w KPiR."""
    dane = dane_domyslne()
    od = fl.dane_falafela(dane)["zasady"]["od_rundy"]
    g = _gra(rund=od + 4)
    _runda(g, A=_lokal("centrum_3"), B=_lokal("centrum_4"))
    while g.runda < od - 1:
        _runda(g)
    _runda(g, A={"oferta": {"falafel": 50, "kebab_w_bulce": 200}})   # falafel w karcie od rundy od − 1
    for _ in range(3):
        s = _runda(g)
    fa, fb = s.firmy["A"], s.firmy["B"]
    assert fa.falafel_runda == g.runda - 1 and fb.falafel_runda is None
    assert fa.bojka_falafel == od and fb.bojka_falafel is None
    sceny = [(r, x) for r in s.wyniki for x in (s.wyniki[r]["A"].get("zdarzenia") or {}).get("sceny", [])
             if x["historia"] == "bojka_o_falafel"]
    assert [r for r, _ in sceny] == [od]   # raz na grę (bez wyboru – domyślne plastry, bez ciągu dalszego)
    assert sceny[0][1]["opcja"] == "plastry"
    kpir = [p for p in s.wyniki[od]["A"]["kpir"]["pozycje"] if "falafel" in p["opis"]]
    assert kpir and kpir[0]["pozostale"] == pytest.approx(45)
    assert not any(x["historia"] == "bojka_o_falafel" for r in s.wyniki
                   for x in (s.wyniki[r]["B"].get("zdarzenia") or {}).get("sceny", []))
