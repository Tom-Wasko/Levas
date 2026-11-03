"""Z4: auto-dostawca i Auchan (silnik/kuchnia/auto_dostawca.py, dostawcy.hipermarkety)."""
import copy
from datetime import timedelta

import pytest
from pomocnicze import _gra

from silnik.boty import decyzje_bota
from silnik.dane import dane_domyslne
from silnik.decyzje import lista_bledow, zastosuj
from silnik.ksiegowosc import rozliczenie as rz
from silnik.ksiegowosc.finanse import Ksiega, Rachunek
from silnik.kuchnia import auto_dostawca as ad
from silnik.kuchnia import magazyn as mag
from silnik.kuchnia import swiezosc as sw
from silnik.kuchnia.dostawcy import ceny_rundy, z_rynku

pytestmark = pytest.mark.dane_gry   # Auchan i auto-dostawca są tylko w dane/ (nie w zamrożonej kopii)


@pytest.fixture(scope="module")
def gra_bota():
    g = _gra(("Tani", "tani"), ("Zrown", "zrownowazony"), rund=6)
    for _ in range(3):
        s = g.przelicz(wymus=True)
    return g, s


def _auto_z_zamowien(zamowienia, mnoznik=1.0):
    suma = {}
    for z in zamowienia:
        k = (z["zasob"], int(z["jakosc"]))
        suma[k] = suma.get(k, 0.0) + float(z["ilosc"])
    return {"pozycje": [{"zasob": z, "jakosc": q, "ilosc": round(i * mnoznik, 2)} for (z, q), i in sorted(suma.items())]}


def test_auchan_ceny_z_rynku():
    dane = dane_domyslne()
    ceny = ceny_rundy(dane, 1, 4)
    assert "Auchan" in ceny and z_rynku(dane, "Auchan") and not z_rynku(dane, "Makro")
    narzut = dane.dostawcy_info["Auchan"]["ceny_z_rynku"]["narzut"]
    for z, jak in ceny["Auchan"].items():
        for q, c in jak.items():
            inne = [x[z][q] for d, x in ceny.items() if d != "Auchan" and q in x.get(z, {})]
            assert c >= min(inne)   # nigdy najtańszy (gazetki tylko obniżają innych)
    # cały asortyment rynku
    wszystkie = {(z, q) for d, x in ceny.items() if d != "Auchan" for z, jak in x.items() for q in jak}
    assert wszystkie == {(z, q) for z, jak in ceny["Auchan"].items() for q in jak}
    assert narzut > 0
    assert ceny_rundy(dane, 1, 1) == {}   # runda przygotowania bez ofert


def test_zamow_ksiegi_i_odrzucone_zamowienia(gra_bota):
    g, s = gra_bota
    dane, r = g.dane, s.runda
    f = copy.deepcopy(s.firmy["Zrown"])
    zas = ad.zasady(dane)
    d = {"auto_dostawy": {"pozycje": [{"zasob": "Mięso kebab", "jakosc": 2, "ilosc": 3},
                                      {"zasob": "Bułka", "jakosc": 2, "ilosc": 10}]},
         "zamowienia": [{"dostawca": "Makro", "zasob": "Sos", "jakosc": 2, "ilosc": 2, "dzien": 0}]}
    ceny = ceny_rundy(dane, 1, r)
    ks, rach = Ksiega(vat=rz.reguly_vat(dane)), Rachunek()
    przed = len(f.partie)
    info = zastosuj(dane, f, d, r, [], ceny, ks, rach)
    lok = f.lokale[0].id
    x = info["auto_dostawy"]["lokale"][lok]
    cena_miesa = ceny["Auchan"]["Mięso kebab"]["2"]
    assert x["pozycje"][0]["cena"] == cena_miesa
    assert x["towar"] == pytest.approx(3 * cena_miesa + 10 * ceny["Auchan"]["Bułka"]["2"], abs=0.01)
    assert x["prowizja"] == pytest.approx(x["towar"] * zas["prowizja"], abs=0.01)
    nowe = f.partie[przed:]
    assert {p.zasob for p in nowe} == {"Mięso kebab", "Bułka"}   # własne zamówienie (Sos) odrzucone
    assert all(p.u_dostawcy and p.termin is None and p.lokal == lok and p.poza_lokalem for p in nowe)
    assert not info["zakupy_zasobow"]
    assert any("auto-dostawach" in u for u in info["dostawy"]["uwagi"])
    opisy = [p["opis"] for p in rach.operacje]
    assert any("Auto-dostawca: abonament" in o for o in opisy) and any("prowizja" in o for o in opisy)
    lb = lista_bledow(dane, f, d, r, list(f.oferta), lokal={}, info=info)
    assert any("auto-dostawach" in b["tekst"] and b["poziom"] == "czerwony" for b in lb)


