"""Eventy w parkach (F3b.1): ta sama historia dla wszystkich drużyn, reakcje kosztują czas, gotówkę i porcje, ciąg
dalszy w kolejnych rundach, skutki (popyt, czas właściciela, kandydat tylko dla jednej drużyny)."""

import pytest
from pomocnicze import _gra, _lokal, _runda

from silnik.decyzje import kandydaci_firmy
from silnik.model import Efekt, Firma
from silnik.swiat import zdarzenia as zd

JSON = "application/json"


@pytest.fixture
def zbyszek(monkeypatch):
    """W rundzie 2 zaczyna się historia pana Zbyszka, potem w parkach spokój."""
    oryginal = zd.eventy_parku
    monkeypatch.setattr(zd, "eventy_parku", lambda dane, ziarno, r: ["pan_zbyszek"] if r == 2 and oryginal(dane, ziarno, r) else [])


def _sceny(s, r, firma):
    return s.wyniki[r][firma]["zdarzenia"]["sceny"]


def test_dane_historii():
    g = _gra()
    hs = g.dane.zdarzenia["parki"]["historie"]
    komiczne = sum(not h["powazna"] for h in hs) / len(hs)
    assert 0.7 <= komiczne <= 0.9   # notatka „Zdarzenia i historie”: w znaczącej większości komiczne
    parki = {b["id"] for b in g.dane.mapa["budynki"] if b["zakladka"] == "zdarzenia"}
    assert {h["park"] for h in hs} <= parki


def test_kolejnosc_bez_powtorzen():
    """P9: co rundę 3–4 różne historie; zanim któraś się powtórzy, przejdą wszystkie."""
    g = _gra()
    z, n = zd.zasady(g.dane), len(zd.historie_parkow(g.dane))
    ziarno = g.konfiguracja["ziarno"]
    assert zd.eventy_parku(g.dane, ziarno, z["od_rundy"] - 1) == []
    rundy = [zd.eventy_parku(g.dane, ziarno, r) for r in range(z["od_rundy"], z["od_rundy"] + 12)]
    assert all(3 <= len(e) <= 4 and len(set(e)) == len(e) for e in rundy)
    assert {len(e) for e in rundy} == {3, 4}
    kolejno = [h for e in rundy for h in e]
    assert len(set(kolejno[:n])) >= n - 3   # talia: pierwsza powtórka najwcześniej na styku talii
    assert set(kolejno[:n + 3]) == set(zd.historie_parkow(g.dane))
    assert rundy[0] == zd.eventy_parku(g.dane, ziarno, z["od_rundy"])   # deterministycznie


def test_opcje_po_2_do_5_godzin():
    g = _gra()
    czasy = {o["koszt"]["czas"] for h in zd.historie_parkow(g.dane).values() for sc in h["sceny"].values()
             for o in sc["opcje"]}
    assert czasy - {0} and min(czasy - {0}) >= 2 and max(czasy) <= 5


def test_ta_sama_historia_dla_wszystkich_i_ciag_dalszy(zbyszek):
    g = _gra()
    _runda(g, A=_lokal("centrum_3"), B=_lokal("dworzec_1"))
    s = _runda(g, A={"zdarzenia": {"pan_zbyszek": "kebab"}}, B={})
    a, b = _sceny(s, 2, "A")[0], _sceny(s, 2, "B")[0]
    assert a["historia"] == b["historia"] == "pan_zbyszek"
    assert a["opcja"] == "kebab" and not a["domyslna"] and a["ciag_dalszy"] == 4
    assert b["domyslna"] and b["ciag_dalszy"] is None and not s.firmy["B"].historie
    assert [(h.scena, h.runda) for h in s.firmy["A"].historie] == [("wizyta", 4)]
    assert any(p["opis"].startswith("Porcje jedzenia") for p in s.wyniki[2]["A"]["rachunek"])
    assert s.wyniki[2]["A"]["czas_wlasciciela"]["wykorzystane"] >= 1
    s = _runda(g, A={}, B={})
    assert not _sceny(s, 3, "A")
    # runda 4: pan Zbyszek przychodzi do lokalu – można go zatrudnić; kandydat tylko dla drużyny A
    s = _runda(g, A={"zdarzenia": {"pan_zbyszek": "zatrudnij"}}, B={})
    assert _sceny(s, 4, "A")[0]["scena"] == "wizyta" and not s.firmy["A"].historie
    k = [k for k in s.kandydaci if k.get("tylko_dla")]
    assert len(k) == 1 and k[0]["tylko_dla"] == "A"
    assert k[0] in kandydaci_firmy(s.kandydaci, s.firmy["A"])
    assert k[0] not in kandydaci_firmy(s.kandydaci, s.firmy["B"])


