"""Licytacje lokali, przejęcia budynków z najemcą i wypowiedzenia najmu (F3b.4, silnik/przejecia.py)."""

import pytest
from test_lokale import _gra, _lokal, _rachunek, _runda
from test_rynek_pracy import _kandydat, _z

from api.prezentacja import widok
from silnik import przejecia as pr


def _do_rundy(g, runda, **decyzje):
    """Rundy bez decyzji aż do `runda` (wyłącznie); decyzje – w pierwszej z nich."""
    s = None
    while g.runda < runda:
        s = _runda(g, **decyzje)
        decyzje = {}
    return s


def _bledy(s, r, firma):
    return [b for b in s.wyniki[r][firma]["lista_bledow"] if b["zakladka"] == pr.ZAKLADKA]


def _kpir(s, r, firma, poczatek):
    return [p for p in s.wyniki[r][firma]["kpir"]["pozycje"] if p["opis"].startswith(poczatek)]


def test_licytacja_od_pierwszej_rundy_przegrany_dostaje_wyjasnienie():
    g = _gra()
    assert g.dane.mapa["zasady"]["licytacje_od_rundy"] == 1   # test gry 28.10: dwie drużyny chcą ten sam lokal
    s = _runda(g, A={"lokal": {"id": "centrum_3", "forma": "najem", "oferta": 9000}},
               B={"lokal": {"id": "centrum_3", "forma": "najem", "oferta": 5000}})
    (p,) = s.rynek[1]["przejecia"]["przetargi"]
    assert p["zwyciezca"] == "A" and not p["remis"] and [o["kwota"] for o in p["oferty"]] == [9000, 5000]
    assert s.firmy["A"].lokale[0].czynsz == 9000
    powod = s.wyniki[1]["B"]["lokal_decyzja"]["powod"]
    assert "9 000,00 zł wobec Twojej 5 000,00 zł" in powod and "wyższy czynsz" in powod


def test_od_rundy_licytacji_wygrywa_wyzsza_oferta_i_placi_swoja_kwote():
    g = _gra()
    od = g.dane.mapa["zasady"]["licytacje_od_rundy"]
    _do_rundy(g, od)
    s = _runda(g, A={"lokal": {"id": "centrum_3", "forma": "najem", "oferta": 6000}}, B=_lokal("centrum_3"))
    (p,) = s.rynek[od]["przejecia"]["przetargi"]
    assert p["zwyciezca"] == "A" and not p["remis"] and p["oferty"][0]["stosunek"] == 1.2
    lok = s.firmy["A"].lokale[0]
    assert lok.czynsz == 6000 and _rachunek(s, od, "A", "Kaucja za lokal") == [-2 * 6000]
    dec = s.wyniki[od]["B"]["lokal_decyzja"]
    assert not dec["przyjety"] and "oferta była wyższa" in dec["powod"] and s.firmy["B"].lokale == []
    assert s.wyniki[od]["B"]["przejecia"]["licytacje"] == [p]


def test_oferta_ponizej_wywolawczej_albo_ponad_limit_odrzucona():
    g = _gra()
    od = g.dane.mapa["zasady"]["licytacje_od_rundy"]
    _do_rundy(g, od)
    s = _runda(g, A={"lokal": {"id": "centrum_3", "forma": "najem", "oferta": 4000}},
               B={"lokal": {"id": "dworzec_1", "forma": "najem", "oferta": 2600 * 3 + 1}})
    assert not s.wyniki[od]["A"]["lokal_decyzja"]["przyjety"] and not s.wyniki[od]["B"]["lokal_decyzja"]["przyjety"]
    assert s.firmy["A"].lokale == [] == s.firmy["B"].lokale


def _przejecie(lokal="politechnika_1", kupujacy="B", oferta=None):
    """A wynajmuje lokal w rundzie 1 i stawia w nim stanowisko w rundzie 2, `kupujacy` kupuje budynek w rundzie przejęć."""
    g = _gra(rund=14, kapital_startowy=300000)
    od = g.dane.mapa["zasady"]["przejecia_od_rundy"]
    _runda(g, A=_lokal(lokal))
    _do_rundy(g, od, A={"stanowiska": {"kuchnia": 1}})
    cena = g.dane.lokale[lokal]["cena"]
    s = _runda(g, **{kupujacy: {"przejecie": {"id": lokal, "oferta": oferta or cena}}})
    return g, s, od


