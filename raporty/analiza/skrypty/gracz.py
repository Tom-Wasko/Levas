"""A2: wspólne narzędzia do grania przez API (serwer analizy na 127.0.0.1:8766, baza
raporty/analiza/analiza.sqlite3 – ustawienia_analizy.py) i zrzutów ekranu z Chrome w tle.

Gracz-człowiek wysyła decyzje tak jak przeglądarka: PUT /api/gry/<id>/decyzje/<firma>,
POST /api/gry/<id>/wyslij/<firma>. Żmudne liczby (obsada dzień po dniu, zamówienia składników)
liczy „kalkulator ucznia” – planista botów z silnik/boty.py na wybranym poziomie; persona nadpisuje
resztę (lokal, ceny, menu, bank, finanse, reklama) i robi swoje błędy.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

SKRYPTY = Path(__file__).resolve().parent
ANALIZA = SKRYPTY.parent
GRA = ANALIZA.parent.parent / "gra"
ZRZUTY = ANALIZA / "zrzuty"
sys.path[:0] = [str(GRA), str(SKRYPTY)]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ustawienia_analizy")

import django  # noqa: E402

django.setup()

import requests  # noqa: E402

from gry import serwisy  # noqa: E402
from silnik.boty import decyzje_bota  # noqa: E402

ADRES = "http://127.0.0.1:8766"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def _json(x):
    return json.loads(json.dumps(x, default=float))


class Klient:
    """Sesja przeglądarki mistrza gry w grze lokalnej (logowanie automatyczne z 127.0.0.1)."""

    def __init__(self, login: str | None = None, haslo: str | None = None):
        """Bez loginu – mistrz gry (logowanie automatyczne z 127.0.0.1); z loginem – uczeń przez
        formularz logowania (allauth)."""
        self.s = requests.Session()
        if login is None:
            self.s.get(ADRES + "/", timeout=60)
            return
        self.s.get(ADRES + "/konta/login/", timeout=60)
        r = self.s.post(ADRES + "/konta/login/", timeout=60, allow_redirects=False,
                        data={"login": login, "password": haslo,
                              "csrfmiddlewaretoken": self.s.cookies.get("csrftoken", "")},
                        headers={"Referer": ADRES + "/konta/login/"})
        self.zalogowany = r.status_code in (302, 303)

    def zapytaj(self, metoda: str, sciezka: str, **kw) -> tuple[int, dict]:
        h = {"X-CSRFToken": self.s.cookies.get("csrftoken", "")}
        r = self.s.request(metoda, ADRES + sciezka, headers=h, timeout=900, **kw)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, {"tekst": r.text[:500]}

    def nowa_gra(self, nazwa: str, firmy: list[dict], ziarno: int, **opcje) -> str:
        kod, d = self.zapytaj("POST", "/api/gry", json={"nazwa": nazwa, "liczba_rund": 18,
                                                         "ziarno": ziarno, "firmy": firmy, **opcje})
        assert kod == 200, d
        return d["id"]

    def widok(self, gid: str, firma: str, runda: int | None = None) -> dict:
        r = f"?runda={runda}" if runda else ""
        kod, d = self.zapytaj("GET", f"/api/gry/{gid}/widok/{quote(firma)}{r}")
        assert kod == 200, d
        return d

    def decyzje(self, gid: str, firma: str, d: dict) -> tuple[int, dict]:
        return self.zapytaj("PUT", f"/api/gry/{gid}/decyzje/{quote(firma)}", json=_json(d))

    def wyslij(self, gid: str, firma: str, wyslane: bool = True) -> tuple[int, dict]:
        return self.zapytaj("POST", f"/api/gry/{gid}/wyslij/{quote(firma)}",
                            json={"wyslane": wyslane})

    def mg(self, gid: str) -> dict:
        return self.zapytaj("GET", f"/api/gry/{gid}/mg")[1]

    def prowadzenie(self, gid: str, d: dict) -> tuple[int, dict]:
        return self.zapytaj("POST", f"/api/gry/{gid}/prowadzenie", json=d)

    def przelicz(self, gid: str) -> tuple[int, dict]:
        return self.zapytaj("POST", f"/api/gry/{gid}/przelicz", json={})


def kalkulator(gid: str, firma: str, strategia: str, poziom: str) -> dict:
    """Plan rundy z planisty botów (obsada, zamówienia, stanowiska) dla firmy gracza."""
    g = serwisy.wczytaj(gid)
    konf = copy.deepcopy(g.konfiguracja)
    for f in konf["firmy"]:
        if f["nazwa"] == firma:
            f["poziom"] = poziom
    return _json(decyzje_bota(g.dane, g.stan(g.runda - 1), firma, strategia, g.runda, konf))


def zrzut(gid: str, firma: str | None, zakladka: str, plik: str, wysokosc: int = 1100) -> Path:
    """Zrzut strony drużyny albo panelu mistrza gry (firma=None) do raporty/analiza/zrzuty."""
    adres = (f"{ADRES}/gra/{gid}/{quote(firma)}#{zakladka}" if firma
             else f"{ADRES}/mg/gra/{gid}")
    cel = ZRZUTY / plik
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size=1400,{wysokosc}", "--virtual-time-budget=9000",
                    f"--screenshot={cel}", adres], timeout=120, capture_output=True)
    return cel


def podsumowanie(k: Klient, gid: str) -> dict:
    """Wyniki wszystkich firm z panelu mistrza gry po ostatniej przeliczonej rundzie."""
    p = k.mg(gid)
    return {f["nazwa"]: {x: f.get(x) for x in (
        "miejsce", "gotowka", "zadluzenie", "lokaty", "majatek_netto", "alarm", "dochod_ostatni",
        "dochod_suma", "wynik_ostatni", "wynik_skumulowany", "pracownicy", "stanowiska")}
        for f in p["firmy"]}


def zapisz_log(nazwa: str, wpisy: list) -> None:
    (ANALIZA / f"log_{nazwa}.json").write_text(
        json.dumps(wpisy, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
