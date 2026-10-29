"""Lista błędów w grze z lokalami (F4.2): sprzęt i kucharz dania, cena wobec kosztu składników, przeterminowanie
przy prognozie popytu, zamówienia ponad saldo konta."""

import copy

import pytest
from pomocnicze import _gra

from silnik.dane import KUCHNIA
from silnik.decyzje import lista_bledow
from silnik.kuchnia import menu as mn
from silnik.kuchnia import swiezosc as sw
from silnik.model import Cena


@pytest.fixture(scope="module")
def gra_botow():
    g = _gra(("Tani", "tani"), ("Zrown", "zrownowazony"), rund=4)
    for _ in range(3):
        s = g.przelicz(wymus=True)
    return g, s


def _firma(gra_botow):
    g, s = gra_botow
    return g.dane, copy.deepcopy(s.firmy["Zrown"]), s.runda


def _teksty(bledy, zakladka=None):
    return [b["tekst"] for b in bledy if zakladka in (None, b["zakladka"])]


def test_sprzet_i_kucharz(gra_botow):
    dane, f, r = _firma(gra_botow)
    u = next(u for u in f.oferta if u in f.ceny)
    du = dane.uslugi[u]
    assert not [b for b in mn.bledy(dane, f, r) if b["zakladka"] != "oferta"]   # bot ma sprzęt i kucharzy
    for s in f.stanowiska_typu(KUCHNIA):   # bez sprzętu dania
        for n in du["sprzet"]:
            s.sprzet.pop(n, None)
    for s in f.stanowiska_typu(KUCHNIA):   # i bez nikogo w kuchni
        s.pracownik = None
    b = mn.bledy(dane, f, r)
    assert any(x["danie"] == u and x["zakladka"] == "sprzet" and du["sprzet"][0] in x["tekst"] for x in b)
    assert any(x["danie"] == u and x["zakladka"] == "zatrudnienie" and x["poziom"] == "czerwony" for x in b)
    # na liście błędów konkretne powody zamiast ogólnego „brak stanowiska z pracownikiem…”
    lb = lista_bledow(dane, f, {}, r, list(f.oferta), lokal={}, info={})
    assert not any(t.startswith(du["nazwa"]) and "brak stanowiska" in t for t in _teksty(lb))
    assert any(t.startswith(du["nazwa"]) and "brak sprzętu" in t for t in _teksty(lb, "sprzet"))
    # lokal jeszcze nie działa – bez uwag o daniach
    for lok in f.lokale:
        lok.dziala_od = r + 1
    assert mn.bledy(dane, f, r) == []


def test_cena_wobec_kosztu_skladnikow(gra_botow):
    dane, f, r = _firma(gra_botow)
    u = next(u for u in f.oferta if u in f.ceny)
    koszt = mn.koszt_porcji(dane, f, u)
    # ręcznie: średnia cena opakowania z partii (bez zapasu – najniższa średnia cena z danych)
    oczekiwany = 0.0
    for z, ile in dane.uslugi[u]["zasoby"].items():
        pz = [p for p in f.partie if p.zasob == z and p.ilosc > 0]
        cena = (sum(p.wartosc_gr for p in pz) / 100 / sum(p.ilosc for p in pz) if pz
                else min(dane.zasoby[z]["srednie_ceny"].values()))
        oczekiwany += ile / dane.zasoby[z]["opakowanie"] * cena
    assert koszt == pytest.approx(oczekiwany) and koszt > 0
    prog = dane.z["lista_bledow"]["udzial_skladnikow"]

    def uwagi(cena, rabat=0.0):
        f.ceny[u] = Cena(cena_gr=round(cena * 100), rabat_gr=round(rabat * 100))
        return [b for b in mn.bledy(dane, f, r) if b["danie"] == u and b["zakladka"] == "oferta"]

    assert uwagi(koszt * 3 / prog) == []
    assert [b["poziom"] for b in uwagi(koszt / (prog + (1 - prog) / 2))] == ["pomaranczowy"]
    assert [b["poziom"] for b in uwagi(koszt * 0.8)] == ["czerwony"]
    # rabat liczy się do ceny
    assert [b["poziom"] for b in uwagi(koszt * 1.5, rabat=koszt)] == ["czerwony"]


