"""Handel między drużynami (gra z lokalami, F3b.8, dane/zdarzenia/handel.yaml; notatka „Prawidła świata”).

Od rundy `od_rundy` drużyna może wystawić innej drużynie (nie botowi) ofertę sprzedaży towaru z magazynu albo
sprzętu ze stanowiska – decyzja `handel_oferty`: [{do, typ: "towar", zasob, jakosc, ilosc, cena}] albo
[{do, typ: "sprzet", stanowisko, nr, nazwa, cena}], cena brutto za całość. Oferta jest sprawdzana po zamknięciu
rundy r (po tygodniu sprzedaży): sprzedawca musi mieć towar w magazynie albo sprzęt na stanowisku (nie z najmu
lokalu, nie w leasingu), a cena mieści się w widełkach `cena_min`–`cena_maks` wartości (towar – koszt zakupu,
sprzęt – cena katalogowa). Adresat przyjmuje ofertę w rundzie r+1 (`handel_przyjmij`: [{id, nr}] – nr stanowiska
na sprzęt, bez niego pierwsze wolne). Transakcja idzie na początku przeliczenia r+1, przed zakupami i sprzedażą,
jeśli sprzedawca nadal ma towar, a kupujący – pieniądze na koncie. Nieprzyjęta oferta wygasa.

Faktury w KPiR obu stron: towar – u sprzedawcy przychód ze sprzedaży (kol. 7, VAT należny wg stawki składnika),
u kupującego zakup towarów (kol. 10, VAT naliczony); partie przechodzą z terminem przydatności (najkrótszy
pierwszy) i są dostarczane w poniedziałek rundy jak dostawa (miejsce w chłodni – silnik/swiezosc.py). Sprzęt –
u sprzedawcy jak sprzedaż sprzętu (pozostałe przychody, niezamortyzowana wartość w koszty), u kupującego jak zakup
(środek trwały od progu amortyzacji). Lokale – jeszcze nie (pytanie w PRACA_NOCNA.md).
"""
from __future__ import annotations

from . import rozliczenie as rz
from . import srodki_trwale as st_trwale
from . import swiezosc as sw
from .dane import Dane
from .finanse import Ksiega, Rachunek, ksieguj, vat_z_brutto
from .losowosc import strumien
from .model import Firma, OfertaHandlu, Partia, grosze
from .zaleglosci import zl

ZAKLADKA = "handel"
TOWAR, SPRZET = "towar", "sprzet"
SPRZEDAZ_TOWAROW = "Sprzedaż towarów dla drużyny"
EPS = 1e-6


def ustawienia(dane: Dane) -> dict | None:
    return (dane.zdarzenia or {}).get("handel")


def otwarty(dane: Dane, runda: int) -> bool:
    u = ustawienia(dane)
    return bool(u) and runda >= u["handel"]["od_rundy"]


def nazwa(f: Firma) -> str:
    return f.nazwa_wyswietlana or f.nazwa


def _sprzet_na_sprzedaz(f: Firma, typ: str, nr: int, nazwa_: str) -> int | None:
    """Jakość sprzętu, który drużyna może sprzedać (własny, nie z najmu lokalu, nie w leasingu); None – nie może."""
    st = f.stanowisko(typ, nr)
    if not st or nazwa_ not in st.sprzet or nazwa_ in st.sprzet_wynajmujacego:
        return None
    if any(lz.typ == typ and lz.nr == nr and lz.nazwa == nazwa_ for lz in f.leasingi):
        return None
    return st.sprzet[nazwa_]


def _wartosc_towaru(f: Firma, zasob: str, jakosc: int) -> float:
    """Koszt zakupu opakowania (średnia z magazynu, zł)."""
    k = f"{zasob}|{jakosc}"
    ile = f.magazyn.get(k, 0.0)
    return f.wartosc_magazynu_gr.get(k, 0) / 100 / ile if ile > EPS else 0.0


def _partie(f: Firma, zasob: str, jakosc: int) -> list[Partia]:
    """Partie towaru w kolejności wydawania: najkrótszy termin pierwszy (bez terminu – na końcu)."""
    return sorted((p for p in f.partie if p.zasob == zasob and p.jakosc == jakosc and p.ilosc > EPS),
                  key=lambda p: (p.termin is None, p.termin or "", p.dostawa))


