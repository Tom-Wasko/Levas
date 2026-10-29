"""Świeżość składników w grze z lokalami (krok F3a.5; notatki/Menu i składniki.md).

Dane: zasoby.yaml – przechowywanie (chlodnia, zamrazarka, suche), termin_dni, miejsce_l, zamiennik_dla, kara_jakosci;
sprzet.yaml – przechowywanie i pojemnosc_l sprzętu (szafa chłodnicza, zamrażarka).

Zasady:
- każde zamówienie to partia z dniem dostawy (zamowienia[].dzien, 0 = poniedziałek rundy); termin = dzień dostawy
  + termin_dni − 1 (bułka z poniedziałku – 2 dni – ląduje w koszu we wtorek wieczorem),
- dzień w lokalu: rano dostawy (do chłodni i zamrażarki wchodzi tyle, ile się zmieści – reszta jedzie do wynajętej
  chłodni: zalozenia.yaml magazyn.wynajem_zl_za_litr za litr nadmiaru, termin krótszy o wynajem_skrocenie_terminu_dni;
  bez tych założeń – jak w F3a.5 – reszta to strata), w ciągu dnia klienci zużywają najpierw partie z najkrótszym
  terminem (FIFO), wieczorem przeterminowane partie idą do kosza,
- magazyn jest wspólny dla lokali firmy, pojemność = suma pojemności sprzętu ze wszystkich stanowisk; suche – bez limitu,
- zamiennik (np. mrożona pita) jest używany, gdy zabraknie składnika podstawowego; danie z zamiennikiem ma jakość
  składnika niższą o kara_jakosci gwiazdek.
`Firma.magazyn` zostaje sumą partii („zasób|jakość” → opakowania) – reszta silnika (jakość, limity) liczy z niego.
"""
from __future__ import annotations

from datetime import date, timedelta

from ..dane import Dane
from ..model import Firma, Partia, grosze

EPS = 1e-9
CHLODZONE = ("chlodnia", "zamrazarka")   # przechowywanie z limitem miejsca (suche – bez limitu)
JAKOSCI = (1, 2, 3)


def zamienniki(dane: Dane, nazwa: str) -> list[str]:
    return [z for z, x in dane.zasoby.items() if x.get("zamiennik_dla") == nazwa]


def przelicznik(dane: Dane, zamiennik: str) -> float:
    """Ile opakowań składnika podstawowego daje jedno opakowanie zamiennika."""
    z = dane.zasoby[zamiennik]
    return z["opakowanie"] / dane.zasoby[z["zamiennik_dla"]]["opakowanie"]


def ilosc(magazyn: dict, nazwa: str) -> float:
    return sum(magazyn.get(f"{nazwa}|{q}", 0.0) for q in JAKOSCI)


def dostepne(dane: Dane, magazyn: dict, nazwa: str) -> float:
    """Zapas składnika razem z zamiennikami – w opakowaniach składnika podstawowego."""
    return ilosc(magazyn, nazwa) + sum(ilosc(magazyn, z) * przelicznik(dane, z) for z in zamienniki(dane, nazwa))


def jakosc_skladnika(dane: Dane, magazyn: dict, nazwa: str) -> float | None:
    """Średnia gwiazdek zapasu ważona ilością; zamiennik – gwiazdki minus kara_jakosci. None – brak zapasu."""
    suma, waga = 0.0, 0.0
    for z, mnoznik, kara in [(nazwa, 1.0, 0.0)] + [(z, przelicznik(dane, z), dane.zasoby[z].get("kara_jakosci", 0.0))
                                                   for z in zamienniki(dane, nazwa)]:
        for q in JAKOSCI:
            ile = magazyn.get(f"{z}|{q}", 0.0) * mnoznik
            suma += ile * (q - kara)
            waga += ile
    return suma / waga if waga > EPS else None


def termin(dane: Dane, zasob: str, dostawa: date) -> date | None:
    dni = dane.zasoby[zasob].get("termin_dni")
    return dostawa + timedelta(days=dni - 1) if dni else None


def nowa_partia(dane: Dane, zasob: str, jakosc: int, ilosc_: float, cena: float, dostawa: date, dostawca: str,
                runda: int) -> Partia:
    t = termin(dane, zasob, dostawa)
    return Partia(zasob=zasob, jakosc=jakosc, ilosc=ilosc_, wartosc_gr=grosze(ilosc_ * cena), dostawa=dostawa.isoformat(),
                  termin=t.isoformat() if t else None, dostawca=dostawca, runda=runda)


