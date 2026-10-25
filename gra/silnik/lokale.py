"""Lokale i działki na mapie miasta (dane: `dane/mapa/lokale.yaml`).

Pula lokali jest wspólna: lokal zajęty przez drużynę znika z oferty innych. Decyzja rundy:

    "lokal": {"id": "centrum_3", "forma": "najem" | "kupno"}

- gotowy – działa od razu, ze sprzętem z zestawu (przy najmie sprzęt wynajmującego – nie do sprzedania);
- niewyposazony – jednorazowa adaptacja (koszt KPiR), działa od następnej rundy, sprzęt trzeba kupić;
- dzialka – tylko kupno, budowa `budowa_rund` rund (raty co rundę), potem lokal bez sprzętu.

Najem: kaucja (`kaucja_miesiecy` × czynsz) i co rundę czynsz (KPiR). Każdy działający lokal: co rundę media
(utrzymanie, KPiR). Kupno, kaucja i budowa to ruchy na rachunku (bez KPiR). Nowy lokal można wziąć, gdy
od wzięcia każdego poprzedniego minęło `nowy_lokal_co_rund` rund. Stanowiska stoją w działających lokalach
i jest ich najwyżej tyle, ile lokal ma miejsc (`miejsca`). Dwie drużyny chcące ten sam lokal w jednej
rundzie: dostaje go ta, która jest wcześniej w kolejności rundy (losowej, jak przy zatrudnianiu).
"""
from __future__ import annotations

from .dane import TYPY_STANOWISK, Dane
from .finanse import Ksiega, Rachunek, ksieguj
from .model import Firma, Lokal, Stanowisko

FORMY = ("najem", "kupno")


def tryb_lokali(dane: Dane, konfiguracja: dict) -> bool:
    """Gra z lokalami: dane mają mapę i gra została założona z lokalami (stare zapisy gier – bez)."""
    return dane.mapa is not None and bool(konfiguracja.get("lokale", False))


def zajete(firmy: dict[str, Firma]) -> dict[str, str]:
    """Zajęte lokale: id → nazwa firmy."""
    return {lok.id: n for n, f in firmy.items() for lok in f.lokale}


def dostepne(dane: Dane, runda: int, zajete_lokale: dict[str, str]) -> list[dict]:
    """Lokale z oferty w rundzie (już wystawione i wolne)."""
    return [lok for lok in dane.mapa["lokale"] if lok.get("od_rundy", 1) <= runda and lok["id"] not in zajete_lokale]


def runda_nowego_lokalu(dane: Dane, firma: Firma) -> int:
    """Najwcześniejsza runda, w której firma może wziąć kolejny lokal."""
    co = dane.mapa["zasady"]["nowy_lokal_co_rund"]
    return max((lok.od_rundy + co for lok in firma.lokale), default=1)


def dziala_od(dane: Dane, lok: dict, runda: int) -> int:
    if lok["typ"] == "dzialka":
        return runda + lok["budowa_rund"]
    if lok["typ"] == "niewyposazony":
        return runda + dane.mapa["zasady"]["urzadzanie_rund"]
    return runda


def koszt_wejscia(dane: Dane, lok: dict, forma: str) -> float:
    """Jednorazowy koszt wzięcia lokalu w rundzie decyzji: kaucja albo cena, plus adaptacja."""
    if forma == "kupno":
        return lok["cena"] + lok.get("adaptacja", 0)
    return dane.mapa["zasady"]["kaucja_miesiecy"] * lok["czynsz"] + lok.get("adaptacja", 0)


def powod_odrzucenia(dane: Dane, firma: Firma, decyzja: dict, runda: int, zajete_lokale: dict[str, str]) -> str | None:
    """Dlaczego lokalu nie można wziąć (None – można)."""
    lok = dane.lokale.get(decyzja.get("id"))
    forma = decyzja.get("forma")
    if lok is None:
        return "Nie ma takiego lokalu."
    if forma not in FORMY:
        return "Wybierz najem albo kupno lokalu."
    if lok.get("od_rundy", 1) > runda:
        return f"{lok['nazwa']} będzie w ofercie od rundy {lok['od_rundy']}."
    if lok["id"] in zajete_lokale:
        return f"{lok['nazwa']} zajęła już firma {zajete_lokale[lok['id']]}."
    if runda < runda_nowego_lokalu(dane, firma):
        return (f"Kolejny lokal można wziąć co {dane.mapa['zasady']['nowy_lokal_co_rund']} rundy "
                f"(najwcześniej w rundzie {runda_nowego_lokalu(dane, firma)}).")
    if forma == "najem" and lok.get("czynsz") is None:
        return f"{lok['nazwa']} jest tylko na sprzedaż."
    if forma == "kupno" and lok.get("cena") is None:
        return f"{lok['nazwa']} jest tylko do wynajęcia."
    if forma == "kupno" and firma.gotowka < koszt_wejscia(dane, lok, forma):
        return f"Za mało gotówki na zakup: potrzeba {koszt_wejscia(dane, lok, forma):,.0f} zł.".replace(",", " ")
    return None


