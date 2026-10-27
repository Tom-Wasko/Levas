"""Biura rachunkowe i samodzielna księgowość (gra z lokalami, F3a.13, dane/mapa/biura.yaml).

Biuro: opłata za rundę = ryczałt (z limitem dokumentów) + dokumenty ponad limit (albo za każdy dokument, nie mniej
niż minimum) + kadry za pracownika ponad `w_cenie`; koszt w KPiR (VAT 23%). Biuro rozlicza podatki od razu
(silnik/rozliczenie.py), ale może się pomylić (`ryzyko_bledu`): mandat, który biuro z OC oddaje.

Samodzielnie: na koniec rundy r silnik liczy poprawne rozliczenie, ale go nie płaci – zapisuje w `firma.deklaracja`
dokumenty rundy (z poprawną kolumną KPiR i stawką VAT) i poprawne kwoty deklaracji. W rundzie r+1 drużyna księguje
dokumenty i składa deklaracje (decyzja `ksiegowosc`); na początku przeliczenia r+1 urząd płaci zadeklarowane kwoty,
korektę (dopłata albo zwrot do poprawnych) i mandat za każdą błędną deklarację. Błędne zapisy są opisane, ale same nie
kosztują. Bez deklaracji urząd rozlicza z urzędu (poprawne kwoty + mandat); po zmianie na biuro deklarację składa
biuro (bez mandatu). Stan rozliczeń (`firma.rozliczenie`) jest zawsze poprawny – błędy kosztują tylko korektę i mandat.
"""
from __future__ import annotations

from .dane import Dane
from .finanse import KOLUMNY, Ksiega, Rachunek, do_grosza, ksieguj
from .handel import SPRZEDAZ_TOWAROW
from .losowosc import strumien
from .model import Firma

SAMODZIELNIE = "samodzielnie"
POZA = "poza"
KOREKTA = "Korekta – zwrot zasobów"
ZWROT = "Zwrot zasobów"
TOLERANCJA = 1.0      # deklaracje w pełnych złotych – różnica poniżej 1 zł to zaokrąglenie, nie błąd

NAZWY_KOLUMN = {"przychod": "7. Przychód ze sprzedaży", "przychod_pozostaly": "8. Pozostałe przychody",
                "towary": "10. Zakup towarów i materiałów", "wynagrodzenia": "12. Wynagrodzenia",
                "pozostale": "13. Pozostałe wydatki", POZA: "Poza KPiR"}
WYJASNIENIA = {
    "przychod": "sprzedaż dań (i towarów innej drużynie) to przychód ze sprzedaży (kolumna 7)",
    "przychod_pozostaly": "odsetki od lokat i sprzedaż sprzętu to pozostałe przychody (kolumna 8), nie sprzedaż dań",
    "towary": "składniki i opakowania do dań to zakup towarów i materiałów (kolumna 10) – także korekta po zwrocie",
    "wynagrodzenia": "pensje i premie pracowników to wynagrodzenia (kolumna 12); ZUS pracodawcy idzie do pozostałych",
    "pozostale": "czynsz, utrzymanie, reklama, opłaty bankowe, ZUS, dostawa i amortyzacja to pozostałe wydatki "
                 "(kolumna 13)",
    POZA: "kredyt, lokata, kaucja, zakup środka trwałego, podatki, Harpagon i mandaty nie są ani przychodem, ani "
          "kosztem podatkowym – "
          "poza KPiR (środek trwały trafia do ewidencji i kosztuje przez amortyzację)",
}
TYPY_POZA = {"podatki": "Potwierdzenie przelewu do urzędu / ZUS", "kredyty": "Umowa kredytu i wyciąg bankowy",
             "lokaty": "Wyciąg bankowy – lokata", "kaucje": "Umowa najmu – kaucja",
             "harpagon": "Kwit Harpagona (na serwetce)", "inwestycje": "Umowa kupna / akt notarialny",
             "kary": "Mandat karny (sanepid)"}
