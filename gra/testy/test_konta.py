"""Konta i role: logowanie wymagane, uczeń widzi tylko swoją drużynę, mistrz gry – wszystko."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client

from gry.models import Druzyna
from konta.role import jest_mg

pytestmark = pytest.mark.django_db

A, B = "Drużyna A", "Drużyna B"


@pytest.fixture
def gra(client):
    d = {
        "nazwa": "Klasa",
        "ziarno": "1",
        "liczba_rund": 4,
        "firmy": [
            {"nazwa": A, "bot": None},
            {"nazwa": B, "bot": None},
            {"nazwa": "Bot", "bot": "tani"},
        ],
    }
    id_ = client.post("/api/gry", d, content_type="application/json").json()["id"]
    return id_


def _dopisz(id_, firma, login):
    d, _ = Druzyna.objects.get_or_create(gra_id=id_, firma=firma)
    d.czlonkowie.add(get_user_model().objects.get(username=login))


def test_bez_logowania(gra):
    c = Client()
    r = c.get("/")
    assert r.status_code == 302 and r["Location"].startswith("/konta/login/?next=/")
    assert c.get(f"/gra/{gra}/{A}").status_code == 302
    assert c.get("/mg/").status_code == 302
    r = c.get(f"/api/gry/{gra}/widok/{A}")
    assert r.status_code == 401 and r.json()["blad"] == "Zaloguj się."
    strona = c.get("/konta/login/")
    assert strona.status_code == 200 and "Zaloguj kontem" not in strona.content.decode()
    assert "Konto zakłada mistrz gry" in strona.content.decode()
    assert c.get("/static/styl.css").status_code in (
        200,
        404,
    )  # statyki bez logowania (404: DEBUG=False)


def test_logowanie_haslem_i_brak_rejestracji():
    call_command("konto", "ola", "--haslo", "tajne-haslo", "--imie", "Ola Nowak")
    c = Client()
    r = c.post("/konta/login/", {"login": "ola", "password": "zle-haslo"})
    assert r.status_code == 200 and "_auth_user_id" not in c.session
    r = c.post("/konta/login/", {"login": "ola", "password": "tajne-haslo"})
    assert r.status_code == 302 and c.session["_auth_user_id"]
    assert "Ola Nowak" in c.get("/").content.decode()
    c.post(
        "/konta/signup/",
        {"username": "intruz", "password1": "Abc12345!x", "password2": "Abc12345!x"},
    )
    assert not get_user_model().objects.filter(username="intruz").exists()
    c.post("/konta/logout/")
    assert c.get("/").status_code == 302


def test_komenda_konto_mistrz_gry():
    call_command("konto", "pani-ania", "--mg", "--haslo", "haslo-mg-1")
    u = get_user_model().objects.get(username="pani-ania")
    assert jest_mg(u) and u.is_staff
    call_command("konto", "pani-ania", "--uczen")
    assert not jest_mg(get_user_model().objects.get(username="pani-ania"))


def test_uczen_nie_odczyta_cudzej_druzyny(gra, uczen):
    ala, bartek, obcy = uczen("ala"), uczen("bartek"), uczen("obcy")
    _dopisz(gra, A, "ala")
    _dopisz(gra, B, "bartek")
    # swoja drużyna: strona, widok, decyzje, wysłanie
    assert ala.get(f"/gra/{gra}/{A}").status_code == 200
    r = ala.get(f"/gra/{gra}")
    assert r.status_code == 302 and r["Location"].endswith("/Dru%C5%BCyna%20A")
    assert ala.get(f"/api/gry/{gra}/widok/{A}").status_code == 200
    assert (
        ala.put(f"/api/gry/{gra}/decyzje/{A}", {}, content_type="application/json").status_code
        == 200
    )
    # cudza drużyna: ani strona, ani API
    assert ala.get(f"/gra/{gra}/{B}").status_code == 403
    for metoda, co in [
        ("get", "widok"),
        ("put", "decyzje"),
        ("post", "wyslij"),
        ("post", "podglad"),
        ("get", "warianty-dane"),
    ]:
        r = getattr(ala, metoda)(
            f"/api/gry/{gra}/{co}/{B}",
            {} if metoda != "get" else None,
            content_type="application/json",
        )
        assert r.status_code == 403, co
        assert r.json()["blad"] == "To nie jest firma Twojej drużyny."
    # zarządzanie grą – tylko mistrz gry
    for metoda, url in [
        ("get", f"/api/gry/{gra}/mg"),
        ("post", f"/api/gry/{gra}/przelicz"),
        ("post", f"/api/gry/{gra}/cofnij"),
        ("get", f"/api/gry/{gra}/eksport"),
        ("delete", f"/api/gry/{gra}"),
        ("post", "/api/gry"),
    ]:
        assert getattr(ala, metoda)(url, content_type="application/json").status_code == 403, url
    assert ala.get("/mg/").status_code == 403 and ala.get(f"/mg/gra/{gra}").status_code == 403
    # lista gier: tylko gry swoich drużyn
    assert [g["id"] for g in ala.get("/api/gry").json()] == [gra]
    assert obcy.get("/api/gry").json() == [] and obcy.get(f"/gra/{gra}").status_code == 403
    assert "Utwórz grę" not in ala.get("/").content.decode()
    # bartek wysyła swoje, ala swoje – runda zamyka się sama
    bartek.post(f"/api/gry/{gra}/wyslij/{B}", {"wyslane": True}, content_type="application/json")
    r = ala.post(f"/api/gry/{gra}/wyslij/{A}", {"wyslane": True}, content_type="application/json")
    assert r.json()["przeliczono"]


def test_mistrz_gry_widzi_wszystko(client, gra):
    assert client.get(f"/gra/{gra}/{B}").status_code == 200
    assert client.get(f"/api/gry/{gra}/mg").status_code == 200
    assert "Utwórz grę" in client.get("/").content.decode()


def test_gra_lokalna_loguje_sama(settings):
    settings.LEVAS_LOKALNIE = True
    r = Client().get("/")
    assert r.status_code == 200 and "Wyloguj" not in r.content.decode()
    assert jest_mg(get_user_model().objects.get(username="lokalny"))
    assert Client(REMOTE_ADDR="10.0.0.7").get("/").status_code == 302  # tylko z tego komputera


def test_przycisk_microsoft_tylko_po_konfiguracji(settings):
    c = Client()
    assert "kontem Microsoft" not in c.get("/konta/login/").content.decode()
    settings.SOCIALACCOUNT_PROVIDERS = {
        "microsoft": {"TENANT": "szkola", "APPS": [{"client_id": "id-testowe", "secret": "x"}]}
    }
    assert "kontem Microsoft" in c.get("/konta/login/").content.decode()


def test_mistrz_gry_zaklada_konta_i_druzyny(django_user_model, gra):
    mg = django_user_model.objects.create_user("pani-ania", password="x")
    call_command("konto", "pani-ania", "--mg")
    c = Client()
    c.force_login(mg)
    for url in [
        "/admin/",
        "/admin/auth/user/add/",
        "/admin/gry/druzyna/add/",
        f"/admin/gry/gra/{gra}/change/",
    ]:
        assert c.get(url).status_code == 200, url
    uczen = Client()
    uczen.force_login(django_user_model.objects.create_user("ala", password="x"))
    assert uczen.get("/admin/").status_code == 302  # uczeń nie wchodzi do panelu administracyjnego
