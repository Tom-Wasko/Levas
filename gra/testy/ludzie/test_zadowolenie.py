"""U20 (decyzja autora 4.11.2026): zadowolenie każdej osoby, ukryte cechy z żartobliwym opisem, ostrzeżenie na liście
błędów i wypowiedzenie z niezadowolenia (szansa rośnie z niezadowoleniem)."""

import pytest
from pomocnicze import _gra, _kandydat, _lokal, _runda, _z

from silnik.boty import _podwyzki
from silnik.ludzie import zadowolenie as zo
from silnik.ludzie.kandydaci import cechy, pula_startowa

pytestmark = pytest.mark.dane_gry


def _start(**zatrudnienie):
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 3}}, B={**_lokal("dworzec_1")})
    k = _kandydat(s, 1)
    s = _runda(g, A={"zatrudnij": [{**_z(k, 1), **zatrudnienie}]})
    p = s.firmy["A"].pracownicy[k["id"]]
    p.cecha = ""   # bez cechy – liczby testu nie zależą od losowania
    return g, s, p


def _zawsze_odchodzi(monkeypatch, dane):
    """Każdy poniżej progu, a wypowiedzenie pewne (bez losowania i bez wpływu cechy)."""
    monkeypatch.setitem(dane.z["pracownicy"]["odejscia"], "prog_zadowolenia", 2.0)
    monkeypatch.setattr(zo, "szansa", lambda *a: 1.0)


def test_kandydaci_maja_ceche_i_opis_z_niej():
    g = _gra(("A", None), ("B", None))
    lista = cechy(g.dane)
    pula = g.stan_poczatkowy().kandydaci
    assert all(k["cecha"] in lista and k["opis"] in lista[k["cecha"]]["opisy"] for k in pula)
    assert len({k["cecha"] for k in pula}) > 3
    assert pula_startowa(g.dane, 1) == pula_startowa(g.dane, 1)


def test_cecha_nie_trafia_do_panelu_gracza():
    v = {"stan": {"pracownicy": {"p1": {"opis": "Narzeka na pogodę.", "cecha": "maruda", "wydajnosc": 1.0}}},
         "kandydaci": [{"id": "k", "cecha": "szybki", "opis": "…"}]}
    assert zo.ukryj(v) == {"stan": {"pracownicy": {"p1": {"opis": "Narzeka na pogodę."}}},
                           "kandydaci": [{"id": "k", "opis": "…"}]}


def test_zatrudniony_przejmuje_ceche_kandydata():
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 3}}, B={**_lokal("dworzec_1")})
    k = _kandydat(s, 1)
    s = _runda(g, A={"zatrudnij": [_z(k, 1)]})
    p = s.firmy["A"].pracownicy[k["id"]]
    assert (p.cecha, p.opis) == (k["cecha"], k["opis"]) and p.zadowolenie is not None


def test_wolniejszy_kucharz_ma_mniej_godzin():
    g, s, p = _start()
    st = s.firmy["A"].stanowisko("kuchnia", 1)
    p.wydajnosc = 0.9
    assert s.firmy["A"].godziny_stanowiska(st, 40) == pytest.approx(36)


def test_najpierw_ostrzezenie_potem_wypowiedzenie(monkeypatch):
    g, s, p = _start()
    _zawsze_odchodzi(monkeypatch, g.dane)
    s = _runda(g)
    p = s.firmy["A"].pracownicy[p.id]
    assert p.niezadowolony == 1 and p.odchodzi is None   # pierwszy tydzień – tylko ostrzeżenie
    r = s.runda + 1
    assert any("może złożyć wypowiedzenie" in t for _, t in zo.ostrzezenia(g.dane, s.firmy["A"], {}, r))
    s = _runda(g)
    p = s.firmy["A"].pracownicy[p.id]
    assert p.odchodzi and p.odchodzi.powod == zo.NIEZADOWOLENIE and p.odchodzi.do == ""
    assert p.odchodzi.runda == r + 1 + 2   # umowa o pracę: okres wypowiedzenia 2 tygodnie
    assert s.wyniki[r]["A"]["odejscia_pracownikow"][0]["pracownik"] == p.id
    assert any("składa wypowiedzenie" in t for _, t in zo.ostrzezenia(g.dane, s.firmy["A"], {}, r + 1))


def test_zleceniobiorca_odchodzi_od_razu_i_wraca_do_puli_z_cecha(monkeypatch):
    g, s, p = _start(umowa="zlecenie")
    _zawsze_odchodzi(monkeypatch, g.dane)
    _runda(g)
    s = _runda(g)
    assert s.firmy["A"].pracownicy[p.id].odchodzi.runda == s.runda + 1
    s = _runda(g)
    assert p.id not in s.firmy["A"].pracownicy
    wrocil = next(k for k in s.kandydaci if k["id"] == p.id)
    assert wrocil["opis"] == p.opis


def test_podwyzka_w_projekcie_usuwa_ostrzezenie():
    g, s, p = _start()
    f = s.firmy["A"]
    p.zadowolenie, p.niezadowolony, p.wykorzystanie = 0.85, 1, 0.5
    p.pensja = p.pensja_preferowana
    [(poziom, tekst)] = zo.ostrzezenia(g.dane, f, {}, s.runda + 1)
    assert poziom == "pomaranczowy" and "szansa ok. 10%" in tekst and "0,85" in tekst
    assert zo.ostrzezenia(g.dane, f, {p.id: {"pensja": p.pensja * 1.2}}, s.runda + 1) == []


def test_szansa_rosnie_z_niezadowoleniem_i_zalezy_od_cechy():
    g, s, p = _start()
    prog = zo.ustawienia(g.dane)["prog_zadowolenia"]
    assert zo.szansa(g.dane, p, prog) == 0
    assert zo.szansa(g.dane, p, prog - 0.02) < zo.szansa(g.dane, p, prog - 0.05)
    p.cecha = "lojalny"
    assert zo.szansa(g.dane, p, prog - 0.05) < 0.25 * 0.5


def test_bot_daje_podwyzke_niezadowolonemu():
    g, s, p = _start()
    ust = g.dane.boty["poziomy"]["sredni"]["dba_o_ludzi"]
    p.zadowolenie, p.niezadowolony = 0.85, 1
    stara = p.pensja
    nowa = _podwyzki(g.dane, s.firmy["A"], ust)[p.id]["pensja"]
    assert stara < nowa <= p.pensja_preferowana * ust["podwyzka_maks"]
    assert "dba_o_ludzi" not in g.dane.boty["poziomy"]["latwy"]