def co(o: OfertaHandlu) -> str:
    if o.typ == TOWAR:
        return f"{o.zasob} {o.jakosc}★ × {o.ilosc:g} opak."
    return f"{o.nazwa} {o.jakosc}★ ({o.stanowisko} {o.nr})"


def stawka_vat(dane: Dane, o: OfertaHandlu) -> float:
    if o.typ == TOWAR:
        return rz.stawka_zasobu(dane, o.zasob) or 0.0
    return dane.podatki["vat"]["srodki_trwale"] if dane.podatki else 0.0


# --- wystawienie ofert (koniec rundy r) -----------------------------------------------------------------------

def _sprawdz(dane: Dane, firmy: dict[str, Firma], sprzedawca: str, o: dict, runda: int, i: int,
             w_ofertach: dict[str, float], sprzet_w_ofertach: set) -> tuple[OfertaHandlu | None, str]:
    u = ustawienia(dane)["handel"]
    f, do = firmy[sprzedawca], o.get("do")
    if do not in firmy or do == sprzedawca or firmy[do].bot:
        return None, "nie ma takiej drużyny (boty nie handlują)"
    try:
        cena = round(float(o.get("cena") or 0), 2)
    except (TypeError, ValueError):
        cena = 0.0
    if cena <= 0:
        return None, "podaj cenę"
    oferta = OfertaHandlu(id=f"{runda}-{sprzedawca}-{i + 1}", do=do, typ=o.get("typ") or "", cena_gr=grosze(cena),
                          runda=runda)
    if oferta.typ == TOWAR:
        try:
            oferta.zasob, oferta.jakosc, oferta.ilosc = o.get("zasob"), int(o.get("jakosc")), float(o.get("ilosc") or 0)
        except (TypeError, ValueError):
            return None, "niepoprawny towar"
        if oferta.zasob not in dane.zasoby or oferta.ilosc <= EPS:
            return None, "niepoprawny towar"
        k = f"{oferta.zasob}|{oferta.jakosc}"
        if f.magazyn.get(k, 0.0) - w_ofertach.get(k, 0.0) < oferta.ilosc - EPS:
            return None, f"na koniec rundy w magazynie było tylko {f.magazyn.get(k, 0.0) - w_ofertach.get(k, 0.0):g} opak."
        wartosc = _wartosc_towaru(f, oferta.zasob, oferta.jakosc) * oferta.ilosc
    elif oferta.typ == SPRZET:
        try:
            oferta.stanowisko, oferta.nr, oferta.nazwa = o.get("stanowisko"), int(o.get("nr")), o.get("nazwa")
        except (TypeError, ValueError):
            return None, "niepoprawny sprzęt"
        q = _sprzet_na_sprzedaz(f, oferta.stanowisko, oferta.nr, oferta.nazwa)
        klucz = (oferta.stanowisko, oferta.nr, oferta.nazwa)
        if q is None or oferta.nazwa not in dane.sprzet or klucz in sprzet_w_ofertach:
            return None, "tego sprzętu nie ma na stanowisku (sprzętu z najmu lokalu i w leasingu nie można sprzedać)"
        oferta.jakosc = q
        wartosc = dane.sprzet[oferta.nazwa]["ceny"][str(q)]
    else:
        return None, "można sprzedać towar albo sprzęt"
    lo, hi = round(u["cena_min"] * wartosc, 2), round(u["cena_maks"] * wartosc, 2)
    if not lo - EPS <= cena <= hi + EPS:
        return None, f"cena musi być od {zl(lo)} do {zl(hi)} (wartość {zl(round(wartosc, 2))})"
    if oferta.typ == TOWAR:   # rezerwacja dopiero po sprawdzeniu ceny – odrzucona oferta nie zajmuje towaru
        w_ofertach[k] = w_ofertach.get(k, 0.0) + oferta.ilosc
    else:
        sprzet_w_ofertach.add(klucz)
    return oferta, ""


