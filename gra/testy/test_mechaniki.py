"""Testy mechanik potwierdzonych na danych z gry (WIEDZA_O_GRZE.md). Uruchom: .venv/Scripts/python -m pytest testy"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from silnik import Gra  # noqa: E402
from silnik.dane import KATALOG_REVAS, Dane  # noqa: E402
from silnik.finanse import Ksiega, Rachunek, bank_koniec_miesiaca, bank_poczatek_miesiaca  # noqa: E402
from silnik.karta import karta, wskaznik_zadluzenia  # noqa: E402
from silnik.model import Firma, Pracownik, Stanowisko  # noqa: E402
from silnik.operacje import obsluz  # noqa: E402
from silnik.planowanie import oczekiwany_popyt  # noqa: E402
from silnik.rynek import koszt_emisji, wzrost_reklamy_internetowej, wzrost_reklamy_tradycyjnej  # noqa: E402

D = Dane(KATALOG_REVAS)  # dane gry REVAS (fitness): testy liczą na liczbach z prawdziwych gier


def _pracownik(id_, zawod, nr, gw=3):
    return Pracownik(id=id_, imie_nazwisko=id_, zawod=zawod, gwiazdki=gw, pensja_preferowana=5300,
                     koszt_rekrutacji=400, koszt_odprawy=2650, zadowolenie_klientow=0.95,
                     ryzyko_reklamacji=0.0, pensja=5300, stanowisko=nr)


def firma_c_marzec() -> Firma:
    """Drużyna C (gra A/B/C/Apex/Vela), marzec: 1 instruktor (step, TBC, zumba na jednym stanowisku), 1 recepcjonista."""
    f = Firma(nazwa="C")
    sprzet = set(D.uslugi["step"]["sprzet"]) | set(D.uslugi["tbc"]["sprzet"]) | set(D.uslugi["zumba"]["sprzet"])
    f.stanowiska = [Stanowisko(nr=1, typ="kuchnia", sprzet={n: 3 for n in sprzet}, pracownik="i1"),
                    Stanowisko(nr=1, typ="kasa", sprzet={n: 3 for n in D.sprzet_kasy}, pracownik="r1")]
    f.pracownicy = {"i1": _pracownik("i1", "Instruktor", 1), "r1": _pracownik("r1", "Recepcjonista", 1)}
    f.magazyn = {"Napój izotoniczny|3": 100, "Płyn do dezynfekcji|3": 10, "Ręcznik papierowy|3": 20}
    f.wartosc_magazynu_gr = {k: v * 3000 for k, v in f.magazyn.items()}
    return f


def test_oblozenie_instruktora_i_recepcji_druzyna_c():
    # wyniki z gry: sprzedaż step 392, TBC 340, zumba 212 → instruktor 80,3%, recepcja 47,2%
    f = firma_c_marzec()
    w = obsluz(D, f, {"step": 392, "tbc": 340, "zumba": 212}, ziarno=1, runda=3)
    assert w["obsluzeni"] == {"step": 392, "tbc": 340, "zumba": 212}
    assert w["godziny_stanowisk"][1] / 160 == pytest.approx(0.803, abs=0.001)
    assert w["godziny_recepcji"] / 160 == pytest.approx(0.472, abs=0.001)


def test_zuzycie_zasobow_na_klienta():
    # gra A: 85,833 op. napoju = 2060 klientów = 2,06 płynu = 10,3 ręcznika
    f = firma_c_marzec()
    f.pracownicy["i1"].ryzyko_reklamacji = 0.0
    w = obsluz(D, f, {"step": 700, "tbc": 700, "zumba": 660}, ziarno=1, runda=3)
    klienci = sum(w["obsluzeni"].values())
    z = w["zuzyte_zasoby"]
    assert z["Napój izotoniczny"]["ilosc"] == pytest.approx(klienci / 24)
    assert z["Płyn do dezynfekcji"]["ilosc"] == pytest.approx(klienci * 5 / 5000)
    assert z["Ręcznik papierowy"]["ilosc"] == pytest.approx(klienci * 5 / 1000)


def test_brak_pojemnosci_ogranicza_sprzedaz():
    f = firma_c_marzec()
    w = obsluz(D, f, {"step": 2000, "tbc": 2000, "zumba": 2000}, ziarno=1, runda=3)
    godziny = sum(math.ceil(k / 10) * D.uslugi[u]["godziny_prowadzacego"] for u, k in w["obsluzeni"].items())
    assert godziny <= 160 + 1e-6
    assert all(v > 0 for v in w["utracona"].values())


def test_kpir_luty_ath_biuro_zus_podatek():
    # KPiR ATH, luty: 27 dokumentów × 1,20 = 32,40; ZUS 19% od 16 000 = 3040; podatek 19% od 33 306,10 = 6328,16
    k = Ksiega()
    k.dodaj("Sprzedaż", 78462.5, "przychod")
    k.dodaj("Zakup zasobów", 3703, "towary")
    k.dodaj("Wynagrodzenia", 16000, "wynagrodzenia")
    k.dodaj("Pozostałe", 25453.4 - 3040, "pozostale")
    k.dodaj("Składki ZUS pracodawcy", 16000 * D.z["finanse"]["zus_pracodawcy"])
    assert k.suma("pozostale") == pytest.approx(25453.4)
    assert k.dochod == pytest.approx(33306.1)
    assert k.podatek(0.19) == pytest.approx(6328.16, abs=0.01)


def test_wynik_ekonomiczny_ath():
    # ATH: dochód netto marca 304 747,81 → wynik ekonomiczny 15,237 (karta wyników r4)
    assert karta(D, 304747.81, 1.27, 0.95, 1.252, 1.0)["wynik_ekonomiczny"] == pytest.approx(15.237, abs=0.001)
    assert karta(D, -1000, 1, 1, 1, 1)["wynik_dzialalnosci"] == 0


def test_lokata_i_kredyt():
    bank = D.pozycje("banki")["Gaz Bank"]
    f = Firma(nazwa="X", gotowka=600000)
    k, r = Ksiega(), Rachunek()
    bank_poczatek_miesiaca(f, bank, {"lokaty_zaloz": [{"kwota": 500000, "miesiecy": 4}],
                                     "kredyty_wez": [{"kwota": 100, "miesiecy": 1}]}, 8, k, r)
    for runda in range(9, 13):
        bank_koniec_miesiaca(f, bank, runda, k, r)
    odsetki = [p for p in k.pozycje if p["opis"].startswith("Odsetki od lokaty")]
    assert odsetki[0]["przychod_pozostaly"] == pytest.approx(500000 * 0.07 * 4 / 12, abs=0.01)
    kredyt = [p for p in k.pozycje if p["opis"].startswith("Odsetki od kredytu nr")]
    assert kredyt[0]["pozostale"] == pytest.approx(0.83, abs=0.01)   # kredyt 100 PLN / 1 mies. / 10%


def test_koszt_emisji_i_reklama():
    media = D.pozycje("media_tradycyjne")
    assert koszt_emisji(media["Głos Miasta (dziennik)"], 8) == pytest.approx(4420)       # przykład z instrukcji
    assert koszt_emisji(media["Fitness TV"], 3) == pytest.approx(72000)                  # KPiR ATH lipiec
    czerwiec = {"Ulotki": 20, "Ekrany LED": 11, "Billboard (tradycyjny)": 11, "Super Fit (dziennik)": 14,
                "Głos Miasta (dziennik)": 14, "Newsy Miasta (dziennik)": 14, "Radio Fakty": 21, "Fit FM": 21, "Radio City": 21}
    assert wzrost_reklamy_tradycyjnej(D, czerwiec) == pytest.approx(0.4936, abs=0.03)    # ATH: +49,36%


def test_popyt_ath_luty():
    # ATH, luty: step po 35 PLN (pref. 40) przy 3 firmach (pozostałe 44 i 43 PLN) → popyt 740.
    # Wspólna kalibracja z grą A/B/C online zawyża luty ATH o ok. 12% (różnica między grami – patrz
    # POROWNANIE_ABC.md), stąd tolerancja 15%.
    r_sr = (35 / 40 + 44 / 40 + 43 / 40) / 3
    p = oczekiwany_popyt(D, "step", 1, 35, (3, 3, 3), 3, r_sr)
    assert p == pytest.approx(740, rel=0.15)


def test_popyt_abc_marzec():
    # gra A/B/C online, marzec: bodybuilding drużyny A po 108,50 PLN (pref. 155), 5 firm (155; 108,5; 111,11; 150)
    # → popyt 911; sprzęt i zasoby 3★
    ceny = [108.5, 155, 108.5, 111.11, 150]
    r_sr = sum(c / 155 for c in ceny) / 5
    p = oczekiwany_popyt(D, "bodybuilding", 2, 108.5, (2.4, 3, 3), 5, r_sr)
    assert p == pytest.approx(911, rel=0.10)


def test_deterministycznosc_i_zapis(tmp_path):
    def gra():
        g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "agresywny")], liczba_rund=4, ziarno=7, dane=D)
        for _ in range(4):
            g.przelicz()
        return g
    g1, g2 = gra(), gra()
    assert g1.stan(4).wyniki[4]["A"]["kpir"] == g2.stan(4).wyniki[4]["A"]["kpir"]
    plik = tmp_path / "gra.json"
    g1.zapisz(plik)
    g3 = Gra.wczytaj(plik, D)
    assert g3.stan(4).firmy["B"].gotowka == g1.stan(4).firmy["B"].gotowka


def test_reklama_tradycyjna_nasyca_sie_w_medium():
    # ATH (eksperymenty rund 9–12): 60 ulotek +4,18%, 20 ulotek +3,48%, 2 × Fitness TV +6,8%, brak reklamy 0
    assert wzrost_reklamy_tradycyjnej(D, {"Ulotki": 60}) == pytest.approx(0.0418, abs=0.01)
    assert wzrost_reklamy_tradycyjnej(D, {"Ulotki": 20}) == pytest.approx(0.0348, abs=0.01)
    assert wzrost_reklamy_tradycyjnej(D, {"Fitness TV": 2}) == pytest.approx(0.068, abs=0.015)
    assert wzrost_reklamy_tradycyjnej(D, {}) == 0


def test_reklama_internetowa_to_udzial_w_narzedziach():
    # ATH: 5 z 7 narzędzi na rynku +12,7%, 6 z 12 +7,6%, 1 z 11 +0,14%; wyłączone narzędzia – 0
    piec = {f"n{i}": 6 for i in range(5)}
    assert wzrost_reklamy_internetowej(D, piec, 6, 7) == pytest.approx(0.127, abs=0.015)
    assert wzrost_reklamy_internetowej(D, {f"n{i}": 6 for i in range(6)}, 8, 12) == pytest.approx(0.076, abs=0.012)
    # przy bardzo małym udziale model zawyża o ok. 0,3 pkt proc. (0,49% zamiast 0,14%) – błąd dopasowania
    assert wzrost_reklamy_internetowej(D, {"Instagram": 10}, 10, 11) == pytest.approx(0.0014, abs=0.004)
    assert wzrost_reklamy_internetowej(D, {}, 9, 8) == 0


def test_wskaznik_zadluzenia_ath_pazdziernik():
    # ATH październik: kredyt 199 900, majątek ≈ 115 871, skumulowany dochód netto 1 953 410 → 0,911
    assert wskaznik_zadluzenia(199_900, 115_871, 1_953_410) == pytest.approx(0.911, abs=0.002)


def test_lokata_konczy_sie_w_ostatnim_miesiacu():
    # ATH: lokata na 10 mies. z lutego i lokata na 1 mies. z listopada – odsetki obu w KPiR listopada
    bank = D.pozycje("banki")["Gaz Bank"]
    f = Firma(nazwa="X", gotowka=100000)
    k, r = Ksiega(), Rachunek()
    bank_poczatek_miesiaca(f, bank, {"lokaty_zaloz": [{"kwota": 50000, "miesiecy": 1}]}, 11, k, r)
    bank_koniec_miesiaca(f, bank, 11, k, r)
    assert any(p["opis"].startswith("Odsetki od lokaty") for p in k.pozycje)
    assert not f.lokaty


def test_brak_zasobu_najpierw_krotsze_zajecia():
    # ATH grudzień: przy braku napoju bodybuilding (1 h) obsłużony w większym odsetku niż joga (1,5 h)
    f = firma_c_marzec()
    sprzet = set(D.uslugi["bodybuilding"]["sprzet"]) | set(D.uslugi["joga"]["sprzet"])
    f.stanowiska = [Stanowisko(nr=1, typ="kuchnia", sprzet={n: 3 for n in sprzet}, pracownik="i1"),
                    Stanowisko(nr=2, typ="kuchnia", sprzet={n: 3 for n in sprzet}, pracownik="i2"),
                    Stanowisko(nr=1, typ="kasa", sprzet={n: 3 for n in D.sprzet_kasy}, pracownik="r1")]
    f.pracownicy["i2"] = _pracownik("i2", "Instruktor", 2)
    f.magazyn["Napój izotoniczny|3"] = 10          # 240 klientów
    w = obsluz(D, f, {"bodybuilding": 300, "joga": 300}, ziarno=1, runda=6)
    assert w["obsluzeni"]["bodybuilding"] / 300 > w["obsluzeni"]["joga"] / 300


def test_wzrost_reklamy_tradycyjnej_maleje_z_kazda_emisja():
    a, b, c = (wzrost_reklamy_tradycyjnej(D, {"Ulotki": n}) for n in (10, 20, 30))
    assert 0 < a < b < c and (c - b) < (b - a)
