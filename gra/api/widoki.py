"""Widoki JSON dla zakładek (odpowiednik `serwer/app.py` z Revasa)."""

from __future__ import annotations

import json
from copy import deepcopy
from functools import wraps

from django.http import HttpResponse, JsonResponse
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from gry import serwisy
from gry.models import Gra
from silnik.boty import decyzje_bota
from silnik.dane import dane_domyslne
from silnik.gra import Gra as GraSilnika
from silnik.runda import przelicz_runde

from .prezentacja import katalogi, widok


def odpowiedz(dane, status: int = 200) -> JsonResponse:
    return JsonResponse(dane, status=status, safe=False, json_dumps_params={"ensure_ascii": False})


def blad(tekst: str, kod: int = 400) -> JsonResponse:
    return odpowiedz({"blad": tekst}, kod)


class BladZapytania(Exception):
    def __init__(self, tekst: str, kod: int = 400):
        super().__init__(tekst)
        self.kod = kod


def api(widok_):
    """Błędy zapytania jako JSON {"blad": ...}, tak jak oczekuje `api()` w app.js."""

    @wraps(widok_)
    def opakowanie(request, *args, **kwargs):
        try:
            return widok_(request, *args, **kwargs)
        except Gra.DoesNotExist:
            return blad("Nie ma takiej gry.", 404)
        except BladZapytania as e:
            return blad(str(e), e.kod)
        except ValueError as e:  # reguły silnika, np. „Brak decyzji: …”
            return blad(str(e))

    return opakowanie


def cialo(request, wymagane: bool = True) -> dict:
    try:
        d = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        if wymagane:
            raise BladZapytania("Niepoprawny JSON.") from None
        d = {}
    if not isinstance(d, dict):
        raise BladZapytania("Oczekiwano obiektu JSON.")
    return d


def sprawdz_firme(g: GraSilnika, firma: str) -> None:
    if firma not in {f["nazwa"] for f in g.konfiguracja["firmy"]}:
        raise BladZapytania("Nie ma takiej firmy w grze.", 404)


def _warianty(g: GraSilnika, firma: str) -> dict:
    return g.decyzje.setdefault(g.runda, {}).setdefault("_warianty", {}).setdefault(firma, {})


@require_GET
@api
def api_katalogi(request):
    return odpowiedz(katalogi(dane_domyslne()))


@require_http_methods(["GET", "POST"])
@api
def api_gry(request):
    if request.method == "GET":
        return odpowiedz(serwisy.lista())
    d = cialo(request)
    wiersze = [f for f in d.get("firmy", []) if str(f.get("nazwa", "")).strip()]
    firmy = [(f["nazwa"].strip(), f.get("bot") or None) for f in wiersze]
    if not firmy or len({n for n, _ in firmy}) != len(firmy):
        return blad("Podaj różne nazwy firm.")
    if any(n.startswith("_") for n, _ in firmy):
        return blad("Nazwa firmy nie może zaczynać się od podkreślenia.")
    if not any(b is None for _, b in firmy):
        return blad("Co najmniej jedna firma musi być prowadzona przez gracza.")
    ziarno = d.get("ziarno")
    g = GraSilnika.nowa(
        d.get("nazwa") or "Gra",
        firmy,
        int(d["liczba_rund"]) if d.get("liczba_rund") else None,  # brak – domyślna z danych
        int(ziarno) if str(ziarno or "").strip().isdigit() else None,
        ceny_dostawcow=d.get("ceny_dostawcow", "dane"),
        kredyt_odnawialny=d.get("kredyt_odnawialny", "jednoczesnie"),
    )
    return odpowiedz({"id": serwisy.utworz(g)})


@require_http_methods(["DELETE"])
@api
def api_usun(request, id_):
    serwisy.usun(id_)
    return odpowiedz({"ok": True})


@require_GET
@api
def api_widok(request, id_, firma):
    g = serwisy.wczytaj(id_)
    sprawdz_firme(g, firma)
    runda = request.GET.get("runda", "")
    return odpowiedz(widok(g, firma, int(runda) if runda.isdigit() else None))


@require_http_methods(["PUT"])
@api
def api_decyzje(request, id_, firma):
    d = cialo(request)
    with serwisy.zmiana(id_) as g:
        sprawdz_firme(g, firma)
        if g.zakonczona:
            raise BladZapytania("Gra jest zakończona.")
        if firma in g.wyslane():
            raise BladZapytania("Decyzje są wysłane – najpierw wróć do podejmowania decyzji.")
        g.ustaw_decyzje(firma, d)
    return odpowiedz(widok(g, firma))


