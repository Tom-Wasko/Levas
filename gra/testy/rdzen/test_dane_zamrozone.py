"""Zamrożona kopia danych dla testów mechanik (B2): testy bez znacznika czytają `testy/dane_zamrozone/`,
testy zasad ze znacznikiem `dane_gry` – `dane/` (testy/conftest.py)."""

import pytest
from pomocnicze import DANE_GRY, DANE_ZAMROZONE

from silnik.dane import dane_domyslne, sprawdz


def test_testy_mechanik_czytaja_zamrozona_kopie():
    assert dane_domyslne().katalog == DANE_ZAMROZONE


@pytest.mark.dane_gry
def test_testy_zasad_czytaja_dane_gry():
    assert dane_domyslne().katalog == DANE_GRY


def test_zamrozona_kopia_pasuje_do_schematow():
    # nowy klucz w schemacie danych – dopisać go też w kopii (bez zmiany jej liczb)
    assert sprawdz(DANE_ZAMROZONE) == []


def test_zamrozona_kopia_ma_wszystkie_pliki_danych():
    pliki = {p.relative_to(DANE_GRY) for p in DANE_GRY.rglob("*.yaml")}
    assert pliki <= {p.relative_to(DANE_ZAMROZONE) for p in DANE_ZAMROZONE.rglob("*.yaml")}
