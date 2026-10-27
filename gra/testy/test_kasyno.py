"""Portfel właściciela i tajny klub (F3b.7): wpłaty i wypłaty własne poza KPiR, zaproszenie, zakłady, podgląd,
ukrycie klubu (i portfela) przed mistrzem gry oraz wyłączenie klubu na serwerze."""

import copy
import json

import pytest
import yaml
from pydantic import ValidationError
from test_lokale import _gra, _runda

from silnik import kasyno as kas
from silnik import wlasciciel as wl
from silnik.dane import KATALOG_DANYCH, dane_domyslne
from silnik.schematy import PlikKasyna

JSON = "application/json"
DRUZYNA = "Kebab Ali"
SLADY = ("Nocna", "Złotym Kaflem", '"kasyno"', '"portfel', '"zaproszenia"', "Waldemar", "pietruszka")


def _surowe():
    return yaml.safe_load((KATALOG_DANYCH / "zdarzenia" / "kasyno.yaml").read_text(encoding="utf-8"))


@pytest.fixture
def zawsze_zaproszenie(monkeypatch):
    """Zaproszenie od 1. rundy z pewnością – klub otwarty w rundzie 2 (i 3, bo maks to 2 zaproszenia)."""
    oryginal = kas.dane_kasyna

    def dane(d):
        K = copy.deepcopy(oryginal(d))
        if K:
            K["zaproszenie"].update(od_rundy=1, szansa=1)
        return K

    monkeypatch.setattr(kas, "dane_kasyna", dane)


def test_dane_kasyna_i_portfela():
    dane = dane_domyslne()
    K = kas.dane_kasyna(dane)
    assert K and wl.dane_portfela(dane)["portfel"]["oszczednosci"] > 0
    assert {g["typ"] for g in K["gry"].values()} == {"ruletka", "automat"}
    assert all("{" not in t or "{kwota}" in t or "{liczba}" in t for g in K["gry"].values()
               for t in [*(g.get("teksty_wygrana") or []), *(g.get("teksty_przegrana") or []), *(w["tekst"] for w in g.get("wyniki") or [])])
    w = _surowe()
    automat = next(g for g in w["gry"].values() if g["typ"] == "automat")
    automat["wyniki"][0]["szansa"] += 0.1
    with pytest.raises(ValidationError):
        PlikKasyna.model_validate(w)
    w = _surowe()
    ruletka = next(g for g in w["gry"].values() if g["typ"] == "ruletka")
    ruletka["zaklady"][next(iter(ruletka["zaklady"]))]["wygrywa"].append(ruletka["pola"])
    with pytest.raises(ValidationError):
        PlikKasyna.model_validate(w)
    w = _surowe()
    w["zaklady"]["min_stawka"] = w["zaklady"]["maks_stawka"] + 1
    with pytest.raises(ValidationError):
        PlikKasyna.model_validate(w)


def test_wplata_i_wyplata_wlasna_poza_kpir():
    g = _gra()
    oszczednosci = float(wl.dane_portfela(g.dane)["portfel"]["oszczednosci"])
    s = _runda(g, A={"wyplata_wlasna": 1000}, B={"wplata_wlasna": oszczednosci + 500})
    wa, wb = s.wyniki[1]["A"], s.wyniki[1]["B"]
    assert wa["wlasciciel"]["wyplata"] == 1000 and wa["wlasciciel"]["portfel"] == oszczednosci + 1000
    assert wb["wlasciciel"]["wplata"] == oszczednosci and wb["wlasciciel"]["portfel"] == 0
    assert any(b["zakladka"] == wl.ZAKLADKA for b in wb["lista_bledow"])
    assert not any(b["zakladka"] == wl.ZAKLADKA for b in wa["lista_bledow"])
    for w, kwota in ((wa, -1000), (wb, oszczednosci)):
        assert [p["kwota"] for p in w["rachunek"] if p["rodzaj"] == wl.RODZAJ] == [kwota]
        assert w["uzgodnienie"]["roznica"] == 0
    # podatek bez zmian: wpłata nie jest przychodem, wypłata nie jest kosztem
    g2 = _gra()
    s2 = _runda(g2)
    for firma in ("A", "B"):
        assert s.wyniki[1][firma]["kpir"] == s2.wyniki[1][firma]["kpir"]
        assert s.wyniki[1][firma]["rozliczenie"] == s2.wyniki[1][firma]["rozliczenie"]
    assert s.firmy["A"].gotowka == pytest.approx(s2.firmy["A"].gotowka - 1000)
    # wypłata najwyżej tyle, ile jest na koncie
    s = _runda(g, A={"wyplata_wlasna": 10**7})
    W = s.wyniki[2]["A"]["wlasciciel"]
    assert 0 < W["wyplata"] < 10**7 and W["odrzucone"] and s.wyniki[2]["A"]["uzgodnienie"]["roznica"] == 0


