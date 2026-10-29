"""Promocje w grze z lokalami (F3b.3; notatka „Prawidła świata”): rodzaje z listy (`dane/mapa/promocje.yaml`) z ozdobną
nazwą drużyny, która nie wpływa na wynik.

- Decyzja `promocje: [{"typ", "nazwa", "danie"}]` – pełna lista włączonych promocji (brak klucza – bez zmian).
  Nowa promocja kosztuje `koszt_startu` (plakaty, karty; VAT 23%), trwająca (ten sam rodzaj i danie) zachowuje rundę
  startu – zmiana nazwy nic nie kosztuje. Najwyżej `limit_aktywnych` naraz, każdy rodzaj raz, od rundy `od_rundy`.
- Popyt (`efekty_ofert` → oferta dania `promocje`, popyt.podzial): objęci promocją klienci (dni tygodnia i strefy
  klientów z danych) widzą lokal jako atrakcyjniejszy o `przyciaganie` (z każdą rundą trwania zmienia się o
  `przyrost`). Podział zwraca objętych klientów (`objeci`) – z nich `porcje` (2 za 1: dwie porcje na klienta,
  podwójne składniki i czas kuchni) i `rozlicz`: przychód z rabatem, dopłaty (zestaw) i koszt dodatków.
"""
from __future__ import annotations

import numpy as np

from ..dane import Dane
from ..ksiegowosc.finanse import Ksiega, Rachunek, ksieguj
from ..losowosc import strumien
from ..model import Firma, Promocja

OPIS_STARTU = "Materiały promocyjne"
OPIS_DODATKOW = "Napoje do zestawów"
OPIS_DOPLAT = "Sprzedaż: napoje w zestawach promocyjnych"
ZAKLADKA = "promocje"


def zasady(dane: Dane) -> dict | None:
    """mapa/promocje.yaml (od_rundy, limit_aktywnych, typy); None – dane bez promocji."""
    return (dane.mapa or {}).get("promocje")


def przyciaganie(typ: dict, od_rundy: int, runda: int) -> float:
    """Przyciąganie w rundzie: z każdą rundą trwania o `przyrost` (znużenie albo przywiązanie klientów)."""
    p = typ["przyciaganie"] + typ["przyrost"] * (runda - od_rundy)
    return round(min(typ["przyciaganie_max"], max(typ["przyciaganie_min"], p)), 4)


def _nazwa(R: dict, typ: dict, x: dict) -> str:
    return " ".join(str(x.get("nazwa") or "").split())[:R["nazwa_max"]] or typ["nazwa"]


def ustaw(dane: Dane, f: Firma, d: dict, runda: int, ks: Ksiega, rach: Rachunek) -> dict:
    """Promocje z decyzji (po cenach – danie musi być w sprzedaży). Zwraca {"aktywne", "nowe", "wylaczone", "uwagi"}."""
    R = zasady(dane)
    info = {"aktywne": [], "nowe": [], "wylaczone": [], "uwagi": []}
    if not R:
        return info
    if "promocje" in d:
        stare = {(p.typ, p.danie): p for p in f.promocje}
        nowe, typy = [], set()
        for x in d.get("promocje") or []:
            t = x.get("typ")
            typ = R["typy"].get(t)
            if typ is None:
                info["uwagi"].append(f"Nieznana promocja: {t}.")
                continue
            danie = x.get("danie") if typ["zakres"] == "danie" else None
            if not f.lokale:
                info["uwagi"].append(f"{typ['nazwa']}: promocje są dla firm z lokalem.")
            elif runda < R["od_rundy"]:
                info["uwagi"].append(f"{typ['nazwa']}: promocje od rundy {R['od_rundy']}.")
            elif typ["zakres"] == "danie" and not danie:
                info["uwagi"].append(f"{typ['nazwa']}: wybierz danie.")
            elif typ["zakres"] == "danie" and danie not in f.ceny:
                info["uwagi"].append(f"{typ['nazwa']}: danie {dane.uslugi.get(danie, {}).get('nazwa', danie)} "
                                     "nie jest w sprzedaży.")
            elif t in typy:
                info["uwagi"].append(f"{typ['nazwa']}: ten rodzaj promocji już jest włączony.")
            elif len(nowe) >= R["limit_aktywnych"]:
                info["uwagi"].append(f"{typ['nazwa']} „{_nazwa(R, typ, x)}”: najwyżej {R['limit_aktywnych']} promocje naraz.")
            else:
                typy.add(t)
                p = stare.get((t, danie))
                nowe.append(Promocja(typ=t, nazwa=_nazwa(R, typ, x), danie=danie, od_rundy=p.od_rundy if p else runda))
        f.promocje = nowe
        trwa = {(p.typ, p.danie) for p in nowe}
        info["wylaczone"] = [p.model_dump() for k, p in stare.items() if k not in trwa]
        for p in nowe:
            if p.od_rundy == runda and (p.typ, p.danie) not in stare:
                typ = R["typy"][p.typ]
                opis = f"{OPIS_STARTU}: {typ['nazwa']} „{p.nazwa}”"
                stawka = ks.stawka_vat(opis) if ks.vat is not None else 0.0
                brutto = round(typ["koszt_startu"] * (1 + stawka), 2)
                if brutto:
                    ksieguj(f, ks, rach, opis, brutto, "pozostale")
                info["nowe"].append({**p.model_dump(), "brutto": brutto})
    for p in [p for p in f.promocje if p.danie is not None and p.danie not in f.ceny]:
        f.promocje.remove(p)
        info["wylaczone"].append(p.model_dump())
        info["uwagi"].append(f"{R['typy'][p.typ]['nazwa']} „{p.nazwa}”: danie zdjęte ze sprzedaży – promocja wyłączona.")
    info["aktywne"] = [p.model_dump() for p in f.promocje]
    return info


