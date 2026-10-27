"""Wypadki w lokalu i ubezpieczyciel (F3b.5): historie jednej drużyny, szkody, polisy z karencją, boty, widok API."""

import copy

import pytest
import yaml
from pydantic import ValidationError
from test_lokale import _gra, _lokal, _runda

from silnik import awarie as aw
from silnik.dane import KATALOG_DANYCH, dane_domyslne
from silnik.finanse import Ksiega, Rachunek
from silnik.schematy import PlikParkow, PlikWypadkow

RUNDY = range(2, 9)


@pytest.fixture
def pewne_wypadki(monkeypatch):
    """Wypadek zaczyna się co rundę, gdy żaden nie trwa, już od rundy 2."""
    oryginal = aw.zasady
    monkeypatch.setattr(aw, "zasady", lambda dane: {**oryginal(dane), "szansa": 1.0, "od_rundy": 2})


def test_szansa_rosnie_bez_wypadku_i_wraca_po_wypadku():
    """P11: +4 pp. za każdą rundę bez wypadku (od otwarcia lokalu / od rundy wypadków), sufit, reset po wypadku."""
    from silnik.model import Firma, Lokal
    dane = dane_domyslne()
    z = aw.zasady(dane)
    assert z["przyrost"] == pytest.approx(0.04) and z["szansa"] < z["szansa_max"] <= 0.4
    od = z["od_rundy"]
    f = Firma(nazwa="X", gotowka=0, lokale=[Lokal(id="centrum_3", forma="najem", od_rundy=1, dziala_od=1)])
    assert aw.szansa_wypadku(dane, f, od) == pytest.approx(z["szansa"])
    assert aw.szansa_wypadku(dane, f, od + 3) == pytest.approx(z["szansa"] + 3 * z["przyrost"])
    assert aw.szansa_wypadku(dane, f, od + 50) == pytest.approx(z["szansa_max"])
    f.wypadki = {"x": od + 5}
    assert aw.szansa_wypadku(dane, f, od + 5) == pytest.approx(z["szansa"] + 5 * z["przyrost"])   # wypadek z tej rundy nie liczy się
    assert aw.szansa_wypadku(dane, f, od + 6) == pytest.approx(z["szansa"])                     # reset
    assert aw.szansa_wypadku(dane, f, od + 8) == pytest.approx(z["szansa"] + 2 * z["przyrost"])
    f2 = Firma(nazwa="Y", gotowka=0, lokale=[Lokal(id="centrum_3", forma="najem", od_rundy=od, dziala_od=od + 4)])           # późne otwarcie
    assert aw.szansa_wypadku(dane, f2, od + 4) == pytest.approx(z["szansa"])


def _surowe(plik):
    return yaml.safe_load((KATALOG_DANYCH / "zdarzenia" / plik).read_text(encoding="utf-8"))


def test_dane_wypadkow():
    dane = dane_domyslne()
    hs = aw.historie(dane)
    assert len(hs) >= 8 and all(h["park"] is None for h in hs.values())
    assert sum(not h["powazna"] for h in hs.values()) / len(hs) >= 0.7   # w znaczącej większości komiczne
    assert set(aw.ubezpieczyciel(dane)["polisy"]) == {"lokal", "sprzet", "oc"}
    assert aw.ubezpieczyciel(dane)["budynek"] in {b["id"] for b in dane.mapa["budynki"]}
    # szkoda: polisa musi istnieć; w parkach szkód nie ma
    w = _surowe("losowe.yaml")
    w["historie"][0]["sceny"][w["historie"][0]["start"]].setdefault("skutki", []).append({"typ": "szkoda", "opis": "x", "kwota": 10, "polisa": "zycie"})
    with pytest.raises(ValidationError):
        PlikWypadkow.model_validate(w)
    p = _surowe("parki.yaml")
    p["historie"][0]["sceny"][p["historie"][0]["start"]].setdefault("skutki", []).append({"typ": "szkoda", "opis": "x", "kwota": 10})
    with pytest.raises(ValidationError):
        PlikParkow.model_validate(p)


def test_wypadki_w_grze(pewne_wypadki):
    """Wypadki tylko u drużyny z lokalem, naraz jeden, bez powtórek; szkody w KPiR bez polis – bez odszkodowań."""
    g = _gra(rund=10)
    _runda(g, A=_lokal("centrum_3"))
    for _ in RUNDY:
        s = _runda(g)
    fa, fb = s.firmy["A"], s.firmy["B"]
    assert len(fa.wypadki) >= 2 and not fb.wypadki and not fa.polisy
    sceny = [(r, x) for r in RUNDY for x in s.wyniki[r]["A"]["zdarzenia"]["sceny"] if x["wypadek"]]
    assert {x["historia"] for _, x in sceny} == set(fa.wypadki)
    assert all(sum(rr == r for rr, _ in sceny) <= 1 for r in RUNDY)   # najwyżej jeden otwarty wypadek
    for r in RUNDY:
        u = s.wyniki[r]["A"]["ubezpieczenia"]
        kpir = sum(p["pozostale"] for p in s.wyniki[r]["A"]["kpir"]["pozycje"] if p["opis"].startswith("Szkoda – "))
        assert kpir == pytest.approx(u["szkody_razem"]) and u["odszkodowania"] == 0 and u["skladki"] == 0
        assert all(not x["ubezpieczona"] and x["powod"] for x in u["szkody"])
        assert not s.wyniki[r]["B"]["ubezpieczenia"]["szkody"]
    assert any(s.wyniki[r]["A"]["ubezpieczenia"]["szkody"] for r in RUNDY)


