"""Schematy plików danych `dane/*.yaml` (pydantic, `extra="forbid"`).

Każdy plik ma `opis` i `zrodlo` (skąd są liczby); katalog i założenia mają `zrodlo` przy każdej sekcji
lub parametrze. Schematy tylko sprawdzają dane – silnik dostaje zwykłe słowniki (`Dane`), więc sprawdzenie
nie zmienia wyników gry. Uruchomienie: `python -m silnik.dane sprawdz`.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Jakosc = Literal["1", "2", "3"]
Zrodlo = Field(min_length=3)


class Schemat(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Plik(Schemat):
    opis: str = Field(min_length=3)
    zrodlo: str = Zrodlo


# --- uslugi.yaml ---


class Pensje(Schemat):
    niska: float
    srednia: float
    wysoka: float


class Usluga(Schemat):
    nazwa: str
    kategoria: str
    popyt_roczny: int = Field(gt=0)
    cena_preferowana: float = Field(gt=0)
    sezonowosc: list[float] = Field(min_length=12, max_length=12)
    godziny_prowadzacego: float = Field(gt=0)
    godziny_recepcji: float = Field(ge=0)
    grupa: int = Field(gt=0)
    prowadzacy: str
    pensje_rynkowe: Pensje
    sprzet: list[str]
    zasoby: dict[str, float]


class PlikUslug(Plik):
    uslugi: dict[str, Usluga]
    pensje_rynkowe_recepcji: Pensje


# --- sprzet.yaml, zasoby.yaml ---


class Sprzet(Schemat):
    dla: Literal["kuchnia", "kasa"]
    ceny: dict[Jakosc, float]
    utrzymanie: dict[Jakosc, float]
    przechowywanie: Literal["chlodnia", "zamrazarka"] | None = None   # miejsce na składniki (gra z lokalami)
    pojemnosc_l: dict[Jakosc, float] | None = None

    @model_validator(mode="after")
    def _pojemnosc(self):
        if (self.przechowywanie is None) != (self.pojemnosc_l is None):
            raise ValueError("przechowywanie i pojemnosc_l podaje się razem")
        return self


class PlikSprzetu(Plik):
    sprzet: dict[str, Sprzet]


class Zasob(Schemat):
    przechowywanie: Literal["chlodnia", "zamrazarka", "suche"] = "suche"
    termin_dni: int | None = Field(default=None, ge=1)   # razem z dniem dostawy; brak = bez terminu
    miejsce_l: float = Field(default=0, ge=0)              # litry opakowania w chłodni / zamrażarce
    zamiennik_dla: str | None = None
    kara_jakosci: float = Field(default=0, ge=0, le=2)    # gwiazdki mniej, gdy zastępuje składnik podstawowy
    opakowanie: float = Field(gt=0)
    jednostka: str
    typ_opakowania: str
    srednie_ceny: dict[Jakosc, float]


class PlikZasobow(Plik):
    zasoby: dict[str, Zasob]


# --- dostawcy.yaml ---


class PlikDostawcow(Plik):
    pierwsi: list[str]
    wszyscy_od_miesiaca: str
    ceny: dict[
        str, dict[str, dict[str, dict[Jakosc, float]]]
    ]  # miesiąc → dostawca → zasób → jakość → cena


# --- kandydaci.yaml ---


class ZnanyKandydat(Schemat):
    imie_nazwisko: str
    gwiazdki: int = Field(ge=1, le=3)
    zawod: str
    pensja_preferowana: float = Field(gt=0)
    koszt_rekrutacji: float = Field(ge=0)
    koszt_odprawy: float = Field(ge=0)
    zadowolenie_klientow: float = Field(ge=0, le=1)
    ryzyko_reklamacji: float = Field(ge=0, le=1)


class Przedzialy(Schemat):
    pensja: tuple[float, float]
    zk: tuple[float, float]
    ryzyko: tuple[float, float]


class Losowanie(Schemat):
    zrodlo: str = Zrodlo
    na_start: int = Field(ge=0)
    co_runde: int = Field(ge=0)
    wiek: tuple[int, int]
    udzial_kobiet: float = Field(ge=0, le=1)
    gwiazdki: dict[Jakosc, float]
    krok_pensji: int = Field(gt=0)
    wg_gwiazdek: dict[Jakosc, Przedzialy]
    koszty_rekrutacji: list[float] = Field(min_length=1)
    odprawa_czesc_pensji: list[float] = Field(min_length=1)

    @field_validator("gwiazdki")
    @classmethod
    def _suma_jeden(cls, v: dict[str, float]) -> dict[str, float]:
        if abs(sum(v.values()) - 1) > 1e-9:
            raise ValueError("prawdopodobieństwa gwiazdek muszą sumować się do 1")
        return v


class Nazwisko(Schemat):
    m: str
    k: str


class PlikKandydatow(Plik):
    znani: list[ZnanyKandydat]
    losowanie: Losowanie
    imiona_kobiet: list[str] = Field(min_length=1)
    imiona_mezczyzn: list[str] = Field(min_length=1)
    nazwiska: list[Nazwisko] = Field(min_length=1)


# --- katalog.yaml ---


class Sekcja(Schemat):
    zrodlo: str = Zrodlo


class Kalendarz(Sekcja):
    """Długość rundy: tydzień (52 rundy w roku) albo miesiąc (12); start = pierwszy dzień rundy 1."""
    okres: Literal["tydzien", "miesiac"]
    rund_w_roku: int
    start: date

    @model_validator(mode="after")
    def _okres(self) -> Kalendarz:
        if self.rund_w_roku != {"tydzien": 52, "miesiac": 12}[self.okres]:
            raise ValueError("rund_w_roku: tydzień → 52, miesiąc → 12")
        if self.okres == "miesiac" and self.start.day != 1:
            raise ValueError("runda miesięczna zaczyna się pierwszego dnia miesiąca")
        return self


class Rundy(Sekcja):
    kalendarz: Kalendarz
    domyslna_liczba: int = Field(gt=0)
    odblokowanie: dict[str, list[str]]
    uslugi_w_rundzie_1: int = Field(ge=0)
    uslugi_startowe: list[str]
    uslugi_startowe_zrodlo: str
    nowe_uslugi_na_runde: int = Field(ge=0)
    nowe_uslugi_od_rundy: int = Field(ge=1)


class TypStanowiska(Schemat):
    nazwa: str  # nagłówek w zakładkach, np. „Stanowiska kuchenne”
    kto: str  # krótka nazwa, np. „Kuchnia”
    zawody: list[str] = Field(min_length=1)


class StanowiskoStartowe(Schemat):
    typ: Literal["kuchnia", "kasa"]
    sprzet: dict[str, int] = Field(default_factory=dict)  # nazwa → jakość 1–3


class Stanowiska(Sekcja):
    pakiety: dict[str, float]  # liczba nowych stanowisk → cena pakietu
    typy: dict[Literal["kuchnia", "kasa"], TypStanowiska]
    startowe: list[StanowiskoStartowe] = Field(default_factory=list)  # gotowy lokal: stanowiska na start, za darmo

    @model_validator(mode="after")
    def _typy(self) -> Stanowiska:
        if set(self.typy) != {"kuchnia", "kasa"}:
            raise ValueError("potrzebne są oba typy stanowisk: kuchnia i kasa")
        zawody = [z for t in self.typy.values() for z in t.zawody]
        if len(zawody) != len(set(zawody)):
            raise ValueError("zawód może należeć tylko do jednego typu stanowiska")
        return self


class Udogodnienie(Schemat):
    nazwa: str
    procent: float
    cena: float
    utrzymanie: float
    od_rundy: int = 1


class Medium(Schemat):
    nazwa: str
    kategoria: str
    zasieg: float
    cena: float
    znizki: list[tuple[int, float]]  # [od emisji, %]
    od_rundy: int = 1


class Narzedzie(Schemat):
    nazwa: str
    uruchomienie: float
    utrzymanie: float
    od_rundy: int = 1
    zalozenie: bool = False


class Bank(Schemat):
    nazwa: str
    konto: float
    karta: float
    lokata: float
    kredyt_odnawialny: float
    kredyt: float
    od_rundy: int = 1


class Biuro(Schemat):
    nazwa: str
    ksiegowanie: float
    etat: float
    zlecenie: float


class FirmaSzkoleniowa(Schemat):
    nazwa: str
    zadowoleni_klienci: float


class Szkolenie(Schemat):
    nazwa: str
    procent: float
    ceny: list[float]


class SekcjaUdogodnien(Sekcja):
    pozycje: list[Udogodnienie]


class SekcjaMediow(Sekcja):
    pozycje: list[Medium]


class SekcjaNarzedzi(Sekcja):
    pozycje: list[Narzedzie]


class SekcjaBankow(Sekcja):
    pozycje: list[Bank]
    kredyt_maks_miesiecy: int = Field(gt=0)
    lokata_konczy_sie_najpozniej_w_ostatniej_rundzie: bool


class SekcjaBiur(Sekcja):
    pozycje: list[Biuro]


class SekcjaSzkolen(Sekcja):
    firmy: list[FirmaSzkoleniowa]
    pozycje: list[Szkolenie]

    @model_validator(mode="after")
    def _ceny_firm(self) -> SekcjaSzkolen:
        for p in self.pozycje:
            if len(p.ceny) != len(self.firmy):
                raise ValueError(
                    f"szkolenie {p.nazwa}: {len(p.ceny)} cen, a firm jest {len(self.firmy)}"
                )
        return self


class PlikKatalogu(Schemat):
    opis: str
    rundy: Rundy
    stanowiska: Stanowiska
    udogodnienia: SekcjaUdogodnien
    wyposazenie: SekcjaUdogodnien
    media_tradycyjne: SekcjaMediow
    narzedzia_internetowe: SekcjaNarzedzi
    banki: SekcjaBankow
    biura_rachunkowe: SekcjaBiur
    szkolenia: SekcjaSzkolen


# --- boty.yaml ---


class Strategia(Schemat):
    nazwa: str
    cena: float | None  # ułamek ceny preferowanej; None = średnia rynku z poprzedniej rundy
    jakosc: int = Field(ge=1, le=3)
    uslugi: int = Field(gt=0)
    pokrycie: float = Field(gt=0)
    wyposazenie: int = Field(ge=0)
    udogodnienia: int = Field(ge=0)
    reklama: dict[str, int]
    internet: list[str]
    szkolenia: int = Field(ge=0)


class UstawieniaBotow(Schemat):
    bufor_gotowki: float
    cena_nasladowcy_bez_danych: float = Field(gt=0)
    krok_ceny: float = Field(gt=0)
    losuj_z_najlepszych_kandydatow: int = Field(gt=0)
    zapas_zasobow: float = Field(ge=1)


class PlikBotow(Plik):
    ustawienia: UstawieniaBotow
    strategie: dict[str, Strategia]


# --- zalozenia.yaml ---


class Zalozenie(Schemat):
    wartosc: Any
    pewnosc: Literal["potwierdzone", "skalibrowane", "zalozenie"]
    zrodlo: str = Zrodlo


def sprawdz_zalozenia(drzewo: dict, sciezka: str = "") -> list[str]:
    """Każdy liść drzewa założeń to {wartosc, pewnosc, zrodlo}; zwraca listę błędów."""
    bledy = []
    for k, v in drzewo.items():
        if k == "opis" and not sciezka:
            continue
        miejsce = sciezka + k
        if isinstance(v, dict) and "wartosc" in v:
            try:
                Zalozenie.model_validate(v)
            except ValueError as e:
                bledy.append(f"zalozenia.yaml: {miejsce}: {e}")
        elif isinstance(v, dict) and v:
            bledy += sprawdz_zalozenia(v, miejsce + ".")
        else:
            bledy.append(f"zalozenia.yaml: {miejsce}: brak wartosc/pewnosc/zrodlo")
    return bledy


# --- mapa/*.yaml (strefy, lokale, budynki; katalog opcjonalny – bez niego gra działa bez lokali) ---


class Prostokat(Schemat):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    szer: int = Field(default=1, ge=1)
    gl: int = Field(default=1, ge=1)


class Siatka(Schemat):
    szer: int = Field(gt=0)
    gl: int = Field(gt=0)


class Strefa(Schemat):
    nazwa: str
    opis: str
    klienci: str
    kolor: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    mapa: Prostokat
    czynsz_m2: float = Field(gt=0)


class PlikStref(Plik):
    siatka: Siatka
    strefy: dict[str, Strefa]


class StanowiskoZestawu(Schemat):
    typ: Literal["kuchnia", "kasa"]
    sprzet: dict[str, int]


class Zestaw(Schemat):
    nazwa: str
    opis: str
    stanowiska: list[StanowiskoZestawu] = Field(min_length=1)


class ZasadyLokali(Schemat):
    nowy_lokal_co_rund: int = Field(ge=1)
    kaucja_miesiecy: float = Field(ge=0)
    urzadzanie_rund: int = Field(ge=0)


class Miejsca(Schemat):
    kuchnia: int = Field(ge=1)
    kasa: int = Field(ge=1)


class Pole(Schemat):
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class Lokal(Schemat):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    nazwa: str
    strefa: str
    typ: Literal["gotowy", "niewyposazony", "dzialka"]
    adres: str
    opis: str
    metraz: int = Field(gt=0)
    miejsca: Miejsca
    zestaw: str | None = None
    czynsz: float | None = Field(default=None, gt=0)
    cena: float | None = Field(default=None, gt=0)
    adaptacja: float | None = Field(default=None, ge=0)
    budowa_rund: int | None = Field(default=None, ge=1)
    koszt_budowy: float | None = Field(default=None, ge=0)
    utrzymanie: float = Field(ge=0)
    tylko_kupno: bool = False
    wlasciciel: str | None = None
    od_rundy: int = Field(default=1, ge=1)
    mapa: Pole

    @model_validator(mode="after")
    def _typ(self):
        if self.czynsz is None and self.cena is None:
            raise ValueError("lokal musi mieć czynsz (najem) albo cenę (kupno)")
        if self.typ == "gotowy" and not self.zestaw:
            raise ValueError("lokal gotowy musi mieć zestaw sprzętu")
        if self.typ != "gotowy" and self.zestaw:
            raise ValueError("zestaw sprzętu ma tylko lokal gotowy")
        if self.typ == "niewyposazony" and self.adaptacja is None:
            raise ValueError("lokal niewyposażony musi mieć koszt adaptacji")
        if self.typ == "dzialka" and (self.cena is None or self.czynsz is not None or not self.budowa_rund
                                      or self.koszt_budowy is None):
            raise ValueError("działka: tylko kupno (cena, bez czynszu), budowa_rund i koszt_budowy")
        if self.tylko_kupno and (self.cena is None or self.czynsz is not None):
            raise ValueError("tylko_kupno: cena bez czynszu")
        return self


class PlikLokali(Plik):
    zasady: ZasadyLokali
    zestawy: dict[str, Zestaw]
    lokale: list[Lokal] = Field(min_length=1)


class Budynek(Schemat):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    nazwa: str
    rodzaj: str
    strefa: str
    opis: str
    zakladka: str | None
    mapa: Prostokat


class PlikBudynkow(Plik):
    budynki: list[Budynek]


class ModelPopytu(Schemat):
    opcja_zewnetrzna: float = Field(gt=0)
    elastycznosc_ceny: float = Field(ge=0)
    zasieg: float = Field(gt=0)
    szum_proc: float = Field(ge=0)
    zadowolenie_odniesienie: float = Field(gt=0)
    zadowolenie_wykladnik: float = Field(ge=0)


class DniTygodnia(Schemat):
    nazwy: list[str] = Field(min_length=7, max_length=7)
    wagi: list[float] = Field(min_length=7, max_length=7)


class PopytStrefy(Schemat):
    pula: float = Field(ge=0)
    cena: float = Field(gt=0)
    wrazliwosc_ceny: float = Field(ge=0)
    dni: list[float] | None = Field(default=None, min_length=7, max_length=7)
    miesiace: list[float] | None = Field(default=None, min_length=12, max_length=12)


class WydarzenieKalendarza(Schemat):
    nazwa: str
    opis: str
    od: str = Field(pattern=r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
    do: str = Field(pattern=r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
    strefy: dict[str, float] = Field(min_length=1)


class WagiJakosciDania(Schemat):
    skladniki: float = Field(ge=0)
    kucharze: float = Field(ge=0)
    sprzet: float = Field(ge=0)


class PlikMenu(Plik):
    jakosc: WagiJakosciDania
    zmiana_dania: float = Field(ge=0, le=1)


class PlikPopytu(Plik):
    model: ModelPopytu
    dni_tygodnia: DniTygodnia
    strefy: dict[str, PopytStrefy]
    kalendarz: list[WydarzenieKalendarza] = []


SCHEMATY_MAPY: dict[str, type[BaseModel]] = {
    "strefy.yaml": PlikStref,
    "lokale.yaml": PlikLokali,
    "budynki.yaml": PlikBudynkow,
    "popyt.yaml": PlikPopytu,
    "menu.yaml": PlikMenu,
}

SCHEMATY: dict[str, type[BaseModel]] = {
    "uslugi.yaml": PlikUslug,
    "sprzet.yaml": PlikSprzetu,
    "zasoby.yaml": PlikZasobow,
    "dostawcy.yaml": PlikDostawcow,
    "kandydaci.yaml": PlikKandydatow,
    "katalog.yaml": PlikKatalogu,
    "boty.yaml": PlikBotow,
}
