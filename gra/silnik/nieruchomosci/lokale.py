"""Lokale i działki na mapie miasta (dane: `dane/mapa/lokale.yaml`).

Pula lokali jest wspólna: lokal zajęty przez drużynę znika z oferty innych. Decyzja rundy:

    "lokal": {"id": "centrum_3", "forma": "najem" | "kupno", "oferta": kwota}

`oferta` (od rundy `licytacje_od_rundy`) – proponowany czynsz miesięczny albo cena, nie niższa od wywoławczej;
bez niej – cena wywoławcza.

- gotowy – działa od razu, ze sprzętem z zestawu (przy najmie sprzęt wynajmującego – nie do sprzedania);
- niewyposazony – jednorazowa adaptacja (koszt KPiR), działa od następnej rundy, sprzęt trzeba kupić;
- dzialka – tylko kupno, budowa `budowa_rund` rund (raty co rundę), potem lokal bez sprzętu.

Najem: kaucja (`kaucja_miesiecy` × czynsz) i co rundę czynsz (KPiR). Każdy działający lokal: co rundę media
(utrzymanie, KPiR). Kupno, kaucja i budowa to ruchy na rachunku (bez KPiR). Nowy lokal można wziąć, gdy
od wzięcia każdego poprzedniego minęło `nowy_lokal_co_rund` rund. Stanowiska stoją w działających lokalach
i jest ich najwyżej tyle, ile lokal ma miejsc (`miejsca`). Kilka drużyn chcących ten sam lokal w jednej
rundzie: licytacja – wygrywa najwyższa oferta, remis rozstrzyga losowanie (silnik/nieruchomosci/przejecia.py).
"""
from __future__ import annotations

from ..dane import TYPY_STANOWISK, Dane
from ..ksiegowosc.finanse import Ksiega, Rachunek, ksieguj
from ..ksiegowosc.srodki_trwale import przyjmij
from ..model import Firma, Lokal, Stanowisko

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


# lokal „co 3 rundy” (P8): zamiast suchego limitu – właściciel musi odpocząć po ostatniej przeprowadzce
ODPOCZYNEK = (
    "Właściciel musi odpocząć po ostatniej przeprowadzce – wciąż śni mu się umowa najmu w trzech egzemplarzach.",
    "Właściciel leży na kanapie z mrożonym kebabem na czole i mówi, że jeszcze jeden lokal w tym tygodniu "
    "i sam zacznie się obracać na rożnie.",
    "Lekarz rodzinny zalecił właścicielowi „trzy tygodnie bez notariuszy”. Recepta wisi na lodówce, magnesem w kształcie falafela.",
    "Rodzina schowała właścicielowi długopis, pieczątkę i telefon do agenta nieruchomości. Najpierw ma się odstresować.",
    "Właściciel zapisał się na jogę dla przedsiębiorców. Instruktor twierdzi, że pozycja „podpisuję kolejną umowę” "
    "to najczęstsza przyczyna kontuzji kręgosłupa.",
)


def komunikat_odpoczynku(dane: Dane, firma: Firma, runda: int) -> str:
    """Dlaczego jeszcze nie można wziąć kolejnego lokalu – z żartem (tekst zależy od rundy, żeby się nie nudził)."""
    return (f"{ODPOCZYNEK[runda % len(ODPOCZYNEK)]} Kolejny lokal można wziąć co "
            f"{dane.mapa['zasady']['nowy_lokal_co_rund']} rundy – najwcześniej w rundzie {runda_nowego_lokalu(dane, firma)}.")


def dziala_od(dane: Dane, lok: dict, runda: int) -> int:
    if lok["typ"] == "dzialka":
        return runda + lok["budowa_rund"]
    if lok["typ"] == "niewyposazony":
        return runda + dane.mapa["zasady"]["urzadzanie_rund"]
    return runda


def koszt_wejscia(dane: Dane, lok: dict, forma: str, kwota: float | None = None) -> float:
    """Jednorazowy koszt wzięcia lokalu w rundzie decyzji: kaucja albo cena, plus adaptacja. `kwota` – oferta
    (czynsz albo cena) zamiast wywoławczej."""
    if forma == "kupno":
        return (kwota or lok["cena"]) + lok.get("adaptacja", 0)
    return dane.mapa["zasady"]["kaucja_miesiecy"] * (kwota or lok["czynsz"]) + lok.get("adaptacja", 0)


