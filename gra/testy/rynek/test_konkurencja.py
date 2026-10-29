"""Konkurencja i detektyw (P16): ogólny obraz rynku, zlecenie (koszt, godziny, odrzucenia), raport, wpadka, widok."""

import copy

import pytest
import yaml
from pomocnicze import _gra, _runda
from pydantic import ValidationError

from silnik.dane import KATALOG_DANYCH, dane_domyslne
from silnik.rynek import konkurencja as kn
from silnik.schematy import PlikDetektywa


def _surowe():
    return yaml.safe_load((KATALOG_DANYCH / "zdarzenia" / "detektyw.yaml").read_text(encoding="utf-8"))


def _gra_z_botami():
    g = _gra(("A", "zrownowazony"), ("B", "tani"), ("C", None))
    _runda(g)
    _runda(g)
    return g


def test_dane_detektywa():
    dane = dane_domyslne()
    z = kn.dane_detektywa(dane)["detektyw"]
    assert z["budynek"] in {b["id"] for b in dane.mapa["budynki"]}
    assert any(b["zakladka"] == kn.ZAKLADKA for b in dane.mapa["budynki"])
    assert (z["koszt_min"], z["koszt_maks"], z["godziny"], z["szansa_wpadki"]) == (300, 800, 2, 0.15)
    ceny = {kn.koszt(dane, 1, r, f) for r in range(2, 40) for f in "ABC"}
    assert all(300 <= c <= 800 and c % 10 == 0 for c in ceny) and len(ceny) > 5
    w = _surowe()
    w["detektyw"]["koszt_min"] = 900
    with pytest.raises(ValidationError):
        PlikDetektywa.model_validate(w)
    w = _surowe()
    w["detektyw"]["od_rundy"] = 1   # tydzień przygotowawczy
    with pytest.raises(ValidationError):
        PlikDetektywa.model_validate(w)


def test_przeglad_rynku():
    g = _gra_z_botami()
    s = g.stan(2)
    P = {r["firma"]: r for r in kn.przeglad(s.rynek[2], "C")}
    assert set(P) == {"A", "B", "C"} and P["C"]["ja"] and not P["A"]["ja"]
    assert P["A"]["lokale"] == 1 and P["C"]["lokale"] == 0 and P["C"]["cena_min"] is None
    assert P["A"]["cena_min"] <= P["A"]["cena_maks"]
    assert sum(r["udzial"] for r in P.values()) == pytest.approx(1, abs=1e-3)
    assert kn.przeglad(None, "C") == []


def test_zlecenie_raport_i_koszt():
    g = _gra_z_botami()
    gotowka = g.stan(2).firmy["C"].gotowka
    s = _runda(g, C={"detektyw": "B"})
    K = s.wyniki[3]["C"]["konkurencja"]
    z = K["zlecenie"]
    assert z["przyjete"] and z["rywal"] == "B" and z["koszt"] == kn.koszt(g.dane, g.konfiguracja["ziarno"], 3, "C")
    R = K["raport"]
    wb = s.wyniki[3]["B"]
    assert R["gotowka"] == wb["gotowka"] and R["dochod_netto"] == wb["kpir"]["dochod_netto"]
    assert {m["usluga"]: m["sprzedaz"] for m in R["menu"]} == {u: x["sprzedaz"] for u, x in wb["sprzedaz"].items()}
    assert sum(x["liczba"] for x in R["zaloga"]) == len(wb["pracownicy"])
    assert "{" not in R["tekst"]
    assert any(p["opis"] == kn.OPIS for p in s.wyniki[3]["C"]["kpir"]["pozycje"])
    assert any(p["zakladka"] == kn.ZAKLADKA and p["przyjete"] for p in s.wyniki[3]["C"]["czas_wlasciciela"]["pozycje"])
    assert s.firmy["C"].gotowka < gotowka
    assert s.wyniki[3]["A"]["konkurencja"] == {"zlecenie": None, "raport": None, "wpadki": []}


def test_odrzucone_zlecenia():
    g = _gra_z_botami()
    for cel in ("C", "nikt"):
        s = copy.deepcopy(g)
        st = _runda(s, C={"detektyw": cel})
        K = st.wyniki[3]["C"]["konkurencja"]
        assert not K["zlecenie"]["przyjete"] and K["raport"] is None
        assert any(b["zakladka"] == kn.ZAKLADKA and b["poziom"] == "czerwony" for b in st.wyniki[3]["C"]["lista_bledow"])
        assert not any(p["opis"] == kn.OPIS for p in st.wyniki[3]["C"]["kpir"]["pozycje"])
    # tydzień 1 – przygotowawczy
    g = _gra()
    s = _runda(g, A={"detektyw": "B"})
    assert s.wyniki[1]["A"]["konkurencja"]["zlecenie"]["powod"].startswith("detektyw przyjmuje zlecenia od rundy")
    # bez wolnych godzin właściciela
    dane = g.dane
    f = s.firmy["A"]

    class Pelny:
        def wez(self, *a):
            return False
    from silnik.ksiegowosc.finanse import Ksiega, Rachunek
    z = kn.zlec(dane, f, {"detektyw": "B"}, 5, 1, ["A", "B"], Ksiega(), Rachunek(), Pelny())
    assert not z["przyjete"] and "godzin" in z["powod"] and kn.bledy(z)


def test_wpadka():
    """Przy pewnej wpadce raport i tak przychodzi, a śledzony wie, kto go śledził."""
    g = _gra_z_botami()
    g.dane = copy.copy(g.dane)
    g.dane.zdarzenia = {**g.dane.zdarzenia, "detektyw": copy.deepcopy(g.dane.zdarzenia["detektyw"])}
    g.dane.zdarzenia["detektyw"]["detektyw"]["szansa_wpadki"] = 1.0
    s = _runda(g, C={"detektyw": "A"})
    K, KA = s.wyniki[3]["C"]["konkurencja"], s.wyniki[3]["A"]["konkurencja"]
    assert K["zlecenie"]["wpadka"] and K["raport"]["wpadka"] and "{" not in K["raport"]["wpadka"]
    assert [x["kto"] for x in KA["wpadki"]] == ["C"] and "C" in KA["wpadki"][0]["tekst"]


def test_widok_api():
    from api.prezentacja import widok
    g = _gra_z_botami()
    g.ustaw_decyzje("C", {"detektyw": "B"})
    v = widok(g, "C")
    K = v["konkurencja"]
    assert K["otwarty"] and K["decyzja"]["przyjete"] and not K["decyzja"]["wpadka"]
    assert K["koszt"] == K["decyzja"]["koszt"] and {r["firma"] for r in K["przeglad"]} == {"A", "B", "C"}
    s = _runda(g)
    v = widok(g, "C")
    assert v["wyniki"]["konkurencja"]["raport"]["rywal"] == "B"
    v = widok(g, "C", 3)
    assert v["konkurencja"]["decyzja"]["rywal"] == "B"
    assert s.runda == 3
