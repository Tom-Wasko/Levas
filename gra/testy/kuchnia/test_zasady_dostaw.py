"""Dostawcy (F3a.6): dni dostaw, opłaty za dowóz, minimalne zamówienie, limity i czas właściciela w dyskontach,
gazetki, producent od rundy 3, planowanie dostaw w dni dostawcy, gra i sprawdzanie danych."""

from datetime import date, timedelta

import pytest
from pomocnicze import _gra, _kopia, _lokal, _netto, _runda, _zmien

from silnik.dane import dane_domyslne, sprawdz
from silnik.kuchnia import dostawcy as dst
from silnik.kuchnia import planowanie
from silnik.model import Firma
from silnik.rynek import popyt as pp

PN = date(2026, 10, 12)
MAKRO, BIEDRONKA, ROZEN, PIEKARNIA = "Makro", "Biedronka", "Zakłady Mięsne „Rożen” z Łęcznej", "Piekarnia Koziołek"


def _z(dostawca, zasob, ilosc, dzien, cena=10.0, jakosc=2):
    return {"dostawca": dostawca, "zasob": zasob, "jakosc": jakosc, "ilosc": ilosc, "dzien": dzien, "cena": cena}


def test_zasady_dostaw():
    dane = dane_domyslne()
    zam = [_z(MAKRO, "Sos", 2, 1),                       # Makro nie dowozi we wtorki
           _z(MAKRO, "Sos", 3, 3, cena=50),              # czwartek, 150 zł < 1000 – płatny dowóz
           _z(MAKRO, "Napój", 30, 0, cena=50),           # poniedziałek, 1500 zł – dowóz gratis
           _z(BIEDRONKA, "Bułka", 3, 2), _z(BIEDRONKA, "Bułka", 3, 2, jakosc=1),   # limit 4 opakowania dziennie
           _z(BIEDRONKA, "Napój", 1, 4),
           _z(ROZEN, "Mięso kebab", 1, 1, cena=300)]     # 300 zł < minimum 800 zł
    przyjete, w = dst.zasady_dostaw(dane, zam, PN, 7)
    assert [(z["dostawca"], z["zasob"], z["dzien"], z["ilosc"]) for z in przyjete] == [
        (MAKRO, "Sos", 3, 3), (MAKRO, "Napój", 0, 30), (BIEDRONKA, "Bułka", 2, 3), (BIEDRONKA, "Bułka", 2, 1),
        (BIEDRONKA, "Napój", 4, 1)]
    assert len(w["uwagi"]) == 3 and "Makro nie dowozi we wtorek" in w["uwagi"][0]
    assert "minimalnego zamówienia" in w["uwagi"][2]
    assert w["oplaty"] == {MAKRO: 79}
    assert w["czas_wlasciciela"] == {BIEDRONKA: pytest.approx(3.0)}          # dwa dni zakupów po 1,5 h
    assert [(x["dostawca"], x["dzien"], x["oplata"]) for x in w["dostawy"]] == [
        (MAKRO, 0, 0), (BIEDRONKA, 2, 0), (MAKRO, 3, 79), (BIEDRONKA, 4, 0)]


def test_gazetki_i_producent_od_rundy_3():
    dane = dane_domyslne()
    ceny2, gaz2 = dst.oferta_rundy(dane, 1, 2)
    assert ROZEN not in ceny2 and ROZEN in dst.ceny_rundy(dane, 1, 3)
    assert set(gaz2) == {"Biedronka", "Lidl", "Stokrotka"} and len(gaz2["Biedronka"]) == 3
    baza = dst.ceny_miesiaca(dane, 1, dane.miesiac_rundy(2), "dane", 2)   # wrzesień – ceny losowane
    for d, rabaty in gaz2.items():
        for z, r in rabaty.items():
            assert 0.1 <= r <= 0.35
            for q, c in ceny2[d][z].items():
                assert c == pytest.approx(round(baza[d][z][q] * (1 - r), 2))
    assert dst.oferta_rundy(dane, 1, 2) == (ceny2, gaz2)                     # powtarzalne z ziarnem
    assert dst.gazetki(dane, 1, 4, ceny2) != gaz2                             # co tydzień inne
    assert dst.ceny_rundy(dane, 1, 1) == {}


