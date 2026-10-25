"""Dostępność ofert w rundach i tryby kredytu odnawialnego."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from silnik import Gra  # noqa: E402
from silnik.dane import dane_domyslne  # noqa: E402
from silnik.decyzje import zastosuj  # noqa: E402
from silnik.finanse import Ksiega, Rachunek  # noqa: E402
from silnik.model import Firma  # noqa: E402

D = dane_domyslne()


def test_banki_od_rundy():
    assert set(D.dostepne("banki", 1)) == {"MBP Bank", "Beauty Bank", "Euro Biznes Bank"}
    assert len(D.dostepne("banki", 4)) == 6
    f = Firma(nazwa="X")
    zastosuj(D, f, {"bank": "Gaz Bank"}, 1, [], {}, Ksiega(), Rachunek())
    assert f.bank is None
    zastosuj(D, f, {"bank": "Gaz Bank"}, 4, [], {}, Ksiega(), Rachunek())
    assert f.bank == "Gaz Bank"


def test_media_i_internet_od_rundy():
    assert {m["kategoria"] for m in D.dostepne("media_tradycyjne", 5).values()} == {"billboard_ulotki", "prasa"}
    assert "radio" in {m["kategoria"] for m in D.dostepne("media_tradycyjne", 6).values()}
    assert "telewizja" in {m["kategoria"] for m in D.dostepne("media_tradycyjne", 7).values()}
    assert len(D.dostepne("narzedzia_internetowe", 6)) == 6 and "Profil na Facebook" in D.dostepne("narzedzia_internetowe", 6)
    assert len(D.dostepne("narzedzia_internetowe", 7)) == 9
    k = Ksiega()
    zastosuj(D, Firma(nazwa="X"), {"reklama_tradycyjna": {"Fitness TV": 1, "Radio Fakty": 10, "Ulotki": 4}}, 5, [], {}, k, Rachunek())
    assert [p["opis"] for p in k.pozycje] == ["Reklama tradycyjna: Ulotki"]


def _gra(tryb):
    g = Gra.nowa("t", [("A", None)], liczba_rund=3, ziarno=1, kredyt_odnawialny=tryb)
    g.ustaw_decyzje("A", {"oferta": {"step": 300}, "stanowiska": {"instruktor": 5, "recepcja": 5}, "bank": "MBP Bank", "biuro": "Plus"})
    g.wyslij("A")
    g.przelicz()
    # runda 2: zakupy większe niż saldo (sprzęt na 10 stanowisk), ale sprzedaż daje przychód
    kup = [{"typ": "instruktor", "nr": n, "nazwa": s, "jakosc": 3} for n in range(1, 6) for s in D.uslugi["step"]["sprzet"]]
    kup += [{"typ": "recepcja", "nr": n, "nazwa": s, "jakosc": 3} for n in range(1, 6) for s in D.sprzet_recepcji]
    g.ustaw_decyzje("A", {"sprzet_kup": kup})
    g.wyslij("A")
    return g.przelicz().wyniki[2]["A"]


def test_tryby_kredytu_odnawialnego():
    jedn, bież = _gra("jednoczesnie"), _gra("na_biezaco")
    uruch = lambda w: [o for o in w["rachunek"] if o["opis"] == "Uruchomienie kredytu odnawialnego"]
    assert len(uruch(jedn)) <= 1                       # tylko niedobór na koniec miesiąca
    assert len(uruch(bież)) >= 1                       # na bieżąco: od razu przy zakupach
    pierwsza = next(i for i, o in enumerate(bież["rachunek"]) if o["opis"] == "Uruchomienie kredytu odnawialnego")
    assert not any(o["opis"].startswith("Sprzedaż") for o in bież["rachunek"][:pierwsza])
    assert bież["kredyt_odnawialny"] >= jedn["kredyt_odnawialny"]


def test_limit_uslug_dotyczy_przyrostu():
    # gra ATH, marzec: z 3 usług (step, TBC, zumba) na 6 – 5 nowych, 2 usunięte
    f = Firma(nazwa="ATH", oferta={"step": 1, "tbc": 1, "zumba": 1})
    nowa = {u: 1 for u in ("bodybuilding", "crossfit", "joga", "kettlebell_trening", "pilates", "tbc")}
    zastosuj(D, f, {"oferta": nowa}, 3, [], {}, Ksiega(), Rachunek())
    assert set(f.oferta) == set(nowa)
    zastosuj(D, f, {"oferta": {**nowa, "step": 1, "zumba": 1, "trx": 1, "joga": 1, "trening_wzmacniajacy": 1}},
             4, [], {}, Ksiega(), Rachunek())
    assert len(f.oferta) == 9                          # najwyżej +3 w rundzie


def test_ten_sam_kandydat_w_dwoch_firmach():
    # gra A/B/C: drużyny A i C zatrudniły w lutym Małgorzatę Miś i Edytę Tarnowską
    g = Gra.nowa("t", [("A", None), ("C", None)], liczba_rund=3, ziarno=1)
    for f in ("A", "C"):
        g.ustaw_decyzje(f, {"oferta": {"step": 300}, "stanowiska": {"instruktor": 1, "recepcja": 1},
                            "bank": "MBP Bank", "biuro": "Plus"})
        g.wyslij(f)
    g.przelicz()
    mis = next(k for k in g.stan().kandydaci if k["imie_nazwisko"] == "Małgorzata Miś")
    for f in ("A", "C"):
        g.ustaw_decyzje(f, {"zatrudnij": [{"kandydat": mis["id"], "typ": "instruktor", "nr": 1, "pensja": 5300}]})
        g.wyslij(f)
    s = g.przelicz()
    assert all(mis["id"] in s.firmy[f].pracownicy for f in ("A", "C"))