def miejsce(dane: Dane, p: Partia) -> float:
    return p.ilosc * dane.zasoby[p.zasob].get("miejsce_l", 0.0)


def pojemnosc(dane: Dane, firma: Firma) -> dict[str, float]:
    """Litry chłodni i zamrażarki: suma sprzętu z przechowywaniem na stanowiskach firmy."""
    wynik = {t: 0.0 for t in CHLODZONE}
    for st in firma.stanowiska:
        for n, q in st.sprzet.items():
            s = dane.sprzet.get(n, {})
            if s.get("przechowywanie"):
                wynik[s["przechowywanie"]] += s["pojemnosc_l"][str(q)]
    return wynik


def na_stanie(firma: Firma, dzien: str | None = None) -> list[Partia]:
    """Partie dostarczone do dnia `dzien` (ISO; None – wszystkie)."""
    return [p for p in firma.partie if dzien is None or p.dostawa <= dzien]


def wynajem(dane: Dane) -> dict | None:
    """Wynajęta chłodnia (założenia magazyn.*): {"zl_za_litr", "skrocenie_dni"}; None – dane bez niej."""
    m = dane.z.get("magazyn") or {}
    if "wynajem_zl_za_litr" not in m:
        return None
    return {"zl_za_litr": m["wynajem_zl_za_litr"], "skrocenie_dni": m["wynajem_skrocenie_terminu_dni"]}


def zajete(dane: Dane, firma: Firma, dzien: str | None = None) -> dict[str, float]:
    """Litry zajęte we własnej chłodni i zamrażarce (bez partii w wynajętej chłodni)."""
    wynik = {t: 0.0 for t in CHLODZONE}
    for p in na_stanie(firma, dzien):
        if p.wynajem:
            continue
        t = dane.zasoby[p.zasob].get("przechowywanie", "suche")
        if t in wynik:
            wynik[t] += miejsce(dane, p)
    return wynik


def uzgodnij(firma: Firma, dzien: str | None = None) -> None:
    """Magazyn = suma partii na stanie (zmiana w miejscu – widoki lokali dzielą słownik z firmą)."""
    firma.partie[:] = [p for p in firma.partie if p.ilosc > EPS]
    firma.magazyn.clear()
    firma.wartosc_magazynu_gr.clear()
    for p in na_stanie(firma, dzien):
        k = f"{p.zasob}|{p.jakosc}"
        firma.magazyn[k] = firma.magazyn.get(k, 0.0) + p.ilosc
        firma.wartosc_magazynu_gr[k] = firma.wartosc_magazynu_gr.get(k, 0) + p.wartosc_gr


def _strata(p: Partia, ile: float, wartosc_gr: int, powod: str, dzien: str) -> dict:
    return {"data": dzien, "zasob": p.zasob, "jakosc": p.jakosc, "ilosc": round(ile, 3), "wartosc": wartosc_gr / 100,
            "powod": powod}


def _uszczknij(p: Partia, ile: float) -> int:
    """Zdejmuje `ile` opakowań z partii, zwraca ich wartość w groszach (ostatnia część – cała reszta wartości)."""
    wart = p.wartosc_gr if p.ilosc - ile <= EPS else round(p.wartosc_gr * ile / p.ilosc)
    p.ilosc -= ile
    p.wartosc_gr -= wart
    return wart


def _do_wynajmu(dane: Dane, p: Partia, ile: float, dzien: str, wyn: dict) -> tuple[Partia, dict]:
    """Część partii do wynajętej chłodni: nowa partia z terminem krótszym o skrocenie_dni (nie wcześniej niż dziś)."""
    termin_ = p.termin
    if termin_:
        termin_ = max(dzien, (date.fromisoformat(termin_) - timedelta(days=wyn["skrocenie_dni"])).isoformat())
    nowa = Partia(zasob=p.zasob, jakosc=p.jakosc, ilosc=ile, wartosc_gr=_uszczknij(p, ile), dostawa=p.dostawa,
                  termin=termin_, dostawca=p.dostawca, runda=p.runda, wynajem=True)
    litry = miejsce(dane, nowa)
    return nowa, {"data": dzien, "zasob": p.zasob, "jakosc": p.jakosc, "ilosc": round(ile, 3), "litry": round(litry, 1),
                  "koszt": round(litry * wyn["zl_za_litr"], 2), "termin": termin_,
                  "przechowywanie": dane.zasoby[p.zasob]["przechowywanie"]}


