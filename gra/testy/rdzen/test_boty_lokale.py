"""B6: boty korzystają z każdej opcji lokalu – kupno na kredyt pod zastaw, lokal niewyposażony, działka, przebicie
w licytacji – i z leasingu sprzętu (parametry strategii `lokal` i `leasing`, pomiar w balans/warianty.py)."""
import copy

import pytest

from silnik import boty
from silnik.gra import Gra

pytestmark = pytest.mark.dane_gry


def _gra(strategia: dict, rund: int = 1) -> tuple[Gra, list[dict]]:
    """Gra dwóch firm; firma A (zrównoważony) z nadpisaną strategią – decyzje z `rund` rund."""
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5)
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
