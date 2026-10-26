"""Świeżość składników w grze z lokalami (krok F3a.5; notatki/Menu i składniki.md).

Dane: zasoby.yaml – przechowywanie (chlodnia, zamrazarka, suche), termin_dni, miejsce_l, zamiennik_dla, kara_jakosci;
sprzet.yaml – przechowywanie i pojemnosc_l sprzętu (szafa chłodnicza, zamrażarka).

Zasady:
- każde zamówienie to partia z dniem dostawy (zamowienia[].dzien, 0 = poniedziałek rundy); termin = dzień dostawy
  + termin_dni − 1 (bułka z poniedziałku – 2 dni – ląduje w koszu we wtorek wieczorem),
- dzień w lokalu: rano dostawy (do chłodni i zamrażarki wchodzi tyle, ile się zmieści – reszta to strata), w ciągu
  dnia klienci zużywają najpierw partie z najkrótszym terminem (FIFO), wieczorem przeterminowane partie idą do kosza,
- magazyn jest wspólny dla lokali firmy, pojemność = suma pojemności sprzętu ze wszystkich stanowisk; suche – bez limitu,
- zamiennik (np. mrożona pita) jest używany, gdy zabraknie składnika podstawowego; danie z zamiennikiem ma jakość
  składnika niższą o kara_jakosci gwiazdek.
`Firma.magazyn` zostaje sumą partii („zasób|jakość” → opakowania) – reszta silnika (jakość, limity) liczy z niego.
"""
from __future__ import annotations

from datetime import date, timedelta

from .dane import Dane
from .model import Firma, Partia, grosze

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


def zajete(dane: Dane, firma: Firma, dzien: str | None = None) -> dict[str, float]:
    wynik = {t: 0.0 for t in CHLODZONE}
    for p in na_stanie(firma, dzien):
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


def przyjmij(dane: Dane, firma: Firma, dzien: str) -> tuple[dict[str, float], list[dict]]:
    """Ranne dostawy dnia: do chłodni i zamrażarki tyle, ile się zmieści. Zwraca ({zasób: przyjęte}, straty)."""
    poj = pojemnosc(dane, firma)
    zaj = zajete(dane, firma, (date.fromisoformat(dzien) - timedelta(days=1)).isoformat())
    przyjete, straty = {}, []
    for p in [p for p in firma.partie if p.dostawa == dzien]:
        t = dane.zasoby[p.zasob].get("przechowywanie", "suche")
        if t in poj:
            l_opak = dane.zasoby[p.zasob].get("miejsce_l", 0.0)
            wolne = max(0.0, poj[t] - zaj[t])
            nadmiar = p.ilosc - (wolne / l_opak if l_opak > EPS else p.ilosc)
            if nadmiar > EPS:
                straty.append(_strata(p, nadmiar, _uszczknij(p, nadmiar), "miejsce", dzien))
            zaj[t] += miejsce(dane, p)
        przyjete[p.zasob] = przyjete.get(p.zasob, 0.0) + p.ilosc
    uzgodnij(firma, dzien)
    return przyjete, straty


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


def zwroc(firma: Firma, dostawca: str, zasob: str, jakosc: int, runda: int, ile: float) -> tuple[float, int]:
    """Zwrot nadmiaru: całe opakowania z partii tej rundy od dostawcy (najpierw najnowsze). Zwraca (ilość, grosze)."""
    zwrot, wartosc = 0.0, 0
    for p in sorted((p for p in firma.partie if p.runda == runda and p.dostawca == dostawca and p.zasob == zasob
                     and p.jakosc == jakosc), key=lambda p: p.dostawa, reverse=True):
        n = min(int(p.ilosc + EPS), int(ile - zwrot + EPS))
        if n > 0:
            wartosc += _uszczknij(p, n)
            zwrot += n
    uzgodnij(firma)
    return zwrot, wartosc


NAZWY = {"chlodnia": "chłodni", "zamrazarka": "zamrażarki"}


def ostrzezenia(dane: Dane, firma: Firma, runda: int) -> list[tuple[str, str]]:
    """Lista błędów (po decyzjach): dostawy do chłodni / zamrażarki, które się nie zmieszczą."""
    wynik = []
    poj = pojemnosc(dane, firma)
    start = dane.data_rundy(runda).isoformat()
    nowe = [p for p in firma.partie if p.runda == runda]
    for t in CHLODZONE:
        dzienne: dict[str, float] = {}
        for p in nowe:
            if dane.zasoby[p.zasob].get("przechowywanie") == t:
                dzienne[p.dostawa] = dzienne.get(p.dostawa, 0.0) + miejsce(dane, p)
        if not dzienne:
            continue
        if poj[t] <= EPS:
            wynik.append(("czerwony", f"Zamawiasz składniki do {NAZWY[t]}, a nie masz takiego sprzętu – dostawca "
                                      "zostawi je na chodniku i trafią do kosza."))
            continue
        stare = sum(miejsce(dane, p) for p in firma.partie if p.dostawa < start
                    and dane.zasoby[p.zasob].get("przechowywanie") == t)
        for dzien, litry in sorted(dzienne.items()):
            razem = litry + (stare if dzien == start else 0.0)
            if razem > poj[t] + EPS:
                wynik.append(("pomaranczowy", f"Dostawa {date.fromisoformat(dzien).strftime('%d.%m')}: "
                              f"{razem:.0f} l do {NAZWY[t]} o pojemności {poj[t]:.0f} l – nadmiar się zepsuje."))
    return wynik


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
            if t in z and p.dostawa <= iso and not (p.termin and p.termin < iso):
                z[t] += miejsce(dane, p)
        zajetosc.append({k: round(v, 1) for k, v in z.items()})
    return {"dni": [{"data": d.isoformat(), "dzien": nazwy[d.weekday()]} for d in dni], "pojemnosc": pojemnosc(dane, firma),
            "zajetosc": zajetosc,
            "partie": [{"zasob": p.zasob, "jakosc": p.jakosc, "ilosc": round(p.ilosc, 3), "wartosc": p.wartosc,
                        "dostawa": p.dostawa, "termin": p.termin, "dostawca": p.dostawca, "nowa": p.runda == runda,
                        "przechowywanie": dane.zasoby[p.zasob].get("przechowywanie", "suche"),
                        "miejsce_l": round(miejsce(dane, p), 1)}
                       for p in sorted(firma.partie, key=lambda p: (p.termin or "9999", p.dostawa, p.zasob))]}


__all__ = ["dostepne", "jakosc_skladnika", "nowa_partia", "ostrzezenia", "podsumowanie", "pojemnosc", "przyjmij", "uzgodnij", "wyrzuc", "zajete",
           "zamienniki", "zuzyj", "zwroc"]