POLA = {"vat": "VAT", "pit": "zaliczka na PIT", "zdrowotna": "składka zdrowotna"}


def ustawienia(dane: Dane) -> dict:
    return dane.mapa["biura"]


def biura(dane: Dane) -> dict[str, dict]:
    return {b["id"]: b for b in ustawienia(dane)["biura"]} if dane.mapa else {}


def poprawny_wybor(dane: Dane, biuro: str) -> bool:
    return biuro == SAMODZIELNIE or biuro in biura(dane)


# --- biuro: opłata i błędy -----------------------------------------------------------------------------------

def limit_rundy(biuro: dict) -> int | None:
    n = biuro["dokumenty_w_ryczalcie"]
    return None if n is None else round(n * 12 / 52)


def oplata(dane: Dane, biuro: dict, dokumenty: int, etat: int, zlecenie: int) -> dict:
    """Opłata za rundę (brutto). Etatowi wchodzą do `w_cenie` przed zleceniobiorcami (są drożsi)."""
    limit = limit_rundy(biuro)
    ponad = 0 if limit is None else max(0, dokumenty - limit)
    ryczalt = dane.na_runde(biuro["ryczalt"])
    za_dokumenty = round(ponad * biuro["za_dokument"], 2)
    minimum = dane.na_runde(biuro["minimum"])
    ksiegowanie = round(max(ryczalt + za_dokumenty, minimum), 2)
    k = biuro["kadry"]
    platne_etat = max(0, etat - k["w_cenie"])
    platne_zlecenie = max(0, zlecenie - max(0, k["w_cenie"] - etat))
    kadry = dane.na_runde(platne_etat * k["etat"] + platne_zlecenie * k["zlecenie"])
    return {"dokumenty": dokumenty, "limit": limit, "ponad": ponad, "ryczalt": ryczalt, "za_dokumenty": za_dokumenty,
            "minimum": minimum, "ksiegowanie": ksiegowanie, "kadry": kadry, "osoby_platne": platne_etat + platne_zlecenie,
            "razem": round(ksiegowanie + kadry, 2)}


def szacunek(dane: Dane, biuro: dict, dokumenty: int, etat: int, zlecenie: int) -> float:
    """Oczekiwany koszt rundy: opłata + mandat razy ryzyko błędu (gdy biuro nie ma OC)."""
    kara = 0.0 if biuro["oc"] else biuro["ryzyko_bledu"] * ustawienia(dane)["samodzielna"]["kara_blad"]
    return round(oplata(dane, biuro, dokumenty, etat, zlecenie)["razem"] + kara, 2)


def najtansze(dane: Dane, dokumenty: int, etat: int, zlecenie: int) -> str:
    return min(biura(dane).values(), key=lambda b: szacunek(dane, b, dokumenty, etat, zlecenie))["id"]


def nalicz(dane: Dane, firma: Firma, ksiega: Ksiega, rachunek: Rachunek, etat: int, zlecenie: int) -> dict:
    """Faktura biura za rundę – koszt w KPiR (dokumenty rundy + ta faktura)."""
    b = biura(dane)[firma.biuro]
    o = oplata(dane, b, len(dokumenty(ksiega, rachunek)) + 1, etat, zlecenie)
    ksieguj(firma, ksiega, rachunek, f"Koszt biura rachunkowego: {b['nazwa']}", o["ksiegowanie"])
    ksieguj(firma, ksiega, rachunek, "Obsługa kadrowo-płacowa", o["kadry"])
    return {"biuro": b["id"], "nazwa": b["nazwa"], **o}


