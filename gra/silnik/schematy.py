"""Schematy plików danych `dane/*.yaml` (pydantic, `extra="forbid"`).

Każdy plik ma `opis` i `zrodlo` (skąd są liczby); katalog i założenia mają `zrodlo` przy każdej sekcji
lub parametrze. Schematy tylko sprawdzają dane – silnik dostaje zwykłe słowniki (`Dane`), więc sprawdzenie
nie zmienia wyników gry. Uruchomienie: `python -m silnik.dane sprawdz`.
"""

from __future__ import annotations

import re
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
    godziny_kasy: float = Field(ge=0)
    grupa: int = Field(gt=0)
    prowadzacy: str
    pensje_rynkowe: Pensje
    sprzet: list[str]
    zasoby: dict[str, float]


class PlikUslug(Plik):
    uslugi: dict[str, Usluga]
    pensje_rynkowe_kasy: Pensje


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


class Gazetka(Schemat):
    pozycji: int = Field(ge=1)                 # ile składników co tydzień w promocji
    rabat_min: float = Field(gt=0, lt=1)
    rabat_max: float = Field(gt=0, lt=1)


class Dostawca(Schemat):
    rodzaj: Literal["dyskont", "hurtownia", "producent", "piekarnia"]
    opis: str
    dni_dostaw: list[int] = Field(min_length=1)   # 0 = poniedziałek … 6 = niedziela
    koszt_dostawy: float = Field(default=0, ge=0)  # za każdą dostawę (dzień) poniżej progu
    darmowa_od: float | None = Field(default=None, gt=0)
    minimalne_zamowienie: float = Field(default=0, ge=0)   # wartość jednej dostawy
    odbior_osobisty: bool = False                 # dyskont: właściciel jedzie sam (czas właściciela, F3a.7)
    godziny_odbioru: float = Field(default=0, ge=0)
    limit_opakowan: int | None = Field(default=None, ge=1)  # na składnik na dzień
    od_rundy: int = Field(default=0, ge=0)
    gazetka: Gazetka | None = None

    @field_validator("dni_dostaw")
    @classmethod
    def _dni(cls, v):
        if sorted(set(v)) != v or v[0] < 0 or v[-1] > 6:
            raise ValueError("dni dostaw: rosnące, bez powtórzeń, 0–6")
        return v


class PlikDostawcow(Plik):
    pierwsi: list[str]
    wszyscy_od_miesiaca: str
    dostawcy: dict[str, Dostawca] = Field(default_factory=dict)   # bez sekcji (dane Revasa): dostawa każdego dnia, bez opłat
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


class KanalRekrutacji(Schemat):
    nazwa: str
    od_rundy: int = Field(ge=1)
    gwiazdki: list[int] = Field(min_length=1)
    oplata: float = Field(ge=0)                 # zł za zatrudnienie
    mnoznik_rekrutacji: float = Field(ge=0)     # × koszt rekrutacji kandydata
    czas_wlasciciela: float = Field(ge=0)       # godziny na zatrudnienie
    podkupienie_czesc_pensji: float | None = Field(None, ge=0)   # headhunter: opłata za podkupienie (× pensja)


class Wypowiedzenie(Schemat):
    staz_od: int = Field(ge=0)                  # staż u obecnego pracodawcy w rundach
    rund: int = Field(ge=0)


class Agencja(Schemat):
    zrodlo: str = Zrodlo
    limit_nowych: int = Field(ge=1)
    kanaly: dict[str, KanalRekrutacji]
    wypowiedzenie: list[Wypowiedzenie] = Field(min_length=1)

    @field_validator("kanaly")
    @classmethod
    def _headhunter(cls, v: dict[str, KanalRekrutacji]) -> dict[str, KanalRekrutacji]:
        if "headhunter" not in v or v["headhunter"].podkupienie_czesc_pensji is None:
            raise ValueError("kanał headhunter z podkupienie_czesc_pensji jest wymagany (podkupienia)")
        return v


class PlikKandydatow(Plik):
    znani: list[ZnanyKandydat]
    losowanie: Losowanie
    agencja: Agencja | None = None  # kanały rekrutacji gry z lokalami (F3a.8); katalog Revasa ich nie ma
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


class ZakladkaHarmonogramu(Schemat):
    nazwa: str
    tydzien: int = Field(ge=1)


class HarmonogramLokali(Sekcja):
    zakladki: dict[str, ZakladkaHarmonogramu]


class Rundy(Sekcja):
    kalendarz: Kalendarz
    domyslna_liczba: int = Field(gt=0)
    odblokowanie: dict[str, list[str]]
    harmonogram_lokali: HarmonogramLokali | None = None   # gra z lokalami (F4.3) – zamiast `odblokowanie`
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
    sklep: str | None = None      # gra z lokalami: sklep budowlany / meblowy na mapie (F3a.6)


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


class PromocjaBota(Schemat):
    typ: str
    nazwa: str