def oferta(dane: Dane, decyzja: dict, lok: dict, forma: str, runda: int) -> tuple[float | None, str | None]:
    """Kwota oferty (czynsz miesięczny przy najmie, cena przy kupnie) i powód odrzucenia. Bez oferty i przed
    rundą licytacji – cena wywoławcza."""
    z = dane.mapa["zasady"]
    wywolawcza = lok.get("czynsz") if forma == "najem" else lok.get("cena")
    if decyzja.get("oferta") in (None, "") or runda < z["licytacje_od_rundy"]:
        return wywolawcza, None
    try:
        kwota = round(float(decyzja["oferta"]), 2)
    except (TypeError, ValueError):
        return None, "Oferta w licytacji musi być kwotą."
    if kwota < wywolawcza:
        return None, f"Oferta {kwota:,.0f} zł jest niższa od ceny wywoławczej {wywolawcza:,.0f} zł.".replace(",", " ")
    if kwota > z["oferta_max"] * wywolawcza:
        return None, (f"Oferta ponad {z['oferta_max']:g} × cena wywoławcza – sprzedawca podejrzewa literówkę "
                      "i dzwoni na policję.")
    return kwota, None


def powod_odrzucenia(dane: Dane, firma: Firma, decyzja: dict, runda: int, zajete_lokale: dict[str, str],
                     finansowanie: float = 0.0) -> str | None:
    """Dlaczego lokalu nie można wziąć (None – można). finansowanie – kredyt tej rundy pod zastaw tego lokalu
    (silnik/pieniadze/banki.py: finansowanie_lokalu)."""
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
        return komunikat_odpoczynku(dane, firma, runda)
    if forma == "najem" and lok.get("czynsz") is None:
        return f"{lok['nazwa']} jest tylko na sprzedaż."
    if forma == "kupno" and lok.get("cena") is None:
        return f"{lok['nazwa']} jest tylko do wynajęcia."
    kwota, blad = oferta(dane, decyzja, lok, forma, runda)
    if blad:
        return blad
    if forma == "kupno" and firma.gotowka + finansowanie < koszt_wejscia(dane, lok, forma, kwota):
        return f"Za mało gotówki na zakup: potrzeba {koszt_wejscia(dane, lok, forma, kwota):,.0f} zł.".replace(",", " ")
    return None


def wybierz(dane: Dane, firma: Firma, decyzja: dict | None, runda: int, zajete_lokale: dict[str, str],
            ksiega: Ksiega, rachunek: Rachunek, przegrana: str | None = None, finansowanie: float = 0.0) -> dict:
    """Decyzja o nowym lokalu. Zwraca {"id", "forma", "oferta", "przyjety", "powod", "dziala_od"} (pusty – brak
    decyzji). `przegrana` – powód przegranej licytacji (silnik/nieruchomosci/przejecia.py)."""
    if not decyzja or not decyzja.get("id"):
        return {}
    info = {"id": decyzja["id"], "forma": decyzja.get("forma")}
    powod = przegrana or powod_odrzucenia(dane, firma, decyzja, runda, zajete_lokale, finansowanie)   # przegrana – z wyjaśnieniem
    if powod:
        return {**info, "przyjety": False, "powod": powod}
    lok, forma = dane.lokale[decyzja["id"]], decyzja["forma"]
    kwota = oferta(dane, decyzja, lok, forma, runda)[0]
    info["oferta"] = kwota
    nowy = Lokal(id=lok["id"], forma=forma, od_rundy=runda, dziala_od=dziala_od(dane, lok, runda))
    if forma == "najem":
        nowy.czynsz = kwota
        nowy.kaucja = dane.mapa["zasady"]["kaucja_miesiecy"] * kwota
        rachunek.zapisz(firma, f"Kaucja za lokal: {lok['adres']}", -nowy.kaucja, "kaucje")
    else:
        nowy.cena = kwota
        rachunek.zapisz(firma, f"Zakup {'działki' if lok['typ'] == 'dzialka' else 'lokalu'}: {lok['adres']}", -nowy.cena, "inwestycje")
        przyjmij(dane, firma, f"{'Działka' if lok['typ'] == 'dzialka' else 'Lokal'}: {lok['adres']}",
                 "grunt" if lok["typ"] == "dzialka" else "lokal", nowy.cena, runda)
    if lok.get("adaptacja"):
        ksieguj(firma, ksiega, rachunek, f"Adaptacja lokalu: {lok['adres']}", lok["adaptacja"])
        if forma == "najem":   # nakład najemcy – rozliczenie ulepszeń po wypowiedzeniu (silnik/nieruchomosci/przejecia.py)
            nowy.naklady = lok["adaptacja"]
    firma.lokale.append(nowy)
    zajete_lokale[lok["id"]] = firma.nazwa
    if lok["typ"] == "gotowy":
        for st in dane.mapa["zestawy"][lok["zestaw"]]["stanowiska"]:
            if forma == "kupno":  # kupiony sprzęt jest firmy – liczy się do majątku (rozwój firmy), jak kupiony osobno
                firma.majatek += sum(dane.sprzet[n]["ceny"][str(q)] for n, q in st["sprzet"].items())
            firma.stanowiska.append(Stanowisko(
                nr=firma.nowy_nr(st["typ"]), typ=st["typ"], od_rundy=runda, lokal=lok["id"],
                sprzet=dict(st["sprzet"]), sprzet_wynajmujacego=list(st["sprzet"]) if forma == "najem" else []))
    return {**info, "przyjety": True, "powod": None, "dziala_od": nowy.dziala_od}


