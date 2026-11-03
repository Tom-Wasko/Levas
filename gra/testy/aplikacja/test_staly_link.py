"""Stały link do gry z hostuj.bat: pliki przekierowania, wgrywanie przez FTP, komendy."""

import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from panel_gracza import staly_link
from panel_gracza.management.commands import hostuj
from panel_gracza.management.commands import staly_link as komenda

TUNEL = "https://ala-ma-kota.trycloudflare.com"
KONFIG = {"adres": "https://levas.szkola.pl", "host": "ftp.szkola.pl", "login": "levas",
          "haslo": "tajne", "katalog": "/www/levas"}


class FalszyweFTP:
    """Zamiast FTPS: zapisuje polecenia i wgrane pliki."""

    ostatnie = None
    blad = None

    def __init__(self, host, timeout, context):
        self.host, self.polecenia, self.pliki = host, [], {}
        FalszyweFTP.ostatnie = self

    def __enter__(self):
        if FalszyweFTP.blad:
            raise FalszyweFTP.blad
        return self

    def __exit__(self, *wyjatek):
        self.polecenia.append("quit")

    def login(self, login, haslo):
        self.polecenia.append(("login", login, haslo))

    def prot_p(self):
        self.polecenia.append("prot_p")

    def cwd(self, katalog):
        self.polecenia.append(("cwd", katalog))

    def storbinary(self, polecenie, plik):
        self.pliki[polecenie.removeprefix("STOR ")] = plik.read().decode("utf-8")


@pytest.fixture
def ftp(monkeypatch):
    FalszyweFTP.ostatnie, FalszyweFTP.blad = None, None
    monkeypatch.setattr(staly_link, "FTPS", FalszyweFTP)
    return FalszyweFTP


@pytest.fixture
def lokalne(settings, tmp_path):
    settings.PLIK_LOKALNY = tmp_path / "lokalne.json"
    settings.LOKALNE = {"secret_key": "x"}
    return settings.PLIK_LOKALNY


def test_pliki_przekierowania_na_tunel():
    pliki = staly_link.pliki(TUNEL + "/")
    assert f"RewriteRule ^(.*)$ {TUNEL}/$1 [R=302,L]" in pliki[".htaccess"]
    assert "no-store" in pliki[".htaccess"]
    assert f'content="0; url={TUNEL}/"' in pliki["index.html"]
    assert f'location.replace("{TUNEL}/")' in pliki["index.html"]


def test_pliki_gra_wylaczona():
    pliki = staly_link.pliki(None)
    assert "Rewrite" not in pliki[".htaccess"]
    assert "DirectoryIndex index.html" in pliki[".htaccess"]
    assert "gra wyłączona" in pliki["index.html"]
    assert "refresh" not in pliki["index.html"] and "trycloudflare" not in pliki["index.html"]


def test_wgraj_loguje_szyfruje_i_wgrywa_do_katalogu(ftp):
    staly_link.wgraj(KONFIG, TUNEL)
    f = ftp.ostatnie
    assert f.host == "ftp.szkola.pl"
    assert f.polecenia == [("login", "levas", "tajne"), "prot_p", ("cwd", "/www/levas"), "quit"]
    assert set(f.pliki) == {".htaccess", "index.html"}
    assert TUNEL in f.pliki[".htaccess"]


def test_wgraj_bez_katalogu_zostaje_w_startowym(ftp):
    staly_link.wgraj({**KONFIG, "katalog": ""}, None)
    assert not any(isinstance(p, tuple) and p[0] == "cwd" for p in ftp.ostatnie.polecenia)


def test_ustaw_bez_konfiguracji_nic_nie_robi(ftp, lokalne):
    assert staly_link.ustaw(TUNEL) is None
    assert ftp.ostatnie is None


def test_ustaw_z_konfiguracja_i_blad_polaczenia_nie_przerywa(ftp, lokalne, settings, capsys):
    settings.LOKALNE[staly_link.KLUCZ] = KONFIG
    assert staly_link.ustaw(TUNEL) == "https://levas.szkola.pl"
    ftp.blad = OSError("brak sieci")
    assert staly_link.ustaw(None) is None
    assert "brak sieci" in capsys.readouterr().out


def test_komenda_zapisuje_po_udanym_polaczeniu(ftp, lokalne, monkeypatch):
    odpowiedzi = iter(["levas.szkola.pl", "ftp.szkola.pl", "levas", ""])
    monkeypatch.setattr("builtins.input", lambda _pytanie: next(odpowiedzi))
    monkeypatch.setattr(komenda, "getpass", lambda _pytanie: "tajne")
    call_command("staly_link")
    zapisane = json.loads(lokalne.read_text(encoding="utf-8"))
    assert zapisane["secret_key"] == "x"
    assert zapisane["staly_link"] == {"adres": "https://levas.szkola.pl", "host": "ftp.szkola.pl",
                                      "login": "levas", "haslo": "tajne", "katalog": ""}
    assert "gra wyłączona" in ftp.ostatnie.pliki["index.html"]

    # druga zmiana: Enter zostawia stare wartości, także hasło
    monkeypatch.setattr("builtins.input", lambda _pytanie: "")
    monkeypatch.setattr(komenda, "getpass", lambda _pytanie: "")
    call_command("staly_link")
    assert json.loads(lokalne.read_text(encoding="utf-8"))["staly_link"]["haslo"] == "tajne"

    call_command("staly_link", "--usun")
    assert "staly_link" not in json.loads(lokalne.read_text(encoding="utf-8"))


def test_komenda_nie_zapisuje_przy_bledzie_polaczenia(ftp, lokalne, monkeypatch):
    odpowiedzi = iter(["https://levas.szkola.pl", "ftp.szkola.pl", "levas", ""])
    monkeypatch.setattr("builtins.input", lambda _pytanie: next(odpowiedzi))
    monkeypatch.setattr(komenda, "getpass", lambda _pytanie: "zle")
    ftp.blad = OSError("530 Login incorrect")
    with pytest.raises(CommandError, match="odrzucił login"):
        call_command("staly_link")
    assert not lokalne.exists()


@pytest.mark.django_db
def test_hostuj_ustawia_staly_link_i_wylacza_go_na_koniec(
        ftp, lokalne, settings, monkeypatch, django_user_model, capsys):
    settings.LOKALNE[staly_link.KLUCZ] = KONFIG
    django_user_model.objects.create_superuser("mg", password="haslo123")

    class Proces:
        zakonczony = False

        def terminate(self):
            Proces.zakonczony = True

    wgrane = []
    monkeypatch.setattr(hostuj, "port_zajety", lambda port: False)
    monkeypatch.setattr(hostuj.Command, "tunel", lambda self, port: (TUNEL, Proces()))
    monkeypatch.setattr(staly_link, "wgraj", lambda konfig, url: wgrane.append(url))
    oryginal = hostuj.call_command
    monkeypatch.setattr(hostuj, "call_command", lambda nazwa, *a, **k: (
        wgrane.append("runserver") if nazwa == "runserver" else oryginal(nazwa, *a, **k)))
    monkeypatch.setattr(settings, "ALLOWED_HOSTS", list(settings.ALLOWED_HOSTS))

    call_command("hostuj", "--bez-przegladarki")
    assert wgrane == [TUNEL, "runserver", None]
    assert Proces.zakonczony
    assert "Stały link:         https://levas.szkola.pl" in capsys.readouterr().out
