"""Stan gry: firmy, stanowiska, pracownicy, magazyn, bank. Wszystko daje się zapisać do JSON (do_slownika)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Pracownik:
    id: str
    imie_nazwisko: str
    zawod: str
    gwiazdki: int
    pensja_preferowana: float
    koszt_rekrutacji: float
    koszt_odprawy: float
    zadowolenie_klientow: float
    ryzyko_reklamacji: float
    pensja: float = 0.0
    umowa: str = "prace"          # "prace" (umowa o pracę, + ZUS) albo "zlecenie"
    od_rundy: int = 0
    stanowisko: int = 0           # numer stanowiska (od 1) w grupie: instruktor/trener albo recepcja
    premia: float = 0.0           # premia w bieżącej rundzie


@dataclass
class Stanowisko:
    nr: int
    typ: str                      # "instruktor" (instruktor/trener) albo "recepcja"
    sprzet: dict[str, int] = field(default_factory=dict)   # nazwa → jakość 1–3
    pracownik: str | None = None
    od_rundy: int = 0


@dataclass
class Lokata:
    id: int
    kwota: float
    oprocentowanie: float
    od_rundy: int
    miesiecy: int


@dataclass
class Kredyt:
    id: int
    kwota: float
    oprocentowanie: float
    od_rundy: int
    miesiecy: int
    pozostalo: float


@dataclass
class Firma:
    nazwa: str
    bot: str | None = None
    nazwa_wyswietlana: str = ""
    misja: str = ""
    gotowka: float = 0.0
    stanowiska: list[Stanowisko] = field(default_factory=list)
    pracownicy: dict[str, Pracownik] = field(default_factory=dict)
    magazyn: dict[str, float] = field(default_factory=dict)          # "zasób|jakość" → opakowania
    wartosc_magazynu: dict[str, float] = field(default_factory=dict) # "zasób|jakość" → PLN (średni koszt)
    oferta: dict[str, int] = field(default_factory=dict)             # usługa → prognoza popytu na miesiąc
    uslugi_kiedykolwiek: list[str] = field(default_factory=list)
    ceny: dict[str, dict] = field(default_factory=dict)              # usługa → {"cena", "rabat"} (włączona sprzedaż)
    udogodnienia: list[str] = field(default_factory=list)
    wyposazenie: list[str] = field(default_factory=list)
    internet: dict[str, int] = field(default_factory=dict)           # narzędzie → runda uruchomienia
    bank: str | None = None
    biuro: str | None = None
    lokaty: list[Lokata] = field(default_factory=list)
    kredyty: list[Kredyt] = field(default_factory=list)
    kredyt_odnawialny: float = 0.0
    majatek: float = 0.0              # suma inwestycji (sprzęt, stanowiska, udogodnienia, wyposażenie) – rozwój firmy
    rozwoj_poprzedni: float | None = None
    skumulowany_dochod_netto: float = 0.0
    poprzednio_uslug: int = 0         # liczba usług i pracowników w poprzedniej rundzie (przyrost → rozwój firmy)
    poprzednio_pracownikow: int = 0
    utracona_poprzednio: float = 0.0  # udział utraconej sprzedaży w poprzedniej rundzie (zadowolenie klientów)
    baza_klientow: float = 1.0        # trwała utrata klientów po utraconej sprzedaży (mnożnik popytu firmy)
    licznik: int = 0                  # do numerowania lokat i kredytów

    def stanowiska_typu(self, typ: str) -> list[Stanowisko]:
        return [s for s in self.stanowiska if s.typ == typ]

    def stanowisko(self, typ: str, nr: int) -> Stanowisko | None:
        return next((s for s in self.stanowiska if s.typ == typ and s.nr == nr), None)

    def pracownik_stanowiska(self, s: Stanowisko) -> Pracownik | None:
        return self.pracownicy.get(s.pracownik) if s.pracownik else None


@dataclass
class StanGry:
    runda: int                                   # ostatnia przeliczona runda (0 = przed grą)
    firmy: dict[str, Firma]
    kandydaci: list[dict]                        # dostępni na rynku pracy
    wyniki: dict[int, dict[str, dict]] = field(default_factory=dict)   # runda → firma → wyniki
    rynek: dict[int, dict] = field(default_factory=dict)               # runda → dane publiczne rynku


def do_slownika(obiekt) -> dict:
    return asdict(obiekt)


def firma_z_slownika(d: dict) -> Firma:
    f = Firma(**{k: v for k, v in d.items() if k not in ("stanowiska", "pracownicy", "lokaty", "kredyty")})
    f.stanowiska = [Stanowisko(**s) for s in d.get("stanowiska", [])]
    f.pracownicy = {k: Pracownik(**p) for k, p in d.get("pracownicy", {}).items()}
    f.lokaty = [Lokata(**x) for x in d.get("lokaty", [])]
    f.kredyty = [Kredyt(**x) for x in d.get("kredyty", [])]
    return f
