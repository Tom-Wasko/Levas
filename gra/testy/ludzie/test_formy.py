"""UF21+UF10: formy zatrudnienia (pół etatu, zlecenie bez ZUS, student, staż, B2B) i opcja MG z listą form."""

import pytest
from pomocnicze import _gra, _kandydat, _lokal, _rachunek, _runda, _z

from silnik.dane import KUCHNIA
from silnik.ksiegowosc import biuro as bo
from silnik.ksiegowosc import rozliczenie as rz
from silnik.ludzie import formy as fz
from silnik.ludzie import zadowolenie as zo
from silnik.ludzie.kandydaci import pula_startowa

pytestmark = pytest.mark.dane_gry


def _start(k_wybor=None, **zatrudnienie):
    g = _gra(("A", None), ("B", None))
    s = _runda(g, A={**_lokal("centrum_3"), "stanowiska": {"kuchnia": 3}}, B={**_lokal("dworzec_1")})
    k = k_wybor(s) if k_wybor else _kandydat(s, 1)
    s = _runda(g, A={"zatrudnij": [{**_z(k, 1), **zatrudnienie}]})
    return g, s, s.firmy["A"].pracownicy.get(k["id"]), k


def test_parametry_form_i_studenta():
    g = _gra(("A", None), ("B", None))
    d = g.dane
    assert set(fz.formy(d)) == {"prace", "pol_etatu", "zlecenie", "student", "staz", "b2b"}
    assert fz.stawka_zus(d, "prace") == fz.stawka_zus(d, "pol_etatu") == rz.zus_pracodawcy(d) > 0.2
    assert fz.stawka_zus(d, "zlecenie") == fz.stawka_zus(d, "b2b") == fz.stawka_zus(d, "staz") == 0.0   # UF10
    placa = d.z["finanse"]["placa_minimalna"]
    assert fz.placa_minimalna(d, "pol_etatu") == placa / 2 and fz.placa_minimalna(d, "b2b") == 0
    st = fz.studenci(d)
    assert fz.placa_minimalna(d, "zlecenie", student=True) == pytest.approx(placa * st["godziny"])
    assert fz.porownawcza(d, 5000, "b2b") == pytest.approx(4000) and fz.porownawcza(d, 2500, "pol_etatu") == 5000
    k = {"gwiazdki": 2, "student": False}
    assert "studentów" in fz.blad(d, k, "student") and "1★" in fz.blad(d, k, "staz")
    assert fz.blad(d, {**k, "gwiazdki": 1}, "staz") is None and fz.blad(d, k, "b2b") is None
    assert fz.blad(d, k, "etat_na_niby") is not None


def test_studenci_z_osobnego_strumienia(monkeypatch):
    g = _gra(("A", None), ("B", None))
    d = g.dane
    pula = pula_startowa(d, 3)
    studenci = [k for k in pula if k.get("student")]
    assert studenci and all(k["wiek"] < fz.studenci(d)["wiek_do"] for k in studenci)
    monkeypatch.setitem(d.z["pracownicy"], "studenci", None)
    bez = pula_startowa(d, 3)
    assert [{x: v for x, v in k.items() if x != "student"} for k in pula] == bez   # reszta losowania bez zmian


def test_pol_etatu_polowa_godzin_i_oczekiwanej_pensji():
    g, s, p, _ = _start(umowa="pol_etatu", pensja=None)
    d, f = g.dane, s.firmy["A"]
    st = f.stanowisko(KUCHNIA, 1)
    godz = d.z["operacje"]["godziny_pracownika"]
    assert f.godziny_stanowiska(st, godz, d) == pytest.approx(godz * p.wydajnosc / 2)
    p.pensja = p.pensja_preferowana / 2
    assert zo.placa_wzgledna(d, p) == pytest.approx(1.0)
    assert bo._umowy(d, f) == (1, 0)


def test_b2b_faktura_z_vat_bez_zus_i_bez_wypowiedzenia():
    g, s, p, _ = _start(umowa="b2b", pensja=6500)
    s = _runda(g)
    d = g.dane
    faktura = -sum(_rachunek(s, 3, "A", "Faktura B2B: "))
    assert faktura == pytest.approx(d.na_runde(6500) * 1.23, abs=0.02)
    assert sum(_rachunek(s, 3, "A", "Wynagrodzenia pracowników")) == 0
    assert sum(_rachunek(s, 3, "A", "Składki ZUS pracodawcy")) == 0
    from silnik.ludzie.rynek_pracy import okres_wypowiedzenia
    assert okres_wypowiedzenia(d, s.firmy["A"].pracownicy[p.id], 3) == 0
    assert bo._umowy(d, s.firmy["A"]) == (0, 0)


