"""KPiR, bank i podatek (zasady potwierdzone na KPiR gry ATH, styczeń–sierpień – WIEDZA_O_GRZE.md, rozdz. 9).

- każdy wydatek i przychód to pozycja KPiR (sprzęt ≤ 10 000 PLN w całości w koszty miesiąca zakupu),
- biuro rachunkowe: opłata za księgowanie × liczba pozycji KPiR (bez „Obsługi kadrowo-płacowej”, z samą sobą)
  + opłata kadrowa za każdego pracownika (etat / umowa cywilnoprawna),
- CIT 19% od dodatniego dochodu miesiąca, bez rozliczania strat z poprzednich miesięcy,
- lokaty i kredyty: odsetki proste (roczne / 12 za miesiąc); kredyt spłacany równymi ratami kapitałowymi,
- kredyt odnawialny uruchamia się sam przy braku gotówki i jest spłacany, gdy gotówka wróci.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .model import Firma, Kredyt, Lokata

KOLUMNY = ("przychod", "przychod_pozostaly", "towary", "wynagrodzenia", "pozostale")


@dataclass
class Ksiega:
    pozycje: list[dict] = field(default_factory=list)

    def dodaj(self, opis: str, kwota: float, kolumna: str = "pozostale") -> None:
        if abs(kwota) < 0.005:
            return
        p = {"opis": opis, **{k: 0.0 for k in KOLUMNY}}
        p[kolumna] = round(kwota, 2)
        self.pozycje.append(p)

    def suma(self, kolumna: str) -> float:
        return round(sum(p[kolumna] for p in self.pozycje), 2)

    @property
    def przychody(self) -> float:
        return round(self.suma("przychod") + self.suma("przychod_pozostaly"), 2)

    @property
    def koszty(self) -> float:
        return round(self.suma("towary") + self.suma("wynagrodzenia") + self.suma("pozostale"), 2)

    @property
    def dochod(self) -> float:
        return round(self.przychody - self.koszty, 2)

    def podatek(self, stawka: float) -> float:
        return round(max(0.0, self.dochod) * stawka, 2)

    def do_slownika(self, stawka: float) -> dict:
        return {"pozycje": self.pozycje, "przychody": self.przychody, "koszty": self.koszty,
                "towary": self.suma("towary"), "wynagrodzenia": self.suma("wynagrodzenia"),
                "pozostale": self.suma("pozostale"), "dochod": self.dochod, "podatek": self.podatek(stawka),
                "dochod_netto": round(self.dochod - self.podatek(stawka), 2)}


@dataclass
class Rachunek:
    """Historia rachunku bankowego w miesiącu (wpływy i wydatki gotówki)."""
    operacje: list[dict] = field(default_factory=list)

    def zapisz(self, firma: Firma, opis: str, kwota: float) -> None:
        if abs(kwota) < 0.005:
            return
        firma.gotowka = round(firma.gotowka + kwota, 2)
        self.operacje.append({"opis": opis, "kwota": round(kwota, 2), "saldo": firma.gotowka})


def ksieguj(firma: Firma, ksiega: Ksiega, rachunek: Rachunek, opis: str, kwota: float, kolumna: str = "pozostale") -> None:
    """Pozycja KPiR + ruch na rachunku (koszt zmniejsza gotówkę, przychód zwiększa)."""
    ksiega.dodaj(opis, kwota, kolumna)
    znak = 1 if kolumna.startswith("przychod") else -1
    rachunek.zapisz(firma, opis, znak * kwota)


def bank_poczatek_miesiaca(firma: Firma, bank: dict, decyzje: dict, runda: int, ksiega: Ksiega, rachunek: Rachunek) -> dict:
    """Nowe lokaty i kredyty, zerwane lokaty, wcześniejsze spłaty. Zwraca informacje do wyników."""
    info = {"nowe_lokaty": [], "nowe_kredyty": [], "zerwane_lokaty": [], "splacone_kredyty": []}
    for l in decyzje.get("lokaty_zerwij", []):
        lokata = next((x for x in firma.lokaty if x.id == l), None)
        if lokata:
            firma.lokaty.remove(lokata)
            rachunek.zapisz(firma, f"Zerwanie lokaty nr {lokata.id} (bez odsetek)", lokata.kwota)
            info["zerwane_lokaty"].append(lokata.id)
    for k in decyzje.get("kredyty_splac", []):
        kredyt = next((x for x in firma.kredyty if x.id == k), None)
        if kredyt and firma.gotowka >= kredyt.pozostalo:
            firma.kredyty.remove(kredyt)
            rachunek.zapisz(firma, f"Spłata kredytu nr {kredyt.id}", -kredyt.pozostalo)
            info["splacone_kredyty"].append(kredyt.id)
    for d in decyzje.get("kredyty_wez", []):
        firma.licznik += 1
        kredyt = Kredyt(id=firma.licznik, kwota=float(d["kwota"]), oprocentowanie=bank["kredyt"], od_rundy=runda,
                        miesiecy=int(d["miesiecy"]), pozostalo=float(d["kwota"]))
        firma.kredyty.append(kredyt)
        rachunek.zapisz(firma, f"Kredyt nr {kredyt.id}", kredyt.kwota)
        info["nowe_kredyty"].append(kredyt.id)
    for d in decyzje.get("lokaty_zaloz", []):
        kwota = min(float(d["kwota"]), max(0.0, firma.gotowka))
        if kwota <= 0:
            continue
        firma.licznik += 1
        lokata = Lokata(id=firma.licznik, kwota=kwota, oprocentowanie=bank["lokata"], od_rundy=runda,
                        miesiecy=int(d["miesiecy"]))
        firma.lokaty.append(lokata)
        rachunek.zapisz(firma, f"Założenie lokaty nr {lokata.id}", -kwota)
        info["nowe_lokaty"].append(lokata.id)
    return info


def bank_koniec_miesiaca(firma: Firma, bank: dict, runda: int, ksiega: Ksiega, rachunek: Rachunek,
                         rund_w_roku: int = 12) -> None:
    """Raty i odsetki kredytów, odsetki kredytu odnawialnego, zakończone lokaty, opłata za konto (koniec rundy).
    Oprocentowanie roczne dzielone na rundy; okresy kredytów i lokat (pole `miesiecy`) liczone w rundach."""
    oplata = bank["konto"] + bank["karta"]  # miesięczna
    ksieguj(firma, ksiega, rachunek, "Opłata za konto", oplata if rund_w_roku == 12 else round(oplata * 12 / rund_w_roku, 2))
    for k in list(firma.kredyty):
        if k.od_rundy == runda:
            continue
        odsetki = round(k.pozostalo * k.oprocentowanie / rund_w_roku, 2)
        rata = round(min(k.pozostalo, k.kwota / k.miesiecy), 2)
        ksieguj(firma, ksiega, rachunek, f"Odsetki od kredytu nr {k.id}", odsetki)
        rachunek.zapisz(firma, f"Rata kapitałowa kredytu nr {k.id}", -rata)
        k.pozostalo = round(k.pozostalo - rata, 2)
        if k.pozostalo <= 0.005:
            firma.kredyty.remove(k)
    if firma.kredyt_odnawialny > 0:
        ksieguj(firma, ksiega, rachunek, "Odsetki od kredytu odnawialnego",
                round(firma.kredyt_odnawialny * bank["kredyt_odnawialny"] / rund_w_roku, 2))
    for l in list(firma.lokaty):
        # lokata na n miesięcy założona w miesiącu m kończy się z końcem miesiąca m + n − 1 (KPiR ATH, listopad:
        # „Lokata (Luty − Grudzień)” na 10 mies. i „Lokata (Listopad)” na 1 mies. – odsetki obu w listopadzie)
        if runda >= l.od_rundy + l.miesiecy - 1:
            odsetki = round(l.kwota * l.oprocentowanie * l.miesiecy / rund_w_roku, 2)
            firma.lokaty.remove(l)
            rachunek.zapisz(firma, f"Zakończenie lokaty nr {l.id}", l.kwota)
            ksieguj(firma, ksiega, rachunek, f"Odsetki od lokaty nr {l.id}", odsetki, "przychod_pozostaly")


def uruchom_odnawialny(firma: Firma, rachunek: Rachunek) -> float:
    """Gdy saldo jest ujemne – kredyt odnawialny na brakującą kwotę. Zwraca pobraną kwotę."""
    if firma.gotowka >= 0:
        return 0.0
    kwota = round(-firma.gotowka, 2)
    firma.kredyt_odnawialny = round(firma.kredyt_odnawialny + kwota, 2)
    rachunek.zapisz(firma, "Uruchomienie kredytu odnawialnego", kwota)
    return kwota


def wyrownaj_gotowke(firma: Firma, rachunek: Rachunek, pobrany_w_miesiacu: float = 0.0) -> float:
    """Koniec miesiąca: brak gotówki → kredyt odnawialny; nadwyżka → spłata kredytu z poprzednich miesięcy
    (kredytu pobranego w tym miesiącu nie spłaca się od razu – „w kolejnych rundach”, wg instrukcji)."""
    if firma.gotowka < 0:
        return uruchom_odnawialny(firma, rachunek)
    do_splaty = max(0.0, firma.kredyt_odnawialny - pobrany_w_miesiacu)
    if do_splaty > 0 and firma.gotowka > 0:
        splata = round(min(do_splaty, firma.gotowka), 2)
        firma.kredyt_odnawialny = round(firma.kredyt_odnawialny - splata, 2)
        rachunek.zapisz(firma, "Spłata kredytu odnawialnego", -splata)
    return 0.0


def zadluzenie(firma: Firma) -> float:
    return round(sum(k.pozostalo for k in firma.kredyty) + firma.kredyt_odnawialny, 2)


def odsetki_naliczone_lokat(firma: Firma, runda: int, rund_w_roku: int = 12) -> float:
    return round(sum(l.kwota * l.oprocentowanie * max(0, runda - l.od_rundy) / rund_w_roku for l in firma.lokaty), 2)