def efekty_ofert(dane: Dane, f: Firma, oferty_firmy: dict[str, dict[str, dict]], runda: int, dni: list) -> None:
    """Dopisuje do ofert dań firmy ({lokal: {danie: oferta}}) trwające promocje: oferta["promocje"] – lista efektów
    z maską dni rundy (`dni` – daty rundy, z popyt.dni_rundy)."""
    R = zasady(dane)
    if not R or not f.promocje:
        return
    for p in f.promocje:
        typ = R["typy"].get(p.typ)
        if typ is None:
            continue
        maska = np.array([1.0 if typ["dni"] is None or d.weekday() in typ["dni"] else 0.0 for d in dni])
        e = {"typ": p.typ, "nazwa": p.nazwa, "rabat": typ["rabat"], "porcje": typ["porcje"], "doplata": typ["doplata"],
             "koszt_dodatku": typ["koszt_dodatku"], "strefy": typ["strefy_klientow"], "maska": maska,
             "przyciaganie": przyciaganie(typ, p.od_rundy, runda)}
        for dania in oferty_firmy.values():
            for u, o in dania.items():
                if p.danie is None or p.danie == u:
                    o.setdefault("promocje", []).append(e)


def porcje(klienci: float, objeci: dict[str, float], efekty: list[dict]) -> float:
    """Porcje do przygotowania: objęci promocją z `porcje` > 1 biorą więcej."""
    return klienci + sum(objeci.get(e["typ"], 0.0) * (e["porcje"] - 1) for e in efekty)


def rozlicz(sprzedane: int, cena: float, klienci: float, objeci: dict[str, float], efekty: list[dict]) -> dict:
    """Sprzedane porcje (lokal, dzień, danie) → {"przychod" (brutto, bez dopłat), "doplaty", "koszt_dodatkow" (netto),
    "typy": {typ: {"objeci", "rabat", "gratis", "doplaty"}}}. Udział objętych – jak w popycie dnia."""
    c = {e["typ"]: (objeci.get(e["typ"], 0.0) / klienci if klienci else 0.0) for e in efekty}
    q = 1 + sum(c[e["typ"]] * (e["porcje"] - 1) for e in efekty)
    mnoznik = 1.0
    for e in efekty:
        mnoznik *= 1 - c[e["typ"]] + c[e["typ"]] * e["porcje"] * (1 - e["rabat"])
    obsluzeni = sprzedane / q
    typy = {}
    for e in efekty:
        n = obsluzeni * c[e["typ"]]
        typy[e["typ"]] = {"objeci": n, "rabat": n * cena * (1 - e["porcje"] * (1 - e["rabat"])),
                          "gratis": n * (e["porcje"] - 1), "doplaty": n * e["doplata"], "koszt_dodatkow": n * e["koszt_dodatku"]}
    return {"przychod": obsluzeni * cena * mnoznik, "doplaty": sum(t["doplaty"] for t in typy.values()),
            "koszt_dodatkow": sum(t["koszt_dodatkow"] for t in typy.values()), "typy": typy}


def ksieguj_sprzedaz(dane: Dane, f: Firma, ks: Ksiega, rach: Rachunek, wynik: dict, stawka_dodatkow: float | None) -> None:
    """Dopłaty do zestawów (sprzedaż napojów) i zakup napojów do zestawów (towary, VAT wg reguł)."""
    if wynik["doplaty"] >= 0.005:
        ksieguj(f, ks, rach, OPIS_DOPLAT, wynik["doplaty"], "przychod", stawka=stawka_dodatkow)
    if wynik["koszt_dodatkow"] >= 0.005:
        stawka = ks.stawka_vat(OPIS_DODATKOW) if ks.vat is not None else 0.0
        ksieguj(f, ks, rach, OPIS_DODATKOW, round(wynik["koszt_dodatkow"] * (1 + stawka), 2), "towary")


