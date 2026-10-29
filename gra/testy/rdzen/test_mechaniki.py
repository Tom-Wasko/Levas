"""Testy mechanik silnika na danych Levasa: obsługa klientów (godziny, zasoby, kasa), KPiR, karta wyników, powtarzalność.
Uruchom: .venv/Scripts/python -m pytest testy"""
import math

import pytest

from silnik import Gra
from silnik.dane import dane_domyslne
from silnik.ksiegowosc.finanse import Ksiega
from silnik.kuchnia.operacje import obsluz
from silnik.model import Firma, Pracownik, Stanowisko
from silnik.wyniki.karta import karta, wskaznik_zadluzenia

D = dane_domyslne()
ETAT = D.z["operacje"]["godziny_pracownika"]


def _pracownik(id_, zawod, nr):
    return Pracownik(id=id_, imie_nazwisko=id_, zawod=zawod, gwiazdki=3, pensja_preferowana=5300,
                     koszt_rekrutacji=400, koszt_odprawy=2650, zadowolenie_klientow=0.95,
                     ryzyko_reklamacji=0.0, pensja=5300, stanowisko=nr)


def firma_kebab(*uslugi, kucharzy=1) -> Firma:
    """Budka z kebabem: kucharze na stanowiskach ze sprzętem do dań, kasjer i duży zapas składników (jakość 3)."""
    f = Firma(nazwa="C")
    sprzet = {n for u in uslugi for n in D.uslugi[u]["sprzet"]}
    f.stanowiska = [Stanowisko(nr=i, typ="kuchnia", sprzet={n: 3 for n in sprzet}, pracownik=f"k{i}")
                    for i in range(1, kucharzy + 1)]
    f.stanowiska.append(Stanowisko(nr=1, typ="kasa", sprzet={n: 3 for n in D.sprzet_kasy}, pracownik="r1"))
    f.pracownicy = {f"k{i}": _pracownik(f"k{i}", "Kucharz", i) for i in range(1, kucharzy + 1)}
    f.pracownicy["r1"] = _pracownik("r1", "Kasjer", 1)
    for n in {n for u in uslugi for n in D.uslugi[u]["zasoby"]}:
        f.magazyn[f"{n}|3"] = 1000
        f.wartosc_magazynu_gr[f"{n}|3"] = 1000 * 100
    return f


def test_oblozenie_kucharza_i_kasy():
    f = firma_kebab("kebab_w_bulce", "frytki")
    popyt = {"kebab_w_bulce": 300, "frytki": 200}
    w = obsluz(D, f, popyt, ziarno=1, runda=3)
    assert w["obsluzeni"] == popyt
    godz = sum(k * D.uslugi[u]["godziny_prowadzacego"] for u, k in popyt.items())
    assert w["godziny_stanowisk"][1] == pytest.approx(godz)
    assert w["godziny_kasy"] == pytest.approx(sum(k * D.uslugi[u]["godziny_kasy"] for u, k in popyt.items()))


def test_zuzycie_zasobow_na_klienta():
    f = firma_kebab("kebab_w_bulce")
    w = obsluz(D, f, {"kebab_w_bulce": 400}, ziarno=1, runda=3)
    for n, ile in D.uslugi["kebab_w_bulce"]["zasoby"].items():
        assert w["zuzyte_zasoby"][n]["ilosc"] == pytest.approx(400 * ile / D.zasoby[n]["opakowanie"])
        assert f.magazyn[f"{n}|3"] == pytest.approx(1000 - 400 * ile / D.zasoby[n]["opakowanie"])


def test_brak_pojemnosci_ogranicza_sprzedaz():
    f = firma_kebab("kebab_w_bulce", "kebab_w_tortilli")
    w = obsluz(D, f, {"kebab_w_bulce": 2000, "kebab_w_tortilli": 2000}, ziarno=1, runda=3)
    godziny = sum(math.ceil(k / D.uslugi[u]["grupa"]) * D.uslugi[u]["godziny_prowadzacego"] for u, k in w["obsluzeni"].items())
    assert godziny <= ETAT + 1e-6
    assert all(v > 0 for v in w["utracona"].values())


def test_brak_zasobu_najpierw_krotsze_dania():
    # wspólne mięso: przy braku danie z krótszym czasem kucharza obsłużone w większym odsetku popytu
    f = firma_kebab("kebab_w_bulce", "talerz_kebab", kucharzy=2)
    assert D.uslugi["kebab_w_bulce"]["godziny_prowadzacego"] < D.uslugi["talerz_kebab"]["godziny_prowadzacego"]
    f.magazyn["Mięso kebab|3"] = 300 * D.uslugi["kebab_w_bulce"]["zasoby"]["Mięso kebab"] / D.zasoby["Mięso kebab"]["opakowanie"]
    w = obsluz(D, f, {"kebab_w_bulce": 300, "talerz_kebab": 300}, ziarno=1, runda=6)
    assert w["obsluzeni"]["kebab_w_bulce"] > w["obsluzeni"]["talerz_kebab"] > 0


def test_kpir_zus_i_podatek():
    k = Ksiega()
    k.dodaj("Sprzedaż", 78462.5, "przychod")
    k.dodaj("Zakup składników", 3703, "towary")
    k.dodaj("Wynagrodzenia", 16000, "wynagrodzenia")
    k.dodaj("Pozostałe", 20000, "pozostale")
    zus = 16000 * D.z["finanse"]["zus_pracodawcy"]
    k.dodaj("Składki ZUS pracodawcy", zus)
    assert k.suma("pozostale") == pytest.approx(20000 + zus)
    assert k.dochod == pytest.approx(78462.5 - 3703 - 16000 - 20000 - zus)
    assert k.podatek(0.19) == pytest.approx(round(k.dochod * 0.19, 2), abs=0.01)


def test_wynik_ekonomiczny():
    dz = D.z["karta_wynikow"]["wynik_ekonomiczny_dzielnik"]
    k = karta(D, 10 * dz, 1.2, 0.9, 1.1, 1.0)
    assert k["wynik_ekonomiczny"] == pytest.approx(10)
    assert k["wynik_dzialalnosci"] == pytest.approx(10 * 1.2 * 0.9 * 1.1, abs=0.001)
    waga = D.z["karta_wynikow"]["strata"]["waga"]   # Z1: strata daje ujemny wynik (wcześniej 0)
    assert karta(D, -10 * dz, 1, 1, 1, 1)["wynik_dzialalnosci"] == pytest.approx(-10 * waga)


@pytest.mark.dane_gry
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


def test_wskaznik_zadluzenia():
    # kredyt 199 900, majątek ≈ 115 871, skumulowany dochód netto 1 953 410 → 0,911 (wzór z gry ATH)
    assert wskaznik_zadluzenia(199_900, 115_871, 1_953_410) == pytest.approx(0.911, abs=0.002)