def wybierz(dane: Dane, firma: Firma, decyzja: dict | None, runda: int, zajete_lokale: dict[str, str],
            ksiega: Ksiega, rachunek: Rachunek) -> dict:
    """Decyzja o nowym lokalu. Zwraca {"id", "forma", "przyjety", "powod", "dziala_od"} (pusty – brak decyzji)."""
    if not decyzja or not decyzja.get("id"):
        return {}
    info = {"id": decyzja["id"], "forma": decyzja.get("forma")}
    powod = powod_odrzucenia(dane, firma, decyzja, runda, zajete_lokale)
    if powod:
        return {**info, "przyjety": False, "powod": powod}
    lok, forma = dane.lokale[decyzja["id"]], decyzja["forma"]
    nowy = Lokal(id=lok["id"], forma=forma, od_rundy=runda, dziala_od=dziala_od(dane, lok, runda))
    if forma == "najem":
        nowy.czynsz = lok["czynsz"]
        nowy.kaucja = dane.mapa["zasady"]["kaucja_miesiecy"] * lok["czynsz"]
        rachunek.zapisz(firma, f"Kaucja za lokal: {lok['adres']}", -nowy.kaucja)
    else:
        nowy.cena = lok["cena"]
        rachunek.zapisz(firma, f"Zakup {'działki' if lok['typ'] == 'dzialka' else 'lokalu'}: {lok['adres']}", -nowy.cena)
    if lok.get("adaptacja"):
        ksieguj(firma, ksiega, rachunek, f"Adaptacja lokalu: {lok['adres']}", lok["adaptacja"])
    firma.lokale.append(nowy)
    zajete_lokale[lok["id"]] = firma.nazwa
    if lok["typ"] == "gotowy":
        for st in dane.mapa["zestawy"][lok["zestaw"]]["stanowiska"]:
            if forma == "kupno":  # kupiony sprzęt jest firmy – liczy się do majątku (rozwój firmy), jak kupiony osobno
                firma.majatek += sum(dane.sprzet[n]["ceny"][str(q)] for n, q in st["sprzet"].items())
            firma.stanowiska.append(Stanowisko(
                nr=len(firma.stanowiska_typu(st["typ"])) + 1, typ=st["typ"], od_rundy=runda, lokal=lok["id"],
                sprzet=dict(st["sprzet"]), sprzet_wynajmujacego=list(st["sprzet"]) if forma == "najem" else []))
    return {**info, "przyjety": True, "powod": None, "dziala_od": nowy.dziala_od}


def wolne_miejsca(dane: Dane, firma: Firma, runda: int) -> dict[str, list[str]]:
    """Wolne miejsca na nowe stanowiska w działających lokalach: typ → lista id lokali (id powtórzone tyle razy,
    ile miejsc), w kolejności wzięcia lokali."""
    wynik: dict[str, list[str]] = {t: [] for t in TYPY_STANOWISK}
    for lok in firma.lokale:
        if lok.dziala_od > runda:
            continue
        for typ in TYPY_STANOWISK:
            zajetych = sum(1 for s in firma.stanowiska_typu(typ) if s.lokal == lok.id)
            wynik[typ] += [lok.id] * max(0, dane.lokale[lok.id]["miejsca"][typ] - zajetych)
    return wynik


def koszty_rundy(dane: Dane, firma: Firma, runda: int, ksiega: Ksiega, rachunek: Rachunek) -> None:
    """Czynsz najmu, media działających lokali i raty budowy (w miejsce stałego kosztu utrzymania lokalu)."""
    for lok in firma.lokale:
        d = dane.lokale[lok.id]
        if lok.forma == "najem":
            ksieguj(firma, ksiega, rachunek, f"Czynsz najmu: {d['adres']}", dane.na_runde(lok.czynsz))
        if lok.dziala_od <= runda:
            ksieguj(firma, ksiega, rachunek, f"{dane.okres['przymiotnik']} koszt utrzymania lokalu: {d['adres']}",
                    dane.na_runde(d["utrzymanie"]))
        elif d["typ"] == "dzialka":
            etap = runda - lok.od_rundy + 1
            rachunek.zapisz(firma, f"Budowa lokalu: {d['adres']} (etap {etap} z {d['budowa_rund']})",
                            -d["koszt_budowy"] / d["budowa_rund"])


def bledy(dane: Dane, firma: Firma, runda: int, info: dict, dodaj) -> None:
    """Uwagi do listy błędów (zakładka „lokale”)."""
    if info and not info["przyjety"]:
        dodaj("czerwony", "lokale", f"Lokal nie został przydzielony: {info['powod']}")
    if not firma.lokale:
        dodaj("czerwony", "lokale", "Nie masz lokalu – wynajmij albo kup lokal w zakładce Lokale. "
                                    "Bez lokalu nie ma stanowisk ani sprzedaży.")
    for lok in firma.lokale:
        d = dane.lokale[lok.id]
        if lok.dziala_od > runda:
            co = "Budowa" if d["typ"] == "dzialka" else "Urządzanie"
            dodaj("niebieski", "lokale", f"{co}: {d['nazwa']} – lokal zacznie działać w rundzie {lok.dziala_od}.")


def stan_lokali(dane: Dane, firma: Firma, runda: int) -> list[dict]:
    """Lokale firmy do wyników: dane z mapy + forma, status, zajęte miejsca."""
    wynik = []
    for lok in firma.lokale:
        d = dane.lokale[lok.id]
        wynik.append({"id": lok.id, "nazwa": d["nazwa"], "adres": d["adres"], "strefa": d["strefa"], "typ": d["typ"],
                      "forma": lok.forma, "od_rundy": lok.od_rundy, "dziala_od": lok.dziala_od,
                      "dziala": lok.dziala_od <= runda, "czynsz": lok.czynsz, "utrzymanie": d["utrzymanie"],
                      "miejsca": d["miejsca"],
                      "zajete": {t: sum(1 for s in firma.stanowiska_typu(t) if s.lokal == lok.id)
                                 for t in TYPY_STANOWISK}})
    return wynik