def test_dzien_lokalu_u_dostawcy(gra_bota):
    """Partia u dostawcy: nie zajmuje chłodni, zużywana FIFO po własnych, po tygodniu dostaje termin, przechowanie
    kosztuje od następnego tygodnia, przeterminowana – strata „u_dostawcy” (bez sanepidu)."""
    g, s = gra_bota
    dane, r = g.dane, s.runda
    f = copy.deepcopy(s.firmy["Zrown"])
    f.partie.clear()
    sw.uzgodnij(f)
    start = dane.data_rundy(r)
    p = sw.nowa_partia(dane, "Mięso kebab", 2, 5.0, 100.0, start, ad.NAZWA, r, lokal=f.lokale[0].id)
    p.termin, p.u_dostawcy = None, True
    wlasna = sw.nowa_partia(dane, "Mięso kebab", 2, 1.0, 90.0, start, "Makro", r, lokal=f.lokale[0].id)
    f.partie += [p, wlasna]
    dzien = start.isoformat()
    sw.przyjmij(dane, f, dzien)
    assert sw.zajete(dane, f, dzien)["chlodnia"] == pytest.approx(sw.miejsce(dane, wlasna))
    zuz = sw.zuzyj(dane, f, {"Mięso kebab": 1.5}, dzien)
    assert zuz["Mięso kebab"]["ilosc"] == pytest.approx(1.5)
    assert wlasna.ilosc == pytest.approx(0) and p.ilosc == pytest.approx(4.5)   # najpierw własna (z terminem)
    assert ad.przechowanie(dane, f, dzien, r) == []    # tydzień zakupu – bez opłaty
    ostatni = dane.data_rundy(r + 1) - timedelta(days=1)
    zostaje = ad.koniec_tygodnia(dane, f, r, ostatni)
    assert zostaje and p.termin == sw.termin(dane, "Mięso kebab", ostatni).isoformat()
    # następny tydzień: przechowanie i kosz u dostawcy
    jutro = (ostatni + timedelta(days=1)).isoformat()
    prz = ad.przechowanie(dane, f, jutro, r + 1)
    zas = ad.zasady(dane)
    assert prz[0]["koszt"] == pytest.approx(sw.miejsce(dane, p) * zas["przechowanie_zl_za_litr_dzien"], abs=1e-3)
    straty = sw.wyrzuc(f, p.termin)
    assert straty and all(x["powod"] == "u_dostawcy" for x in straty)
    # koszt przechowania w KPiR na koniec rundy
    ks, rach = Ksiega(vat=rz.reguly_vat(dane)), Rachunek()
    raport = {"przechowanie": [{"lokal": p.lokal, "zasob": p.zasob, "jakosc": 2, "dni": 2, "litrodni": 30.0, "koszt": 4.5}]}
    w = mag.koniec_rundy(dane, f, r + 1, 1, raport, ks, rach)
    assert w["auto_dostawca"]["koszt"] == 4.5


def test_runda_na_auto_dostawach(gra_bota):
    """Pełna runda: bot przechodzi na auto-dostawy (ilości ze swoich zamówień × 1,5) – sprzedaje, płaci prowizję
    i abonament, reszta zostaje u dostawcy z terminem."""
    g0, _ = gra_bota
    g = copy.deepcopy(g0)
    s = g.stan(g.runda - 1)
    r = g.runda
    d = decyzje_bota(g.dane, s, "Zrown", "zrownowazony", r, g.konfiguracja)
    d["auto_dostawy"] = _auto_z_zamowien(d.pop("zamowienia", []), 1.5)
    g.ustaw_decyzje("Zrown", d)
    s2 = g.przelicz(wymus=True)
    w = s2.wyniki[r]["Zrown"]
    assert w["auto_dostawy"]["lokale"]
    opisy = [p["opis"] for p in w["rachunek"]]
    assert any(o.startswith("Auto-dostawca: abonament") for o in opisy)
    assert any(o.startswith("Auto-dostawca: prowizja") for o in opisy)
    assert sum(w["obsluga"]["obsluzeni"].values()) > 0 if "obsluga" in w else True
    f = s2.firmy["Zrown"]
    reszta = [p for p in f.partie if p.u_dostawcy and p.runda == r]
    assert reszta and all(p.termin or not dane_domyslne().zasoby[p.zasob].get("termin_dni") for p in reszta)
    assert w["magazyn"]["auto_dostawca"]["zostaje"]