def przyjmij(dane: Dane, firma: Firma, dzien: str) -> tuple[dict[str, float], list[dict], list[dict]]:
    """Ranne dostawy dnia: do chłodni i zamrażarki tyle, ile się zmieści, reszta – do wynajętej chłodni (bez niej
    w danych – strata). Zwraca ({zasób: przyjęte}, straty, wynajem)."""
    poj = pojemnosc(dane, firma)
    zaj = zajete(dane, firma, (date.fromisoformat(dzien) - timedelta(days=1)).isoformat())
    wyn = wynajem(dane)
    przyjete, straty, wynajete = {}, [], []
    for p in [p for p in firma.partie if p.dostawa == dzien and not p.wynajem]:
        t = dane.zasoby[p.zasob].get("przechowywanie", "suche")
        dostarczone = p.ilosc
        if t in poj:
            l_opak = dane.zasoby[p.zasob].get("miejsce_l", 0.0)
            wolne = max(0.0, poj[t] - zaj[t])
            nadmiar = p.ilosc - (wolne / l_opak if l_opak > EPS else p.ilosc)
            if nadmiar > EPS and wyn:
                nowa, w = _do_wynajmu(dane, p, nadmiar, dzien, wyn)
                firma.partie.append(nowa)
                wynajete.append(w)
            elif nadmiar > EPS:
                straty.append(_strata(p, nadmiar, _uszczknij(p, nadmiar), "miejsce", dzien))
                dostarczone = p.ilosc
            zaj[t] += miejsce(dane, p)
        przyjete[p.zasob] = przyjete.get(p.zasob, 0.0) + dostarczone
    uzgodnij(firma, dzien)
    return przyjete, straty, wynajete


def wyrzuc(firma: Firma, dzien: str) -> list[dict]:
    """Wieczorem: partie, którym kończy się termin, idą do kosza."""
    straty = [_strata(p, p.ilosc, p.wartosc_gr, "termin", dzien) for p in na_stanie(firma, dzien)
              if p.termin and p.termin <= dzien and p.ilosc > EPS]
    for p in na_stanie(firma, dzien):
        if p.termin and p.termin <= dzien:
            p.ilosc, p.wartosc_gr = 0.0, 0
    uzgodnij(firma, dzien)
    return straty


def zuzyj(dane: Dane, firma: Firma, zuzycie: dict[str, float], dzien: str | None) -> dict[str, dict]:
    """FIFO: najpierw partie składnika z najkrótszym terminem, potem zamienniki. zuzycie w opakowaniach składnika
    podstawowego; wynik {zasób (także zamiennik): {"ilosc", "wartosc"}} – ilości w opakowaniach danego zasobu."""
    wynik: dict[str, dict] = {}
    staly = "9999-12-31"   # partie bez terminu – na końcu kolejki
    for nazwa, ile in zuzycie.items():
        pozostalo = ile
        for z in [nazwa] + zamienniki(dane, nazwa):
            mn = 1.0 if z == nazwa else przelicznik(dane, z)
            for p in sorted((p for p in na_stanie(firma, dzien) if p.zasob == z and p.ilosc > EPS),
                            key=lambda p: (p.termin or staly, p.dostawa)):
                if pozostalo <= EPS:
                    break
                bierz = min(p.ilosc, pozostalo / mn)
                w = wynik.setdefault(z, {"ilosc": 0.0, "wartosc": 0.0})
                w["ilosc"] += bierz
                w["wartosc"] += _uszczknij(p, bierz) / 100
                pozostalo -= bierz * mn
        wynik.setdefault(nazwa, {"ilosc": 0.0, "wartosc": 0.0})
    uzgodnij(firma, dzien)
    return wynik


NAZWY = {"chlodnia": "chłodni", "zamrazarka": "zamrażarki"}


