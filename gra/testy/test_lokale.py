"""Lokale i działki na mapie miasta (F3a.3): przydział, koszty, miejsca na stanowiska, budowa, boty, dane mapy."""

import re
from pathlib import Path

import pytest
from test_dane import _kopia, _zmien

from silnik import Gra
from silnik.dane import dane_domyslne, sprawdz
from silnik.finanse import vat_z_brutto

INDEX_JS = Path(__file__).parents[1] / "panel_gracza" / "static" / "zakladki" / "index.js"


def _gra(*firmy, rund=8, **opcje):
    opcje.setdefault("kapital_startowy", 100000)   # testy kupna lokali i działek – kapitał większy niż domyślny
    return Gra.nowa("lokale", [(n, b) for n, b in firmy] or [("A", None), ("B", None)], rund, 1, **opcje)


def _runda(g, **decyzje):
    for firma, d in decyzje.items():
        g.ustaw_decyzje(firma, d)
    return g.przelicz(wymus=True)


def _lokal(id_, forma="najem"):
    return {"lokal": {"id": id_, "forma": forma}}


def _netto(brutto, stawka=0.23):
    """Kwota w KPiR gry z lokalami: ceny są brutto, VAT idzie do rejestru (F3a.11)."""
    return round(brutto - vat_z_brutto(brutto, stawka), 2)


def _rachunek(s, r, firma, poczatek):
    return [p["kwota"] for p in s.wyniki[r][firma]["rachunek"] if p["opis"].startswith(poczatek)]


def test_gra_bez_lokali_jak_w_revas():
    g = _gra(lokale=False)
    assert not g.konfiguracja["lokale"]
    assert {s.typ for s in g.stan_poczatkowy().firmy["A"].stanowiska} == {"kuchnia", "kasa"}
    s = _runda(g, A=_lokal("centrum_3"))
    assert s.firmy["A"].lokale == [] and "lokale" not in s.wyniki[1]["A"]


def test_najem_gotowego_lokalu_kaucja_czynsz_i_sprzet_wynajmujacego():
    g = _gra()
    dane = g.dane
    assert g.stan_poczatkowy().firmy["A"].stanowiska == []
    s = _runda(g, A=_lokal("centrum_3"))
    f, lok = s.firmy["A"], dane.lokale["centrum_3"]
    assert [(x.id, x.forma, x.dziala_od) for x in f.lokale] == [("centrum_3", "najem", 1)]
    kaucja = dane.mapa["zasady"]["kaucja_miesiecy"] * lok["czynsz"]
    assert _rachunek(s, 1, "A", "Kaucja za lokal") == [-kaucja]
    kpir = {p["opis"]: p["pozostale"] for p in s.wyniki[1]["A"]["kpir"]["pozycje"]}
    assert kpir[f"Czynsz najmu: {lok['adres']}"] == pytest.approx(_netto(dane.na_runde(lok["czynsz"])), abs=0.01)
    assert any(o.startswith("Tygodniowy koszt utrzymania lokalu") for o in kpir)
    # zestaw sprzętu z lokalu: stanowiska działają od razu, sprzętu wynajmującego nie można sprzedać
    kuchnia = f.stanowisko("kuchnia", 1)
    assert kuchnia.lokal == "centrum_3" and set(kuchnia.sprzet_wynajmujacego) == set(kuchnia.sprzet)
    s = _runda(g, A={"sprzet_sprzedaj": [{"typ": "kuchnia", "nr": 1, "nazwa": "Rożen"}]})
    assert "Rożen" in s.firmy["A"].stanowisko("kuchnia", 1).sprzet


def test_ten_sam_lokal_w_jednej_rundzie_dostaje_jedna_firma():
    s = _runda(_gra(), A=_lokal("centrum_3"), B=_lokal("centrum_3"))
    decyzje = {n: s.wyniki[1][n]["lokal_decyzja"] for n in ("A", "B")}
    assert sorted(d["przyjety"] for d in decyzje.values()) == [False, True]
    przegrany = next(n for n, d in decyzje.items() if not d["przyjety"])
    assert "zajęła już firma" in decyzje[przegrany]["powod"]
    assert s.firmy[przegrany].lokale == [] and s.firmy[przegrany].gotowka == pytest.approx(s.wyniki[1][przegrany]["gotowka"])
    assert any(b["zakladka"] == "lokale" and b["poziom"] == "czerwony" for b in s.wyniki[1][przegrany]["lista_bledow"])


def test_kolejny_lokal_co_trzy_rundy_i_zajety_lokal():
    g = _gra()
    co = g.dane.mapa["zasady"]["nowy_lokal_co_rund"]
    _runda(g, A=_lokal("centrum_3"))
    s = _runda(g, A=_lokal("dworzec_1"), B=_lokal("centrum_3"))
    assert "co 3 rundy" in s.wyniki[2]["A"]["lokal_decyzja"]["powod"]
    assert "zajęła już firma A" in s.wyniki[2]["B"]["lokal_decyzja"]["powod"]
    for _ in range(co - 2):
        _runda(g)
    s = _runda(g, A=_lokal("dworzec_1"))
    assert s.wyniki[1 + co]["A"]["lokal_decyzja"]["przyjety"]
    assert [x.id for x in s.firmy["A"].lokale] == ["centrum_3", "dworzec_1"]


