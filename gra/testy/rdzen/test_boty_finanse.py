"""B11: boty potrafią korzystać z finansów – lokata z nadwyżki (`lokaty`), jeden kredyt (`kredyt`), Harpagon przy
braku gotówki (`harpagon`) i kasyno po zaproszeniu (`kasyno`); bez ustawień – nic z tego. Pomiar w
balans/warianty.py (warianty lokata:*, kredyt:*, harpagon:*, kasyno:*). B12: samodzielna księgowość
(`ksiegowosc`) i higiena obniżona po odbiorze lokali (`higiena_po_odbiorze`)."""
import copy

import pytest

from silnik import boty
from silnik.gra import Gra
from silnik.ksiegowosc import biuro as bo
from silnik.pieniadze import banki as bk
from silnik.pieniadze import kasyno as kas
from silnik.pieniadze import wlasciciel as wl

pytestmark = pytest.mark.dane_gry

FINANSE = ("kredyty_wez", "lokaty_zaloz", "lokaty_zerwij", "harpagon_wez", "harpagon_splac", "kasyno",
           "wyplata_wlasna", "wplata_wlasna")


def _dane_strategii(dane, strategia: dict):
    """Dane gry ze strategią zrównoważoną nadpisaną ustawieniami `strategia`."""
    dane = copy.copy(dane)
    st = dane.boty["strategie"]
    dane.boty = {**dane.boty, "strategie": {**st, "zrownowazony": {**st["zrownowazony"], **strategia}}}
    return dane


def _gra(rund: int, ziarno: int = 5, **opcje) -> Gra:
    """Gra A (zrównoważony) i B (tani) przeliczona do rundy `rund` - 1 włącznie."""
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, ziarno, **opcje)
    for _ in range(rund - 1):
        g.przelicz(wymus=True)
    return g


def _decyzje(g: Gra, strategia: dict, runda: int) -> dict:
    return boty.decyzje_bota(_dane_strategii(g.dane, strategia), g.stan(runda - 1), "A", "zrownowazony", runda,
                             g.konfiguracja)


def test_bez_ustawien_bot_nie_rusza_finansow():
    g = _gra(3)
    d = _decyzje(g, {}, 3)
    assert not any(d.get(x) for x in FINANSE)


def test_bot_bierze_kredyt_w_najtanszym_banku_w_wybranej_rundzie():
    g = _gra(7)   # obrotowy: bank wymaga historii firmy
    k = {"produkt": "obrotowy", "kwota": 20000, "rund": 52, "od_rundy": 7}
    assert not _decyzje(g, {"kredyt": {**k, "od_rundy": 8}}, 7).get("kredyty_wez")
    d = _decyzje(g, {"kredyt": k}, 7)
    assert d["kredyty_wez"] == [x := d["kredyty_wez"][0]] and x["kwota"] == 20000 and x["miesiecy"] == 52
    oferty = {b: p["oprocentowanie"] for b, bank in bk.banki(g.dane).items() for p in bank["kredyty"]
              if p["produkt"] == "obrotowy"}
    dostepne = [b for b in oferty if not bk.powod_kredytu(g.dane, g.stan(6).firmy["A"], {**x, "bank": b}, 7)]
    assert dostepne and oferty[x["bank"]] == min(oferty[b] for b in dostepne)
    przed = sum(k.kwota_gr for k in g.stan(6).firmy["A"].kredyty)
    g.ustaw_decyzje("A", d)
    s = g.przelicz(wymus=True)
    assert sum(k.kwota_gr for k in s.firmy["A"].kredyty) == przed + 20000 * 100


def test_bot_odklada_nadwyzke_na_lokate_i_zrywa_ja_przy_braku_gotowki():
    g = _gra(3)
    f = g.stan(2).firmy["A"]
    lo = {"bufor": 5000, "rund": 4, "min_kwota": 1000}
    d = _decyzje(g, {"lokaty": lo}, 3)
    assert d["lokaty_zaloz"] == [{"kwota": round(f.gotowka - 5000, 2), "miesiecy": 4,
                                  "bank": bk.najlepsze(g.dane)["lokata"]}]
    assert not _decyzje(g, {"lokaty": {**lo, "bufor": f.gotowka - 500}}, 3).get("lokaty_zaloz")   # < min_kwota
    g.ustaw_decyzje("A", d)
    s = g.przelicz(wymus=True)
    assert len(s.firmy["A"].lokaty) == 1
    d = _decyzje(g, {"lokaty": {**lo, "zerwij_ponizej": 10**9}}, 4)
    assert d["lokaty_zerwij"] == [s.firmy["A"].lokaty[0].id] and not d.get("lokaty_zaloz")


