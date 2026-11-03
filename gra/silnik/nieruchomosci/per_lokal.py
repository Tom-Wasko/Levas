"""Lokal jako osobna jednostka (Z2 przebudowy 2.11.2026, raporty/przebudowa_zakladek.md).

Osobno w każdym lokalu: menu i ceny, magazyn (partie z polem `lokal`, chłodnia lokalu), stanowiska z ludźmi
i sprzętem, wyposażenie i udogodnienia. Wspólne dla firmy: promocje, higiena, bank, podatki, czas właściciela,
handel, reklama; progi dostaw dostawców liczone dla całej firmy.

`Firma.oferta`, `ceny`, `wyposazenie`, `udogodnienia`, `magazyn` zostają sumą lokali (`synchronizuj`, `scal`) – reszta
silnika (wyniki, karta, limity, boty) liczy z nich jak dawniej. Pola lokalu None = stary zapis: `utrwal` przepisuje
wartości firmy (menu i ceny do każdego lokalu, wyposażenie i udogodnienia do pierwszego, partie do pierwszego).
Towar między własnymi lokalami: `przewozy` (zalozenia.yaml magazyn.przewoz) – czas właściciela i trochę pieniędzy
za kurs, partia traci dzień terminu. Pracowników nie przenosi się.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

from ..dane import Dane
from ..model import Cena, Firma, Lokal, Partia

LISTY = ("wyposazenie", "udogodnienia")
EPS = 1e-9


def lokal(firma: Firma, lok_id: str | None) -> Lokal | None:
    return next((x for x in firma.lokale if x.id == lok_id), None)


def wiele(firma: Firma) -> bool:
    return len(firma.lokale) > 1


def menu(firma: Firma, lok: Lokal) -> dict[str, int]:
    return lok.menu if lok.menu is not None else firma.oferta


def ceny(firma: Firma, lok: Lokal) -> dict[str, Cena]:
    return lok.ceny if lok.ceny is not None else firma.ceny


def lista(firma: Firma, lok: Lokal, rodzaj: str) -> list[str]:
    """Wyposażenie / udogodnienia lokalu; stary zapis – całość firmy w pierwszym lokalu."""
    wartosc = getattr(lok, rodzaj)
    if wartosc is not None:
        return wartosc
    utrwalone = any(getattr(x, rodzaj) is not None for x in firma.lokale)
    return getattr(firma, rodzaj) if firma.lokale and lok is firma.lokale[0] and not utrwalone else []


def glowny(firma: Firma, runda: int | None = None) -> Lokal | None:
    """Lokal „domyślny” (zamówienia i zakupy bez wskazanego lokalu): pierwszy działający, inaczej pierwszy."""
    if not firma.lokale:
        return None
    return next((x for x in firma.lokale if runda is None or x.dziala_od <= runda), firma.lokale[0])


def lokal_partii(firma: Firma, p: Partia) -> str | None:
    if p.lokal and lokal(firma, p.lokal):
        return p.lokal
    return firma.lokale[0].id if firma.lokale else None


def nazwa(dane: Dane, lok_id: str) -> str:
    return dane.lokale[lok_id]["nazwa"] if dane.lokale and lok_id in dane.lokale else lok_id


def utrwal(firma: Firma) -> None:
    """Uzupełnia pola lokali ze starego zapisu (wartości firmy) i przypisuje partie bez lokalu do pierwszego."""
    if not firma.lokale:
        return
    for rodzaj in LISTY:
        utrwalone = any(getattr(x, rodzaj) is not None for x in firma.lokale)
        for i, lok in enumerate(firma.lokale):
            if getattr(lok, rodzaj) is None:
                setattr(lok, rodzaj, list(getattr(firma, rodzaj)) if i == 0 and not utrwalone else [])
    nowy = any(x.menu is not None for x in firma.lokale)   # lokal dokupiony do już podzielonej firmy
    for lok in firma.lokale:
        if lok.menu is None:   # nowy lokal: dania firmy bez prognozy (prognozę podaje gracz w lokalu)
            lok.menu = {u: 0 for u in firma.oferta} if nowy else dict(firma.oferta)
        if lok.ceny is None:
            lok.ceny = {u: c.model_copy() for u, c in firma.ceny.items()}
    for p in firma.partie:
        p.lokal = lokal_partii(firma, p)


def synchronizuj(firma: Firma) -> None:
    """Pola firmy = suma lokali: oferta (prognozy zsumowane), ceny (pierwszy lokal z daniem w menu), wyposażenie
    i udogodnienia (wszystkie sztuki)."""
    if not firma.lokale:
        return
    oferta: dict[str, int] = {}
    cn: dict[str, Cena] = {}
    for lok in firma.lokale:
        m, c = menu(firma, lok), ceny(firma, lok)
        for u, p in m.items():
            oferta[u] = oferta.get(u, 0) + int(p or 0)
            if u in c and u not in cn:
                cn[u] = c[u]
    for lok in firma.lokale:   # ceny dań spoza menu (zostają do ponownego włączenia)
        for u, c in ceny(firma, lok).items():
            cn.setdefault(u, c)
    listy = {r: [n for lok in firma.lokale for n in lista(firma, lok, r)] for r in LISTY}
    firma.oferta, firma.ceny = oferta, cn
    for rodzaj, wartosc in listy.items():
        setattr(firma, rodzaj, wartosc)


def widok(firma: Firma, lok_id: str) -> Firma:
    """Firma widziana z jednego lokalu: jego stanowiska, partie (te same obiekty), magazyn z tych partii, menu, ceny,
    wyposażenie i udogodnienia. Pracownicy wspólni. Zmiany listy partii (nowe, zużyte) – `scal`."""
    from ..kuchnia import swiezosc as sw  # swiezosc korzysta z tego modułu
    lok = lokal(firma, lok_id)
    zmiany: dict = {"stanowiska": [s for s in firma.stanowiska if s.lokal == lok_id],
                    "partie": [p for p in firma.partie if lokal_partii(firma, p) == lok_id],
                    "magazyn": {}, "wartosc_magazynu_gr": {}}
    if lok is not None:
        zmiany.update(lokale=[lok], oferta=dict(menu(firma, lok)), ceny=dict(ceny(firma, lok)),
                      **{r: list(lista(firma, lok, r)) for r in LISTY})
    v = firma.model_copy(update=zmiany)
    if firma.partie:
        sw.uzgodnij(v)
    else:   # bez partii (stary zapis, testy): magazyn wspólny z firmą – zużycie idzie do firmy
        v.magazyn, v.wartosc_magazynu_gr = firma.magazyn, firma.wartosc_magazynu_gr
    return v


def widoki(firma: Firma, runda: int | None = None) -> dict[str, Firma]:
    """Widoki lokali (runda – tylko działające w tej rundzie)."""
    return {x.id: widok(firma, x.id) for x in firma.lokale if runda is None or x.dziala_od <= runda}


def scal(firma: Firma, wid: dict[str, Firma]) -> None:
    """Partie z widoków z powrotem do firmy; magazyn firmy = suma partii."""
    from ..kuchnia import swiezosc as sw
    for lok_id, v in wid.items():
        for p in v.partie:
            p.lokal = lok_id
    firma.partie[:] = [p for p in firma.partie if lokal_partii(firma, p) not in wid] \
        + [p for v in wid.values() for p in v.partie]
    sw.uzgodnij(firma)


def nazwa_srodka(firma: Firma, lok: Lokal, n: str) -> str:
    """Nazwa środka trwałego wyposażenia / udogodnienia w lokalu (pierwszy lokal – sama nazwa, jak w starych zapisach)."""
    return n if firma.lokale and lok is firma.lokale[0] else f"{n} ({lok.id})"


# --- przewozy towaru między lokalami ----------------------------------------------------------------------------
def zasady_przewozu(dane: Dane) -> dict | None:
    return (dane.z.get("magazyn") or {}).get("przewoz")


def przewozy(dane: Dane, firma: Firma, lista_: list[dict], runda: int, czas, info: dict) -> list[dict]:
    """Sprawdza przewozy z decyzji: [{"z", "do", "zasob", "jakosc", "ilosc", "dzien"}]. Kurs = para lokali i dzień;
    każdy kurs zajmuje czas właściciela i kosztuje (zalozenia magazyn.przewoz). Zwraca przyjęte przewozy; koszt kursu
    w polu "koszt" jego pierwszego przewozu; uwagi – info["uwagi_przewozow"]."""
    if not lista_:
        return []
    zas = zasady_przewozu(dane)
    uwagi = info.setdefault("uwagi_przewozow", [])
    if not zas:
        uwagi.append("Przewozy towaru między lokalami nie są dostępne w tej grze.")
        return []
    if runda < zas["od_rundy"]:
        uwagi.append(f"Przewozy towaru między lokalami – od rundy {zas['od_rundy']}.")
        return []
    dni = (dane.data_rundy(runda + 1) - dane.data_rundy(runda)).days
    kursy: dict[tuple, list[dict]] = {}
    for x in lista_:
        z, do = lokal(firma, x.get("z")), lokal(firma, x.get("do"))
        ilosc = float(x.get("ilosc") or 0)
        if z is None or do is None or z is do or ilosc <= EPS or x.get("zasob") not in dane.zasoby:
            uwagi.append("Przewóz pominięty: wskaż dwa różne własne lokale, składnik i ilość.")
            continue
        if z.dziala_od > runda or do.dziala_od > runda:
            uwagi.append(f"Przewóz {nazwa(dane, z.id)} → {nazwa(dane, do.id)}: oba lokale muszą już działać.")
            continue
        dzien = min(max(0, int(x.get("dzien") or 0)), dni - 1)
        kursy.setdefault((z.id, do.id, dzien), []).append({"z": z.id, "do": do.id, "zasob": x["zasob"],
                                                          "jakosc": int(x.get("jakosc") or 0) or None,
                                                          "ilosc": ilosc, "dzien": dzien})
    wynik = []
    for (z, do, dzien), lst in kursy.items():
        opis = f"Przewóz towaru: {nazwa(dane, z)} → {nazwa(dane, do)}"
        if not czas.wez(zas["czas_wlasciciela"], opis, "dostawcy"):
            uwagi.append(f"{opis} (dzień {dzien + 1}): brak czasu właściciela – towar zostaje na miejscu.")
            continue
        lst[0]["koszt"] = zas["koszt_kursu"]
        wynik += lst
    return wynik


def wykonaj_przewozy(dane: Dane, firma: Firma, wid: dict[str, Firma], przew: list[dict], dzien_nr: int,
                     dzien: str) -> list[dict]:
    """Rano dnia `dzien_nr`, przed dostawami: partie (FIFO – najkrótszy termin) przechodzą z widoku lokalu „z” do „do”
    jako dostawa tego dnia z terminem krótszym o skrocenie_terminu_dni (nie wcześniej niż dziś). Zwraca wykonane
    przewozy z przewiezioną ilością."""
    skr = (zasady_przewozu(dane) or {}).get("skrocenie_terminu_dni", 1)
    wykonane = []
    for x in przew:
        if x["dzien"] != dzien_nr or x["z"] not in wid or x["do"] not in wid:
            continue
        zrodlo, cel = wid[x["z"]], wid[x["do"]]
        pozostalo, przewiezione = x["ilosc"], 0.0
        for p in sorted((p for p in zrodlo.partie if p.zasob == x["zasob"] and p.ilosc > EPS and p.dostawa < dzien
                         and not p.u_dostawcy   # Z4: towar u auto-dostawcy nie jeździ między lokalami
                         and (x["jakosc"] is None or p.jakosc == x["jakosc"]) and not (p.termin and p.termin < dzien)),
                        key=lambda p: (p.termin or "9999-12-31", p.dostawa)):
            if pozostalo <= EPS:
                break
            bierz = min(p.ilosc, pozostalo)
            wart = p.wartosc_gr if p.ilosc - bierz <= EPS else round(p.wartosc_gr * bierz / p.ilosc)
            p.ilosc -= bierz
            p.wartosc_gr -= wart
            termin = p.termin
            if termin:
                termin = max(dzien, (date.fromisoformat(termin) - timedelta(days=skr)).isoformat())
            cel.partie.append(Partia(zasob=p.zasob, jakosc=p.jakosc, ilosc=bierz, wartosc_gr=wart, dostawa=dzien,
                                     termin=termin, dostawca=p.dostawca, runda=p.runda, lokal=x["do"]))
            pozostalo -= bierz
            przewiezione += bierz
        wykonane.append({**x, "przewiezione": round(przewiezione, 3)})
    return wykonane


def podziel_zamowienia(zamowienia: list[dict], udzialy: dict[str, float]) -> list[dict]:
    """Zamówienia firmy na lokale w proporcji `udzialy` (boty): ilość każdego zamówienia dzielona w górę na
    opakowania; lokale bez udziału – pominięte."""
    lok = [k for k, v in udzialy.items() if v > 0]
    suma = sum(udzialy[k] for k in lok)
    if not lok:
        return zamowienia
    if len(lok) == 1:
        return [{**z, "lokal": lok[0]} for z in zamowienia]
    wynik = []
    for z in zamowienia:
        reszta = z["ilosc"]
        for i, k in enumerate(lok):
            n = reszta if i == len(lok) - 1 else min(reszta, math.ceil(z["ilosc"] * udzialy[k] / suma - 1e-9))
            reszta -= n
            if n > 0:
                wynik.append({**z, "ilosc": n, "lokal": k})
    return wynik
