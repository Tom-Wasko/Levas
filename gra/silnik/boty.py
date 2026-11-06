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
- jak człowiek – słaby, średni, dobry (Z5, tylko do pomiarów trudności): bez modelu popytu – prognoza z raportów
  poprzednich rund i potencjału lokalu z zakładki Klienci (_prognoza_czlowieka); wersje różnią się staraniem.
"""
from __future__ import annotations

import math
from copy import deepcopy

import numpy as np

from .dane import KASA, KUCHNIA, Dane
from .decyzje import kandydaci_firmy
from .ksiegowosc import biuro as bo
from .ksiegowosc.finanse import Ksiega, Rachunek
from .kuchnia import menu as mn
from .kuchnia.dostawcy import ceny_rundy, z_rynku
from .kuchnia.jakosc import mnoznik_wyposazenia
from .kuchnia.planowanie import (
    godziny_uslugi,
    kasjerzy_potrzebni,
    stanowiska_potrzebne,
    zamowienie_zasobow,
)
from .losowosc import strumien
from .ludzie import rynek_pracy as rp
from .ludzie import zadowolenie as zo
from .model import Firma, StanGry
from .nieruchomosci import lokale as lk
from .nieruchomosci import per_lokal as pl
from .pieniadze import banki as bk
from .rynek import popyt as pp
from .rynek import promocje as pm
from .rynek import reklama as rk
from .swiat import awarie as aw
from .swiat import zdarzenia as zd
from .wyniki.karta import KOLEJKI

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


def _podwyzki(dane: Dane, f: Firma, ust: dict) -> dict:
    """Pensja do progu zadowolenia z zapasem, najwyżej podwyzka_maks × preferowana (U20). Bot nie zna cech – liczy
    jak dla zwyczajnej osoby, więc materialiście czy marudzie podwyżka może nie wystarczyć."""
    u = zo.ustawienia(dane)
    if not u:
        return {}
    waga = dane.z["karta_wynikow"]["zadowolenie_pracownikow"]["placa_wzgledem_preferowanej"]
    zmiany = {}
    for p in sorted(f.pracownicy.values(), key=lambda p: p.id):
        if p.odchodzi or not p.niezadowolony or p.zadowolenie is None:
            continue
        brak = u["prog_zadowolenia"] + ust["zapas"] - p.zadowolenie
        nowa = min(p.pensja_preferowana * ust["podwyzka_maks"], p.pensja + p.pensja_preferowana * brak / waga)
        if nowa > p.pensja:
            zmiany[p.id] = {"pensja": round(nowa), "umowa": p.umowa, "premia": 0}
    return zmiany


def poziom(dane: Dane, konf: dict, nazwa: str) -> dict:
    """Ustawienia poziomu bota z konfiguracji gry (firmy[].poziom; bez niego – średni)."""
    klucz = next((f.get("poziom") for f in konf.get("firmy", []) if f["nazwa"] == nazwa), None) or DOMYSLNY_POZIOM
    return (dane.boty.get("poziomy") or {}).get(klucz) or {}


def przewaga_popytu(dane: Dane, konf: dict, nazwa: str) -> float:
    """Mnożnik atrakcyjności lokali firmy z poziomu bota (niemożliwy > 1); drużyny graczy – zawsze 1."""
    if not any(f["nazwa"] == nazwa and f.get("bot") for f in konf.get("firmy", [])):
        return 1.0
    return poziom(dane, konf, nazwa).get("przewaga_popytu", 1.0)


def _kredyt_na_lokal(dane: Dane, f: Firma, decyzja: dict, runda: int) -> dict | None:
    """Kredyt pod zastaw kupowanego lokalu (produkt banku z `od_lokalu` i `zastaw`) – najwięcej, ile bank da; None –
    żaden bank nie udzieli (np. ten kredyt już w spłacie)."""
    nowy = bk.nowy_lokal(dane, {"lokal": decyzja}, runda)
    for b, bank in bk.banki(dane).items():
        for p in bank["kredyty"]:
            if p.get("od_lokalu") and p.get("zastaw") and nowy:
                k = {"bank": b, "produkt": p["produkt"], "rund": p["maks_rund"], "zastaw": nowy["id"],
                     "kwota": float(int(min(p["maks_kwota"], p["zastaw"] * nowy["wartosc"])))}
                if not bk.powod_kredytu(dane, f, k, runda, nowy):
                    return k
    return None


def _kredyt_bez_historii(dane: Dane, f: Firma, brak: float, runda: int, wziete: list[dict] = ()) -> dict | None:
    """Dopłata do kupna lokalu (B6): kredyt bez zastawu i bez wymogu historii (np. „na start”) na brakującą kwotę
    (w górę do pełnego złotego, najwyżej maks_kwota) – najtańszy, którego bank udzieli; None – żaden albo za mały.
    wziete – kredyty już w decyzjach tej rundy (tego samego produktu bank nie da drugi raz)."""
    kwota = float(math.ceil(brak))
    oferty = sorted(((p["oprocentowanie"], b, p) for b, bank in bk.banki(dane).items() for p in bank["kredyty"]
                     if not p.get("historia") and not p.get("zastaw") and not p.get("od_lokalu")
                     and p["maks_kwota"] >= kwota), key=lambda x: (x[0], x[1]))
    for _, b, p in oferty:
        k = {"bank": b, "produkt": p["produkt"], "rund": p["maks_rund"], "kwota": kwota}
        if not any((x["bank"], x["produkt"]) == (b, p["produkt"]) for x in wziete)                 and not bk.powod_kredytu(dane, f, k, runda):
            return k
    return None


def _kredyty_na_kupno(dane: Dane, f: Firma, lok: dict, dec: dict, runda: int, rezerwa: float,
                      przebicie: float = 1.0) -> list[dict] | None:
    """Kredyty na kupno lokalu: pod jego zastaw, a gdy po wejściu (działka – z budową w ratach) nie zostaje
    `rezerwa` gotówki – dopłata bez historii. None – nie stać nawet z nimi."""
    k = _kredyt_na_lokal(dane, f, dec, runda)
    kredyty = [k] if k else []
    wejscie = lk.koszt_wejscia(dane, lok, "kupno", lok["cena"] * przebicie)         + lok.get("koszt_budowy", 0)   # działka: budowa w ratach w kolejnych rundach (lokale.py)
    brak = rezerwa + wejscie - f.gotowka - sum(x["kwota"] for x in kredyty)
    if brak > 0:
        dop = _kredyt_bez_historii(dane, f, brak, runda)
        if not dop:
            return None
        kredyty.append(dop)
    return kredyty


def _wybierz_lokal(dane: Dane, stan: StanGry, nazwa: str, strategia_klucz: str, runda: int, konf: dict,
                   min_kuchnia: int = 0, strefy: list[str] | None = None, wybor: dict | None = None,
                   f: Firma | None = None) -> tuple[dict | None, dict | None]:
    """Lokal wg strategii: tani – najniższy czynsz (cena), premium – Stare Miasto i Centrum, inni – środek stawki.
    Losowanie spośród trzech najlepszych (ziarno gry), żeby boty nie biły się zawsze o ten sam lokal.
    min_kuchnia – najmniej miejsc w kuchni (planujący bot; bez takich lokali – każdy); strefy – tylko lokale w tych
    strefach (strategia: strefy, np. pomiar w balans/warianty.py; bez wolnych – każda strefa). wybor – parametr
    strategii `lokal` (B6): `typy` lokali (bez – gotowy), `forma` (najem / kupno – na kredyt pod zastaw lokalu, gdy
    po wejściu zostaje `rezerwa` gotówki; bez takich lokali – gotowy w najmie), `przebicie` – oferta w licytacji
    × cena wywoławcza. Zwraca (decyzja lokal, kredyty na kupno – pusta lista przy najmie)."""
    w = wybor or {}
    forma = w.get("forma", "najem")
    pole = "czynsz" if forma == "najem" else "cena"
    wolne = [lok for lok in lk.dostepne(dane, runda, lk.zajete(stan.firmy), len(stan.firmy))
             if lok["typ"] in w.get("typy", ["gotowy"]) and lok.get(pole)]
    if forma == "kupno" and f is not None:
        wolne = [lok for lok in wolne if _kredyty_na_kupno(dane, f, lok, {"id": lok["id"], "forma": "kupno"}, runda,
                                                            w.get("rezerwa", 0), w.get("przebicie", 1.0)) is not None]
    if not wolne and wybor:
        return _wybierz_lokal(dane, stan, nazwa, strategia_klucz, runda, konf, min_kuchnia, strefy)
    if strefy:   # B6: strefa przed kuchnią – inaczej pomiar strefy bez lokalu z min_kuchnia mierzył inną strefę
        wolne = [lok for lok in wolne if lok["strefa"] in strefy] or wolne
    wolne = [lok for lok in wolne if lok["miejsca"][KUCHNIA] >= min_kuchnia] or wolne
    if not wolne:
        return None, []
    if strategia_klucz == "tani":
        wolne.sort(key=lambda lok: lok[pole])
    elif strategia_klucz == "premium":
        wolne.sort(key=lambda lok: (lok["strefa"] not in ("stare_miasto", "centrum"), -lok["miejsca"]["kuchnia"], lok[pole]))
    else:
        sr = sorted(lok[pole] for lok in wolne)[len(wolne) // 2]
        wolne.sort(key=lambda lok: (abs(lok[pole] - sr), lok["id"]))
    najlepsze = wolne[:3]
    lok = najlepsze[int(strumien(konf["ziarno"], runda, "lokal", nazwa).integers(len(najlepsze)))]
    dec = {"id": lok["id"], "forma": forma}
    if w.get("przebicie", 1.0) > 1.0 and runda >= dane.mapa["zasady"]["licytacje_od_rundy"]:
        dec["oferta"] = round(lok[pole] * w["przebicie"], 2)
    kredyty = _kredyty_na_kupno(dane, f, lok, dec, runda, w.get("rezerwa", 0), w.get("przebicie", 1.0))         if forma == "kupno" and f is not None else None
    return dec, kredyty or []


def _przejecie(dane: Dane, stan: StanGry, f: Firma, nazwa: str, st: dict, runda: int) -> dict | None:
    """B6: kupno budynku z najemcą – wykup własnego lokalu w najmie (strategia `wykup`) albo budynku, który
    wynajmuje rywal (`przejecie`), gdy po zakupie zostaje `rezerwa` gotówki; najtańszy z możliwych."""
    if runda < dane.mapa["zasady"]["przejecia_od_rundy"]:
        return None
    firmy = [f] if st.get("wykup") else []
    firmy += [g for n, g in stan.firmy.items() if n != nazwa] if st.get("przejecie") else []
    kandydaci = [(c, x.id) for g in firmy for x in g.lokale
                 if x.forma == "najem" and not x.wlasciciel and x.najem_do is None
                 and (c := dane.lokale[x.id].get("cena"))
                 and f.gotowka - c >= st["wykup" if g is f else "przejecie"]["rezerwa"]]
    return {"id": min(kandydaci)[1]} if kandydaci else None


def _wez_lokal(dane: Dane, stan: StanGry, f: Firma, d: dict, dec: dict, kredyty: list[dict] | None,
               runda: int) -> Firma:
    """Decyzja o lokalu (i kredytach na jego kupno) w decyzjach bota; zwraca kopię firmy z tym lokalem – dalsze
    decyzje liczone tak, jakby lokal już był. Kredyt bez zastawu bank wypłaca przed zakupem, pod zastaw kupowanego
    lokalu – razem z zakupem (silnik/pieniadze/banki.py: kredyty_na_lokal)."""
    d["lokal"] = dec
    kredyty = kredyty or []
    if kredyty:
        d.setdefault("kredyty_wez", []).extend(kredyty)
    f = deepcopy(f)
    pod_zastaw = sum(k["kwota"] for k in kredyty if k.get("zastaw"))
    f.gotowka += sum(k["kwota"] for k in kredyty if not k.get("zastaw"))
    lk.wybierz(dane, f, dec, runda, lk.zajete(stan.firmy), Ksiega(), Rachunek(), finansowanie=pod_zastaw)
    f.gotowka += pod_zastaw
    return f


def _kampanie(dane: Dane, f: Firma, st: dict, runda: int, ust: dict) -> list[dict]:
    """Kampanie ze strategii w strefach własnych lokali: dostępne, po przerwie od poprzedniej w tym kanale i strefie,
    emisje_kampanii emisji (najwyżej maks_emisji kanału), a po zapłacie zostaje bufor gotówki."""
    strefy = sorted({dane.lokale[lok.id]["strefa"] for lok in f.lokale})
    wynik, wydatki = [], 0.0
    for x in st.get("kampanie", []) if strefy else []:
        a, _, k = x.partition("/")
        kan = rk.kanal(dane, a, k)
        if kan is None or kan["od_rundy"] > runda:
            continue
        for s in [None] if kan["zasieg"] == "miasto" else [z for z in strefy if z in rk.strefy_kanalu(dane, kan)]:
            emisje = min(ust["emisje_kampanii"], kan["maks_emisji"])
            koszt = rk.brutto(dane, rk.koszt(dane, kan, s, emisje))
            ostatnia = max((x.do_rundy for x in f.kampanie if (x.agencja, x.kanal, x.strefa) == (a, k, s)), default=None)
            if (ostatnia is not None and runda - ostatnia <= ust["przerwa_kampanii"]) \
                    or f.gotowka - wydatki - koszt < ust["bufor_kampanii"]:
                continue
            wynik.append({"agencja": a, "kanal": k, "strefa": s, "emisje": emisje})
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


def _przechowywanie(dane: Dane) -> list[str]:
    """Sprzęt kuchni z miejscem na składniki (szafa chłodnicza, zamrażarka – sprzet.yaml `przechowywanie`)."""
    return [n for n, s in dane.sprzet.items() if s.get("przechowywanie")]


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
        for n in _przechowywanie(dane):   # chłodnia i zamrażarka – jak w zestawie gotowego lokalu (B6)
            if miejsca and not any(n in sp for _, sp, _ in miejsca):
                miejsca[0][1][n] = q
                kup.append({"typ": KUCHNIA, "nr": miejsca[0][0], "nazwa": n, "jakosc": q})
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
                         "wyposazenie": wyp, "rozruch": pp.rozruch(dane, lok, r_sprz),
                         "zadowolenie": pp.zadowolenie_lokalu(dane, lok)} for u in oferta}
            for lok in f.lokale if lok.dziala_od <= r_sprz}
    return pp.prognoza(dane, r_sprz, {**konkurencja, nazwa: moje}, nazwa)


def _korekta_prognozy(stan: StanGry, nazwa: str, runda: int, granice: list[float]) -> float:
    """Błąd modelu popytu, którym bot trudny poprawia prognozę, w granicach z danych. W raporcie rundy
    „prognoza” to oferta bota, a ta zawiera już korektę z tamtej rundy – stąd korekta narastająco (B3: sam
    stosunek popyt / oferta przy stałym błędzie modelu skakał co rundę między błędem a 1)."""
    sp = (stan.wyniki.get(runda - 1, {}).get(nazwa) or {}).get("sprzedaz", {}).values()
    prog = sum(v["prognoza"] for v in sp if v["prognoza"])
    if not prog:
        return 1.0
    k = _korekta_prognozy(stan, nazwa, runda - 1, granice) * sum(v["popyt"] for v in sp if v["prognoza"]) / prog
    return min(max(granice), max(min(granice), k))


def _prognoza_czlowieka(dane: Dane, stan: StanGry, f: Firma, nazwa: str, oferta: list[str], runda: int,
                        r_sprz: int, konkurencja: dict, pc: dict) -> dict:
    """Prognoza bota „jak człowiek” (Z5) tylko z tego, co drużyna widzi w zakładkach: popyt dań w lokalach
    z raportów `pc["rund"]` ostatnich rund (średnia), przy `pc["pule"]` razy pula strefy w rundzie sprzedaży
    / pula w tamtej rundzie (zakładka Klienci). Lokal albo danie bez historii – potencjał lokalu jak w zakładce
    Klienci (2★, ceny preferowane strefy, obecna konkurencja). Format jak pp.prognoza."""
    lokale = [lok.id for lok in f.lokale if lok.dziala_od <= r_sprz]
    pule: dict[int, dict] = {}

    def pula(r: int, z: str) -> float:
        if r not in pule:
            pule[r] = pp.pule(dane, r)
        return sum(float(pule[r][z][u].sum()) for u in oferta)

    historia: dict[tuple[str, str], list[float]] = {}
    for r in range(runda - 1, max(0, runda - 1 - pc["rund"]), -1):
        for x in ((stan.wyniki.get(r, {}).get(nazwa) or {}).get("klienci") or {}).get("lokale", []):
            if x["id"] not in lokale:
                continue
            z = dane.lokale[x["id"]]["strefa"]
            skala = pula(r_sprz, z) / pula(r, z) if pc.get("pule") and pula(r, z) else 1.0
            for u, n in x["dania"].items():
                if u in oferta:
                    historia.setdefault((x["id"], u), []).append(n * skala)
    potencjal = None
    wynik: dict[str, dict[str, float]] = {}
    for lok in lokale:
        for u in oferta:
            if h := historia.get((lok, u)):
                n = sum(h) / len(h)
            else:
                if potencjal is None:
                    moje = {x: {v: {"strefa": dane.lokale[x]["strefa"], "jakosc": (2, 2, 2), "cena":
                                    dane.uslugi[v]["cena_preferowana"]
                                    * dane.mapa["popyt"]["strefy"][dane.lokale[x]["strefa"]]["cena"]}
                                for v in oferta} for x in lokale}
                    potencjal = pp.prognoza(dane, r_sprz, {**konkurencja, nazwa: moje}, nazwa)["lokale"]
                n = potencjal.get(lok, {}).get(u, 0.0)
            wynik.setdefault(lok, {})[u] = round(n, 1)
    dni = None
    for lok, dania in wynik.items():   # rozkład na dni – wagi dni strefy z zakładki Klienci
        w = pp.wagi_dni(dane, dane.lokale[lok]["strefa"], pp.dni_rundy(dane, r_sprz))
        porcje = sum(dania.values()) * w / w.sum() if w.sum() > 0 else w
        dni = porcje if dni is None else dni + porcje
    dania_firmy = {u: round(sum(x.get(u, 0.0) for x in wynik.values()), 1) for u in oferta}
    return {"dania": dania_firmy, "lokale": wynik,
            "dni": [round(float(x), 1) for x in dni] if dni is not None else []}


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
        dec, kredyty = _wybierz_lokal(dane, stan, nazwa, strategia_klucz, runda, konf,
                                     st.get("min_kuchnia", 0) if planuje else 0, st.get("strefy"), st.get("lokal"), f)
        if dec is None:
            d["lokal"] = None
            if not f.lokale:
                return d
        else:
            f = _wez_lokal(dane, stan, f, d, dec, kredyty, runda)
    if not d.get("lokal") and (pr := _przejecie(dane, stan, f, nazwa, st, runda)):
        d["przejecie"] = pr
        f = deepcopy(f)
        f.gotowka -= dane.lokale[pr["id"]]["cena"]   # dalsze zakupy z gotówki po kupnie budynku
    if (p := st.get("przejecie")) and p.get("wypowiedz"):
        d["wypowiedz"] = [{"id": b.id, "ulepszenia": p.get("ulepszenia", "zatrzymaj")} for b in f.budynki
                          if (u := pl.lokal(stan.firmy[b.najemca], b.id)) and u.najem_do is None]
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
    glowny = pl.glowny(f, runda)   # wyposażenie bot kupuje do lokalu głównego (Z2)
    wyp = mnoznik_wyposazenia(dane, pl.lista(f, glowny, "wyposazenie") if glowny else f.wyposazenie)
    ceny = {u: _cena(dane, st, stan, u, runda) for u in oferta}
    szczyt, udzialy_dni, plan = 1.0, None, None
    r_sprz = max(runda, 2)
    konkurencja = pp.oferty_konkurencji(dane, stan, r_sprz, nazwa)
    korekta = _korekta_prognozy(stan, nazwa, runda, pz["korekta_prognozy"]) if pz.get("korekta_prognozy") else 1.0
    blad = pz.get("blad_prognozy", 0)
    if blad:   # łatwy: prognoza „na oko”
        korekta *= 1 + float(strumien(konf["ziarno"], runda, "bot", nazwa, "prognoza").uniform(-blad, blad))

    czlowiek = pz.get("prognoza_czlowieka")

    def prognoza_cen(c: dict[str, float]) -> tuple[dict, dict]:
        if czlowiek:   # „jak człowiek”: z raportów poprzednich rund, nie z modelu popytu
            prog = _prognoza_czlowieka(dane, stan, f, nazwa, oferta, runda, r_sprz, konkurencja, czlowiek)
        else:
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
                pr, plk = prognoza_cen(c)
                pn = _plan_firmy(dane, f, plk, r_sprz, runda, ekonomia(c))
                if (mz := _marza(dane, pn, ekonomia(c))) > najlepsza[0]:
                    najlepsza = (mz, c, pr, plk, pn)
            _, ceny, prog, prog_lok, plan = najlepsza
        drugi = pz.get("kolejny_lokal")
        if drugi and "lokal" not in d and plan["lokale"] \
                and all(p["czesc"] < drugi["obsluga"] for p in plan["lokale"].values()) \
                and f.gotowka > drugi["gotowka"] and len(f.lokale) < drugi["maks_lokali"] \
                and runda >= lk.runda_nowego_lokalu(dane, f) and all(x.dziala_od <= runda for x in f.lokale):
            dec, kredyty = _wybierz_lokal(dane, stan, nazwa, strategia_klucz, runda, konf, st.get("min_kuchnia", 0),
                                         st.get("strefy"), {**st.get("lokal", {}), **drugi.get("lokal", {})}, f)
            if dec is not None:
                f = _wez_lokal(dane, stan, f, d, dec, kredyty, runda)
                prog, prog_lok = prognoza_cen(ceny)
                plan = _plan_firmy(dane, f, prog_lok, r_sprz, runda, ekonomia(ceny))
        _zatrudnieni(f, plan)
        klienci = {u: plan["sprzedaz"].get(u, 0.0) for u in oferta}   # zamówienia: tyle, ile kuchnia sprzeda
        udzialy_dni = plan["dni"]
    else:
        klienci = {u: prog["dania"].get(u, 0.0) * korekta * st["pokrycie"] for u in oferta}
        if pz.get("zamowienia_ze_sprzedazy"):   # człowiek: kuchnia nie nadążyła tydzień temu – zamawia mniej
            sp = (stan.wyniki.get(runda - 1, {}).get(nazwa) or {}).get("sprzedaz", {})
            klienci = {u: min(k, sp[u]["sprzedaz"] * pz["zamowienia_ze_sprzedazy"])
                       if sp.get(u, {}).get("przyczyna") in KOLEJKI else k for u, k in klienci.items()}
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

    # zatrudnienie (od tygodnia z harmonogramu, domyślnie 1 – U23): stanowiska bez pracownika, które mają (albo dostają) sprzęt
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
    if pz.get("dba_o_ludzi"):   # U20: podwyżka dla niezadowolonych (łatwy ich ignoruje)
        d["zmiany"] = _podwyzki(dane, stan.firmy[nazwa], pz["dba_o_ludzi"])

    # zasoby na przewidywanych klientów
    if "dostawcy" in odbl:
        ceny_d = ceny_rundy(dane, konf["ziarno"], runda, konf.get("ceny_dostawcow", "dane"))
        ceny_d = {k: v for k, v in ceny_d.items() if not z_rynku(dane, k)   # Z4: boty nie kupują w Auchan
                  and (st.get("dostawcy") is None or k in st["dostawcy"])}
        qz = st.get("jakosc_zasobow") or q
        zapas = st.get("zapas_zasobow") or ust["zapas_zasobow"]
        if len(f.lokale) > 1 and prog_lok:
            # magazyn każdego lokalu osobno (Z2): zamówienie z zapasów lokalu na jego część klientów (B6: wcześniej
            # z zapasów całej firmy, dzielone potem wg prognozy – nadmiar w jednym lokalu „pokrywał” braki w drugim,
            # więc w drugim brakowało towaru, a w pierwszym się psuł)
            waga = {x: {u: n * (plan["lokale"][x]["czesc"] if plan is not None else 1.0) for u, n in v.items()}
                    for x, v in prog_lok.items()}
            d["zamowienia"] = []
            for x, wx in waga.items():
                kx = {u: k * wx.get(u, 0.0) / s for u, k in klienci.items()
                      if (s := sum(w.get(u, 0.0) for w in waga.values())) > 0}
                d["zamowienia"] += [{**z, "lokal": x} for z in zamowienie_zasobow(
                    dane, pl.widok(f, x), kx, ceny_d, qz, zapas, udzialy_dni, dane.data_rundy(runda),
                    bool(st.get("dyskonty")))]
        else:
            d["zamowienia"] = zamowienie_zasobow(dane, f, klienci, ceny_d, qz, zapas, udzialy_dni,
                                                 dane.data_rundy(runda), bool(st.get("dyskonty")))

    # inwestycje dodatkowe wg strategii (gdy jest gotówka): po zakupach zostaje bufor gotówki (B5: wcześniej bot
    # kupował od razu cały komplet i wpadał w debet)
    bufor = f.gotowka > ust["bufor_gotowki"]
    budzet = [f.gotowka - ust["bufor_gotowki"]]
    if "inwestycje_wyposazenie" in odbl and bufor:
        d["wyposazenie_kup"] = _w_budzecie(sorted(dane.pozycje("wyposazenie").values(), key=lambda p: -p["procent"]),
                                           runda, f.wyposazenie, st["wyposazenie"], budzet)
    if "hr_udogodnienia" in odbl and bufor:
        d["udogodnienia_kup"] = _w_budzecie(sorted(dane.pozycje("udogodnienia").values(),
                                                   key=lambda p: p["cena"] / p["procent"]),
                                            runda, f.udogodnienia, st["udogodnienia"], budzet)
    bufor = budzet[0] > 0
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
    if (ls := st.get("leasing")) and d.get("sprzet_kup") and f.gotowka < ls["gotowka"]:
        # B6: przy małej gotówce nowy sprzęt w leasingu (bank z najtańszym leasingiem) zamiast zakupu
        bank = bk.najlepsze(dane)["leasing"]
        d["leasing_wez"] = [{**x, "bank": bank, "rund": ls["rund"]} for x in d["sprzet_kup"]]
        d["sprzet_kup"] = []
    if plan is not None and d.get("sprzet_kup") and "inwestycje_sprzet" in odbl:
        # B6: sprzęt ponad gotówkę (lokal bez zestawu – cały komplet naraz), gdy po zakupach zostałoby mniej niż
        # rezerwa_po_sprzecie – wcześniej bot wpadał w debet ponad limit i bank blokował mu inwestycje na kilka rund.
        # Najpierw leasing (najdroższe pozycje, bank z najtańszym leasingiem, najkrótszy okres) – nie liczy się do
        # wskaźnika zadłużenia karty; resztę braku kredytem bez historii
        cena = {id(x): dane.sprzet[x["nazwa"]]["ceny"][str(x["jakosc"])] for x in d["sprzet_kup"]}
        brak = sum(cena.values()) + ust.get("rezerwa_po_sprzecie", 0.0) - f.gotowka   # f – z lokalem (_wez_lokal)
        bank = bk.banki(dane).get(bk.najlepsze(dane)["leasing"])
        for x in sorted(d["sprzet_kup"], key=lambda x: -cena[id(x)]) if bank and brak > 0 else []:
            d.setdefault("leasing_wez", []).append({**x, "bank": bank["nazwa"], "rund": min(bank["leasing"]["rund"])})
            d["sprzet_kup"].remove(x)
            brak -= cena[id(x)] * (1 - bank["leasing"]["wplata"])
            if brak <= 0:
                break
        if brak > 0 and (k := _kredyt_bez_historii(dane, f, brak, runda, d.get("kredyty_wez", []))):
            d.setdefault("kredyty_wez", []).append(k)
    if aw.dane_wypadkow(dane):   # polisy wg strategii – od kiedy ma lokal
        d["polisy"] = list(st.get("polisy", [])) if f.lokale else []
    if st.get("higiena"):   # poziom higieny lokali wg strategii (dane/zdarzenia/urzad.yaml)
        d["higiena"] = st["higiena"]
    return d


def _w_budzecie(pozycje: list[dict], runda: int, ma: list[str], ile: int, budzet: list[float]) -> list[str]:
    """Pozycje do kupienia w podanej kolejności, dostępne, jeszcze niekupione, najwyżej do `ile` sztuk łącznie,
    póki starcza budżetu (budzet[0] maleje o ich ceny)."""
    wynik = []
    for p in pozycje:
        if len(ma) + len(wynik) >= ile:
            break
        if p["od_rundy"] <= runda and p["nazwa"] not in ma and p["cena"] <= budzet[0]:
            wynik.append(p["nazwa"])
            budzet[0] -= p["cena"]
    return wynik


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
