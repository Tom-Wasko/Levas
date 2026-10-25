"""Widoki Django: strony, API zakładek i zapis gry w bazie (konfiguracja + decyzje)."""

import json

import pytest
from django.contrib.staticfiles import finders
from django.test import Client

from gry import serwisy
from gry.models import Decyzja, Gra, Runda

pytestmark = pytest.mark.django_db

GRACZ = "Moja firma"


def _nowa(client, **zmiany) -> str:
    d = {
        "nazwa": "Test API",
        "liczba_rund": 4,
        "ziarno": "2026",
        "firmy": [{"nazwa": GRACZ, "bot": None}, {"nazwa": "Bot 1", "bot": "zrownowazony"}],
    } | zmiany
    r = client.post("/api/gry", d, content_type="application/json")
    assert r.status_code == 200, r.json()
    return r.json()["id"]


def _url(id_: str, co: str, firma: str = GRACZ) -> str:
    return f"/api/gry/{id_}/{co}/{firma}"


def test_strony_i_statyki(client):
    assert client.get("/").status_code == 200
    id_ = _nowa(client)
    r = client.get(f"/gra/{id_}")
    assert r.status_code == 302 and r["Location"].endswith("/Moja%20firma")
    r = client.get(f"/gra/{id_}/{GRACZ}")
    assert r.status_code == 200 and "csrftoken" in r.cookies
    assert client.get(f"/gra/{id_}/Nikt").status_code == 404
    assert client.get("/gra/nie-ma-takiej").status_code == 404
    # testy działają z DEBUG=False, więc statyki sprawdzamy przez wyszukiwarkę Django
    assert finders.find("app.js") and finders.find("zakladki/index.js")


def test_domyslna_gra_tygodniowa(client):
    strona = client.get("/").content.decode()
    assert 'value="26"' in strona and "100 000 PLN" in strona
    id_ = _nowa(client, liczba_rund="")
    v = client.get(_url(id_, "widok")).json()
    kal = v["gra"]["kalendarz"]
    assert v["gra"]["liczba_rund"] == 26 and kal["rund_w_roku"] == 52 and len(kal["nazwy"]) == 26
    assert v["miesiac"] == kal["nazwy"][0] and kal["nazwy"][0].startswith("Tydzień 1")
    # Levas: drużyna zaczyna bez lokalu i wybiera go na mapie; bez lokali – gotowy lokal na start (jak w REVAS)
    assert v["gra"]["lokale"] and v["stan"]["stanowiska"] == [] and v["lokale"]["oferta"]
    v = client.get(_url(_nowa(client, lokale="nie"), "widok")).json()
    assert not v["gra"]["lokale"] and "lokale" not in v
    assert {s["typ"] for s in v["stan"]["stanowiska"]} == {"kuchnia", "kasa"}


def test_nowa_gra_walidacja(client):
    def blad(firmy):
        r = client.post("/api/gry", {"firmy": firmy}, content_type="application/json")
        return r.status_code, r.json().get("blad", "")

    assert blad([]) == (400, "Podaj różne nazwy firm.")
    assert blad([{"nazwa": "A"}, {"nazwa": "A"}])[0] == 400
    assert blad([{"nazwa": "A", "bot": "tani"}])[1].startswith("Co najmniej jedna")
    assert blad([{"nazwa": "_A"}])[0] == 400
    r = client.post("/api/gry", "nie json", content_type="application/json")
    assert r.status_code == 400


def test_runda_od_decyzji_do_przeliczenia(client):
    id_ = _nowa(client)
    assert [g["id"] for g in client.get("/api/gry").json()] == [id_]
    assert client.get("/api/katalogi").status_code == 200

    v = client.get(_url(id_, "widok")).json()
    assert v["runda"] == 1
    r = client.put(_url(id_, "decyzje"), {"nazwa": "Kebab Test"}, content_type="application/json")
    assert r.status_code == 200
    assert Decyzja.objects.get(runda__gra_id=id_, firma=GRACZ).dane["nazwa"] == "Kebab Test"

    r = client.post(_url(id_, "wyslij"), {"wyslane": True}, content_type="application/json")
    assert r.status_code == 200 and r.json()["przeliczono"] is True
    assert client.get("/api/gry").json()[0]["runda"] == 2
    assert Runda.objects.get(gra_id=id_, numer=1).przeliczona

    assert client.post(f"/api/gry/{id_}/przelicz").json()["runda"] == 3
    assert client.post(f"/api/gry/{id_}/cofnij").json()["runda"] == 2
    assert client.get(_url(id_, "widok") + "?runda=1").json()["runda"] == 1


