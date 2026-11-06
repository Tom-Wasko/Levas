"""Porównania par gier (plan optymalizacji, B2): ta sama gra, ziarno i rywale, a badana firma (bot)
różni się tylko jedną decyzją albo parametrem strategii. Gra bazowa jest wspólna dla wszystkich
wariantów z tym samym kontekstem i ziarnem – liczona raz. Wyniki gier trafiają na bieżąco do
`gry.csv` (przerwany pomiar wznawia się od miejsca przerwania), a pary i tabela – do `pary.csv`
i `raport.md`.

    python -X utf8 -m balans.warianty szybki [-o katalog]        # ≤ 10 min, kontrola regresji
    python -X utf8 -m balans.warianty pelny -o katalog --minut 60 [--ziarna 30] [--strategie …]
        [--firm 4,6,8] [--rund 12,18,26] [--strefy …] [--warianty bank,jakosc:3] [--procesy 5]
        [--dane "mapa.popyt.model.zasieg=2|mapa.popyt.model.zasieg=4"]   # B6: liczby całej gry
    python -X utf8 -m balans.warianty raport katalog             # tabela z zapisanych gier
    python -X utf8 -m balans.warianty lista                      # dostępne warianty

Wariant to dane, nie kod: nadpisanie parametrów strategii albo poziomu bota (dane/boty.yaml),
decyzji, którą bot podejmuje (klucz z silnik/decyzje.py), albo pól każdego zatrudnienia.
Wyjątek – „zamknięcie firmy” od rundy N (U21): badana firma od tej rundy nie gra (decyzje
z `_zamknij`), a gra trwa. Najemca nie może wypowiedzieć najmu (`wypowiedz` w decyzjach to
wypowiedzenie przez nowego właściciela budynku), więc czynsz płaci do końca gry.
Kontekst: strategia badanej firmy, długość gry, liczba firm, poziom botów, strefa lokalu
(parametr strategii `strefy`), kapitał startowy i poziom rywali (bez niego – jak badanej; trudność
mierzy badana firma „jak człowiek” wśród rywali na poziomie średnim, Z5:
`--poziom czlowiek_dobry --rywale sredni`). Rywale – boty kolejnych strategii, przesunięte o ziarno.
Kontekst `dane` (B6) zmienia liczby dla wszystkich firm (`dane_ze_zmianami`) – do porównania tabel
kontekstów przy innych liczbach; `--warianty baza` – same gry bazowe.
"""
from __future__ import annotations

import argparse
import copy
import csv
import math
import os
import statistics
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from silnik.boty import decyzje_bota
from silnik.dane import KATALOG_GRY, Dane, dane_domyslne
from silnik.gra import Gra
from silnik.ksiegowosc import biuro as bo
from silnik.pieniadze import banki as bk
from silnik.wyniki.majatek import z_portfelem

BADANA = "Badana"
BAZA = "baza"
POLA_GRY = ["karta", "dochod", "gotowka", "majatek", "pierwszy_plus", "alarmy", "miejsce",
            "lokale", "czas_s"]
POLA_OPISU = ["strefy_lokali"]   # B6: strefy lokali badanej na koniec (strefa bywa zajęta)
ROZNICE = ("karta", "majatek", "dochod")   # różnice w parach
DOMINACJA = 0.7   # plan: opcja wygrywa ≥ 70% par przy istotnej różnicy
POMIARY = KATALOG_GRY.parent / "raporty" / "kalibracja" / "pomiary"


@dataclass(frozen=True)
class Kontekst:
    strategia: str = "zrownowazony"
    rund: int = 18
    firm: int = 6
    poziom: str = "sredni"
    strefa: str = ""
    kapital: int = 0          # 0 – kapitał domyślny gry
    rywale: str = ""          # poziom rywali; "" – jak badanej (poziom)
    dane: str = ""            # B6: zmiany danych gry „ścieżka=wartość;…” (dane_ze_zmianami)

    def klucz(self) -> str:
        k = f"{self.strategia}/{self.rund}r/{self.firm}f/{self.poziom}"
        k += f"/{self.strefa}" if self.strefa else ""
        k += f"/{self.kapital}zl" if self.kapital else ""
        k += f"/rywale_{self.rywale}" if self.rywale else ""
        return k + (f"/{self.dane}" if self.dane else "")