def test_przejecie_budynku_najemca_placi_czynsz_nowemu_wlascicielowi():
    g, s, od = _przejecie()
    lok = g.dane.lokale["politechnika_1"]
    info = s.wyniki[od]["B"]["przejecia"]
    assert info["przejecie"]["przyjety"] and not info["przejecie"]["wykup"]
    assert _rachunek(s, od, "B", "Zakup budynku z najemcą") == [-lok["cena"]]
    assert [b.id for b in s.firmy["B"].budynki] == ["politechnika_1"] and s.firmy["A"].lokale[0].wlasciciel == "B"
    (czynsz,) = _kpir(s, od, "B", "Czynsz najmu od najemcy")
    assert czynsz["przychod_pozostaly"] > 0
    assert any(b["poziom"] == "niebieski" for b in _bledy(s, od, "A"))
    assert info["budynki"][0]["najemca"] == "A" and s.wyniki[od]["A"]["przejecia"]["najmy"][0]["wlasciciel"] == "B"
    assert s.rynek[od]["przejecia"]["wlasciciele"] == {"politechnika_1": "B"}


def test_przejecie_przed_runda_i_lokal_bez_ceny_odrzucone():
    g = _gra(kapital_startowy=300000)
    s = _runda(g, A=_lokal("politechnika_1"), B={"przejecie": {"id": "politechnika_1"}})
    assert not s.wyniki[1]["B"]["przejecia"]["przejecie"]["przyjety"]
    _do_rundy(g, g.dane.mapa["zasady"]["przejecia_od_rundy"], A=_lokal("centrum_3"))
    s = _runda(g, B={"przejecie": {"id": "centrum_3"}})
    r = g.runda - 1
    assert "nie chce sprzedać" in s.wyniki[r]["B"]["przejecia"]["przejecie"]["powod"]
    assert any(b["poziom"] == "czerwony" for b in _bledy(s, r, "B"))


def test_wykup_wlasnego_lokalu_zamienia_najem_we_wlasnosc():
    g, s, od = _przejecie(kupujacy="A")
    lok = s.firmy["A"].lokale[0]
    assert s.wyniki[od]["A"]["przejecia"]["przejecie"]["wykup"]
    assert (lok.forma, lok.czynsz, lok.kaucja) == ("kupno", 0, 0)
    assert _rachunek(s, od, "A", "Zwrot kaucji") == [2 * g.dane.lokale["politechnika_1"]["czynsz"]]
    assert all(not st.sprzet_wynajmujacego for st in s.firmy["A"].stanowiska)


def test_licytacja_budynku_wygrywa_wyzsza_oferta():
    g = _gra(("A", None), ("B", None), ("C", None), rund=10, kapital_startowy=300000)
    od = g.dane.mapa["zasady"]["przejecia_od_rundy"]
    _do_rundy(g, od, A=_lokal("politechnika_1"))
    s = _runda(g, B={"przejecie": {"id": "politechnika_1", "oferta": 130000}}, C={"przejecie": {"id": "politechnika_1"}})
    (p,) = s.rynek[od]["przejecia"]["przetargi"]
    assert p["rodzaj"] == "przejecie" and p["zwyciezca"] == "B" and s.firmy["C"].budynki == []
    assert "oferta była wyższa" in s.wyniki[od]["C"]["przejecia"]["przejecie"]["powod"]


