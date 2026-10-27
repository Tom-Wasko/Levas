"""Urząd i sanepid (F3b.6): odbiór lokalu, higiena (koszt i wpływ na kontrole), skargi z historii, boty, widok API."""

import copy

import pytest
import yaml
from pydantic import ValidationError
from test_lokale import _gra, _lokal, _runda

from silnik import magazyn as mag
from silnik import urzad as urz
from silnik import zdarzenia as zd
from silnik.dane import KATALOG_DANYCH, dane_domyslne
from silnik.finanse import Ksiega, Rachunek
from silnik.schematy import PlikUrzedu, Skutek


def _surowe():
    return yaml.safe_load((KATALOG_DANYCH / "zdarzenia" / "urzad.yaml").read_text(encoding="utf-8"))


def test_dane_urzedu():
    dane = dane_domyslne()
    H = urz.higiena(dane)
    assert H["poziomy"][H["domyslna"]]["odbior"] and any(not p["odbior"] for p in H["poziomy"].values())
    assert urz.dane_urzedu(dane)["urzad"]["budynek"] in {b["id"] for b in dane.mapa["budynki"]}
    assert any(b["zakladka"] == urz.ZAKLADKA for b in dane.mapa["budynki"])
    w = _surowe()
    w["higiena"]["domyslna"] = next(k for k, p in w["higiena"]["poziomy"].items() if not p["odbior"])
    with pytest.raises(ValidationError):
        PlikUrzedu.model_validate(w)
    with pytest.raises(ValidationError):
        Skutek.model_validate({"typ": "kontrola", "opis": "Skarga", "rund": 2})   # bez szansy
    # skargi z historii w danych
    hs = zd.historie(dane)
    assert any(s["typ"] == "kontrola" for h in hs.values() for sc in h["sceny"].values()
               for s in [*sc.get("skutki", []), *(x for o in sc.get("opcje", []) for x in o.get("skutki", []))])


def test_odbior_lokalu_i_odmowa():
    """Bez sprzątania sanepid nie odbiera lokalu – lokal rusza dopiero po odbiorze przy lepszej higienie."""
    g = _gra()
    s = _runda(g, A={**_lokal("centrum_3"), "higiena": "brak"}, B=_lokal("centrum_1"))
    wa, wb = s.wyniki[1]["A"], s.wyniki[1]["B"]
    assert [(o["lokal"], o["przyjety"], o["dziala_od"]) for o in wa["urzad"]["odbiory"]] == [("centrum_3", False, 2)]
    assert "{" not in wa["urzad"]["odbiory"][0]["tekst"]
    assert s.firmy["A"].lokale[0].dziala_od == 2 and not s.firmy["A"].odbiory
    assert any(b["zakladka"] == urz.ZAKLADKA for b in wa["lista_bledow"])
    assert wa["urzad"]["lokale"] == 0 and wa["urzad"]["koszt"] == 0
    assert [o["przyjety"] for o in wb["urzad"]["odbiory"]] == [True] and s.firmy["B"].odbiory == {"centrum_1": 1}
    s = _runda(g, A={"higiena": "brak"})
    assert s.firmy["A"].lokale[0].dziala_od == 3
    s = _runda(g, A={"higiena": "podstawowa"})
    assert s.firmy["A"].odbiory == {"centrum_3": 3} and s.firmy["A"].lokale[0].dziala_od == 3
    s = _runda(g)
    assert not s.wyniki[4]["A"]["urzad"]["odbiory"] and s.firmy["A"].higiena == "podstawowa"


def test_koszt_higieny():
    g = _gra()
    s = _runda(g, A={**_lokal("centrum_3"), "higiena": "firma"})
    dane = g.dane
    p = urz.higiena(dane)["poziomy"]["firma"]
    u = s.wyniki[1]["A"]["urzad"]
    assert u["higiena"] == "firma" and u["lokale"] == 1 and u["koszt"] == pytest.approx(dane.na_runde(p["koszt"]))
    assert any(x["opis"].startswith(urz.SPRZATANIE) for x in s.wyniki[1]["A"]["kpir"]["pozycje"])
    s = _runda(g)   # decyzja trwa
    assert s.wyniki[2]["A"]["urzad"]["higiena"] == "firma" and s.wyniki[2]["A"]["urzad"]["koszt"] > 0
    assert s.wyniki[2]["B"]["urzad"]["koszt"] == 0   # bez lokalu


