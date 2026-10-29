"""Wspólne fixtury: `client` jest zalogowany jako mistrz gry (pełny dostęp), `uczen` – konta uczniów.

Dane gry: testy mechanik (wzory, scenariusze co do grosza) czytają zamrożoną kopię `testy/dane_zamrozone/`,
więc kalibracja liczb w `dane/` ich nie łamie. Testy zasad (determinizm, schematy, brak liczb w kodzie,
uzgodnienie kasy, boty) mają znacznik `dane_gry` i czytają `dane/`.
"""

import pytest
from django.test import Client
from pomocnicze import DANE_GRY, DANE_ZAMROZONE

from konta.role import nadaj_mg
from silnik import dane as modul_danych

modul_danych.KATALOG_DANYCH = DANE_ZAMROZONE   # przed importem testów – `from silnik.dane import KATALOG_DANYCH`


def pytest_runtest_setup(item):
    modul_danych.KATALOG_DANYCH = DANE_GRY if item.get_closest_marker("dane_gry") else DANE_ZAMROZONE


@pytest.fixture
def mistrz(django_user_model):
    user = django_user_model.objects.create_user("mistrz", password="haslo-mg")
    nadaj_mg(user)
    return user


@pytest.fixture
def client(client, mistrz):
    client.force_login(mistrz)
    return client


@pytest.fixture
def uczen(django_user_model):
    """uczen("ala") → Client zalogowany jako uczeń o tym loginie."""

    def zrob(login: str) -> Client:
        c = Client()
        c.force_login(django_user_model.objects.create_user(login, password="haslo-uczen"))
        return c

    return zrob
