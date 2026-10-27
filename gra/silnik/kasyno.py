"""Tajny klub z grami (gra z lokalami, dane/zdarzenia/kasyno.yaml).

Klubu nie ma na mapie ani w menu. Na koniec rundy drużyna może dostać zaproszenie (`Firma.zaproszenia`) – wtedy
w następnej rundzie drzwi są otwarte i można postawić kilka zakładów (`kasyno`: lista {gra, zaklad, stawka}).
Gra się z prywatnego portfela właściciela (silnik/wlasciciel.py), więc w księgach firmy nic się nie pojawia;
wygraną można wpłacić do firmy jako zwykłą wpłatę własną.

Mistrz gry nie widzi klubu: `ukryj` usuwa z widoku firmy klub, portfel i zaproszenia (api/widoki.py – widoki
mistrza gry, podgląd i eksport), a w rankingu i przeglądzie mistrza gry klubu nie ma wcale.
"""
from __future__ import annotations

from .dane import Dane
from .losowosc import strumien
from .model import Firma
from .zaleglosci import zl

ZAKLADKA = "kasyno"
EPS = 1e-6


def dane_kasyna(dane: Dane) -> dict | None:
    return (dane.zdarzenia or {}).get("kasyno")


def otwarte(f: Firma, runda: int) -> bool:
    return runda in f.zaproszenia


def tekst_zaproszenia(dane: Dane, f: Firma, runda: int) -> str | None:
    if not otwarte(f, runda):
        return None
    teksty = dane_kasyna(dane)["zaproszenie"]["teksty"]
    return teksty[f.zaproszenia.index(runda) % len(teksty)]


def _rozstrzygnij(gra: dict, zaklad: str | None, stawka: float, rng) -> dict:
    if gra["typ"] == "ruletka":
        liczba = int(rng.integers(gra["pola"]))
        z = gra["zaklady"][zaklad]
        wyplata = round(stawka * z["mnoznik"], 2) if liczba in z["wygrywa"] else 0.0
        teksty = gra["teksty_wygrana"] if wyplata else gra["teksty_przegrana"]
        tekst = teksty[int(rng.integers(len(teksty)))]
        return {"liczba": liczba, "wyplata": wyplata, "tekst": tekst.format(liczba=liczba, kwota=zl(wyplata))}
    los, suma = float(rng.random()), 0.0
    wynik = gra["wyniki"][-1]
    for w in gra["wyniki"]:
        suma += w["szansa"]
        if los < suma:
            wynik = w
            break
    wyplata = round(stawka * wynik["mnoznik"], 2)
    return {"mnoznik": wynik["mnoznik"], "wyplata": wyplata, "tekst": wynik["tekst"].format(kwota=zl(wyplata))}


def rozegraj(dane: Dane, f: Firma, d: dict, runda: int, ziarno: int | str, portfel: float,
             podglad: bool = False) -> tuple[float, dict | None]:
    """Zakłady rundy z portfela właściciela. Zwraca (portfel po grach, info – None bez zakładów).
    `podglad` – stawki schodzą z portfela, wyniki są nieznane (`ukryte`) do zamknięcia rundy."""
    K, zaklady = dane_kasyna(dane), d.get("kasyno") or []
    if not K or not zaklady or not isinstance(zaklady, list):
        return portfel, None
    info = {"zaklady": [], "odrzucone": [], "ukryte": podglad}
    if not otwarte(f, runda):
        info["odrzucone"].append({"co": "Wizyta przy ul. Nocnej", "powod": "drzwi od podwórza są zamknięte, a na dzwonek nikt nie odpowiada"})
        return portfel, info
    L = K["zaklady"]
    for i, z in enumerate(zaklady):
        z = z if isinstance(z, dict) else {}
        gra = K["gry"].get(z.get("gra"))
        try:
            stawka = round(float(z.get("stawka") or 0), 2)
        except (TypeError, ValueError):
            stawka = 0.0
        co = f"Zakład {i + 1}" + (f" – {gra['nazwa']}" if gra else "")
        if i >= L["maks"]:
            powod = f"w jednej rundzie najwyżej {L['maks']} zakładów – ochroniarz Mariusz odprowadza cię do wyjścia"
        elif not gra:
            powod = "nie ma takiej gry"
        elif gra["typ"] == "ruletka" and z.get("zaklad") not in gra["zaklady"]:
            powod = "pan Waldemar nie przyjmuje takiego zakładu"
        elif not L["min_stawka"] - EPS <= stawka <= L["maks_stawka"] + EPS:
            powod = f"stawka od {zl(L['min_stawka'])} do {zl(L['maks_stawka'])}"
        elif stawka > portfel + EPS:
            powod = "w prywatnym portfelu brakuje pieniędzy – klub nie przyjmuje kart firmowych"
        else:
            powod = None
        if powod:
            info["odrzucone"].append({"co": co, "powod": powod})
            continue
        portfel = round(portfel - stawka, 2)
        wynik = {"gra": z["gra"], "nazwa": gra["nazwa"], "typ": gra["typ"], "stawka": stawka,
                 "zaklad": z.get("zaklad") if gra["typ"] == "ruletka" else None,
                 "zaklad_nazwa": gra["zaklady"][z["zaklad"]]["nazwa"] if gra["typ"] == "ruletka" else None}
        if not podglad:
            wynik.update(_rozstrzygnij(gra, wynik["zaklad"], stawka, strumien(ziarno, runda, "kasyno", f.nazwa, i)))
            portfel = round(portfel + wynik["wyplata"], 2)
        info["zaklady"].append(wynik)
    info["stawki"] = round(sum(w["stawka"] for w in info["zaklady"]), 2)
    if not podglad:
        info["wyplaty"] = round(sum(w["wyplata"] for w in info["zaklady"]), 2)
        info["bilans"] = round(info["wyplaty"] - info["stawki"], 2)
    return portfel, info


