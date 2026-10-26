"""Prowadzenie gry przez mistrza gry (F3a.14): harmonogram zamykania rund, pauza, wgląd w drużyny tylko do
odczytu, poziom botów, eksport wyników do arkusza."""

from datetime import datetime, timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from gry import harmonogram as hg
from gry.models import Gra

pytestmark = pytest.mark.django_db

JSON = "application/json"
FIRMY = [{"nazwa": "Kebab Ali", "bot": None}, {"nazwa": "Pita Pan", "bot": None},
         {"nazwa": "Bot", "bot": "tani", "poziom": "trudny"}]


@pytest.fixture
def gra(client):
    d = {"nazwa": "Klasa", "ziarno": "7", "liczba_rund": 4, "firmy": FIRMY}
    return client.post("/api/gry", d, content_type=JSON).json()["id"]


def _mg(client, gra):
    return client.get(f"/api/gry/{gra}/mg").json()


def _ustaw(client, gra, **d):
    return client.post(f"/api/gry/{gra}/prowadzenie", d, content_type=JSON)


def _lokalnie(*a):
    return timezone.make_aware(datetime(*a), timezone.get_current_timezone())


def test_nastepny_termin_tygodniowy():
    terminy = hg.popraw([{"dzien": 3, "godzina": "8:00"}, {"dzien": 1, "godzina": "08:00"},
                         {"dzien": 1, "godzina": "08:00"}])
    assert terminy == [{"dzien": 1, "godzina": "08:00"}, {"dzien": 3, "godzina": "08:00"}]
    pon = _lokalnie(2026, 10, 26, 12, 0)  # poniedziałek
    assert hg.nastepny(terminy, pon) == _lokalnie(2026, 10, 27, 8, 0)
    assert hg.nastepny(terminy, _lokalnie(2026, 10, 27, 8, 0)) == _lokalnie(2026, 10, 29, 8, 0)  # ściśle po
    assert hg.nastepny(terminy, _lokalnie(2026, 10, 29, 9, 0)) == _lokalnie(2026, 11, 3, 8, 0)
    assert hg.nastepny([], pon) is None
    for zle in ([{"dzien": 7, "godzina": "8:00"}], [{"dzien": 1, "godzina": "25:00"}], [{"dzien": 1}], "pon"):
        with pytest.raises(ValueError):
            hg.popraw(zle)


def test_harmonogram_zamyka_runde_po_terminie(client, gra):
    assert _ustaw(client, gra, harmonogram=[{"dzien": 9, "godzina": "8:00"}]).status_code == 400
    p = _ustaw(client, gra, harmonogram=[{"dzien": 0, "godzina": "8:00"}]).json()["prowadzenie"]
    assert p["harmonogram_opis"] == "poniedziałek 08:00" and p["termin"]
    termin = datetime.fromisoformat(p["termin"])
    assert hg.do_zamkniecia(termin - timedelta(minutes=1)) == []
    assert hg.do_zamkniecia(termin) == [(gra, termin)]
    assert hg.zamknij_spoznione(termin) == [{"gra": gra, "nazwa": "Klasa", "runda": 1}]
    # następny termin liczony od zamknięcia – za tydzień, ta sama komenda nic już nie zamyka
    assert hg.zamknij_spoznione(termin + timedelta(minutes=5)) == []
    assert _mg(client, gra)["gra"]["runda"] == 2
    nowy = datetime.fromisoformat(_mg(client, gra)["prowadzenie"]["termin"])
    assert nowy > termin + timedelta(days=6)


def test_komenda_zamykaj_rundy(client, gra):
    _ustaw(client, gra, harmonogram=[{"dzien": 0, "godzina": "8:00"}])
    Gra.objects.filter(pk=gra).update(termin_od=timezone.now() - timedelta(days=8))
    out = StringIO()
    call_command("zamykaj_rundy", stdout=out)
    assert "runda 1 zamknięta" in out.getvalue() and _mg(client, gra)["gra"]["runda"] == 2


