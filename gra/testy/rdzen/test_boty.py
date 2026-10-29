"""Poziomy botów (F4.4, P19, Z5): łatwy, średni, trudny i niemożliwy różnią się sposobem planowania (niemożliwy –
oszukuje); wersje „jak człowiek” prognozują z raportów poprzednich rund."""
import pytest

from balans.symuluj import rozegraj
from silnik import boty
from silnik.dane import dane_domyslne
from silnik.gra import Gra

pytestmark = pytest.mark.dane_gry

RUND = 12   # trudny bot otwiera drugi lokal dopiero z zapasem gotówki


@pytest.fixture(scope="module")
def poziomy() -> dict[str, dict[str, dict]]:
    return {p: rozegraj(RUND, p, 7) for p in ("latwy", "sredni", "trudny")}


def _srednia(w: dict[str, dict], co: str) -> float:
    return sum(x[co] for x in w.values()) / len(w)


def test_wyzszy_poziom_zarabia_srednio_wiecej(poziomy):
    assert _srednia(poziomy["latwy"], "gotowka") < _srednia(poziomy["sredni"], "gotowka")
    assert _srednia(poziomy["sredni"], "gotowka") < _srednia(poziomy["trudny"], "gotowka")


def test_planujacy_bot_marnuje_mniej_towaru(poziomy):
    # łatwy zamawia na cały przewidywany popyt – towar psuje się, gdy kuchnia nie nadąża
    assert _srednia(poziomy["sredni"], "przeterminowane") < _srednia(poziomy["latwy"], "przeterminowane") / 2
    assert _srednia(poziomy["trudny"], "przeterminowane") < _srednia(poziomy["latwy"], "przeterminowane") / 2


def test_trudny_bot_otwiera_kolejny_lokal(poziomy):
    zasady = dane_domyslne().boty["poziomy"]["trudny"]["kolejny_lokal"]
    assert any(x["lokale"] > 1 for x in poziomy["trudny"].values())
    assert all(x["lokale"] <= zasady["maks_lokali"] for x in poziomy["trudny"].values())
    assert all(x["lokale"] == 1 for p in ("latwy", "sredni") for x in poziomy[p].values())


def test_poziom_z_konfiguracji_gry():
    dane = dane_domyslne()
    konf = {"firmy": [{"nazwa": "A", "bot": "tani", "poziom": "trudny"}, {"nazwa": "B", "bot": "tani"}]}
    assert boty.poziom(dane, konf, "A") is dane.boty["poziomy"]["trudny"]
    assert boty.poziom(dane, konf, "B") is dane.boty["poziomy"][boty.DOMYSLNY_POZIOM]


def test_latwy_bot_nie_reklamuje_sie_i_nie_daje_promocji():
    g = Gra.nowa("t", [("A", "agresywny"), ("B", "premium")], 6, 3, poziomy={"A": "latwy", "B": "latwy"})
    for _ in range(6):
        g.przelicz(wymus=True)
    for r in range(1, 7):
        for n in ("A", "B"):
            assert not g.decyzje[r].get(n, {}).get("kampanie")
            assert not g.decyzje[r].get(n, {}).get("promocje")


def test_niemozliwy_bot_oszukuje_popytem():
    """Poziom niemożliwy (P19): przy tej samej strategii klienci wolą jego lokale; drużyn graczy to nie dotyczy."""
    dane = dane_domyslne()
    konf = {"firmy": [{"nazwa": "A", "bot": "tani", "poziom": "niemozliwy"}, {"nazwa": "B", "bot": "tani", "poziom": "trudny"},
                      {"nazwa": "C", "bot": None, "poziom": "niemozliwy"}]}
    assert boty.przewaga_popytu(dane, konf, "A") == dane.boty["poziomy"]["niemozliwy"]["przewaga_popytu"] > 1
    assert boty.przewaga_popytu(dane, konf, "B") == boty.przewaga_popytu(dane, konf, "C") == 1
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "zrownowazony")], 6, 5, poziomy={"A": "niemozliwy", "B": "trudny"})
    for _ in range(6):
        s = g.przelicz(wymus=True)
    sprzedaz = {n: sum(v["sprzedaz"] for r in range(2, 7) for v in s.wyniki[r][n]["sprzedaz"].values()) for n in "AB"}
    assert sprzedaz["A"] > sprzedaz["B"]