class Strategia(Schemat):
    nazwa: str
    min_kuchnia: int = Field(0, ge=0)   # gra z lokalami, bot planujący: najmniej miejsc w kuchni wybieranego lokalu
    cena: float | None  # ułamek ceny preferowanej; None = średnia rynku z poprzedniej rundy
    jakosc: int = Field(ge=1, le=3)
    uslugi: int = Field(gt=0)
    pokrycie: float = Field(gt=0)
    wyposazenie: int = Field(ge=0)
    udogodnienia: int = Field(ge=0)
    reklama: dict[str, int]
    internet: list[str]
    szkolenia: int = Field(ge=0)
    kampanie: list[str] = Field(default_factory=list)   # gra z lokalami: "agencja/kanał" z mapa/reklama.yaml
    promocje: list[PromocjaBota] = Field(default_factory=list)   # gra z lokalami: typy z mapa/promocje.yaml
    polisy: list[str] = Field(default_factory=list)   # gra z lokalami: rodzaje polis z zdarzenia/losowe.yaml
    higiena: str | None = None   # gra z lokalami: poziom higieny z zdarzenia/urzad.yaml (None – domyślny)


class UstawieniaBotow(Schemat):
    bufor_gotowki: float
    bufor_kampanii: float = Field(0, ge=0)   # gra z lokalami: gotówka, która musi zostać po kampaniach reklamowych
    min_sila_kampanii: float = Field(0, ge=0, le=1)   # słabszej (po powtórkach – nasycenie) bot nie zamawia
    min_obsluga_promocji: float = Field(1, ge=0, le=1)   # promocje tylko, gdy w poprzedniej rundzie obsłużył taką
                                                          # część popytu (kuchnia nie nadąża – promocja tylko ucina cenę)
    cena_nasladowcy_bez_danych: float = Field(gt=0)
    krok_ceny: float = Field(gt=0)
    losuj_z_najlepszych_kandydatow: int = Field(gt=0)
    zapas_zasobow: float = Field(ge=1)


class KolejnyLokalBota(Schemat):
    obsluga: float = Field(gt=0, le=1)
    gotowka: float = Field(ge=0)
    maks_lokali: int = Field(ge=1)


class PoziomBota(Schemat):
    """Zachowanie bota na poziomie (gra z lokalami) – opis pól w dane/boty.yaml."""
    nazwa: str
    opis: str
    planowanie: Literal["proste", "przepustowosc"] = "przepustowosc"
    cel_obslugi: float = Field(1.0, gt=0, le=1)
    blad_prognozy: float = Field(0, ge=0, lt=1)
    losowy_kandydat: bool = False
    kampanie: bool = True
    promocje: bool = True
    korekta_prognozy: list[float] | None = Field(None, min_length=2, max_length=2)
    mnozniki_ceny: list[float] = Field(default_factory=list)
    narzut_pracy: float = Field(1.0, ge=1)
    obsluga_kampanii: float | None = Field(None, ge=0, le=1)
    kolejny_lokal: KolejnyLokalBota | None = None
    przewaga_popytu: float = Field(1.0, ge=1)   # niemożliwy: mnożnik atrakcyjności lokali bota (oszustwo)


class PlikBotow(Plik):
    ustawienia: UstawieniaBotow
    strategie: dict[str, Strategia]
    poziomy: dict[str, PoziomBota] | None = None


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
    # licytacje i przejęcia (silnik/przejecia.py)
    licytacje_od_rundy: int = Field(ge=1)      # od tej rundy można przebić cenę wywoławczą (wcześniej remis)
    oferta_max: float = Field(ge=1)            # najwyżej tyle × cena wywoławcza (chroni przed literówką)
    przejecia_od_rundy: int = Field(ge=1)
    wypowiedzenie_rund: int = Field(ge=1)      # KC art. 673, 678
    ulepszenia_zwrot: float = Field(ge=0, le=1)     # część nakładów najemcy, którą płaci zatrzymujący je właściciel
    przywrocenie_koszt: float = Field(ge=0, le=1)   # część nakładów, którą płaci najemca za przywrócenie stanu


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


# --- mapa/banki.yaml (F3a.9) ---


class Terminal(Schemat):
    abonament: float = Field(ge=0)       # miesięczny
    prowizja: float = Field(ge=0, lt=1)  # od płatności kartą


class Limit(Schemat):
    kwota: float = Field(ge=0)
    oprocentowanie: float = Field(ge=0, lt=1)


class ProduktKredytowy(Schemat):
    produkt: Literal["start", "inwestycyjny", "obrotowy"]
    nazwa: str
    oprocentowanie: float = Field(gt=0, lt=1)
    prowizja: float = Field(ge=0, lt=1)
    maks_kwota: float = Field(gt=0)
    maks_rund: int = Field(gt=0)
    historia: bool = False               # wymaga historii firmy (banki.yaml: historia_rund)
    od_lokalu: bool = False              # dla firmy z lokalem (także kupowanym w tej rundzie – może być zastawem)
    zastaw: float | None = Field(default=None, gt=0, le=1)  # część wartości zastawu, którą bank pożycza


class OfertaLeasingu(Schemat):
    wplata: float = Field(ge=0, lt=1)    # wpłata własna – część ceny sprzętu
    oprocentowanie: float = Field(gt=0, lt=1)
    rund: list[int] = Field(min_length=1)
    wykup: float = Field(ge=0, lt=1)


