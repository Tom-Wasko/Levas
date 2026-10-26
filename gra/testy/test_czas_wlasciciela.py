"""Czas właściciela (F3a.7): pula godzin na rundę, odbiór osobisty w dyskontach, odrzucenie zakupów bez czasu."""

from datetime import date, timedelta

import pytest
from test_lokale import _gra, _lokal, _runda

from silnik import czas_wlasciciela as cw
from silnik import dostawcy as dst
from silnik.dane import dane_domyslne

PN = date(2026, 10, 12)


def test_pula_godzin():
    c = cw.Czas(3)
    assert c.wez(1.5, "a", "dostawcy") and c.wez(1.5, "b", "dostawcy") and not c.wez(1, "c", "dostawcy")
    p = c.podsumowanie()
    assert (p["pula"], p["wykorzystane"], p["wolne"]) == (3, 3, 0)
    assert [x["przyjete"] for x in p["pozycje"]] == [True, True, False]
    assert cw.nowy(dane_domyslne()).pula == dane_domyslne().z["operacje"]["czas_wlasciciela"]


def test_zakupy_w_dyskoncie_bez_czasu_sa_odrzucone():
    dane = dane_domyslne()
    zam = [{"dostawca": "Biedronka", "zasob": "Napój", "jakosc": 2, "ilosc": 1, "dzien": dz, "cena": 3.0} for dz in (0, 2)]
    zam.append({"dostawca": "Makro", "zasob": "Napój", "jakosc": 2, "ilosc": 1, "dzien": 3, "cena": 3.0})   # dowóz – bez czasu
    czas = cw.Czas(2)
    przyjete, w = dst.zasady_dostaw(dane, zam, PN, 7, czas)
    assert [(z["dostawca"], z["dzien"]) for z in przyjete] == [("Biedronka", 0), ("Makro", 3)]
    assert len(w["uwagi"]) == 1 and "brak czasu właściciela" in w["uwagi"][0] and "w środę" in w["uwagi"][0]
    assert w["czas_wlasciciela"] == {"Biedronka": pytest.approx(1.5)}
    assert [(x["dostawca"], x["dzien"]) for x in w["dostawy"]] == [("Biedronka", 0), ("Makro", 3)]
    assert czas.wykorzystane == pytest.approx(1.5) and [p["przyjete"] for p in czas.pozycje] == [True, False]
    assert len(dst.zasady_dostaw(dane, zam, PN, 7)[0]) == 3                  # bez puli (gra Revas) – bez limitu


def test_gra_brak_czasu_na_liscie_bledow():
    g = _gra(("A", None), ("B", None))
    _runda(g, A=_lokal("centrum_3"))
    zam = [{"dostawca": d, "zasob": "Napój", "jakosc": 2, "ilosc": 1, "dzien": dz} for dz in range(7) for d in ("Biedronka", "Lidl")]
    s = _runda(g, A={"zamowienia": zam})
    w = s.wyniki[2]["A"]
    c = w["czas_wlasciciela"]
    assert c["pula"] == g.dane.z["operacje"]["czas_wlasciciela"] == 20
    assert c["wykorzystane"] == pytest.approx(19.5) and [p["opis"] for p in c["pozycje"] if not p["przyjete"]] == [
        f"Odbiór osobisty: Lidl (niedziela {g.dane.data_rundy(2) + timedelta(days=6):%d.%m})"]
    assert [x["dzien"] for x in w["dostawy"]["dostawy"] if x["dostawca"] == "Lidl"] == [0, 1, 2, 3, 4, 5]
    assert any(b["poziom"] == "czerwony" and "brak czasu właściciela" in b["tekst"] for b in w["lista_bledow"])
    assert s.wyniki[2]["B"]["czas_wlasciciela"]["wykorzystane"] == 0