def test_bot_jak_czlowiek_prognozuje_z_raportow_a_nie_z_modelu(monkeypatch):
    """Z5: wersje „jak człowiek” nie używają prognozy modelu popytu (pp.prognoza dla własnych cen i jakości),
    tylko popytu z raportów poprzednich rund; wersja dobra – średnia z dwóch rund razy zmiana puli strefy."""
    def model(*a, **k):
        raise AssertionError("bot „jak człowiek” użył prognozy modelu")

    monkeypatch.setattr(boty, "_prognoza_lokali", model)
    wersje = {"A": "czlowiek_slaby", "B": "czlowiek_sredni", "C": "czlowiek_dobry"}
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani"), ("C", "premium")], 5, 3, poziomy=wersje)
    for _ in range(4):
        s = g.przelicz(wymus=True)
    assert all(sum(v["sprzedaz"] for v in s.wyniki[4][n]["sprzedaz"].values()) > 0 for n in wersje)
    dane, f = g.dane, s.firmy["C"]
    oferta, lok = list(f.oferta), f.lokale[0].id
    konk = boty.pp.oferty_konkurencji(dane, s, 5, "C")
    popyt = {r: next(x for x in s.wyniki[r]["C"]["klienci"]["lokale"] if x["id"] == lok)["dania"] for r in (3, 4)}
    zeszly = boty._prognoza_czlowieka(dane, s, f, "C", oferta, 5, 5, konk, {"rund": 1})
    assert zeszly["lokale"][lok] == {u: popyt[4][u] for u in oferta}
    assert sum(zeszly["dni"]) == pytest.approx(sum(zeszly["dania"].values()), abs=0.5)
    strefa = dane.lokale[lok]["strefa"]

    def pula(r):
        return sum(float(x.sum()) for u, x in boty.pp.pule(dane, r)[strefa].items() if u in oferta)

    dobry = boty._prognoza_czlowieka(dane, s, f, "C", oferta, 5, 5, konk, {"rund": 2, "pule": True})
    for u in oferta:
        oczekiwana = (popyt[4][u] * pula(5) / pula(4) + popyt[3][u] * pula(5) / pula(3)) / 2
        assert dobry["lokale"][lok][u] == pytest.approx(oczekiwana, abs=0.06)


def test_bot_jak_czlowiek_bez_historii_bierze_potencjal_lokalu():
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 4, 3, poziomy={"A": "czlowiek_sredni"})
    s = g.przelicz(wymus=True)
    dane, f = g.dane, s.firmy["A"]
    oferta, lok = list(f.oferta), f.lokale[0].id
    prog = boty._prognoza_czlowieka(dane, s, f, "A", oferta, 2, 2, boty.pp.oferty_konkurencji(dane, s, 2, "A"),
                                    {"rund": 1})
    assert not s.wyniki[1]["A"]["sprzedaz"] and all(prog["lokale"][lok][u] > 0 for u in oferta)


def test_poziomy_jak_czlowiek_tylko_do_pomiarow():
    from silnik.schematy import PoziomBota
    poziomy = dane_domyslne().boty["poziomy"]
    wersje = [k for k, p in poziomy.items() if p.get("prognoza_czlowieka")]
    assert len(wersje) == 3 and all(poziomy[k].get("tylko_pomiar") for k in wersje)
    with pytest.raises(ValueError, match="prognoza_czlowieka"):
        PoziomBota(nazwa="x", opis="x", prognoza_czlowieka={"rund": 1}, mnozniki_ceny=[1.1])
