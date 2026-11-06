"""Agencje reklamowe w grze z lokalami (F3b.2, Z5): emisje, progi rabatów, zamówienie z walidacją, zagłuszanie,
nasycenie emisjami, wygasanie, poszerzenie puli i przyciąganie klientów, gra z botami, widok API i brak reklamy z Revasa."""

import copy
import math

import pytest
from pomocnicze import KEBAB, _gra, _lokal, _oferta, _runda

from silnik import boty
from silnik.dane import dane_domyslne
from silnik.ksiegowosc.finanse import Ksiega, Rachunek
from silnik.model import Firma, Kampania
from silnik.rynek import popyt as pp
from silnik.rynek import reklama as rk

ULOTKI = {"agencja": "papier_przyjmie", "kanal": "ulotki", "strefa": "centrum", "emisje": 5}


def _firma_z_lokalem(runda=3):
    g = _gra()
    s = _runda(g, A=_lokal("centrum_3"))
    return g.dane, copy.deepcopy(s.firmy["A"])


def _zamow(dane, f, kampanie, runda=3):
    ks, rach = Ksiega(vat=dane.podatki["vat"]), Rachunek()
    return rk.zamow(dane, f, {"kampanie": kampanie}, runda, ks, rach), ks, rach


def _kampania(agencja="papier_przyjmie", kanal="ulotki", strefa="centrum", od=3, do=None, emisje=None):
    return Kampania(agencja=agencja, kanal=kanal, strefa=strefa, od_rundy=od, do_rundy=od if do is None else do, koszt=100,
                    emisje=emisje)


def test_koszt_emisji_i_progi_rabatow():
    dane = dane_domyslne()
    ulotki, radio = rk.kanal(dane, "papier_przyjmie", "ulotki"), rk.kanal(dane, "fala_koziolka", "radio")
    pule = dane.mapa["popyt"]["strefy"]
    c = rk.cena_emisji(dane, ulotki, "centrum")
    assert c == round(ulotki["cena_emisji"] * pule["centrum"]["pula"])
    assert rk.cena_emisji(dane, radio, None) == radio["cena_emisji"] and rk.strefy_kanalu(dane, radio) == []
    (od1, r1), (od2, r2) = ulotki["znizki"][:2]
    assert [rk.rabat(ulotki, n) for n in (1, od1 - 1, od1, od2 - 1, od2, ulotki["maks_emisji"])] == [0, 0, r1, r1, r2, r2]
    assert rk.koszt(dane, ulotki, "centrum", od1 - 1) == pytest.approx((od1 - 1) * c)
    assert rk.koszt(dane, ulotki, "centrum", od1) == pytest.approx(od1 * c * (1 - r1))     # rabat na wszystkie emisje
    assert rk.brutto(dane, 100) == pytest.approx(123)
    assert rk.strefy_kanalu(dane, rk.kanal(dane, "kozi_grod", "noc_kebaba")) == ["akademickie", "politechnika"]