def plan_wynajmu(dane: Dane, firma: Firma, runda: int) -> list[dict]:
    """Szacunek nadmiaru przy dostawach rundy (dostawa dnia + zapas z poprzednich rund w pierwszym dniu, bez
    sprzedaży między dostawami): [{"data", "przechowywanie", "litry", "pojemnosc", "koszt"}]."""
    wynik = []
    poj = pojemnosc(dane, firma)
    wyn = wynajem(dane)
    start = dane.data_rundy(runda).isoformat()
    nowe = [p for p in firma.partie if p.runda == runda and not p.wynajem]
    for t in CHLODZONE:
        dzienne: dict[str, float] = {}
        for p in nowe:
            if dane.zasoby[p.zasob].get("przechowywanie") == t:
                dzienne[p.dostawa] = dzienne.get(p.dostawa, 0.0) + miejsce(dane, p)
        stare = sum(miejsce(dane, p) for p in firma.partie if p.dostawa < start and not p.wynajem
                    and dane.zasoby[p.zasob].get("przechowywanie") == t)
        for dzien, litry in sorted(dzienne.items()):
            nadmiar = litry + (stare if dzien == start else 0.0) - poj[t]
            if nadmiar > EPS:
                wynik.append({"data": dzien, "przechowywanie": t, "litry": round(nadmiar, 1), "pojemnosc": poj[t],
                              "koszt": round(nadmiar * wyn["zl_za_litr"], 2) if wyn else None})
    return wynik


def ostrzezenia(dane: Dane, firma: Firma, runda: int) -> list[tuple[str, str]]:
    """Lista błędów (po decyzjach): dostawy do chłodni / zamrażarki, które się nie zmieszczą."""
    wyn = wynajem(dane)
    wynik = []
    for x in plan_wynajmu(dane, firma, runda):
        t, dzien = x["przechowywanie"], date.fromisoformat(x["data"]).strftime("%d.%m")
        if wyn and x["pojemnosc"] <= EPS:
            wynik.append(("pomaranczowy", f"Dostawa {dzien}: nie masz {NAZWY[t]} – {x['litry']:.0f} l pojedzie do "
                                          f"wynajętej chłodni (ok. {x['koszt']:.0f} zł, termin krótszy o {wyn['skrocenie_dni']} dni)."))
        elif wyn:
            wynik.append(("pomaranczowy", f"Dostawa {dzien}: ok. {x['litry']:.0f} l nie zmieści się w {NAZWY[t].removesuffix('i') + 'i'} "
                                          f"({x['pojemnosc']:.0f} l) – pojedzie do wynajętej chłodni (ok. {x['koszt']:.0f} zł, "
                                          f"termin krótszy o {wyn['skrocenie_dni']} dni)."))
        elif x["pojemnosc"] <= EPS:
            wynik.append(("czerwony", f"Zamawiasz składniki do {NAZWY[t]}, a nie masz takiego sprzętu – dostawca "
                                      "zostawi je na chodniku i trafią do kosza."))
        else:
            wynik.append(("pomaranczowy", f"Dostawa {dzien}: {x['litry'] + x['pojemnosc']:.0f} l do {NAZWY[t]} o pojemności "
                                          f"{x['pojemnosc']:.0f} l – nadmiar się zepsuje."))
    return list(dict.fromkeys(wynik))


def podsumowanie(dane: Dane, firma: Firma, runda: int) -> dict:
    """Zakładka „Magazyn i świeżość” (decyzje): partie po decyzjach (z zamówionymi), pojemność i zajętość chłodni
    / zamrażarki dzień po dniu – bez sprzedaży, czyli najwięcej, ile może być w środku."""
    start = dane.data_rundy(runda)
    n = (dane.data_rundy(runda + 1) - start).days
    dni = [start + timedelta(days=i) for i in range(n)]
    nazwy = dane.mapa["popyt"]["dni_tygodnia"]["nazwy"] if dane.mapa else [str(i) for i in range(n)]
    zajetosc = []
    for d in dni:
        iso = d.isoformat()
        z = {t: 0.0 for t in CHLODZONE}
        for p in firma.partie:
            t = dane.zasoby[p.zasob].get("przechowywanie", "suche")
            if t in z and not p.wynajem and p.dostawa <= iso and not (p.termin and p.termin < iso):
                z[t] += miejsce(dane, p)
        zajetosc.append({k: round(v, 1) for k, v in z.items()})
    return {"dni": [{"data": d.isoformat(), "dzien": nazwy[d.weekday()]} for d in dni], "pojemnosc": pojemnosc(dane, firma),
            "zajetosc": zajetosc, "wynajem": wynajem(dane), "plan_wynajmu": plan_wynajmu(dane, firma, runda),
            "partie": [{"zasob": p.zasob, "jakosc": p.jakosc, "ilosc": round(p.ilosc, 3), "wartosc": p.wartosc,
                        "dostawa": p.dostawa, "termin": p.termin, "dostawca": p.dostawca, "nowa": p.runda == runda,
                        "przechowywanie": dane.zasoby[p.zasob].get("przechowywanie", "suche"), "wynajem": p.wynajem,
                        "miejsce_l": round(miejsce(dane, p), 1)}
                       for p in sorted(firma.partie, key=lambda p: (p.termin or "9999", p.dostawa, p.zasob))]}