def dane_ze_zmianami(zmiany: str = "") -> Dane:
    """Dane domyślne ze zmianami `ścieżka=wartość` po „;”, np. `mapa.popyt.model.zasieg=2`
    (B6: liczby dla wszystkich firm w grze – porównanie kontekstów, nie par wariantów).
    Ścieżka: atrybut danych, potem klucze słowników, `*` – każdy klucz; wartość w składni YAML;
    `ścieżka*=x` mnoży liczbę, np. `lokale.*.cena*=1.5`."""
    d = dane_domyslne()
    return _ze_zmianami(d, zmiany) if zmiany else d


@lru_cache(maxsize=8)
def _ze_zmianami(dane: Dane, zmiany: str) -> Dane:   # klucz z danymi – testy zmieniają katalog
    d = copy.deepcopy(dane)
    for z in zmiany.split(";"):
        sciezka, _, wartosc = z.partition("=")
        razy = sciezka.endswith("*")
        atrybut, *klucze = sciezka.strip().rstrip("*").split(".")
        cele = [getattr(d, atrybut)]
        for k in klucze[:-1]:
            cele = [c[x] for c in cele for x in (c if k == "*" else [k])]
        for c in cele:
            if klucze[-1] not in c and not razy:
                raise KeyError(f"{sciezka}: nie ma klucza {klucze[-1]}")
            if razy:   # `ścieżka*=x` – mnożnik (puste wartości zostają)
                if c.get(klucze[-1]) is not None:
                    c[klucze[-1]] = round(c[klucze[-1]] * float(wartosc), 2)
            else:
                c[klucze[-1]] = yaml.safe_load(wartosc)
    return d


@dataclass(frozen=True)
class Wariant:
    nazwa: str
    opis: str = ""
    strategia: tuple = ()     # ((parametr, wartość), …) – nadpisanie strategii badanej firmy
    poziom: tuple = ()        # ((ustawienie, wartość), …) – nadpisanie poziomu bota badanej firmy
    decyzje: tuple = ()       # ((klucz, wartość), …) – zamiast decyzji bota, gdy ją podejmuje
    zatrudnienie: tuple = ()  # ((pole, wartość), …) – w każdym zatrudnieniu (np. umowa)
    zamknij_od: int = 0       # U21: od tej rundy firma się zamyka (0 – nie zamyka)
    zamknij_twardo: bool = False   # przy zamknięciu też sprzedaje sprzęt, zdejmuje menu i polisy


@dataclass
class Zadanie:
    kontekst: Kontekst
    ziarno: int
    wariant: Wariant = field(default_factory=lambda: Wariant(BAZA))

    def klucz(self) -> tuple[str, int, str]:
        return self.kontekst.klucz(), self.ziarno, self.wariant.nazwa


