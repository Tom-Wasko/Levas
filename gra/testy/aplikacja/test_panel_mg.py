"""Panel mistrza gry: nowa gra z kapitałem i botami, podgląd drużyn, zamknięcie i cofnięcie rundy."""

import pytest
from django.contrib.staticfiles import finders

pytestmark = pytest.mark.django_db

DRUZYNY = ["Drużyna 1", "Drużyna 2"]


def _nowa(client, **zmiany):
    d = {
        "nazwa": "Klasa",
        "ziarno": "7",
        "kapital_startowy": "50000",
        "firmy": [{"nazwa": n, "bot": None} for n in DRUZYNY] + [{"nazwa": "Bot", "bot": "tani"}],
    } | zmiany
    return client.post("/api/gry", d, content_type="application/json")


def _przeglad(client, id_):
    r = client.get(f"/api/gry/{id_}/mg")
    assert r.status_code == 200
    return r.json()


def test_strony_panelu(client):
    assert 'value="18"' in client.get("/mg/").content.decode()
    id_ = _nowa(client).json()["id"]
    assert client.get(f"/mg/gra/{id_}").status_code == 200
    assert client.get("/mg/gra/nie-ma-takiej").status_code == 404
    assert finders.find("mg/mg.js") and finders.find("mg/mg.css")


def test_kapital_startowy(client):
    assert _nowa(client, kapital_startowy="abc").status_code == 400
    assert _nowa(client, kapital_startowy="0").status_code == 400
    id_ = _nowa(client).json()["id"]
    p = _przeglad(client, id_)
    assert p["gra"]["kapital"] == 50000
    assert {f["nazwa"]: f["gotowka"] for f in p["firmy"]} == {"Drużyna 1": 50000, "Drużyna 2": 50000, "Bot": 50000}
    # bez kapitału – z danych gry
    id2 = _nowa(client, kapital_startowy="").json()["id"]
    assert _przeglad(client, id2)["gra"]["kapital"] == 40000


def test_prowadzenie_rundy(client):
    id_ = _nowa(client).json()["id"]
    p = _przeglad(client, id_)
    assert p["gra"]["runda"] == 1 and p["gra"]["brakujace"] == DRUZYNY and not p["historia"]
    assert [f["wyslane"] for f in p["firmy"]] == [False, False, None]  # bot nie wysyła decyzji
    client.post(f"/api/gry/{id_}/wyslij/Drużyna 1", {"wyslane": True}, content_type="application/json")
    p = _przeglad(client, id_)
    assert p["gra"]["brakujace"] == ["Drużyna 2"] and p["firmy"][0]["wyslane"]
    # mistrz gry zamyka rundę bez decyzji drużyny 2
    assert client.post(f"/api/gry/{id_}/przelicz").json()["runda"] == 2
    p = _przeglad(client, id_)
    assert p["gra"]["runda"] == 2 and p["gra"]["brakujace"] == DRUZYNY
    assert [h["runda"] for h in p["historia"]] == [1] and p["historia"][0]["skrot"] == "T1"
    for _ in range(2):
        client.post(f"/api/gry/{id_}/przelicz")
    p = _przeglad(client, id_)
    assert sorted(f["miejsce"] for f in p["firmy"]) == [1, 2, 3]  # ranking od rundy 2
    assert all(f["wynik_skumulowany"] is not None for f in p["firmy"])
    assert client.post(f"/api/gry/{id_}/cofnij").json()["runda"] == 3
    assert len(_przeglad(client, id_)["historia"]) == 2


def test_koniec_kroku_2_cala_gra(client):
    """Jedna drużyna i wszystkie boty grają 18 tygodni; mistrz gry zamyka każdą rundę z przeglądarki."""
    from silnik.dane import dane_domyslne

    boty = [{"nazwa": f"Bot {k}", "bot": k} for k in dane_domyslne().boty["strategie"]]
    id_ = _nowa(client, kapital_startowy="", firmy=[{"nazwa": "Drużyna 1", "bot": None}] + boty).json()["id"]
    for r in range(1, 19):
        assert client.post(f"/api/gry/{id_}/przelicz").json()["runda"] == r + 1
    p = _przeglad(client, id_)
    assert p["gra"]["zakonczona"] and len(p["historia"]) == 18 and p["historia"][-1]["skrot"] == "T18"
    assert client.post(f"/api/gry/{id_}/przelicz").status_code == 400  # gra zakończona


def test_domyslny_kredyt_i_przycisk_zamow_brakujace(client):
    """Domyślnie kredyt „na bieżąco” i bez przycisku „Zamów brakujące”; mistrz gry włącza go w trakcie gry."""
    id_ = _nowa(client).json()["id"]
    p = _przeglad(client, id_)
    assert p["gra"]["kredyt_odnawialny"] == "na_biezaco" and p["gra"]["auto_zamowienia"] is False
    gracz = lambda: client.get(f"/api/gry/{id_}/widok/Drużyna 1").json()["gra"]["auto_zamowienia"]  # noqa: E731
    assert gracz() is False
    r = client.post(f"/api/gry/{id_}/prowadzenie", {"auto_zamowienia": True}, content_type="application/json")
    assert r.json()["gra"]["auto_zamowienia"] is True and gracz() is True
    assert _przeglad(client, _nowa(client, auto_zamowienia=True).json()["id"])["gra"]["auto_zamowienia"] is True


def test_miejsce_na_pulpicie_jak_ranking_mistrza_gry():
    """Z7: pulpit drużyny liczy miejsce ze średniej kart z rund 2…, a nie z karty ostatniej rundy."""
    from api import prezentacja as pr
    from silnik import Gra

    g = Gra.nowa("Z7", [(f"Bot {k}", k) for k in ("tani", "premium", "zrownowazony", "agresywny")], 8, 7)
    inna = False
    for r in range(1, 9):   # po ostatniej rundzie pulpit pokazuje podsumowanie (runda N+1) – jak mistrz gry
        g.przelicz(wymus=True)
        if r < 2:
            continue
        mg = {f["nazwa"]: f.get("miejsce") for f in pr.przeglad_mg(g)["firmy"]}
        assert {n: pr.widok(g, n)["dashboard"]["miejsce"] for n in mg} == mg
        karty = g.stan(r).rynek[r]["karta"]
        inna |= mg != pr.miejsca({n: karty[n] for n in mg})
    assert inna   # w tej grze ranking ostatniej rundy choć raz różni się od skumulowanego


def test_po_koncu_gry_druzyna_widzi_wyniki_ostatniej_rundy():
    """Decyzja autora (Z7): po końcu gry widok domyślny to podsumowanie – wyniki rundy N, bez decyzji."""
    from api import prezentacja as pr
    from silnik import Gra

    g = Gra.nowa("Koniec", [("A", None), ("B", "zrownowazony")], 3, 5)
    for _ in range(3):
        g.przelicz(wymus=True)
    v = pr.widok(g, "A")
    assert g.zakonczona and v["koniec"] and not v["edycja"] and v["runda"] == 4 and v["decyzje"] == {}
    assert v["wyniki"] == g.stan(3).wyniki[3]["A"] and v["dashboard"]["miejsce"] in (1, 2)
    assert not pr.widok(g, "A", 3)["koniec"]   # wcześniejsze rundy – zwykły podgląd