def wystaw(dane: Dane, firmy: dict[str, Firma], sprzedawca: str, d: dict, runda: int) -> dict | None:
    """Oferty z decyzji `handel_oferty` – po tygodniu sprzedaży; zastępują oferty z poprzedniej rundy (wygasłe)."""
    u = ustawienia(dane)
    f = firmy[sprzedawca]
    f.oferty_handlu = []
    if not u:
        return None
    info = {"wystawione": [], "odrzucone": []}
    oferty = [] if f.bot else list(d.get("handel_oferty") or [])
    if oferty and runda < u["handel"]["od_rundy"]:
        info["odrzucone"].append({"co": "Oferty handlowe", "powod": f"handel między drużynami od rundy {u['handel']['od_rundy']}"})
        oferty = []
    w_ofertach, sprzet_w_ofertach = {}, set()
    for i, o in enumerate(oferty):
        opis = f"Oferta dla {nazwa(firmy[o['do']]) if o.get('do') in firmy else o.get('do')}"
        if len(f.oferty_handlu) >= u["handel"]["maks_ofert"]:
            info["odrzucone"].append({"co": opis, "powod": f"najwyżej {u['handel']['maks_ofert']} ofert w rundzie"})
            continue
        oferta, powod = _sprawdz(dane, firmy, sprzedawca, o, runda, i, w_ofertach, sprzet_w_ofertach)
        if oferta is None:
            info["odrzucone"].append({"co": opis, "powod": powod})
            continue
        f.oferty_handlu.append(oferta)
        info["wystawione"].append(publiczna(dane, firmy, sprzedawca, oferta))
    return info


def publiczna(dane: Dane, firmy: dict[str, Firma], sprzedawca: str, o: OfertaHandlu) -> dict:
    """Oferta do widoku sprzedawcy i adresata (z najkrótszym terminem towaru – świeżość)."""
    stawka = stawka_vat(dane, o)
    vat = vat_z_brutto(o.cena, stawka) if stawka else 0.0
    termin = None
    if o.typ == TOWAR and sprzedawca in firmy:
        termin = next((p.termin for p in _partie(firmy[sprzedawca], o.zasob, o.jakosc) if p.termin), None)
    return {"id": o.id, "od": sprzedawca, "od_nazwa": nazwa(firmy[sprzedawca]), "do": o.do,
            "do_nazwa": nazwa(firmy[o.do]) if o.do in firmy else o.do, "typ": o.typ, "co": co(o), "cena": o.cena,
            "stawka": stawka, "vat": vat, "netto": round(o.cena - vat, 2), "zasob": o.zasob, "jakosc": o.jakosc,
            "ilosc": o.ilosc, "nazwa": o.nazwa, "stanowisko": o.stanowisko, "nr": o.nr, "termin": termin,
            "runda": o.runda}


# --- przyjęcie ofert (początek rundy r+1) ------------------------------------------------------------------

def _ksiegi(dane: Dane, ksiegi: dict, rachunki: dict, n: str) -> tuple[Ksiega, Rachunek]:
    if n not in ksiegi:   # podgląd jednej drużyny: zapisy drugiej strony idą do pustej księgi
        ksiegi[n], rachunki[n] = Ksiega(vat=rz.reguly_vat(dane)), Rachunek()
    return ksiegi[n], rachunki[n]


def _przenies_towar(dane: Dane, s: Firma, k: Firma, o: OfertaHandlu, runda: int) -> None:
    zostalo, wziete = o.ilosc, []
    for p in _partie(s, o.zasob, o.jakosc):
        ile = min(zostalo, p.ilosc)
        sw._uszczknij(p, ile)
        wziete.append((p, ile))
        zostalo -= ile
        if zostalo <= EPS:
            break
    reszta = o.cena_gr   # u kupującego wartość partii = cena z faktury, rozdzielona wg ilości
    for j, (p, ile) in enumerate(wziete):
        w = reszta if j == len(wziete) - 1 else round(o.cena_gr * ile / o.ilosc)
        reszta -= w
        k.partie.append(Partia(zasob=p.zasob, jakosc=p.jakosc, ilosc=ile, wartosc_gr=w,
                               dostawa=dane.data_rundy(runda).isoformat(), termin=p.termin,
                               dostawca=f"Drużyna {nazwa(s)}", runda=runda))
    sw.uzgodnij(s)
    sw.uzgodnij(k)