class BankMapy(Schemat):
    nazwa: str
    specjalizacja: str
    opis: str
    konto: float = Field(ge=0)           # miesięczna opłata
    terminal: Terminal
    lokaty: dict[int, float] = Field(min_length=1)   # okres w rundach → oprocentowanie roczne
    limit: Limit
    kredyty: list[ProduktKredytowy] = Field(default_factory=list)
    leasing: OfertaLeasingu | None = None


class PlikBankow(Plik):
    udzial_kart: float = Field(ge=0, le=1)
    historia_rund: int = Field(ge=0)
    stopa_karna: float = Field(gt=0, lt=1)
    przejecie_po: int = Field(gt=0)
    wycena_zastawu: float = Field(gt=0, le=1)
    czynsz_po_przejeciu: float = Field(gt=0, lt=1)
    banki: list[BankMapy] = Field(min_length=1)

    @model_validator(mode="after")
    def _nazwy(self):
        nazwy = [b.nazwa for b in self.banki]
        if len(set(nazwy)) != len(nazwy):
            raise ValueError("nazwy banków muszą być różne")
        return self


# --- mapa/harpagon.yaml ---


class Wizyta(Schemat):
    rodzaj: Literal["szkody", "klienci", "pracownik"]
    waga: float = Field(gt=0)
    koszt: tuple[float, float] | None = None      # szkody: naprawa od–do
    odplyw: float | None = Field(default=None, gt=0, lt=1)   # klienci: tyle mniej gości w tej rundzie
    historie: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _parametry(self):
        if self.rodzaj == "szkody" and not (self.koszt and 0 < self.koszt[0] <= self.koszt[1]):
            raise ValueError("wizyta „szkody” wymaga kosztu [od, do]")
        if self.rodzaj == "klienci" and self.odplyw is None:
            raise ValueError("wizyta „klienci” wymaga odpływu")
        return self


class PlikHarpagona(Plik):
    maks_kwota: float = Field(gt=0)
    min_kwota: float = Field(gt=0)
    oprocentowanie_rundy: float = Field(gt=0, lt=1)
    termin_rund: int = Field(gt=0)
    odsetki_karne_rundy: float = Field(gt=0, lt=1)
    karne_od: int = Field(gt=0)
    wizyty_od: int = Field(gt=0)
    przed_terminem: str
    karne: str
    przypomnienia: list[str] = Field(min_length=1)
    wizyty: list[Wizyta] = Field(min_length=1)


# --- mapa/biura.yaml (F3a.13) ---

class KadryBiura(Schemat):
    w_cenie: int = Field(ge=0)
    etat: float = Field(ge=0)
    zlecenie: float = Field(ge=0)


class BiuroMapy(Schemat):
    id: str
    nazwa: str
    wlasciciel: str | None = None
    opis: str
    ryczalt: float = Field(ge=0)
    dokumenty_w_ryczalcie: int | None = Field(default=None, ge=0)   # None – bez limitu
    za_dokument: float = Field(ge=0)
    minimum: float = Field(ge=0)
    kadry: KadryBiura
    ryzyko_bledu: float = Field(ge=0, lt=1)
    oc: bool


class Samodzielna(Schemat):
    kara_blad: float = Field(gt=0)
    kara_brak: float = Field(gt=0)
    opis: str


class PlikBiur(Plik):
    szacunek_dokumentow: int = Field(gt=0)
    biura: list[BiuroMapy] = Field(min_length=1)
    bledy: list[str] = Field(min_length=1)
    samodzielna: Samodzielna

    @model_validator(mode="after")
    def _unikalne(self):
        ids = [b.id for b in self.biura]
        if len(ids) != len(set(ids)) or "samodzielnie" in ids:
            raise ValueError("id biur muszą być unikalne (i różne od „samodzielnie”)")
        return self


# --- mapa/reklama.yaml (agencje reklamowe, F3b.2) ---


class KanalReklamy(Schemat):
    nazwa: str
    od_rundy: int = Field(ge=1)
    zasieg: Literal["strefa", "miasto"]
    strefy: list[str] | None = None      # tylko te strefy (brak – każda)
    rundy: int = Field(ge=1)
    koszt: float = Field(gt=0)           # netto; zasięg „strefa” – × pula strefy
    pula: float = Field(ge=0, lt=1)
    przyciaganie: float = Field(ge=0, lt=2)
    teksty: list[str] = Field(min_length=1)


class AgencjaReklamowa(Schemat):
    nazwa: str
    budynek: str
    rodzaj: str
    opis: str
    kanaly: dict[str, KanalReklamy] = Field(min_length=1)


class ModelReklamy(Schemat):
    zagluszanie: float = Field(ge=0)
    nasycenie: float = Field(ge=0, lt=1)
    okno_nasycenia: int = Field(ge=1)
    wygasanie: float = Field(ge=0, lt=1)
    prog_wygasania: float = Field(gt=0, le=1)
    maks_przyciagania: float = Field(default=10.0, gt=0)   # P10: sufit sumy kampanii firmy w strefie (nasycenie)
    maks_puli: float = Field(default=10.0, gt=0)           # sufit poszerzenia puli strefy przez wszystkie kampanie