def test_bot_pozycza_u_harpagona_przy_braku_gotowki_i_splaca_z_nadwyzki():
    g = _gra(3)
    assert not _decyzje(g, {"harpagon": {"prog": 0, "kwota": 5000}}, 3).get("harpagon_wez")
    d = _decyzje(g, {"harpagon": {"prog": 10**9, "kwota": 5000}}, 3)
    assert d["harpagon_wez"] == 5000 and not d.get("harpagon_splac")
    g.ustaw_decyzje("A", d)
    s = g.przelicz(wymus=True)
    assert (p := s.firmy["A"].harpagon) is not None
    d = _decyzje(g, {"harpagon": {"prog": 1, "kwota": 5000}}, 4)
    assert d["harpagon_splac"] == p.dlug and not d.get("harpagon_wez")
    got = s.firmy["A"].gotowka   # nadwyżka ponad próg mniejsza niż dług – spłata częściowa
    d = _decyzje(g, {"harpagon": {"prog": got - 1000, "kwota": 5000}}, 4)
    assert d["harpagon_splac"] == pytest.approx(1000) and not d.get("harpagon_wez")


def test_boty_dostaja_zaproszenia_do_klubu_tylko_przy_kasyno_botow():
    def zaproszenia(**opcje):
        return _gra(13, 1, **opcje).stan(12).firmy["A"].zaproszenia
    assert zaproszenia() == []
    assert zaproszenia(kasyno_botow=True) == [4, 11]   # ziarno 1 (losowanie w silnik/pieniadze/kasyno.py)


def test_bot_gra_w_kasynie_tylko_po_zaproszeniu_i_wplaca_wygrana():
    r = 4   # ziarno 1: pierwsze zaproszenie (test wyżej)
    ka = {"gra": "ruletka", "zaklad": "czerwone", "stawka": 1000, "zakladow": 3}
    bez = _decyzje(_gra(r, 1), {"kasyno": ka}, r)   # bez zaproszenia – bez gry i bez wypłaty z portfela
    assert not bez.get("kasyno") and not bez.get("wyplata_wlasna")
    g = _gra(r, 1, kasyno_botow=True)
    assert kas.otwarte(g.stan(r - 1).firmy["A"], r)
    d = _decyzje(g, {"kasyno": ka}, r)
    assert d["kasyno"] == [{"gra": "ruletka", "zaklad": "czerwone", "stawka": 1000}] * 3
    assert d["wyplata_wlasna"] == 3000 and not d.get("wplata_wlasna")
    g.ustaw_decyzje("A", d)
    s = g.przelicz(wymus=True)
    wygrana = wl.portfel(g.dane, s.firmy["A"]) - wl.dane_portfela(g.dane)["portfel"]["oszczednosci"]
    d = _decyzje(g, {"kasyno": ka}, r + 1)
    assert d.get("wplata_wlasna", 0) == pytest.approx(max(wygrana, 0)) and not d.get("kasyno")


def _samodzielnie(rund: int, ksiegowosc: dict | None) -> tuple[Gra, dict]:
    """Gra, w której A od 1. rundy księguje sam; decyzje A w rundzie `rund` z ustawieniem `ksiegowosc`."""
    g = Gra.nowa("t", [("A", "zrownowazony"), ("B", "tani")], 12, 5)
    for r in range(1, rund):
        if r == 1:
            g.ustaw_decyzje("A", {**_decyzje(g, {}, 1), "biuro": bo.SAMODZIELNIE})
        g.przelicz(wymus=True)
    return g, _decyzje(g, {"ksiegowosc": ksiegowosc} if ksiegowosc else {}, rund)


def test_bot_ksieguje_sam_bez_bledow_i_nie_placi_mandatu():
    g, bez = _samodzielnie(3, None)
    assert not bez.get("ksiegowosc")   # bez ustawienia – nie składa deklaracji
    _, d = _samodzielnie(3, {"bledy": 0})
    dk = g.stan(2).firmy["A"].deklaracja
    assert d["ksiegowosc"]["deklaracja"] == dk["poprawne"]
    assert bo.sprawdz_zapisy(dk["dokumenty"], d["ksiegowosc"]["zapisy"])["dobre"] == len(dk["dokumenty"])
    g.ustaw_decyzje("A", d)
    g.przelicz(wymus=True)
    k = g.stan().wyniki[g.runda - 1]["A"]["ksiegowosc"]
    assert k["tryb"] == "deklaracja" and k["kara"] == 0


def test_bot_z_bledami_zaniza_deklaracje_o_odchylenie():
    g, d = _samodzielnie(3, {"bledy": 1, "odchylenie": 0.5})
    pop = g.stan(2).firmy["A"].deklaracja["poprawne"]
    assert d["ksiegowosc"]["deklaracja"] == {p: round(v * 0.5, 2) for p, v in pop.items()}


def test_bot_obniza_higiene_dopiero_po_odbiorze_lokali():
    g = _gra(3)
    f = g.stan(2).firmy["A"]
    assert f.lokale and all(x.id in f.odbiory for x in f.lokale)
    assert _decyzje(g, {"higiena_po_odbiorze": "brak"}, 3)["higiena"] == "brak"
    g0 = _gra(1)   # przed pierwszym lokalem – higiena ze strategii (odbiór jeszcze przed nami)
    assert _decyzje(g0, {"higiena": "podstawowa", "higiena_po_odbiorze": "brak"}, 1)["higiena"] == "podstawowa"