def test_brak_czasu_wlasciciela(zbyszek, monkeypatch):
    g = _gra()
    _runda(g, A=_lokal("centrum_3"))
    pula = g.dane.z["operacje"]["czas_wlasciciela"]
    monkeypatch.setattr(zd, "efekty_czasu", lambda f, r: [Efekt(typ="czas", wartosc=pula, od_rundy=r, do_rundy=r, opis="Test")])
    s = _runda(g, A={"zdarzenia": {"pan_zbyszek": "kebab"}})
    sc = _sceny(s, 2, "A")[0]
    assert sc["opcja"] == "idz_dalej" and sc["domyslna"]
    assert any(b["poziom"] == "czerwony" and b["zakladka"] == "zdarzenia" for b in s.wyniki[2]["A"]["lista_bledow"])


def test_skutki_popytu_i_czasu():
    f = Firma(nazwa="X", gotowka=0)
    zd._skutek(f, {"typ": "popyt", "mnoznik": 1.1, "rund": 2, "opis": "Sława"}, "h", 5, None, None, [])
    zd._skutek(f, {"typ": "czas", "godziny": 3, "rund": 2, "opis": "Katar"}, "h", 5, None, None, [])
    assert [round(zd.mnoznik_popytu(f, r), 3) for r in (4, 5, 6, 7)] == [1, 1.1, 1.1, 1]
    assert [len(zd.efekty_czasu(f, r)) for r in (5, 6, 7, 8)] == [0, 1, 1, 0]   # czas – od następnej rundy


def test_efekt_czasu_zmniejsza_pule(zbyszek, monkeypatch):
    g = _gra()
    _runda(g, A=_lokal("centrum_3"))
    monkeypatch.setattr(zd, "efekty_czasu", lambda f, r: [Efekt(typ="czas", wartosc=4, od_rundy=r, do_rundy=r, opis="Katar")])
    s = _runda(g, A={})
    C = s.wyniki[2]["A"]["czas_wlasciciela"]
    assert any(p["opis"] == "Katar" and p["godziny"] == 4 for p in C["pozycje"]) and C["wykorzystane"] >= 4


def test_bot_reaguje(zbyszek):
    g = _gra(("A", None), ("B", "zrownowazony"))
    s = _runda(g, A=_lokal("centrum_3"))
    s = _runda(g, A={})
    assert _sceny(s, 2, "B")[0]["opcja"] in {"kebab", "pieniadze", "idz_dalej"}


def test_widok_api(client, zbyszek):
    d = {"nazwa": "Parki", "ziarno": "5", "liczba_rund": 6, "firmy": [{"nazwa": "A", "bot": None}]}
    gra = client.post("/api/gry", d, content_type=JSON).json()["id"]
    v = client.get(f"/api/gry/{gra}/widok/A").json()
    client.put(f"/api/gry/{gra}/decyzje/A", {**v["decyzje"], **_lokal("centrum_3")}, content_type=JSON)
    client.post(f"/api/gry/{gra}/przelicz")
    v = client.get(f"/api/gry/{gra}/widok/A").json()
    Z = v["zdarzenia"]
    assert [s["historia"] for s in Z["aktywne"]] == ["pan_zbyszek"] and Z["aktywne"][0]["nowa"]
    assert any(b["poziom"] == "niebieski" and b["zakladka"] == "zdarzenia" for b in v["lista_bledow"])
    r = client.put(f"/api/gry/{gra}/decyzje/A", {**v["decyzje"], "zdarzenia": {"pan_zbyszek": "kebab"}}, content_type=JSON)
    assert r.status_code == 200
    v = client.get(f"/api/gry/{gra}/widok/A").json()
    assert not any(b["zakladka"] == "zdarzenia" for b in v["lista_bledow"])
    assert any(p["zakladka"] == "zdarzenia" for p in v["czas_wlasciciela"]["pozycje"])


pytestmark = pytest.mark.django_db
