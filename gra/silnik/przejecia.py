"""Licytacje lokali, przejęcia budynków z najemcą i wypowiedzenia najmu (gra z lokalami; zasady: `zasady`
w dane/mapa/lokale.yaml).

Decyzje rundy:

    "lokal":     {"id", "forma", "oferta"}       – licytacja, gdy ten sam lokal chce kilka drużyn (silnik/lokale.py)
    "przejecie": {"id", "oferta"}                – kupno budynku, który wynajmuje drużyna (od `przejecia_od_rundy`)
    "wypowiedz": [{"id", "ulepszenia": "zatrzymaj" | "przywroc"}]   – właściciel wypowiada najem

Licytacja: o ten sam lokal (albo budynek) w jednej rundzie walczy kilka drużyn – wygrywa najwyższa oferta
względem ceny wywoławczej (czynszu przy najmie, ceny przy kupnie), remis rozstrzyga losowanie. Przed rundą
`licytacje_od_rundy` oferty są równe cenie wywoławczej, więc każdy spór kończy się losowaniem.

Przejęcie: kupujący wchodzi w umowę najmu (KC art. 678) – najemca płaci ten sam czynsz, ale nowemu
właścicielowi (jego przychód z VAT). Najemca kupujący swój lokal – wykup: najem zamienia się we własność, kaucja
wraca, sprzęt wynajmującego staje się sprzętem firmy. Cena budynku – ruch na rachunku i środek trwały (jak kupno).

Wypowiedzenie: najem trwa jeszcze `wypowiedzenie_rund` rund, licząc rundę wypowiedzenia (KC art. 673). Na
początku następnej rundy najemca się wyprowadza: kaucja wraca, jego sprzęt w lokalu jest sprzedany (jak
w zakładce Sprzęt), pracownicy przechodzą na wolne stanowiska w innych lokalach (reszta – zwolnienie z odprawą),
a nakłady najemcy (adaptacja, stanowiska) są rozliczone (KC art. 676) wg wyboru właściciela: „zatrzymaj” –
płaci najemcy `ulepszenia_zwrot` × nakłady i zostają mu stanowiska najemcy; „przywroc” – najemca płaci
`przywrocenie_koszt` × nakłady za przywrócenie stanu pierwotnego. Budynek staje się lokalem właściciela
(własność, działa od razu) ze sprzętem wynajmującego.
"""
from __future__ import annotations

from . import srodki_trwale as st_trwale
from .dane import Dane
from .decyzje import cena_sprzedazy_sprzetu
from .finanse import Ksiega, Rachunek, ksieguj
from .lokale import oferta, powod_odrzucenia
from .losowosc import strumien
from .model import Firma, KupionyBudynek, Lokal, StanGry, Stanowisko
from .rynek_pracy import jako_kandydat

ZAKLADKA = "przejecia"
ULEPSZENIA = ("zatrzymaj", "przywroc")


def zasady(dane: Dane) -> dict:
    return dane.mapa["zasady"]


def nazwa_firmy(firmy: dict[str, Firma], nazwa: str) -> str:
    f = firmy.get(nazwa)
    return (f.nazwa_wyswietlana or nazwa) if f else nazwa


def najem(firmy: dict[str, Firma], lokal_id: str) -> tuple[str, Lokal] | None:
    """Kto wynajmuje lokal: (firma, jej lokal) – None, gdy nikt."""
    return next(((n, x) for n, f in firmy.items() for x in f.lokale if x.id == lokal_id and x.forma == "najem"), None)


# --- przejęcie budynku ------------------------------------------------------------------------------------------
def powod_przejecia(dane: Dane, firmy: dict[str, Firma], nazwa: str, decyzja: dict, runda: int) -> str | None:
    """Dlaczego budynku nie można kupić (None – można)."""
    z, lok = zasady(dane), dane.lokale.get(decyzja.get("id"))
    if runda < z["przejecia_od_rundy"]:
        return f"Budynki z najemcą można kupować od rundy {z['przejecia_od_rundy']}."
    if lok is None:
        return "Nie ma takiego budynku."
    if lok.get("cena") is None:
        return f"{lok['nazwa']}: właściciel nie chce sprzedać budynku – lokal jest tylko do wynajęcia."
    wynajety = najem(firmy, lok["id"])
    if wynajety is None:
        return f"{lok['nazwa']} nie ma najemcy – kup go w zakładce Lokale."
    if wynajety[1].wlasciciel:
        return f"{lok['nazwa']} kupiła już firma {nazwa_firmy(firmy, wynajety[1].wlasciciel)}."
    kwota, blad = oferta(dane, decyzja, lok, "kupno", runda)
    if blad:
        return blad
    if firmy[nazwa].gotowka < kwota:
        return f"Za mało gotówki na zakup budynku: potrzeba {kwota:,.0f} zł.".replace(",", " ")
    return None


