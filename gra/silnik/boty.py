"""Boty – firmy komputerowe. Decydują tym samym formatem co gracz (silnik/decyzje.py), na podstawie stanu
po poprzedniej rundzie i danych publicznych rynku. Deterministyczne (ziarno gry), więc w grze przez GitHub
każdy komputer liczy je sam.

Strategie (dane/boty.yaml: strategie): cena w % ceny preferowanej, jakość (gwiazdki sprzętu, zasobów, pracowników),
docelowa liczba usług, pokrycie popytu, inwestycje w wyposażenie i udogodnienia, reklama, szkolenia.

Poziomy (dane/boty.yaml: poziomy, gra z lokalami; bez lokali – zawsze dawne reguły):
- łatwy – proste reguły: osobna kuchnia na każde danie, zamówienia na cały przewidywany popyt (choć kuchnia
  nie nadąży – psuje się towar), prognoza z losowym błędem, najtańszy kandydat, bez kampanii i promocji;
- średni – planuje lokal: kucharzy, sztuki sprzętu i kasjerów na popyt dzień po dniu (najwyżej tyle, ile miejsc
  w lokalu), a zamawia tylko to, co kuchnia zdąży sprzedać;
- trudny – jak średni, a do tego poprawia prognozę o błąd z poprzedniej rundy, wybiera cenę o największej
  oczekiwanej marży (po koszcie składników i pracy), reklamuje się tylko z wolną kuchnią i bierze kolejny
  gotowy lokal, gdy obecne nie nadążają;
- niemożliwy – jak trudny, ale oszukuje: klienci bez powodu wolą jego lokale (przewaga_popytu, silnik/runda.py).
"""
from __future__ import annotations

from copy import deepcopy

import numpy as np

from .dane import KASA, KUCHNIA, Dane
from .decyzje import kandydaci_firmy
from .ksiegowosc import biuro as bo
from .ksiegowosc.finanse import Ksiega, Rachunek
from .kuchnia import menu as mn
from .kuchnia.dostawcy import ceny_rundy
from .kuchnia.jakosc import mnoznik_wyposazenia
from .kuchnia.planowanie import (
    godziny_uslugi,
    kasjerzy_potrzebni,
    stanowiska_potrzebne,
    zamowienie_zasobow,
)
from .losowosc import strumien
from .ludzie import rynek_pracy as rp
from .model import Firma, StanGry
from .nieruchomosci import lokale as lk
from .pieniadze import banki as bk
from .rynek import popyt as pp
from .rynek import promocje as pm
from .rynek import reklama as rk
from .swiat import awarie as aw
from .swiat import zdarzenia as zd

DOMYSLNY_POZIOM = "sredni"


def _ranking_uslug(dane: Dane) -> list[str]:
    """Usługi od najwyższego przychodu na godzinę prowadzącego (cena × grupa / godziny)."""
    return sorted(dane.uslugi, key=lambda u: -dane.uslugi[u]["cena_preferowana"] * dane.uslugi[u]["grupa"]
                  / dane.uslugi[u]["godziny_prowadzacego"])


def _cena(dane: Dane, strategia: dict, stan: StanGry, u: str, runda: int, mnoznik: float = 1.0) -> float:
    pref = dane.uslugi[u]["cena_preferowana"]
    wsp = strategia["cena"]
    if wsp is None:  # naśladowca: średnia cen rynku z poprzedniej rundy
        ceny = stan.rynek.get(runda - 1, {}).get("ceny", {}).get(u, {})
        wsp = (sum(ceny.values()) / len(ceny) / pref) if ceny else dane.boty["ustawienia"]["cena_nasladowcy_bez_danych"]
    krok = dane.boty["ustawienia"]["krok_ceny"]
    return round(pref * wsp * mnoznik / krok) * krok


def poziom(dane: Dane, konf: dict, nazwa: str) -> dict:
    """Ustawienia poziomu bota z konfiguracji gry (firmy[].poziom; bez niego – średni)."""
    klucz = next((f.get("poziom") for f in konf.get("firmy", []) if f["nazwa"] == nazwa), None) or DOMYSLNY_POZIOM
    return (dane.boty.get("poziomy") or {}).get(klucz) or {}


def przewaga_popytu(dane: Dane, konf: dict, nazwa: str) -> float:
    """Mnożnik atrakcyjności lokali firmy z poziomu bota (niemożliwy > 1); drużyny graczy – zawsze 1."""
    if not any(f["nazwa"] == nazwa and f.get("bot") for f in konf.get("firmy", [])):
        return 1.0
    return poziom(dane, konf, nazwa).get("przewaga_popytu", 1.0)


