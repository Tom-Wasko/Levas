"""Karta wyników w grze z lokalami (F4.1): składniki kebabowe wskaźników Revasa, iloczyn, karta skumulowana, widok."""

import copy
import math

import pytest
from pomocnicze import _gra

from silnik.model import PozyczkaHarpagona
from silnik.wyniki import karta as kw

WSKAZNIKI = ("wynik_ekonomiczny", "zadowolenie_pracownikow", "zadowolenie_klientow", "rozwoj_firmy", "wskaznik_zadluzenia")


@pytest.fixture(scope="module")
def gra_botow():
    g = _gra(("Tani", "tani"), ("Premium", "premium"), ("Zrown", "zrownowazony"), ("Agr", "agresywny"), rund=5)
    for _ in range(5):
        s = g.przelicz(wymus=True)
    return g, s


def test_karta_kebabowa_w_grze(gra_botow):
    g, s = gra_botow
    p = g.dane.z["karta_wynikow"]["kebab"]
    for r in range(2, 6):
        for n, w in s.wyniki[r].items():
            k, kk = w["karta"], w["karta_kebab"]
            iloczyn = math.prod(k[x] for x in WSKAZNIKI) if k["wynik_ekonomiczny"] >= 0 else 0.0
            assert k["wynik_dzialalnosci"] == pytest.approx(iloczyn, abs=2e-3), (r, n)
            m = kk["miary"]
            assert 0 <= m["kolejki"] <= 1 and 0 <= m["brakujace_dania"] <= 1 and m["lokale"] == 1
            sk = kk["skladniki"]["zadowolenie_klientow"]
            assert sk.get("kolejki", 0) == pytest.approx(p["zadowolenie_klientow"]["kolejki"] * m["kolejki"], abs=1e-4)
            assert ("kontrola_z_mandatem" in sk) == (m["mandat"] > 0)
    # boty stoją w kolejkach i dostają mandaty – poprawki naprawdę obniżają zadowolenie klientów
    assert any(w["karta_kebab"]["skladniki"]["zadowolenie_klientow"] for r in range(2, 6) for w in s.wyniki[r].values())
    # gra bez lokali – karta Revasa bez składników kebabowych
    g2 = _gra(lokale=False)
    for _ in range(2):
        s2 = g2.przelicz(wymus=True)
    assert "karta" in s2.wyniki[2]["A"] and "karta_kebab" not in s2.wyniki[2]["A"]


def test_poprawki_i_harpagon(gra_botow):
    g, s = gra_botow
    dane = g.dane
    p = dane.z["karta_wynikow"]["kebab"]
    f = copy.deepcopy(s.firmy["Zrown"])
    w = copy.deepcopy(s.wyniki[4]["Zrown"])
    w["karta"] = {"wynik_dzialalnosci": 0.5, "wynik_ekonomiczny": 1.0, "zadowolenie_pracownikow": 0.9,
                  "zadowolenie_klientow": 1.0, "rozwoj_firmy": 0.6, "wskaznik_zadluzenia": 1.0}
    w["urzad"] = {**(w.get("urzad") or {}), "kontrola": {"mandat": 1000.0}}
    w["zdarzenia"] = {**(w.get("zdarzenia") or {}), "szkody": [{"historia": "a"}, {"historia": "b"}]}
    w["swiezosc"] = {**w["swiezosc"], "wylaczone": [{"danie": u} for u in f.oferta]}   # cały dzień bez menu
    for x in w["pracownicy"]:
        x["wykorzystanie"] = 1.0
    f.harpagon = PozyczkaHarpagona(kwota_gr=1_000_000, dlug_gr=1_200_000, od_rundy=2, termin=6)
    netto = dane.z["karta_wynikow"]["wynik_ekonomiczny_dzielnik"]
    kk = kw.kebab(dane, f, w, netto, 0.0)
    m, pk = kk["miary"], p["zadowolenie_klientow"]
    dni = len(w["klienci"]["dni"])
    assert m["brakujace_dania"] == pytest.approx(1 / dni, abs=1e-4) and m["wypadki"] == 2
    assert m["przepracowanie"] == pytest.approx(1 - p["zadowolenie_pracownikow"]["prog_przepracowania"])
    oczekiwane = (1.0 + pk["kolejki"] * m["kolejki"] + pk["brakujace_dania"] * m["brakujace_dania"]
                  + pk["kontrola_z_mandatem"] + 2 * pk["wypadek"])
    k = w["karta"]
    assert k["zadowolenie_klientow"] == pytest.approx(oczekiwane, abs=1e-3)
    assert k["zadowolenie_pracownikow"] == pytest.approx(0.9 + p["zadowolenie_pracownikow"]["przepracowanie"]
                                                         * m["przepracowanie"], abs=1e-3)
    # dług u Harpagona liczony z wagą – wskaźnik zadłużenia niższy niż przy tym samym kredycie w banku
    w2 = {**w, "karta": {**k, "wskaznik_zadluzenia": 1.0}}
    f.harpagon = None
    kw.kebab(dane, f, w2, netto, 12_000.0)
    assert k["wskaznik_zadluzenia"] < w2["karta"]["wskaznik_zadluzenia"] < 1
    assert kk["skladniki"]["wskaznik_zadluzenia"]["dlug_harpagona"] < 0
    assert k["wynik_dzialalnosci"] == pytest.approx(math.prod(k[x] for x in WSKAZNIKI), abs=2e-3)
    # kolejne lokale podnoszą rozwój; zero (brak sprzedaży) zostaje zerem
    f.lokale = f.lokale * 3
    w3 = {**w, "karta": {**k, "zadowolenie_klientow": 0.0, "rozwoj_firmy": 0.6}}
    kw.kebab(dane, f, w3, -1.0, 0.0)
    assert w3["karta"]["zadowolenie_klientow"] == 0.0 and w3["karta"]["wynik_dzialalnosci"] == 0.0
    assert w3["karta"]["rozwoj_firmy"] == pytest.approx(0.6 + 2 * p["rozwoj_firmy"]["kolejny_lokal"])


def test_cena_wzgledem_strefy(gra_botow):
    g, s = gra_botow
    dane = g.dane
    w = s.wyniki[4]["Premium"]
    lok = s.firmy["Premium"].lokale[0].id
    mn = dane.mapa["popyt"]["strefy"][dane.lokale[lok]["strefa"]]["cena"]
    sprzedane = {u: v for u, v in w["sprzedaz"].items() if v["sprzedaz"] > 0}
    klienci = sum(v["sprzedaz"] for v in sprzedane.values())
    oczekiwana = sum(v["sprzedaz"] * v["cena_po_rabacie"] / (dane.uslugi[u]["cena_preferowana"] * mn)
                     for u, v in sprzedane.items()) / klienci
    assert kw.cena_wzgledem_strefy(dane, sprzedane) == pytest.approx(oczekiwana)
    assert w["karta_kebab"]["miary"]["cena_wzgledem_strefy"] == pytest.approx(oczekiwana, abs=1e-4)


def test_karta_skumulowana_i_widok(gra_botow):
    from api.prezentacja import karta_skumulowana, widok
    g, s = gra_botow
    skum = karta_skumulowana(g, 5)
    for n in s.firmy:
        assert skum[n]["zadowolenie_klientow"] == pytest.approx(
            sum(s.wyniki[r][n]["karta"]["zadowolenie_klientow"] for r in range(2, 6)) / 4, abs=1e-3)
    v = widok(g, "Tani")
    assert v["wyniki"]["karta_kebab"]["miary"] and v["dzielnik_karty"] == g.dane.z["karta_wynikow"]["wynik_ekonomiczny_dzielnik"]