def przeterminowanie(dane: Dane, firma: Firma, runda: int) -> list[dict]:
    """Lista błędów (F4.2): szacunek partii, które przy prognozie popytu (`Firma.oferta`, dania w sprzedaży)
    przeterminują się w tej rundzie, zanim trafią do dań. Zużycie FIFO jak w `zuzyj` (najpierw najkrótszy termin, potem
    zamienniki), dzienne zużycie wg wag dni strefy pierwszego działającego lokalu (z kalendarzem), bez limitów obsługi.
    [{"zasob", "ilosc" (opakowania), "wartosc" (zł), "termin" (pierwszy)}]; składniki dań bez prognozy – pominięte."""
    from ..rynek import popyt as pp  # popyt korzysta ze świeżości – import w funkcji
    lokale = [lok for lok in firma.lokale if lok.dziala_od <= runda]
    dania = [u for u in firma.oferta if u in firma.ceny]
    if not lokale or not dania:
        return []
    dni = pp.dni_rundy(dane, runda)
    wagi = pp.wagi_dni(dane, dane.lokale[lokale[0].id]["strefa"], dni)
    wagi = wagi / wagi.sum()
    potrzeba, bez_prognozy = {}, set()
    for u in dania:
        for z, ile in dane.uslugi[u]["zasoby"].items():
            if not firma.oferta[u]:
                bez_prognozy.add(z)
            potrzeba[z] = potrzeba.get(z, 0.0) + firma.oferta[u] * ile / dane.zasoby[z]["opakowanie"]
    staly = "9999-12-31"
    wynik = []
    for nazwa, tydzien in potrzeba.items():
        if nazwa in bez_prognozy:
            continue
        partie = [(p, 1.0 if p.zasob == nazwa else przelicznik(dane, p.zasob)) for z in [nazwa] + zamienniki(dane, nazwa)
                  for p in firma.partie if p.zasob == z and p.ilosc > EPS]
        zostalo = {id(p): p.ilosc for p, _ in partie}
        straty: dict[str, dict] = {}
        for i, d in enumerate(dni):
            iso, braknie = d.isoformat(), tydzien * float(wagi[i])
            for p, mn in sorted((x for x in partie if x[0].dostawa <= iso and (x[0].termin or staly) >= iso),
                                key=lambda x: (x[0].zasob != nazwa, x[0].termin or staly, x[0].dostawa)):
                bierz = min(zostalo[id(p)], braknie / mn)
                zostalo[id(p)] -= bierz
                braknie -= bierz * mn
            for p, _ in partie:
                if p.termin == iso and zostalo[id(p)] > EPS:
                    s = straty.setdefault(p.zasob, {"zasob": p.zasob, "ilosc": 0.0, "wartosc": 0.0, "termin": iso})
                    s["ilosc"] += zostalo[id(p)]
                    s["wartosc"] += p.wartosc_gr / 100 * zostalo[id(p)] / p.ilosc
                    zostalo[id(p)] = 0.0
        wynik += [{**s, "ilosc": round(s["ilosc"], 2), "wartosc": round(s["wartosc"], 2)} for s in straty.values()]
    return wynik


__all__ = ["dostepne", "jakosc_skladnika", "nowa_partia", "ostrzezenia", "plan_wynajmu", "podsumowanie", "pojemnosc", "przeterminowanie", "przyjmij",
           "uzgodnij", "wynajem", "wyrzuc", "zajete", "zamienniki", "zuzyj"]