class PlikReklamy(Plik):
    model: ModelReklamy
    agencje: dict[str, AgencjaReklamowa] = Field(min_length=1)


class TypPromocji(Schemat):
    nazwa: str
    opis: str
    zakres: Literal["danie", "wszystkie"]
    dni: list[int] | None = None                 # dni tygodnia (0 = poniedziałek); brak – wszystkie
    strefy_klientow: list[str] | None = None     # klienci z tych stref; brak – wszyscy
    rabat: float = Field(0, ge=0, lt=1)
    porcje: int = Field(1, ge=1)
    doplata: float = Field(0, ge=0)              # zł brutto ponad cenę dania
    koszt_dodatku: float = Field(0, ge=0)        # zł netto za objętego klienta
    przyciaganie: float = Field(ge=0, lt=2)
    przyrost: float = 0                          # zmiana przyciągania z każdą rundą trwania
    przyciaganie_min: float = Field(ge=0)
    przyciaganie_max: float = Field(ge=0, lt=2)
    koszt_startu: float = Field(ge=0)            # netto
    teksty: list[str] = Field(min_length=1)

    @field_validator("dni")
    @classmethod
    def _dni(cls, v):
        if v is not None and (not v or any(not 0 <= d <= 6 for d in v) or len(set(v)) != len(v)):
            raise ValueError("dni: różne liczby 0–6 (0 = poniedziałek)")
        return v

    @model_validator(mode="after")
    def _przedzial(self):
        if not self.przyciaganie_min <= self.przyciaganie <= self.przyciaganie_max:
            raise ValueError("przyciaganie poza przyciaganie_min–przyciaganie_max")
        return self


class PlikPromocji(Plik):
    od_rundy: int = Field(ge=1)
    limit_aktywnych: int = Field(ge=1)
    nazwa_max: int = Field(ge=1)
    typy: dict[str, TypPromocji] = Field(min_length=1)


SCHEMATY_MAPY: dict[str, type[BaseModel]] = {
    "strefy.yaml": PlikStref,
    "lokale.yaml": PlikLokali,
    "budynki.yaml": PlikBudynkow,
    "popyt.yaml": PlikPopytu,
    "menu.yaml": PlikMenu,
    "banki.yaml": PlikBankow,
    "harpagon.yaml": PlikHarpagona,
    "biura.yaml": PlikBiur,
    "reklama.yaml": PlikReklamy,
    "promocje.yaml": PlikPromocji,
}

# --- podatki_2026.yaml (gra z lokalami, F3a.11) ---

Stawka = Field(ge=0, lt=1)


class Zdrowotna(Schemat):
    stawka: float = Stawka
    minimalna_miesieczna: float = Field(ge=0)
    limit_odliczenia_roczny: float = Field(ge=0)


class ZusWlasciciela(Schemat):
    ulga_na_start_rund: int = Field(ge=0)
    spoleczne_miesieczne: float = Field(ge=0)


class VatSprzedazy(Schemat):
    domyslna: float = Stawka
    uslugi: dict[str, float] = {}


class VatZasobow(Schemat):
    domyslna: float = Stawka
    zasoby: dict[str, float] = {}


class RegulaVat(Schemat):
    zawiera: str = Field(min_length=3)
    stawka: float = Stawka


class Vat(Schemat):
    sprzedaz: VatSprzedazy
    zasoby: VatZasobow
    koszty: list[RegulaVat]
    srodki_trwale: float = Stawka


class PlikPodatkow(Plik):
    pit_liniowy: float = Stawka
    zdrowotna: Zdrowotna
    zus_wlasciciela: ZusWlasciciela
    vat: Vat
    zus_pracodawcy: float = Stawka


# --- zdarzenia/*.yaml (eventy w parkach F3b.1; katalog opcjonalny – bez niego gra bez eventów) ---


class KosztOpcji(Schemat):
    czas: float = Field(default=0, ge=0)       # godziny właściciela
    gotowka: float = Field(default=0, ge=0)    # zł
    porcje: int = Field(default=0, ge=0)       # porcje jedzenia (zasady.koszt_porcji zł)


SKUTKI_POLA = {"kwota": ("gotowka", "szkoda"), "mnoznik": ("popyt",), "godziny": ("czas",), "kandydat": ("kandydat",),
               "szansa": ("kontrola",)}