def katalog_wariantow(dane: Dane) -> dict[str, Wariant]:
    """Warianty, które dzisiejsze boty umieją rozegrać; nowe opcje botów (B3) dopisuje się tutaj."""
    zd = dane.zdarzenia or {}   # gra z lokalami: higiena i polisy
    w = [Wariant(f"bank:{b}", f"konto w {b}", decyzje=(("bank", b),)) for b in bk.banki(dane)]
    w += [Wariant(f"biuro:{b}", f"biuro rachunkowe {x['nazwa']}", decyzje=(("biuro", b),))
          for b, x in bo.biura(dane).items()]
    w += [Wariant(f"higiena:{h}", f"higiena: {x['nazwa']}", strategia=(("higiena", h),))
          for h, x in zd["urzad"]["higiena"]["poziomy"].items()]
    polisy = list(zd["losowe"]["ubezpieczyciel"]["polisy"])
    w += [Wariant("polisy:brak", "bez polis", strategia=(("polisy", []),)),
          Wariant("polisy:wszystkie", "wszystkie polisy", strategia=(("polisy", polisy),)),
          Wariant("umowa:zlecenie", "wszyscy na umowie zlecenie",
                  zatrudnienie=(("umowa", "zlecenie"),)),
          Wariant("kampanie:brak", "bez kampanii reklamowych", decyzje=(("kampanie", []),)),
          Wariant("promocje:brak", "bez promocji", decyzje=(("promocje", []),))]
    w += [Wariant(f"jakosc:{q}", f"jakość {q}★ (sprzęt, składniki, ludzie)",
                  strategia=(("jakosc", q),)) for q in (1, 2, 3)]
    w += [Wariant(f"cena:{c}", f"cena {c:.0%} ceny preferowanej", strategia=(("cena", c),))
          for c in (0.85, 1.0, 1.15, 1.3)]
    # B7: szerokość menu (liczba dań bota) i jedna promocja danego typu zamiast promocji strategii
    w += [Wariant(f"menu:{n}", f"menu {n} dań", strategia=(("uslugi", n),)) for n in (3, 5, 8)]
    w += [Wariant(f"promocja:{t}", f"tylko promocja {t}",
                  strategia=(("promocje", [{"typ": t, "nazwa": f"Promocja {t}"}]),))
          for t in dane.mapa["promocje"]["typy"]]
    # B8: zaopatrzenie – gwiazdki składników (sprzęt i ludzie wg strategii), zapas, dostawcy
    w += [Wariant(f"skladniki:{q}", f"składniki {q}★ (sprzęt i ludzie wg strategii)",
                  strategia=(("jakosc_zasobow", q),)) for q in (1, 2, 3)]
    w += [Wariant(f"zapas:{z}", f"zapas zamówień ×{z}", strategia=(("zapas_zasobow", z),))
          for z in (1.0, 1.15, 1.3)]
    rodzaj = {k: v.get("rodzaj") for k, v in dane.dostawcy_info.items()}
    hurt = [k for k, r in rodzaj.items() if r in ("hurtownia", "piekarnia")]
    w += [Wariant("dostawcy:bez_producenta", "hurtownie i piekarnia, bez producenta mięsa",
                  strategia=(("dostawcy", hurt),)),
          Wariant("dostawcy:bez_piekarni", "bez piekarni",
                  strategia=(("dostawcy", [k for k, r in rodzaj.items() if r != "piekarnia"]),))]
    w += [Wariant(f"dostawcy:tylko_{k}", f"wszystko z jednej hurtowni {k}",
                  strategia=(("dostawcy", [k]),))
          for k, r in rodzaj.items() if r == "hurtownia"]
    drugi = dane.boty["poziomy"]["trudny"]["kolejny_lokal"]
    w += [Wariant("lokale:drugi", "drugi lokal jak bot trudny",
                  poziom=(("kolejny_lokal", drugi),)),
          Wariant("lokale:jeden", "bez drugiego lokalu", poziom=(("kolejny_lokal", None),))]
    # B6: typ i forma lokalu (strategia `lokal`, silnik/boty.py: _wybierz_lokal); kupno – na kredyt
    # pod zastaw lokalu, gdy zostaje rezerwa gotówki (inaczej gotowy w najmie); drugi lokal – jak
    # u trudnego, ale innego typu
    # u lokalu bez zestawu – większa rezerwa na sprzęt kupowany po urządzeniu albo budowie;
    # brakującą kwotę bot dopłaca kredytem bez historii (silnik/boty.py: _kredyty_na_kupno)
    kupno = {"forma": "kupno", "rezerwa": 10000}
    bez_zestawu = {**kupno, "rezerwa": 30000}
    typy = {"kupno": {"typy": ["gotowy"], **kupno},
            "niewyposazony": {"typy": ["niewyposazony"]},
            "niewyposazony_kupno": {"typy": ["niewyposazony"], **bez_zestawu},
            "dzialka": {"typy": ["dzialka"], **bez_zestawu},
            "przebicie": {"przebicie": 1.2}}
    w += [Wariant(f"lokale:{n}", f"pierwszy i kolejny lokal: {x}", strategia=(("lokal", x),))
          for n, x in typy.items()]
    w += [Wariant("lokale:wykup", "wykup własnego lokalu, gdy zostaje 30 tys. zł",
                  strategia=(("wykup", {"rezerwa": 30000}),)),
          Wariant("lokale:przejecie", "kupno budynku rywala, gdy zostaje 30 tys. zł",
                  strategia=(("przejecie", {"rezerwa": 30000}),)),
          Wariant("lokale:przejecie_wypowiedz", "kupno budynku rywala i wypowiedzenie najmu",
                  strategia=(("przejecie", {"rezerwa": 30000, "wypowiedz": True}),))]
    leasing = {"gotowka": 30000, "rund": 26}   # leasing, gdy gotówki mniej niż bufor botów
    w += [Wariant("leasing:sprzet", f"sprzęt w leasingu: {leasing}",
                  strategia=(("leasing", leasing),)),
          Wariant("lokale:niewyposazony_leasing", "niewyposażony w najmie, sprzęt w leasingu",
                  strategia=(("lokal", typy["niewyposazony"]), ("leasing", leasing))),
          # kompromis z inwentarza: niewyposażony wygrywa, gdy gracz chce własny, lepszy sprzęt –
          # porównanie z `jakosc:3` (gotowy z zestawem wynajmującego, reszta 3★)
          Wariant("lokale:niewyposazony_q3", "niewyposażony w najmie, sprzęt i reszta 3★",
                  strategia=(("lokal", typy["niewyposazony"]), ("jakosc", 3)))]
    w += [Wariant(f"lokale:drugi_{n}", f"drugi lokal jak bot trudny, {x}",
                  poziom=(("kolejny_lokal", {**drugi, "lokal": x}),))
          for n, x in typy.items() if n in ("kupno", "niewyposazony", "dzialka")]
    # U21: „zarób i zamknij” – zwolnienia i koniec zamówień (jak w analizie A), wersja twarda:
    # do tego sprzedaż sprzętu, puste menu i bez polis; lokal zostaje (najemca nie wypowie najmu)
    w += [Wariant(f"zamkniecie:{r}{'_twarde' if t else ''}",
                  f"od rundy {r} zwalnia wszystkich i nie zamawia"
                  + (", sprzedaje sprzęt, bez menu i polis" if t else ""),
                  zamknij_od=r, zamknij_twardo=t) for r in (6, 11) for t in (False, True)]
    w.append(Wariant("zamkniecie:1", "od rundy 1 nic nie robi (bez lokalu) – punkt odniesienia",
                     zamknij_od=1))
    # B3: umiejętności poziomu trudnego pojedynczo wyłączone (na innych poziomach – bez zmian)
    w += [Wariant(f"poziom:bez_{u}", f"poziom bez ustawienia {u}", poziom=((u, None),))
          for u in ("korekta_prognozy", "mnozniki_ceny", "obsluga_kampanii")]
    # K: diagnoza poziomu „jak człowiek – dobry” – po jednej przewadze nad średnim zabranej
    # (`--poziom czlowiek_dobry --rywale sredni`); „jak_sredni” – wszystkie naraz, punkt kontrolny
    if sr := dane.boty["poziomy"].get("czlowiek_sredni"):
        jak_sr = (("prognoza_czlowieka", sr["prognoza_czlowieka"]),
                  ("blad_prognozy", sr.get("blad_prognozy")))
        w += [Wariant("czlowiek:prognoza_bez_pul", "prognoza z 2 rund, bez poprawki o pulę",
                      poziom=(("prognoza_czlowieka", {**sr["prognoza_czlowieka"], "rund": 2}),)),
              Wariant("czlowiek:prognoza_jak_sredni", "prognoza i jej błąd jak u średniego",
                      poziom=jak_sr),
              Wariant("czlowiek:jak_sredni", "prognoza, reklama i lokale jak u średniego",
                      poziom=jak_sr + (("kolejny_lokal", None), ("obsluga_kampanii", None)))]
    return {x.nazwa: x for x in w}


