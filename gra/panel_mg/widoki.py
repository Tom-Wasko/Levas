"""Panel mistrza gry (podstawowy, bez logowania – tryb deweloperski): nowe gry, prowadzenie rund."""

from django.http import Http404
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from gry import serwisy
from gry.models import Gra
from silnik.dane import dane_domyslne


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


@ensure_csrf_cookie
def gra(request, id_):
    try:
        g = serwisy.wczytaj(id_)
    except Gra.DoesNotExist:
        raise Http404("Nie ma takiej gry.") from None
    return render(request, "panel_mg/gra.html", {"id": id_, "nazwa": g.konfiguracja["nazwa"]})
