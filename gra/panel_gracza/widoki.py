"""Strony gracza: lista gier, wybór firmy, strona z zakładkami."""

from urllib.parse import quote

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie

from gry import serwisy
from gry.models import Gra
from konta.role import firmy_ucznia, jest_mg, moze_firme
from silnik.dane import dane_domyslne


def _gra(id_: str):
    try:
        return serwisy.wczytaj(id_)
    except Gra.DoesNotExist:
        raise Http404("Nie ma takiej gry.") from None


@ensure_csrf_cookie
def start(request):
    dane = dane_domyslne()
    strategie = {k: v["nazwa"] for k, v in dane.boty["strategie"].items()}
    kalendarz = {
        "pierwsza": dane.nazwa_rundy(1),
        "okres": dane.okres["mianownik"],
        "mnoga": dane.okres["mnoga"],
        "domyslna": dane.katalog_ofert["rundy"]["domyslna_liczba"],
        "maks": dane.rund_w_roku,
    }
    kapital = f"{dane.z['finanse']['kapital_startowy']:,.0f}".replace(",", "\u00a0")
    kontekst = {"strategie": strategie, "kalendarz": kalendarz, "kapital": kapital}
    kontekst["mg"] = jest_mg(request.user)  # uczeń widzi tylko gry swoich drużyn, bez zakładania
    return render(request, "panel_gracza/start.html", kontekst)


@ensure_csrf_cookie
def wybor_firmy(request, id_):
    g = _gra(id_)
    ludzie = [f["nazwa"] for f in g.konfiguracja["firmy"] if not f["bot"]]
    if not jest_mg(request.user):
        moje = firmy_ucznia(request.user, id_)
        ludzie = [f for f in ludzie if f in moje]
        if not ludzie:
            raise PermissionDenied("Nie należysz do żadnej drużyny w tej grze.")
    if len(ludzie) == 1:
        return redirect(f"/gra/{quote(id_)}/{quote(ludzie[0], safe='')}")
    kontekst = {"id": id_, "gra": g.konfiguracja, "ludzie": ludzie}
    return render(request, "panel_gracza/wybor.html", kontekst)


@ensure_csrf_cookie
def strona_gry(request, id_, firma):
    g = _gra(id_)
    if firma not in {f["nazwa"] for f in g.konfiguracja["firmy"]}:
        raise Http404("Nie ma takiej firmy.")
    if not moze_firme(request.user, id_, firma):
        raise PermissionDenied("To nie jest firma Twojej drużyny.")
    kontekst = {"id": id_, "firma": firma, "mg": jest_mg(request.user)}
    return render(request, "panel_gracza/gra.html", kontekst)
