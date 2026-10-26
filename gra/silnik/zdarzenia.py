"""Eventy w parkach (gra z lokalami, F3b.1; notatki „Elementy mapy” i „Zdarzenia i historie”).

Dane: `dane/zdarzenia/parki.yaml`. Od rundy `zasady.od_rundy` co rundę w jednym z parków zaczyna się historia – ta
sama dla wszystkich drużyn (kolejność losowana bez powtórzeń w cyklu wszystkich historii, strumień „parki”). Każda
drużyna przeżywa ją osobno: w scenie wybiera opcję (decyzja `zdarzenia: {historia: opcja}`, bez wyboru – opcja
domyślna), opcje kosztują czas właściciela, gotówkę i porcje jedzenia. Ciąg dalszy czeka w `Firma.historie` na swoją
rundę (z szansą, strumień „zdarzenia”). Skutki: gotówka (bez VAT), mnożnik popytu i mniej godzin właściciela
(`Firma.efekty`), kandydat na rynku pracy widoczny tylko dla tej drużyny (`tylko_dla`).
"""
from __future__ import annotations

from . import czas_wlasciciela as cw
from .dane import Dane
from .finanse import Ksiega, Rachunek, ksieguj
from .losowosc import strumien
from .model import Efekt, Firma, OtwartaHistoria

ZAKLADKA = "zdarzenia"


def zasady(dane: Dane) -> dict:
    return dane.zdarzenia["parki"]["zasady"]


def historie(dane: Dane) -> dict[str, dict]:
    return {h["id"]: h for h in dane.zdarzenia["parki"]["historie"]}


def event_parku(dane: Dane, ziarno, runda: int) -> str | None:
    """Historia, która zaczyna się w parku w tej rundzie (ta sama dla wszystkich drużyn); None – jeszcze nie ma."""
    if not dane.zdarzenia or runda < zasady(dane)["od_rundy"]:
        return None
    ids = list(historie(dane))
    cykl, i = divmod(runda - zasady(dane)["od_rundy"], len(ids))
    return ids[int(strumien(ziarno, cykl, "parki").permutation(len(ids))[i])]


def aktywne(dane: Dane, f: Firma, runda: int, ziarno) -> list[OtwartaHistoria]:
    """Sceny firmy w tej rundzie: event parku (gdy firma nie jest już w tej historii) i ciągi dalsze."""
    wynik = [h for h in f.historie if h.runda <= runda]
    hid = event_parku(dane, ziarno, runda)
    if hid and all(h.historia != hid for h in f.historie):
        wynik.insert(0, OtwartaHistoria(historia=hid, scena=historie(dane)[hid]["start"], runda=runda))
    return wynik


def _koszt(o: dict, koszt_porcji: float) -> dict:
    k = o["koszt"]
    return {"czas": k["czas"], "gotowka": k["gotowka"], "porcje": k["porcje"],
            "razem_zl": round(k["gotowka"] + k["porcje"] * koszt_porcji, 2)}


def _ciag_dalszy(nastepne: list[dict], los: float) -> dict | None:
    prog = 0.0
    for n in nastepne:
        prog += n["szansa"]
        if los < prog:
            return n
    return None


def rozegraj(dane: Dane, f: Firma, d: dict, runda: int, ziarno, ks: Ksiega, rach: Rachunek, czas: cw.Czas,
             podglad: bool = False) -> dict:
    """Sceny rundy: koszty wybranych opcji (czas, gotówka, porcje), a poza podglądem także skutki i ciąg dalszy.
    Zwraca {"sceny": [...], "bledy": [...], "kandydaci": [...]} – kandydaci do puli rynku pracy."""
    wybory = d.get("zdarzenia") or {}
    hs, kp = historie(dane), zasady(dane)["koszt_porcji"]
    wynik = {"sceny": [], "bledy": [], "kandydaci": []}
    zostaja = [h for h in f.historie if h.runda > runda]
    for oh in aktywne(dane, f, runda, ziarno):
        h = hs.get(oh.historia)
        sc = h["sceny"].get(oh.scena) if h else None
        if sc is None:   # historia zniknęła z danych
            continue
        wpis = {"historia": h["id"], "tytul": h["tytul"], "park": h["park"], "powazna": h["powazna"], "scena": oh.scena,
                "tekst": sc["tekst"], "opcja": None, "domyslna": False, "wynik": None, "koszt": None, "skutki": [],
                "ciag_dalszy": None}
        skutki, nastepne = sc["skutki"], sc["nastepna"]
        if sc["opcje"]:
            opcje = {o["id"]: o for o in sc["opcje"]}
            o = opcje.get(wybory.get(h["id"])) or opcje[sc["domyslna"]]
            if o["koszt"]["czas"] and not czas.wez(o["koszt"]["czas"], f"{h['tytul']}: {o['tekst']}", ZAKLADKA):
                wynik["bledy"].append({"poziom": "czerwony", "zakladka": ZAKLADKA, "tekst":
                                       f"„{h['tytul']}”: nie starcza czasu właściciela na „{o['tekst']}” "
                                       f"({cw.godziny(o['koszt']['czas'])} h) – gra wybrała „{opcje[sc['domyslna']]['tekst']}”."})
                o = opcje[sc["domyslna"]]
            elif podglad and h["id"] not in wybory:   # tylko przy decyzjach (w wynikach rundy to bez sensu)
                wynik["bledy"].append({"poziom": "niebieski", "zakladka": ZAKLADKA, "tekst":
                                       f"„{h['tytul']}”: wybierz reakcję w zakładce Zdarzenia (bez wyboru: „{o['tekst']}”)."})
            wpis.update(opcja=o["id"], opcja_tekst=o["tekst"], domyslna=o["id"] == sc["domyslna"], wynik=o["wynik"],
                        koszt=_koszt(o, kp))
            if o["koszt"]["gotowka"]:
                ksieguj(f, ks, rach, f"Park – {h['tytul']}", o["koszt"]["gotowka"], "pozostale", stawka=0)
            if o["koszt"]["porcje"]:
                ksieguj(f, ks, rach, f"Porcje jedzenia – {h['tytul']} ({o['koszt']['porcje']} szt.)",
                        o["koszt"]["porcje"] * kp, "towary", stawka=0)
            skutki, nastepne = o["skutki"], o["nastepna"]
        wpis["skutki"] = [{k: v for k, v in s.items() if v is not None} for s in skutki]
        if not podglad:
            for s in skutki:
                _skutek(f, s, h["id"], runda, ks, rach, wynik["kandydaci"])
            n = _ciag_dalszy(nastepne, strumien(ziarno, runda, "zdarzenia", f.nazwa, h["id"]).random())
            if n:
                wpis["ciag_dalszy"] = runda + n["za_ile_rund"]
                zostaja.append(OtwartaHistoria(historia=h["id"], scena=n["scena"], runda=runda + n["za_ile_rund"],
                                               zrodlo=oh.zrodlo, sciezka=[*oh.sciezka, oh.scena]))
        wynik["sceny"].append(wpis)
    if not podglad:
        f.historie = zostaja
        f.efekty = [e for e in f.efekty if e.do_rundy >= runda]
    return wynik


