"""B6: boty korzystają z każdej opcji lokalu – kupno na kredyt pod zastaw, lokal niewyposażony, działka, przebicie
w licytacji – z leasingu sprzętu i z kupna budynku z najemcą (parametry strategii `lokal`, `leasing`, `wykup`,
`przejecie`; pomiar w balans/warianty.py)."""
import copy

import pytest

from silnik import boty
from silnik.gra import Gra

pytestmark = pytest.mark.dane_gry


def _gra(strategia: dict, rund: int = 1, **opcje) -> tuple[Gra, list[dict]]:
    """Gra dwóch firm; firma A (zrównoważony) z nadpisaną strategią – decyzje z `rund` rund."""
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5, **opcje)
    dane = copy.copy(g.dane)
    st = dane.boty["strategie"]
    dane.boty = {**dane.boty, "strategie": {**st, "zrownowazony": {**st["zrownowazony"], **strategia}}}
    decyzje = []
    for r in range(1, rund + 1):
        d = boty.decyzje_bota(dane, g.stan(r - 1), "A", "zrownowazony", r, g.konfiguracja)
        decyzje.append(d)
        g.ustaw_decyzje("A", d)
        g.przelicz(wymus=True)
    return g, decyzje


def _lokal(g: Gra, id_: str) -> dict:
    return next(x for x in g.dane.mapa["lokale"] if x["id"] == id_)


def test_bot_kupuje_lokal_na_kredyt_pod_jego_zastaw():
    g, (d,) = _gra({"lokal": {"forma": "kupno", "rezerwa": 10000}})
    lok = _lokal(g, d["lokal"]["id"])
    assert d["lokal"]["forma"] == "kupno" and lok["typ"] == "gotowy" and lok.get("cena")
    (k,) = d["kredyty_wez"]
    assert k["zastaw"].endswith(lok["id"]) and k["kwota"] > 0   # zastaw: id majątku „lokal:…”
    f = g.stan().firmy["A"]
    assert [(x.id, x.forma) for x in f.lokale] == [(lok["id"], "kupno")] and f.kredyty


def test_bot_bez_srodkow_na_kupno_bierze_gotowy_lokal_w_najmie():
    _, (d,) = _gra({"lokal": {"forma": "kupno", "rezerwa": 10 ** 6}})
    assert d["lokal"]["forma"] == "najem" and not d.get("kredyty_wez")


def test_bot_bierze_lokal_wybranego_typu_i_przebija_cene():
    g, (d,) = _gra({"lokal": {"typy": ["niewyposazony"], "przebicie": 1.2}})
    lok = _lokal(g, d["lokal"]["id"])
    assert lok["typ"] == "niewyposazony" and d["lokal"]["oferta"] == pytest.approx(lok["czynsz"] * 1.2)


def test_bot_z_mala_gotowka_bierze_sprzet_w_leasingu():
    g, dec = _gra({"lokal": {"typy": ["niewyposazony"]}, "leasing": {"gotowka": 10 ** 6, "rund": 26}}, rund=2)
    d = dec[1]   # sprzęt odblokowany w rundzie 2, lokal niewyposażony – wszystko do kupienia
    assert d["leasing_wez"] and not d["sprzet_kup"]
    assert all(x["rund"] == 26 for x in d["leasing_wez"])
    assert len(g.stan().firmy["A"].leasingi) == len(d["leasing_wez"])


def test_bot_z_dwoma_lokalami_zamawia_z_zapasow_kazdego_lokalu(monkeypatch):
    """Magazyn każdego lokalu jest osobny (Z2), więc zamówienie bot liczy osobno z zapasów lokalu (B6: wcześniej z
    zapasów całej firmy – nadmiar jednego lokalu „pokrywał” braki drugiego; drugi lokal tracił sprzedaż)."""
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5, poziomy={"A": "trudny", "B": "sredni"},
                 kapital_startowy=200000)
    for _ in range(6):
        g.przelicz(wymus=True)
    f = g.stan(6).firmy["A"]
    assert len(f.lokale) == 2
    wywolania, oryginal = [], boty.zamowienie_zasobow
    monkeypatch.setattr(boty, "zamowienie_zasobow", lambda dane, firma, *a: (
        wywolania.append((tuple(x.id for x in firma.lokale), dict(firma.magazyn))) or oryginal(dane, firma, *a)))
    d = boty.decyzje_bota(g.dane, g.stan(6), "A", "zrownowazony", 7, g.konfiguracja)
    assert sorted(lok for lok, _ in wywolania) == sorted((x.id,) for x in f.lokale)
    for (lok,), mag in wywolania:   # zapasy z widoku lokalu, nie całej firmy
        assert mag == boty.pl.widok(f, lok).magazyn
    assert {z["lokal"] for z in d["zamowienia"]} == {x.id for x in f.lokale}


def test_bot_wykupuje_wynajmowany_lokal_gdy_go_stac():
    g, dec = _gra({"strefy": ["felin"], "wykup": {"rezerwa": 0}}, rund=4, kapital_startowy=300000)
    lok = dec[0]["lokal"]["id"]
    assert dec[0]["lokal"]["forma"] == "najem" and _lokal(g, lok).get("cena")
    assert not any(d.get("przejecie") for d in dec[:3])   # przejęcia od rundy 4
    assert dec[3]["przejecie"] == {"id": lok}
    assert [(x.id, x.forma) for x in g.stan().firmy["A"].lokale] == [(lok, "kupno")]


def test_bot_kupuje_budynek_rywala_i_wypowiada_mu_najem():
    g, dec = _gra({"przejecie": {"rezerwa": 0, "wypowiedz": True}}, rund=5, kapital_startowy=300000)
    lok = dec[3]["przejecie"]["id"]
    assert lok in {x.id for x in g.stan(3).firmy["B"].lokale}
    assert dec[4]["wypowiedz"] == [{"id": lok, "ulepszenia": "zatrzymaj"}]
    umowa = next(x for x in g.stan().firmy["B"].lokale if x.id == lok)
    assert umowa.wlasciciel == "A" and umowa.najem_do is not None
