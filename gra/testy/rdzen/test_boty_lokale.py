"""B6: boty korzystają z każdej opcji lokalu – kupno na kredyt pod zastaw, lokal niewyposażony, działka, przebicie
w licytacji – z leasingu sprzętu i z kupna budynku z najemcą (parametry strategii `lokal`, `leasing`, `wykup`,
`przejecie`; pomiar w balans/warianty.py)."""
import copy

import pytest

from silnik import boty
from silnik.gra import Gra
from silnik.pieniadze import banki as bk

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
    k, *doplata = d["kredyty_wez"]   # dopłata bez historii, gdy po kredycie pod zastaw zabrakłoby rezerwy
    assert k["zastaw"].endswith(lok["id"]) and k["kwota"] > 0   # zastaw: id majątku „lokal:…”
    assert len(doplata) <= 1 and not any(x.get("zastaw") for x in doplata)
    f = g.stan().firmy["A"]
    assert [(x.id, x.forma) for x in f.lokale] == [(lok["id"], "kupno")] and len(f.kredyty) == 1 + len(doplata)


def test_bot_kupuje_dzialke_z_budowa_i_doplaca_kredytem_bez_historii():
    """Działka: wejście z budową w ratach ponad kredyt pod zastaw (0,7 × cena z budową) – brakującą kwotę i rezerwę
    bot dopłaca kredytem bez wymogu historii (np. „na start”); bez niej bank przejmował działkę po zaległych ratach."""
    g, (d,) = _gra({"lokal": {"typy": ["dzialka"], "forma": "kupno", "rezerwa": 10000}})
    lok = _lokal(g, d["lokal"]["id"])
    assert lok["typ"] == "dzialka" and d["lokal"]["forma"] == "kupno"
    zastaw, doplata = d["kredyty_wez"]
    assert zastaw["zastaw"] == f"lokal:{lok['id']}" and "zastaw" not in doplata
    assert 40000 + zastaw["kwota"] + doplata["kwota"] >= lok["cena"] + lok["koszt_budowy"] + 10000
    f = g.stan().firmy["A"]
    assert [(x.id, x.forma) for x in f.lokale] == [(lok["id"], "kupno")] and len(f.kredyty) == 2


def test_bot_finansuje_sprzet_lokalu_niewyposazonego_leasingiem():
    """Lokal bez zestawu: cały sprzęt 3★ naraz (od tygodnia 2) to więcej, niż bot ma gotówki – najdroższe pozycje
    bierze w leasing (nie liczy się do wskaźnika zadłużenia karty), aż po zakupach i opłatach wstępnych zostanie
    rezerwa (ustawienia.rezerwa_po_sprzecie); bez tego wpadał w debet ponad limit konta."""
    g, (d1, d2) = _gra({"lokal": {"typy": ["niewyposazony"]}, "jakosc": 3}, rund=2)
    assert _lokal(g, d1["lokal"]["id"])["typ"] == "niewyposazony" and not d1.get("kredyty_wez")
    przed = g.stan(1).firmy["A"].gotowka
    cena = lambda x: g.dane.sprzet[x["nazwa"]]["ceny"][str(x["jakosc"])]   # noqa: E731
    lea, kup = d2["leasing_wez"], d2["sprzet_kup"]
    assert lea and sum(map(cena, lea + kup)) > przed and not d2.get("kredyty_wez")
    assert min(map(cena, lea)) >= max(map(cena, kup), default=0)   # w leasing najdroższe
    wplata = bk.banki(g.dane)[lea[0]["bank"]]["leasing"]["wplata"]
    zostaje = przed - sum(map(cena, kup)) - wplata * sum(map(cena, lea))
    assert zostaje >= g.dane.boty["ustawienia"]["rezerwa_po_sprzecie"]
    f = g.stan(2).firmy["A"]
    assert len(f.leasingi) == len(lea) and not f.kredyty and f.gotowka > 0


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
