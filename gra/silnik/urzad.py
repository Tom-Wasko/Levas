"""Urząd i sanepid (gra z lokalami, F3b.6; notatka „Elementy mapy” – Urząd / Sanepid).

Dane: `dane/zdarzenia/urzad.yaml`. Firma jest zarejestrowana w CEIDG przed grą (wpis bezpłatny – tylko opis
w zakładce). Każdy lokal przed pierwszą rundą sprzedaży odbiera sanepid (w decyzjach, po lokalach): przy poziomie
higieny bez `odbior` – odmowa i lokal zaczyna działać `odbior.odroczenie_rund` rund później (`Lokal.dziala_od`),
i tak do skutku; przyjęte odbiory – `Firma.odbiory` (lokal → runda).

Higiena – decyzja `higiena: poziom` (`Firma.higiena`, trwa do zmiany; None – `higiena.domyslna`). Koszt poziomu
(miesięczny, brutto) co rundę za każdy działający lokal. Kontrola sanepidu (silnik/magazyn.py) dostaje
`modyfikatory`: dodatek poziomu i skarg (skutek `kontrola` w historiach → `Efekt` typu „kontrola”) do części szansy
z problemów, mnożnik tej części i dodatek do mandatu.
"""
from __future__ import annotations

from . import magazyn as mag
from .dane import Dane
from .finanse import Ksiega, Rachunek, ksieguj
from .losowosc import strumien
from .model import Efekt, Firma

ZAKLADKA = "urzad"
SPRZATANIE = "Utrzymanie czystości"


def dane_urzedu(dane: Dane) -> dict | None:
    return (dane.zdarzenia or {}).get("urzad")


def higiena(dane: Dane) -> dict:
    return dane_urzedu(dane)["higiena"]


def poziom(dane: Dane, f: Firma) -> str:
    h = higiena(dane)
    return f.higiena if f.higiena in h["poziomy"] else h["domyslna"]


def skargi(f: Firma, runda: int) -> list[Efekt]:
    return [e for e in f.efekty if e.typ == "kontrola" and e.od_rundy <= runda <= e.do_rundy]


def modyfikatory(dane: Dane, f: Firma, runda: int) -> dict | None:
    """Zmiany kontroli sanepidu w rundzie: {"higiena", "dodatek", "mnoznik", "mandat", "skargi"} (None – bez urzędu)."""
    if not dane_urzedu(dane):
        return None
    p = higiena(dane)["poziomy"][poziom(dane, f)]
    sk = round(sum(e.wartosc for e in skargi(f, runda)), 4)
    return {"higiena": poziom(dane, f), "dodatek": round(p["dodatek"] + sk, 4), "mnoznik": p["mnoznik"],
            "mandat": p["mandat"], "skargi": sk}


def _nazwa_lokalu(dane: Dane, lid: str) -> str:
    return (dane.lokale.get(lid) or {}).get("nazwa", lid)


def ustaw(dane: Dane, f: Firma, d: dict, runda: int, ziarno, ks: Ksiega, rach: Rachunek) -> dict:
    """Higiena z decyzji, odbiór lokali, które w tej rundzie mają zacząć działać, i koszt utrzymania czystości.
    Zwraca {"higiena", "zmiana", "odbiory", "koszt", "lokale", "uwagi"}."""
    info = {"higiena": None, "zmiana": False, "odbiory": [], "koszt": 0.0, "lokale": 0, "uwagi": []}
    if not dane_urzedu(dane):
        return info
    H, O = higiena(dane), dane_urzedu(dane)["odbior"]
    if "higiena" in d:
        x = d.get("higiena")
        if x not in H["poziomy"]:
            info["uwagi"].append(f"Nieznany poziom higieny: {x}.")
        else:
            info["zmiana"] = x != poziom(dane, f)
            f.higiena = x
    info["higiena"] = poziom(dane, f)
    p = H["poziomy"][info["higiena"]]
    for lok in f.lokale:
        if lok.id in f.odbiory or lok.dziala_od > runda:
            continue
        teksty = O["teksty_ok" if p["odbior"] else "teksty_odmowa"]
        los = strumien(ziarno, runda, "odbior", f.nazwa, lok.id)
        tekst = " ".join(teksty[int(los.integers(len(teksty)))].split()).replace("{rund}", str(O["odroczenie_rund"]))
        if p["odbior"]:
            f.odbiory[lok.id] = runda
        else:
            lok.dziala_od = runda + O["odroczenie_rund"]
        info["odbiory"].append({"lokal": lok.id, "nazwa": _nazwa_lokalu(dane, lok.id), "przyjety": p["odbior"],
                                "dziala_od": lok.dziala_od, "tekst": tekst})
    info["lokale"] = sum(lok.dziala_od <= runda for lok in f.lokale)
    info["koszt"] = dane.na_runde(round(p["koszt"] * info["lokale"], 2))
    if info["koszt"] > 0:
        ksieguj(f, ks, rach, f"{SPRZATANIE}: {p['nazwa']}", info["koszt"], "pozostale")
    return info