def test_kupno_wymaga_gotowki_a_sprzet_kupionego_lokalu_jest_majatkiem():
    g = _gra()
    s = _runda(g, A=_lokal("lsm_czuby_2", "kupno"), B=_lokal("zygmuntowskie_1", "kupno"))
    assert "Za mało gotówki" in s.wyniki[1]["A"]["lokal_decyzja"]["powod"]
    assert _rachunek(s, 1, "B", "Zakup lokalu") == [-g.dane.lokale["zygmuntowskie_1"]["cena"]]
    b = s.firmy["B"]
    assert b.lokale[0].forma == "kupno" and b.majatek > 0
    assert all(st.sprzet_wynajmujacego == [] for st in b.stanowiska)
    assert not any(p["opis"].startswith("Czynsz") for p in s.wyniki[1]["B"]["kpir"]["pozycje"])
    s = _runda(g, A=_lokal("zemborzyce_1", "najem"))
    assert "tylko na sprzedaż" in s.wyniki[2]["A"]["lokal_decyzja"]["powod"]


def test_stanowiska_tylko_na_wolnych_miejscach_w_dzialajacym_lokalu():
    g = _gra()
    # niewyposażony lokal: adaptacja (KPiR), działa od następnej rundy – w rundzie wzięcia brak miejsc
    s = _runda(g, A=_lokal("centrum_2") | {"stanowiska": {"kuchnia": 1}})
    lok = g.dane.lokale["centrum_2"]
    assert s.firmy["A"].lokale[0].dziala_od == 2 and s.firmy["A"].stanowiska == []
    assert any(p["opis"].startswith("Adaptacja lokalu") for p in s.wyniki[1]["A"]["kpir"]["pozycje"])
    assert any(b["zakladka"] == "stanowiska" for b in s.wyniki[1]["A"]["lista_bledow"])
    assert not any(p["opis"].startswith("Tygodniowy koszt utrzymania") for p in s.wyniki[1]["A"]["kpir"]["pozycje"])
    s = _runda(g, A={"stanowiska": {"kuchnia": 5, "kasa": 1}})
    f = s.firmy["A"]
    assert len(f.stanowiska_typu("kuchnia")) == lok["miejsca"]["kuchnia"] and len(f.stanowiska_typu("kasa")) == 1
    assert all(st.lokal == "centrum_2" and st.sprzet == {} for st in f.stanowiska)


def test_dzialka_budowa_w_ratach_potem_lokal_bez_sprzetu():
    g = _gra()
    lok = g.dane.lokale["czechow_3"]
    n = lok["budowa_rund"]
    s = _runda(g, A=_lokal("czechow_3", "kupno"))
    assert s.firmy["A"].lokale[0].dziala_od == 1 + n
    raty = []
    for r in range(1, n + 2):
        s = s if r == 1 else _runda(g)
        raty += _rachunek(s, r, "A", "Budowa lokalu")
        bledy = [b["tekst"] for b in s.wyniki[r]["A"]["lista_bledow"] if b["zakladka"] == "lokale"]
        assert any("Budowa" in b for b in bledy) == (r <= n)
    assert sum(raty) == pytest.approx(-lok["koszt_budowy"]) and len(raty) == n
    s = _runda(g, A={"stanowiska": {"kuchnia": 2, "kasa": 1}})
    assert len(s.firmy["A"].stanowiska) == 3


def test_boty_wynajmuja_lokale_i_graja_cala_gre():
    g = _gra(("Tani", "tani"), ("Premium", "premium"), ("Zrown", "zrownowazony"), ("Agr", "agresywny"), rund=6)
    for _ in range(6):
        s = g.przelicz(wymus=True)
    for n, f in s.firmy.items():
        assert len(f.lokale) == 1 and f.lokale[0].forma == "najem", n
        assert f.stanowiska and all(st.lokal == f.lokale[0].id for st in f.stanowiska), n
        miejsca = g.dane.lokale[f.lokale[0].id]["miejsca"]
        assert all(len(f.stanowiska_typu(t)) <= miejsca[t] for t in miejsca), n
    assert len({f.lokale[0].id for f in s.firmy.values()}) == len(s.firmy)
    assert sum(s.wyniki[6][n]["sprzedaz"] and 1 or 0 for n in s.firmy) == len(s.firmy)


def test_dane_mapy():
    dane = dane_domyslne()
    assert sprawdz() == []
    strefy = dane.mapa["strefy"]
    assert len(strefy) == 10 and all(lok["strefa"] in strefy for lok in dane.mapa["lokale"])
    # budynki prowadzą do istniejących zakładek panelu gracza
    zakladki = set(re.search(r"const ZAKLADKI = \{([^}]*)\}", INDEX_JS.read_text(encoding="utf-8")).group(1).replace(" ", "")
                   .replace("\n", "").split(","))
    assert {b["zakladka"] for b in dane.mapa["budynki"] if b["zakladka"]} <= zakladki
    assert "lokale" in zakladki and "mapa" in zakladki


def test_sprawdz_wykrywa_bledy_mapy(tmp_path):
    kat = _kopia(tmp_path)

    def nachodzi(d):
        d["lokale"][1]["mapa"] = dict(d["lokale"][0]["mapa"])

    _zmien(kat, "mapa/lokale.yaml", nachodzi)
    _zmien(kat, "mapa/budynki.yaml", lambda d: d["budynki"][0].update(strefa="atlantyda"))
    bledy = sprawdz(kat)
    assert any("zajmuje już" in b for b in bledy), bledy
    assert any("atlantyda" in b for b in bledy), bledy