def test_przeterminowanie_przy_prognozie(gra_botow):
    dane, f, r = _firma(gra_botow)
    u = next(u for u in f.oferta if u in f.ceny and "Bułka" in dane.uslugi[u]["zasoby"])
    for x in list(f.oferta):   # tylko jedno danie, prognoza 70 porcji na tydzień
        if x != u:
            f.oferta.pop(x)
    f.oferta[u] = 70
    start = dane.data_rundy(r)
    f.partie = [sw.nowa_partia(dane, "Bułka", 2, 10, 40.0, start, "Test", r)]   # 500 bułek, termin 2 dni
    s = {x["zasob"]: x for x in sw.przeterminowanie(dane, f, r)}["Bułka"]
    from silnik.rynek import popyt as pp
    dni = pp.dni_rundy(dane, r)
    w = pp.wagi_dni(dane, dane.lokale[f.lokale[0].id]["strefa"], dni)
    zuzyte = 70 * (w[0] + w[1]) / w.sum() * dane.uslugi[u]["zasoby"]["Bułka"] / dane.zasoby["Bułka"]["opakowanie"]
    assert s["ilosc"] == pytest.approx(10 - zuzyte, abs=0.01) and s["termin"] == f.partie[0].termin
    assert s["wartosc"] == pytest.approx(40.0 * (10 - zuzyte), abs=0.1)
    lb = lista_bledow(dane, f, {}, r, list(f.oferta), lokal={}, info={})
    assert any(t.startswith("Bułka: przy Twojej prognozie") for t in _teksty(lb, "swiezosc"))
    # mała strata – poniżej progu z danych nie ma ostrzeżenia
    f.partie = [sw.nowa_partia(dane, "Bułka", 2, zuzyte + 0.01, 40.0, start, "Test", r)]
    assert sw.przeterminowanie(dane, f, r)[0]["wartosc"] < dane.z["lista_bledow"]["przeterminowanie_min_zl"]
    assert not _teksty(lista_bledow(dane, f, {}, r, list(f.oferta), lokal={}, info={}), "swiezosc")
    # danie bez prognozy – składnik pominięty (nie wiadomo, ile zejdzie)
    f.oferta[u] = 0
    assert sw.przeterminowanie(dane, f, r) == []


def test_zamowienia_ponad_saldo(gra_botow):
    dane, f, r = _firma(gra_botow)
    f.gotowka_gr = -500_000
    info = {"zakupy_zasobow": {"Hurtownia": [{"wartosc": 6000.0}]}}
    lb = lista_bledow(dane, f, {}, r, list(f.oferta), lokal={}, info=info)
    t = [b for b in lb if b["zakladka"] == "dostawcy"]
    assert len(t) == 1 and t[0]["poziom"] == "pomaranczowy" and "5 000 zł" in t[0]["tekst"] and "6 000 zł" in t[0]["tekst"]
    # brak wynika z czegoś innego niż zamówienia – ogólna uwaga o kredycie odnawialnym
    info = {"zakupy_zasobow": {"Hurtownia": [{"wartosc": 100.0}]}}
    lb = lista_bledow(dane, f, {}, r, list(f.oferta), lokal={}, info=info)
    assert not [b for b in lb if b["zakladka"] == "dostawcy"] and any("kredyt odnawialny" in t for t in _teksty(lb))


def test_cena_poza_widelkami_rynku_odrzucona():
    from pomocnicze import _lokal, _runda
    g = _gra(("A", None), ("B", None))
    dane = g.dane
    rynkowa = mn.cena_rynkowa(dane, "kebab_w_bulce")
    assert mn.widelki_ceny(dane, "kebab_w_bulce") == (round(rynkowa * 0.5, 2), round(rynkowa * 2, 2))
    _runda(g, A=_lokal("centrum_3"))
    s = _runda(g, A={"sprzedaz": {"kebab_w_bulce": {"cena": 25}, "kebab_box": {"cena": 200}}})
    assert set(s.firmy["A"].ceny) == {"kebab_w_bulce"}
    tekst = _teksty(s.wyniki[2]["A"]["lista_bledow"], "oferta")
    assert any("za wysoka" in t and "Danie nie weszło do sprzedaży" in t for t in tekst)
    s = _runda(g, A={"sprzedaz": {"kebab_w_bulce": {"cena": 25, "rabat": 20}}})    # po rabacie 5 zł
    assert s.firmy["A"].ceny["kebab_w_bulce"].cena == 25 and s.firmy["A"].ceny["kebab_w_bulce"].rabat == 0
    assert any("za niska" in t and "Zostaje poprzednia cena" in t for t in _teksty(s.wyniki[3]["A"]["lista_bledow"], "oferta"))
