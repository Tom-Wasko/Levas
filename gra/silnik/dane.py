"""Dane gry i założenia (`dane/*.yaml`) w jednym obiekcie.

Każdy plik ma `opis` i `zrodlo`; schematy w `silnik/schematy.py`. Sprawdzenie danych (schematy i odwołania
między plikami, np. sprzęt usługi musi być w `sprzet.yaml`):

    python -m silnik.dane sprawdz
"""
from __future__ import annotations

import hashlib
import sys
from datetime import date, timedelta
from functools import cached_property, lru_cache
from pathlib import Path

import yaml
from pydantic import ValidationError

from .schematy import SCHEMATY, sprawdz_zalozenia

KATALOG_GRY = Path(__file__).resolve().parents[1]
KATALOG_DANYCH = KATALOG_GRY / "dane"
KATALOG_REVAS = KATALOG_GRY / "dane_revas"   # dane oryginalnej gry REVAS (fitness) – wzorzec do testów mechaniki

MIESIACE = ["styczen", "luty", "marzec", "kwiecien", "maj", "czerwiec", "lipiec", "sierpien", "wrzesien",
            "pazdziernik", "listopad", "grudzien"]
MIESIACE_NAZWY = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień",
                  "Październik", "Listopad", "Grudzień"]
# Słowa okresu rundy (katalog.yaml: rundy.kalendarz.okres)
OKRESY = {
    "tydzien": {"mianownik": "tydzień", "dopelniacz": "tygodnia", "miejscownik": "tygodniu", "skrot": "tydz.",
                "przymiotnik": "Tygodniowy", "mnoga": "tygodnie"},
    "miesiac": {"mianownik": "miesiąc", "dopelniacz": "miesiąca", "miejscownik": "miesiącu", "skrot": "mies.",
                "przymiotnik": "Miesięczny", "mnoga": "miesiące"},
}
# Typy stanowisk (budowa modelu): kuchnia – pracownicy przygotowują dania, kasa – obsługa klientów.
# Nazwy i zawody typów są w katalog.yaml: stanowiska.typy.
KUCHNIA, KASA = "kuchnia", "kasa"
TYPY_STANOWISK = (KUCHNIA, KASA)

_Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def _wczytaj(plik: Path):
    return yaml.load(plik.read_text(encoding="utf-8"), Loader=_Loader)


def _wartosci(wezel):
    """Z drzewa założeń zostawia same wartości: {"a": {"wartosc": 1, ...}} → {"a": 1}."""
    if isinstance(wezel, dict):
        if "wartosc" in wezel:
            return wezel["wartosc"]
        return {k: _wartosci(v) for k, v in wezel.items() if k != "opis"}
    return wezel


