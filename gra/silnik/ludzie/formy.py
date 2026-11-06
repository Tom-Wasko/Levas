"""UF21: formy zatrudnienia (zalozenia.yaml: pracownicy.formy_zatrudnienia) i studenci (pracownicy.studenci).

Forma to klucz w `Pracownik.umowa`: „prace” (umowa o pracę) i „zlecenie” jak dotąd, do tego pół etatu, zlecenie ze
studentem, staż z urzędu pracy i kontrakt B2B. Parametry formy mówią, ile godzin osoba pracuje, jakie są składki ZUS
pracodawcy, czy jest okres wypowiedzenia, jak liczy się do opłaty kadrowej biura i do zadowolenia (składnik
„umowa zlecenie”), przy jakiej pensji osoba jest zadowolona z płacy i czy obowiązuje płaca minimalna.
Student (kandydat do 26 lat, cecha osoby, nie forma) nie płaci PIT – zadowala go niższa pensja – ale pracuje mniej
godzin i częściej odchodzi. Bez danych (zamrożona kopia testów) są tylko dwie dawne formy i nie ma studentów.
"""
from __future__ import annotations

from ..dane import Dane
from ..ksiegowosc.rozliczenie import zus_pracodawcy
from ..model import Firma, Pracownik

PRACE, ZLECENIE, STAZ = "prace", "zlecenie", "staz"

# dawne dwie formy – gdy danych UF21 nie ma (zachowanie sprzed UF21)
_DAWNE = {
    PRACE: {"nazwa": "Umowa o pracę", "opis": "", "etat": 1.0, "zus": "etat", "wypowiedzenie": True, "kadry": "etat",
            "kara_zlecenia": False, "oczekiwana": 1.0, "placa_minimalna": True},
    ZLECENIE: {"nazwa": "Umowa zlecenie", "opis": "", "etat": 1.0, "zus": "zlecenie", "wypowiedzenie": False,
               "kadry": "zlecenie", "kara_zlecenia": True, "oczekiwana": 1.0, "placa_minimalna": True},
}


def formy(dane: Dane) -> dict[str, dict]:
    return (dane.z.get("pracownicy") or {}).get("formy_zatrudnienia") or _DAWNE


def forma(dane: Dane, umowa: str) -> dict:
    f = formy(dane)
    return f.get(umowa) or f[PRACE]


def studenci(dane: Dane) -> dict | None:
    return (dane.z.get("pracownicy") or {}).get("studenci")


def dozwolone(dane: Dane, konfiguracja: dict | None) -> list[str]:
    """Formy włączone w grze (opcja MG `formy_zatrudnienia`; brak – wszystkie). Umowa o pracę zawsze."""
    wszystkie = list(formy(dane))
    wybrane = (konfiguracja or {}).get("formy_zatrudnienia")
    if wybrane is None:
        return wszystkie
    return [u for u in wszystkie if u in wybrane or u == PRACE]


def stawka_zus(dane: Dane, umowa: str, student: bool = False) -> float:
    """Składki ZUS pracodawcy od pensji; student na zleceniu – bez składek."""
    rodzaj = forma(dane, umowa)["zus"]
    if rodzaj == "brak" or (rodzaj == "zlecenie" and student):
        return 0.0
    return zus_pracodawcy(dane, "zlecenie" if rodzaj == "zlecenie" else PRACE)


def etat(dane: Dane, p: Pracownik) -> float:
    """Mnożnik godzin pracy osoby: forma × (student – mniej godzin)."""
    s = studenci(dane) if p.student else None
    return forma(dane, p.umowa)["etat"] * (s["godziny"] if s else 1.0)


def oczekiwana(dane: Dane, p: Pracownik) -> float | None:
    """Pensja miesięczna, przy której osoba jest zadowolona z płacy; None – forma bez pensji (staż)."""
    m = forma(dane, p.umowa)["oczekiwana"]
    if not m:
        return None
    s = studenci(dane) if p.student else None
    return p.pensja_preferowana * m * (s["pensja"] if s else 1.0)


