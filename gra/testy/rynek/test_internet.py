"""UF19: marketing internetowy od rundy 7 (dane/mapa/reklama.yaml, sekcja internet; silnik/rynek/reklama.py) –
efekt narasta przez kilka rund i gaśnie wolniej niż reklama tradycyjna, osobna zakładka, prognoza obecności w sieci."""

import copy

import pytest
from pomocnicze import _gra, _lokal, _runda

from silnik.ksiegowosc.finanse import Ksiega, Rachunek
from silnik.model import Kampania
from silnik.rynek import reklama as rk
from silnik.schematy import PlikReklamy

pytestmark = pytest.mark.dane_gry   # sekcja internet jest w dane/, nie w zamrożonej kopii testów

MAPY = {"agencja": "lajk", "kanal": "mapy", "strefa": "centrum", "emisje": 5}


def _firma_z_lokalem():
    g = _gra()
    s = _runda(g, A=_lokal("centrum_3"))
    return g.dane, copy.deepcopy(s.firmy["A"])


def _kampania(agencja="lajk", kanal="mapy", od=7, emisje=5):
    return Kampania(agencja=agencja, kanal=kanal, strefa="centrum", od_rundy=od, do_rundy=od, koszt=100, emisje=emisje)


def test_waga_narasta_potem_wolno_gasnie():
    dane = _gra().dane
    mi = rk.internet(dane)["model"]
    w = [rk.waga_internetu(mi, wiek) for wiek in range(30)]
    assert rk.waga_internetu(mi, -1) is None
    nar = mi["narastanie"]
    assert [x[0] for x in w[:len(nar)]] == nar and all(b > a for a, b in zip(nar, nar[1:]))   # narasta
    assert [x[1] for x in w[:len(nar)]] == ["trwa"] + ["narasta"] * (len(nar) - 1)
    ogon = [x for x in w[len(nar):] if x]
    assert ogon[0] == (pytest.approx(nar[-1] * mi["trwalosc"]), "wygasa")
    assert all(b[0] == pytest.approx(a[0] * mi["trwalosc"]) for a, b in zip(ogon, ogon[1:]))
    assert w[-1] is None and min(x[0] for x in ogon) >= mi["prog_wygasania"]
    assert mi["trwalosc"] > rk.zasady(dane)["model"]["wygasanie"]   # wolniej niż reklama tradycyjna


def test_efekt_w_popycie_narasta_i_trwa_dluzej_niz_ulotek():
    dane, f = _firma_z_lokalem()
    mi = rk.internet(dane)["model"]
    kan = rk.kanal(dane, "lajk", "mapy")
    f.kampanie = [_kampania()]
    suma = [(rk.efekty_rundy(dane, {"A": f}, r)["suma"].get("A") or {}).get("centrum", 0.0) for r in range(6, 13)]
    pelny = kan["przyciaganie"] * rk.efekt_emisji(dane, 5)
    assert suma[0] == 0                                                      # przed emisją nic
    assert suma[1] == pytest.approx(pelny * mi["narastanie"][0], abs=1e-4)  # runda emisji – część efektu
    assert suma[1] < suma[2] < suma[3] and suma[3] == pytest.approx(pelny, abs=1e-4)
    assert suma[4] == pytest.approx(pelny * mi["trwalosc"], abs=1e-4)
    ulotki = copy.deepcopy(f)
    ulotki.kampanie = [_kampania("papier_przyjmie", "ulotki")]
    trad = [bool(rk.efekty_rundy(dane, {"A": ulotki}, r)["kampanie"]) for r in range(7, 20)]
    net = [bool(rk.efekty_rundy(dane, {"A": f}, r)["kampanie"]) for r in range(7, 20)]
    assert sum(net) > sum(trad) + 3                                          # działa kilka rund dłużej
    wpis = rk.efekty_rundy(dane, {"A": f}, 8)["kampanie"]["A"][0]
    assert wpis["internet"] and wpis["faza"] == "narasta" and wpis["koszt"] == 0


def test_zamowienie_od_rundy_7_i_uwagi_w_zakladce_internet():
    dane, f = _firma_z_lokalem()
    assert all(k["od_rundy"] == 7 for a in rk.internet(dane)["agencje"].values() for k in a["kanaly"].values())
    ks, rach = Ksiega(vat=dane.podatki["vat"]), Rachunek()
    info = rk.zamow(dane, f, {"kampanie": [MAPY, {**MAPY, "agencja": "papier_przyjmie", "kanal": "ulotki"}]}, 5, ks, rach)
    assert info["uwagi_internet"] == ["Wizytówka w Mapach Google i opinie (Agencja „Lajk i Spółka”): dostępne od rundy 7."]
    assert [z["kanal"] for z in info["zamowione"]] == ["ulotki"] and info["uwagi"] == []
    info = rk.zamow(dane, f, {"kampanie": [MAPY]}, 7, ks, rach)
    assert [z["kanal"] for z in info["zamowione"]] == ["mapy"] and not info["uwagi_internet"]
    assert rk.ZAKLADKA_INTERNET == "internet"


def test_widok_agencje_obu_rodzajow_i_prognoza_obecnosci():
    dane, f = _firma_z_lokalem()
    f.kampanie = [_kampania(od=7)]
    v = rk.widok(dane, f, 8, None)
    rodzaje = {a["id"]: a["internet"] for a in v["agencje"]}
    assert rodzaje["lajk"] and not rodzaje["papier_przyjmie"]
    mi, kan = v["internet"]["model"], rk.kanal(dane, "lajk", "mapy")
    pelny = kan["przyciaganie"] * rk.efekt_emisji(dane, 5)
    oczek = [pelny * mi["narastanie"][1], pelny * mi["narastanie"][2], pelny * mi["trwalosc"], pelny * mi["trwalosc"] ** 2]
    assert v["internet"]["prognoza"]["centrum"] == [pytest.approx(x, abs=1e-4) for x in oczek]
    f.kampanie = [_kampania("papier_przyjmie", "ulotki")]
    assert rk.widok(dane, f, 8, None)["internet"]["prognoza"] == {}   # ulotki to nie obecność w sieci


def test_harmonogram_i_schemat():
    from silnik.harmonogram import elementy
    dane = _gra().dane
    el = elementy(dane)
    assert el["internet"]["tydzien"] == 7 and el["internet"]["grupa"] == "Marketing"
    assert all("internet" not in s for s in el["reklama"]["sciezki"] + el["reklama_wszystkie"]["sciezki"])
    R = copy.deepcopy(rk.zasady(dane))
    R["agencje"]["lajk"] = R["internet"]["agencje"]["lajk"]
    with pytest.raises(ValueError, match="jednocześnie"):
        PlikReklamy.model_validate({"opis": "test", "zrodlo": "test", **R})