def blad_biura(dane: Dane, firma: Firma, nazwa: str, runda: int, ziarno: int, rachunek: Rachunek) -> dict | None:
    """Losowy błąd biura w deklaracji: mandat (biuro z OC go oddaje – poza KPiR)."""
    b = biura(dane)[firma.biuro]
    rng = strumien(ziarno, runda, "biuro", nazwa)
    if rng.random() >= b["ryzyko_bledu"]:
        return None
    u = ustawienia(dane)
    kara = float(u["samodzielna"]["kara_blad"])
    tekst = u["bledy"][int(rng.integers(len(u["bledy"])))].format(kara=f"{kara:.0f} zł", biuro=b["nazwa"])
    rachunek.zapisz(firma, f"Mandat karny skarbowy – błąd w deklaracji ({b['nazwa']})", -kara, "podatki")
    if b["oc"]:
        rachunek.zapisz(firma, f"Zwrot mandatu z OC biura ({b['nazwa']})", kara, "podatki")
    return {"tekst": tekst, "kara": kara, "oc": b["oc"]}


# --- dokumenty rundy ----------------------------------------------------------------------------------------

def _kolumna(p: dict | None) -> str:
    if p is None:
        return "pozostale"
    return next((k for k in KOLUMNY if abs(p[k]) >= 0.005), "towary")   # zakup w całości zwrócony – nadal towary


def dokumenty(ksiega: Ksiega, rachunek: Rachunek) -> list[dict]:
    """Dokumenty rundy w kolejności rachunku (+ dowody wewnętrzne): opis, typ, kierunek, brutto, rozbicie na stawki
    (tylko faktura z kilkoma stawkami) i poprawny zapis (kolumna KPiR albo „poza”, stawka VAT)."""
    pozycje: dict[str, list[dict]] = {}
    for p in ksiega.pozycje:
        if not p.get("bez_gotowki"):
            pozycje.setdefault(p["opis"], []).append(p)
    wpisy: dict[str, list[dict]] = {}
    for w in ksiega.rejestr_vat:
        wpisy.setdefault(("i|" if w.get("inwestycja") else "") + w["opis"], []).append(w)
    wynik: list[dict] = []

    def wez_wpisy(klucz: str, kwota: float) -> list[dict]:
        lista, wziete, suma = wpisy.get(klucz, []), [], 0.0
        while lista and suma + abs(lista[0]["brutto"]) <= kwota + 0.005:
            w = lista.pop(0)
            wziete.append(w)
            suma += abs(w["brutto"])
        return wziete

    def dodaj(opis: str, typ: str, kwota: float, kolumna: str, wybrane: list[dict]) -> None:
        brutto = round(abs(kwota), 2)
        stawki: dict[float, float] = {}
        for w in wybrane:
            stawki[w["stawka"]] = round(stawki.get(w["stawka"], 0.0) + abs(w["brutto"]), 2)
        reszta = round(brutto - sum(stawki.values()), 2)
        if stawki and reszta >= 0.005:
            stawki[0.0] = reszta          # część bez VAT na fakturze z VAT
        vat = round(sum(abs(w["vat"]) for w in wybrane), 2)
        jedna = (next(iter(stawki)) if stawki else 0.0) if len(stawki) <= 1 else None
        wynik.append({"id": f"d{len(wynik) + 1}", "opis": opis, "typ": typ,
                      "kierunek": "wplyw" if kwota > 0 else "wydatek" if kwota < 0 else "brak", "brutto": brutto,
                      "stawki": None if jedna is not None else [{"stawka": s, "brutto": b} for s, b in sorted(stawki.items())],
                      "netto": round(brutto - vat, 2), "vat": vat, "poprawne": {"kolumna": kolumna, "stawka": jedna}})

    for o in rachunek.operacje:
        k, opis, rodzaj = o["kwota"], o["opis"], o["rodzaj"]
        if abs(k) < 0.005:
            continue
        if rodzaj == "kpir":
            lista = pozycje.get(opis) or [None]
            p = lista.pop(0) if lista[0] is not None else None
            kol = _kolumna(p)
            typ = ("Faktura sprzedaży" if opis.startswith(SPRZEDAZ_TOWAROW)
                   else "Raport kasy fiskalnej" if kol == "przychod" else "Lista płac" if kol == "wynagrodzenia"
                   else "Deklaracja ZUS" if "ZUS" in opis
                   else "Wyciąg bankowy" if any(x in opis for x in ("Odsetki", "Prowizja", "Opłata za konto"))
                   else "Faktura sprzedaży" if kol == "przychod_pozostaly" else "Faktura zakupu")
            dodaj(opis, typ, k, kol, wez_wpisy(opis, abs(k)))
        elif rodzaj == "korekta":
            dodaj(opis, "Faktura korygująca", k, "towary", wez_wpisy(opis.replace(ZWROT, KOREKTA, 1), abs(k)))
        elif rodzaj == "inwestycje":
            w = wez_wpisy("i|" + opis, abs(k))
            dodaj(opis, "Faktura zakupu (środek trwały)" if w else TYPY_POZA[rodzaj], k, POZA, w)
        else:
            dodaj(opis, TYPY_POZA.get(rodzaj, "Wyciąg bankowy"), k, POZA, [])
    for p in ksiega.pozycje:
        if p.get("bez_gotowki"):
            dodaj(p["opis"], "Dowód wewnętrzny", 0.0, _kolumna(p), [])
            wynik[-1]["brutto"] = wynik[-1]["netto"] = round(sum(p[c] for c in KOLUMNY), 2)
    return wynik


