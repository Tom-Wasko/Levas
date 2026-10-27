"""Stan gry: firmy, stanowiska, pracownicy, magazyn, bank – modele pydantic (`extra="forbid"`).

Kwoty są trzymane w groszach (pola `…_gr`, int). Silnik liczy w złotych przez właściwości o nazwach bez
`_gr` (np. `f.gotowka += 12.345` zapisuje 1235 gr), więc każde przypisanie zaokrągla do grosza. Na granicy:
- konstruktory i `model_validate` przyjmują też kwoty w złotych pod nazwą bez `_gr` (dane, decyzje z JS,
  import stanu prawdziwej gry),
- `do_slownika` daje widok w złotych dla zakładek JS,
- `model_dump`/`model_validate_json` to zapis stanu w groszach (z `WERSJA_STANU`).
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

WERSJA_STANU = 1
GR = "_gr"


def grosze(zl: float) -> int:
    """Złote → grosze, połówki w górę (od zera), jak w księgowości: 0,005 zł → 1 gr."""
    return int(Decimal(repr(float(zl))).scaleb(2).quantize(Decimal(1), ROUND_HALF_UP))


def zlote(gr: int) -> float:
    return gr / 100


def _kwota(pole: str) -> property:
    """Właściwość w złotych dla pola `pole_gr` w groszach."""
    nazwa = pole + GR
    return property(lambda s: getattr(s, nazwa) / 100, lambda s, v: setattr(s, nazwa, grosze(v)),
                    doc=f"{pole} w złotych (pole {nazwa} w groszach)")


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _ze_zlotych(cls, d: Any) -> Any:
        """Kwoty w złotych pod nazwą bez `_gr` → grosze (słowniki kwot przeliczane wartość po wartości)."""
        if not isinstance(d, dict):
            return d
        zl = [k for k in d if isinstance(k, str) and k + GR in cls.model_fields]
        if not zl:
            return d
        d = dict(d)
        for k in zl:
            v = d.pop(k)
            d[k + GR] = {n: grosze(x) for n, x in v.items()} if isinstance(v, dict) else None if v is None else grosze(v)
        return d


class Odejscie(Model):
    """Pracownik przyjął ofertę innej firmy (F3a.8) albo został zwolniony (P6, `do` puste): odchodzi w rundzie `runda`
    (po okresie wypowiedzenia) – do nowej firmy albo z powrotem do puli kandydatów."""
    do: str
    runda: int
    pensja_gr: int
    umowa: str = "prace"
    od_rundy: int                 # runda przyjęcia oferty

    pensja = _kwota("pensja")


class Pracownik(Model):
    id: str
    imie_nazwisko: str
    zawod: str
    gwiazdki: int
    pensja_preferowana_gr: int
    koszt_rekrutacji_gr: int
    koszt_odprawy_gr: int
    zadowolenie_klientow: float
    ryzyko_reklamacji: float
    pensja_gr: int = 0
    umowa: str = "prace"          # "prace" (umowa o pracę, + ZUS) albo "zlecenie"
    od_rundy: int = 0
    stanowisko: int = 0           # numer stanowiska (od 1) w grupie: instruktor/trener albo recepcja
    premia_gr: int = 0            # premia w bieżącej rundzie
    odchodzi: Odejscie | None = None   # gra z lokalami: okres wypowiedzenia po przyjęciu oferty innej firmy

    pensja_preferowana = _kwota("pensja_preferowana")
    koszt_rekrutacji = _kwota("koszt_rekrutacji")
    koszt_odprawy = _kwota("koszt_odprawy")
    pensja = _kwota("pensja")
    premia = _kwota("premia")


WLASCICIEL = "wlasciciel"   # id właściciela na stanowisku (nie ma go w Firma.pracownicy)


class WlascicielNaStanowisku(Model):
    """Właściciel sam staje na wolnym stanowisku w tej rundzie (P5): pracownik 1★ bez pensji, godziny z puli
    czasu właściciela (silnik/czas_wlasciciela.py)."""
    typ: str
    nr: int
    godziny: float
    zawod: str
    zadowolenie_klientow: float
    ryzyko_reklamacji: float


class Stanowisko(Model):
    nr: int
    typ: str                      # "kuchnia" albo "kasa" (silnik/dane.py: TYPY_STANOWISK)
    sprzet: dict[str, int] = Field(default_factory=dict)   # nazwa → jakość 1–3
    pracownik: str | None = None
    od_rundy: int = 0
    lokal: str | None = None      # id lokalu (dane/mapa/lokale.yaml); None – gra bez lokali
    sprzet_wynajmujacego: list[str] = Field(default_factory=list)   # sprzęt z najmu lokalu – nie do sprzedania


class OfertaHandlu(Model):
    """Oferta sprzedaży innej drużynie (silnik/handel.py): wystawiona w rundzie `runda`, do przyjęcia w następnej."""
    id: str
    do: str                       # drużyna adresat
    typ: str                      # "towar" albo "sprzet"
    cena_gr: int                  # brutto za całość
    runda: int
    zasob: str | None = None      # towar: zasób, jakość, ilość opakowań
    jakosc: int | None = None     # jakość towaru albo sprzętu (przy wystawieniu)
    ilosc: float | None = None
    nazwa: str | None = None      # sprzęt `nazwa` ze stanowiska `stanowisko` nr `nr`
    stanowisko: str | None = None
    nr: int | None = None

    cena = _kwota("cena")


class Lokal(Model):
    """Lokal drużyny (dane: dane/mapa/lokale.yaml)."""
    id: str
    forma: str                    # "najem" albo "kupno"
    od_rundy: int                 # runda wynajęcia / zakupu
    dziala_od: int                # pierwsza runda sprzedaży (po urządzeniu lub budowie)
    czynsz_gr: int = 0            # miesięczny (najem)
    kaucja_gr: int = 0
    cena_gr: int = 0              # cena zakupu (kupno)
    # przejęcie budynku przez inną drużynę (silnik/przejecia.py): najem trwa dalej, czynsz idzie do właściciela
    wlasciciel: str | None = None
    najem_do: int | None = None   # po wypowiedzeniu: ostatnia runda najmu
    ulepszenia: str | None = None # rozliczenie nakładów po wypowiedzeniu: "zatrzymaj" | "przywroc" (KC art. 676)
    naklady_gr: int = 0           # nakłady najemcy na lokal (adaptacja, stanowiska) – do rozliczenia ulepszeń

    czynsz = _kwota("czynsz")
    kaucja = _kwota("kaucja")
    cena = _kwota("cena")
    naklady = _kwota("naklady")


class KupionyBudynek(Model):
    """Budynek kupiony razem z najemcą – inną drużyną (silnik/przejecia.py); po końcu najmu – lokal właściciela."""
    id: str                       # id lokalu z mapy
    od_rundy: int
    cena_gr: int
    najemca: str

    cena = _kwota("cena")


class Partia(Model):
    """Dostawa składnika w grze z lokalami (silnik/swiezosc.py): zużywana od najkrótszego terminu (FIFO)."""
    zasob: str
    jakosc: int
    ilosc: float                  # opakowania (pozostało)
    wartosc_gr: int               # wartość pozostałej ilości
    dostawa: str                  # data dostawy (ISO) – od rana tego dnia partia jest w lokalu
    termin: str | None = None     # ostatni dzień użycia (ISO); wieczorem tego dnia partia idzie do kosza
    dostawca: str = ""
    runda: int = 0                # runda zakupu
    wynajem: bool = False         # w wynajętej chłodni (nie zmieściło się we własnej) – nie zajmuje własnego miejsca

    wartosc = _kwota("wartosc")


class Lokata(Model):
    id: int
    kwota_gr: int
    oprocentowanie: float
    od_rundy: int
    miesiecy: int
    bank: str = ""                # gra z lokalami: bank lokaty (silnik/banki.py)

    kwota = _kwota("kwota")


class Kredyt(Model):
    id: int
    kwota_gr: int
    oprocentowanie: float
    od_rundy: int
    miesiecy: int
    pozostalo_gr: int             # dług do spłaty (z zaległymi ratami kapitałowymi i doliczonymi odsetkami)
    bank: str = ""                # gra z lokalami (silnik/banki.py): bank, produkt i zastaw
    produkt: str = ""             # "start" | "inwestycyjny" | "obrotowy"
    zastaw: str = ""              # "lokal:<id>" | "sprzet:<typ>:<nr>:<nazwa>"
    zalegle: int = 0              # rund z rzędu bez zapłaconej raty
    zaleglosc_gr: int = 0         # zaległe raty kapitałowe

    kwota = _kwota("kwota")
    pozostalo = _kwota("pozostalo")
    zaleglosc = _kwota("zaleglosc")


class Leasing(Model):
    """Sprzęt w leasingu (gra z lokalami, silnik/banki.py): na stanowisku, ale własność banku do wykupu."""
    id: int
    bank: str
    typ: str
    nr: int
    nazwa: str
    jakosc: int
    cena_gr: int
    od_rundy: int
    rund: int
    pozostalo_rat: int
    rata_gr: int
    wykup_gr: int
    zalegle: int = 0

    cena = _kwota("cena")
    rata = _kwota("rata")
    wykup = _kwota("wykup")


class PozyczkaHarpagona(Model):
    """Pożyczka od lichwiarza Harpagona (gra z lokalami, silnik/lichwiarz.py) – poza KPiR."""
    kwota_gr: int
    dlug_gr: int                      # kapitał + naliczone odsetki
    od_rundy: int
    termin: int                       # ostatnia runda spłaty bez presji
    odsetki_gr: int = 0               # suma naliczonych odsetek
    wizyty: int = 0

    kwota = _kwota("kwota")
    dlug = _kwota("dlug")
    odsetki = _kwota("odsetki")


class RozliczenieJDG(Model):
    """Stan rozliczeń jednoosobowej działalności (gra z lokalami, silnik/rozliczenie.py) – narastająco od startu gry."""
    vat_nadwyzka_gr: int = 0          # nadwyżka VAT naliczonego do przeniesienia na następną rundę
    dochod_gr: int = 0                # dochód z KPiR narastająco (straty pomniejszają)
    zdrowotna_odliczona_gr: int = 0   # zapłacona zdrowotna odliczona od dochodu (do limitu rocznego)
    zaliczki_gr: int = 0              # wpłacone zaliczki na PIT
    zaplacone_gr: int = 0             # razem wpłacone do urzędu i ZUS (VAT, PIT, składki właściciela)

    vat_nadwyzka = _kwota("vat_nadwyzka")
    dochod = _kwota("dochod")
    zdrowotna_odliczona = _kwota("zdrowotna_odliczona")
    zaliczki = _kwota("zaliczki")
    zaplacone = _kwota("zaplacone")


class Cena(Model):
    """Cena usługi i rabat (włączona sprzedaż)."""
    cena_gr: int
    rabat_gr: int = 0

    cena = _kwota("cena")
    rabat = _kwota("rabat")


class SrodekTrwaly(Model):
    """Pozycja ewidencji środków trwałych (gra z lokalami): amortyzacja liniowa od rundy po zakupie."""
    nazwa: str
    rodzaj: str                   # klucz stawki w zalozenia.yaml: finanse.amortyzacja_roczna
    od_rundy: int
    stawka: float                 # roczna
    wartosc_gr: int = 0           # wartość początkowa
    umorzenie_gr: int = 0         # suma odpisów

    wartosc = _kwota("wartosc")
    umorzenie = _kwota("umorzenie")


class OtwartaHistoria(Model):
    """Ciąg dalszy historii z eventu w parku (silnik/zdarzenia.py) – scena czeka na swoją rundę."""
    historia: str
    scena: str
    runda: int
    zrodlo: str = "park"
    sciezka: list[str] = Field(default_factory=list)   # sceny rozegrane wcześniej


class Efekt(Model):
    """Skutek eventu trwający kilka rund: mnożnik popytu, godziny właściciela mniej albo dodatek do szansy kontroli
    sanepidu (silnik/zdarzenia.py, silnik/urzad.py)."""
    typ: str                      # "popyt" | "czas" | "kontrola"
    wartosc: float                # mnożnik, godziny albo szansa
    od_rundy: int
    do_rundy: int
    opis: str = ""


class Kampania(Model):
    """Kampania agencji reklamowej (silnik/reklama.py): trwa rundy od_rundy–do_rundy, potem wygasa."""
    agencja: str
    kanal: str
    strefa: str | None            # None – zasięg „miasto”
    od_rundy: int
    do_rundy: int
    koszt: float                  # netto
    sila: float = 1.0             # po nasyceniu (wcześniejsze kampanie w tym kanale i strefie)


class Promocja(Model):
    """Promocja z listy (silnik/promocje.py): trwa od rundy od_rundy, dopóki drużyna jej nie wyłączy."""
    typ: str
    nazwa: str                    # ozdobna nazwa drużyny – bez wpływu na wynik
    danie: str | None = None      # zakres „danie”
    od_rundy: int


class Firma(Model):
    nazwa: str
    bot: str | None = None
    nazwa_wyswietlana: str = ""
    misja: str = ""
    gotowka_gr: int = 0
    stanowiska: list[Stanowisko] = Field(default_factory=list)
    lokale: list[Lokal] = Field(default_factory=list)
    budynki: list[KupionyBudynek] = Field(default_factory=list)   # budynki z najemcą (gra z lokalami)
    srodki_trwale: list[SrodekTrwaly] = Field(default_factory=list)
    pracownicy: dict[str, Pracownik] = Field(default_factory=dict)
    magazyn: dict[str, float] = Field(default_factory=dict)           # "zasób|jakość" → opakowania
    wartosc_magazynu_gr: dict[str, int] = Field(default_factory=dict) # "zasób|jakość" → grosze (średni koszt)
    partie: list[Partia] = Field(default_factory=list)                # gra z lokalami: dostawy z terminami
    oferta: dict[str, int] = Field(default_factory=dict)              # usługa → prognoza popytu na miesiąc
    uslugi_kiedykolwiek: list[str] = Field(default_factory=list)
    ceny: dict[str, Cena] = Field(default_factory=dict)               # usługa → cena i rabat
    udogodnienia: list[str] = Field(default_factory=list)
    wyposazenie: list[str] = Field(default_factory=list)
    internet: dict[str, int] = Field(default_factory=dict)            # narzędzie → runda uruchomienia
    bank: str | None = None
    biuro: str | None = None
    lokaty: list[Lokata] = Field(default_factory=list)
    kredyty: list[Kredyt] = Field(default_factory=list)
    leasingi: list[Leasing] = Field(default_factory=list)
    harpagon: PozyczkaHarpagona | None = None
    historie: list[OtwartaHistoria] = Field(default_factory=list)   # eventy w parkach: ciągi dalsze
    efekty: list[Efekt] = Field(default_factory=list)
    wypadki: dict[str, int] = Field(default_factory=dict)   # wypadki w lokalu (silnik/awarie.py): id → runda początku
    polisy: dict[str, int] = Field(default_factory=dict)    # polisy ubezpieczyciela: rodzaj → runda początku ochrony
    higiena: str | None = None    # poziom higieny lokali (silnik/urzad.py); None – domyślny z danych
    odbiory: dict[str, int] = Field(default_factory=dict)   # lokal → runda odbioru przez sanepid
    portfel_gr: int | None = None   # prywatny portfel właściciela (silnik/wlasciciel.py); None – oszczędności z danych
    zaproszenia: list[int] = Field(default_factory=list)    # rundy z otwartym klubem (silnik/kasyno.py)
    oferty_handlu: list[OfertaHandlu] = Field(default_factory=list)   # wystawione innym drużynom (silnik/handel.py)
    wlasciciel_na: WlascicielNaStanowisku | None = None   # tylko w trakcie rundy (silnik/decyzje.py)
    kampanie: list[Kampania] = Field(default_factory=list)          # agencje reklamowe (gra z lokalami)
    promocje: list[Promocja] = Field(default_factory=list)          # promocje z listy (gra z lokalami)
    rozliczenie: RozliczenieJDG = Field(default_factory=RozliczenieJDG)   # JDG – gra z lokalami
    deklaracja: dict | None = None    # samodzielna księgowość: dokumenty i poprawne kwoty rundy (silnik/biuro.py)
    kredyt_odnawialny_gr: int = 0
    majatek_gr: int = 0               # suma inwestycji (sprzęt, stanowiska, udogodnienia, wyposażenie) – rozwój firmy
    rozwoj_poprzedni: float | None = None
    skumulowany_dochod_netto_gr: int = 0
    poprzednio_uslug: int = 0         # liczba usług i pracowników w poprzedniej rundzie (przyrost → rozwój firmy)
    poprzednio_pracownikow: int = 0
    utracona_poprzednio: float = 0.0  # udział utraconej sprzedaży w poprzedniej rundzie (zadowolenie klientów)
    baza_klientow: float = 1.0        # trwała utrata klientów po utraconej sprzedaży (mnożnik popytu firmy)
    licznik: int = 0                  # do numerowania lokat i kredytów

    gotowka = _kwota("gotowka")
    kredyt_odnawialny = _kwota("kredyt_odnawialny")
    majatek = _kwota("majatek")
    skumulowany_dochod_netto = _kwota("skumulowany_dochod_netto")

    def wartosc_magazynu(self, klucz: str) -> float:
        """Wartość zapasu „zasób|jakość” w złotych."""
        return self.wartosc_magazynu_gr.get(klucz, 0) / 100

    def stanowiska_typu(self, typ: str) -> list[Stanowisko]:
        return [s for s in self.stanowiska if s.typ == typ]

    def nowy_nr(self, typ: str) -> int:
        """Numer następnego stanowiska typu (po wyprowadzce z lokalu w numeracji mogą być luki)."""
        return max((s.nr for s in self.stanowiska_typu(typ)), default=0) + 1

    def stanowisko(self, typ: str, nr: int) -> Stanowisko | None:
        return next((s for s in self.stanowiska if s.typ == typ and s.nr == nr), None)

    def pracownik_stanowiska(self, s: Stanowisko) -> Pracownik | None:
        if s.pracownik:
            return self.pracownicy.get(s.pracownik)
        w = self.wlasciciel_na
        if w is None or (w.typ, w.nr) != (s.typ, s.nr):
            return None
        return Pracownik(id=WLASCICIEL, imie_nazwisko="Właściciel", zawod=w.zawod, gwiazdki=1,
                         pensja_preferowana_gr=0, koszt_rekrutacji_gr=0, koszt_odprawy_gr=0,
                         zadowolenie_klientow=w.zadowolenie_klientow, ryzyko_reklamacji=w.ryzyko_reklamacji,
                         stanowisko=s.nr)

    def godziny_stanowiska(self, s: Stanowisko, godziny_pracownika: float) -> float:
        """Godziny pracy na stanowisku w rundzie: etat pracownika albo godziny właściciela (0 – nieobsadzone)."""
        if s.pracownik:
            return godziny_pracownika if s.pracownik in self.pracownicy else 0.0
        w = self.wlasciciel_na
        return min(godziny_pracownika, w.godziny) if w and (w.typ, w.nr) == (s.typ, s.nr) else 0.0


class StanGry(Model):
    runda: int                                   # ostatnia przeliczona runda (0 = przed grą)
    firmy: dict[str, Firma]
    kandydaci: list[dict]                        # dostępni na rynku pracy (dane rynku, kwoty w złotych)
    # raporty rund dla zakładek (już w złotych, zaokrąglone przy liczeniu)
    wyniki: dict[int, dict[str, dict]] = Field(default_factory=dict)   # runda → firma → wyniki
    rynek: dict[int, dict] = Field(default_factory=dict)               # runda → dane publiczne rynku
    wersja: int = WERSJA_STANU

    @field_validator("wersja")
    @classmethod
    def _wersja(cls, v: int) -> int:
        if v != WERSJA_STANU:
            raise ValueError(f"Stan zapisany w wersji {v}, a gra obsługuje wersję {WERSJA_STANU}.")
        return v


def _na_zlote(x: Any) -> Any:
    if isinstance(x, dict):
        wynik = {}
        for k, v in x.items():
            if isinstance(k, str) and k.endswith(GR):
                wynik[k[: -len(GR)]] = {n: g / 100 for n, g in v.items()} if isinstance(v, dict) else None if v is None else v / 100
            else:
                wynik[k] = _na_zlote(v)
        return wynik
    if isinstance(x, list):
        return [_na_zlote(v) for v in x]
    return x


def do_slownika(obiekt: BaseModel) -> dict:
    """Widok w złotych (pola bez `_gr`) – dla zakładek JS i raportów."""
    return _na_zlote(obiekt.model_dump())


def firma_z_slownika(d: dict) -> Firma:
    """Firma z widoku w złotych (np. import stanu prawdziwej gry) albo z zapisu w groszach."""
    return Firma.model_validate(d)