class Skutek(Schemat):
    # oddaj_zapas – tylko bank żywności; szkoda – tylko wypadki w lokalu (losowe.yaml, silnik/awarie.py);
    # kontrola – skarga do sanepidu: większa szansa kontroli (silnik/urzad.py)
    typ: Literal["gotowka", "popyt", "czas", "kandydat", "oddaj_zapas", "szkoda", "kontrola"]
    opis: str = Field(min_length=3)
    kwota: float | None = None                          # gotowka: + przychód, − koszt; szkoda: koszt (> 0)
    polisa: str | None = None                           # szkoda: rodzaj polisy, która ją pokrywa (None – żadna)
    mnoznik: float | None = Field(default=None, gt=0)    # popyt: mnożnik atrakcyjności lokali
    godziny: float | None = Field(default=None, gt=0)    # czas: o tyle mniej godzin właściciela
    szansa: float | None = Field(default=None, gt=0, le=1)   # kontrola: dodatek do szansy kontroli sanepidu
    rund: int = Field(default=1, ge=1)
    kandydat: ZnanyKandydat | None = None               # kandydat: osoba tylko dla tej drużyny

    @model_validator(mode="after")
    def _pola(self):
        for pole, typy in SKUTKI_POLA.items():
            if (getattr(self, pole) is not None) != (self.typ in typy):
                raise ValueError(f"skutek typu {self.typ}: pole {pole} " + ("wymagane" if self.typ in typy else "zbędne"))
        if self.typ == "szkoda" and self.kwota <= 0:
            raise ValueError("szkoda: kwota musi być dodatnia")
        if self.polisa is not None and self.typ != "szkoda":
            raise ValueError(f"skutek typu {self.typ}: pole polisa zbędne")
        return self


class Nastepna(Schemat):
    scena: str
    za_ile_rund: int = Field(default=1, ge=1)
    szansa: float = Field(default=1, gt=0, le=1)


def _szanse(nastepne: list[Nastepna]):
    if sum(n.szansa for n in nastepne) > 1 + 1e-9:
        raise ValueError("szanse kolejnych scen sumują się do więcej niż 1")


class Opcja(Schemat):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    tekst: str = Field(min_length=3)
    koszt: KosztOpcji = Field(default_factory=KosztOpcji)
    wynik: str = Field(min_length=3)
    skutki: list[Skutek] = []
    nastepna: list[Nastepna] = []

    @model_validator(mode="after")
    def _sprawdz(self):
        _szanse(self.nastepna)
        return self


class Scena(Schemat):
    """Scena z opcjami (skutki i ciąg dalszy przy opcjach) albo scena końcowa / przejściowa bez wyboru."""
    tekst: str = Field(min_length=3)
    opcje: list[Opcja] = []
    domyslna: str | None = None
    skutki: list[Skutek] = []
    nastepna: list[Nastepna] = []

    @model_validator(mode="after")
    def _sprawdz(self):
        _szanse(self.nastepna)
        if not self.opcje:
            if self.domyslna is not None:
                raise ValueError("scena bez opcji nie ma opcji domyślnej")
            return self
        ids = [o.id for o in self.opcje]
        if len(ids) != len(set(ids)):
            raise ValueError("id opcji muszą być unikalne")
        if self.skutki or self.nastepna:
            raise ValueError("w scenie z opcjami skutki i ciąg dalszy są przy opcjach")
        dom = next((o for o in self.opcje if o.id == self.domyslna), None)
        if dom is None:
            raise ValueError(f"opcja domyślna {self.domyslna!r} nie jest jedną z opcji")
        if dom.koszt.czas:
            raise ValueError("opcja domyślna nie może wymagać czasu właściciela")
        return self


class Historia(Schemat):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    park: str | None = None  # id budynku z mapa/budynki.yaml (park albo woda); w parkach wymagany
    tytul: str = Field(min_length=3)
    powazna: bool = False    # ok. 80% historii ma być komicznych (notatka „Zdarzenia i historie”)
    start: str
    sceny: dict[str, Scena]

    @model_validator(mode="after")
    def _graf(self):
        def dalej(s: Scena) -> list[str]:
            return [n.scena for n in [*s.nastepna, *(x for o in s.opcje for x in o.nastepna)]]

        for nazwa, s in self.sceny.items():
            for n in dalej(s):
                if n not in self.sceny:
                    raise ValueError(f"scena {nazwa}: nie ma sceny {n!r}")
        if self.start not in self.sceny:
            raise ValueError(f"nie ma sceny startowej {self.start!r}")
        stan: dict[str, int] = {}   # 1 – w trakcie, 2 – sprawdzona

        def odwiedz(n: str):
            if stan.get(n) == 1:
                raise ValueError(f"historia zapętla się na scenie {n!r} – każda ścieżka musi się kończyć")
            if stan.get(n) == 2:
                return
            stan[n] = 1
            for m in dalej(self.sceny[n]):
                odwiedz(m)
            stan[n] = 2

        odwiedz(self.start)
        if nieosiagalne := sorted(set(self.sceny) - set(stan)):
            raise ValueError(f"sceny nieosiągalne ze startu: {', '.join(nieosiagalne)}")
        return self


class ZasadyZdarzen(Schemat):
    od_rundy: int = Field(ge=1)
    koszt_porcji: float = Field(gt=0)
    eventow_na_runde: tuple[int, int] = (1, 1)   # [min, max] – ile historii zaczyna się w parkach w jednej rundzie

    @model_validator(mode="after")
    def _zakres(self):
        if not 1 <= self.eventow_na_runde[0] <= self.eventow_na_runde[1]:
            raise ValueError("eventow_na_runde: [min, max], 1 <= min <= max")
        return self


def skutki_historii(h: Historia) -> list[Skutek]:
    return [sk for s in h.sceny.values() for sk in [*s.skutki, *(x for o in s.opcje for x in o.skutki)]]


