"""Debet ponad limit i inwestor ratunkowy (Z3): alarm, blokada inwestycji i kredytów w następnej rundzie, wpłata
inwestora od mistrza gry (spłata debetu, udział w dochodach, niezwrócona wpłata jako dług w karcie i majątku)."""

import pytest
from pomocnicze import _gra, _lokal, _runda

from silnik.ksiegowosc.finanse import Rachunek, zadluzenie
from silnik.model import Firma, Inwestor
from silnik.pieniadze import banki as bk
from silnik.pieniadze import inwestor as inw

SPRZET = {"typ": "kuchnia", "nr": 2, "nazwa": "Rożen", "jakosc": 2}   # druga kuchnia A


def _w_debecie(ponad=5000):
    """Runda 1 za nami, firma A (mBank) z debetem ponad limit konta."""
    g = _gra(("A", None), ("B", None))
    _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 1}, "bank": "mBank"},
           B={**_lokal("zygmuntowskie_1"), "bank": "mBank"})
    f = g.stan(1).firmy["A"]
    f.kredyt_odnawialny, f.gotowka = bk.banki(g.dane)["mBank"]["limit"]["kwota"] + ponad, 0
    return g


def _bledy(s, r, firma):
    return [b["tekst"] for b in s.wyniki[r][firma]["lista_bledow"] if b["zakladka"] == "finanse_bank"]


def test_alarm_i_blokada_inwestycji_i_kredytow():
    g = _w_debecie()
    assert g.stan(1).wyniki[1]["B"]["alarm"] == 0
    s = _runda(g, A={"sprzet_kup": [SPRZET], "kredyty_wez": [{"kwota": 5000, "miesiecy": 6}],
                     "lokaty_zaloz": [{"bank": "mBank", "kwota": 1000, "rund": 4}], "harpagon_wez": 5000},
               B={"lokaty_zaloz": [{"bank": "mBank", "kwota": 1000, "rund": 4}]})
    a = s.firmy["A"]
    assert "Rożen" not in a.stanowisko("kuchnia", 2).sprzet and not a.kredyty and not a.lokaty
    assert a.harpagon is not None   # pilna gotówka u Harpagona zostaje
    assert sum("zablokowane – debet" in t for t in _bledy(s, 2, "A")) == 3
    assert s.firmy["B"].lokaty and not _bledy(s, 2, "B")
    assert s.wyniki[2]["A"]["alarm"] == bk.debet_ponad_limit(g.dane, a) > 0


def test_inwestor_splaca_debet_i_liczy_sie_jak_dlug():
    g = _w_debecie(ponad=5000)
    debet = g.stan(1).firmy["A"].kredyt_odnawialny
    g.ustaw_inwestora("A", 20000)
    s = _runda(g, A={"sprzet_kup": [SPRZET]})
    a, w = s.firmy["A"], s.wyniki[2]["A"]
    assert a.inwestor.kwota == 20000 and a.inwestor.od_rundy == 2
    assert a.inwestor.do_rundy == 1 + inw.warunki(g.dane)["rund"]
    assert w["inwestor"]["splata_debetu"] == debet   # wpłata najpierw spłaca debet, więc blokady nie ma
    assert "Rożen" in a.stanowisko("kuchnia", 2).sprzet
    assert any("Inwestor ratunkowy wpłacił" in b["tekst"] for b in w["lista_bledow"])
    assert w["majatek_netto"]["inwestor"] == -a.inwestor.dlug < 0
    assert w["zadluzenie"] == pytest.approx(zadluzenie(a)) and zadluzenie(a) >= a.inwestor.dlug
    assert [o["kwota"] for o in w["rachunek"] if o["rodzaj"] == "inwestor"][0] == 20000
    assert w["uzgodnienie"]["roznica"] == 0


def test_warunki_przyslania_inwestora():
    g = _w_debecie()
    with pytest.raises(ValueError, match="debetem ponad limit"):
        g.ustaw_inwestora("B", 10000)
    with pytest.raises(ValueError, match="najwyżej"):
        g.ustaw_inwestora("A", inw.warunki(g.dane)["max_kwota"] + 1)
    g.ustaw_inwestora("A", 10000)
    g.ustaw_inwestora("A", 0)    # odwołanie przed zamknięciem rundy
    assert "inwestorzy" not in g.konfiguracja
    g.ustaw_inwestora("A", 10000)
    _runda(g)
    with pytest.raises(ValueError, match="jeden na grę"):
        g.ustaw_inwestora("A", 10000)
    g.cofnij()   # wpłata zostaje przy rundzie 2 i wraca przy ponownym przeliczeniu
    assert _runda(g).firmy["A"].inwestor.kwota == 10000


def test_udzial_w_dodatnim_dochodzie_do_konca_umowy():
    f = Firma(nazwa="A", gotowka=5000)
    f.inwestor = Inwestor(kwota=1000, od_rundy=2, do_rundy=3, udzial=0.3)
    rach = Rachunek()
    assert inw.koniec_rundy(f, 2, 2000, rach) == 600
    assert inw.koniec_rundy(f, 3, -500, rach) == 0     # strata – bez wypłaty
    assert inw.koniec_rundy(f, 4, 5000, rach) == 0     # po umowie – bez wypłaty
    assert f.gotowka == 4400 and f.inwestor.dlug == 400
    assert inw.koniec_rundy(f, 3, 3000, rach) == 900 and f.inwestor.dlug == 0   # ponad wpłatę – zysk inwestora