@pytest.mark.parametrize("ulepszenia", ["zatrzymaj", "przywroc"])
def test_wypowiedzenie_wyprowadzka_i_rozliczenie_ulepszen(ulepszenia):
    g, s, od = _przejecie("politechnika_2")   # lokal do urządzenia: adaptacja i stanowisko to nakłady najemcy
    naklady = s.firmy["A"].lokale[0].naklady
    assert naklady >= g.dane.lokale["politechnika_2"]["adaptacja"] and s.firmy["A"].stanowiska
    k = _kandydat(s, 1)
    s = _runda(g, A={"zatrudnij": [_z(k, next(st.nr for st in s.firmy["A"].stanowiska if not st.sprzet_wynajmujacego))]}, B={"wypowiedz": [{"id": "politechnika_2", "ulepszenia": ulepszenia}]})
    r = od + 1
    w = s.wyniki[r]["B"]["przejecia"]["wypowiedzenia"][0]
    koniec = r + g.dane.mapa["zasady"]["wypowiedzenie_rund"] - 1
    assert w["przyjete"] and w["najem_do"] == koniec and s.firmy["A"].lokale[0].najem_do == koniec
    assert any(b["poziom"] == "czerwony" and str(koniec) in b["tekst"] for b in _bledy(s, r, "A"))
    s = _runda(g, B={"wypowiedz": [{"id": "politechnika_2"}]})
    assert "już wypowiedziany" in s.wyniki[r + 1]["B"]["przejecia"]["wypowiedzenia"][0]["powod"]
    s = _do_rundy(g, koniec + 2)
    assert s.firmy["A"].lokale == [] and s.firmy["A"].stanowiska == [] and s.firmy["A"].pracownicy == {}
    (x,) = s.wyniki[koniec + 1]["A"]["przejecia"]["wyprowadzki"]
    assert x["zwolnieni"] == [k["imie_nazwisko"]] and any(c["id"] == k["id"] for c in s.kandydaci)
    assert _kpir(s, koniec + 1, "A", f"Koszt zwolnienia {k['imie_nazwisko']}")
    assert _rachunek(s, koniec + 1, "A", "Zwrot kaucji") == [2 * g.dane.lokale["politechnika_2"]["czynsz"]]
    (lok,) = s.firmy["B"].lokale
    assert (lok.id, lok.forma, lok.dziala_od) == ("politechnika_2", "kupno", koniec + 1) and s.firmy["B"].budynki == []
    zasady = g.dane.mapa["zasady"]
    if ulepszenia == "zatrzymaj":
        assert x["rozliczenie"] == pytest.approx(naklady * zasady["ulepszenia_zwrot"], abs=0.01)
        assert _rachunek(s, koniec + 1, "B", "Rozliczenie ulepszeń") == [pytest.approx(-x["rozliczenie"], abs=0.01)]
        assert [st.lokal for st in s.firmy["B"].stanowiska] == ["politechnika_2"]
    else:
        assert x["rozliczenie"] == pytest.approx(-naklady * zasady["przywrocenie_koszt"], abs=0.01)
        assert _kpir(s, koniec + 1, "A", "Przywrócenie lokalu") and s.firmy["B"].stanowiska == []


def test_widok_zakladki_przejecia():
    g, s, od = _przejecie()
    v = widok(g, "B")
    P = v["przejecia"]
    assert P["od_rundy"] == g.dane.mapa["zasady"]["przejecia_od_rundy"] and P["budynki"][0]["id"] == "politechnika_1"
    assert P["wyniki"]["przejecie"]["przyjety"]
    g.ustaw_decyzje("B", {"wypowiedz": [{"id": "politechnika_1"}]})
    assert widok(g, "B")["przejecia"]["decyzja"]["wypowiedzenia"][0]["przyjete"]
    assert g.stan(g.runda - 1).firmy["A"].lokale[0].najem_do is None   # podgląd nie zmienia stanu gry
    va = widok(g, "A")
    assert va["przejecia"]["najmy"][0]["wlasciciel"] == "B" and va["przejecia"]["do_kupienia"] == []


def test_bot_po_wypowiedzeniu_szuka_nowego_lokalu(monkeypatch):
    from silnik import boty
    monkeypatch.setattr(boty, "_wybierz_lokal", lambda dane, stan, nazwa, *a:
                        _lokal("felin_1" if stan.firmy[nazwa].lokale else "politechnika_1")["lokal"])
    g = _gra(("H", None), ("Bot", "zrownowazony"), rund=12, kapital_startowy=300000)
    od = g.dane.mapa["zasady"]["przejecia_od_rundy"]
    _do_rundy(g, od)
    _runda(g, H={"przejecie": {"id": "politechnika_1"}})
    s = _runda(g, H={"wypowiedz": [{"id": "politechnika_1"}]})
    koniec = s.firmy["Bot"].lokale[0].najem_do
    s = _do_rundy(g, koniec + 2)
    assert [x.id for x in s.firmy["Bot"].lokale] == ["felin_1"] and [x.id for x in s.firmy["H"].lokale] == ["politechnika_1"]
    assert s.firmy["Bot"].pracownicy and all(st.lokal == "felin_1" for st in s.firmy["Bot"].stanowiska)