class Dane:
    def __init__(self, katalog: Path = KATALOG_DANYCH):
        self.katalog = katalog
        self.pliki: dict[str, dict] = {p.name: _wczytaj(p) for p in sorted(katalog.glob("*.yaml"))}
        p = self.pliki
        self.uslugi: dict = p["uslugi.yaml"]["uslugi"]
        self.pensje_recepcji: dict = p["uslugi.yaml"]["pensje_rynkowe_recepcji"]
        self.sprzet: dict = p["sprzet.yaml"]["sprzet"]
        self.zasoby: dict = p["zasoby.yaml"]["zasoby"]          # kolejność = kolejność w raportach
        self.dostawcy: dict = p["dostawcy.yaml"]["ceny"]
        self.dostawcy_pierwsi: list[str] = p["dostawcy.yaml"]["pierwsi"]
        self.dostawcy_wszyscy_od: int = MIESIACE.index(p["dostawcy.yaml"]["wszyscy_od_miesiaca"])
        self.kandydaci: list = p["kandydaci.yaml"]["znani"]
        self.rynek_pracy: dict = p["kandydaci.yaml"]
        self.katalog_ofert: dict = p["katalog.yaml"]
        kal = self.katalog_ofert["rundy"]["kalendarz"]
        kal["start"] = str(kal["start"])  # YAML daje datę – w słownikach (i JSON-ie dla strony) tekst ISO
        self.typy_stanowisk: dict = self.katalog_ofert["stanowiska"]["typy"]
        self.boty: dict = p["boty.yaml"]
        self.zalozenia_pelne: dict = p["zalozenia.yaml"]
        self.z: dict = _wartosci(self.zalozenia_pelne)

    @cached_property
    def sprzet_kasy(self) -> list[str]:
        return [n for n, s in self.sprzet.items() if s["dla"] == KASA]

    @cached_property
    def zawody(self) -> list[str]:
        """Wszystkie zawody: najpierw kuchni, potem kasy (kolejność jak w raportach)."""
        return [z for t in TYPY_STANOWISK for z in self.typy_stanowisk[t]["zawody"]]

    def zawody_typu(self, typ: str) -> list[str]:
        return self.typy_stanowisk[typ]["zawody"]

    def typ_zawodu(self, zawod: str) -> str:
        """Typ stanowiska, na którym pracuje zawód."""
        return KASA if zawod in self.zawody_typu(KASA) else KUCHNIA

    @cached_property
    def wersja(self) -> str:
        """Skrót danych i założeń – w grze wieloosobowej wszyscy muszą mieć ten sam."""
        h = hashlib.sha256()
        for plik in sorted(self.katalog.glob("*.yaml")):
            h.update(plik.read_bytes())
        return h.hexdigest()[:12]

    @cached_property
    def maks_nowych_stanowisk(self) -> int:
        """Największy pakiet stanowisk kupowany w jednej rundzie."""
        return max(int(n) for n in self.katalog_ofert["stanowiska"]["pakiety"])

    # --- kalendarz rund -------------------------------------------------------------------------
    # Dane (pensje, czynsz, utrzymanie, opłaty) są w złotych na miesiąc; silnik księguje je na rundę (na_runde).
    @property
    def kalendarz(self) -> dict:
        return self.katalog_ofert["rundy"]["kalendarz"]

    @property
    def rund_w_roku(self) -> int:
        return int(self.kalendarz["rund_w_roku"])

    @property
    def tygodniowe(self) -> bool:
        return self.kalendarz["okres"] == "tydzien"

    @property
    def okres(self) -> dict[str, str]:
        """Słowa okresu rundy, np. {"mianownik": "tydzień", "dopelniacz": "tygodnia", …}."""
        return OKRESY[self.kalendarz["okres"]]

    def na_runde(self, kwota_miesieczna: float) -> float:
        """Kwota miesięczna z danych przeliczona na jedną rundę (runda miesięczna – bez zmian)."""
        if self.rund_w_roku == 12:
            return kwota_miesieczna
        return round(kwota_miesieczna * 12 / self.rund_w_roku, 2)

    def data_rundy(self, runda: int) -> date:
        """Pierwszy dzień rundy."""
        s = date.fromisoformat(self.kalendarz["start"])
        if self.tygodniowe:
            return s + timedelta(days=7 * (runda - 1))
        m = s.month - 1 + runda - 1
        return date(s.year + m // 12, m % 12 + 1, 1)

    def miesiac_rundy(self, runda: int) -> int:
        """Miesiąc rundy (0 = styczeń) – do sezonowości i cen dostawców; tydzień należy do miesiąca swojego czwartku."""
        d = self.data_rundy(runda)
        return ((d + timedelta(days=3)) if self.tygodniowe else d).month - 1

    def nazwa_rundy(self, runda: int) -> str:
        """„Tydzień 3 (19–25.10)” albo „Luty”."""
        if not self.tygodniowe:
            return MIESIACE_NAZWY[self.miesiac_rundy(runda)]
        a = self.data_rundy(runda)
        b = a + timedelta(days=6)
        od = f"{a.day}" if a.month == b.month else f"{a.day}.{a.month:02d}"
        return f"Tydzień {runda} ({od}–{b.day}.{b.month:02d})"

    def skrot_rundy(self, runda: int) -> str:
        """Etykieta osi wykresów: „T3” albo „Lut”."""
        return f"T{runda}" if self.tygodniowe else MIESIACE_NAZWY[self.miesiac_rundy(runda)][:3]

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


def sprawdz(katalog: Path = KATALOG_DANYCH) -> list[str]:
    """Błędy danych: brakujące pliki, schematy, założenia i odwołania między plikami (pusta lista = dane dobre)."""
    bledy = []
    for nazwa in [*SCHEMATY, "zalozenia.yaml"]:
        if not (katalog / nazwa).exists():
            bledy.append(f"brak pliku dane/{nazwa}")
    if bledy:
        return bledy
    pliki = {p.name: _wczytaj(p) for p in sorted(katalog.glob("*.yaml"))}
    for nazwa, schemat in SCHEMATY.items():
        try:
            schemat.model_validate(pliki[nazwa])
        except ValidationError as e:
            for b in e.errors():
                bledy.append(f"{nazwa}: {'.'.join(map(str, b['loc']))}: {b['msg']}")
    bledy += sprawdz_zalozenia(pliki["zalozenia.yaml"])
    if bledy:
        return bledy

    d = Dane(katalog)

    def brak(co: str, gdzie: str, czego: str, plik: str):
        bledy.append(f"{gdzie}: {co} – nie ma w {plik} ({czego})")

    for u, x in d.uslugi.items():
        for n in x["sprzet"]:
            if d.sprzet.get(n, {}).get("dla") != KUCHNIA:
                brak(n, f"uslugi.yaml: {u}", "sprzęt kuchni", "sprzet.yaml")
        for z in x["zasoby"]:
            if z not in d.zasoby:
                brak(z, f"uslugi.yaml: {u}", "zasób", "zasoby.yaml")
        if x["prowadzacy"] not in d.zawody_typu(KUCHNIA):
            brak(x["prowadzacy"], f"uslugi.yaml: {u}", "zawód kuchni", "katalog.yaml: stanowiska.typy")
    for m, ceny in d.dostawcy.items():
        if m not in MIESIACE:
            brak(m, "dostawcy.yaml: ceny", "miesiąc", "MIESIACE")
        for dost, zasoby in ceny.items():
            for z in zasoby:
                if z not in d.zasoby:
                    brak(z, f"dostawcy.yaml: {m}.{dost}", "zasób", "zasoby.yaml")
    wszyscy = {dost for ceny in d.dostawcy.values() for dost in ceny}
    for dost in d.dostawcy_pierwsi:
        if dost not in wszyscy:
            brak(dost, "dostawcy.yaml: pierwsi", "dostawca", "dostawcy.yaml: ceny")
    for k in d.kandydaci:
        if k["zawod"] not in d.zawody:
            brak(k["zawod"], f"kandydaci.yaml: {k['imie_nazwisko']}", "zawód", "katalog.yaml: stanowiska.typy")
    for i, st in enumerate(d.katalog_ofert["stanowiska"].get("startowe", [])):
        for n, q in st["sprzet"].items():
            if d.sprzet.get(n, {}).get("dla") != st["typ"]:
                brak(n, f"katalog.yaml: stanowiska.startowe[{i}]", f"sprzęt typu {st['typ']}", "sprzet.yaml")
            elif str(q) not in d.sprzet[n]["ceny"]:
                brak(str(q), f"katalog.yaml: stanowiska.startowe[{i}].{n}", "jakość", "sprzet.yaml")
    for u in d.katalog_ofert["rundy"]["uslugi_startowe"]:
        if u not in d.uslugi:
            brak(u, "katalog.yaml: rundy.uslugi_startowe", "usługa", "uslugi.yaml")
    media, narzedzia = d.pozycje("media_tradycyjne"), d.pozycje("narzedzia_internetowe")
    for s, st in d.boty["strategie"].items():
        for n in st["reklama"]:
            if n not in media:
                brak(n, f"boty.yaml: {s}.reklama", "medium", "katalog.yaml: media_tradycyjne")
        for n in st["internet"]:
            if n not in narzedzia:
                brak(n, f"boty.yaml: {s}.internet", "narzędzie", "katalog.yaml: narzedzia_internetowe")
    return bledy


@lru_cache(maxsize=1)
def dane_domyslne() -> Dane:
    return Dane()


def main(argv: list[str]) -> int:
    if argv[:1] != ["sprawdz"]:
        print("Użycie: python -m silnik.dane sprawdz [katalog]")
        return 2
    katalog = Path(argv[1]) if len(argv) > 1 else KATALOG_DANYCH
    bledy = sprawdz(katalog)
    for b in bledy:
        print("BŁĄD", b)
    if not bledy:
        print(f"Dane w porządku: {katalog} (wersja {Dane(katalog).wersja}).")
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
