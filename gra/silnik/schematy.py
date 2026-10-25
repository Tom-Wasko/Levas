"""Schematy plików danych `dane/*.yaml` (pydantic, `extra="forbid"`).

Każdy plik ma `opis` i `zrodlo` (skąd są liczby); katalog i założenia mają `zrodlo` przy każdej sekcji
lub parametrze. Schematy tylko sprawdzają dane – silnik dostaje zwykłe słowniki (`Dane`), więc sprawdzenie
nie zmienia wyników gry. Uruchomienie: `python -m silnik.dane sprawdz`.
"""

from __future__ import annotations

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
    dla: Literal["instruktor", "recepcja"]
    ceny: dict[Jakosc, float]
    utrzymanie: dict[Jakosc, float]


class PlikSprzetu(Plik):
    sprzet: dict[str, Sprzet]


class Zasob(Schemat):
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


class Rundy(Sekcja):
    domyslna_liczba: int = Field(gt=0)
    odblokowanie: dict[str, list[str]]
    uslugi_w_rundzie_1: int = Field(ge=0)
    uslugi_startowe: list[str]
    uslugi_startowe_zrodlo: str
    nowe_uslugi_na_runde: int = Field(ge=0)
    nowe_uslugi_od_rundy: int = Field(ge=1)


class Stanowiska(Sekcja):
    pakiety: dict[str, float]  # liczba nowych stanowisk → cena pakietu


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


SCHEMATY: dict[str, type[BaseModel]] = {
    "uslugi.yaml": PlikUslug,
    "sprzet.yaml": PlikSprzetu,
    "zasoby.yaml": PlikZasobow,
    "dostawcy.yaml": PlikDostawcow,
    "kandydaci.yaml": PlikKandydatow,
    "katalog.yaml": PlikKatalogu,
    "boty.yaml": PlikBotow,
}
