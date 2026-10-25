"""Widoki JSON dla zakładek (odpowiednik `serwer/app.py` z Revasa)."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from functools import wraps

from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from gry import serwisy
from gry.models import Gra
from konta import druzyny
from konta.role import gry_ucznia, jest_mg, moze_firme
from silnik.boty import decyzje_bota
from silnik.dane import dane_domyslne
from silnik.gra import Gra as GraSilnika
from silnik.runda import przelicz_runde

from .prezentacja import katalogi, przeglad_mg, widok

MAKS_KAPITAL = 10_000_000  # zł – górna granica kapitału startowego w nowej grze
MAKS_NOWYCH_KONT = 60  # kont uczniów naraz (lista klasy)


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


def tylko_mg(widok_):
    """Zarządzanie grą (nowa gra, zamknięcie i cofnięcie rundy, plik gry) – tylko mistrz gry."""

    @wraps(widok_)
    def opakowanie(request, *args, **kwargs):
        if not jest_mg(request.user):
            raise BladZapytania("Tylko mistrz gry może to zrobić.", 403)
        return widok_(request, *args, **kwargs)

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


def sprawdz_firme(request, id_: str, g: GraSilnika, firma: str) -> None:
    if firma not in {f["nazwa"] for f in g.konfiguracja["firmy"]}:
        raise BladZapytania("Nie ma takiej firmy w grze.", 404)
    if not moze_firme(request.user, id_, firma):
        raise BladZapytania("To nie jest firma Twojej drużyny.", 403)


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
        gry = serwisy.lista()
        if not jest_mg(request.user):
            moje = gry_ucznia(request.user)
            gry = [g for g in gry if g["id"] in moje]
        return odpowiedz(gry)
    if not jest_mg(request.user):
        return blad("Tylko mistrz gry zakłada gry.", 403)
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
    kapital = d.get("kapital_startowy")
    if kapital not in (None, ""):
        try:
            kapital = float(kapital)
        except (TypeError, ValueError):
            return blad("Kapitał startowy musi być liczbą.")
        if not 0 < kapital <= MAKS_KAPITAL:
            return blad(f"Kapitał startowy: od 1 do {MAKS_KAPITAL:,.0f} PLN.".replace(",", " "))
    else:
        kapital = None
    g = GraSilnika.nowa(
        d.get("nazwa") or "Gra",
        firmy,
        int(d["liczba_rund"]) if d.get("liczba_rund") else None,  # brak – domyślna z danych
        int(ziarno) if str(ziarno or "").strip().isdigit() else None,
        ceny_dostawcow=d.get("ceny_dostawcow", "dane"),
        kredyt_odnawialny=d.get("kredyt_odnawialny", "jednoczesnie"),
        kapital_startowy=kapital,
        lokale=d.get("lokale", True) not in (False, "nie", "0", 0),
    )
    return odpowiedz({"id": serwisy.utworz(g)})


@require_GET
@api
@tylko_mg
def api_mg(request, id_):
    """Widok mistrza gry: runda, decyzje drużyn, wyniki wszystkich firm."""
    g = serwisy.wczytaj(id_)
    p = przeglad_mg(g)
    sklad = druzyny.sklad(id_)
    for f in p["firmy"]:
        if not f["bot"]:
            f["sklad"] = sklad.get(f["nazwa"], [])
            f["autorzy"] = druzyny.autorzy(g, f["nazwa"])
    return odpowiedz(p)


def _sklad_gry(id_: str, g: GraSilnika) -> dict:
    sklad = druzyny.sklad(id_)
    return {
        "druzyny": [
            {"firma": f["nazwa"], "sklad": sklad.get(f["nazwa"], [])}
            for f in g.konfiguracja["firmy"]
            if not f["bot"]
        ],
        "uczniowie": druzyny.uczniowie(),
        "maks": druzyny.MAKS_CZLONKOW,
    }


@require_GET
@api
@tylko_mg
def api_druzyny(request, id_):
    """Skład drużyn gry i konta uczniów do dopisania."""
    return odpowiedz(_sklad_gry(id_, serwisy.wczytaj(id_)))


@require_POST
@api
@tylko_mg
def api_druzyna(request, id_, firma):
    """{"dodaj": login} albo {"usun": login} – zmiana składu drużyny."""
    g = serwisy.wczytaj(id_)
    if firma not in {f["nazwa"] for f in g.konfiguracja["firmy"] if not f["bot"]}:
        raise BladZapytania("Nie ma takiej drużyny w grze.", 404)
    d = cialo(request)
    try:
        if d.get("dodaj"):
            druzyny.dodaj(id_, firma, str(d["dodaj"]))
        elif d.get("usun"):
            druzyny.usun(id_, firma, str(d["usun"]))
        else:
            raise BladZapytania("Podaj login do dodania albo usunięcia.")
    except ValidationError as e:
        raise BladZapytania(" ".join(e.messages)) from e
    return odpowiedz(_sklad_gry(id_, g))


@require_POST
@api
@tylko_mg
def api_konta(request):
    """{"osoby": ["Imię Nazwisko", ...]} – konta uczniów z losowymi hasłami do przekazania."""
    osoby = [str(o).strip() for o in cialo(request).get("osoby", []) if str(o).strip()]
    if not osoby:
        raise BladZapytania("Wpisz imię i nazwisko co najmniej jednej osoby.")
    if len(osoby) > MAKS_NOWYCH_KONT:
        raise BladZapytania(f"Najwyżej {MAKS_NOWYCH_KONT} kont naraz.")
    konta = []
    for imie in osoby:
        try:
            user, haslo = druzyny.nowe_konto(druzyny.wolny_login(imie), imie)
        except ValidationError as e:
            raise BladZapytania(f"{imie}: {' '.join(e.messages)}") from e
        konta.append({**druzyny.osoba(user), "haslo": haslo})
    return odpowiedz({"konta": konta})


@require_POST
@api
@tylko_mg
def api_nowe_haslo(request, login):
    """Nowe losowe hasło ucznia (zapomniane hasło)."""
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.filter(username=login).first()
    if user is None:
        raise BladZapytania("Nie ma takiego konta.", 404)
    if jest_mg(user):
        raise BladZapytania("Hasło mistrza gry zmienia się w panelu Konta.", 403)
    haslo = druzyny.nowe_haslo()
    user.set_password(haslo)
    user.save(update_fields=["password"])
    return odpowiedz({**druzyny.osoba(user), "haslo": haslo})


@require_http_methods(["DELETE"])
@api
@tylko_mg
def api_usun(request, id_):
    serwisy.usun(id_)
    return odpowiedz({"ok": True})


@require_GET
@api
def api_widok(request, id_, firma):
    g = serwisy.wczytaj(id_)
    sprawdz_firme(request, id_, g, firma)
    runda = request.GET.get("runda", "")
    v = widok(g, firma, int(runda) if runda.isdigit() else None)
    return odpowiedz(_z_druzyna(v, id_, g, firma))


def _z_druzyna(v: dict, id_: str, g: GraSilnika, firma: str) -> dict:
    """Do widoku firmy: skład drużyny i kto ostatnio zapisał / wysłał decyzje."""
    v["druzyna"] = {
        "sklad": druzyny.sklad(id_).get(firma, []),
        "autorzy": druzyny.autorzy(g, firma),
    }
    return v


@require_GET
@api
def api_stan(request, id_, firma):
    """Lekki stan do odświeżania strony drużyny: runda, wersja decyzji, ostatni zapis, wysłane."""
    g = serwisy.wczytaj(id_)
    sprawdz_firme(request, id_, g, firma)
    a = druzyny.autorzy(g, firma)
    return odpowiedz(
        {
            "runda": g.runda,
            "wersja": a["wersja"],
            "zapisal": a.get("zapisal"),
            "wyslane": [] if g.zakonczona else g.wyslane(),
        }
    )


def _sprawdz_wersje(request, g: GraSilnika, firma: str) -> None:
    """Dwie osoby z drużyny zmieniają decyzje naraz: zapis na starej wersji odrzucamy (409)."""
    wersja = request.GET.get("wersja", "")
    a = druzyny.autorzy(g, firma)
    zapisal = a.get("zapisal") or {}
    if (
        not wersja.isdigit()
        or int(wersja) == a["wersja"]
        or zapisal.get("login") == request.user.username
    ):
        return
    kiedy = timezone.localtime(datetime.fromisoformat(zapisal["kiedy"])).strftime("%H:%M")
    raise BladZapytania(
        f"{zapisal['nazwa']} zmienia teraz decyzje drużyny (zapis o {kiedy}). "
        "Wczytano aktualne decyzje – powtórz swoją zmianę.",
        409,
    )


@require_http_methods(["PUT"])
@api
def api_decyzje(request, id_, firma):
    d = cialo(request)
    with serwisy.zmiana(id_) as g:
        sprawdz_firme(request, id_, g, firma)
        if g.zakonczona:
            raise BladZapytania("Gra jest zakończona.")
        if firma in g.wyslane():
            raise BladZapytania("Decyzje są wysłane – najpierw wróć do podejmowania decyzji.")
        _sprawdz_wersje(request, g, firma)
        g.ustaw_decyzje(firma, d)
        druzyny.autor(g, firma, request.user)
    return odpowiedz(_z_druzyna(widok(g, firma), id_, g, firma))


@require_POST
@api
def api_wyslij(request, id_, firma):
    wyslane = bool(cialo(request, wymagane=False).get("wyslane", True))
    przeliczono = False
    with serwisy.zmiana(id_) as g:
        sprawdz_firme(request, id_, g, firma)
        g.wyslij(firma, wyslane)
        druzyny.autor(g, firma, request.user, wyslal=wyslane)
        if wyslane and not g.brakujace() and not g.zakonczona:
            g.przelicz()
            przeliczono = True
    v = _z_druzyna(widok(g, firma), id_, g, firma)
    v["przeliczono"] = przeliczono
    return odpowiedz(v)


@require_POST
@api
@tylko_mg
def api_przelicz(request, id_):
    with serwisy.zmiana(id_) as g:
        if g.zakonczona:
            raise BladZapytania("Gra jest zakończona.")
        g.przelicz(wymus=True)
    return odpowiedz({"ok": True, "runda": g.runda})


@require_POST
@api
@tylko_mg
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
        sprawdz_firme(request, id_, g, firma)
        if request.method == "PUT":
            _warianty(g, firma)[nazwa] = d.get("decyzje") or deepcopy(g.szkic(firma))
        else:
            _warianty(g, firma).pop(request.GET.get("nazwa", ""), None)
    return odpowiedz(widok(g, firma))


@require_GET
@api
def api_dane_wariantu(request, id_, firma):
    g = serwisy.wczytaj(id_)
    sprawdz_firme(request, id_, g, firma)
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
    sprawdz_firme(request, id_, g, firma)
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
@tylko_mg
def api_eksport(request, id_):
    g = serwisy.wczytaj(id_)
    tresc = json.dumps(g.do_slownika(), ensure_ascii=False, indent=1)
    r = HttpResponse(tresc, content_type="application/json; charset=utf-8")
    r["Content-Disposition"] = content_disposition_header(True, f"{id_}.json")
    return r


@require_POST
@api
@tylko_mg
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