def test_polisy_skladki_i_odszkodowania(pewne_wypadki):
    """Polisy kupione w rundzie 2 chronią od rundy 3: składki co rundę, odszkodowanie (szkoda − franszyza) × pokrycie."""
    g = _gra(rund=10)
    _runda(g, A=_lokal("centrum_3"))
    s = _runda(g, A={"polisy": ["lokal", "sprzet", "oc", "lokal"]})
    assert s.firmy["A"].polisy == {"lokal": 3, "sprzet": 3, "oc": 3}
    for _ in range(3, 9):
        s = _runda(g)
    U = aw.ubezpieczyciel(g.dane)
    for r in RUNDY:
        w = s.wyniki[r]["A"]
        sk = [p for p in w["kpir"]["pozycje"] if p["opis"].startswith(aw.SKLADKA)]
        platne = [p for p in w["ubezpieczenia"]["polisy"] if p["skladka"] > 0]   # sprzęt: składka od majątku (tu 0)
        assert len(w["ubezpieczenia"]["polisy"]) == 3 and len(sk) == len(platne) >= 2 and w["ubezpieczenia"]["skladki"] == pytest.approx(sum(p["pozostale"] for p in sk))   # zwolnione z VAT
        odsz = sum(p["przychod_pozostaly"] for p in w["kpir"]["pozycje"] if p["opis"].startswith(aw.ODSZKODOWANIE))
        assert odsz == pytest.approx(w["ubezpieczenia"]["odszkodowania"])
        for x in w["ubezpieczenia"]["szkody"]:
            poczatek = s.firmy["A"].wypadki[x["historia"]]
            if x["polisa"] and poczatek >= 3:
                p = U["polisy"][x["polisa"]]
                assert x["ubezpieczona"] and x["odszkodowanie"] == pytest.approx(round(max(0, x["kwota"] - p["franszyza"]) * p["pokrycie"], 2))
            else:
                assert not x["ubezpieczona"] and x["odszkodowanie"] == 0
    assert sum(s.wyniki[r]["A"]["ubezpieczenia"]["odszkodowania"] for r in RUNDY) > 0
    # wypowiedzenie: bez składek od następnej rundy
    s = _runda(g, A={"polisy": ["oc"]})
    assert s.firmy["A"].polisy == {"oc": 3} and s.wyniki[9]["A"]["ubezpieczenia"]["wypowiedziane"] == ["lokal", "sprzet"]


def test_szkoda_karencja_i_limit():
    g = _gra()
    s = _runda(g, A=_lokal("centrum_3"))
    dane, f = g.dane, copy.deepcopy(s.firmy["A"])
    h = next(iter(aw.historie(dane).values()))
    f.polisy, f.wypadki = {"sprzet": 5}, {h["id"]: 4}
    ks, rach = Ksiega(vat=dane.podatki["vat"]), Rachunek()
    x = aw.szkoda(dane, f, {"opis": "Ekspres", "kwota": 10 ** 6, "polisa": "sprzet"}, h, 5, ks, rach)
    assert x["kwota"] == aw.zasady(dane)["max_strata"] and not x["ubezpieczona"] and "od rundy 5" in x["powod"]
    f.wypadki[h["id"]] = 5
    x = aw.szkoda(dane, f, {"opis": "Ekspres", "kwota": 1000, "polisa": "sprzet"}, h, 6, ks, rach)
    p = aw.ubezpieczyciel(dane)["polisy"]["sprzet"]
    assert x["ubezpieczona"] and x["odszkodowanie"] == pytest.approx((1000 - p["franszyza"]) * p["pokrycie"])
    x = aw.szkoda(dane, f, {"opis": "Ząb", "kwota": 500, "polisa": "oc"}, h, 6, ks, rach)
    assert not x["ubezpieczona"] and x["powod"].startswith("brak polisy")
    # bez lokalu i z nieznaną polisą – uwagi, bez polis
    info = aw.ustaw(dane, copy.deepcopy(s.firmy["B"]), {"polisy": ["oc", "zycie"]}, 2, ks, rach)
    assert info["polisy"] == [] and len(info["uwagi"]) == 2 and len(aw.bledy(info)) == 2


def test_boty_kupuja_polisy_wg_strategii():
    g = _gra(("Prem", "premium"), ("Tani", "tani"))
    for _ in range(3):
        s = g.przelicz(wymus=True)
    assert set(s.firmy["Prem"].polisy) == set(dane_domyslne().boty["strategie"]["premium"]["polisy"])
    assert s.firmy["Tani"].polisy == {}


def test_widok_api_i_gra_bez_lokali():
    from api.prezentacja import widok
    g = _gra()
    _runda(g, A=_lokal("centrum_3"))
    g.ustaw_decyzje("A", {"polisy": ["lokal", "zycie"]})
    v = widok(g, "A")
    U = v["ubezpieczenia"]
    assert [o["rodzaj"] for o in U["oferta"]] == ["lokal", "sprzet", "oc"] and U["posiadane"] == {"lokal": 3}
    assert U["decyzja"]["nowe"] == ["lokal"] and U["decyzja"]["skladki"] > 0
    assert any(p["opis"].startswith(aw.SKLADKA) for p in v["koszty_decyzji"])
    assert any(b["zakladka"] == aw.ZAKLADKA for b in v["lista_bledow"])