def przejmij(dane: Dane, firmy: dict[str, Firma], nazwa: str, decyzja: dict | None, runda: int, przegrana: str | None,
             ksiega: Ksiega, rachunek: Rachunek) -> dict:
    """Kupno budynku z najemcą. Zwraca {"id", "przyjety", "powod", "kwota", "najemca", "wykup"} (pusty – brak decyzji)."""
    if not decyzja or not decyzja.get("id"):
        return {}
    info = {"id": decyzja["id"]}
    powod = powod_przejecia(dane, firmy, nazwa, decyzja, runda) or przegrana
    if powod:
        return {**info, "przyjety": False, "powod": powod}
    f, lok = firmy[nazwa], dane.lokale[decyzja["id"]]
    kwota = oferta(dane, decyzja, lok, "kupno", runda)[0]
    najemca, umowa = najem(firmy, lok["id"])
    rachunek.zapisz(f, f"Zakup budynku z najemcą: {lok['adres']}", -kwota, "inwestycje")
    st_trwale.przyjmij(dane, f, f"Lokal: {lok['adres']}", "lokal", kwota, runda)
    if najemca == nazwa:   # wykup: najem zamienia się we własność
        rachunek.zapisz(f, f"Zwrot kaucji za lokal: {lok['adres']}", umowa.kaucja, "kaucje")
        umowa.forma, umowa.cena, umowa.czynsz, umowa.kaucja, umowa.naklady = "kupno", kwota, 0, 0, 0
        for st in f.stanowiska:
            if st.lokal == lok["id"] and st.sprzet_wynajmujacego:
                f.majatek += sum(dane.sprzet[n]["ceny"][str(st.sprzet[n])] for n in st.sprzet_wynajmujacego if n in st.sprzet)
                st.sprzet_wynajmujacego = []
        return {**info, "przyjety": True, "powod": None, "kwota": kwota, "najemca": najemca, "wykup": True}
    umowa.wlasciciel = nazwa
    f.budynki.append(KupionyBudynek(id=lok["id"], od_rundy=runda, cena_gr=0, najemca=najemca))
    f.budynki[-1].cena = kwota
    return {**info, "przyjety": True, "powod": None, "kwota": kwota, "najemca": najemca, "wykup": False}


def wypowiedz(dane: Dane, firmy: dict[str, Firma], nazwa: str, lista: list | None, runda: int) -> list[dict]:
    """Wypowiedzenia najmu przez właściciela. Zwraca [{"id", "przyjete", "powod", "najem_do", "ulepszenia"}]."""
    wynik = []
    for w in lista or []:
        lok_id = w.get("id") if isinstance(w, dict) else w
        b = next((x for x in firmy[nazwa].budynki if x.id == lok_id), None)
        info = {"id": lok_id}
        if b is None:
            wynik.append({**info, "przyjete": False, "powod": "To nie twój budynek – wypowiedzieć najem może tylko właściciel."})
            continue
        umowa = next(x for x in firmy[b.najemca].lokale if x.id == lok_id)
        if umowa.najem_do is not None:
            wynik.append({**info, "przyjete": False, "powod": f"Najem już wypowiedziany – do rundy {umowa.najem_do}."})
            continue
        ulepszenia = w.get("ulepszenia") if isinstance(w, dict) else None
        umowa.najem_do = runda + zasady(dane)["wypowiedzenie_rund"] - 1
        umowa.ulepszenia = ulepszenia if ulepszenia in ULEPSZENIA else ULEPSZENIA[0]
        wynik.append({**info, "przyjete": True, "powod": None, "najemca": b.najemca, "najem_do": umowa.najem_do,
                      "ulepszenia": umowa.ulepszenia})
    return wynik