def _wykonaj(dane: Dane, firmy: dict[str, Firma], sprzedawca: str, kupujacy: str, o: OfertaHandlu, p: dict,
             runda: int, ksiegi: dict, rachunki: dict) -> str:
    """Transakcja; zwraca powód odmowy albo pusty napis."""
    s, k = firmy[sprzedawca], firmy[kupujacy]
    if k.gotowka < o.cena - EPS:
        return f"{nazwa(k)} nie miał(a) na koncie {zl(o.cena)}"
    ks_s, rach_s = _ksiegi(dane, ksiegi, rachunki, sprzedawca)
    ks_k, rach_k = _ksiegi(dane, ksiegi, rachunki, kupujacy)
    stawka = stawka_vat(dane, o)
    if o.typ == TOWAR:
        if s.magazyn.get(f"{o.zasob}|{o.jakosc}", 0.0) < o.ilosc - EPS:
            return f"{nazwa(s)} nie ma już tyle towaru"
        _przenies_towar(dane, s, k, o, runda)
        ksieguj(s, ks_s, rach_s, f"{SPRZEDAZ_TOWAROW} {nazwa(k)}: {o.zasob}", o.cena, "przychod", stawka=stawka)
        ksieguj(k, ks_k, rach_k, f"Zakup towarów od drużyny {nazwa(s)}: {o.zasob}", o.cena, "towary", stawka=stawka)
        return ""
    q = _sprzet_na_sprzedaz(s, o.stanowisko, o.nr, o.nazwa)
    if q is None:
        return f"{nazwa(s)} nie ma już tego sprzętu na stanowisku"
    try:
        nr = int(p["nr"]) if p.get("nr") not in (None, "") else None
    except (TypeError, ValueError):
        nr = None
    cel = k.stanowisko(o.stanowisko, nr) if nr is not None else \
        next((x for x in k.stanowiska if x.typ == o.stanowisko and o.nazwa not in x.sprzet), None)
    if cel is None or o.nazwa in cel.sprzet:
        return f"{nazwa(k)} nie ma wolnego stanowiska ({o.stanowisko}) na {o.nazwa}"
    s.stanowisko(o.stanowisko, o.nr).sprzet.pop(o.nazwa)
    st_trwale.sprzedaj(s, f"{o.nazwa} ({o.stanowisko} {o.nr})", ks_s)
    ksieguj(s, ks_s, rach_s, f"Sprzedaż sprzętu: {o.nazwa} dla drużyny {nazwa(k)}", o.cena, "przychod_pozostaly",
            stawka=stawka)
    s.majatek -= dane.sprzet[o.nazwa]["ceny"][str(q)]   # majątek po cenie zakupu (jak przy sprzedaży sprzętu)
    cel.sprzet[o.nazwa] = q
    st_trwale.zakup(dane, k, ks_k, rach_k, f"Koszt zakupu: {o.nazwa} od drużyny {nazwa(s)}",
                    f"{o.nazwa} ({cel.typ} {cel.nr})", "sprzet", o.cena, runda, True)
    k.majatek += o.cena
    o.jakosc = q
    p["_nr"] = cel.nr
    return ""


