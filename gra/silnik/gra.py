"""Gra: konfiguracja + decyzje wszystkich firm we wszystkich rundach. Stan liczony jest od nowa z decyzji
(event sourcing), więc zapis gry to mały plik JSON, a powrót do dowolnej rundy jest prosty.

Użycie:
    g = Gra.nowa("Trening", [("Moja firma", None), ("Bot 1", "zrownowazony")], liczba_rund=12)
    g.ustaw_decyzje("Moja firma", {...})      # decyzje bieżącej rundy
    g.przelicz()                               # boty decydują same, runda się przelicza
    g.stan().wyniki[2]["Moja firma"]
"""
from __future__ import annotations

import json
import secrets
from copy import deepcopy
from pathlib import Path

from .dane import Dane, dane_domyslne
from .kandydaci import pula_startowa
from .model import Firma, StanGry, firma_z_slownika

WERSJA_SILNIKA = "1.0"


class Gra:
    def __init__(self, konfiguracja: dict, decyzje: dict | None = None, dane: Dane | None = None):
        self.konfiguracja = konfiguracja
        self.decyzje: dict[int, dict[str, dict]] = {int(k): v for k, v in (decyzje or {}).items()}
        self.dane = dane or dane_domyslne()
        self._stany: dict[int, StanGry] = {}

    # --- tworzenie i zapis -----------------------------------------------------------------------
    @classmethod
    def nowa(cls, nazwa: str, firmy: list[tuple[str, str | None]], liczba_rund: int | None = None,
             ziarno: int | str | None = None, dane: Dane | None = None, **opcje) -> Gra:
        dane = dane or dane_domyslne()
        konf = {"nazwa": nazwa, "ziarno": ziarno if ziarno is not None else secrets.randbelow(10**9),
                "liczba_rund": liczba_rund or dane.katalog_ofert["rundy"]["domyslna_liczba"],
                "firmy": [{"nazwa": n, "bot": b} for n, b in firmy],
                "ceny_dostawcow": opcje.get("ceny_dostawcow", "dane"),
                "kredyt_odnawialny": opcje.get("kredyt_odnawialny", "jednoczesnie"),
                "wersja_silnika": WERSJA_SILNIKA, "wersja_danych": dane.wersja}
        return cls(konf, {}, dane)

    def do_slownika(self) -> dict:
        return {"konfiguracja": self.konfiguracja, "decyzje": {str(k): v for k, v in self.decyzje.items()}}

    def zapisz(self, plik: str | Path) -> None:
        Path(plik).write_text(json.dumps(self.do_slownika(), ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def wczytaj(cls, plik: str | Path, dane: Dane | None = None) -> Gra:
        d = json.loads(Path(plik).read_text(encoding="utf-8"))
        return cls(d["konfiguracja"], d.get("decyzje"), dane)

    # --- stan ------------------------------------------------------------------------------------
    @property
    def runda_startowa(self) -> int:
        """Pierwsza runda gry: 1 albo runda, od której gra startuje z zaimportowanego stanu prawdziwej gry."""
        return int(self.konfiguracja.get("import", {}).get("runda", 1))

    def stan_poczatkowy(self) -> StanGry:
        kapital = self.dane.z["finanse"]["kapital_startowy"]
        firmy = {f["nazwa"]: Firma(nazwa=f["nazwa"], bot=f["bot"], nazwa_wyswietlana=f["nazwa"], gotowka=kapital)
                 for f in self.konfiguracja["firmy"]}
        imp = self.konfiguracja.get("import")
        if imp:
            for nazwa, d in imp.get("firmy", {}).items():
                f = firma_z_slownika(d)
                f.bot = firmy[nazwa].bot
                firmy[nazwa] = f
        return StanGry(self.runda_startowa - 1, firmy, pula_startowa(self.dane, self.konfiguracja["ziarno"]))

    @property
    def runda(self) -> int:
        """Bieżąca runda (do której zbierane są decyzje)."""
        return max(self.decyzje_kompletne(), default=self.runda_startowa - 1) + 1

    def decyzje_kompletne(self) -> list[int]:
        """Rundy już przeliczone."""
        return sorted(r for r, d in self.decyzje.items() if d.get("_przeliczona"))

    def stan(self, runda: int | None = None) -> StanGry:
        """Stan po rundzie `runda` (domyślnie po ostatniej przeliczonej)."""
        start = self.runda_startowa - 1
        cel = max(start, self.runda - 1 if runda is None else runda)
        if cel in self._stany:
            return self._stany[cel]
        from .runda import przelicz_runde
        poprz = max((r for r in self._stany if r < cel), default=None)
        s = self._stany[poprz] if poprz is not None else self.stan_poczatkowy()
        for r in range((poprz if poprz is not None else start) + 1, cel + 1):
            s = przelicz_runde(self.dane, s, self._decyzje_do_przeliczenia(r), self.konfiguracja)
            self._stany[r] = s
        self._stany.setdefault(start, s if cel == start else self.stan_poczatkowy())
        return s

    def _decyzje_do_przeliczenia(self, runda: int) -> dict[str, dict]:
        return {n: d for n, d in self.decyzje.get(runda, {}).items() if not n.startswith("_")}

    # --- decyzje ---------------------------------------------------------------------------------
    def ustaw_decyzje(self, firma: str, decyzje: dict, runda: int | None = None) -> None:
        runda = runda or self.runda
        if runda != self.runda:
            raise ValueError(f"Decyzje można zmieniać tylko w bieżącej rundzie ({self.runda}).")
        self.decyzje.setdefault(runda, {})[firma] = decyzje

    def szkic(self, firma: str) -> dict:
        """Decyzje firmy w bieżącej rundzie (wysłane albo robocze)."""
        return self.decyzje.get(self.runda, {}).get(firma, {})

    def wyslij(self, firma: str, wyslane: bool = True) -> None:
        """„Wyślij decyzje” (albo „Wróć do podejmowania decyzji”, gdy wyslane=False)."""
        d = self.decyzje.setdefault(self.runda, {})
        d.setdefault(firma, {})
        lista = d.setdefault("_wyslane", [])
        if wyslane and firma not in lista:
            lista.append(firma)
        elif not wyslane and firma in lista:
            lista.remove(firma)

    def wyslane(self) -> list[str]:
        return list(self.decyzje.get(self.runda, {}).get("_wyslane", []))

    def brakujace(self) -> list[str]:
        """Firmy prowadzone przez ludzi, które nie wysłały decyzji w bieżącej rundzie."""
        wyslane = self.wyslane()
        return [f["nazwa"] for f in self.konfiguracja["firmy"] if not f["bot"] and f["nazwa"] not in wyslane]

    @property
    def zakonczona(self) -> bool:
        return self.runda > self.konfiguracja["liczba_rund"]

    def przelicz(self, wymus: bool = False) -> StanGry:
        """Przelicza bieżącą rundę (boty decydują same). Bez `wymus` wymaga decyzji wszystkich ludzi."""
        r = self.runda
        if r > self.konfiguracja["liczba_rund"]:
            raise ValueError("Gra jest zakończona.")
        if self.brakujace() and not wymus:
            raise ValueError("Brak decyzji: " + ", ".join(self.brakujace()))
        stan = self.stan(r - 1)
        from .boty import decyzje_bota
        d = self.decyzje.setdefault(r, {})
        for f in self.konfiguracja["firmy"]:
            if f["bot"] and f["nazwa"] not in d:
                d[f["nazwa"]] = decyzje_bota(self.dane, stan, f["nazwa"], f["bot"], r, self.konfiguracja)
            d.setdefault(f["nazwa"], {})
        d["_przeliczona"] = True
        self._stany = {k: v for k, v in self._stany.items() if k < r}
        return self.stan(r)

    def cofnij(self) -> None:
        """Cofa ostatnią przeliczoną rundę (decyzje ludzi zostają do poprawienia, botów są usuwane)."""
        r = self.runda - 1
        if r < self.runda_startowa:
            return
        d = self.decyzje.get(r, {})
        d.pop("_przeliczona", None)
        d.pop("_wyslane", None)
        for f in self.konfiguracja["firmy"]:
            if f["bot"]:
                d.pop(f["nazwa"], None)
        self._stany = {k: v for k, v in self._stany.items() if k < r}

    def kopia(self) -> Gra:
        return Gra(deepcopy(self.konfiguracja), deepcopy(self.decyzje), self.dane)