def raport(dane: Dane, f: Firma, nazwa_firmy: str, runda: int, wynik: dict | None, info: dict, ziarno=None) -> dict:
    """Wyniki promocji firmy w rundzie: trwające z liczbami (objęci, rabat, porcje gratis, dopłaty), komiczny tekst
    z pierwszej rundy promocji (z ziarnem), wyłączone."""
    R = zasady(dane)
    typy = (wynik or {}).get("typy", {})
    lista = []
    for p in f.promocje:
        typ = R["typy"].get(p.typ)
        if typ is None:
            continue
        t = typy.get(p.typ, {})
        x = {**p.model_dump(), "rodzaj": typ["nazwa"], "przyciaganie": przyciaganie(typ, p.od_rundy, runda),
             "rund": runda - p.od_rundy + 1, **{k: round(t.get(k, 0.0), 2) for k in ("rabat", "doplaty", "koszt_dodatkow")},
             "objeci": int(round(t.get("objeci", 0.0))), "gratis": int(round(t.get("gratis", 0.0)))}
        if p.od_rundy == runda and ziarno is not None:
            rng = strumien(ziarno, runda, "promocje", nazwa_firmy, p.typ)
            danie = dane.uslugi[p.danie]["nazwa"] if p.danie else ""
            x["tekst"] = typ["teksty"][int(rng.integers(len(typ["teksty"])))].format(nazwa=p.nazwa, danie=danie)
        lista.append(x)
    return {"promocje": lista, "nowe": info.get("nowe", []), "wylaczone": info.get("wylaczone", []),
            "przychod": round(sum((wynik or {}).get("przychod", {}).values()), 2) if wynik else 0.0}


def publiczne(dane: Dane, firmy: dict[str, Firma]) -> dict:
    """Promocje na mieście (dane rynku): {firma: [{"typ", "rodzaj", "nazwa", "danie", "od_rundy"}]}."""
    R = zasady(dane)
    if not R:
        return {}
    return {n: [{"typ": p.typ, "rodzaj": R["typy"][p.typ]["nazwa"], "nazwa": p.nazwa, "danie": p.danie,
                 "od_rundy": p.od_rundy} for p in f.promocje if p.typ in R["typy"]]
            for n, f in sorted(firmy.items()) if f.promocje}


def widok(dane: Dane, f: Firma, runda: int, rynek_poprzedni: dict | None, info: dict | None) -> dict:
    """Zakładka Promocje: rodzaje z liczbami, włączone (z decyzji), dania w sprzedaży, promocje konkurencji."""
    R = zasady(dane)
    nazwy_dni = dane.mapa["popyt"]["dni_tygodnia"]["nazwy"]
    rodzaje = []
    for t, typ in R["typy"].items():
        rodzaje.append({"id": t, "nazwa": typ["nazwa"], "opis": typ["opis"], "zakres": typ["zakres"],
                        "dni": [nazwy_dni[d] for d in typ["dni"]] if typ["dni"] is not None else None,
                        "strefy": [dane.mapa["strefy"][s]["nazwa"] for s in typ["strefy_klientow"] or []] or None,
                        **{k: typ[k] for k in ("rabat", "porcje", "doplata", "koszt_dodatku", "przyciaganie", "przyrost",
                                               "przyciaganie_min", "przyciaganie_max", "koszt_startu")}})
    aktywne = []
    for p in f.promocje:
        typ = R["typy"].get(p.typ)
        if typ:
            aktywne.append({**p.model_dump(), "rodzaj": typ["nazwa"], "przyciaganie": przyciaganie(typ, p.od_rundy, runda),
                            "nowa": p.od_rundy == runda})
    konk = {n: x for n, x in ((rynek_poprzedni or {}).get("promocje") or {}).items() if n != f.nazwa}
    return {"od_rundy": R["od_rundy"], "limit": R["limit_aktywnych"], "nazwa_max": R["nazwa_max"], "rodzaje": rodzaje,
            "aktywne": aktywne, "dania": [{"id": u, "nazwa": dane.uslugi[u]["nazwa"]} for u in f.ceny if u in dane.uslugi],
            "nowe": (info or {}).get("nowe", []), "konkurencja": konk}


__all__ = ["OPIS_DODATKOW", "OPIS_DOPLAT", "OPIS_STARTU", "ZAKLADKA", "efekty_ofert", "ksieguj_sprzedaz", "porcje",
           "przyciaganie", "publiczne", "raport", "rozlicz", "ustaw", "widok", "zasady"]
