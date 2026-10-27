"""Kalendarz miejski (F3b.9): daty stałe i ruchome, mnożniki stref, zmiana tygodniowej puli, widok, sprawdzanie danych."""

from datetime import date, timedelta

import pytest
import yaml
from pydantic import ValidationError
from test_dane import _kopia, _zmien
from test_lokale import _gra, _runda

from silnik import kalendarz as kl
from silnik import popyt as pp
from silnik.dane import KATALOG_DANYCH, dane_domyslne, sprawdz
from silnik.schematy import PlikKalendarza


def _runda_z(dane, dzien):
    return next(r for r in range(1, 60) if dane.data_rundy(r) <= dzien < dane.data_rundy(r + 1))


def _dni_wydarzenia(dane, nazwa, od, do):
    k = kl.dane_kalendarza(dane)
    w = next(x for x in k["wydarzenia"] if x["nazwa"] == nazwa)
    return [od + timedelta(days=i) for i in range((do - od).days + 1) if kl.trwa(k, w, od + timedelta(days=i))]


def test_daty_stale_i_ruchome():
    d = dane_domyslne()
    assert _dni_wydarzenia(d, "Tłusty czwartek", date(2027, 1, 1), date(2027, 3, 31)) == [date(2027, 2, 4)]
    assert _dni_wydarzenia(d, "Wielkanoc", date(2027, 3, 1), date(2027, 4, 30)) == [date(2027, 3, 27), date(2027, 3, 28),
                                                                                   date(2027, 3, 29)]
    assert _dni_wydarzenia(d, "Black Friday", date(2026, 11, 1), date(2026, 11, 30)) == [date(2026, 11, 27)]
    ferie = _dni_wydarzenia(d, "Ferie zimowe", date(2027, 1, 1), date(2027, 2, 28))
    assert len(ferie) == 14 and ferie[0].weekday() == 0
    # zakres przez Nowy Rok
    przerwa = _dni_wydarzenia(d, "Przerwa świąteczna na uczelniach", date(2026, 12, 1), date(2027, 1, 31))
    assert przerwa[0] == date(2026, 12, 21) and przerwa[-1] == date(2027, 1, 6)
    # rok bez daty ruchomej – wydarzenia nie ma
    assert not _dni_wydarzenia(d, "Tłusty czwartek", date(2030, 1, 1), date(2030, 12, 31))


def test_mnozniki_i_zmiana_puli(monkeypatch):
    d = dane_domyslne()
    swieta = kl.tydzien(d, _runda_z(d, date(2026, 12, 24)))
    assert {"Wigilia i Boże Narodzenie", "Przerwa świąteczna na uczelniach"} <= {w["nazwa"] for w in swieta["wydarzenia"]}
    assert swieta["strefy"]["akademickie"] < -0.5 < swieta["strefy"]["centrum"] < 0
    assert kl.mnoznik(d, "akademickie", date(2026, 12, 24)) == pytest.approx(0.35 * 0.35)   # dwa wydarzenia się mnożą
    assert kl.mnoznik(d, "stare_miasto", date(2026, 12, 31)) == 2.0   # strefa wygrywa z „wszystkie”
    jarmark = kl.tydzien(d, _runda_z(d, date(2026, 12, 9)))
    assert jarmark["strefy"]["stare_miasto"] == pytest.approx(0.25) and "felin" not in jarmark["strefy"]
    # zmiana tygodnia = stosunek wag dni z kalendarzem i bez
    r = _runda_z(d, date(2026, 11, 11))
    dni = pp.dni_rundy(d, r)
    z = pp.wagi_dni(d, "centrum", dni).sum() / pp.wagi_dni(d, "centrum", dni, kalendarz=False).sum() - 1
    assert kl.tydzien(d, r)["strefy"]["centrum"] == pytest.approx(z, abs=1e-4) and z > 0
    # pula strefy w rundzie świątecznej jest mniejsza niż bez kalendarza
    pr = pp.pule(d, _runda_z(d, date(2026, 12, 24)))
    monkeypatch.setattr(d, "kalendarz_miasta", None)   # dane_domyslne() są wspólne – przywracane po teście
    bez = pp.pule(d, _runda_z(d, date(2026, 12, 24)))
    u = next(iter(pr["akademickie"]))
    assert pr["akademickie"][u].sum() < 0.5 * bez["akademickie"][u].sum()
    assert kl.tydzien(d, 1)["strefy"] == {} and kl.widok(d, 1, 26) is None


def test_schemat_kalendarza():
    w = yaml.safe_load((KATALOG_DANYCH / "kalendarz" / "kalendarz.yaml").read_text(encoding="utf-8"))
    PlikKalendarza.model_validate(w)
    for zmiana in ({"od": "13-01"}, {"od": 3, "do": 1, "wzgledem": "wielkanoc"}, {"wzgledem": "kometa", "od": 0, "do": 0},
                   {"rodzaj": "zlot_ufo"}, {"strefy": {"centrum": -1}}):
        z = {**w, "wydarzenia": [{**w["wydarzenia"][0], **zmiana}]}
        with pytest.raises(ValidationError):
            PlikKalendarza.model_validate(z)


def test_sprawdz_wykrywa_bledy_kalendarza(tmp_path):
    kat = _kopia(tmp_path)

    def zmien(d):
        d["wydarzenia"][0]["strefy"] = {"atlantyda": 2.0}
        d["ruchome"]["wielkanoc"].pop(2027)

    _zmien(kat, "kalendarz/kalendarz.yaml", zmien)
    bledy = sprawdz(kat)
    assert any("atlantyda" in b for b in bledy), bledy
    assert any("wielkanoc" in b and "2027" in b for b in bledy), bledy


def test_widok_kalendarza():
    from api.prezentacja import widok
    g = _gra()
    v = widok(g, "A")["kalendarz_miasta"]
    assert len(v["tygodnie"]) == g.konfiguracja["liczba_rund"] and v["biezacy"]["runda"] == 1 and v["poprzedni"] is None
    assert v["biezacy"]["wydarzenia"][0]["opis"] and "opis" not in v["tygodnie"][0]["wydarzenia"][0]
    assert v["rodzaje"]["uczelnie"]
    _runda(g)
    v = widok(g, "A")["kalendarz_miasta"]
    assert v["biezacy"]["runda"] == 2 and v["poprzedni"]["runda"] == 1
    assert "kalendarz_miasta" not in widok(_gra(lokale=False), "A")
