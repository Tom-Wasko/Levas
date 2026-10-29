"""KPiR, bank i podatek (zasady potwierdzone na KPiR gry ATH, styczeń–sierpień – dokumentacja/WIEDZA_O_GRZE.md, rozdz. 9).

- każdy wydatek i przychód to pozycja KPiR (sprzęt ≤ 10 000 PLN w całości w koszty miesiąca zakupu),
- biuro rachunkowe: opłata za księgowanie × liczba pozycji KPiR (bez „Obsługi kadrowo-płacowej”, z samą sobą)
  + opłata kadrowa za każdego pracownika (etat / umowa cywilnoprawna),
- CIT 19% od dodatniego dochodu miesiąca, bez rozliczania strat z poprzednich miesięcy,
- lokaty i kredyty banków – silnik/pieniadze/banki.py,
- kredyt odnawialny uruchamia się sam przy braku gotówki i jest spłacany, gdy gotówka wróci.

Gra z lokalami (F3a.11, dane/podatki_2026.yaml): księga ma reguły VAT (`vat`). Kwoty w grze są brutto – `ksieguj`
wydziela VAT (stawka podana albo z reguł po opisie), do KPiR idzie netto, do rejestru VAT podatek, a rachunek
dostaje brutto. Pozycje bez ruchu gotówki (`Ksiega.dodaj`: amortyzacja) są bez VAT. CIT zastępuje rozliczenie
JDG (silnik/ksiegowosc/rozliczenie.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from ..model import Firma

KOLUMNY = ("przychod", "przychod_pozostaly", "towary", "wynagrodzenia", "pozostale")
KOLUMNY_KOSZTOW = ("towary", "wynagrodzenia", "pozostale")


def do_grosza(x: float) -> float:
    """Zaokrąglenie „handlowe” do grosza (połówka w górę), bez błędów binarnych floatów."""
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def do_zlotego(x: float) -> int:
    """Kwoty w deklaracjach: do pełnych złotych (końcówki od 50 gr w górę)."""
    return int(Decimal(str(x)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def vat_z_brutto(brutto: float, stawka: float) -> float:
    return do_grosza(brutto * stawka / (1 + stawka))


@dataclass
class Ksiega:
    pozycje: list[dict] = field(default_factory=list)
    vat: dict | None = None                       # reguły VAT (podatki_2026.yaml: vat) – gra z lokalami
    rejestr_vat: list[dict] = field(default_factory=list)

    def stawka_vat(self, opis: str) -> float:
        """Stawka z reguł po fragmencie opisu (pierwsza pasująca); brak – zwolnione (0)."""
        return next((r["stawka"] for r in self.vat["koszty"] if r["zawiera"] in opis), 0.0)

    def zarejestruj(self, opis: str, stawki: dict[float, float], nalezny: bool, inwestycja: bool = False) -> float:
        """Wpisy do rejestru VAT (sprzedaży – należny, zakupów – naliczony) z kwot brutto wg stawek. Zwraca VAT.
        `inwestycja` – VAT od środka trwałego (zapłacony w kwocie inwestycji – osobno w uzgodnieniu kasy)."""
        razem = 0.0
        for stawka, brutto in stawki.items():
            vat = vat_z_brutto(brutto, stawka)
            if stawka <= 0 or abs(vat) < 0.005:
                continue
            self.rejestr_vat.append({"opis": opis, "stawka": stawka, "brutto": round(brutto, 2),
                                     "netto": round(brutto - vat, 2), "vat": vat,
                                     "rodzaj": "nalezny" if nalezny else "naliczony", **({"inwestycja": True} if inwestycja else {})})
            razem += vat
        return round(razem, 2)

    def vat_suma(self, rodzaj: str) -> float:
        return round(sum(w["vat"] for w in self.rejestr_vat if w["rodzaj"] == rodzaj), 2)

    def dodaj(self, opis: str, kwota: float, kolumna: str = "pozostale", bez_gotowki: bool = False) -> None:
        """Pozycja KPiR bez ruchu na rachunku (`bez_gotowki` – amortyzacja, niezamortyzowana wartość: koszt bez
        wydatku, w uzgodnieniu kasy dodawany z powrotem)."""
        if abs(kwota) < 0.005:
            return
        p = {"opis": opis, **{k: 0.0 for k in KOLUMNY}, **({"bez_gotowki": True} if bez_gotowki else {})}
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

    def do_slownika(self, stawka: float = 0) -> dict:
        return {"pozycje": self.pozycje, "przychody": self.przychody, "koszty": self.koszty,
                "towary": self.suma("towary"), "wynagrodzenia": self.suma("wynagrodzenia"),
                "pozostale": self.suma("pozostale"), "dochod": self.dochod, "podatek": self.podatek(stawka),
                "dochod_netto": round(self.dochod - self.podatek(stawka), 2)}


# rodzaje operacji na rachunku: kpir – z zapisem w KPiR (ksieguj), korekta – zmienia istniejący zapis KPiR (zwrot
# zasobów), reszta – poza KPiR
RODZAJE_OPERACJI = {"kpir": "Zapisy w KPiR", "korekta": "Korekty zapisów w KPiR (zwroty zasobów)",
                    "podatki": "Podatki i składki", "inwestycje": "Inwestycje (lokale, budowa, środki trwałe)",
                    "kredyty": "Kredyty", "lokaty": "Lokaty", "kaucje": "Kaucje za lokale",
                    "harpagon": "Harpagon (poza księgami)",
                    "inwestor": "Inwestor ratunkowy (poza KPiR)",
                    "wlasciciel": "Wpłaty i wypłaty własne właściciela (poza KPiR)",
                    "kary": "Mandaty i kary (poza KPiR – nie są kosztem podatkowym)"}


@dataclass
class Rachunek:
    """Historia rachunku bankowego w miesiącu (wpływy i wydatki gotówki). Każda operacja ma rodzaj (RODZAJE_OPERACJI)
    – z niego uzgodnienie kasy z KPiR (silnik/ksiegowosc/uzgodnienie.py)."""
    operacje: list[dict] = field(default_factory=list)

    def zapisz(self, firma: Firma, opis: str, kwota: float, rodzaj: str) -> None:
        assert rodzaj in RODZAJE_OPERACJI, rodzaj
        kwota = round(kwota, 2)   # najpierw kwota operacji, potem saldo – saldo = suma operacji co do grosza
        if abs(kwota) < 0.005:
            return
        firma.gotowka = round(firma.gotowka + kwota, 2)
        self.operacje.append({"opis": opis, "kwota": kwota, "saldo": firma.gotowka, "rodzaj": rodzaj})


def ksieguj(firma: Firma, ksiega: Ksiega, rachunek: Rachunek, opis: str, kwota: float, kolumna: str = "pozostale",
            stawka: float | None = None, stawki: dict[float, float] | None = None) -> None:
    """Pozycja KPiR + ruch na rachunku (koszt zmniejsza gotówkę, przychód zwiększa). Z regułami VAT kwota jest
    brutto: `stawki` – części brutto wg stawek (zakup różnych składników), `stawka` – jedna stawka, bez nich – reguły."""
    znak = 1 if kolumna.startswith("przychod") else -1
    kwota = do_grosza(kwota)     # raz, handlowo – ta sama kwota w KPiR (netto + VAT) i na rachunku
    if ksiega.vat is not None and abs(kwota) >= 0.005:
        if stawki is None:
            stawki = {ksiega.stawka_vat(opis) if stawka is None else stawka: kwota}
        vat = ksiega.zarejestruj(opis, stawki, znak > 0)
        ksiega.dodaj(opis, round(kwota - vat, 2), kolumna)
    else:
        ksiega.dodaj(opis, kwota, kolumna)
    rachunek.zapisz(firma, opis, znak * kwota, "kpir")


def uruchom_odnawialny(firma: Firma, rachunek: Rachunek) -> float:
    """Gdy saldo jest ujemne – kredyt odnawialny na brakującą kwotę. Zwraca pobraną kwotę."""
    if firma.gotowka >= 0:
        return 0.0
    kwota = round(-firma.gotowka, 2)
    firma.kredyt_odnawialny = round(firma.kredyt_odnawialny + kwota, 2)
    rachunek.zapisz(firma, "Uruchomienie kredytu odnawialnego", kwota, "kredyty")
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
        rachunek.zapisz(firma, "Spłata kredytu odnawialnego", -splata, "kredyty")
    return 0.0


def zadluzenie(firma: Firma) -> float:
    """Kredyty i debet; niezwrócona wpłata inwestora ratunkowego liczy się jak dług (Z3)."""
    inwestor = firma.inwestor.dlug if firma.inwestor else 0.0
    return round(sum(k.pozostalo for k in firma.kredyty) + firma.kredyt_odnawialny + inwestor, 2)