def test_planowanie_w_dni_dostawcy():
    dane = dane_domyslne()
    ceny = dst.ceny_rundy(dane, 1, 3)
    udzialy = [1.0] * 7
    zam = planowanie.zamowienie_zasobow(dane, Firma(nazwa="A"), {"kebab_w_bulce": 300}, ceny, 2, 1.0, udzialy, PN)
    assert zam and not [z for z in zam if dst.info(dane, z["dostawca"])["odbior_osobisty"]]   # bez dyskontów
    for z in zam:
        assert (PN + timedelta(days=z["dzien"])).weekday() in dst.info(dane, z["dostawca"])["dni_dostaw"], z
    przyjete, w = dst.zasady_dostaw(dane, [{**z, "cena": ceny[z["dostawca"]][z["zasob"]][str(z["jakosc"])]} for z in zam], PN, 7)
    assert len(przyjete) == len(zam) and not w["uwagi"]
    # za mały popyt na minimum producenta – mięso od innego dostawcy
    male = planowanie.zamowienie_zasobow(dane, Firma(nazwa="A"), {"kebab_w_bulce": 20}, ceny, 3, 1.0, udzialy, PN)
    assert {z["dostawca"] for z in male if z["zasob"] == "Mięso kebab"} - {ROZEN}
    assert planowanie._dostawy(dane, "Bułka", 7, 0, udzialy, [1, 4]) == [(1, 4), (4, 3)]   # pn–czw, pt–nd


def test_gra_odrzucone_zamowienie_i_oplata_za_dowoz():
    g = _gra(("A", None), ("B", None))
    _runda(g, A=_lokal("centrum_3"))
    dni = pp.dni_rundy(g.dane, 2)
    s = _runda(g, A={"zamowienia": [{"dostawca": MAKRO, "zasob": "Sos", "jakosc": 2, "ilosc": 1, "dzien": 1},
                                    {"dostawca": MAKRO, "zasob": "Tortilla", "jakosc": 2, "ilosc": 2, "dzien": 3},
                                    {"dostawca": PIEKARNIA, "zasob": "Bułka", "jakosc": 2, "ilosc": 10, "dzien": 0}]})
    w = s.wyniki[2]["A"]
    assert {(p.zasob, p.dostawa) for p in s.firmy["A"].partie if p.zasob != "Bułka"} == {("Tortilla", dni[3].isoformat())}
    assert any(b["poziom"] == "czerwony" and b["zakladka"] == "dostawcy" and "nie dowozi" in b["tekst"] for b in w["lista_bledow"])
    kpir = {p["opis"]: p for p in w["kpir"]["pozycje"]}
    assert kpir["Koszt dostawy: Makro"]["pozostale"] == _netto(79)
    assert "Koszt dostawy: Piekarnia Koziołek" not in kpir                    # 10 worków bułek > 150 zł
    assert [(x["dostawca"], x["oplata"]) for x in w["dostawy"]["dostawy"]] == [(PIEKARNIA, 0), (MAKRO, 79)]


def test_sprawdz_dostawcow(tmp_path):
    kat = _kopia(tmp_path)

    def zmien(d):
        d["dostawcy"].pop("Selgros")
        d["dostawcy"]["Lidl"]["gazetka"]["rabat_min"] = 0.5

    _zmien(kat, "dostawcy.yaml", zmien)
    _zmien(kat, "mapa/budynki.yaml", lambda d: d["budynki"].append(
        {**d["budynki"][-1], "id": "atlantyda", "nazwa": "Hurtownia Atlantyda", "rodzaj": "dostawca", "zakladka": "dostawcy",
         "mapa": {"x": 20, "y": 19, "szer": 1, "gl": 1}}))
    bledy = sprawdz(kat)
    assert any("Selgros" in b for b in bledy), bledy
    assert any("rabat_min > rabat_max" in b for b in bledy), bledy
    assert any("Atlantyda" in b for b in bledy), bledy
    _zmien(kat, "dostawcy.yaml", lambda d: d["dostawcy"]["Makro"].update(dni_dostaw=[3, 0]))
    assert any("dni dostaw" in b for b in sprawdz(kat))