def test_zamowienie_walidacja_vat_i_kpir():
    dane, f = _firma_z_lokalem()
    info, ks, rach = _zamow(dane, f, [
        ULOTKI,
        {"agencja": "papier_przyjmie", "kanal": "nie_ma"},
        {"agencja": "papier_przyjmie", "kanal": "plakaty", "emisje": 3},                       # bez strefy
        {"agencja": "kozi_grod", "kanal": "noc_kebaba", "strefa": "centrum", "emisje": 3},     # tylko strefy akademickie
        {"agencja": "lajk", "kanal": "influencer", "strefa": "centrum", "emisje": 3},          # od rundy 5
        {"agencja": "papier_przyjmie", "kanal": "ulotki", "strefa": "centrum", "emisje": 2},   # już zamówiona w tej rundzie
        {"agencja": "fala_koziolka", "kanal": "radio", "strefa": "centrum", "emisje": 3},      # od rundy 5
        {"agencja": "papier_przyjmie", "kanal": "plakaty", "strefa": "centrum"},               # bez emisji
        {"agencja": "papier_przyjmie", "kanal": "plakaty", "strefa": "centrum", "emisje": 999},  # ponad maks_emisji
    ])
    assert [(z["kanal"], z["strefa"], z["emisje"]) for z in info["zamowione"]] == [("ulotki", "centrum", 5)]
    assert len(info["uwagi"]) == 8 and any("wybierz strefę" in u for u in info["uwagi"])
    assert any("od rundy 5" in u for u in info["uwagi"]) and any("już zamówiona" in u for u in info["uwagi"])
    assert any("podaj liczbę emisji" in u for u in info["uwagi"]) and any("najwyżej" in u for u in info["uwagi"])
    netto = rk.koszt(dane, rk.kanal(dane, "papier_przyjmie", "ulotki"), "centrum", 5)
    poz = [p for p in ks.pozycje if p["opis"].startswith(rk.OPIS)]
    assert [p["pozostale"] for p in poz] == [pytest.approx(netto)]
    assert sum(o["kwota"] for o in rach.operacje) == pytest.approx(-rk.brutto(dane, netto))
    assert [(k.kanal, k.od_rundy, k.do_rundy, k.emisje) for k in f.kampanie] == [("ulotki", 3, 3, 5)]
    assert "5 × paczka" in poz[0]["opis"]
    # radio na całe miasto: strefa z decyzji pomijana, działa tylko w rundzie emisji
    info, _, _ = _zamow(dane, f, [{"agencja": "fala_koziolka", "kanal": "radio", "strefa": "centrum", "emisje": 10}], runda=5)
    assert info["zamowione"][0]["strefa"] is None and info["zamowione"][0]["do_rundy"] == 5
    # w następnej rundzie tę samą kampanię można zamówić znowu (bez osłabienia – nasyca się tylko liczba emisji)
    info, _, _ = _zamow(dane, f, [ULOTKI], runda=4)
    assert [z["emisje"] for z in info["zamowione"]] == [5] and not info["uwagi"]
    # bez lokalu agencja nie przyjmuje zlecenia
    info, _, _ = _zamow(dane, Firma(nazwa="X"), [ULOTKI])
    assert not info["zamowione"] and "z lokalem" in info["uwagi"][0]


def test_nasycenie_emisjami_i_wygasanie():
    dane, f = _firma_z_lokalem()
    m = rk.zasady(dane)["model"]
    e = [rk.efekt_emisji(dane, n) for n in range(0, 21)]
    assert e[0] == 0 and e[1] == pytest.approx(1 - math.exp(-m["tempo_emisji"])) and rk.efekt_emisji(dane, None) == 1
    assert all(b > a for a, b in zip(e, e[1:])) and e[10] > 0.9                           # ok. 10 emisji – ponad 90%
    assert all(e[n + 1] - e[n] < e[n] - e[n - 1] for n in range(1, 20))                    # każda kolejna daje mniej
    f.kampanie = [_kampania(emisje=5)]
    pula5 = rk.kanal(dane, "papier_przyjmie", "ulotki")["pula"] * e[5]
    assert rk.efekty_rundy(dane, {"A": f}, 3)["pula"]["centrum"] == pytest.approx(rk.nasycenie(pula5, m["maks_puli"]), abs=1e-4)
    assert rk.efekty_rundy(dane, {"A": f}, 3)["kampanie"]["A"][0]["nasycenie"] == pytest.approx(e[5], abs=1e-4)
    f.kampanie = [_kampania()]                                  # zapis sprzed Z5 (bez emisji) – pełny efekt
    pula = rk.kanal(dane, "papier_przyjmie", "ulotki")["pula"]
    fazy = [rk.efekty_rundy(dane, {"A": f}, r) for r in (2, 3, 4, 5, 6, 7)]
    P = lambda x: pytest.approx(rk.nasycenie(x, m["maks_puli"]), abs=1e-4)   # P10: sufit sumy kampanii
    assert fazy[0]["kampanie"] == {} and fazy[1]["pula"]["centrum"] == P(pula)
    assert fazy[2]["kampanie"]["A"][0]["faza"] == "wygasa" and fazy[2]["pula"]["centrum"] == P(pula * m["wygasanie"])
    assert fazy[3]["pula"]["centrum"] == P(pula * m["wygasanie"] ** 2)
    assert fazy[5]["kampanie"] == {}                                                       # poniżej progu – koniec
    przyc = rk.kanal(dane, "papier_przyjmie", "ulotki")["przyciaganie"]
    assert fazy[1]["firmy"]["A"] == {"centrum": pytest.approx(rk.nasycenie(przyc, m["maks_przyciagania"]), abs=1e-4)}
    assert fazy[1]["suma"]["A"] == {"centrum": pytest.approx(przyc)}


