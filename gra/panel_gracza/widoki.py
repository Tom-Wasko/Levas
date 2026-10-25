"""Strony gracza: lista gier, wybór firmy, strona z zakładkami."""

from urllib.parse import quote

from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie

from gry import serwisy
from gry.models import Gra
from silnik.dane import dane_domyslne


def _gra(id_: str):
    try:
        return serwisy.wczytaj(id_)
    except Gra.DoesNotExist:
        raise Http404("Nie ma takiej gry.") from None


@ensure_csrf_cookie
def start(request):
    strategie = {k: v["nazwa"] for k, v in dane_domyslne().boty["strategie"].items()}
    return render(request, "panel_gracza/start.html", {"strategie": strategie})


@ensure_csrf_cookie
def wybor_firmy(request, id_):
    g = _gra(id_)
    ludzie = [f["nazwa"] for f in g.konfiguracja["firmy"] if not f["bot"]]
    if len(ludzie) == 1:
        return redirect(f"/gra/{quote(id_)}/{quote(ludzie[0], safe='')}")
    kontekst = {"id": id_, "gra": g.konfiguracja, "ludzie": ludzie}
    return render(request, "panel_gracza/wybor.html", kontekst)


@ensure_csrf_cookie
def strona_gry(request, id_, firma):
    g = _gra(id_)
    if firma not in {f["nazwa"] for f in g.konfiguracja["firmy"]}:
        raise Http404("Nie ma takiej firmy.")
    return render(request, "panel_gracza/gra.html", {"id": id_, "firma": firma})