def mnoznik_odejsc(dane: Dane, p: Pracownik) -> float:
    s = studenci(dane) if p.student else None
    return s["odejscia"] if s else 1.0


def placa_minimalna(dane: Dane, umowa: str, student: bool = False) -> float:
    """Najniższa dozwolona pensja miesięczna w tej formie (0 – bez płacy minimalnej)."""
    f = forma(dane, umowa)
    if not f["placa_minimalna"]:
        return 0.0
    s = studenci(dane) if student else None
    return dane.z["finanse"]["placa_minimalna"] * f["etat"] * (s["godziny"] if s else 1.0)


def porownawcza(dane: Dane, pensja: float, umowa: str) -> float:
    """Licytacja kandydata: oferta w przeliczeniu na umowę o pracę (B2B ÷ 1,25, pół etatu × 2, staż – stypendium)."""
    f = forma(dane, umowa)
    if not f["oczekiwana"]:
        return float((f.get("staz") or {}).get("stypendium", 0))
    return pensja / f["oczekiwana"]


def blad(dane: Dane, kandydat: dict, umowa: str, firma: Firma | None = None) -> str | None:
    """Czy osoba może dostać tę formę – None albo powód (kandydat: słownik z puli albo pracownik)."""
    if umowa not in formy(dane):
        return f"nieznana forma zatrudnienia „{umowa}”"
    f = formy(dane)[umowa]
    if f.get("tylko_studenci") and not kandydat.get("student"):
        wiek = (studenci(dane) or {}).get("wiek_do")
        return f"{f['nazwa'].lower()} – tylko dla studentów" + (f" do {wiek} lat" if wiek else "")
    st = f.get("staz")
    if st:
        if kandydat.get("gwiazdki", 0) > st["max_gwiazdek"]:
            return f"staż – tylko dla osób bez doświadczenia ({st['max_gwiazdek']}★)"
        if firma is not None and sum(p.umowa == umowa for p in firma.pracownicy.values()) >= st["naraz"]:
            return f"staż – najwyżej {st['naraz']} stażysta naraz"
    return None


def koniec_stazu(dane: Dane, firma: Firma, runda: int) -> list[dict]:
    """Po `rund` tygodniach stażu osoba przechodzi na umowę o pracę za pensję preferowaną (co najmniej minimalną)."""
    st = (formy(dane).get(STAZ) or {}).get("staz")
    if not st:
        return []
    wynik = []
    for p in firma.pracownicy.values():
        if p.umowa == STAZ and runda >= p.od_rundy + st["rund"]:
            p.umowa = PRACE
            p.pensja = max(p.pensja_preferowana, placa_minimalna(dane, PRACE, p.student))
            wynik.append({"pracownik": p.id, "imie_nazwisko": p.imie_nazwisko, "pensja": p.pensja})
    return wynik


def koniec_stazu_runda(dane: Dane, p: Pracownik) -> int | None:
    st = (formy(dane).get(STAZ) or {}).get("staz")
    return p.od_rundy + st["rund"] if st and p.umowa == STAZ else None


def przytnij(dane: Dane, d: dict, konfiguracja: dict | None) -> dict:
    """Decyzje z formą wyłączoną przez MG (opcja `formy_zatrudnienia`) – na umowę o pracę."""
    ok = set(dozwolone(dane, konfiguracja))
    if not d or len(ok) == len(formy(dane)):
        return d

    def popraw(x: dict) -> dict:
        return {**x, "umowa": PRACE} if x.get("umowa", PRACE) not in ok else x
    d = dict(d)
    for k in ("zatrudnij", "podkup"):
        if d.get(k):
            d[k] = [popraw(x) for x in d[k]]
    if d.get("zmiany"):
        d["zmiany"] = {pid: popraw(z) for pid, z in d["zmiany"].items()}
    return d


def widok(dane: Dane) -> dict:
    """Katalog form dla panelu: parametry i stawka ZUS (student na zleceniu – 0, liczy panel)."""
    return {"formy": {k: {**f, "zus_stawka": stawka_zus(dane, k)} for k, f in formy(dane).items()},
            "studenci": studenci(dane)}