def publiczne(dokumenty_: list[dict]) -> list[dict]:
    """Dokumenty bez poprawnych zapisów i kwot netto/VAT (do widoku drużyny przed złożeniem deklaracji)."""
    return [{k: v for k, v in d.items() if k not in ("poprawne", "netto", "vat")} for d in dokumenty_]


# --- samodzielna księgowość: deklaracja do złożenia i jej sprawdzenie ---------------------------------------

def stan_rozliczen(firma: Firma) -> dict:
    r = firma.rozliczenie
    return {"vat_nadwyzka": r.vat_nadwyzka, "dochod": r.dochod, "zaliczki": r.zaliczki,
            "zdrowotna_odliczona": r.zdrowotna_odliczona, "zaplacone": r.zaplacone}


def otworz(firma: Firma, runda: int, ksiega: Ksiega, rachunek: Rachunek, rozliczenie: dict, stan_przed: dict) -> None:
    """Koniec rundy przy samodzielnej księgowości: dokumenty i poprawne kwoty czekają na deklarację drużyny."""
    firma.deklaracja = {"runda": runda, "dokumenty": dokumenty(ksiega, rachunek), "stan_przed": stan_przed,
                        "ulga_na_start": rozliczenie["ulga_na_start"],
                        "poprawne": {"vat": rozliczenie["vat_do_zaplaty"], "pit": rozliczenie["zaliczka"],
                                     "zdrowotna": rozliczenie["zdrowotna"]}}


def _stawka(x) -> float | None:
    try:
        return round(float(x), 4)
    except (TypeError, ValueError):
        return None


def _proc(s: float | None) -> str:
    return "–" if s is None else f"{s * 100:g}%"


def sprawdz_zapisy(dokumenty_: list[dict], zapisy: dict) -> dict:
    """Każdy dokument: zapis drużyny vs poprawny; błędy z wyjaśnieniem."""
    wynik, dobre = [], 0
    for d in dokumenty_:
        z = zapisy.get(d["id"]) if isinstance(zapisy, dict) else None
        z = z if isinstance(z, dict) else {}
        pop, bledy = d["poprawne"], []
        kol, st = z.get("kolumna"), _stawka(z.get("stawka"))
        if not kol:
            bledy.append(f"nie zaksięgowano – powinno być: {NAZWY_KOLUMN[pop['kolumna']]}"
                         + (f", VAT {_proc(pop['stawka'])}" if pop["stawka"] is not None else ""))
        else:
            if kol != pop["kolumna"]:
                bledy.append(f"wpisano do „{NAZWY_KOLUMN.get(kol, kol)}”, a powinno być „{NAZWY_KOLUMN[pop['kolumna']]}” – "
                             f"{WYJASNIENIA[pop['kolumna']]}")
            if pop["stawka"] is not None and (st is None or abs(st - pop["stawka"]) > 1e-6):
                bledy.append(f"stawka VAT {_proc(st)} zamiast {_proc(pop['stawka'])}")
        dobre += not bledy
        wynik.append({"id": d["id"], "opis": d["opis"], "typ": d["typ"], "brutto": d["brutto"],
                      "kolumna": kol, "stawka": st, "poprawne": pop, "ok": not bledy, "bledy": bledy})
    return {"liczba": len(dokumenty_), "dobre": dobre, "dokumenty": wynik}