def wybierz_warianty(dane: Dane, wzorce: list[str] | None) -> list[Wariant]:
    """Warianty po nazwie albo przedrostku (`bank` = wszystkie banki); bez wzorców – wszystkie;
    `baza` – żadnych (same gry bazowe, np. pomiar trudności)."""
    kat = katalog_wariantow(dane)
    if not wzorce:
        return list(kat.values())
    if wzorce == [BAZA]:
        return []
    pasuje = lambda n, x: n == x or n.startswith(x + ":")   # noqa: E731
    nieznane = [x for x in wzorce if not any(pasuje(n, x) for n in kat)]
    if nieznane:
        raise ValueError(f"nieznane warianty: {', '.join(nieznane)} "
                         "(lista: python -m balans.warianty lista)")
    return [w for n, w in kat.items() if any(pasuje(n, x) for x in wzorce)]


# --- jedna gra -------------------------------------------------------------------------------
def _dane_badanej(dane: Dane, strategia: str, poziom: str, nad_strategii: dict,
                  nad_poziomu: dict) -> Dane:
    """Dane do decyzji badanej firmy z nadpisaną strategią i poziomem (gra liczy na swoich)."""
    if not nad_strategii and not nad_poziomu:
        return dane
    d = copy.copy(dane)
    st, pz = dane.boty["strategie"], dane.boty["poziomy"]
    d.boty = {**dane.boty, "strategie": {**st, strategia: {**st[strategia], **nad_strategii}},
              "poziomy": {**pz, poziom: {**pz.get(poziom, {}), **nad_poziomu}}}
    return d