def _wybierz_lokal(dane: Dane, stan: StanGry, nazwa: str, strategia_klucz: str, runda: int, konf: dict,
                   min_kuchnia: int = 0, strefy: list[str] | None = None) -> dict | None:
    """Gotowy lokal do najmu wg strategii: tani – najniższy czynsz, premium – Stare Miasto i Centrum, inni – środek
    stawki. Losowanie spośród trzech najlepszych (ziarno gry), żeby boty nie biły się zawsze o ten sam lokal.
    min_kuchnia – najmniej miejsc w kuchni (planujący bot; bez takich lokali – każdy); strefy – tylko lokale w tych
    strefach (strategia: strefy, np. pomiar w balans/warianty.py; bez wolnych – każda strefa)."""
    wolne = [lok for lok in lk.dostepne(dane, runda, lk.zajete(stan.firmy), len(stan.firmy)) if lok["typ"] == "gotowy" and lok.get("czynsz")]
    wolne = [lok for lok in wolne if lok["miejsca"][KUCHNIA] >= min_kuchnia] or wolne
    if strefy:
        wolne = [lok for lok in wolne if lok["strefa"] in strefy] or wolne
    if not wolne:
        return None
    if strategia_klucz == "tani":
        wolne.sort(key=lambda lok: lok["czynsz"])
    elif strategia_klucz == "premium":
        wolne.sort(key=lambda lok: (lok["strefa"] not in ("stare_miasto", "centrum"), -lok["miejsca"]["kuchnia"], lok["czynsz"]))
    else:
        sr = sorted(lok["czynsz"] for lok in wolne)[len(wolne) // 2]
        wolne.sort(key=lambda lok: (abs(lok["czynsz"] - sr), lok["id"]))
    najlepsze = wolne[:3]
    lok = najlepsze[int(strumien(konf["ziarno"], runda, "lokal", nazwa).integers(len(najlepsze)))]
    return {"id": lok["id"], "forma": "najem"}


def _kampanie(dane: Dane, f: Firma, st: dict, runda: int, ust: dict) -> list[dict]:
    """Kampanie ze strategii w strefach własnych lokali: dostępne, nietrwające, nie za słabe po powtórkach, a po
    zapłacie zostaje bufor gotówki."""
    strefy = sorted({dane.lokale[lok.id]["strefa"] for lok in f.lokale})
    wynik, wydatki = [], 0.0
    for x in st.get("kampanie", []) if strefy else []:
        a, _, k = x.partition("/")
        kan = rk.kanal(dane, a, k)
        if kan is None or kan["od_rundy"] > runda:
            continue
        for s in [None] if kan["zasieg"] == "miasto" else [z for z in strefy if z in rk.strefy_kanalu(dane, kan)]:
            koszt = rk.brutto(dane, rk.koszt(dane, kan, s))
            if rk.trwa(f, a, k, s, runda) or rk.sila_nowej(dane, f, a, k, s, runda) < ust["min_sila_kampanii"] \
                    or f.gotowka - wydatki - koszt < ust["bufor_kampanii"]:
                continue
            wynik.append({"agencja": a, "kanal": k, "strefa": s})
            wydatki += koszt
    return wynik


def _promocje(dane: Dane, f: Firma, st: dict, runda: int, d: dict, bufor: bool, poprzednie: dict | None,
              ust: dict) -> list[dict] | None:
    """Promocje ze strategii (nowe tylko z buforem gotówki); danie – trwającej promocji albo najdroższe w sprzedaży.

    Bot, który w poprzedniej rundzie nie obsłużył prawie całego popytu, promocje wyłącza – brakuje mu rąk albo
    lokalu, więc promocja dałaby tylko rabat."""
    R = pm.zasady(dane)
    if not R or not f.lokale or runda < R["od_rundy"]:
        return None
    sp = (poprzednie or {}).get("sprzedaz", {}).values()
    popyt = sum(v["popyt"] for v in sp)
    if not popyt or sum(v["sprzedaz"] for v in sp) < ust["min_obsluga_promocji"] * popyt:   # bez danych – też nie
        return []
    sprz = d.get("sprzedaz") or {u: {"cena": c.cena} for u, c in f.ceny.items()}
    trwa = {p.typ: p.danie for p in f.promocje}
    wynik = []
    for x in st.get("promocje", []):
        danie = trwa.get(x["typ"]) if trwa.get(x["typ"]) in sprz else max(sprz, key=lambda u: sprz[u]["cena"], default=None)
        if (x["typ"] in trwa or bufor) and danie:
            wynik.append({"typ": x["typ"], "nazwa": x["nazwa"], "danie": danie})
    return wynik[:R["limit_aktywnych"]]


# --- planowanie lokalu (poziom średni i trudny, model puli) ---


def _czesc_dni(w: np.ndarray, potrzeba: float, pojemnosc: float) -> np.ndarray:
    """Obsłużona część każdego dnia rundy: tygodniowa potrzeba godzin rozkłada się wg wag dni, pojemność – równo."""
    if potrzeba <= 0:
        return np.ones(len(w))
    dzien = potrzeba * w / w.sum()
    return np.minimum(1.0, pojemnosc / len(w) / np.maximum(dzien, 1e-9))


def _ile(w: np.ndarray, potrzeba: float, godziny: float, cel: float, maks: int,
         oplata: tuple[float, float] | None = None) -> int:
    """Najmniej osób (sztuk sprzętu), z którymi obsłużona część tygodniowej potrzeby osiąga cel (najwyżej maks).
    oplata – (marża z całej potrzeby, koszt osoby): kolejna osoba tylko, gdy dodatkowa sprzedaż pokrywa jej koszt
    (pierwsza zawsze – bez niej lokal nic nie sprzeda)."""
    if potrzeba <= 0:
        return 0

    def czesc(n: int) -> float:
        return float((_czesc_dni(w, potrzeba, n * godziny) * w).sum() / w.sum())

    for n in range(1, maks + 1):
        if czesc(n) >= cel or (oplata and n < maks and (czesc(n + 1) - czesc(n)) * oplata[0] < oplata[1]):
            return n
    return maks


def _plan_lokalu(dane: Dane, f: Firma, lok_id: str, klienci: dict[str, float], w: np.ndarray,
                 nowe_kuchnia: list[int], nowe_kasa: list[int], ekonomia: dict) -> dict:
    """Obsada lokalu w modelu puli: kucharze każdego zawodu i kasjerzy tak, żeby dzień po dniu obsłużyć część
    popytu ekonomia["cel"], ale kolejna osoba tylko, gdy dodatkowa sprzedaż × marża porcji (ekonomia["marza"])
    pokrywa jej koszt (ekonomia["osoby"]); sprzęt – tyle sztuk, żeby nie hamował kucharzy. Najwyżej tyle, ile
    stanowisk (istniejących i nowych, `nowe_*` – numery wolnych miejsc w lokalu). Zwraca liczby, obsłużoną część
    każdego dnia ("dni") i nowe stanowiska."""
    op = dane.z["operacje"]
    kuchnia = [s for s in f.stanowiska_typu(KUCHNIA) if s.lokal == lok_id]
    kasa = [s for s in f.stanowiska_typu(KASA) if s.lokal == lok_id]
    miejsc_k, miejsc_r = len(kuchnia) + len(nowe_kuchnia), len(kasa) + len(nowe_kasa)
    cel, osoby, marza, godz = ekonomia["cel"], ekonomia["osoby"], ekonomia["marza"], op["godziny_pracownika"]
    zawody: dict[str, list[float]] = {}   # zawód → [godziny, marża]
    sprzet: dict[str, float] = {}
    for u, k in klienci.items():
        h = godziny_uslugi(dane, u, k)
        x = zawody.setdefault(dane.uslugi[u]["prowadzacy"], [0.0, 0.0])
        x[0] += h
        x[1] += k * marza.get(u, 0.0)
        for n in dane.uslugi[u]["sprzet"]:
            sprzet[n] = sprzet.get(n, 0.0) + h
    kucharze = {z: _ile(w, h, godz, cel, miejsc_k, (m, osoby.get(z, 0.0))) for z, (h, m) in zawody.items()}
    while sum(kucharze.values()) > miejsc_k:   # kilka zawodów – kuchnia nie zmieści wszystkich
        z = max(kucharze, key=kucharze.get)
        kucharze[z] -= 1
    dni = np.ones(len(w))
    for z, (h, _) in zawody.items():
        dni = np.minimum(dni, _czesc_dni(w, h, kucharze[z] * godz))
    obsada = float((dni * w).sum() / w.sum()) - 1e-6   # sprzęt ma nadążyć za kucharzami
    sztuki = {n: _ile(w, h, op["godziny_sprzetu"], obsada, miejsc_k) for n, h in sprzet.items()}
    stanowisk = min(miejsc_k, max([len(kuchnia), sum(kucharze.values()), *sztuki.values()]))
    rec = sum(k * dane.uslugi[u]["godziny_kasy"] for u, k in klienci.items())
    kasjer = (sum(k * marza.get(u, 0.0) for u, k in klienci.items()), osoby.get(dane.zawody_typu(KASA)[0], 0.0))
    kasjerzy = min(miejsc_r, max(1 if klienci else 0, _ile(w, rec, godz, cel, miejsc_r, kasjer)))
    dni = np.minimum(dni, _czesc_dni(w, rec, kasjerzy * godz))
    for n, h in sprzet.items():
        dni = np.minimum(dni, _czesc_dni(w, h, sztuki[n] * op["godziny_sprzetu"]))
    return {"kucharze": kucharze, "sztuki": sztuki, "kasjerzy": kasjerzy, "dni": dni,
            "nowe_kuchnia": nowe_kuchnia[:max(0, stanowisk - len(kuchnia))],
            "nowe_kasa": nowe_kasa[:max(0, kasjerzy - len(kasa))], "kuchnia": kuchnia, "kasa": kasa}


def _plan_firmy(dane: Dane, f: Firma, prognoza_lokali: dict[str, dict[str, float]], r_sprz: int, runda: int,
                ekonomia: dict) -> dict:
    """Plany wszystkich działających lokali. Nowe stanowiska zajmują wolne miejsca w kolejności lokali
    (silnik/decyzje.py), więc lokal dostaje numery następne po miejscach wcześniejszych lokali."""
    miejsca = lk.wolne_miejsca(dane, f, runda)
    nr = {t: f.nowy_nr(t) for t in (KUCHNIA, KASA)}
    maks = dane.maks_nowych_stanowisk
    plany, sprzedaz, dni = {}, {}, None
    for lok_id, klienci in prognoza_lokali.items():
        nowe = {t: [nr[t] + i for i, x in enumerate(miejsca[t][:maks]) if x == lok_id] for t in (KUCHNIA, KASA)}
        w = pp.wagi_dni(dane, dane.lokale[lok_id]["strefa"], pp.dni_rundy(dane, r_sprz))
        p = _plan_lokalu(dane, f, lok_id, klienci, w, nowe[KUCHNIA], nowe[KASA], ekonomia)
        p["czesc"] = float((p["dni"] * w).sum() / w.sum()) if w.sum() > 0 else 0.0
        plany[lok_id] = p
        for u, k in klienci.items():
            sprzedaz[u] = sprzedaz.get(u, 0.0) + k * p["czesc"]
        porcje = sum(klienci.values()) * p["dni"] * w / w.sum()
        dni = porcje if dni is None else dni + porcje
    return {"lokale": plany, "sprzedaz": sprzedaz, "dni": [float(x) for x in dni] if dni is not None else None}


def _decyzje_planu(dane: Dane, plan: dict, q: int) -> tuple[list[dict], list[tuple[str, int, str]], dict[str, int]]:
    """Z planu lokali: zakupy sprzętu, stanowiska do obsadzenia [(typ, nr, zawód)] (najpierw pierwszy kucharz
    i kasjer lokalu bez nich – bez nich lokal nic nie sprzeda) i liczba nowych stanowisk każdego typu."""
    kup, pilne, reszta = [], [], []
    nowe = {KUCHNIA: 0, KASA: 0}
    for p in plan["lokale"].values():
        miejsca = [(s.nr, dict(s.sprzet), s.pracownik) for s in p["kuchnia"]] + [(n, {}, None) for n in p["nowe_kuchnia"]]
        for n, ile in p["sztuki"].items():
            brak = ile - sum(1 for _, sp, _ in miejsca if n in sp)
            for nr, sp, _ in miejsca:
                if brak <= 0:
                    break
                if n not in sp:
                    sp[n] = q
                    kup.append({"typ": KUCHNIA, "nr": nr, "nazwa": n, "jakosc": q})
                    brak -= 1
        wolne = [nr for nr, _, prac in miejsca if not prac]
        for z, ile in p["kucharze"].items():
            maja = p["zatrudnieni"].get(z, 0)
            for i in range(min(len(wolne), max(0, ile - maja))):
                (pilne if maja + i == 0 else reszta).append((KUCHNIA, wolne.pop(0), z))
        kasy = [(s.nr, s.sprzet, s.pracownik) for s in p["kasa"]] + [(n, {}, None) for n in p["nowe_kasa"]]
        for nr, sp, _ in kasy:
            for n in dane.sprzet_kasy:
                if n not in sp:
                    kup.append({"typ": KASA, "nr": nr, "nazwa": n, "jakosc": q})
        maja = sum(1 for _, _, prac in kasy if prac)
        kasjer = dane.zawody_typu(KASA)[0]
        for i, nr in enumerate([nr for nr, _, prac in kasy if not prac][:max(0, p["kasjerzy"] - maja)]):
            (pilne if maja + i == 0 else reszta).append((KASA, nr, kasjer))
        nowe[KUCHNIA] += len(p["nowe_kuchnia"])
        nowe[KASA] += len(p["nowe_kasa"])
    return kup, pilne + reszta, nowe


def _zatrudnieni(f: Firma, plan: dict) -> None:
    """Liczba zatrudnionych kucharzy każdego zawodu w lokalach planu (do `_decyzje_planu`)."""
    for p in plan["lokale"].values():
        z: dict[str, int] = {}
        for s in p["kuchnia"]:
            prac = f.pracownik_stanowiska(s)
            if prac:
                z[prac.zawod] = z.get(prac.zawod, 0) + 1
        p["zatrudnieni"] = z


def _prognoza_lokali(dane: Dane, f: Firma, nazwa: str, oferta: list[str], ceny: dict[str, float], q: int,
                     wyp: float, konkurencja: dict, r_sprz: int) -> dict:
    moje = {lok.id: {u: {"strefa": dane.lokale[lok.id]["strefa"], "cena": ceny[u], "jakosc": (q, q, q),
                         "wyposazenie": wyp} for u in oferta} for lok in f.lokale if lok.dziala_od <= r_sprz}
    return pp.prognoza(dane, r_sprz, {**konkurencja, nazwa: moje}, nazwa)


def _korekta_prognozy(stan: StanGry, nazwa: str, runda: int, granice: list[float]) -> float:
    """Popyt / prognoza poprzedniej rundy (bot trudny poprawia nią prognozę), w granicach z danych."""
    sp = (stan.wyniki.get(runda - 1, {}).get(nazwa) or {}).get("sprzedaz", {}).values()
    prog = sum(v["prognoza"] for v in sp if v["prognoza"])
    if not prog:
        return 1.0
    return min(max(granice), max(min(granice), sum(v["popyt"] for v in sp if v["prognoza"]) / prog))


def _koszt_pracy(dane: Dane, stan: StanGry, zawod: str, narzut: float) -> float:
    """Szacunkowy koszt rundy jednej osoby zawodu: średnia pensja preferowana kandydatów × narzut."""
    p = [k["pensja_preferowana"] for k in stan.kandydaci if k["zawod"] == zawod]
    return dane.na_runde(sum(p) / len(p)) * narzut if p else 0.0


def _marza(dane: Dane, plan: dict, ekonomia: dict) -> float:
    """Oczekiwana marża rundy: sprzedaż w granicach przepustowości × (cena − składniki) − koszt pracy obsady."""
    m = sum(n * ekonomia["marza"][u] for u, n in plan["sprzedaz"].items())
    for p in plan["lokale"].values():
        m -= sum(n * ekonomia["osoby"].get(z, 0.0) for z, n in p["kucharze"].items())
        m -= p["kasjerzy"] * ekonomia["osoby"].get(dane.zawody_typu(KASA)[0], 0.0)
    return m


def decyzje_bota(dane: Dane, stan: StanGry, nazwa: str, strategia_klucz: str, runda: int, konf: dict) -> dict:
    strategie = dane.boty["strategie"]
    st = strategie.get(strategia_klucz, strategie["zrownowazony"])
    ust = dane.boty["ustawienia"]
    f: Firma = stan.firmy[nazwa]
    q = st["jakosc"]
    rundy = dane.katalog_ofert["rundy"]
    odbl = dane.odblokowane(runda)
    d: dict = {"zatrudnij": [], "sprzet_kup": [], "zamowienia": []}
    pz = poziom(dane, konf, nazwa)
    planuje = pz.get("planowanie", "przepustowosc") == "przepustowosc" and dane.mapa.get("popyt")
    # wszystkie lokale z wypowiedzianym najmem (nowy właściciel budynku, silnik/nieruchomosci/przejecia.py) – szuka nowego
    wyprowadzka = f.lokale and all(x.najem_do is not None for x in f.lokale) \
        and runda >= lk.runda_nowego_lokalu(dane, f)
    if not f.lokale or wyprowadzka:
        # bez lokalu: najem gotowego lokalu; dalsze decyzje liczone tak, jakby lokal już był (przegrany spór o lokal
        # – stanowiska odrzucone, ponowna próba w następnej rundzie)
        d["lokal"] = _wybierz_lokal(dane, stan, nazwa, strategia_klucz, runda, konf,
                                    st.get("min_kuchnia", 0) if planuje else 0, st.get("strefy"))
        if d["lokal"] is None and not f.lokale:
            return d
        if d["lokal"] is not None:
            f = deepcopy(f)
            lk.wybierz(dane, f, d["lokal"], runda, lk.zajete(stan.firmy), Ksiega(), Rachunek())
    miejsca = lk.wolne_miejsca(dane, f, runda)
    if not f.bank:
        d["bank"] = bk.najlepsze(dane)["konto"]
    if not (f.biuro and bo.poprawny_wybor(dane, f.biuro)):   # biura z mapy – najtańsze dla typowej rundy
        d["biuro"] = bo.najtansze(dane, bo.ustawienia(dane)["szacunek_dokumentow"], 4, 0)

    # usługi: start z usługami startowymi, potem po 3 nowe aż do celu
    oferta = list(f.oferta) or list(rundy["uslugi_startowe"])
    if runda >= rundy["nowe_uslugi_od_rundy"]:
        for u in _ranking_uslug(dane):
            if len(oferta) >= st["uslugi"] or len([x for x in oferta if x not in f.oferta]) >= rundy["nowe_uslugi_na_runde"]:
                break
            if u not in oferta:
                oferta.append(u)

    # popyt strefowy w rundzie sprzedaży (runda 1 planuje rundę 2): prognoza dla własnych lokali przy cenach
    # konkurencji z poprzedniej rundy
    wyp = mnoznik_wyposazenia(dane, f.wyposazenie)
    ceny = {u: _cena(dane, st, stan, u, runda) for u in oferta}
    szczyt, udzialy_dni, plan = 1.0, None, None
    r_sprz = max(runda, 2)
    konkurencja = pp.oferty_konkurencji(dane, stan, r_sprz, nazwa)
    korekta = _korekta_prognozy(stan, nazwa, runda, pz["korekta_prognozy"]) if pz.get("korekta_prognozy") else 1.0
    blad = pz.get("blad_prognozy", 0)
    if blad:   # łatwy: prognoza „na oko”
        korekta *= 1 + float(strumien(konf["ziarno"], runda, "bot", nazwa, "prognoza").uniform(-blad, blad))

    def prognoza_cen(c: dict[str, float]) -> tuple[dict, dict]:
        prog = _prognoza_lokali(dane, f, nazwa, oferta, c, q, wyp, konkurencja, r_sprz)
        lok = {x: {u: n * korekta * st["pokrycie"] for u, n in dania.items()} for x, dania in prog["lokale"].items()}
        return prog, lok

    prog, prog_lok = prognoza_cen(ceny)
    if planuje:
        osoby = {z: _koszt_pracy(dane, stan, z, pz.get("narzut_pracy", 1.0)) for z in dane.zawody}

        def ekonomia(c: dict[str, float]) -> dict:
            return {"cel": pz.get("cel_obslugi", 1.0), "osoby": osoby,
                    "marza": {u: c[u] - mn.koszt_porcji(dane, f, u) for u in c}}

        plan = _plan_firmy(dane, f, prog_lok, r_sprz, runda, ekonomia(ceny))
        if pz.get("mnozniki_ceny") and "sprzedaz" in odbl:   # trudny: cena o największej oczekiwanej marży
            najlepsza = (_marza(dane, plan, ekonomia(ceny)), ceny, prog, prog_lok, plan)
            for m in pz["mnozniki_ceny"]:
                c = {u: _cena(dane, st, stan, u, runda, m) for u in oferta}
                if c == ceny:
                    continue
                pr, pl = prognoza_cen(c)
                pn = _plan_firmy(dane, f, pl, r_sprz, runda, ekonomia(c))
                if (mz := _marza(dane, pn, ekonomia(c))) > najlepsza[0]:
                    najlepsza = (mz, c, pr, pl, pn)
            _, ceny, prog, prog_lok, plan = najlepsza
        drugi = pz.get("kolejny_lokal")
        if drugi and "lokal" not in d and plan["lokale"] \
                and all(p["czesc"] < drugi["obsluga"] for p in plan["lokale"].values()) \
                and f.gotowka > drugi["gotowka"] and len(f.lokale) < drugi["maks_lokali"] \
                and runda >= lk.runda_nowego_lokalu(dane, f) and all(x.dziala_od <= runda for x in f.lokale):
            d["lokal"] = _wybierz_lokal(dane, stan, nazwa, strategia_klucz, runda, konf, st.get("min_kuchnia", 0),
                                        st.get("strefy"))
            if d["lokal"] is None:
                d.pop("lokal")
            else:
                f = deepcopy(f)
                lk.wybierz(dane, f, d["lokal"], runda, lk.zajete(stan.firmy), Ksiega(), Rachunek())
                prog, prog_lok = prognoza_cen(ceny)
                plan = _plan_firmy(dane, f, prog_lok, r_sprz, runda, ekonomia(ceny))
        _zatrudnieni(f, plan)
        klienci = {u: plan["sprzedaz"].get(u, 0.0) for u in oferta}   # zamówienia: tyle, ile kuchnia sprzeda
        udzialy_dni = plan["dni"]
    else:
        klienci = {u: prog["dania"].get(u, 0.0) * korekta * st["pokrycie"] for u in oferta}
        udzialy_dni = prog["dni"] or None
        szczyt = max([pp.szczyt(dane, dane.lokale[x]["strefa"], r_sprz) for x in prog_lok] or [1.0])
    prognoza_dan = {u: sum(x.get(u, 0.0) for x in prog_lok.values()) / st["pokrycie"] for u in oferta}
    d["oferta"] = {u: int(round(prognoza_dan[u])) for u in oferta}
    if "sprzedaz" in odbl:
        d["sprzedaz"] = {u: {"cena": ceny[u], "rabat": 0} for u in oferta}

    istniejace = f.stanowiska_typu(KUCHNIA)
    rec = f.stanowiska_typu(KASA)
    if plan is not None:
        d["sprzet_kup"], cele, d["stanowiska"] = _decyzje_planu(dane, plan, q)
    else:
        cele = _stanowiska_proste(dane, f, d, oferta, klienci, szczyt, miejsca, q)

    # zatrudnienie (od rundy 2): stanowiska bez pracownika, które mają (albo dostają) sprzęt
    if "hr_zatrudnienie" in odbl:
        pula = kandydaci_firmy(rp.widoczni(dane, stan.kandydaci, runda), stan.firmy[nazwa])
        rng = strumien(konf["ziarno"], runda, "bot", nazwa)
        if plan is None:
            obsada = {o["nr"]: o["zawod"] for o in d.pop("_obsada", [])}
            for s in istniejace:
                if not s.pracownik and s.sprzet and s.nr not in obsada:
                    zawod = next((dane.uslugi[u]["prowadzacy"] for u in dane.uslugi
                                  if all(n in s.sprzet for n in dane.uslugi[u]["sprzet"])), dane.zawody_typu(KUCHNIA)[0])
                    obsada[s.nr] = zawod
            kasjer = dane.zawody_typu(KASA)[0]
            cele = [(KUCHNIA, nr, zawod) for nr, zawod in sorted(obsada.items())]
            cele += [(KASA, s.nr, kasjer) for s in rec if not s.pracownik]
            cele += [(KASA, f.nowy_nr(KASA) + i, kasjer) for i in range(d["stanowiska"][KASA])]
        cele = cele[: rp.ustawienia(dane)["limit_nowych"]]   # agencja pracy: limit nowych, reszta w kolejnych
        for typ, nr, zawod in cele:
            kandydaci = [k for k in pula if k["zawod"] == zawod]
            if not kandydaci:
                continue
            if pz.get("losowy_kandydat"):   # łatwy: pierwszy lepszy kandydat zawodu
                najlepsi = sorted(kandydaci, key=lambda k: k["id"])
            else:
                najlepsi = sorted(kandydaci, key=lambda k: (abs(k["gwiazdki"] - q), k["pensja_preferowana"]))[:ust["losuj_z_najlepszych_kandydatow"]]
            k = najlepsi[int(rng.integers(len(najlepsi)))]
            pula.remove(k)
            d["zatrudnij"].append({"kandydat": k["id"], "typ": typ, "nr": nr, "pensja": k["pensja_preferowana"],
                                   "umowa": "prace", "zastepca": True, "wzor": {"zawod": zawod, "gwiazdki": q}})
    else:
        d.pop("_obsada", None)

    # zasoby na przewidywanych klientów
    if "dostawcy" in odbl:
        ceny_d = ceny_rundy(dane, konf["ziarno"], runda, konf.get("ceny_dostawcow", "dane"))
        d["zamowienia"] = zamowienie_zasobow(dane, f, klienci, ceny_d, q, ust["zapas_zasobow"], udzialy_dni,
                                             dane.data_rundy(runda))

    # inwestycje dodatkowe wg strategii (gdy jest gotówka)
    bufor = f.gotowka > ust["bufor_gotowki"]
    if "inwestycje_wyposazenie" in odbl and bufor:
        d["wyposazenie_kup"] = [p["nazwa"] for p in sorted(dane.pozycje("wyposazenie").values(), key=lambda p: -p["procent"])
                                if p["od_rundy"] <= runda and p["nazwa"] not in f.wyposazenie][:max(0, st["wyposazenie"] - len(f.wyposazenie))]
    if "hr_udogodnienia" in odbl and bufor:
        d["udogodnienia_kup"] = [p["nazwa"] for p in sorted(dane.pozycje("udogodnienia").values(), key=lambda p: p["cena"] / p["procent"])
                                 if p["od_rundy"] <= runda and p["nazwa"] not in f.udogodnienia][:max(0, st["udogodnienia"] - len(f.udogodnienia))]
    agencje = rk.zasady(dane) is not None   # kampanie agencji reklamowych
    reklamuje = pz.get("kampanie", True)
    if plan is not None and pz.get("obsluga_kampanii") is not None:   # trudny: reklama tylko z wolną kuchnią
        reklamuje = reklamuje and all(p["czesc"] >= pz["obsluga_kampanii"] for p in plan["lokale"].values())
    if agencje:
        d["kampanie"] = _kampanie(dane, f, st, runda, ust) if reklamuje else []
    poprzednie = stan.wyniki.get(runda - 1, {}).get(nazwa)
    if (promo := _promocje(dane, f, st, runda, d, bufor, poprzednie, ust)) is not None:
        d["promocje"] = promo if pz.get("promocje", True) else []
    if "hr_szkolenia" in odbl and bufor and st["szkolenia"]:
        szk = dane.katalog_ofert["szkolenia"]
        najlepsze = sorted(szk["pozycje"], key=lambda p: -p["procent"])[:st["szkolenia"]]
        d["szkolenia"] = [{"firma": szk["firmy"][1]["nazwa"], "szkolenie": p["nazwa"]} for p in najlepsze]
    if dane.zdarzenia:   # eventy w parkach: losowa opcja (najwyżej 3 h właściciela)
        d["zdarzenia"] = zd.wybor_bota(dane, f, runda, konf["ziarno"])
    if aw.dane_wypadkow(dane):   # polisy wg strategii – od kiedy ma lokal
        d["polisy"] = list(st.get("polisy", [])) if f.lokale else []
    if st.get("higiena"):   # poziom higieny lokali wg strategii (dane/zdarzenia/urzad.yaml)
        d["higiena"] = st["higiena"]
    return d


def _stanowiska_proste(dane: Dane, f: Firma, d: dict, oferta: list[str], klienci: dict[str, float], szczyt: float,
                       miejsca: dict | None, q: int) -> list:
    """Dawne reguły (gra bez lokali i bot łatwy): osobne stanowisko z kompletem sprzętu na każde danie, kasa na
    szczyt popytu. Obsada stanowisk kuchni – w d["_obsada"] (lista celów zatrudnienia powstaje przy zatrudnianiu)."""
    nowe_inst = []
    istniejace = f.stanowiska_typu(KUCHNIA)
    wolne = [s for s in istniejace if not s.sprzet]
    nastepny = f.nowy_nr(KUCHNIA)
    for u in oferta:
        potrzeba = stanowiska_potrzebne(dane, u, klienci[u] * szczyt)  # obsługa dzień po dniu: obsada na szczyt
        maja = [s for s in istniejace if all(n in s.sprzet for n in dane.uslugi[u]["sprzet"])]
        for _ in range(max(0, potrzeba - len(maja))):
            if wolne:
                cel = wolne.pop(0).nr
            elif len(nowe_inst) < dane.maks_nowych_stanowisk and (miejsca is None or len(nowe_inst) < len(miejsca[KUCHNIA])):
                cel = nastepny
                nowe_inst.append(u)
                nastepny += 1
            else:
                break
            for n in dane.uslugi[u]["sprzet"]:
                d["sprzet_kup"].append({"typ": KUCHNIA, "nr": cel, "nazwa": n, "jakosc": q})
            d.setdefault("_obsada", []).append({"nr": cel, "zawod": dane.uslugi[u]["prowadzacy"]})
    rec = f.stanowiska_typu(KASA)
    potrzeba_rec = max(1, kasjerzy_potrzebni(dane, {u: k * szczyt for u, k in klienci.items()}))
    nowe_rec = min(dane.maks_nowych_stanowisk, max(0, potrzeba_rec - len(rec)))
    if miejsca is not None:
        nowe_rec = min(nowe_rec, len(miejsca[KASA]))
    for s in rec:  # stanowiska kupione wcześniej (np. w rundzie 1, gdy sprzęt był jeszcze niedostępny)
        for n in dane.sprzet_kasy:
            if n not in s.sprzet:
                d["sprzet_kup"].append({"typ": KASA, "nr": s.nr, "nazwa": n, "jakosc": q})
    for i in range(nowe_rec):
        nr = f.nowy_nr(KASA) + i
        for n in dane.sprzet_kasy:
            d["sprzet_kup"].append({"typ": KASA, "nr": nr, "nazwa": n, "jakosc": q})
    d["stanowiska"] = {KUCHNIA: len(nowe_inst), KASA: nowe_rec}
    return []