def _deklaracja(k: dict | None) -> dict | None:
    if not isinstance(k, dict) or not isinstance(k.get("deklaracja"), dict):
        return None
    dk = {}
    for pole in POLA:
        try:
            dk[pole] = max(0.0, do_grosza(float(k["deklaracja"].get(pole))))
        except (TypeError, ValueError):
            return None
    return dk


def rozlicz_deklaracje(dane: Dane, firma: Firma, d: dict, runda: int, rachunek: Rachunek, podglad: bool = False) -> dict | None:
    """Początek rundy: deklaracje za poprzednią rundę – zapłata, korekta, mandat (operacje poza KPiR)."""
    dk = firma.deklaracja
    if not dk:
        return None
    firma.deklaracja = None
    u, pop, za = ustawienia(dane)["samodzielna"], dk["poprawne"], dk["runda"]
    k = d.get("ksiegowosc")
    zlozona = _deklaracja(k)
    nowe_biuro = d.get("biuro") or firma.biuro
    if podglad:   # „Analiza – co jeśli”: bez sprawdzania (wynik nie może zdradzić poprawnych kwot)
        tryb, zlozona = "podglad", dict(pop)
    elif zlozona is None:
        tryb = "biuro" if nowe_biuro in biura(dane) else "brak"
        zlozona = dict(pop)
    else:
        tryb = "deklaracja"
    pozycje, kary = [], 0.0
    for pole, nazwa in POLA.items():
        ile, dobra = zlozona[pole], pop[pole]
        if ile:
            rachunek.zapisz(firma, f"{nazwa[0].upper() + nazwa[1:]} – deklaracja za rundę {za}", -ile, "podatki")
        roznica = round(dobra - ile, 2)
        if abs(roznica) >= 0.005:
            rachunek.zapisz(firma, f"Korekta deklaracji ({nazwa}) – {'dopłata' if roznica > 0 else 'zwrot nadpłaty'}",
                            -roznica, "podatki")
        blad = abs(roznica) >= TOLERANCJA
        if blad:
            kary += u["kara_blad"]
        pozycje.append({"pole": pole, "nazwa": nazwa, "zadeklarowano": ile, "poprawnie": dobra,
                        "korekta": roznica, "blad": blad})
    if tryb == "brak":
        kary = float(u["kara_brak"])
    if kary:
        rachunek.zapisz(firma, f"Mandat karny skarbowy – deklaracje za rundę {za}", -kary, "podatki")
    roz = firma.rozliczenie
    roz.zaplacone = round(roz.zaplacone + sum(pop.values()), 2)
    wynik = {"za_runde": za, "tryb": tryb, "pozycje": pozycje, "kara": kary,
             "razem": round(sum(pop.values()) + kary, 2)}
    if tryb == "deklaracja":
        wynik["zapisy"] = sprawdz_zapisy(dk["dokumenty"], k.get("zapisy") or {})
    elif tryb == "podglad":
        wynik = {"za_runde": za, "tryb": tryb}
    return wynik


def zamknij_samodzielnie(firma: Firma, ostatnia: bool) -> bool:
    """Czy rozliczenie rundy czeka na deklarację drużyny (w ostatniej rundzie rozlicza urząd)."""
    return firma.biuro == SAMODZIELNIE and not ostatnia