def _wymus(w: Wariant, d: dict) -> dict:
    for k, v in w.decyzje:
        if k in d:
            d[k] = copy.deepcopy(v)
    for z in d.get("zatrudnij", []) if w.zatrudnienie else []:
        z.update(dict(w.zatrudnienie))
    return d


def _zamknij(w: Wariant, f, r: int) -> dict:
    """U21: decyzje zamkniętej firmy (brak klucza = bez zmian): nic nie kupuje, nie zatrudnia, nie
    reklamuje się; w rundzie zamknięcia zwalnia wszystkich (wersja twarda: sprzedaje sprzęt)."""
    d = {"zatrudnij": [], "zamowienia": [], "kampanie": [], "promocje": [], "sprzet_kup": [],
         "kredyty_wez": [], "leasing_wez": [], "lokaty_zaloz": [], "szkolenia": []}
    if r == w.zamknij_od:
        d["zwolnij"] = [pid for pid, p in f.pracownicy.items() if not p.odchodzi]
        if w.zamknij_twardo:
            d["sprzet_sprzedaj"] = [{"typ": s.typ, "nr": s.nr, "nazwa": n} for s in f.stanowiska
                                    for n in s.sprzet if n not in s.sprzet_wynajmujacego]
    if w.zamknij_twardo:
        d |= {"oferta": {}, "sprzedaz": {}, "polisy": []}
    return d


def firmy(k: Kontekst, ziarno: int, strategie: list[str]) -> list[tuple[str, str]]:
    """Badana firma i rywale: kolejne strategie od przesunięcia zależnego od ziarna."""
    rywale = [strategie[(ziarno + i) % len(strategie)] for i in range(1, k.firm)]
    return [(BADANA, k.strategia)] + [(f"R{i}_{s}", s) for i, s in enumerate(rywale, 1)]


def rozegraj(z: Zadanie) -> dict:
    """Gra jednego zadania; liczby badanej firmy (pola POLA_GRY)."""
    t = time.perf_counter()
    k, w = z.kontekst, z.wariant
    fs = firmy(k, z.ziarno, list(dane_domyslne().boty["strategie"]))
    opcje = {"kapital_startowy": k.kapital} if k.kapital else {}
    poziomy = {n: k.poziom if n == BADANA else k.rywale or k.poziom for n, _ in fs}
    g = Gra.nowa("warianty", fs, k.rund, z.ziarno, poziomy=poziomy, dane=dane_ze_zmianami(k.dane),
                 **opcje)
    nad = dict(w.strategia) | ({"strefy": [k.strefa]} if k.strefa else {})
    db = _dane_badanej(g.dane, k.strategia, k.poziom, nad, dict(w.poziom))
    for r in range(1, k.rund + 1):
        if w.zamknij_od and r >= w.zamknij_od:
            d = _zamknij(w, g.stan(r - 1).firmy[BADANA], r)
        else:
            d = _wymus(w, decyzje_bota(db, g.stan(r - 1), BADANA, k.strategia, r, g.konfiguracja))
        g.ustaw_decyzje(BADANA, d)
        s = g.przelicz(wymus=True)
    return {**miary(s, k.rund), "czas_s": round(time.perf_counter() - t, 2)}