def mozna_wyposazac(lok: Lokal, runda: int) -> bool:
    """Lokal działa albo to ostatnia runda budowy / urządzania: można kupić stanowiska i sprzęt i zatrudnić ludzi,
    a lokal rusza od razu gotowy do sprzedaży (stanowiska nie sprzedają, dopóki lokal nie działa – popyt.py)."""
    return lok.dziala_od <= runda + 1


def wolne_miejsca(dane: Dane, firma: Firma, runda: int) -> dict[str, list[str]]:
    """Wolne miejsca na nowe stanowiska w lokalach, które można wyposażać (mozna_wyposazac): typ → lista id lokali
    (id powtórzone tyle razy, ile miejsc), w kolejności wzięcia lokali."""
    wynik: dict[str, list[str]] = {t: [] for t in TYPY_STANOWISK}
    for lok in firma.lokale:
        if not mozna_wyposazac(lok, runda):
            continue
        for typ in TYPY_STANOWISK:
            zajetych = sum(1 for s in firma.stanowiska_typu(typ) if s.lokal == lok.id)
            wynik[typ] += [lok.id] * max(0, dane.lokale[lok.id]["miejsca"][typ] - zajetych)
    return wynik


def koszty_rundy(dane: Dane, firma: Firma, runda: int, ksiega: Ksiega, rachunek: Rachunek,
                 firmy: dict[str, Firma] | None = None) -> None:
    """Czynsz najmu, media działających lokali i raty budowy (w miejsce stałego kosztu utrzymania lokalu);
    właściciel budynku z najemcą (silnik/nieruchomosci/przejecia.py) dostaje czynsz najemcy."""
    for b in firma.budynki:
        najem = next(x for x in firmy[b.najemca].lokale if x.id == b.id)
        ksieguj(firma, ksiega, rachunek, f"Czynsz najmu od najemcy: {dane.lokale[b.id]['adres']}",
                dane.na_runde(najem.czynsz), "przychod_pozostaly")
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
                            -d["koszt_budowy"] / d["budowa_rund"], "inwestycje")
            if etap == d["budowa_rund"]:   # budynek gotowy – środek trwały (koszt budowy)
                przyjmij(dane, firma, f"Budynek: {d['adres']}", "budynek", d["koszt_budowy"], runda)


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
            jak = ("kup stanowiska kuchni i kasy (Inwestycje), sprzęt na stanowiska i zatrudnij pracowników (Kadry), "
                   f"a od rundy {lok.dziala_od} lokal od razu sprzedaje.")
            kiedy = ("Już w tej rundzie możesz go wyposażyć: " + jak) if mozna_wyposazac(lok, runda) \
                else f"W rundzie {lok.dziala_od - 1} będzie można go wyposażyć: " + jak
            dodaj("niebieski", "lokale", f"{co}: {d['nazwa']} – lokal zacznie działać w rundzie {lok.dziala_od}. {kiedy}")


def stan_lokali(dane: Dane, firma: Firma, runda: int) -> list[dict]:
    """Lokale firmy do wyników: dane z mapy + forma, status, zajęte miejsca."""
    wynik = []
    for lok in firma.lokale:
        d = dane.lokale[lok.id]
        wynik.append({"id": lok.id, "nazwa": d["nazwa"], "adres": d["adres"], "strefa": d["strefa"], "typ": d["typ"],
                      "forma": lok.forma, "od_rundy": lok.od_rundy, "dziala_od": lok.dziala_od,
                      "dziala": lok.dziala_od <= runda, "wyposazanie": mozna_wyposazac(lok, runda), "czynsz": lok.czynsz, "utrzymanie": d["utrzymanie"],
                      "wlasciciel": lok.wlasciciel, "najem_do": lok.najem_do,
                      "miejsca": d["miejsca"],
                      "zajete": {t: sum(1 for s in firma.stanowiska_typu(t) if s.lokal == lok.id)
                                 for t in TYPY_STANOWISK}})
    return wynik