def zaproszenie(dane: Dane, f: Firma, runda: int, ziarno: int | str, liczba_rund: int) -> int | None:
    """Na koniec rundy: czy drużyna dostaje zaproszenie na następną rundę (boty nie dostają)."""
    K = dane_kasyna(dane)
    if not K or f.bot:
        return None
    z, nast = K["zaproszenie"], runda + 1
    if nast < z["od_rundy"] or nast > liczba_rund or len(f.zaproszenia) >= z["maks"] or nast in f.zaproszenia:
        return None
    if strumien(ziarno, runda, "kasyno", f.nazwa).random() >= z["szansa"]:
        return None
    f.zaproszenia.append(nast)
    return nast


def raport(info: dict | None, zaproszono: int | None) -> dict | None:
    if not info and not zaproszono:
        return None
    return {"gry": info, "zaproszenie": zaproszono}


def bledy(info: dict | None) -> list[dict]:
    return [{"poziom": "czerwony", "zakladka": ZAKLADKA, "tekst": f"{o['co']}: {o['powod']}."}
            for o in (info or {}).get("odrzucone", [])]


def widok(dane: Dane, fp: Firma, runda: int, decyzja: dict | None, wyniki: dict | None) -> dict | None:
    """Zakładka klubu: tylko gdy drzwi są otwarte w tej rundzie albo są wyniki gier z poprzedniej rundy."""
    K = dane_kasyna(dane)
    ost = (wyniki or {}).get("kasyno")
    if not K or not (otwarte(fp, runda) or (ost and ost.get("gry"))):
        return None
    otw = otwarte(fp, runda)
    return {"otwarte": otw, "adres": K["kasyno"]["adres"], "zaproszenie": tekst_zaproszenia(dane, fp, runda),
            "klub": {k: K["kasyno"][k] for k in ("nazwa", "tekst")} if otw else None,
            "gry": {k: {"typ": g["typ"], "nazwa": g["nazwa"], "opis": g["opis"],
                        "zaklady": {z: {"nazwa": x["nazwa"], "mnoznik": x["mnoznik"]} for z, x in (g.get("zaklady") or {}).items()}}
                    for k, g in K["gry"].items()} if otw else None,
            "limity": dict(K["zaklady"]), "decyzja": decyzja}


# --- ukrywanie przed mistrzem gry ------------------------------------------------------------------

PORTFEL = "wlasciciel"   # zakładka i klucz wyników portfela właściciela (silnik/wlasciciel.py)


def _klucze(portfel: bool) -> tuple[str, ...]:
    return (ZAKLADKA, PORTFEL) if portfel else (ZAKLADKA,)


def _bez_bledow(lista: list | None, portfel: bool) -> list | None:
    if not isinstance(lista, list):
        return lista
    return [b for b in lista if not isinstance(b, dict) or b.get("zakladka") not in _klucze(portfel)]


def ukryj_wyniki(w: dict | None, portfel: bool = True) -> dict | None:
    """Wyniki firmy z rundy bez klubu (i portfela właściciela) oraz bez błędów tych zakładek (kopia)."""
    if not isinstance(w, dict):
        return w
    w = {k: v for k, v in w.items() if k not in _klucze(portfel)}
    if "lista_bledow" in w:
        w["lista_bledow"] = _bez_bledow(w["lista_bledow"], portfel)
    return w


def ukryj_decyzje(d: dict | None) -> dict | None:
    return {k: v for k, v in d.items() if k != ZAKLADKA} if isinstance(d, dict) else d


def ukryj(v: dict, portfel: bool = True) -> dict:
    """Widok firmy (api/prezentacja.widok) bez śladu klubu – dla mistrza gry także bez prywatnego portfela
    (zmiany portfela zdradzałyby klub); `portfel=False` – klub wyłączony na serwerze, portfel zostaje (kopia)."""
    v = {k: x for k, x in v.items() if k not in _klucze(portfel)}
    v["decyzje"] = ukryj_decyzje(v.get("decyzje"))
    for k in ("stan", "stan_przed"):
        if isinstance(v.get(k), dict):
            v[k] = {x: y for x, y in v[k].items() if x != "zaproszenia" and (not portfel or x != "portfel")}
    v["wyniki"] = ukryj_wyniki(v.get("wyniki"), portfel)
    v["lista_bledow"] = _bez_bledow(v.get("lista_bledow"), portfel)
    return v