def miary(s, rund: int) -> dict:
    # karta skumulowana (plan): średni wynik działalności z rund 2..N, jak ranking mistrza gry
    karty = {n: sum(s.wyniki[r][n]["karta"]["wynik_dzialalnosci"] for r in range(2, rund + 1))
             / max(1, rund - 1) for n in s.firmy}
    ws = [s.wyniki[r][BADANA] for r in range(1, rund + 1)]
    plus = next((r for r, w in enumerate(ws, 1) if w["kpir"]["dochod_netto"] > 0), rund + 1)
    # alarm = debet ponad limit konta (plan; po Z3 – pole alarm w wynikach)
    alarmy = sum(bool(w["alarm"]) if "alarm" in w else w["bank"]["debet_ponad_limit"] > 0
                 for w in ws)
    return {"karta": round(karty[BADANA], 4),
            "dochod": round(sum(w["kpir"]["dochod_netto"] for w in ws), 2),
            "gotowka": round(ws[-1]["gotowka"], 2), "majatek": z_portfelem(ws[-1]),
            "pierwszy_plus": plus, "alarmy": alarmy,
            "miejsce": 1 + sum(v > karty[BADANA] for v in karty.values()),
            "lokale": len(s.firmy[BADANA].lokale),
            "strefy_lokali": ";".join(dane_domyslne().lokale[x.id]["strefa"]
                                      for x in s.firmy[BADANA].lokale)}


# --- pomiar ----------------------------------------------------------------------------------
def zadania(konteksty: list[Kontekst], ziarna: list[int], warianty: list[Wariant]) -> list[Zadanie]:
    """Kolejność: ziarno po ziarnie, więc przerwany pomiar ma pełne pary pierwszych ziaren."""
    return [Zadanie(k, z, w) for z in ziarna for k in konteksty for w in [Wariant(BAZA), *warianty]]


def _wczytaj_gry(plik: Path) -> list[dict]:
    if not plik.exists():
        return []
    with open(plik, encoding="utf-8", newline="") as p:
        return list(csv.DictReader(p))


def mierz(katalog: Path, lista: list[Zadanie], procesy: int = 1, minut: float | None = None,
          wypisuj: bool = False) -> int:
    """Rozgrywa zadania, których nie ma w `gry.csv`, i dopisuje je na bieżąco; zwraca liczbę
    nowych gier. Po `minut` nie zaczyna nowych gier (rozpoczęte kończy)."""
    katalog.mkdir(parents=True, exist_ok=True)
    plik = katalog / "gry.csv"
    zrobione = {(g["kontekst"], int(g["ziarno"]), g["wariant"]) for g in _wczytaj_gry(plik)}
    do_zrobienia = [z for z in lista if z.klucz() not in zrobione]
    koniec = time.monotonic() + minut * 60 if minut else None
    czas_minal = lambda: koniec is not None and time.monotonic() > koniec   # noqa: E731
    nowy = not plik.exists()
    nowe = 0
    pola = ["kontekst", *asdict(Kontekst()), "ziarno", "wariant", *POLA_GRY, *POLA_OPISU]
    if not nowy:   # wznowienie pomiaru sprzed nowych kolumn – w starym układzie
        with open(plik, encoding="utf-8", newline="") as p:
            pola = next(csv.reader(p), pola)
    with open(plik, "a", encoding="utf-8", newline="") as p:
        pisz = csv.DictWriter(p, pola, extrasaction="ignore")
        if nowy:
            pisz.writeheader()

        def zapisz(z: Zadanie, wynik: dict) -> None:
            nonlocal nowe
            pisz.writerow({"kontekst": z.kontekst.klucz(), **asdict(z.kontekst),
                           "ziarno": z.ziarno, "wariant": z.wariant.nazwa, **wynik})
            p.flush()
            nowe += 1
            if wypisuj:
                print(f"  {nowe}/{len(do_zrobienia)} {z.kontekst.klucz()} z{z.ziarno} "
                      f"{z.wariant.nazwa}: karta {wynik['karta']:.2f} ({wynik['czas_s']:.1f} s)",
                      flush=True)

        if procesy <= 1:
            for z in do_zrobienia:
                if czas_minal():
                    break
                zapisz(z, rozegraj(z))
            return nowe
        kolejka = iter(do_zrobienia)
        with ProcessPoolExecutor(procesy) as pula:
            w_toku = {}
            while True:
                while len(w_toku) < 2 * procesy and not czas_minal() \
                        and (z := next(kolejka, None)):
                    w_toku[pula.submit(rozegraj, z)] = z
                if not w_toku:
                    break
                gotowe, _ = wait(w_toku, return_when=FIRST_COMPLETED)
                for f in gotowe:
                    zapisz(w_toku.pop(f), f.result())
    return nowe


# --- raport ----------------------------------------------------------------------------------
def _sr_przedzial(x: list[float]) -> tuple[float, float]:
    """Średnia i połowa 95% przedziału ufności (t-Studenta)."""
    if len(x) < 2:
        return (x[0] if x else 0.0), math.inf
    from scipy.stats import t
    return statistics.fmean(x), t.ppf(0.975, len(x) - 1) * statistics.stdev(x) / math.sqrt(len(x))