def test_wyslane_decyzje_czekaja_na_drugiego_gracza(client):
    firmy = [{"nazwa": GRACZ}, {"nazwa": "Druga"}, {"nazwa": "Bot 1", "bot": "tani"}]
    id_ = _nowa(client, firmy=firmy)
    r = client.post(_url(id_, "wyslij"), {"wyslane": True}, content_type="application/json")
    assert r.json()["przeliczono"] is False
    assert client.put(_url(id_, "decyzje"), {}, content_type="application/json").status_code == 400
    client.post(_url(id_, "wyslij"), {"wyslane": False}, content_type="application/json")
    assert client.put(_url(id_, "decyzje"), {}, content_type="application/json").status_code == 200
    assert client.post(f"/api/gry/{id_}/przelicz").json()["runda"] == 2  # mistrz gry wymusza


def test_warianty_i_podglad(client):
    id_ = _nowa(client)
    client.post(f"/api/gry/{id_}/przelicz")
    r = client.put(_url(id_, "warianty"), {"nazwa": "Tanio"}, content_type="application/json")
    assert r.status_code == 200 and r.json()["warianty"] == ["Tanio"]
    assert client.get(_url(id_, "warianty-dane") + "?nazwa=Tanio").status_code == 200
    assert client.get(_url(id_, "warianty-dane") + "?nazwa=Brak").status_code == 404

    r = client.post(
        _url(id_, "podglad"), {"warianty": ["biezace", "Tanio"]}, content_type="application/json"
    )
    assert r.status_code == 200
    assert [w["nazwa"] for w in r.json()["warianty"]] == ["Bieżące decyzje", "Tanio"]

    r = client.delete(_url(id_, "warianty") + "?nazwa=Tanio")
    assert r.json()["warianty"] == []


def test_eksport_import_i_usuwanie(client):
    id_ = _nowa(client)
    client.post(f"/api/gry/{id_}/przelicz")
    r = client.get(f"/api/gry/{id_}/eksport")
    assert r.status_code == 200 and "attachment" in r["Content-Disposition"]
    plik = json.loads(r.content)
    assert plik["decyzje"]["1"]["_przeliczona"] is True

    from django.core.files.uploadedfile import SimpleUploadedFile

    r = client.post("/api/gry/import", {"plik": SimpleUploadedFile("g.json", r.content)})
    nowy = r.json()["id"]
    assert serwisy.wczytaj(nowy).runda == 2
    r = client.post("/api/gry/import", {"plik": SimpleUploadedFile("g.json", b"{}")})
    assert r.status_code == 400

    assert client.delete(f"/api/gry/{id_}").status_code == 200
    assert not Gra.objects.filter(pk=id_).exists()
    assert client.get(_url(id_, "widok")).status_code == 404


def test_odczyt_z_bazy_daje_ten_sam_stan(client):
    """Event sourcing: gra wczytana z bazy (bez pamięci podręcznej) liczy te same wyniki."""
    id_ = _nowa(client)
    client.put(_url(id_, "decyzje"), {"nazwa": "Kebab Test"}, content_type="application/json")
    for _ in range(3):
        client.post(f"/api/gry/{id_}/przelicz")
    przed = client.get(_url(id_, "widok") + "?runda=3").json()
    serwisy._pamiec.clear()
    g = serwisy.wczytaj(id_)
    assert g.runda == 4
    assert client.get(_url(id_, "widok") + "?runda=3").json() == przed


def test_csrf_wymagany_poza_testami(mistrz):
    c = Client(enforce_csrf_checks=True)
    c.force_login(mistrz)
    assert c.post("/api/gry", {}, content_type="application/json").status_code == 403
    c.get("/")
    token = c.cookies["csrftoken"].value
    r = c.post(
        "/api/gry",
        {"firmy": [{"nazwa": "A"}]},
        content_type="application/json",
        headers={"X-CSRFToken": token},
    )
    assert r.status_code == 200