def _bez_skutku(historie: list[Historia], typ: str, gdzie: str):
    if inne := sorted({h.id for h in historie for sk in skutki_historii(h) if sk.typ == typ}):
        raise ValueError(f"skutek {typ} jest tylko w {gdzie}: {', '.join(inne)}")


def _unikalne_id(historie: list[Historia]):
    ids = [h.id for h in historie]
    if len(ids) != len(set(ids)):
        raise ValueError("id historii muszą być unikalne")


class PlikParkow(Plik):
    zasady: ZasadyZdarzen
    historie: list[Historia] = Field(min_length=1)

    @model_validator(mode="after")
    def _unikalne(self):
        _unikalne_id(self.historie)
        if bez := [h.id for h in self.historie if not h.park]:
            raise ValueError(f"historie w parkach muszą mieć park: {', '.join(bez)}")
        _bez_skutku(self.historie, "oddaj_zapas", "historii banku żywności")
        _bez_skutku(self.historie, "szkoda", "wypadkach w lokalu (losowe.yaml)")
        return self


class ZasadyWypadkow(Schemat):
    od_rundy: int = Field(ge=1)
    szansa: float = Field(gt=0, le=1)      # na rundę i drużynę z działającym lokalem
    max_strata: float = Field(gt=0)        # zł – górna granica jednej szkody
    przyrost: float = Field(default=0, ge=0)     # P11: + za każdą rundę bez wypadku (reset po wypadku)
    szansa_max: float = Field(default=1, gt=0, le=1)


class Polisa(Schemat):
    nazwa: str
    opis: str
    stala: float = Field(ge=0)             # zł miesięcznie
    za_lokal: float = Field(ge=0)          # zł miesięcznie za każdy lokal
    od_majatku: float = Field(ge=0, lt=1)  # miesięcznie, ułamek majątku (ceny zakupu inwestycji)
    pokrycie: float = Field(gt=0, le=1)    # część szkody ponad franszyzę, którą zwraca ubezpieczyciel
    franszyza: float = Field(ge=0)         # zł – tę część szkody firma zawsze pokrywa sama


class Ubezpieczyciel(Schemat):
    nazwa: str
    budynek: str | None                    # id z mapa/budynki.yaml
    karencja_rund: int = Field(ge=0)
    polisy: dict[str, Polisa] = Field(min_length=1)

    @model_validator(mode="after")
    def _skladki(self):
        if bez := [k for k, p in self.polisy.items() if not (p.stala or p.za_lokal or p.od_majatku)]:
            raise ValueError(f"polisy bez składki: {', '.join(bez)}")
        return self


class PlikWypadkow(Plik):
    """dane/zdarzenia/losowe.yaml: wypadki w lokalu jednej drużyny i polisy ubezpieczyciela (silnik/awarie.py)."""
    zasady: ZasadyWypadkow
    ubezpieczyciel: Ubezpieczyciel
    historie: list[Historia] = Field(min_length=1)

    @model_validator(mode="after")
    def _sprawdz(self):
        _unikalne_id(self.historie)
        if w_parku := [h.id for h in self.historie if h.park]:
            raise ValueError(f"wypadki dzieją się w lokalu (bez pola park): {', '.join(w_parku)}")
        _bez_skutku(self.historie, "oddaj_zapas", "historii banku żywności")
        for h in self.historie:
            for sk in skutki_historii(h):
                if sk.polisa is not None and sk.polisa not in self.ubezpieczyciel.polisy:
                    raise ValueError(f"{h.id}: nieznana polisa {sk.polisa!r} (ubezpieczyciel.polisy)")
        return self


class TekstySanepidu(Schemat):
    kontrole_ok: list[str] = Field(min_length=1)
    kontrole_mandat: list[str] = Field(min_length=1)


class ZasadyBanku(Schemat):
    prog_zl: float = Field(gt=0)
    dni_do_terminu: int = Field(ge=0)
    szansa: float = Field(gt=0, le=1)


class BankZywnosci(Schemat):
    zasady: ZasadyBanku
    historia: Historia

    @model_validator(mode="after")
    def _bez_parku(self):
        if self.historia.park:
            raise ValueError("historia banku żywności nie dzieje się w parku (bez pola park)")
        _bez_skutku([self.historia], "szkoda", "wypadkach w lokalu (losowe.yaml)")
        return self


class PlikMagazynu(Plik):
    """dane/zdarzenia/magazyn.yaml: teksty kontroli sanepidu i historia „bank żywności” (silnik/magazyn.py)."""
    sanepid: TekstySanepidu
    bank_zywnosci: BankZywnosci


class Rejestracja(Schemat):
    pkd: str
    opis_pkd: str
    tekst: str = Field(min_length=3)


class Urzad(Schemat):
    nazwa: str
    budynek: str | None                    # id z mapa/budynki.yaml
    rejestracja: Rejestracja


class Odbior(Schemat):
    odroczenie_rund: int = Field(ge=1)
    teksty_ok: list[str] = Field(min_length=1)
    teksty_odmowa: list[str] = Field(min_length=1)