def test_bez_zaproszenia_drzwi_zamkniete():
    g = _gra()
    s = _runda(g, A={"kasyno": [{"gra": "automat", "zaklad": None, "stawka": 100}]})
    W = s.wyniki[1]["A"]
    assert W["kasyno"]["gry"]["odrzucone"] and not W["kasyno"]["gry"]["zaklady"]
    assert W["wlasciciel"]["portfel"] == wl.dane_portfela(g.dane)["portfel"]["oszczednosci"]
    assert any(b["zakladka"] == kas.ZAKLADKA for b in W["lista_bledow"])


def test_zaproszenie_i_zaklady(zawsze_zaproszenie):
    g = _gra(("A", None), ("Bot", "tani"))
    s = _runda(g)
    assert s.firmy["A"].zaproszenia == [2] and not s.firmy["Bot"].zaproszenia
    assert s.wyniki[1]["A"]["kasyno"] == {"gry": None, "zaproszenie": 2}
    K = kas.dane_kasyna(g.dane)
    ruletka = next(k for k, x in K["gry"].items() if x["typ"] == "ruletka")
    automat = next(k for k, x in K["gry"].items() if x["typ"] == "automat")
    zaklad = next(iter(K["gry"][ruletka]["zaklady"]))
    przed = wl.portfel(g.dane, s.firmy["A"])
    zaklady = [{"gra": ruletka, "zaklad": zaklad, "stawka": 100}, {"gra": automat, "zaklad": None, "stawka": 50},
               {"gra": ruletka, "zaklad": "nie-ma", "stawka": 100}, {"gra": automat, "stawka": przed * 10}]
    s = _runda(g, A={"kasyno": zaklady, "wplata_wlasna": 10**6})
    Z = s.wyniki[2]["A"]["kasyno"]["gry"]
    assert [z["gra"] for z in Z["zaklady"]] == [ruletka, automat] and len(Z["odrzucone"]) == 2
    assert Z["stawki"] == 150 and Z["bilans"] == round(Z["wyplaty"] - 150, 2)
    assert all(z["tekst"] and "{" not in z["tekst"] for z in Z["zaklady"])
    W = s.wyniki[2]["A"]["wlasciciel"]
    assert W["wplata"] == round(przed + Z["bilans"], 2) and W["portfel"] == 0   # wygrana od razu do firmy
    assert s.wyniki[2]["A"]["uzgodnienie"]["roznica"] == 0
    # wynik powtarzalny przy ponownym przeliczeniu (event sourcing)
    assert g.przelicz(wymus=True).wyniki[2]["A"]["kasyno"]["gry"] == Z
    # drugie zaproszenie, potem limit
    assert s.firmy["A"].zaproszenia == [2, 3]
    s = _runda(g)
    s = _runda(g)
    assert s.firmy["A"].zaproszenia == [2, 3]


def test_podglad_bez_wynikow_i_ukrycie(zawsze_zaproszenie):
    from api.prezentacja import widok
    g = _gra()
    _runda(g)
    K = kas.dane_kasyna(g.dane)
    automat = next(k for k, x in K["gry"].items() if x["typ"] == "automat")
    g.ustaw_decyzje("A", {"kasyno": [{"gra": automat, "stawka": 100}]})
    v = widok(g, "A")
    assert v["kasyno"]["otwarte"] and v["kasyno"]["zaproszenie"] in K["zaproszenie"]["teksty"]
    D = v["kasyno"]["decyzja"]
    assert D["ukryte"] and D["stawki"] == 100 and "wyplaty" not in D and "wyplata" not in D["zaklady"][0]
    assert v["wlasciciel"]["portfel_po"] == v["wlasciciel"]["portfel_przed"] - 100
    tekst = json.dumps(kas.ukryj(v), ensure_ascii=False)
    assert not any(x in tekst for x in SLADY)
    tekst = json.dumps(kas.ukryj(v, portfel=False), ensure_ascii=False)
    assert '"kasyno"' not in tekst and '"wlasciciel"' in tekst
    assert "kasyno" not in widok(_gra(lokale=False), "A") and "wlasciciel" not in widok(_gra(lokale=False), "A")