def przyjmij(dane: Dane, firmy: dict[str, Firma], decyzje: dict[str, dict], runda: int, ksiegi: dict,
             rachunki: dict, ziarno: int | str) -> dict[str, dict]:
    """Transakcje z ofert przyjętych w tej rundzie (przed decyzjami drużyn). Zwraca firma → {transakcje, nieudane}."""
    wynik = {n: {"transakcje": [], "nieudane": []} for n in firmy}
    u = ustawienia(dane)
    if not u:
        return wynik
    oferty = {o.id: (n, o) for n, f in firmy.items() for o in f.oferty_handlu}
    for kupujacy in sorted(decyzje):
        if kupujacy not in firmy or firmy[kupujacy].bot:
            continue
        for p in decyzje[kupujacy].get("handel_przyjmij") or []:
            p = dict(p)
            n, o = oferty.get(str(p.get("id")), (None, None))
            if o is None or o.do != kupujacy or o.runda != runda - 1:
                wynik[kupujacy]["nieudane"].append({"co": f"Oferta {p.get('id')}",
                                                    "powod": "nie ma takiej oferty albo już wygasła"})
                continue
            oferty.pop(o.id)
            opis = publiczna(dane, firmy, n, o)
            powod = _wykonaj(dane, firmy, n, kupujacy, o, p, runda, ksiegi, rachunki)
            if powod:
                for strona in (n, kupujacy):
                    wynik[strona]["nieudane"].append({"co": f"{opis['co']} za {zl(o.cena)}", "powod": powod,
                                                      "id": o.id})
                continue
            T = ustawienia(dane)["teksty"]
            rng = strumien(ziarno, runda, "handel", o.id)
            tekst = T[int(rng.integers(len(T)))].format(sprzedawca=nazwa(firmy[n]), kupujacy=nazwa(firmy[kupujacy]),
                                                        co=co(o))
            wspolne = {"id": o.id, "co": co(o), "cena": o.cena, "vat": opis["vat"], "netto": opis["netto"],
                       "typ": o.typ, "tekst": tekst}
            wynik[n]["transakcje"].append({**wspolne, "strona": "sprzedaz", "z_kim": nazwa(firmy[kupujacy])})
            wynik[kupujacy]["transakcje"].append({**wspolne, "strona": "zakup", "z_kim": nazwa(firmy[n]),
                                                  **({"nr": p["_nr"]} if "_nr" in p else {})})
    return wynik


# --- raport, błędy i widok ----------------------------------------------------------------------------------

def raport(info_przyjecia: dict | None, info_wystawienia: dict | None) -> dict | None:
    if info_wystawienia is None:
        return None
    return {**(info_przyjecia or {"transakcje": [], "nieudane": []}), **info_wystawienia}


def bledy(info: dict | None) -> list[dict]:
    if not info:
        return []
    return [{"poziom": "czerwony", "zakladka": ZAKLADKA, "tekst": f"{o['co']}: {o['powod']}."}
            for o in info.get("odrzucone", []) + info.get("nieudane", [])]


def widok(dane: Dane, firmy_przed: dict[str, Firma], firma: str, runda: int, decyzja: dict | None) -> dict | None:
    """Zakładka Handel: oferty do drużyny (do przyjęcia w tej rundzie), wystawione w poprzedniej (czekają),
    towar i sprzęt na sprzedaż (stan na początku rundy), stanowiska na kupiony sprzęt."""
    u = ustawienia(dane)
    if not u or firma not in firmy_przed:
        return None
    fp = firmy_przed[firma]
    towary = []
    for k, ile in sorted(fp.magazyn.items()):
        zasob, q = k.split("|")[0], int(k.split("|")[1])
        if ile > EPS:
            towary.append({"zasob": zasob, "jakosc": q, "ilosc": round(ile, 3),
                           "wartosc": round(_wartosc_towaru(fp, zasob, q), 2),
                           "termin": next((p.termin for p in _partie(fp, zasob, q) if p.termin), None)})
    sprzet = [{"stanowisko": st.typ, "nr": st.nr, "nazwa": n, "jakosc": q, "katalog": dane.sprzet[n]["ceny"][str(q)]}
              for st in fp.stanowiska for n, q in st.sprzet.items()
              if n in dane.sprzet and _sprzet_na_sprzedaz(fp, st.typ, st.nr, n) is not None]
    return {"otwarty": runda >= u["handel"]["od_rundy"], "od_rundy": u["handel"]["od_rundy"],
            "limity": {k: u["handel"][k] for k in ("maks_ofert", "cena_min", "cena_maks")},
            "druzyny": [{"nazwa": n, "wyswietlana": nazwa(x)} for n, x in sorted(firmy_przed.items())
                        if n != firma and not x.bot],
            "przychodzace": [publiczna(dane, firmy_przed, n, o) for n, x in sorted(firmy_przed.items())
                             for o in x.oferty_handlu if o.do == firma and o.runda == runda - 1],
            "wystawione": [publiczna(dane, firmy_przed, firma, o) for o in fp.oferty_handlu if o.runda == runda - 1],
            "towary": towary, "sprzet": sprzet,
            "stanowiska": [{"typ": st.typ, "nr": st.nr, "sprzet": sorted(st.sprzet)} for st in fp.stanowiska],
            "decyzja": decyzja}