# --- licytacje ---------------------------------------------------------------------------------------------------
def licytacje(dane: Dane, firmy: dict[str, Firma], decyzje: dict, runda: int, ziarno: int,
              zajete_lokale: dict[str, str]) -> dict:
    """Spory o lokale i budynki przed decyzjami. Zwraca {"przegrane": {(firma, "lokal" | "przejecie"): powód},
    "przetargi": [{"id", "rodzaj", "oferty": [{"firma", "forma", "kwota", "wywolawcza", "stosunek"}], "zwyciezca",
    "remis"}]} – przetargi tylko z co najmniej dwiema ważnymi ofertami."""
    zgloszenia: dict[tuple[str, str], list[dict]] = {}
    for nazwa in sorted(firmy):
        d = decyzje.get(nazwa, {})
        dl = d.get("lokal")
        if dl and dl.get("id") and not powod_odrzucenia(dane, firmy[nazwa], dl, runda, zajete_lokale):
            lok = dane.lokale[dl["id"]]
            wyw = lok["czynsz"] if dl["forma"] == "najem" else lok["cena"]
            zgloszenia.setdefault(("lokal", lok["id"]), []).append(
                {"firma": nazwa, "forma": dl["forma"], "kwota": oferta(dane, dl, lok, dl["forma"], runda)[0], "wywolawcza": wyw})
        dp = d.get("przejecie")
        if dp and dp.get("id") and not powod_przejecia(dane, firmy, nazwa, dp, runda):
            lok = dane.lokale[dp["id"]]
            zgloszenia.setdefault(("przejecie", lok["id"]), []).append(
                {"firma": nazwa, "forma": "kupno", "kwota": oferta(dane, dp, lok, "kupno", runda)[0], "wywolawcza": lok["cena"]})
    przegrane, przetargi = {}, []
    for (rodzaj, lok_id), oferty in sorted(zgloszenia.items()):
        if len(oferty) < 2:
            continue
        for o in oferty:
            o["stosunek"] = round(o["kwota"] / o["wywolawcza"], 4)
        najwyzsza = max(o["stosunek"] for o in oferty)
        remis = [o for o in oferty if o["stosunek"] == najwyzsza]
        zwyciezca = remis[int(strumien(ziarno, runda, "licytacje", rodzaj, lok_id).integers(len(remis)))]["firma"] \
            if len(remis) > 1 else remis[0]["firma"]
        lok = dane.lokale[lok_id]
        for o in oferty:
            if o["firma"] != zwyciezca:
                przegrane[(o["firma"], rodzaj)] = (
                    f"{lok['nazwa']}: licytację wygrała firma {nazwa_firmy(firmy, zwyciezca)} – "
                    + ("remis, zdecydowało losowanie (notariusz rzucał monetą trzy razy, bo za pierwszym razem upadła na kant)."
                       if len(remis) > 1 and o in remis else "jej oferta była wyższa."))
        przetargi.append({"id": lok_id, "rodzaj": rodzaj, "zwyciezca": zwyciezca, "remis": len(remis) > 1,
                          "oferty": sorted(oferty, key=lambda o: (-o["stosunek"], o["firma"]))})
    return {"przegrane": przegrane, "przetargi": przetargi}


# --- koniec najmu ------------------------------------------------------------------------------------------------
def koniec_najmu(dane: Dane, s: StanGry, runda: int, ksiegi: dict[str, Ksiega], rachunki: dict[str, Rachunek]) -> dict:
    """Wyprowadzki po wypowiedzeniu (początek rundy po ostatniej rundzie najmu). Zwraca {firma: [opis wyprowadzki]}
    – dla najemcy i właściciela."""
    z, wynik = zasady(dane), {}
    for nazwa in sorted(s.firmy):
        najemca = s.firmy[nazwa]
        for umowa in [x for x in najemca.lokale if x.najem_do is not None and runda > x.najem_do]:
            wynik.setdefault(nazwa, []).append(
                _wyprowadzka(dane, s, nazwa, umowa, runda, z, ksiegi, rachunki))
            wynik.setdefault(umowa.wlasciciel, []).append(wynik[nazwa][-1])
    return wynik


