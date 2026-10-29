"""Uzgodnienie kasy (F3a.12): w każdej rundzie każdej firmy gotówka zgadza się co do grosza z KPiR ± VAT ± operacjami
poza KPiR (silnik/ksiegowosc/uzgodnienie.py). Losowe gry botów (hypothesis) – w grze z lokalami i bez; drużyna „H” gra jak bot,
ale dokłada losowe decyzje finansowe: kredyty, lokaty, Harpagon, kupno lokalu i działki, sprzedaż sprzętu, zwroty,
a w grze z lokalami – biuro z mapy albo samodzielną księgowość z (czasem błędnymi) deklaracjami (silnik/ksiegowosc/biuro.py)."""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pomocnicze import DANE_GRY

from silnik.boty import decyzje_bota
from silnik.dane import Dane
from silnik.gra import Gra
from silnik.pieniadze import banki as bk

pytestmark = pytest.mark.dane_gry

D = Dane(DANE_GRY)
STRATEGIE = sorted(D.boty["strategie"])
LOKALE = sorted(D.lokale)
BANKI = bk.banki(D)


@st.composite
def _dodatki(draw, lokale: bool) -> dict:
    """Losowe decyzje finansowe na rundę (część z nich silnik odrzuci – to też ma się uzgadniać)."""
    d = {}
    if draw(st.booleans()):
        d["kredyty_wez"] = [{"bank": "Crédit Agricole", "produkt": "start", "kwota": draw(st.integers(1000, 30000)),
                             "rund": 26} if lokale else {"kwota": draw(st.integers(1000, 30000)), "miesiecy": 6}]
    if draw(st.booleans()):
        bank = draw(st.sampled_from(sorted(BANKI)))
        d["lokaty_zaloz"] = [{"bank": bank, "kwota": draw(st.integers(500, 20000)),
                              "rund": draw(st.sampled_from(sorted(BANKI[bank]["lokaty"])))} if lokale
                             else {"kwota": draw(st.integers(500, 20000)), "miesiecy": 3}]
    if draw(st.booleans()):
        d["zwrot_nadmiaru"] = True     # zamieniane na dostawców z zamówień bota
    if draw(st.booleans()):
        d["sprzet_sprzedaj"] = [{"typ": "kuchnia", "nr": 1, "nazwa": "Rożen"}]
    if lokale:
        if draw(st.booleans()):
            d["harpagon_wez" if draw(st.booleans()) else "harpagon_splac"] = draw(st.integers(500, 20000))
        d["biuro"] = draw(st.sampled_from(["samodzielnie", "samodzielnie", "jks", "eksiegi", "halinka"]))
        d["_deklaracja"] = draw(st.sampled_from(["brak", "dobra", "zla"]))
        if draw(st.integers(0, 3)) == 0:
            d["lokal"] = {"id": draw(st.sampled_from(LOKALE)), "forma": draw(st.sampled_from(["najem", "kupno"]))}
    return d


def _graj(lokale: bool, ziarno: int, strategie: list[str], dodatki: list[dict]):
    rund = len(dodatki)
    g = Gra.nowa("lokale", [("H", strategie[0]), ("B1", strategie[1]), ("B2", strategie[2])], rund, ziarno,
                 lokale=lokale, kapital_startowy=100000)
    for r, extra in enumerate(dodatki, start=1):
        d = decyzje_bota(g.dane, g.stan(), "H", strategie[0], r, g.konfiguracja)
        if extra.pop("zwrot_nadmiaru", False):
            extra["zwrot_nadmiaru"] = {z["dostawca"]: True for z in d.get("zamowienia", []) if "dostawca" in z}
        dk, tryb = g.stan().firmy["H"].deklaracja, extra.pop("_deklaracja", "brak")
        if dk and tryb != "brak":
            zle = tryb == "zla"
            extra["ksiegowosc"] = {"zapisy": {x["id"]: {"kolumna": "towary" if zle else x["poprawne"]["kolumna"],
                                                        "stawka": x["poprawne"]["stawka"]} for x in dk["dokumenty"]},
                                   "deklaracja": {k: v * (1.5 if zle else 1) for k, v in dk["poprawne"].items()}}
        g.ustaw_decyzje("H", {**d, **extra})
        g.przelicz(wymus=True)
        _dokumenty_pokrywaja_rachunek(g.stan(), r)
    return g.stan()


def _dokumenty_pokrywaja_rachunek(s, r):
    """Samodzielna księgowość: każda operacja rachunku jest w dokumentach rundy (kwota ze znakiem)."""
    dk = s.firmy["H"].deklaracja
    if dk:
        z_dokumentow = sum(x["brutto"] * (1 if x["kierunek"] == "wplyw" else -1)
                           for x in dk["dokumenty"] if x["kierunek"] != "brak")
        assert round(z_dokumentow, 2) == round(sum(o["kwota"] for o in s.wyniki[r]["H"]["rachunek"]), 2)


def _sprawdz(s):
    for r, firmy in s.wyniki.items():
        for f, w in firmy.items():
            u = w["uzgodnienie"]
            assert (u["roznica"], u["roznica_kpir"], u["roznica_rachunku"]) == (0, 0, 0), (r, f, u)
            assert u["koniec"] == w["gotowka"]
            assert all(o["rodzaj"] for o in w["rachunek"])


@settings(max_examples=6, deadline=None, suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(lokale=st.booleans(), ziarno=st.integers(0, 10**6), strategie=st.lists(st.sampled_from(STRATEGIE), min_size=3,
                                                                                max_size=3), data=st.data())
def test_kasa_zgadza_sie_z_kpir_w_losowych_grach(lokale, ziarno, strategie, data):
    dodatki = [data.draw(_dodatki(lokale)) for _ in range(6)]
    _sprawdz(_graj(lokale, ziarno, strategie, dodatki))


def test_uzgodnienie_obejmuje_wszystkie_rodzaje_operacji():
    """Scenariusz z każdym rodzajem: inwestycje (kupno działki), kaucja, kredyt, lokata, Harpagon, podatki."""
    dodatki = [{"lokal": {"id": "centrum_2", "forma": "najem"}, "harpagon_wez": 3000,
                "kredyty_wez": [{"bank": "Crédit Agricole", "produkt": "start", "kwota": 20000, "rund": 26}],
                "lokaty_zaloz": [{"bank": "ING", "kwota": 5000, "rund": 4}]},
               {"harpagon_splac": 5000}, {}, {"lokal": {"id": "czechow_3", "forma": "kupno"}}]   # lokal co 3 rundy
    s = _graj(True, 3, ["zrownowazony"] * 3, dodatki)
    _sprawdz(s)
    rodzaje = {p["rodzaj"] for r in s.wyniki for p in s.wyniki[r]["H"]["uzgodnienie"]["poza"]}
    assert {"inwestycje", "kaucje", "kredyty", "lokaty", "harpagon", "podatki"} <= rodzaje