def pary(gry: list[dict]) -> list[dict]:
    """Para = wariant i gra bazowa z tym samym kontekstem i ziarnem; różnice wariant − baza."""
    baza = {(g["kontekst"], g["ziarno"]): g for g in gry if g["wariant"] == BAZA}
    pola = [p for p in POLA_GRY if p != "czas_s"]
    wynik = []
    for g in gry:
        b = baza.get((g["kontekst"], g["ziarno"]))
        if g["wariant"] == BAZA or b is None:
            continue
        wynik.append({"kontekst": g["kontekst"], "ziarno": int(g["ziarno"]),
                      "wariant": g["wariant"], **{f"{p}_baza": float(b[p]) for p in pola},
                      **{f"{p}_wariant": float(g[p]) for p in pola},
                      **{f"d_{p}": float(g[p]) - float(b[p]) for p in ROZNICE}})
    return wynik


def podsumuj(lista: list[dict]) -> dict:
    """Statystyki par: różnica karty i majątku z przedziałem, odsetek wygranych, pierwszy plus
    i alarmy (średnio w grze bazowej i w wariancie)."""
    dk = [p["d_karta"] for p in lista]
    karta, pk = _sr_przedzial(dk)
    majatek, pm = _sr_przedzial([p["d_majatek"] for p in lista])
    wygrane = (sum(d > 0 for d in dk) + 0.5 * sum(d == 0 for d in dk)) / len(dk)
    if all(d == 0 for d in dk):
        ocena = "= baza"
    elif wygrane >= DOMINACJA and karta - pk > 0:
        ocena = "lepszy"
    elif wygrane <= 1 - DOMINACJA and karta + pk < 0:
        ocena = "gorszy"
    else:
        ocena = "szum"
    sr = lambda p: statistics.fmean(x[p] for x in lista)   # noqa: E731
    return {"n": len(lista), "d_karta": karta, "p_karta": pk, "wygrane": wygrane,
            "d_majatek": majatek, "p_majatek": pm, "plus_baza": sr("pierwszy_plus_baza"),
            "plus_wariant": sr("pierwszy_plus_wariant"), "alarmy_baza": sr("alarmy_baza"),
            "alarmy_wariant": sr("alarmy_wariant"), "ocena": ocena}


NAGLOWEK = ("| wariant | pary | Δ karta (95%) | wygrane | Δ majątek zł (95%) "
            "| 1. plus: baza → wariant | alarmy | ocena |\n|---|---|---|---|---|---|---|---|")


def _wiersz(nazwa: str, s: dict) -> str:
    return (f"| {nazwa} | {s['n']} | {s['d_karta']:+.2f} ± {s['p_karta']:.2f} "
            f"| {s['wygrane']:.0%} | {s['d_majatek']:+,.0f} ± {s['p_majatek']:,.0f} "
            f"| {s['plus_baza']:.1f} → {s['plus_wariant']:.1f} "
            f"| {s['alarmy_baza']:.1f} → {s['alarmy_wariant']:.1f} | {s['ocena']} |"
            ).replace(",", " ")


def raport(katalog: Path) -> str:
    """Zapisuje `pary.csv` i `raport.md` z gier w `gry.csv`; zwraca tekst raportu."""
    gry = _wczytaj_gry(katalog / "gry.csv")
    lista = pary(gry)
    if lista:
        with open(katalog / "pary.csv", "w", encoding="utf-8", newline="") as p:
            pisz = csv.DictWriter(p, list(lista[0]))
            pisz.writeheader()
            pisz.writerows(lista)
    warianty = sorted({p["wariant"] for p in lista})
    konteksty = sorted({p["kontekst"] for p in lista})
    czas = sum(float(g["czas_s"]) for g in gry)
    tekst = [f"# Pomiar wariantów: {katalog.name}", "",
             f"{len(gry)} gier, {len(lista)} par, {len(konteksty)} kontekstów, czas gier "
             f"{czas / 60:.0f} min (suma procesów). Karta = średni wynik działalności z rund 2..N. "
             f"Ocena: „lepszy”/„gorszy” – ≥ {DOMINACJA:.0%} wygranych par i przedział bez zera; "
             "„szum” – reszta.", "", "## Wszystkie konteksty", "", NAGLOWEK]
    tekst += [_wiersz(w, podsumuj([p for p in lista if p["wariant"] == w])) for w in warianty]
    for k in konteksty:
        tekst += ["", f"## {k}", "", NAGLOWEK]
        tekst += [_wiersz(w, podsumuj(x)) for w in warianty
                  if (x := [p for p in lista if p["wariant"] == w and p["kontekst"] == k])]
    tekst = "\n".join(tekst) + "\n"
    (katalog / "raport.md").write_text(tekst, encoding="utf-8")
    return tekst