class PoziomHigieny(Schemat):
    nazwa: str
    opis: str
    koszt: float = Field(ge=0)             # zł miesięcznie (brutto) za działający lokal
    dodatek: float = Field(ge=0, le=1)     # do części szansy kontroli z problemów
    mnoznik: float = Field(gt=0)           # mnoży część szansy z problemów (z dodatkami)
    mandat: float = Field(ge=0)            # zł – doliczane do mandatu
    odbior: bool                           # czy sanepid odbierze lokal przy tym poziomie


class Higiena(Schemat):
    domyslna: str
    poziomy: dict[str, PoziomHigieny] = Field(min_length=1)

    @model_validator(mode="after")
    def _domyslna(self):
        if self.domyslna not in self.poziomy:
            raise ValueError(f"higiena.domyslna {self.domyslna!r} nie jest poziomem")
        if not self.poziomy[self.domyslna].odbior:
            raise ValueError("higiena.domyslna musi pozwalać na odbiór lokalu")
        return self


class PlikUrzedu(Plik):
    """dane/zdarzenia/urzad.yaml: rejestracja firmy, odbiór lokalu i higiena (silnik/urzad.py)."""
    urzad: Urzad
    odbior: Odbior
    higiena: Higiena


class Portfel(Schemat):
    oszczednosci: float = Field(ge=0)      # zł prywatnych oszczędności właściciela na start


class PlikWlasciciela(Plik):
    """dane/zdarzenia/wlasciciel.yaml: prywatny portfel właściciela – wpłaty i wypłaty własne (silnik/wlasciciel.py)."""
    portfel: Portfel


class Klub(Schemat):
    nazwa: str
    adres: str
    tekst: str = Field(min_length=3)


class Zaproszenie(Schemat):
    od_rundy: int = Field(ge=1)
    szansa: float = Field(ge=0, le=1)
    maks: int = Field(ge=0)
    teksty: list[str] = Field(min_length=1)


class LimitZakladow(Schemat):
    maks: int = Field(ge=1)
    min_stawka: float = Field(gt=0)
    maks_stawka: float = Field(gt=0)

    @model_validator(mode="after")
    def _zakres(self):
        if self.min_stawka > self.maks_stawka:
            raise ValueError("zaklady.min_stawka większa niż maks_stawka")
        return self


class ZakladRuletki(Schemat):
    nazwa: str
    mnoznik: float = Field(gt=0)           # wypłata = stawka × mnożnik (razem ze stawką)
    wygrywa: list[int] = Field(min_length=1)


class WynikAutomatu(Schemat):
    szansa: float = Field(gt=0, le=1)
    mnoznik: float = Field(ge=0)
    tekst: str = Field(min_length=3)


class GraKasyna(Schemat):
    typ: Literal["ruletka", "automat"]
    nazwa: str
    opis: str
    pola: int | None = None                # ruletka: liczba pól koła (0 … pola−1)
    zaklady: dict[str, ZakladRuletki] | None = None
    teksty_wygrana: list[str] | None = None
    teksty_przegrana: list[str] | None = None
    wyniki: list[WynikAutomatu] | None = None

    @model_validator(mode="after")
    def _typ(self):
        if self.typ == "ruletka":
            if not (self.pola and self.zaklady and self.teksty_wygrana and self.teksty_przegrana) or self.wyniki:
                raise ValueError(f"ruletka {self.nazwa!r}: potrzebne pola, zaklady i teksty (bez wyniki)")
            for k, z in self.zaklady.items():
                if any(not 0 <= n < self.pola for n in z.wygrywa) or len(set(z.wygrywa)) != len(z.wygrywa):
                    raise ValueError(f"ruletka {self.nazwa!r}, zakład {k!r}: liczby spoza koła albo powtórzone")
        else:
            if not self.wyniki or self.zaklady or self.pola:
                raise ValueError(f"automat {self.nazwa!r}: potrzebne wyniki (bez pola i zaklady)")
            if abs(sum(w.szansa for w in self.wyniki) - 1) > 1e-6:
                raise ValueError(f"automat {self.nazwa!r}: szanse wyników nie sumują się do 1")
        return self


class PlikKasyna(Plik):
    """dane/zdarzenia/kasyno.yaml: tajny klub, zaproszenia i gry (silnik/kasyno.py)."""
    kasyno: Klub
    zaproszenie: Zaproszenie
    zaklady: LimitZakladow
    gry: dict[str, GraKasyna] = Field(min_length=1)


class ZasadyHandlu(Schemat):
    od_rundy: int = Field(ge=1)
    maks_ofert: int = Field(ge=1)          # ofert wystawionych przez drużynę w jednej rundzie
    cena_min: float = Field(gt=0)          # widełki ceny jako część wartości (towar – koszt zakupu, sprzęt – katalog)
    cena_maks: float = Field(gt=0)
    maks_kontr: int = Field(default=3, ge=0)   # P13: kontrofert w jednej negocjacji (obie strony razem)


