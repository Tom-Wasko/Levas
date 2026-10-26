"""Agencje reklamowe w grze z lokalami (F3b.2): koszt, zamówienie z walidacją, zagłuszanie, nasycenie, wygasanie,
poszerzenie puli i przyciąganie klientów, gra z botami, widok API i brak reklamy z Revasa."""

import copy

import pytest
from test_lokale import _gra, _lokal, _runda
from test_popyt import KEBAB, _oferta

from silnik import boty
from silnik import popyt as pp
from silnik import reklama as rk
from silnik.dane import dane_domyslne
from silnik.finanse import Ksiega, Rachunek
from silnik.model import Firma, Kampania

ULOTKI = {"agencja": "papier_przyjmie", "kanal": "ulotki", "strefa": "centrum"}


def _firma_z_lokalem(runda=3):
    g = _gra()
    s = _runda(g, A=_lokal("centrum_3"))
    return g.dane, copy.deepcopy(s.firmy["A"])


def _zamow(dane, f, kampanie, runda=3):
    ks, rach = Ksiega(vat=dane.podatki["vat"]), Rachunek()
    return rk.zamow(dane, f, {"kampanie": kampanie}, runda, ks, rach), ks, rach


def _kampania(agencja="papier_przyjmie", kanal="ulotki", strefa="centrum", od=3, do=3, sila=1.0):
    return Kampania(agencja=agencja, kanal=kanal, strefa=strefa, od_rundy=od, do_rundy=do, koszt=100, sila=sila)


def test_koszt_strefy_i_miasta():
    dane = dane_domyslne()
    ulotki, radio = rk.kanal(dane, "papier_przyjmie", "ulotki"), rk.kanal(dane, "fala_koziolka", "radio")
    pule = dane.mapa["popyt"]["strefy"]
    assert rk.koszt(dane, ulotki, "centrum") == pytest.approx(round(ulotki["koszt"] * pule["centrum"]["pula"] / 10) * 10)
    assert rk.koszt(dane, radio, None) == radio["koszt"] and rk.strefy_kanalu(dane, radio) == []
    assert rk.brutto(dane, 100) == pytest.approx(123)
    assert rk.strefy_kanalu(dane, rk.kanal(dane, "kozi_grod", "noc_kebaba")) == ["akademickie", "politechnika"]


def test_zamowienie_walidacja_vat_i_kpir():
    dane, f = _firma_z_lokalem()
    info, ks, rach = _zamow(dane, f, [
        ULOTKI,
        {"agencja": "papier_przyjmie", "kanal": "nie_ma"},
        {"agencja": "papier_przyjmie", "kanal": "plakaty"},                       # bez strefy
        {"agencja": "kozi_grod", "kanal": "noc_kebaba", "strefa": "centrum"},     # tylko strefy akademickie
        {"agencja": "lajk", "kanal": "influencer", "strefa": "centrum"},          # od rundy 5
        {"agencja": "papier_przyjmie", "kanal": "ulotki", "strefa": "centrum"},   # ta sama kampania jeszcze trwa
        {"agencja": "fala_koziolka", "kanal": "radio", "strefa": "centrum"},      # od rundy 5
    ])
    assert [(z["kanal"], z["strefa"]) for z in info["zamowione"]] == [("ulotki", "centrum")]
    assert len(info["uwagi"]) == 6 and any("wybierz strefę" in u for u in info["uwagi"])
    assert any("od rundy 5" in u for u in info["uwagi"]) and any("jeszcze trwa" in u for u in info["uwagi"])
    netto = rk.koszt(dane, rk.kanal(dane, "papier_przyjmie", "ulotki"), "centrum")
    poz = [p for p in ks.pozycje if p["opis"].startswith(rk.OPIS)]
    assert [p["pozostale"] for p in poz] == [pytest.approx(netto)]
    assert sum(o["kwota"] for o in rach.operacje) == pytest.approx(-rk.brutto(dane, netto))
    assert [(k.kanal, k.od_rundy, k.do_rundy, k.sila) for k in f.kampanie] == [("ulotki", 3, 3, 1.0)]
    # radio na całe miasto: strefa z decyzji pomijana
    info, _, _ = _zamow(dane, f, [{"agencja": "fala_koziolka", "kanal": "radio", "strefa": "centrum"}], runda=5)
    assert info["zamowione"][0]["strefa"] is None and info["zamowione"][0]["do_rundy"] == 6
    # bez lokalu agencja nie przyjmuje zlecenia
    info, _, _ = _zamow(dane, Firma(nazwa="X"), [ULOTKI])
    assert not info["zamowione"] and "z lokalem" in info["uwagi"][0]