def bledy(dane: Dane, info: dict | None) -> list[dict]:
    info = info or {}
    wynik = [{"poziom": "czerwony", "zakladka": ZAKLADKA, "tekst": t} for t in info.get("uwagi", [])]
    if (p := info.get("higiena")) and dane_urzedu(dane):
        nazwa = higiena(dane)["poziomy"][p]["nazwa"]
        wynik += [{"poziom": "czerwony", "zakladka": ZAKLADKA,
                   "tekst": f"Sanepid nie odbierze lokalu {o['nazwa']} przy higienie „{nazwa}” – lokal nie ruszy w tej rundzie."}
                  for o in info.get("odbiory", []) if not o["przyjety"]]
    return wynik


def raport(info: dict | None, magazyn: dict | None) -> dict:
    """Wyniki rundy: higiena i jej koszt, odbiory lokali, kontrola sanepidu (z silnik/magazyn.py)."""
    info = info or {"higiena": None, "zmiana": False, "odbiory": [], "koszt": 0.0, "lokale": 0, "uwagi": []}
    return {**info, "kontrola": (magazyn or {}).get("sanepid")}


def widok(dane: Dane, f: Firma, runda: int, info: dict | None, wyniki: dict, firma: str,
          przeterminowane: float = 0.0) -> dict | None:
    """Zakładka Urząd i sanepid: rejestracja, poziomy higieny, odbiory lokali, ryzyko kontroli i historia kontroli."""
    if not dane_urzedu(dane):
        return None
    U, H = dane_urzedu(dane), higiena(dane)
    rap = [(r, (wyniki[r].get(firma) or {}).get("urzad")) for r in sorted(wyniki) if r < runda]
    rap = [(r, x) for r, x in rap if x]
    z = mag.zasady_sanepidu(dane)
    return {"nazwa": U["urzad"]["nazwa"], "rejestracja": U["urzad"]["rejestracja"],
            "odroczenie_rund": U["odbior"]["odroczenie_rund"],
            "poziomy": [{"id": k, **{x: p[x] for x in ("nazwa", "opis", "koszt", "dodatek", "mnoznik", "mandat", "odbior")},
                         "koszt_rundy": dane.na_runde(p["koszt"])} for k, p in H["poziomy"].items()],
            "higiena": poziom(dane, f), "domyslna": H["domyslna"],
            "lokale": [{"id": lok.id, "nazwa": _nazwa_lokalu(dane, lok.id), "dziala_od": lok.dziala_od,
                        "odbior": f.odbiory.get(lok.id)} for lok in f.lokale],
            "skargi": [{"opis": e.opis, "szansa": e.wartosc, "do_rundy": e.do_rundy} for e in skargi(f, runda)],
            "ryzyko": mag.ryzyko(dane, f, runda, przeterminowane, modyfikatory(dane, f, runda)),
            "szansa_bazowa": z["szansa_bazowa"] if z else None,
            "decyzja": info,
            "kontrole": [{"runda": r, **x["kontrola"]} for r, x in rap if (x.get("kontrola") or {}).get("kontrola")],
            "koszt_razem": round(sum(x["koszt"] for _, x in rap), 2),
            "mandaty_razem": round(sum((x.get("kontrola") or {}).get("mandat", 0) for _, x in rap), 2)}