# --- polecenia -------------------------------------------------------------------------------
# szybki: 3 strategie × 6 ziaren × (baza + warianty), 6 firm, 18 rund – ok. 9 min na 5 procesach
SZYBKI = {"strategie": ["zrownowazony", "tani", "premium"], "ziarna": 6, "minut": 10}


def main(argv: list[str]) -> int:
    pa = argparse.ArgumentParser(prog="python -m balans.warianty",
                                 description=__doc__.split("\n\n")[0])
    pa.add_argument("polecenie", choices=["szybki", "pelny", "raport", "lista"])
    pa.add_argument("katalog_raportu", nargs="?", type=Path)
    pa.add_argument("-o", "--wyjscie", type=Path)
    pa.add_argument("--ziarna", type=int)
    pa.add_argument("--od-ziarna", type=int, default=1000)
    pa.add_argument("--strategie")
    pa.add_argument("--firm", default="6")
    pa.add_argument("--rund", default="18")
    pa.add_argument("--poziom", default="sredni", help="poziomy badanej firmy, po przecinku")
    pa.add_argument("--rywale", default="", help="poziom rywali (bez – jak --poziom)")
    pa.add_argument("--strefy", help="strefy lokalu badanej firmy, po przecinku (bez – strategia)")
    pa.add_argument("--kapital", type=int, default=0)
    pa.add_argument("--dane", default="",
                    help="zmiany danych gry „ścieżka=wartość;…”, kolejne konteksty po „|” (B6)")
    pa.add_argument("--warianty", help="nazwy albo przedrostki po przecinku (bez – wszystkie)")
    pa.add_argument("--minut", type=float)
    pa.add_argument("--procesy", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = pa.parse_args(argv)
    dane = dane_domyslne()
    if a.polecenie == "lista":
        for w in katalog_wariantow(dane).values():
            print(f"{w.nazwa:24s} {w.opis}")
        return 0
    if a.polecenie == "raport":
        print(raport(a.katalog_raportu or a.wyjscie))
        return 0
    lista = lambda x, typ=str: [typ(v) for v in x.split(",")] if x else []   # noqa: E731
    szybki = a.polecenie == "szybki"
    strategie = lista(a.strategie) or (SZYBKI["strategie"] if szybki
                                        else list(dane.boty["strategie"]))
    konteksty = [Kontekst(s, r, f, p, st, a.kapital, a.rywale, zm) for s in strategie
                 for p in lista(a.poziom) for r in lista(a.rund, int) for f in lista(a.firm, int)
                 for st in lista(a.strefy) or [""] for zm in a.dane.split("|")]
    for zm in {k.dane for k in konteksty}:
        dane_ze_zmianami(zm)   # błąd w ścieżce – od razu, nie w procesie pomiaru
    ile = a.ziarna or (SZYBKI["ziarna"] if szybki else 30)
    ziarna = list(range(a.od_ziarna, a.od_ziarna + ile))
    warianty = wybierz_warianty(dane, lista(a.warianty))
    minut = a.minut or (SZYBKI["minut"] if szybki else None)
    katalog = a.wyjscie or POMIARY / time.strftime(f"{a.polecenie}_%Y%m%d_%H%M")
    lz = zadania(konteksty, ziarna, warianty)
    print(f"{len(lz)} gier ({len(konteksty)} kontekstów × {len(ziarna)} ziaren × "
          f"{len(warianty) + 1}), {a.procesy} procesów, limit {minut or '–'} min → {katalog}",
          flush=True)
    t = time.time()
    nowe = mierz(katalog, lz, a.procesy, minut, wypisuj=True)
    print(f"{nowe} nowych gier w {(time.time() - t) / 60:.1f} min")
    print(raport(katalog))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
