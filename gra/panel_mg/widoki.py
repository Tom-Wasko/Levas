"""Panel mistrza gry (tylko rola mistrza gry): nowe gry, prowadzenie rund."""

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from gry import serwisy
from gry.models import Gra
from konta.role import jest_mg
from silnik.dane import dane_domyslne


def wymaga_mg(widok):
    @wraps(widok)
    def opakowanie(request, *args, **kwargs):
        if not jest_mg(request.user):
            raise PermissionDenied("Panel mistrza gry jest tylko dla mistrza gry.")
        return widok(request, *args, **kwargs)

    return opakowanie


@wymaga_mg
@ensure_csrf_cookie
def lista(request):
    dane = dane_domyslne()
    ustawienia = {
        "strategie": {k: v["nazwa"] for k, v in dane.boty["strategie"].items()},
        "rundy": dane.katalog_ofert["rundy"]["domyslna_liczba"],
        "maks_rund": dane.rund_w_roku,
        "kapital": dane.z["finanse"]["kapital_startowy"],
        "pierwsza": dane.nazwa_rundy(1),
        "mnoga": dane.okres["mnoga"],
    }
    return render(request, "panel_mg/lista.html", {"ustawienia": ustawienia})


@wymaga_mg
@ensure_csrf_cookie
def gra(request, id_):
    try:
        g = serwisy.wczytaj(id_)
    except Gra.DoesNotExist:
        raise Http404("Nie ma takiej gry.") from None
    return render(request, "panel_mg/gra.html", {"id": id_, "nazwa": g.konfiguracja["nazwa"]})
