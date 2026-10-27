"""Konkurencja i detektyw (gra z lokalami, P16 – pytanie 26; dane: `dane/zdarzenia/detektyw.yaml`).

Przegląd – każda drużyna widzi ogólny obraz rywali z rynku poprzedniej rundy (`StanGry.rynek`): liczbę lokali,
przedział cen menu, czy się reklamują i mają promocje, udział w popycie na wszystkie dania.

Detektyw – decyzja `detektyw: firma rywala` (od `od_rundy`). Zlecenie kosztuje od `koszt_min` do `koszt_maks` zł
brutto (cena losowana co rundę dla każdej drużyny, co `krok`) i `godziny` właściciela (silnik/czas_wlasciciela.py);
bez wolnych godzin zlecenie jest odrzucone i nic nie kosztuje. Raport z dokładnymi danymi rywala z tej rundy
(gotówka, lokale, ceny i sprzedaż dań, załoga, kampanie, promocje, przychody i dochód) przychodzi w wynikach.
Z szansą `szansa_wpadki` detektyw wpada – raport i tak przychodzi, ale śledzony dowiaduje się w swoich wynikach,
kto go śledził. Boty nie zatrudniają detektywa.
"""
from __future__ import annotations

from collections import Counter

from .dane import Dane
from .finanse import Ksiega, Rachunek, ksieguj
from .losowosc import strumien
from .model import Firma

ZAKLADKA = "konkurencja"
OPIS = "Detektyw „Sokole Oko”: obserwacja konkurencji"


def dane_detektywa(dane: Dane) -> dict | None:
    return (dane.zdarzenia or {}).get("detektyw")


def koszt(dane: Dane, ziarno: int, runda: int, firma: str) -> float:
    """Cena zlecenia dla drużyny w rundzie (brutto, co `krok` zł)."""
    z = dane_detektywa(dane)["detektyw"]
    krokow = round((z["koszt_maks"] - z["koszt_min"]) / z["krok"])
    los = strumien(ziarno, runda, "detektyw", firma, "koszt")
    return round(z["koszt_min"] + z["krok"] * int(los.integers(0, krokow + 1)), 2)


def _wybierz(ziarno: int, runda: int, firma: str, co: str, teksty: list[str], **pola) -> str:
    return teksty[int(strumien(ziarno, runda, "detektyw", firma, co).integers(len(teksty)))].format(**pola)


def zlec(dane: Dane, f: Firma, d: dict, runda: int, ziarno: int, firmy: list[str], ks: Ksiega, rach: Rachunek,
         czas, podglad: bool = False) -> dict | None:
    """Zlecenie detektywa z decyzji rundy (po eventach w parkach – zużywa godziny właściciela).
    Zwraca {"rywal", "koszt", "godziny", "przyjete", "powod", "wpadka"} albo None (bez zlecenia)."""
    u = dane_detektywa(dane)
    cel = d.get("detektyw")
    if not u or not cel:
        return None
    z = u["detektyw"]
    info = {"rywal": cel, "koszt": koszt(dane, ziarno, runda, f.nazwa), "godziny": z["godziny"], "przyjete": False,
            "powod": None, "wpadka": False}
    if runda < z["od_rundy"]:
        info["powod"] = f"detektyw przyjmuje zlecenia od rundy {z['od_rundy']}"
    elif cel == f.nazwa or cel not in firmy:
        info["powod"] = f"nie ma rywala {cel!r}"
    elif not czas.wez(z["godziny"], f"Detektyw: obserwacja {cel}", ZAKLADKA):
        info["powod"] = "brak wolnych godzin właściciela"
    else:
        ksieguj(f, ks, rach, OPIS, info["koszt"], "pozostale")
        info["przyjete"] = True
        if not podglad:   # wpadka – dopiero w przeliczeniu
            info["wpadka"] = bool(strumien(ziarno, runda, "detektyw", f.nazwa, "wpadka").random() < z["szansa_wpadki"])
    return info


def bledy(info: dict | None) -> list[dict]:
    if not info or info["przyjete"]:
        return []
    return [{"poziom": "czerwony", "zakladka": ZAKLADKA, "tekst": f"Detektyw: {info['powod']} – zlecenie odrzucone."}]


