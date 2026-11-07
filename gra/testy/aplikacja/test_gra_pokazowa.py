"""UF17: `manage.py gra_pokazowa` – nowa gra „Pokazowa” rozegrana do końca, widoczna dla mistrza gry w „Twoich grach”."""

import pytest
from django.core.management import call_command

from gry import serwisy
from gry.models import Druzyna, Gra
from konta.role import gry_ucznia

pytestmark = pytest.mark.django_db


def test_gra_pokazowa_od_nowa_rozegrana_do_konca(mistrz, django_user_model):
    uczen = django_user_model.objects.create_user("ala", password="haslo-uczen")
    for _ in range(2):   # drugie wywołanie usuwa starą grę
        call_command("gra_pokazowa", "--rund", "3", "--ziarno", "7")
    gry = list(Gra.objects.filter(nazwa="Pokazowa"))
    assert len(gry) == 1
    g = serwisy.wczytaj(gry[0].pk)
    assert g.zakonczona and g.runda == 4
    firmy = {f["nazwa"]: f for f in g.konfiguracja["firmy"]}
    assert firmy["Pokazowa"]["bot"] is None and sum(1 for f in firmy.values() if f["bot"]) == 4
    for r in range(1, 4):   # drużyna „Pokazowa” ma w każdej rundzie wysłane decyzje bota
        d = g.decyzje[r]
        assert "Pokazowa" in d["_wyslane"] and d["Pokazowa"].get("zatrudnij") is not None
    druzyna = Druzyna.objects.get(gra=gry[0], firma="Pokazowa")
    assert list(druzyna.czlonkowie.all()) == [mistrz]
    assert gry[0].pk in gry_ucznia(mistrz) and not gry_ucznia(uczen)


def test_gra_pokazowa_wybrane_konto(django_user_model):
    django_user_model.objects.create_user("autor", password="x")
    call_command("gra_pokazowa", "--rund", "2", "--ziarno", "3", "--konto", "autor")
    druzyna = Druzyna.objects.get(gra__nazwa="Pokazowa")
    assert [u.username for u in druzyna.czlonkowie.all()] == ["autor"]
    with pytest.raises(Exception, match="Nie ma kont"):
        call_command("gra_pokazowa", "--rund", "2", "--konto", "nikt")
