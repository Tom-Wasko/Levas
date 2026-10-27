"""Limity (F3a.15): najwyżej 3 nowych pracowników na rundę i nowy lokal co 3 rundy – zapis decyzji z przekroczeniem
jest odrzucony, lista błędów mówi, ile zostało i od kiedy można wziąć kolejny lokal."""

import pytest
from test_lokale import _gra, _lokal, _runda

from silnik import limity as lm
from silnik import rynek_pracy as rp

pytestmark = pytest.mark.django_db

JSON = "application/json"


@pytest.fixture
def gra(client):
    d = {"nazwa": "Limity", "ziarno": "3", "liczba_rund": 8,
         "firmy": [{"nazwa": "A", "bot": None}, {"nazwa": "B", "bot": None}]}
    return client.post("/api/gry", d, content_type=JSON).json()["id"]


def _widok(client, gra, firma="A"):
    return client.get(f"/api/gry/{gra}/widok/{firma}").json()


def _zapisz(client, gra, d, firma="A"):
    return client.put(f"/api/gry/{gra}/decyzje/{firma}", d, content_type=JSON)


def _zatrudnij(v, n):
    kucharze = [k for k in v["kandydaci"] if k["zawod"] == "Kucharz"]
    return [{"kandydat": k["id"], "typ": "kuchnia", "nr": i + 1, "pensja": 5000} for i, k in enumerate(kucharze[:n])]


def _bledy(v, poziom):
    return [b["tekst"] for b in v["lista_bledow"] if b["poziom"] == poziom]


def test_naruszenia_w_silniku():
    g = _gra()
    limit = rp.ustawienia(g.dane)["limit_nowych"]
    s = _runda(g, A=_lokal("centrum_3"))
    f = s.firmy["A"]
    zatr = [{"kandydat": f"k{i}"} for i in range(limit)]
    assert lm.naruszenia(g.dane, f, {"zatrudnij": zatr}, 2) == []
    # oferta podkupienia liczy się do limitu; „podkupienie” własnego pracownika – nie
    assert lm.naruszenia(g.dane, f, {"zatrudnij": zatr, "podkup": [{"pracownik": "p", "firma": "A"}]}, 2) == []
    za_duzo = lm.naruszenia(g.dane, f, {"zatrudnij": zatr, "podkup": [{"pracownik": "p", "firma": "B"}]}, 2)
    assert len(za_duzo) == 1 and f"najwyżej {limit} nowych" in za_duzo[0]
    co = g.dane.mapa["zasady"]["nowy_lokal_co_rund"]
    assert "co 3 rundy" in lm.naruszenia(g.dane, f, _lokal("dworzec_1"), 2)[0]
    from silnik.lokale import ODPOCZYNEK  # P8: zamiast suchego limitu – właściciel musi odpocząć
    assert lm.naruszenia(g.dane, f, _lokal("dworzec_1"), 2)[0].startswith(ODPOCZYNEK[2 % len(ODPOCZYNEK)])
    assert lm.naruszenia(g.dane, f, _lokal("dworzec_1"), 1 + co) == []
    assert lm.naruszenia(g.dane, f, {"lokal": {"id": ""}}, 2) == []   # anulowany wybór


def test_zapis_ponad_limit_pracownikow_odrzucony(client, gra):
    v = _widok(client, gra)
    limit = v["agencja"]["limit"]
    d = {**v["decyzje"], **_lokal("centrum_3"), "stanowiska": {"kuchnia": 3}}
    r = _zapisz(client, gra, {**d, "zatrudnij": _zatrudnij(v, limit + 1)})
    assert r.status_code == 400 and f"najwyżej {limit} nowych pracowników" in r.json()["blad"]
    assert not _widok(client, gra)["decyzje"].get("zatrudnij")   # nic się nie zapisało
    v = _zapisz(client, gra, {**d, "zatrudnij": _zatrudnij(v, limit)}).json()
    assert len(v["decyzje"]["zatrudnij"]) == limit
    assert any("Wykorzystany limit nowych pracowników" in t for t in _bledy(v, "niebieski"))


def test_zapis_lokalu_przed_terminem_odrzucony(client, gra):
    v = _widok(client, gra)
    assert _zapisz(client, gra, {**v["decyzje"], **_lokal("centrum_3")}).status_code == 200
    client.post(f"/api/gry/{gra}/przelicz")
    v = _widok(client, gra)
    assert v["lokale"]["nowy_od"] == 4
    assert any("najwcześniej w rundzie 4" in t for t in _bledy(v, "niebieski"))
    assert "najwcześniej w rundzie 4" in v["lokale"]["odpoczynek"]   # P8: komunikat z żartem
    r = _zapisz(client, gra, {**v["decyzje"], **_lokal("dworzec_1")})
    assert r.status_code == 400 and "najwcześniej w rundzie 4" in r.json()["blad"]
    # inna drużyna bez lokalu może wziąć lokal od razu
    assert _zapisz(client, gra, {**_widok(client, gra, "B")["decyzje"], **_lokal("dworzec_1")}, "B").status_code == 200
    for _ in range(2):
        client.post(f"/api/gry/{gra}/przelicz")
    v = _widok(client, gra)
    assert _zapisz(client, gra, {**v["decyzje"], **_lokal("stare_miasto_1")}).status_code == 200