class PlikHandlu(Plik):
    """dane/zdarzenia/handel.yaml: handel między drużynami – towar i sprzęt z fakturą (silnik/handel.py)."""
    handel: ZasadyHandlu
    teksty: list[str] = Field(min_length=1)   # przekazanie: {sprzedawca}, {kupujacy}, {co}

    @model_validator(mode="after")
    def _widelki(self):
        if self.handel.cena_min > self.handel.cena_maks:
            raise ValueError("handel: cena_min większa niż cena_maks")
        return self


class ZasadyDetektywa(Schemat):
    nazwa: str
    budynek: str | None = None              # budynek na mapie (mapa/budynki.yaml)
    od_rundy: int = Field(ge=2)             # tydzień 1 jest przygotowawczy
    koszt_min: float = Field(gt=0)          # zł brutto za zlecenie, losowane co rundę
    koszt_maks: float = Field(gt=0)
    krok: float = Field(gt=0)
    godziny: float = Field(ge=0)            # godziny właściciela
    szansa_wpadki: float = Field(ge=0, le=1)


class PlikDetektywa(Plik):
    """dane/zdarzenia/detektyw.yaml: przegląd konkurencji i detektyw (silnik/konkurencja.py, P16)."""
    detektyw: ZasadyDetektywa
    powitania: list[str] = Field(min_length=1)
    raporty: list[str] = Field(min_length=1)    # {rywal}
    wpadki: list[str] = Field(min_length=1)     # zleceniodawca: {rywal}
    ofiary: list[str] = Field(min_length=1)     # śledzony: {kto}

    @model_validator(mode="after")
    def _widelki(self):
        if self.detektyw.koszt_min > self.detektyw.koszt_maks:
            raise ValueError("detektyw: koszt_min większy niż koszt_maks")
        return self


SCHEMATY_ZDARZEN: dict[str, type[BaseModel]] = {
    "parki.yaml": PlikParkow,
    "magazyn.yaml": PlikMagazynu,
    "losowe.yaml": PlikWypadkow,
    "urzad.yaml": PlikUrzedu,
    "wlasciciel.yaml": PlikWlasciciela,
    "kasyno.yaml": PlikKasyna,
    "handel.yaml": PlikHandlu,
    "detektyw.yaml": PlikDetektywa,
}


# --- kalendarz/kalendarz.yaml (F3b.9) ---

DATA_MD = r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"   # 'MM-DD'


class WydarzenieKalendarza(Schemat):
    nazwa: str
    rodzaj: str
    opis: str = Field(min_length=3)
    od: str | int                 # 'MM-DD' albo – z `wzgledem` – dni od daty ruchomej
    do: str | int
    wzgledem: str | None = None   # klucz z `ruchome` (np. wielkanoc)
    strefy: dict[str, float] = Field(min_length=1)
    dania: dict[str, float] = Field(default_factory=dict)   # P14: mnożnik popytu na danie w strefach wydarzenia
    rok: int | None = None        # wydarzenie jednego roku (np. mecz z terminarza); None – co roku

    @model_validator(mode="after")
    def _daty(self):
        if self.wzgledem is None:
            if not all(isinstance(x, str) and re.match(DATA_MD, x) for x in (self.od, self.do)):
                raise ValueError("od i do: data 'MM-DD' (albo `wzgledem` i przesunięcie w dniach)")
        elif not (isinstance(self.od, int) and isinstance(self.do, int) and self.od <= self.do):
            raise ValueError("z `wzgledem` od i do to liczby dni, od ≤ do")
        if any(m < 0 for m in self.strefy.values()):
            raise ValueError("mnożniki stref nie mogą być ujemne")
        if any(m < 0 for m in self.dania.values()):
            raise ValueError("mnożniki dań nie mogą być ujemne")
        return self


class PlikKalendarza(Plik):
    rodzaje: dict[str, str] = Field(min_length=1)
    ruchome: dict[str, dict[int, str]]
    wydarzenia: list[WydarzenieKalendarza]

    @model_validator(mode="after")
    def _odwolania(self):
        for n, lata in self.ruchome.items():
            if any(not re.match(DATA_MD, d) for d in lata.values()):
                raise ValueError(f"ruchome.{n}: daty 'MM-DD'")
        for w in self.wydarzenia:
            if w.rodzaj not in self.rodzaje:
                raise ValueError(f"{w.nazwa}: rodzaj {w.rodzaj!r} – nie ma w `rodzaje`")
            if w.wzgledem is not None and w.wzgledem not in self.ruchome:
                raise ValueError(f"{w.nazwa}: wzgledem {w.wzgledem!r} – nie ma w `ruchome`")
        return self


SCHEMATY_KALENDARZA: dict[str, type[BaseModel]] = {"kalendarz.yaml": PlikKalendarza}


SCHEMATY: dict[str, type[BaseModel]] = {
    "uslugi.yaml": PlikUslug,
    "sprzet.yaml": PlikSprzetu,
    "zasoby.yaml": PlikZasobow,
    "dostawcy.yaml": PlikDostawcow,
    "kandydaci.yaml": PlikKandydatow,
    "katalog.yaml": PlikKatalogu,
    "boty.yaml": PlikBotow,
    "podatki_2026.yaml": PlikPodatkow,
}
OPCJONALNE = {"podatki_2026.yaml"}   # wzorzec Revasa (bez lokali) nie ma podatków JDG