def test_higiena_i_skargi_zmieniaja_kontrole():
    g = _gra()
    s = _runda(g, A=_lokal("centrum_3"))
    dane, f = g.dane, copy.deepcopy(s.firmy["A"])
    z = mag.zasady_sanepidu(dane)
    bez = mag.szansa_kontroli(dane, 100, 300)
    assert mag.szansa_kontroli(dane, 100, 300, urz.modyfikatory(dane, f, 2)) == bez   # domyślna higiena – bez zmian
    f.higiena = "haccp"
    hac = mag.szansa_kontroli(dane, 100, 300, urz.modyfikatory(dane, f, 2))
    assert hac["problem"] == pytest.approx(bez["problem"] * urz.higiena(dane)["poziomy"]["haccp"]["mnoznik"], abs=1e-4)
    f.higiena = "brak"
    m = urz.modyfikatory(dane, f, 2)
    assert mag.szansa_kontroli(dane, 0, 0, m)["problem"] == pytest.approx(urz.higiena(dane)["poziomy"]["brak"]["dodatek"])
    assert mag.mandat(dane, 0, 0, m) == z["mandat_min"] + urz.higiena(dane)["poziomy"]["brak"]["mandat"]
    # skarga z historii: od tej rundy przez `rund` rund
    f.higiena = None
    zd._skutek(f, {"typ": "kontrola", "szansa": 0.2, "rund": 2, "opis": "Skarga"}, "h", 2, Ksiega(vat=None), Rachunek(), [])
    assert [urz.modyfikatory(dane, f, r)["skargi"] for r in (1, 2, 3, 4)] == [0, 0.2, 0.2, 0]
    assert mag.szansa_kontroli(dane, 0, 0, urz.modyfikatory(dane, f, 3))["szansa"] == pytest.approx(z["szansa_bazowa"] + 0.2)
    # kontrola na koniec rundy zapisuje higienę i skargi
    w = mag.koniec_rundy(dane, f, 3, 1, {}, Ksiega(vat=None), Rachunek(), urz.modyfikatory(dane, f, 3))
    assert w["sanepid"]["skargi"] == 0.2 and w["sanepid"]["higiena"] == urz.higiena(dane)["domyslna"]


def test_boty_higiena_wg_strategii():
    g = _gra(("Prem", "premium"), ("Tani", "tani"))
    for _ in range(3):
        s = g.przelicz(wymus=True)
    st = dane_domyslne().boty["strategie"]
    assert s.firmy["Prem"].higiena == st["premium"]["higiena"] and s.firmy["Tani"].higiena == st["tani"]["higiena"]
    assert all(set(s.firmy[n].odbiory) == {lok.id for lok in s.firmy[n].lokale if lok.dziala_od <= 3} for n in ("Prem", "Tani"))


def test_widok_api_i_gra_bez_lokali():
    from api.prezentacja import widok
    g = _gra()
    g.ustaw_decyzje("A", {**_lokal("centrum_3"), "higiena": "brak"})
    v = widok(g, "A")
    U = v["urzad"]
    assert [p["id"] for p in U["poziomy"]] == list(urz.higiena(g.dane)["poziomy"]) and U["higiena"] == "brak"
    assert U["decyzja"]["odbiory"][0]["przyjety"] is False and U["ryzyko"] is not None
    assert any(b["zakladka"] == urz.ZAKLADKA for b in v["lista_bledow"])
    g.ustaw_decyzje("A", {**_lokal("centrum_3"), "higiena": "podstawowa"})
    s = g.przelicz(wymus=True)
    v = widok(g, "A")
    assert v["urzad"]["lokale"] == [{"id": "centrum_3", "nazwa": v["urzad"]["lokale"][0]["nazwa"], "dziala_od": 1, "odbior": 1}]
    assert v["wyniki"]["urzad"]["odbiory"][0]["przyjety"] and s.firmy["A"].odbiory == {"centrum_3": 1}
    assert "urzad" not in widok(_gra(lokale=False), "A")
