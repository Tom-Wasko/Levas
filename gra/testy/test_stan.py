"""Stan gry (pydantic, kwoty w groszach): testy własności zapisu i powtarzalności."""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from silnik import Gra
from silnik.dane import dane_domyslne
from silnik.model import (
    WERSJA_STANU,
    Cena,
    Firma,
    Kredyt,
    Pracownik,
    StanGry,
    do_slownika,
    firma_z_slownika,
    grosze,
    zlote,
)

KWOTY = st.integers(min_value=-(10**12), max_value=10**12)
NAZWY = st.text(alphabet="abcąćęłńóśźż|123 ", min_size=1, max_size=12)

pracownicy = st.builds(
    Pracownik,
    id=NAZWY,
    imie_nazwisko=NAZWY,
    zawod=st.sampled_from(["Instruktor", "Recepcjonista"]),
    gwiazdki=st.integers(1, 3),
    pensja_preferowana_gr=KWOTY,
    koszt_rekrutacji_gr=KWOTY,
    koszt_odprawy_gr=KWOTY,
    zadowolenie_klientow=st.floats(0, 2),
    ryzyko_reklamacji=st.floats(0, 1),
    pensja_gr=KWOTY,
    premia_gr=KWOTY,
)
firmy = st.builds(
    Firma,
    nazwa=NAZWY,
    gotowka_gr=KWOTY,
    pracownicy=st.dictionaries(NAZWY, pracownicy, max_size=3),
    magazyn=st.dictionaries(NAZWY, st.floats(0, 1000), max_size=3),
    wartosc_magazynu_gr=st.dictionaries(NAZWY, KWOTY, max_size=3),
    ceny=st.dictionaries(NAZWY, st.builds(Cena, cena_gr=KWOTY, rabat_gr=KWOTY), max_size=3),
    kredyty=st.lists(
        st.builds(
            Kredyt,
            id=st.integers(0, 99),
            kwota_gr=KWOTY,
            oprocentowanie=st.floats(0, 0.2),
            od_rundy=st.integers(1, 26),
            miesiecy=st.integers(1, 26),
            pozostalo_gr=KWOTY,
        ),
        max_size=2,
    ),
    kredyt_odnawialny_gr=KWOTY,
    majatek_gr=KWOTY,
    skumulowany_dochod_netto_gr=KWOTY,
)


@given(KWOTY)
def test_grosze_zlote_grosze(g):
    assert grosze(zlote(g)) == g


def test_zaokraglanie_do_grosza():
    assert grosze(0.005) == 1 and grosze(-0.005) == -1 and grosze(1234.564) == 123456
    f = Firma(nazwa="X", gotowka=100.0)
    f.gotowka += 0.1 + 0.2  # 100,30 zł, a nie 100,30000000000001
    assert f.gotowka_gr == 10030 and f.gotowka == 100.3


@given(firmy)
def test_zapis_i_odczyt_daje_ten_sam_stan(f):
    assert Firma.model_validate_json(f.model_dump_json()) == f  # zapis w groszach
    assert firma_z_slownika(do_slownika(f)) == f  # widok w złotych dla zakładek


def test_nieznane_pole_i_wersja_stanu():
    with pytest.raises(ValidationError):
        Firma(nazwa="X", gotowka_zl=5)
    with pytest.raises(ValidationError, match="wersji"):
        StanGry(runda=0, firmy={}, kandydaci=[], wersja=WERSJA_STANU + 1)


def _gra(ziarno: int, boty: list[str], rundy: int) -> Gra:
    g = Gra.nowa("Test", [(f"F{i}", b) for i, b in enumerate(boty)], rundy, ziarno)
    for _ in range(rundy):
        g.przelicz()
    return g


@settings(max_examples=6, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    ziarno=st.integers(0, 10**9),
    boty=st.lists(st.sampled_from(sorted(dane_domyslne().boty["strategie"])), min_size=1, max_size=4),
)
def test_to_samo_ziarno_i_decyzje_daja_ten_sam_wynik(ziarno, boty):
    a, b = _gra(ziarno, boty, 3), _gra(ziarno, boty, 3)
    sa = a.stan()
    assert sa.model_dump_json() == b.stan().model_dump_json()
    # zapis stanu po grze i odczyt
    assert (
        StanGry.model_validate_json(sa.model_dump_json()).model_dump_json() == sa.model_dump_json()
    )
    # event sourcing: same decyzje (zapis gry) odtwarzają ten sam stan
    c = Gra(a.do_slownika()["konfiguracja"], a.do_slownika()["decyzje"])
    assert c.stan().model_dump_json() == sa.model_dump_json()
