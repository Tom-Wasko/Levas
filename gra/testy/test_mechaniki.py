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
    assert w["godziny_kasy"] / 160 == pytest.approx(0.472, abs=0.001)


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


def test_deterministycznosc_i_zapis(tmp_path):
    def gra():
        g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "agresywny")], liczba_rund=4, ziarno=7)
        for _ in range(4):
            g.przelicz()
        return g
    g1, g2 = gra(), gra()
    assert g1.stan(4).wyniki[4]["A"]["kpir"] == g2.stan(4).wyniki[4]["A"]["kpir"]
    plik = tmp_path / "gra.json"
    g1.zapisz(plik)
    g3 = Gra.wczytaj(plik)
    assert g3.stan(4).firmy["B"].gotowka == g1.stan(4).firmy["B"].gotowka


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