def test_nasycenie_i_wygasanie():
    dane, f = _firma_z_lokalem()
    m = rk.zasady(dane)["model"]
    f.kampanie = [_kampania(od=3, do=3)]
    assert rk.sila_nowej(dane, f, "papier_przyjmie", "ulotki", "centrum", 4) == pytest.approx(1 - m["nasycenie"])
    assert rk.sila_nowej(dane, f, "papier_przyjmie", "ulotki", "dworzec", 4) == 1.0          # inna strefa
    assert rk.sila_nowej(dane, f, "papier_przyjmie", "ulotki", "centrum", 3 + m["okno_nasycenia"]) == 1.0
    f.kampanie.append(_kampania(od=4, do=4, sila=0.7))
    assert rk.sila_nowej(dane, f, "papier_przyjmie", "ulotki", "centrum", 5) == pytest.approx((1 - m["nasycenie"]) ** 2)
    f.kampanie = [_kampania(od=3, do=3)]
    pula = rk.kanal(dane, "papier_przyjmie", "ulotki")["pula"]
    fazy = [rk.efekty_rundy(dane, {"A": f}, r) for r in (2, 3, 4, 5, 6, 7)]
    assert fazy[0]["kampanie"] == {} and fazy[1]["pula"]["centrum"] == pytest.approx(pula)
    assert fazy[2]["kampanie"]["A"][0]["faza"] == "wygasa" and fazy[2]["pula"]["centrum"] == pytest.approx(pula * m["wygasanie"])
    assert fazy[3]["pula"]["centrum"] == pytest.approx(pula * m["wygasanie"] ** 2)
    assert fazy[5]["kampanie"] == {}                                                       # poniżej progu – koniec
    assert fazy[1]["firmy"]["A"] == {"centrum": pytest.approx(rk.kanal(dane, "papier_przyjmie", "ulotki")["przyciaganie"])}


def test_zagluszanie_ten_sam_rodzaj_i_radio_w_kazdej_strefie():
    dane, f = _firma_z_lokalem()
    m = rk.zasady(dane)["model"]
    a, b, c = (copy.deepcopy(f) for _ in range(3))
    a.kampanie = [_kampania()]
    b.kampanie = [_kampania(kanal="plakaty")]                                        # ten sam rodzaj (druk)
    c.kampanie = [_kampania(agencja="lajk", kanal="grupa_osiedlowa")]                # inny rodzaj
    ef = rk.efekty_rundy(dane, {"A": a, "B": b, "C": c}, 3)
    zag = {n: ef["kampanie"][n][0]["zagluszanie"] for n in "ABC"}
    assert zag == {"A": pytest.approx(1 / (1 + m["zagluszanie"]), abs=1e-4), "B": pytest.approx(1 / (1 + m["zagluszanie"]), abs=1e-4),
                   "C": 1.0}
    assert ef["kampanie"]["A"][0]["konkurenci"] == 1
    # radio (całe miasto) zagłusza billboard tego samego rodzaju w każdej strefie i działa wszędzie
    a.kampanie = [_kampania(agencja="fala_koziolka", kanal="radio", strefa=None, od=5, do=6)]
    b.kampanie = [_kampania(agencja="fala_koziolka", kanal="billboard", strefa="dworzec", od=5, do=7)]
    ef = rk.efekty_rundy(dane, {"A": a, "B": b}, 5)
    assert set(ef["firmy"]["A"]) == set(dane.mapa["strefy"]) and ef["kampanie"]["B"][0]["konkurenci"] == 1
    assert ef["firmy"]["A"]["dworzec"] < ef["firmy"]["A"]["centrum"]


def test_pula_i_przyciaganie_w_popycie():
    dane = dane_domyslne()
    zwykla, szersza = pp.pule(dane, 5), pp.pule(dane, 5, reklama={"centrum": 0.1})
    assert szersza["centrum"][KEBAB].sum() == pytest.approx(1.1 * zwykla["centrum"][KEBAB].sum())
    assert szersza["dworzec"][KEBAB].sum() == pytest.approx(zwykla["dworzec"][KEBAB].sum())
    oferty = {KEBAB: {("A", "centrum"): _oferta("centrum", reklama_strefy={"centrum": 0.2}), ("B", "centrum"): _oferta("centrum")}}
    pod = pp.podzial(dane, zwykla, oferty)
    a, b = (pod[(n, "centrum")][KEBAB]["strefy"]["centrum"] for n in "AB")
    assert a > 1.1 * b
    # przyciąganie działa tylko na mieszkańców strefy kampanii
    assert pod[("A", "centrum")][KEBAB]["strefy"]["dworzec"] == pytest.approx(pod[("B", "centrum")][KEBAB]["strefy"]["dworzec"])