def _wyprowadzka(dane: Dane, s: StanGry, nazwa: str, umowa: Lokal, runda: int, z: dict,
                 ksiegi: dict[str, Ksiega], rachunki: dict[str, Rachunek]) -> dict:
    najemca, wl = s.firmy[nazwa], umowa.wlasciciel
    wlasciciel = s.firmy[wl]
    lok = dane.lokale[umowa.id]
    adres = lok["adres"]
    ks_n, rach_n, ks_w, rach_w = ksiegi[nazwa], rachunki[nazwa], ksiegi[wl], rachunki[wl]
    stanowiska = [st for st in najemca.stanowiska if st.lokal == umowa.id]
    info = {"id": umowa.id, "najemca": nazwa, "wlasciciel": wl, "ulepszenia": umowa.ulepszenia,
            "naklady": umowa.naklady, "rozliczenie": 0.0, "kaucja": umowa.kaucja, "sprzedany_sprzet": 0.0,
            "przeniesieni": [], "zwolnieni": [], "stanowiska_wlasciciela": 0}
    # sprzęt najemcy w lokalu – sprzedany jak w zakładce Sprzęt
    for st in stanowiska:
        for n, q in list(st.sprzet.items()):
            if n in st.sprzet_wynajmujacego:
                continue
            st.sprzet.pop(n)
            cena = dane.sprzet[n]["ceny"][str(q)]
            st_trwale.sprzedaj(najemca, f"{n} ({st.typ} {st.nr})", ks_n)
            ksieguj(najemca, ks_n, rach_n, f"Sprzedaż sprzętu: {n}", cena_sprzedazy_sprzetu(dane, cena), "przychod_pozostaly")
            najemca.majatek -= cena
            info["sprzedany_sprzet"] += cena_sprzedazy_sprzetu(dane, cena)
    # nakłady najemcy (KC art. 676)
    if umowa.naklady > 0 and umowa.ulepszenia == "zatrzymaj":
        kwota = round(umowa.naklady * z["ulepszenia_zwrot"], 2)
        st_trwale.zakup(dane, wlasciciel, ks_w, rach_w, f"Rozliczenie ulepszeń lokalu: {adres}", f"Ulepszenia: {adres}",
                        "lokal", kwota, runda)
        ksieguj(najemca, ks_n, rach_n, f"Rozliczenie ulepszeń lokalu: {adres}", kwota, "przychod_pozostaly")
        info["rozliczenie"] = kwota
    elif umowa.naklady > 0:
        kwota = round(umowa.naklady * z["przywrocenie_koszt"], 2)
        ksieguj(najemca, ks_n, rach_n, f"Przywrócenie lokalu do stanu pierwotnego: {adres}", kwota)
        info["rozliczenie"] = -kwota
    if umowa.kaucja:
        rach_n.zapisz(najemca, f"Zwrot kaucji za lokal: {adres}", umowa.kaucja, "kaucje")
    # stanowiska zostające w budynku: ze sprzętem wynajmującego, a przy zatrzymaniu ulepszeń – wszystkie
    for st in stanowiska:
        if not st.sprzet_wynajmujacego and umowa.ulepszenia != "zatrzymaj":
            continue
        sprzet = {n: q for n, q in st.sprzet.items() if n in st.sprzet_wynajmujacego}
        wlasciciel.majatek += sum(dane.sprzet[n]["ceny"][str(q)] for n, q in sprzet.items())
        wlasciciel.stanowiska.append(Stanowisko(nr=wlasciciel.nowy_nr(st.typ), typ=st.typ, od_rundy=runda,
                                                lokal=umowa.id, sprzet=sprzet))
        info["stanowiska_wlasciciela"] += 1
    # pracownicy najemcy: na wolne stanowiska w jego innych działających lokalach, reszta zwolniona z odprawą
    najemca.stanowiska = [st for st in najemca.stanowiska if st.lokal != umowa.id]
    najemca.lokale.remove(umowa)
    dzialajace = {x.id for x in najemca.lokale if x.dziala_od <= runda}
    for st in stanowiska:
        p = najemca.pracownicy.get(st.pracownik) if st.pracownik else None
        if p is None:
            continue
        wolne = next((x for x in najemca.stanowiska if x.typ == st.typ and x.pracownik is None and x.lokal in dzialajace), None)
        if wolne:
            wolne.pracownik, p.stanowisko = p.id, wolne.nr
            info["przeniesieni"].append(p.imie_nazwisko)
        else:
            del najemca.pracownicy[p.id]
            ksieguj(najemca, ks_n, rach_n, f"Koszt zwolnienia {p.imie_nazwisko}", p.koszt_odprawy)
            s.kandydaci.append(jako_kandydat(p))
            info["zwolnieni"].append(p.imie_nazwisko)
    # budynek – lokal właściciela
    b = next(x for x in wlasciciel.budynki if x.id == umowa.id)
    wlasciciel.budynki.remove(b)
    wlasciciel.lokale.append(Lokal(id=umowa.id, forma="kupno", od_rundy=b.od_rundy, dziala_od=runda, cena_gr=b.cena_gr))
    return info


