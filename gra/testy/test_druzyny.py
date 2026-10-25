"""Drużyny 1–4 osób: skład ustala mistrz gry, decyzje drużyny, zamknięcie rundy po decyzjach wszystkich."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from gry.admin import DruzynaForm
from gry.models import Gra
from konta.druzyny import wolny_login

pytestmark = pytest.mark.django_db

DRUZYNY = ["Kebab Ali", "Pita Pan", "Rożen 3B", "Sos i Spółka"]
JSON = "application/json"


@pytest.fixture
def gra(client):
    firmy = [{"nazwa": n, "bot": None} for n in DRUZYNY] + [
        {"nazwa": "Bot tani", "bot": "tani"},
        {"nazwa": "Bot premium", "bot": "premium"},
    ]
    d = {"nazwa": "Klasa 3B", "ziarno": "7", "liczba_rund": 3, "firmy": firmy}
    return client.post("/api/gry", d, content_type=JSON).json()["id"]


def zaloguj(login: str) -> Client:
    c = Client()
    c.force_login(get_user_model().objects.get(username=login))
    return c


def dopisz(client, gra, firma, login):
    return client.post(f"/api/gry/{gra}/druzyny/{firma}", {"dodaj": login}, content_type=JSON)


def test_cztery_druzyny_i_boty_w_jednej_grze(client, gra):
    osoby = [f"Uczeń{i} Klasa" for i in range(8)]
    konta = client.post("/api/konta", {"osoby": osoby}, content_type=JSON).json()["konta"]
    assert [k["login"] for k in konta] == [f"uczen{i}.klasa" for i in range(8)]
    assert all(len(k["haslo"]) == 8 for k in konta)
    # hasło z okna mistrza gry działa przy logowaniu
    assert Client().login(username=konta[0]["login"], password=konta[0]["haslo"])
    for i, firma in enumerate(DRUZYNY):
        for k in konta[2 * i : 2 * i + 2]:
            assert dopisz(client, gra, firma, k["login"]).status_code == 200
    sklad = client.get(f"/api/gry/{gra}/druzyny").json()
    assert [len(d["sklad"]) for d in sklad["druzyny"]] == [2, 2, 2, 2]
    assert len(sklad["uczniowie"]) == 8  # konto mistrza gry nie jest na liście uczniów

    for i, firma in enumerate(DRUZYNY):
        pierwszy, drugi = zaloguj(konta[2 * i]["login"]), zaloguj(konta[2 * i + 1]["login"])
        v = pierwszy.get(f"/api/gry/{gra}/widok/{firma}").json()
        assert [o["nazwa"] for o in v["druzyna"]["sklad"]] == sorted(osoby[2 * i : 2 * i + 2])
        inna = DRUZYNY[(i + 1) % 4]
        assert pierwszy.get(f"/api/gry/{gra}/widok/{inna}").status_code == 403
        # jedna osoba zapisuje decyzje, druga je wysyła
        r = pierwszy.put(
            f"/api/gry/{gra}/decyzje/{firma}?wersja=0", v["decyzje"], content_type=JSON
        )
        assert r.status_code == 200
        assert r.json()["druzyna"]["autorzy"]["zapisal"]["login"] == konta[2 * i]["login"]
        w = drugi.post(f"/api/gry/{gra}/wyslij/{firma}", {}, content_type=JSON).json()
        assert w["przeliczono"] is (i == 3)  # runda zamyka się po decyzjach wszystkich drużyn
        if i < 3:
            assert w["druzyna"]["autorzy"]["wyslal"]["login"] == konta[2 * i + 1]["login"]
            mg = client.get(f"/api/gry/{gra}/mg").json()
            wyslaly = [f["nazwa"] for f in mg["firmy"] if f["wyslane"]]
            assert wyslaly == DRUZYNY[: i + 1] and mg["gra"]["runda"] == 1
    mg = client.get(f"/api/gry/{gra}/mg").json()
    assert mg["gra"]["runda"] == 2
    from gry import serwisy

    autorzy = serwisy.wczytaj(gra).decyzje[1]["_autorzy"]  # zostają w historii rundy
    assert autorzy[DRUZYNY[3]]["wyslal"]["login"] == konta[7]["login"]
    ludzie = [f for f in mg["firmy"] if not f["bot"]]
    assert all(len(f["sklad"]) == 2 for f in ludzie) and len(mg["firmy"]) == 6
    # nowa runda: wysłanie z poprzedniej nie przechodzi dalej
    st = zaloguj(konta[0]["login"]).get(f"/api/gry/{gra}/stan/{DRUZYNY[0]}").json()
    assert st == {"runda": 2, "wersja": 0, "zapisal": None, "wyslane": []}


def test_najwyzej_4_osoby_i_jedna_druzyna_w_grze(client, gra):
    konta = client.post("/api/konta", {"osoby": list("ABCDEF")}, content_type=JSON).json()["konta"]
    loginy = [k["login"] for k in konta]
    for login in loginy[:4]:
        assert dopisz(client, gra, DRUZYNY[0], login).status_code == 200
    r = dopisz(client, gra, DRUZYNY[0], loginy[4])
    assert r.status_code == 400 and "najwyżej 4" in r.json()["blad"]
    r = dopisz(client, gra, DRUZYNY[1], loginy[0])
    assert (
        r.status_code == 400 and r.json()["blad"] == f"{loginy[0]} gra już w drużynie {DRUZYNY[0]}."
    )
    assert (
        dopisz(client, gra, DRUZYNY[0], loginy[0]).status_code == 200
    )  # ponowne dodanie nic nie psuje
    assert dopisz(client, gra, "Bot tani", loginy[5]).status_code == 404
    assert (
        dopisz(client, gra, DRUZYNY[1], "nie-ma-takiego").json()["blad"]
        == "Nie ma konta nie-ma-takiego."
    )
    # usunięcie zwalnia miejsce i ucznia
    client.post(f"/api/gry/{gra}/druzyny/{DRUZYNY[0]}", {"usun": loginy[0]}, content_type=JSON)
    assert dopisz(client, gra, DRUZYNY[1], loginy[0]).status_code == 200
    assert dopisz(client, gra, DRUZYNY[0], loginy[4]).status_code == 200
    # w innej grze ten sam uczeń może grać w innej drużynie
    inna = client.post(
        "/api/gry", {"nazwa": "Druga", "firmy": [{"nazwa": "X", "bot": None}]}, content_type=JSON
    ).json()["id"]
    assert dopisz(client, inna, "X", loginy[0]).status_code == 200
    uczen = zaloguj(loginy[0])
    assert {g["id"] for g in uczen.get("/api/gry").json()} == {gra, inna}


def test_dwie_osoby_zmieniaja_decyzje_naraz(client, gra):
    konta = client.post(
        "/api/konta", {"osoby": ["Ala Nowak", "Bartek Wiśniewski"]}, content_type=JSON
    )
    ala_login, bartek_login = [k["login"] for k in konta.json()["konta"]]
    assert (ala_login, bartek_login) == ("ala.nowak", "bartek.wisniewski")
    for login in (ala_login, bartek_login):
        dopisz(client, gra, DRUZYNY[0], login)
    ala, bartek = zaloguj(ala_login), zaloguj(bartek_login)
    url = f"/api/gry/{gra}/decyzje/{DRUZYNY[0]}"
    d = ala.get(f"/api/gry/{gra}/widok/{DRUZYNY[0]}").json()["decyzje"]
    assert (
        ala.put(f"{url}?wersja=0", d, content_type=JSON).json()["druzyna"]["autorzy"]["wersja"] == 1
    )
    # Ala zapisuje dalej na swojej wersji – to jej własne zmiany
    assert ala.put(f"{url}?wersja=0", d, content_type=JSON).status_code == 200
    # Bartek ma stary widok (wersja 0) – zapis odrzucony, nic nie nadpisuje
    r = bartek.put(f"{url}?wersja=0", {"cokolwiek": 1}, content_type=JSON)
    assert r.status_code == 409 and r.json()["blad"].startswith(
        "Ala Nowak zmienia teraz decyzje drużyny"
    )
    assert "cokolwiek" not in ala.get(f"/api/gry/{gra}/widok/{DRUZYNY[0]}").json()["decyzje"]
    st = bartek.get(f"/api/gry/{gra}/stan/{DRUZYNY[0]}").json()
    assert st["wersja"] == 2 and st["zapisal"]["login"] == ala_login
    assert bartek.put(f"{url}?wersja=2", d, content_type=JSON).status_code == 200
    # wysłanie i cofnięcie wysłania też podbija wersję (inni widzą zmianę)
    bartek.post(f"/api/gry/{gra}/wyslij/{DRUZYNY[0]}", {}, content_type=JSON)
    w = ala.post(
        f"/api/gry/{gra}/wyslij/{DRUZYNY[0]}", {"wyslane": False}, content_type=JSON
    ).json()
    assert w["druzyna"]["autorzy"]["wersja"] == 5 and "wyslal" not in w["druzyna"]["autorzy"]
    # autorzy przetrwali zapis do bazy
    from gry import serwisy

    serwisy._pamiec.clear()
    assert (
        serwisy.wczytaj(gra).decyzje[1]["_autorzy"][DRUZYNY[0]]["zapisal"]["login"] == bartek_login
    )


def test_nowe_haslo_i_uprawnienia_kont(client, gra, uczen):
    konto = client.post("/api/konta", {"osoby": ["Ola Zięba"]}, content_type=JSON).json()["konta"][
        0
    ]
    j = client.post(f"/api/konta/{konto['login']}/haslo").json()
    assert j["haslo"] != konto["haslo"]
    assert Client().login(username="ola.zieba", password=j["haslo"])
    assert not Client().login(username="ola.zieba", password=konto["haslo"])
    assert client.post("/api/konta/mistrz/haslo").status_code == 403
    assert client.post("/api/konta/nikt/haslo").status_code == 404
    assert client.post("/api/konta", {"osoby": [" "]}, content_type=JSON).status_code == 400
    ala = uczen("ala")
    assert ala.post("/api/konta", {"osoby": ["X"]}, content_type=JSON).status_code == 403
    assert ala.post("/api/konta/ola.zieba/haslo").status_code == 403
    assert ala.get(f"/api/gry/{gra}/druzyny").status_code == 403
    assert dopisz(ala, gra, DRUZYNY[0], "ala").status_code == 403


def test_wolny_login(django_user_model):
    assert wolny_login("Żaneta Łuczak-Gęś") == "zaneta.luczak.ges"
    django_user_model.objects.create_user("zaneta.luczak.ges")
    assert wolny_login("  Żaneta   Łuczak-Gęś ") == "zaneta.luczak.ges2"
    assert wolny_login("!!!") == "uczen"


def test_panel_konta_pilnuje_skladu(client, gra):
    konta = client.post("/api/konta", {"osoby": list("ABCDE")}, content_type=JSON).json()["konta"]
    ids = list(
        get_user_model()
        .objects.filter(username__in=[k["login"] for k in konta])
        .values_list("pk", flat=True)
    )
    g = Gra.objects.get(pk=gra)
    form = DruzynaForm({"gra": g.pk, "firma": DRUZYNY[0], "czlonkowie": ids})
    assert not form.is_valid() and "najwyżej 4" in str(form.errors)
    assert not DruzynaForm({"gra": g.pk, "firma": "Bot tani", "czlonkowie": ids[:1]}).is_valid()
    assert DruzynaForm({"gra": g.pk, "firma": DRUZYNY[0], "czlonkowie": ids[:4]}).is_valid()


def test_strony_mistrza_gry_i_druzyny(client, gra):
    j = client.post("/api/konta", {"osoby": ["Ala Nowak"]}, content_type=JSON).json()["konta"][0]
    dopisz(client, gra, DRUZYNY[0], j["login"])
    assert client.get(f"/mg/gra/{gra}").status_code == 200
    strona = zaloguj(j["login"]).get(f"/gra/{gra}/{DRUZYNY[0]}").content.decode()
    assert '"ala.nowak"' in strona  # login do odświeżania (kto zmienia decyzje)