def test_gra_kampania_popyt_wyniki_i_bledy(monkeypatch):
    # dwa boty w Centrum; bot A w rundzie 3 dostaje kampanie (i reklamę z Revasa, której w grze z lokalami nie ma)
    dodatki = {}
    bot = boty.decyzje_bota
    monkeypatch.setattr(boty, "decyzje_bota", lambda dane, stan, nazwa, *a: {**bot(dane, stan, nazwa, *a), **dodatki.get((nazwa, a[1]), {})})
    monkeypatch.setattr(boty, "_wybierz_lokal", lambda dane, stan, nazwa, *a: _lokal({"A": "centrum_3", "B": "centrum_1"}[nazwa])["lokal"])
    g = _gra(("A", "nasladowca"), ("B", "nasladowca"))
    g.przelicz(wymus=True)
    g.przelicz(wymus=True)
    s0 = copy.deepcopy(g).przelicz(wymus=True)
    dodatki[("A", 3)] = {"kampanie": [{"agencja": "kozi_grod", "kanal": "degustacja", "strefa": "centrum"},
                                      {"agencja": "papier_przyjmie", "kanal": "ulotki"}],
                         "reklama_tradycyjna": {"Ulotki": 10}}
    s = g.przelicz(wymus=True)
    popyt = {n: (sum(v["popyt"] for v in s0.wyniki[3][n]["sprzedaz"].values()),
                 sum(v["popyt"] for v in s.wyniki[3][n]["sprzedaz"].values())) for n in "AB"}
    assert popyt["A"][1] > 1.03 * popyt["A"][0]
    w = s.wyniki[3]["A"]
    ra = w["reklama_agencje"]
    assert [z["kanal"] for z in ra["zamowione"]] == ["degustacja"]
    assert ra["kampanie"][0]["tekst"] and "{" not in ra["kampanie"][0]["tekst"] and "Centrum" in ra["kampanie"][0]["tekst"]
    assert ra["pula_stref"]["centrum"] > 0
    assert [b["tekst"] for b in w["lista_bledow"] if b["zakladka"] == rk.ZAKLADKA] == [
        "Ulotki za wycieraczki (Drukarnia „Papier Przyjmie”): wybierz strefę."]
    assert not any(p["opis"].startswith("Reklama tradycyjna") for p in w["kpir"]["pozycje"])   # bez reklamy z Revasa
    assert w["reklama"] == {"tradycyjna": 0.0, "internetowa": 0.0}
    assert s.rynek[3]["kampanie"]["A"]["wydatki"] == ra["zamowione"][0]["koszt"] and "B" not in s.rynek[3]["kampanie"]
    s = g.przelicz(wymus=True)
    assert s.wyniki[4]["A"]["reklama_agencje"]["kampanie"][0]["faza"] == "wygasa"
    assert s.rynek[4]["kampanie"]["A"]["wydatki"] == 0


def test_boty_zamawiaja_kampanie_w_swojej_strefie():
    g = _gra(("Agr", "agresywny"), ("Zrown", "zrownowazony"))
    for _ in range(5):
        s = g.przelicz(wymus=True)
    for n in ("Agr", "Zrown"):
        f = s.firmy[n]
        strefy = {g.dane.lokale[lok.id]["strefa"] for lok in f.lokale}
        assert f.kampanie and all(k.strefa in strefy or k.strefa is None for k in f.kampanie), n
        assert not f.internet
    assert {k.kanal for k in s.firmy["Agr"].kampanie} > {"plakaty"}


def test_widok_api_i_gra_bez_lokali():
    from api.prezentacja import widok
    g = _gra()
    _runda(g, A=_lokal("centrum_3"))
    _runda(g)
    g.ustaw_decyzje("A", {"kampanie": [ULOTKI]})
    r = widok(g, "A")["reklama"]
    assert r["moje_strefy"] == ["centrum"] and [z["kanal"] for z in r["zamowione"]] == ["ulotki"]
    kanaly = {k["id"]: k for a in r["agencje"] for k in a["kanaly"]}
    assert kanaly["ulotki"]["dostepny"] and not kanaly["influencer"]["dostepny"]
    assert kanaly["ulotki"]["trwa"] == [] and kanaly["radio"]["koszty"] == {"miasto": kanaly["radio"]["koszty"]["miasto"]}
    assert [x["faza"] for x in r["trwajace"]] == ["trwa"]
    v = widok(_gra(lokale=False), "A")
    assert "reklama" not in v