# --- lista błędów, wyniki, widok ------------------------------------------------------------------------------------
def bledy(dane: Dane, firmy: dict[str, Firma], nazwa: str, runda: int, info: dict) -> list[dict]:
    """Uwagi do listy błędów (zakładka „przejecia”): odrzucone decyzje, wypowiedzenia, nowy właściciel."""
    wynik = []

    def dodaj(poziom: str, tekst: str) -> None:
        wynik.append({"poziom": poziom, "zakladka": ZAKLADKA, "tekst": tekst})

    p = info.get("przejecie") or {}
    if p and not p["przyjety"]:
        dodaj("czerwony", f"Budynek nie został kupiony: {p['powod']}")
    for w in info.get("wypowiedzenia", []):
        if not w["przyjete"]:
            dodaj("czerwony", f"Wypowiedzenie nieprzyjęte: {w['powod']}")
    for lok in firmy[nazwa].lokale:
        if lok.wlasciciel and lok.najem_do is not None:
            dodaj("czerwony", f"{dane.lokale[lok.id]['nazwa']}: firma {nazwa_firmy(firmy, lok.wlasciciel)} wypowiedziała "
                              f"najem – ostatnia runda w lokalu: {lok.najem_do}. Poszukaj nowego lokalu, zanim kucharze "
                              "zaczną gotować na klatce schodowej.")
        elif lok.wlasciciel and lok.wlasciciel != nazwa:
            dodaj("niebieski", f"{dane.lokale[lok.id]['nazwa']}: właścicielem budynku jest firma "
                               f"{nazwa_firmy(firmy, lok.wlasciciel)} – czynsz płacisz teraz jej.")
    return wynik


def raport(dane: Dane, firmy: dict[str, Firma], nazwa: str, runda: int, info: dict, przetargi: list[dict],
           wyprowadzki: list[dict]) -> dict:
    """Wyniki rundy (zakładka Licytacje i przejęcia)."""
    return {"przejecie": info.get("przejecie") or {}, "wypowiedzenia": info.get("wypowiedzenia", []),
            "licytacje": [p for p in przetargi if any(o["firma"] == nazwa for o in p["oferty"])],
            "wyprowadzki": wyprowadzki, **stan(dane, firmy, nazwa)}


def stan(dane: Dane, firmy: dict[str, Firma], nazwa: str) -> dict:
    """Budynki firmy z najemcami i jej najmy u innych drużyn."""
    f = firmy[nazwa]
    budynki = []
    for b in f.budynki:
        umowa = next(x for x in firmy[b.najemca].lokale if x.id == b.id)
        budynki.append({"id": b.id, "nazwa": dane.lokale[b.id]["nazwa"], "adres": dane.lokale[b.id]["adres"],
                        "najemca": b.najemca, "od_rundy": b.od_rundy, "cena": b.cena, "czynsz": umowa.czynsz,
                        "najem_do": umowa.najem_do, "ulepszenia": umowa.ulepszenia, "naklady": umowa.naklady})
    najmy = [{"id": x.id, "nazwa": dane.lokale[x.id]["nazwa"], "wlasciciel": x.wlasciciel, "czynsz": x.czynsz,
              "najem_do": x.najem_do, "naklady": x.naklady} for x in f.lokale if x.wlasciciel]
    return {"budynki": budynki, "najmy": najmy}


def publiczne(dane: Dane, firmy: dict[str, Firma], przetargi: list[dict]) -> dict:
    """Do rynku rundy: rozstrzygnięte licytacje i właściciele budynków z najemcami."""
    return {"przetargi": przetargi,
            "wlasciciele": {x.id: x.wlasciciel for f in firmy.values() for x in f.lokale if x.wlasciciel}}


def widok(dane: Dane, firmy: dict[str, Firma], nazwa: str, runda: int, decyzja: dict | None, wyniki: dict | None) -> dict:
    """Zakładka Licytacje i przejęcia: budynki do kupienia (wynajmowane przez drużyny), własne budynki i najmy."""
    z = zasady(dane)
    do_kupienia = []
    for lok in dane.mapa["lokale"]:
        wynajety = najem(firmy, lok["id"])
        if lok.get("cena") is None or wynajety is None or wynajety[1].wlasciciel:
            continue
        do_kupienia.append({"id": lok["id"], "nazwa": lok["nazwa"], "adres": lok["adres"], "strefa": lok["strefa"],
                            "cena": lok["cena"], "czynsz": wynajety[1].czynsz, "najemca": wynajety[0],
                            "wykup": wynajety[0] == nazwa})
    return {"od_rundy": z["przejecia_od_rundy"], "licytacje_od_rundy": z["licytacje_od_rundy"],
            "oferta_max": z["oferta_max"], "wypowiedzenie_rund": z["wypowiedzenie_rund"],
            "ulepszenia_zwrot": z["ulepszenia_zwrot"], "przywrocenie_koszt": z["przywrocenie_koszt"],
            "do_kupienia": do_kupienia, **stan(dane, firmy, nazwa), "decyzja": decyzja, "wyniki": wyniki}