def test_sufit_sumy_kampanii():
    """P10: kampanie się sumują z nasyceniem – jedna prawie w pełni, wiele naraz nie przekroczy sufitu."""
    dane, f = _firma_z_lokalem()
    m = rk.zasady(dane)["model"]
    R = rk.zasady(dane)["agencje"]
    f.kampanie = [_kampania(agencja=a, kanal=k, strefa=None if kan["zasieg"] == "miasto" else "centrum", od=5, emisje=kan["maks_emisji"])
                  for a, ag in R.items() for k, kan in ag["kanaly"].items() if kan["zasieg"] == "miasto" or "centrum" in (kan.get("strefy") or ["centrum"])]
    ef = rk.efekty_rundy(dane, {"A": f}, 5)
    suma, dziala = ef["suma"]["A"]["centrum"], ef["firmy"]["A"]["centrum"]
    assert suma > m["maks_przyciagania"] * 0.9 and dziala < m["maks_przyciagania"] and dziala < suma
    assert ef["pula"]["centrum"] < m["maks_puli"]
    assert rk.nasycenie(0.1, m["maks_przyciagania"]) > 0.09   # mała kampania – prawie bez strat


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
    a.kampanie = [_kampania(agencja="fala_koziolka", kanal="radio", strefa=None, od=5, emisje=10)]
    b.kampanie = [_kampania(agencja="fala_koziolka", kanal="billboard", strefa="dworzec", od=5, emisje=4)]
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
    monkeypatch.setattr(boty, "_wybierz_lokal", lambda dane, stan, nazwa, *a: (_lokal({"A": "centrum_3", "B": "centrum_1"}[nazwa])["lokal"], None))
    g = _gra(("A", "nasladowca"), ("B", "nasladowca"))
    g.przelicz(wymus=True)
    g.przelicz(wymus=True)
    s0 = copy.deepcopy(g).przelicz(wymus=True)
    dodatki[("A", 3)] = {"kampanie": [{"agencja": "kozi_grod", "kanal": "degustacja", "strefa": "centrum", "emisje": 8},
                                      {"agencja": "papier_przyjmie", "kanal": "ulotki", "emisje": 5}],
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
    ust = g.dane.boty["ustawienia"]
    for n in ("Agr", "Zrown"):   # emisje ze strategii, przerwa między kampaniami w tym samym kanale i strefie
        k = s.firmy[n].kampanie
        assert all(x.emisje == min(ust["emisje_kampanii"], rk.kanal(g.dane, x.agencja, x.kanal)["maks_emisji"]) for x in k)
        for x in k:
            assert not any((y.agencja, y.kanal, y.strefa) == (x.agencja, x.kanal, x.strefa)
                           and 0 < y.od_rundy - x.od_rundy <= ust["przerwa_kampanii"] for y in k)


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
    assert list(kanaly["radio"]["ceny"]) == ["miasto"] and kanaly["ulotki"]["znizki"] and kanaly["ulotki"]["emisja"]
    assert [(x["faza"], x["emisje"]) for x in r["trwajace"]] == [("trwa", 5)]


def test_strategia_nadpisuje_emisje_i_przerwe_kampanii():
    """B10: emisje_kampanii i przerwa_kampanii ze strategii mają pierwszeństwo przed ustawieniami botów."""
    g = _gra(("Zrown", "zrownowazony"), ("Tani", "tani"))
    st = g.dane.boty["strategie"]
    g.dane = copy.copy(g.dane)
    g.dane.boty = {**g.dane.boty, "strategie": {**st, "zrownowazony": {**st["zrownowazony"],
                                                                       "emisje_kampanii": 3, "przerwa_kampanii": 0}}}
    for _ in range(6):
        s = g.przelicz(wymus=True)
    k = s.firmy["Zrown"].kampanie
    assert k and all(x.emisje == 3 for x in k)
    rundy = sorted(x.od_rundy for x in k if (x.agencja, x.kanal) == ("papier_przyjmie", "ulotki"))
    assert len(rundy) >= 2 and any(b - a == 1 for a, b in zip(rundy, rundy[1:]))   # bez przerwy – co rundę
    assert all(x.emisje == g.dane.boty["ustawienia"]["emisje_kampanii"] for x in s.firmy["Tani"].kampanie)