@require_POST
@api
def api_wyslij(request, id_, firma):
    wyslane = bool(cialo(request, wymagane=False).get("wyslane", True))
    przeliczono = False
    with serwisy.zmiana(id_) as g:
        sprawdz_firme(g, firma)
        g.wyslij(firma, wyslane)
        if wyslane and not g.brakujace() and not g.zakonczona:
            g.przelicz()
            przeliczono = True
    v = widok(g, firma)
    v["przeliczono"] = przeliczono
    return odpowiedz(v)


@require_POST
@api
def api_przelicz(request, id_):
    with serwisy.zmiana(id_) as g:
        if g.zakonczona:
            raise BladZapytania("Gra jest zakończona.")
        g.przelicz(wymus=True)
    return odpowiedz({"ok": True, "runda": g.runda})


@require_POST
@api
def api_cofnij(request, id_):
    with serwisy.zmiana(id_) as g:
        g.cofnij()
    return odpowiedz({"ok": True, "runda": g.runda})


@require_http_methods(["PUT", "DELETE"])
@api
def api_warianty(request, id_, firma):
    """PUT: zapisuje robocze decyzje (albo podane) jako nazwany wariant do porównania w Analizie.
    DELETE ?nazwa=…: usuwa wariant."""
    if request.method == "PUT":
        d = cialo(request)
        nazwa = str(d.get("nazwa") or "").strip()[:40]
        if not nazwa:
            return blad("Podaj nazwę wariantu.")
    with serwisy.zmiana(id_) as g:
        sprawdz_firme(g, firma)
        if request.method == "PUT":
            _warianty(g, firma)[nazwa] = d.get("decyzje") or deepcopy(g.szkic(firma))
        else:
            _warianty(g, firma).pop(request.GET.get("nazwa", ""), None)
    return odpowiedz(widok(g, firma))


@require_GET
@api
def api_dane_wariantu(request, id_, firma):
    g = serwisy.wczytaj(id_)
    sprawdz_firme(g, firma)
    zapisane = g.decyzje.get(g.runda, {}).get("_warianty", {}).get(firma, {})
    w = zapisane.get(request.GET.get("nazwa", ""))
    return odpowiedz(w) if w is not None else blad("Nie ma takiego wariantu.", 404)


@require_POST
@api
def api_podglad(request, id_, firma):
    """Przewidywany wynik bieżącej rundy dla decyzji (bez zapisu). Boty decydują jak zwykle,
    pozostali gracze – według swoich roboczych decyzji.
    Body: {"warianty": [nazwa wariantu albo "biezace"]} – domyślnie bieżące."""
    g = serwisy.wczytaj(id_)
    sprawdz_firme(g, firma)
    if g.zakonczona:
        return blad("Gra jest zakończona.")
    kopia = g.kopia()
    nazwy = cialo(request, wymagane=False).get("warianty") or ["biezace"]
    zapisane = _warianty(kopia, firma)
    nazwy = [n for n in nazwy if n == "biezace" or n in zapisane]
    stan = kopia.stan(kopia.runda - 1)
    r = kopia.runda
    baza = {
        f["nazwa"]: (
            decyzje_bota(kopia.dane, stan, f["nazwa"], f["bot"], r, kopia.konfiguracja)
            if f["bot"]
            else kopia.szkic(f["nazwa"])
        )
        for f in kopia.konfiguracja["firmy"]
    }
    wyniki = []
    for nazwa in nazwy:
        dec = deepcopy(baza)
        dec[firma] = g.szkic(firma) if nazwa == "biezace" else zapisane[nazwa]
        s = przelicz_runde(kopia.dane, stan, dec, kopia.konfiguracja)
        wyniki.append(
            {
                "nazwa": "Bieżące decyzje" if nazwa == "biezace" else nazwa,
                "wyniki": s.wyniki[r][firma],
                "rynek": s.rynek[r],
            }
        )
    return odpowiedz({"runda": r, "warianty": wyniki})


@require_GET
@api
def api_eksport(request, id_):
    g = serwisy.wczytaj(id_)
    tresc = json.dumps(g.do_slownika(), ensure_ascii=False, indent=1)
    r = HttpResponse(tresc, content_type="application/json; charset=utf-8")
    r["Content-Disposition"] = content_disposition_header(True, f"{id_}.json")
    return r


@require_POST
@api
def api_import(request):
    plik = request.FILES.get("plik")
    if not plik:
        return blad("Brak pliku.")
    try:
        d = json.loads(plik.read().decode("utf-8"))
        g = GraSilnika(d["konfiguracja"], d.get("decyzje"))
        if not g.konfiguracja["nazwa"] or not g.konfiguracja["firmy"]:
            raise KeyError("konfiguracja")
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError, UnicodeDecodeError):
        return blad("To nie jest plik gry.")
    return odpowiedz({"id": serwisy.utworz(g)})
