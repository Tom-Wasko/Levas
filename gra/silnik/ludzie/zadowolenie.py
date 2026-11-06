"""Zadowolenie każdej osoby i odejścia z niezadowolenia (U20, decyzja autora 4.11.2026).

Zadowolenie osoby liczy ten sam wzór co wskaźnik karty (karta_wynikow.zadowolenie_pracownikow), tylko dla jednej osoby:
jej pensja z premią ÷ preferowana, sprzęt jej stanowiska, udogodnienia jej lokalu, szkolenia firmy, umowa zlecenie
i przepracowanie (próg z kebabu karty). Ukryta cecha osoby (dane/kandydaci.yaml: cechy) mnoży składniki albo przesuwa
wynik; gracz zgaduje ją z żartobliwego opisu. Wskaźnik karty liczy się jak dotąd (kalibracja karty bez zmian).

Poniżej progu (zalozenia.yaml: pracownicy.odejscia) pierwszy tydzień to tylko ostrzeżenie na liście błędów; od kolejnego
tygodnia z rzędu osoba może złożyć wypowiedzenie – szansa rośnie z niezadowoleniem. Wypowiedzenie działa jak
zwolnienie bez odprawy: umowa o pracę – okres wypowiedzenia, zlecenie – od razu; osoba wraca do puli kandydatów.
"""
from __future__ import annotations

import numpy as np

from ..dane import Dane
from ..losowosc import strumien
from ..model import Firma, Odejscie, Pracownik, do_slownika
from ..nieruchomosci import per_lokal as pl
from . import formy as fz
from .kandydaci import cechy
from .rynek_pracy import okres_wypowiedzenia

NIEZADOWOLENIE = "niezadowolenie"
NEUTRALNA = {"placa": 1.0, "warunki": 1.0, "przeciazenie": 1.0, "odejscie": 1.0, "zadowolenie": 0.0}
UKRYTE = frozenset({"cecha", "wydajnosc"})   # pola osoby, których panel gracza nie dostaje


def ustawienia(dane: Dane) -> dict | None:
    """Parametry odejść; None – dane bez U20 (np. zamrożona kopia testów): osoby nie odchodzą same."""
    return (dane.z.get("pracownicy") or {}).get("odejscia")


def wplyw(dane: Dane, p: Pracownik) -> dict:
    c = cechy(dane).get(p.cecha) or {}
    return {k: c.get(k, v) for k, v in NEUTRALNA.items()}


def placa_wzgledna(dane: Dane, p: Pracownik) -> float:
    """B9: (pensja + premia) ÷ pensja preferowana; pensja jest miesięczna, a premia – za rundę, więc w grze
    tygodniowej liczy się jak miesięczna podwyżka o premia × rund_w_roku / 12 (na ten tydzień).
    UF21: zamiast preferowanej – pensja oczekiwana w tej formie (pół etatu, B2B, student); staż – płaca neutralna."""
    premia = p.premia * dane.rund_w_roku / 12
    oczekiwana = fz.oczekiwana(dane, p)
    if oczekiwana is None:
        return 1 + premia / p.pensja_preferowana
    return (p.pensja + premia) / oczekiwana


def skladniki(dane: Dane, f: Firma, p: Pracownik, wykorzystanie: float, szkolenia_procent: float) -> dict[str, float]:
    w = dane.z["karta_wynikow"]["zadowolenie_pracownikow"]
    kb = dane.z["karta_wynikow"]["kebab"]["zadowolenie_pracownikow"]
    c = wplyw(dane, p)
    st = f.stanowisko(dane.typ_zawodu(p.zawod), p.stanowisko)
    jakosci = list(st.sprzet.values()) if st else []
    sprzet = float(np.mean(jakosci)) if jakosci else ustawienia(dane)["sprzet_bez_sprzetu"]
    lok = pl.lokal(f, st.lokal) if st else None
    poz = dane.pozycje("udogodnienia")
    udog = sum(poz[n]["procent"] / 100 for n in pl.lista(f, lok, "udogodnienia")) if lok else 0.0
    return {
        "placa": w["placa_wzgledem_preferowanej"] * (placa_wzgledna(dane, p) - 1) * c["placa"],
        "sprzet": w["sprzet_na_gwiazdke"] * (sprzet - 3) * c["warunki"],
        "udogodnienia": w["udogodnienia_na_procent"] * udog * c["warunki"],
        "szkolenia": (w["szkolenia_w_miesiacu_na_procent"] * szkolenia_procent
                      + w.get("szkolenie_w_miesiacu", 0.0) * (szkolenia_procent > 0)),
        "umowa": w["udzial_umow_zlecenie"] * bool(fz.forma(dane, p.umowa)["kara_zlecenia"]),
        "przeciazenie": kb["przepracowanie"] * max(0.0, wykorzystanie - kb["prog_przepracowania"]) * c["przeciazenie"],
        "charakter": c["zadowolenie"],
    }


def zadowolenie(dane: Dane, skl: dict[str, float]) -> float:
    return round(dane.z["karta_wynikow"]["zadowolenie_pracownikow"]["stala"] + sum(skl.values()), 3)


def szansa(dane: Dane, p: Pracownik, z: float) -> float:
    """Szansa wypowiedzenia w tygodniu: za każde 0,01 poniżej progu szansa_na_setna (najwyżej szansa_maks) × cecha."""
    u = ustawienia(dane)
    brak = max(0.0, u["prog_zadowolenia"] - z) * 100
    return round(min(1.0, min(u["szansa_maks"], u["szansa_na_setna"] * brak) * wplyw(dane, p)["odejscie"]
                     * fz.mnoznik_odejsc(dane, p)), 3)


