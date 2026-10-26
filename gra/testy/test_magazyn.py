"""Magazyn w grze z lokalami (zmiana 26.10): wynajęta chłodnia, kontrole sanepidu, bank żywności, brak zwrotów."""

import copy

import pytest
from test_lokale import _gra, _lokal, _runda

from silnik import magazyn as mag
from silnik import zdarzenia as zd
from silnik.dane import dane_domyslne
from silnik.finanse import Ksiega, Rachunek
from silnik.model import Firma

DOSTAWCA = "Makro"


def test_szansa_i_mandat():
    dane = dane_domyslne()
    z = dane.z["magazyn"]["sanepid"]
    assert mag.szansa_kontroli(dane, 0, 0) == {"szansa": z["szansa_bazowa"], "problem": 0}
    sz = mag.szansa_kontroli(dane, 100, 300)
    assert sz["szansa"] == pytest.approx(z["szansa_bazowa"] + 100 * z["szansa_za_litr_wynajmu"]
                                         + 300 * z["szansa_za_zl_przeterminowanych"])
    assert mag.szansa_kontroli(dane, 10 ** 6, 0)["szansa"] == z["szansa_max"]
    assert mag.mandat(dane, 0, 0) == z["mandat_min"] and mag.mandat(dane, 10 ** 6, 0) == z["mandat_max"]
    assert mag.mandat(dane, 100, 300) % 50 == 0


def test_kontrola_sanepidu():
    """Duży nadmiar w wynajmie i przeterminowany towar: kontrola, mandat poza KPiR, mniejszy popyt i tekst bez {…}."""
    g = _gra()
    s = _runda(g, A=_lokal("centrum_3"))
    dane, f = g.dane, copy.deepcopy(s.firmy["A"])
    raport = {"wynajem": [{"litry": 2000, "koszt": 2000}], "straty": [{"wartosc": 1500, "powod": "termin"}]}
    wyniki = {}
    for ziarno in range(40):
        ff, ks, rach = copy.deepcopy(f), Ksiega(vat=None), Rachunek()
        w = mag.koniec_rundy(dane, ff, 2, ziarno, raport, ks, rach)
        wyniki.setdefault(w["sanepid"]["mandat"] > 0, (w, ff, rach))
    assert set(wyniki) == {True, False}
    w, ff, rach = wyniki[True]
    sp = w["sanepid"]
    assert sp["kontrola"] and sp["szansa"] == dane.z["magazyn"]["sanepid"]["szansa_max"]
    assert "{" not in sp["tekst"] and "zł" in sp["tekst"]
    assert [(o["rodzaj"], o["kwota"]) for o in rach.operacje if o["opis"] == mag.MANDAT] == [("kary", -sp["mandat"])]
    assert [(o["rodzaj"], o["kwota"]) for o in rach.operacje if o["opis"].startswith(mag.WYNAJEM)] == [("kpir", -2000)]
    assert [(e.typ, e.od_rundy) for e in ff.efekty] == [("popyt", 3)]
    # bez lokalu – bez kontroli
    w = mag.koniec_rundy(dane, Firma(nazwa="X"), 2, 1, raport, Ksiega(vat=None), Rachunek())
    assert w["sanepid"] is None and w["wynajem"]["koszt"] == 2000


def test_wynajem_w_grze():
    """Zamówienie ponad chłodnię lokalu: koszt wynajmu w KPiR (z VAT), wyniki magazynu, brak kosztu magazynowania."""
    g = _gra()
    _runda(g, A=_lokal("centrum_3"))
    s = _runda(g, A={"zamowienia": [{"dostawca": DOSTAWCA, "zasob": "Mięso kebab", "jakosc": 2, "ilosc": 100, "dzien": 0}]})
    w = s.wyniki[2]["A"]
    wyn = w["swiezosc"]["wynajem"]
    assert wyn and wyn[0]["zasob"] == "Mięso kebab" and w["magazyn"]["wynajem"]["koszt"] == pytest.approx(sum(x["koszt"] for x in wyn))
    poz = [p for p in w["kpir"]["pozycje"] if p["opis"].startswith(mag.WYNAJEM)]
    assert len(poz) == 1 and poz[0]["pozostale"] < w["magazyn"]["wynajem"]["koszt"]   # netto – VAT w rejestrze
    assert not any("magazynowania" in p["opis"] for p in w["kpir"]["pozycje"])
    assert w["magazyn"]["sanepid"] is not None
    u = w["uzgodnienie"]
    assert (u["roznica"], u["roznica_kpir"], u["roznica_rachunku"]) == (0, 0, 0)


@pytest.fixture
def pewny_bank(monkeypatch):
    """Bank żywności zawsze dzwoni, gdy zapas jest duży."""
    oryginal = mag.bank

    def bank(dane):
        b = copy.deepcopy(oryginal(dane))
        b["zasady"]["szansa"] = 1.0
        return b

    monkeypatch.setattr(mag, "bank", bank)


def test_bank_zywnosci(pewny_bank):
    g = _gra()
    _runda(g, A=_lokal("centrum_3"))
    # w czwartek rundy 2 dużo hummusu (7 dni) – w rundzie 3 zostaje z krótkim terminem
    s = _runda(g, A={"zamowienia": [{"dostawca": DOSTAWCA, "zasob": "Hummus", "jakosc": 2, "ilosc": 80, "dzien": 3}]})
    f = s.firmy["A"]
    assert mag.wartosc_zapasu(g.dane, f, 3) >= mag.bank(g.dane)["zasady"]["prog_zl"]
    assert [h.historia for h in zd.aktywne(g.dane, f, 3, g.konfiguracja["ziarno"])][-1] == "bank_zywnosci"
    przed = sum(p.ilosc for p in f.partie if p.zasob == "Hummus")
    s = _runda(g, A={"zdarzenia": {"bank_zywnosci": "oddaj"}})
    sc = next(x for x in s.wyniki[3]["A"]["zdarzenia"]["sceny"] if x["historia"] == "bank_zywnosci")
    assert sc["opcja"] == "oddaj" and sc["oddane"] > 0 and "{" not in sc["tekst"] and sc["park"] is None
    straty = [x for x in s.wyniki[3]["A"]["swiezosc"]["straty"] if x["powod"] == "bank"]
    assert straty and sum(x["ilosc"] for x in straty) == pytest.approx(przed)
    assert not [p for p in s.firmy["A"].partie if p.zasob == "Hummus" and p.runda < 3]
    assert any(e.typ == "popyt" and e.wartosc > 1 for e in s.firmy["A"].efekty)
    assert any(h.historia == "bank_zywnosci" for h in s.firmy["A"].historie)    # podziękowanie w następnej rundzie


def test_bank_zywnosci_zostaw(pewny_bank):
    g = _gra()
    _runda(g, A=_lokal("centrum_3"))
    _runda(g, A={"zamowienia": [{"dostawca": DOSTAWCA, "zasob": "Hummus", "jakosc": 2, "ilosc": 80, "dzien": 3}]})
    s = _runda(g, A={})
    sc = next(x for x in s.wyniki[3]["A"]["zdarzenia"]["sceny"] if x["historia"] == "bank_zywnosci")
    assert sc["opcja"] == "zostaw" and "oddane" not in sc
    assert not [x for x in s.wyniki[3]["A"]["swiezosc"]["straty"] if x["powod"] == "bank"]


def test_bez_zapasu_bez_banku(pewny_bank):
    g = _gra()
    s = _runda(g, A=_lokal("centrum_3"))
    assert not mag.startuje(g.dane, s.firmy["A"], 2, g.konfiguracja["ziarno"])