def test_pauza_wstrzymuje_decyzje_zamkniecie_i_harmonogram(client, gra, uczen):
    ala = uczen("ala")
    client.post(f"/api/gry/{gra}/druzyny/Kebab Ali", {"dodaj": "ala"}, content_type=JSON)
    _ustaw(client, gra, harmonogram=[{"dzien": 0, "godzina": "8:00"}])
    Gra.objects.filter(pk=gra).update(termin_od=timezone.now() - timedelta(days=8))
    p = _ustaw(client, gra, pauza=True).json()["prowadzenie"]
    assert p["pauza"] and p["termin"] is None and hg.do_zamkniecia() == []
    url = f"/api/gry/{gra}/decyzje/Kebab Ali?wersja=0"
    v = ala.get(f"/api/gry/{gra}/widok/Kebab Ali").json()
    assert v["prowadzenie"]["pauza"] and not v["tylko_odczyt"]
    assert ala.put(url, v["decyzje"], content_type=JSON).status_code == 400
    assert ala.post(f"/api/gry/{gra}/wyslij/Kebab Ali", {"wyslane": True}, content_type=JSON).status_code == 400
    assert client.post(f"/api/gry/{gra}/przelicz").status_code == 400
    assert ala.get(f"/api/gry/{gra}/stan/Kebab Ali").json()["pauza"]
    # wznowienie: termin, który minął w czasie pauzy, nie zamyka rundy od razu
    p = _ustaw(client, gra, pauza=False).json()["prowadzenie"]
    assert not p["pauza"] and p["termin"] and hg.do_zamkniecia() == []
    assert ala.put(url, v["decyzje"], content_type=JSON).status_code == 200


def test_mistrz_gry_oglada_druzyne_uczniow_tylko_do_odczytu(client, gra, uczen):
    ala = uczen("ala")
    client.post(f"/api/gry/{gra}/druzyny/Kebab Ali", {"dodaj": "ala"}, content_type=JSON)
    v = client.get(f"/api/gry/{gra}/widok/Kebab Ali").json()
    assert v["tylko_odczyt"]
    url = f"/api/gry/{gra}/decyzje/Kebab Ali?wersja=0"
    assert client.put(url, v["decyzje"], content_type=JSON).status_code == 403
    assert client.post(f"/api/gry/{gra}/wyslij/Kebab Ali", {"wyslane": True}, content_type=JSON).status_code == 403
    assert not ala.get(f"/api/gry/{gra}/widok/Kebab Ali").json()["tylko_odczyt"]
    # drużynę bez uczniów prowadzi mistrz gry
    v2 = client.get(f"/api/gry/{gra}/widok/Pita Pan").json()
    assert not v2["tylko_odczyt"]
    assert client.put(f"/api/gry/{gra}/decyzje/Pita Pan?wersja=0", v2["decyzje"], content_type=JSON).status_code == 200
    # mistrz gry nadal zamyka rundę za wszystkich
    assert client.post(f"/api/gry/{gra}/przelicz").json()["runda"] == 2


def test_poziom_botow(client, gra):
    bot = next(f for f in _mg(client, gra)["firmy"] if f["bot"])
    assert bot["poziom"] == "trudny"
    assert set(_mg(client, gra)["prowadzenie"]["poziomy"]) == {"latwy", "sredni", "trudny"}
    assert _ustaw(client, gra, poziom={"firma": "Bot", "poziom": "latwy"}).status_code == 200
    assert next(f for f in _mg(client, gra)["firmy"] if f["bot"])["poziom"] == "latwy"
    assert _ustaw(client, gra, poziom={"firma": "Bot", "poziom": "mistrz"}).status_code == 400
    assert _ustaw(client, gra, poziom={"firma": "Kebab Ali", "poziom": "latwy"}).status_code == 404
    zle = {"nazwa": "X", "firmy": [{"nazwa": "A", "bot": None}, {"nazwa": "B", "bot": "tani", "poziom": "?"}]}
    assert client.post("/api/gry", zle, content_type=JSON).status_code == 400


def test_eksport_csv(client, gra, uczen):
    for _ in range(3):
        client.post(f"/api/gry/{gra}/przelicz")
    r = client.get(f"/api/gry/{gra}/wyniki.csv")
    assert r.status_code == 200 and r["Content-Type"].startswith("text/csv")
    tekst = r.content.decode("utf-8")
    assert tekst.startswith("﻿runda;tydzień;firma;bot;przychody")
    wiersze = tekst.strip().split("\r\n")
    assert len(wiersze) == 1 + 3 * 3   # nagłówek + 3 rundy × 3 firmy
    assert any(w.startswith("2;T2;Kebab Ali;;") for w in wiersze) and "," in wiersze[1]  # przecinek dziesiętny
    ranking = client.get(f"/api/gry/{gra}/ranking.csv").content.decode("utf-8").strip().split("\r\n")
    assert ranking[0].startswith("﻿miejsce;firma") and len(ranking) == 4 and ranking[1].startswith("1;")
    assert client.get(f"/api/gry/{gra}/inne.csv").status_code == 404
    assert uczen("ala").get(f"/api/gry/{gra}/wyniki.csv").status_code == 403