def test_staz_bez_pensji_tylko_1_gwiazdka_potem_umowa_o_prace():
    g, s, p, k = _start(umowa="staz", pensja=4000)
    d = g.dane
    assert p.umowa == "staz" and p.pensja == 0
    assert zo.placa_wzgledna(d, p) == pytest.approx(1.0)
    rund = fz.formy(d)["staz"]["staz"]["rund"]
    f = s.firmy["A"]
    assert fz.koniec_stazu(d, f, p.od_rundy + rund - 1) == []
    (x,) = fz.koniec_stazu(d, f, p.od_rundy + rund)
    assert p.umowa == "prace" and p.pensja == max(p.pensja_preferowana, d.z["finanse"]["placa_minimalna"]) == x["pensja"]
    # osoba z doświadczeniem nie pójdzie na staż – zatrudnienie nieudane, czerwony błąd
    g, s, p, k = _start(lambda s: _kandydat(s, 2), umowa="staz")
    assert p is None
    assert any("staż" in b["tekst"] and b["poziom"] == "czerwony" for b in s.wyniki[2]["A"]["lista_bledow"])


def test_student_mniej_godzin_nizsza_oczekiwana_czesciej_odchodzi():
    g, s, p, k = _start(lambda s: next(x for x in s.kandydaci if x.get("student") and x["zawod"] == "Kasjer"),
                        typ="kasa", umowa="student", pensja=None)
    if p is None:   # kasjer bez stanowiska kasy w tym ustawieniu – sprawdź na kopii osoby
        pytest.skip("brak stanowiska kasy")
    d = g.dane
    st = fz.studenci(d)
    assert p.student and fz.etat(d, p) == st["godziny"] and fz.mnoznik_odejsc(d, p) == st["odejscia"]
    assert fz.oczekiwana(d, p) == pytest.approx(p.pensja_preferowana * st["pensja"])
    assert fz.stawka_zus(d, p.umowa, p.student) == 0
    skl = zo.skladniki(d, s.firmy["A"], p, 0.5, 0.0)
    assert skl["umowa"] < 0   # to dalej zlecenie
    u = zo.ustawienia(d)
    p2 = p.model_copy(update={"student": False})
    assert zo.szansa(d, p, u["prog_zadowolenia"] - 0.05) > zo.szansa(d, p2, u["prog_zadowolenia"] - 0.05)


def test_zmiana_formy_w_profilu():
    g, s, p, _ = _start()
    s = _runda(g, A={"zmiany": {p.id: {"pensja": p.pensja, "umowa": "student"}}})   # nie student – bez zmiany
    q = s.firmy["A"].pracownicy[p.id]
    assert q.umowa == "prace"
    s = _runda(g, A={"zmiany": {p.id: {"pensja": p.pensja, "umowa": "staz"}}})      # na staż tylko nowi
    assert s.firmy["A"].pracownicy[p.id].umowa == "prace"
    s = _runda(g, A={"zmiany": {p.id: {"pensja": 7000, "umowa": "b2b"}}})
    assert s.firmy["A"].pracownicy[p.id].umowa == "b2b"


def test_opcja_mg_wylacza_formy():
    g = _gra(("A", None), ("B", None))
    d = g.dane
    assert fz.dozwolone(d, {}) == list(fz.formy(d))
    konf = {"formy_zatrudnienia": ["zlecenie"]}
    assert fz.dozwolone(d, konf) == ["prace", "zlecenie"]
    dec = {"zatrudnij": [{"kandydat": "x", "umowa": "b2b"}, {"kandydat": "y", "umowa": "zlecenie"}],
           "zmiany": {"p": {"umowa": "pol_etatu"}, "q": {"pensja": 5000}}}
    w = fz.przytnij(d, dec, konf)
    assert [z["umowa"] for z in w["zatrudnij"]] == ["prace", "zlecenie"]
    assert w["zmiany"] == {"p": {"umowa": "prace"}, "q": {"pensja": 5000}}
    assert fz.przytnij(d, dec, {}) is dec