def bledy(dane: Dane, firma: Firma, d: dict) -> list[dict]:
    """Lista błędów (szkic): niezłożona deklaracja i niezaksięgowane dokumenty."""
    dk = firma.deklaracja
    if not dk or (d.get("biuro") or firma.biuro) != SAMODZIELNIE:
        return []
    u, k, wynik = ustawienia(dane)["samodzielna"], d.get("ksiegowosc") or {}, []
    if _deklaracja(k) is None:
        wynik.append({"poziom": "czerwony", "zakladka": "finanse_biuro",
                      "tekst": f"Nie złożono deklaracji za rundę {dk['runda']} – urząd rozliczy z urzędu i wystawi "
                               f"mandat {u['kara_brak']:.0f} zł."})
    zapisy = k.get("zapisy") if isinstance(k.get("zapisy"), dict) else {}
    brak = sum(1 for x in dk["dokumenty"] if not (zapisy.get(x["id"]) or {}).get("kolumna"))
    if brak:
        wynik.append({"poziom": "pomaranczowy", "zakladka": "finanse_biuro",
                      "tekst": f"Niezaksięgowane dokumenty za rundę {dk['runda']}: {brak} z {len(dk['dokumenty'])}."})
    return wynik


def ukryj(w: dict | None, podglad: bool = False) -> dict | None:
    """Wyniki rundy, której deklaracje drużyna dopiero składa: bez KPiR, VAT, rozliczenia i uzgodnienia kasy.
    `podglad` – „Analiza – co jeśli”: przychody i koszty zostają, bez podatków (to byłyby poprawne odpowiedzi)."""
    if not w:
        return w
    w = dict(w)
    if podglad:
        w["kpir"] = {**w["kpir"], "podatek": None, "dochod_netto": None, "ukryte_podatki": True}
    else:
        w["kpir"] = {"ukryte": True, "pozycje": [], **{k: None for k in (
            "przychody", "koszty", "towary", "wynagrodzenia", "pozostale", "dochod", "podatek", "dochod_netto")}}
    for k in ("vat", "rozliczenie", "uzgodnienie"):
        w[k] = None
    return w


def widok(dane: Dane, firma_przed: Firma, firma: Firma, d: dict, wyniki: dict | None) -> dict:
    """Zakładka Biuro rachunkowe (gra z lokalami): oferty z szacunkiem opłaty, deklaracja do złożenia (dokumenty
    bez poprawnych zapisów) i podpowiedzi – zapisy, które drużyna już raz zrobiła dobrze (ten sam opis)."""
    u = ustawienia(dane)
    etat = sum(1 for p in firma.pracownicy.values() if p.umowa == "prace")
    dok = len(dokumenty_ostatnie := (firma_przed.deklaracja or {}).get("dokumenty") or []) or u["szacunek_dokumentow"]
    oferty = [{**b, "szacunek": oplata(dane, b, dok, etat, len(firma.pracownicy) - etat),
               "limit_rundy": limit_rundy(b)} for b in u["biura"]]
    dk = firma_przed.deklaracja
    podpowiedzi = {}
    for x in ((wyniki or {}).get("ksiegowosc") or {}).get("zapisy", {}).get("dokumenty", []):
        if x["ok"]:
            podpowiedzi[x["opis"]] = {"kolumna": x["kolumna"], "stawka": x["stawka"]}
    return {"oferty": oferty, "samodzielna": u["samodzielna"], "kolumny": NAZWY_KOLUMN, "wyjasnienia": WYJASNIENIA,
            "dokumenty_szacunek": dok, "pracownicy": {"etat": etat, "zlecenie": len(firma.pracownicy) - etat},
            "deklaracja": None if not dk else {"runda": dk["runda"], "dokumenty": publiczne(dk["dokumenty"]),
                                               "stan_przed": dk["stan_przed"], "ulga_na_start": dk["ulga_na_start"]},
            "podpowiedzi": podpowiedzi, "liczba_dokumentow": len(dokumenty_ostatnie)}
