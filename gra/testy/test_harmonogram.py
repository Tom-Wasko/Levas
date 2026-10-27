"""Harmonogram odblokowań w grze z lokalami (F4.3): zakładki i elementy mapy w tygodniach z danych, zmiany mistrza
gry dla jednej gry (bez zmiany wspólnych danych), widok dla panelu MG i strony drużyny."""

import pytest
from test_lokale import _gra

from silnik import harmonogram as hm
from silnik import rynek_pracy as rp
from silnik.dane import dane_domyslne
from silnik.gra import Gra

JSON = "application/json"


def test_domyslny_harmonogram():
    dane = dane_domyslne()
    g = _gra()
    revas = dane.katalog_ofert["rundy"]["odblokowanie"]
    ukryte = {"marketing_tradycyjny", "marketing_internetowy"}   # w grze z lokalami marketing to agencje na mieście
    for r in range(1, 9):
        stare = {k for t, ks in revas.items() if int(t) <= r for k in ks} - ukryte
        assert g.dane.odblokowane(r) == stare, r
    assert hm.baza(g.dane) is dane and g.dane.nadpisane_rundy == {}
    assert all(e["tydzien"] == e["domyslny"] for e in hm.widok(g.dane, 1))


def test_zmiany_mistrza_gry():
    dane = dane_domyslne()
    el = hm.elementy(dane)
    hh = next(k for k in el if k.startswith("rekrutacja_") and el[k]["tydzien"] > 2)
    g = _gra(odblokowanie={"handel": 2, hh: 2, "hr_szkolenia": 3})
    assert g.dane.nadpisane_rundy == {"handel": 2, hh: 2, "hr_szkolenia": 3}
    assert g.dane.zdarzenia["handel"]["handel"]["od_rundy"] == 2
    assert rp.kanaly(g.dane, 2)[hh.removeprefix("rekrutacja_")]["dostepny"]
    assert "hr_szkolenia" in g.dane.odblokowane(3) and "hr_szkolenia" not in g.dane.odblokowane(2)
    # wspólne dane bez zmian
    assert dane.zdarzenia["handel"]["handel"]["od_rundy"] == el["handel"]["tydzien"]
    assert not rp.kanaly(dane, 2)[hh.removeprefix("rekrutacja_")]["dostepny"]
    # zapis i kopia gry zachowują zmiany
    g2 = Gra(g.do_slownika()["konfiguracja"], g.do_slownika()["decyzje"])
    assert g2.dane.nadpisane_rundy == g.dane.nadpisane_rundy and g.kopia().dane.nadpisane_rundy == g.dane.nadpisane_rundy
    # w trakcie gry: tylko przyszłe elementy, nie wcześniej niż bieżący tydzień
    for _ in range(2):
        g.przelicz(wymus=True)
    assert g.runda == 3
    for zle in ({"handel": 5}, {"nieznany": 4}, {"karta_wynikow": 2}, {"promocje": 9 + 1}, {"wypadki": "x"}):
        with pytest.raises(ValueError):
            g.ustaw_odblokowanie(zle)
    g.ustaw_odblokowanie({"wypadki": 9, "hr_szkolenia": el["hr_szkolenia"]["tydzien"]})   # 9 = wyłączone (8 rund)
    assert g.konfiguracja["odblokowanie"] == {"handel": 2, hh: 2, "wypadki": 9}
    assert g.dane.zdarzenia["losowe"]["zasady"]["od_rundy"] == 9
    w = {e["klucz"]: e for e in hm.widok(g.dane, g.runda)}
    assert w["wypadki"]["tydzien"] == 9 and not w["wypadki"]["odblokowany"] and w["handel"]["odblokowany"]


@pytest.mark.django_db
def test_api_prowadzenie(client):
    d = {"nazwa": "Klasa", "ziarno": "7", "liczba_rund": 6, "firmy": [{"nazwa": "A", "bot": None}],
         "odblokowanie": {"handel": 3}}
    gra = client.post("/api/gry", d, content_type=JSON).json()["id"]
    p = client.get(f"/api/gry/{gra}/mg").json()["prowadzenie"]["odblokowanie"]
    assert {e["klucz"]: e["tydzien"] for e in p}["handel"] == 3
    assert client.post("/api/gry", {**d, "odblokowanie": {"handel": 99}}, content_type=JSON).status_code == 400
    r = client.post(f"/api/gry/{gra}/prowadzenie", {"odblokowanie": {"promocje": 4}}, content_type=JSON)
    assert r.status_code == 200
    assert client.post(f"/api/gry/{gra}/prowadzenie", {"odblokowanie": {"zle": 4}}, content_type=JSON).status_code == 400
    assert client.post(f"/api/gry/{gra}/prowadzenie", {"odblokowanie": [1]}, content_type=JSON).status_code == 400
    p = client.get(f"/api/gry/{gra}/mg").json()["prowadzenie"]["odblokowanie"]
    assert {e["klucz"]: e["tydzien"] for e in p}["promocje"] == 4
    v = client.get(f"/api/gry/{gra}/widok/A").json()
    assert v["harmonogram"]["promocje"] == 4 and v["harmonogram"]["handel"] == 3
