"""Wspólne fixtury: `client` jest zalogowany jako mistrz gry (pełny dostęp), `uczen` – konta uczniów."""

import pytest
from django.test import Client

from konta.role import nadaj_mg


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