def _skutek(f: Firma, s: dict, hid: str, runda: int, ks: Ksiega, rach: Rachunek, kandydaci: list[dict]):
    if s["typ"] == "gotowka":
        if s["kwota"] > 0:
            ksieguj(f, ks, rach, s["opis"], s["kwota"], "przychod_pozostaly", stawka=0)
        else:
            ksieguj(f, ks, rach, s["opis"], -s["kwota"], "pozostale", stawka=0)
    elif s["typ"] == "popyt":   # od tej rundy (sprzedaż jest po decyzjach)
        f.efekty.append(Efekt(typ="popyt", wartosc=s["mnoznik"], od_rundy=runda, do_rundy=runda + s["rund"] - 1,
                              opis=s["opis"]))
    elif s["typ"] == "czas":    # od następnej rundy (w tej czas jest już rozdzielony)
        f.efekty.append(Efekt(typ="czas", wartosc=s["godziny"], od_rundy=runda + 1, do_rundy=runda + s["rund"],
                              opis=s["opis"]))
    elif s["typ"] == "kandydat":
        kandydaci.append({**s["kandydat"], "id": f"zd_{hid}_{f.nazwa}_{runda}", "tylko_dla": f.nazwa})


def mnoznik_popytu(f: Firma, runda: int) -> float:
    m = 1.0
    for e in f.efekty:
        if e.typ == "popyt" and e.od_rundy <= runda <= e.do_rundy:
            m *= e.wartosc
    return m


def efekty_czasu(f: Firma, runda: int) -> list[Efekt]:
    return [e for e in f.efekty if e.typ == "czas" and e.od_rundy <= runda <= e.do_rundy]


def wybor_bota(dane: Dane, f: Firma, runda: int, ziarno) -> dict:
    """Bot wybiera losowo jedną z opcji, które zajmują najwyżej 3 godziny właściciela."""
    hs, wynik = historie(dane), {}
    for oh in aktywne(dane, f, runda, ziarno):
        sc = hs[oh.historia]["sceny"].get(oh.scena) if oh.historia in hs else None
        opcje = [o["id"] for o in (sc or {}).get("opcje", []) if o["koszt"]["czas"] <= 3]
        if opcje:
            wynik[oh.historia] = opcje[int(strumien(ziarno, runda, "bot", f.nazwa, "zdarzenia", oh.historia).integers(len(opcje)))]
    return wynik


def widok(dane: Dane, fp: Firma, runda: int, ziarno, wyniki: dict, firma: str) -> dict:
    """Zakładka Zdarzenia: sceny tej rundy (z opcjami i kosztami), efekty i dziennik historii z poprzednich rund."""
    hs, kp = historie(dane), zasady(dane)["koszt_porcji"]
    akt = []
    for oh in aktywne(dane, fp, runda, ziarno):
        h = hs.get(oh.historia)
        sc = h["sceny"].get(oh.scena) if h else None
        if sc is None:
            continue
        akt.append({"historia": h["id"], "tytul": h["tytul"], "park": h["park"], "powazna": h["powazna"],
                    "scena": oh.scena, "tekst": sc["tekst"], "domyslna": sc["domyslna"], "nowa": oh.scena == h["start"],
                    "opcje": [{"id": o["id"], "tekst": o["tekst"], "koszt": _koszt(o, kp)} for o in sc["opcje"]],
                    "skutki": [{k: v for k, v in s.items() if v is not None} for s in sc["skutki"]]})
    dziennik = [{**w, "runda": r} for r in sorted(wyniki) if r < runda
                for w in ((wyniki[r].get(firma) or {}).get("zdarzenia") or {}).get("sceny", [])]
    return {"aktywne": akt, "koszt_porcji": kp, "od_rundy": zasady(dane)["od_rundy"],
            "efekty": [{"typ": e.typ, "wartosc": e.wartosc, "od_rundy": e.od_rundy, "do_rundy": e.do_rundy, "opis": e.opis}
                       for e in fp.efekty if e.do_rundy >= runda],
            "oczekujace": [{"historia": h.historia, "tytul": hs[h.historia]["tytul"], "runda": h.runda}
                           for h in fp.historie if h.runda > runda and h.historia in hs],
            "dziennik": dziennik}
