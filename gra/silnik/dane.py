"""Dane gry (revas_gra/dane/*.json) i założenia (revas_gra/zalozenia.json) w jednym obiekcie."""
from __future__ import annotations

import hashlib
import json
from functools import cached_property, lru_cache
from pathlib import Path

KATALOG_GRY = Path(__file__).resolve().parents[1]
KATALOG_DANYCH = KATALOG_GRY / "dane"
PLIK_ZALOZEN = KATALOG_GRY / "zalozenia.json"

MIESIACE = ["styczen", "luty", "marzec", "kwiecien", "maj", "czerwiec", "lipiec", "sierpien", "wrzesien",
            "pazdziernik", "listopad", "grudzien"]
MIESIACE_NAZWY = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień",
                  "Październik", "Listopad", "Grudzień"]
ZASOBY_KOLEJNOSC = ["Napój izotoniczny", "Płyn do dezynfekcji", "Ręcznik papierowy", "Woda"]
INSTRUKTOR, TRENER, RECEPCJONISTA = "Instruktor", "Trener personalny", "Recepcjonista"


def _wczytaj(plik: Path):
    return json.loads(plik.read_text(encoding="utf-8"))


def _wartosci(wezel):
    """Z drzewa założeń zostawia same wartości: {"a": {"wartosc": 1, ...}} → {"a": 1}."""
    if isinstance(wezel, dict):
        if "wartosc" in wezel:
            return wezel["wartosc"]
        return {k: _wartosci(v) for k, v in wezel.items() if not k.startswith("_")}
    return wezel


class Dane:
    def __init__(self, katalog: Path = KATALOG_DANYCH, zalozenia: Path = PLIK_ZALOZEN):
        self.katalog = katalog
        self.uslugi: dict = _wczytaj(katalog / "uslugi.json")["uslugi"]
        self.pensje_recepcji: dict = _wczytaj(katalog / "uslugi.json")["pensje_rynkowe_recepcji"]
        self.sprzet: dict = _wczytaj(katalog / "sprzet.json")
        self.zasoby: dict = _wczytaj(katalog / "zasoby.json")
        self.dostawcy: dict = _wczytaj(katalog / "dostawcy.json")
        self.kandydaci: list = _wczytaj(katalog / "kandydaci.json")
        self.katalog_ofert: dict = _wczytaj(katalog / "katalog.json")
        self.zalozenia_pelne: dict = _wczytaj(zalozenia)
        self.z: dict = _wartosci(self.zalozenia_pelne)

    @cached_property
    def sprzet_recepcji(self) -> list[str]:
        return [n for n, s in self.sprzet.items() if s["dla"] == "recepcja"]

    @cached_property
    def wersja(self) -> str:
        """Skrót danych i założeń – w grze wieloosobowej wszyscy muszą mieć ten sam."""
        h = hashlib.sha256()
        for plik in sorted(self.katalog.glob("*.json")) + [PLIK_ZALOZEN]:
            h.update(plik.read_bytes())
        return h.hexdigest()[:12]

    def odblokowane(self, runda: int) -> set[str]:
        wynik = set()
        for r, zakladki in self.katalog_ofert["rundy"]["odblokowanie"].items():
            if int(r) <= runda:
                wynik |= set(zakladki)
        return wynik

    def pozycje(self, rodzaj: str) -> dict[str, dict]:
        """Pozycje katalogu po nazwie: udogodnienia, wyposazenie, media_tradycyjne, narzedzia_internetowe, banki, …"""
        return {p["nazwa"]: p for p in self.katalog_ofert[rodzaj]["pozycje"]}

    def dostepne(self, rodzaj: str, runda: int) -> dict[str, dict]:
        """Pozycje katalogu dostępne w rundzie (pole od_rundy; brak = od początku gry)."""
        return {n: p for n, p in self.pozycje(rodzaj).items() if p.get("od_rundy", 1) <= runda}


@lru_cache(maxsize=1)
def dane_domyslne() -> Dane:
    return Dane()