@pytest.mark.django_db
def test_mistrz_gry_nie_widzi_klubu(client, uczen, zawsze_zaproszenie, settings):
    firmy = [{"nazwa": DRUZYNA, "bot": None}, {"nazwa": "Bot tani", "bot": "tani"}]
    gra = client.post("/api/gry", {"nazwa": "Klasa", "ziarno": "7", "liczba_rund": 4, "firmy": firmy},
                      content_type=JSON).json()["id"]
    ala = uczen("ala")
    assert client.post(f"/api/gry/{gra}/druzyny/{DRUZYNA}", {"dodaj": "ala"}, content_type=JSON).status_code == 200
    v = ala.get(f"/api/gry/{gra}/widok/{DRUZYNA}").json()
    r = ala.put(f"/api/gry/{gra}/decyzje/{DRUZYNA}?wersja=0", {**v["decyzje"], "wyplata_wlasna": 500}, content_type=JSON)
    assert r.status_code == 200
    ala.post(f"/api/gry/{gra}/wyslij/{DRUZYNA}", {}, content_type=JSON)
    v = ala.get(f"/api/gry/{gra}/widok/{DRUZYNA}").json()
    assert v["gra"]["runda"] == 2 and v["kasyno"]["otwarte"] and v["wlasciciel"]["portfel_przed"] > 0
    automat = next(k for k, x in v["kasyno"]["gry"].items() if x["typ"] == "automat")
    d = {**v["decyzje"], "kasyno": [{"gra": automat, "stawka": 100}]}
    r = ala.put(f"/api/gry/{gra}/decyzje/{DRUZYNA}?wersja={v['druzyna']['autorzy']['wersja']}", d, content_type=JSON)
    assert r.status_code == 200 and r.json()["kasyno"]["decyzja"]["ukryte"]
    ala.post(f"/api/gry/{gra}/wyslij/{DRUZYNA}", {}, content_type=JSON)
    v = ala.get(f"/api/gry/{gra}/widok/{DRUZYNA}").json()
    assert v["wyniki"]["kasyno"]["gry"]["zaklady"] and v["decyzje"].get("kasyno") is None
    poprzednia = ala.get(f"/api/gry/{gra}/widok/{DRUZYNA}?runda=2").json()
    # szkic rundy 3 z zakładem (drugie zaproszenie) – podgląd mistrza gry liczy go, ale nie pokazuje
    assert v["kasyno"]["otwarte"]
    r = ala.put(f"/api/gry/{gra}/decyzje/{DRUZYNA}?wersja={v['druzyna']['autorzy']['wersja']}",
                {**v["decyzje"], "kasyno": [{"gra": automat, "stawka": 100}]}, content_type=JSON)
    assert r.status_code == 200
    # mistrz gry: ani śladu klubu ani portfela (wpłaty i wypłaty widać tylko jako operacje na koncie)
    odpowiedzi = [client.get(f"/api/gry/{gra}/mg"), client.get(f"/api/gry/{gra}/widok/{DRUZYNA}"),
                  client.get(f"/api/gry/{gra}/widok/{DRUZYNA}?runda=2"), client.post(f"/api/gry/{gra}/podglad/{DRUZYNA}", {}, content_type=JSON),
                  client.get(f"/api/gry/{gra}/eksport"), client.get(f"/api/gry/{gra}/wyniki.csv"),
                  client.get(f"/api/gry/{gra}/ranking.csv")]
    for r in odpowiedzi:
        assert r.status_code == 200
        tekst = r.content.decode("utf-8")
        assert not any(x in tekst for x in SLADY), (r.request["PATH_INFO"], [x for x in SLADY if x in tekst])
    assert "kasyno" in json.dumps(poprzednia["decyzje"]) or poprzednia.get("kasyno")
    # klub wyłączony na serwerze: uczeń nie widzi klubu, portfel zostaje
    settings.LEVAS_KASYNO = False
    v = ala.get(f"/api/gry/{gra}/widok/{DRUZYNA}?runda=2").json()
    assert "kasyno" not in v and "wlasciciel" in v and "kasyno" not in v["decyzje"]