def dane_rywala(w: dict) -> dict:
    """Dokładne dane rywala z jego wyników rundy (raport detektywa)."""
    zaloga = Counter((p["zawod"], p["gwiazdki"]) for p in w.get("pracownicy", []))
    pensje: dict[tuple, float] = {}
    for p in w.get("pracownicy", []):
        pensje[p["zawod"], p["gwiazdki"]] = pensje.get((p["zawod"], p["gwiazdki"]), 0) + p["pensja"]
    return {"gotowka": w["gotowka"], "zadluzenie": w.get("zadluzenie", 0),
            "przychody": w["kpir"]["przychody"], "koszty": w["kpir"]["koszty"], "dochod_netto": w["kpir"]["dochod_netto"],
            "lokale": [{"nazwa": lk["nazwa"], "strefa": lk["strefa"], "forma": lk["forma"]} for lk in w.get("lokale", [])],
            "menu": [{"usluga": u, "cena": s["cena"], "cena_po_rabacie": s.get("cena_po_rabacie", s["cena"]),
                      "popyt": s["popyt"], "sprzedaz": s["sprzedaz"], "przychod": s["przychod"],
                      "reklamacje": s.get("reklamacje", 0)} for u, s in w.get("sprzedaz", {}).items()],
            "zaloga": [{"zawod": zw, "gwiazdki": g, "liczba": n, "pensja": round(pensje[zw, g] / n, 2)}
                       for (zw, g), n in sorted(zaloga.items())],
            "kampanie": [{"nazwa": k["nazwa"], "agencja": k.get("agencja_nazwa"), "strefa": k.get("strefa_nazwa"),
                          "koszt": k.get("koszt", 0)} for k in (w.get("reklama_agencje") or {}).get("kampanie", [])],
            "promocje": [{"nazwa": p["nazwa"], "rodzaj": p.get("rodzaj"), "danie": p.get("danie")}
                         for p in (w.get("promocje") or {}).get("promocje", [])],
            "zadowolenie_klientow": (w.get("karta") or {}).get("zadowolenie_klientow")}


def raporty(dane: Dane, wyniki: dict[str, dict], zlecenia: dict[str, dict | None], runda: int, ziarno: int) -> None:
    """Raporty detektywa i wpadki – po wynikach wszystkich firm rundy (wpisuje `wyniki[firma]["konkurencja"]`)."""
    u = dane_detektywa(dane)
    if not u:
        return
    for n in wyniki:
        wyniki[n]["konkurencja"] = {"zlecenie": zlecenia.get(n), "raport": None, "wpadki": []}
    for n in sorted(zlecenia):
        z = zlecenia[n]
        if not z or not z["przyjete"]:
            continue
        k = wyniki[n]["konkurencja"]
        k["raport"] = {"rywal": z["rywal"], **dane_rywala(wyniki[z["rywal"]]),
                       "tekst": _wybierz(ziarno, runda, n, "raport", u["raporty"], rywal=z["rywal"])}
        if z["wpadka"]:
            k["raport"]["wpadka"] = _wybierz(ziarno, runda, n, "wpadka_tekst", u["wpadki"], rywal=z["rywal"])
            wyniki[z["rywal"]]["konkurencja"]["wpadki"].append(
                {"kto": n, "tekst": _wybierz(ziarno, runda, n, "ofiara", u["ofiary"], kto=n)})


def przeglad(rynek: dict | None, firma: str) -> list[dict]:
    """Ogólny obraz rynku dla każdej drużyny (z publicznego rynku rundy): firma, lokale, ceny, reklama, promocje, udział."""
    if not rynek:
        return []
    popyt = rynek.get("popyt", {})
    klienci = {n: sum(p.get(n, 0) for p in popyt.values()) for n in rynek["firmy"]}
    razem = sum(klienci.values())
    lokale = Counter((rynek.get("lokale") or {}).values())
    wynik = []
    for n in rynek["firmy"]:
        ceny = [c[n] for c in rynek.get("ceny", {}).values() if c.get(n) is not None]
        kampanie = ((rynek.get("kampanie") or {}).get(n) or {}).get("kampanie", [])
        wynik.append({"firma": n, "ja": n == firma, "lokale": lokale.get(n, 0), "dania": len(ceny),
                      "cena_min": min(ceny) if ceny else None, "cena_maks": max(ceny) if ceny else None,
                      "reklama": bool(kampanie), "promocje": bool((rynek.get("promocje") or {}).get(n)),
                      "udzial": round(klienci[n] / razem, 4) if razem else 0.0})
    return wynik


def widok(dane: Dane, firma: str, runda: int, ziarno: int, rynek: dict | None, decyzja: dict | None) -> dict | None:
    """Zakładka Konkurencja: przegląd rynku z poprzedniej rundy, cennik detektywa w tej rundzie i zlecenie."""
    u = dane_detektywa(dane)
    if not u:
        return None
    z = u["detektyw"]
    return {"nazwa": z["nazwa"], "od_rundy": z["od_rundy"], "otwarty": runda >= z["od_rundy"],
            "koszt": koszt(dane, ziarno, runda, firma), "godziny": z["godziny"], "szansa_wpadki": z["szansa_wpadki"],
            "powitanie": _wybierz(ziarno, runda, firma, "powitanie", u["powitania"]),
            "przeglad": przeglad(rynek, firma), "decyzja": decyzja}