def _procent(x: float) -> str:
    return f"{round(x * 100)}%"


def _liczba(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def powody(dane: Dane, p: Pracownik, skl: dict[str, float], wykorzystanie: float) -> list[str]:
    """Widoczne powody niezadowolenia (bez cechy – tę gracz zgaduje z opisu)."""
    wynik = []
    if skl["placa"] < 0:
        wynik.append(f"pensja {_procent(1 - placa_wzgledna(dane, p))} poniżej oczekiwanej")
    if skl["przeciazenie"] < 0:
        wynik.append(f"przepracowanie (wykorzystanie {_procent(wykorzystanie)})")
    if skl["sprzet"] < 0:
        wynik.append("słaby sprzęt na stanowisku")
    if skl["umowa"] < 0:
        wynik.append("umowa zlecenie")
    return wynik or ["bez wyraźnego powodu – może to kwestia charakteru"]


def po_rundzie(dane: Dane, f: Firma, w: dict, r: int, ziarno, szkolenia_procent: float) -> list[dict] | None:
    """Zadowolenie osób po tygodniu (dopisuje je do w["pracownicy"]) i wypowiedzenia z niezadowolenia.
    None – gra bez U20 albo bez lokali."""
    u = ustawienia(dane)
    if not u or not f.lokale:
        return None
    odejscia = []
    for x in w["pracownicy"]:
        p = f.pracownicy[x["id"]]
        skl = skladniki(dane, f, p, x["wykorzystanie"], szkolenia_procent)
        z = zadowolenie(dane, skl)
        p.zadowolenie, p.wykorzystanie = z, x["wykorzystanie"]
        p.niezadowolony = p.niezadowolony + 1 if z < u["prog_zadowolenia"] else 0
        x.update(zadowolenie=z, niezadowolony=p.niezadowolony,
                 powody=powody(dane, p, skl, x["wykorzystanie"]) if p.niezadowolony else [])
        if p.odchodzi or p.niezadowolony <= u["tygodnie_ostrzezenia"]:
            continue
        if strumien(ziarno, r, "odejscia", f.nazwa, p.id).random() >= szansa(dane, p, z):
            continue
        do_rundy = r + 1 + okres_wypowiedzenia(dane, p, r + 1)
        p.odchodzi = Odejscie(do="", runda=do_rundy, pensja=p.pensja, umowa=p.umowa, od_rundy=r + 1,
                              powod=NIEZADOWOLENIE)
        x["odchodzi"] = do_slownika(p.odchodzi)
        odejscia.append({"pracownik": p.id, "imie_nazwisko": p.imie_nazwisko, "zadowolenie": z,
                         "runda_odejscia": do_rundy, "powody": x["powody"]})
    return odejscia


def _z_projektem(dane: Dane, p: Pracownik, zm: dict | None) -> Pracownik:
    """Osoba z pensją, umową i premią z projektu decyzji (jak w decyzje.zastosuj)."""
    if not zm:
        return p
    q = p.model_copy()
    if zm.get("pensja"):
        q.pensja = float(zm["pensja"])
    if zm.get("umowa") in fz.formy(dane):
        q.umowa = zm["umowa"]
    q.premia = float(zm.get("premia", 0) or 0)
    return q


def ostrzezenia(dane: Dane, f: Firma, zmiany: dict, runda: int) -> list[tuple[str, str]]:
    """Lista błędów (zakładka zatrudnienie): wypowiedzenia z niezadowolenia i niezadowoleni po projekcie pensji."""
    u = ustawienia(dane)
    if not u or not f.lokale:
        return []
    wynik = []
    for p in sorted(f.pracownicy.values(), key=lambda p: p.id):
        o = p.odchodzi
        if o and o.powod == NIEZADOWOLENIE:
            kiedy = (f"pracuje do tygodnia {o.runda - 1}, potem odchodzi" if o.runda > runda
                     else "umowa zlecenie – odchodzi od razu, stanowisko zostaje puste")
            if o.od_rundy == runda:
                wynik.append(("pomaranczowy", f"{p.imie_nazwisko} składa wypowiedzenie z niezadowolenia – {kiedy}. "
                                              "Poszukaj zastępstwa w Rynku pracy."))
            continue
        if o or not p.niezadowolony or p.zadowolenie is None:
            continue
        q = _z_projektem(dane, p, zmiany.get(p.id))
        przed = skladniki(dane, f, p, p.wykorzystanie, 0.0)
        po = skladniki(dane, f, q, p.wykorzystanie, 0.0)
        z = round(p.zadowolenie + sum(po.values()) - sum(przed.values()), 3)
        if z >= u["prog_zadowolenia"]:
            continue
        s = szansa(dane, q, z)
        ile = "ok. " + _procent(s) if p.niezadowolony >= u["tygodnie_ostrzezenia"] else "na razie zero"
        wynik.append(("pomaranczowy", f"{p.imie_nazwisko}: zadowolenie {_liczba(z)} (próg {_liczba(u['prog_zadowolenia'])}) – "
                                      f"{', '.join(powody(dane, q, po, p.wykorzystanie))}. Jeśli tak zostanie, po tym tygodniu "
                                      f"może złożyć wypowiedzenie (szansa {ile}). Pomaga podwyżka, lepszy sprzęt "
                                      "albo odciążenie."))
    return wynik


def ukryj(v):
    """Widok dla panelu gracza bez ukrytych pól osób (cecha, wydajność)."""
    if isinstance(v, dict):
        return {k: ukryj(x) for k, x in v.items() if k not in UKRYTE}
    if isinstance(v, list):
        return [ukryj(x) for x in v]
    return v
