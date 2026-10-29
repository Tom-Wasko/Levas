"""Widoki JSON dla zakładek (odpowiednik `serwer/app.py` z Revasa)."""

from __future__ import annotations

import csv
import io
import json
from copy import deepcopy
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from gry import harmonogram as hg
from gry import serwisy
from gry.models import Gra
from konta import druzyny
from konta.role import firmy_ucznia, gry_ucznia, jest_mg, moze_firme
from silnik import co_jesli
from silnik import harmonogram as hm
from silnik.dane import dane_domyslne
from silnik.gra import Gra as GraSilnika
from silnik.ksiegowosc.biuro import ukryj
from silnik.limity import naruszenia
from silnik.pieniadze import kasyno as kas
from silnik.rynek import handel as hd

from .prezentacja import katalogi, przeglad_mg, tabela_wynikow, widok

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


def _bez_klubu(request) -> bool:
    """Klub z silnik/pieniadze/kasyno.py jest tajny: mistrz gry go nie widzi,
    a LEVAS_KASYNO=0 wyłącza go na serwerze."""
    return jest_mg(request.user) or not settings.LEVAS_KASYNO


def _dla(request, v: dict) -> dict:
    """Widok firmy bez klubu dla mistrza gry (także bez portfela właściciela)
    i przy wyłączonym klubie."""
    return kas.ukryj(v, portfel=jest_mg(request.user)) if _bez_klubu(request) else v


def _bez_klubu_w_decyzjach(decyzje: dict) -> dict:
    """Plik gry (eksport) bez zakładów w klubie – także w zapisanych wariantach."""
    wynik = {}
    for r, rd in decyzje.items():
        rd = {k: kas.ukryj_decyzje(d) for k, d in rd.items()}
        if isinstance(rd.get("_warianty"), dict):
            rd["_warianty"] = {
                f: {n: kas.ukryj_decyzje(d) for n, d in w.items()}
                for f, w in rd["_warianty"].items()
            }
        wynik[r] = rd
    return wynik


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
    znane = dane_domyslne().boty.get("poziomy") or {}
    poziomy = {f["nazwa"].strip(): f["poziom"] for f in wiersze if f.get("bot") and f.get("poziom")}
    if any(p not in znane for p in poziomy.values()):
        return blad("Nie ma takiego poziomu botów.")
    try:
        g = GraSilnika.nowa(
            d.get("nazwa") or "Gra",
            firmy,
            int(d["liczba_rund"]) if d.get("liczba_rund") else None,  # brak – domyślna z danych
            int(ziarno) if str(ziarno or "").strip().isdigit() else None,
            ceny_dostawcow=d.get("ceny_dostawcow", "dane"),
            kredyt_odnawialny=d.get("kredyt_odnawialny", "na_biezaco"),
            auto_zamowienia=bool(d.get("auto_zamowienia")),
            kapital_startowy=kapital,
            poziomy=poziomy,
            odblokowanie=d.get("odblokowanie") or None,   # {element: tydzień} – zmiany harmonogramu
        )
    except ValueError as e:
        return blad(str(e))
    return odpowiedz({"id": serwisy.utworz(g)})


@require_GET
@api
@tylko_mg
def api_mg(request, id_):
    """Widok mistrza gry: runda, decyzje drużyn, wyniki wszystkich firm."""
    return odpowiedz(_przeglad(id_))


def _przeglad(id_: str) -> dict:
    g = serwisy.wczytaj(id_)
    p = przeglad_mg(g)
    sklad = druzyny.sklad(id_)
    for f in p["firmy"]:
        if not f["bot"]:
            f["sklad"] = sklad.get(f["nazwa"], [])
            f["autorzy"] = druzyny.autorzy(g, f["nazwa"])
    p["prowadzenie"] = hg.prowadzenie(id_)
    p["prowadzenie"]["dni"] = hg.DNI
    poziomy = g.dane.boty.get("poziomy") or {}
    p["prowadzenie"]["poziomy"] = {k: v["nazwa"] for k, v in poziomy.items()}
    p["prowadzenie"]["odblokowanie"] = hm.widok(g.dane, g.runda)
    return p


@require_POST
@api
@tylko_mg
def api_prowadzenie(request, id_):
    """Prowadzenie gry: {"pauza": bool}, {"harmonogram": [{"dzien", "godzina"}]},
    {"poziom": {"firma", "poziom"}} (poziom bota), {"odblokowanie": {element: tydzień}}
    (harmonogram odblokowań gry z lokalami), {"auto_zamowienia": bool} (przycisk „Zamów brakujące”
    w Dostawcach) albo {"inwestor": {"firma", "kwota"}} (inwestor ratunkowy, kwota 0 odwołuje)."""
    d = cialo(request)
    if "inwestor" in d:
        firma, kwota = (d["inwestor"] or {}).get("firma"), (d["inwestor"] or {}).get("kwota")
        try:
            with serwisy.zmiana(id_) as g:
                g.ustaw_inwestora(firma, float(kwota or 0))
        except (TypeError, ValueError) as e:
            raise BladZapytania(str(e)) from e
    if "auto_zamowienia" in d:
        with serwisy.zmiana(id_) as g:
            g.konfiguracja["auto_zamowienia"] = bool(d["auto_zamowienia"])
    if "odblokowanie" in d:
        if not isinstance(d["odblokowanie"], dict):
            raise BladZapytania("Harmonogram odblokowań: {element: tydzień}.")
        try:
            with serwisy.zmiana(id_) as g:
                g.ustaw_odblokowanie(d["odblokowanie"])
        except ValueError as e:
            raise BladZapytania(str(e)) from e
    if "poziom" in d:
        firma, poziom = (d["poziom"] or {}).get("firma"), (d["poziom"] or {}).get("poziom")
        with serwisy.zmiana(id_) as g:
            f = next((x for x in g.konfiguracja["firmy"] if x["nazwa"] == firma and x["bot"]), None)
            if f is None:
                raise BladZapytania("Nie ma takiego bota w grze.", 404)
            if poziom not in (g.dane.boty.get("poziomy") or {}):
                raise BladZapytania("Nie ma takiego poziomu botów.")
            f["poziom"] = poziom  # od następnej rundy (zapisane decyzje botów zostają)
    try:
        hg.ustaw(id_, d.get("pauza"), d.get("harmonogram"))
    except ValueError as e:
        raise BladZapytania(str(e)) from e
    return odpowiedz(_przeglad(id_))


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
    return odpowiedz(_z_druzyna(request, v, id_, g, firma))


def _z_druzyna(request, v: dict, id_: str, g: GraSilnika, firma: str) -> dict:
    """Do widoku firmy: skład drużyny, kto ostatnio zapisał / wysłał decyzje, pauza i termin
    zamknięcia rundy, wgląd mistrza gry tylko do odczytu."""
    v = _dla(request, v)
    sklad = druzyny.sklad(id_).get(firma, [])
    v["druzyna"] = {"sklad": sklad, "autorzy": druzyny.autorzy(g, firma)}
    for f, wersja in druzyny.loga(id_).items():
        marka = v.setdefault("marki", {}).setdefault(f, {"nazwa": f})
        marka["logo"] = f"/api/gry/{id_}/logo/{quote(f)}?w={wersja}"
    v["prowadzenie"] = hg.prowadzenie(id_)
    v["tylko_odczyt"] = _tylko_odczyt(request, id_, firma, sklad)
    return v


def _tylko_odczyt(request, id_: str, firma: str, sklad: list | None = None) -> bool:
    """Mistrz gry ogląda drużynę uczniów (nie swoją) – bez zmiany decyzji. Drużynę bez uczniów
    (także w grze lokalnej) prowadzi mistrz gry."""
    if not jest_mg(request.user) or firma in firmy_ucznia(request.user, id_):
        return False
    return bool(druzyny.sklad(id_).get(firma) if sklad is None else sklad)


def _moze_zmieniac(request, id_: str, firma: str) -> None:
    if _tylko_odczyt(request, id_, firma):
        raise BladZapytania("Mistrz gry ogląda decyzje drużyny tylko do odczytu.", 403)
    if hg.prowadzenie(id_)["pauza"]:
        raise BladZapytania("Gra jest wstrzymana przez mistrza gry – poczekaj na wznowienie.")


@require_GET
@api
def api_stan(request, id_, firma):
    """Lekki stan do odświeżania strony drużyny: runda, wersja decyzji, ostatni zapis, wysłane."""
    g = serwisy.wczytaj(id_)
    sprawdz_firme(request, id_, g, firma)
    a = druzyny.autorzy(g, firma)
    p = hg.prowadzenie(id_)
    return odpowiedz(
        {
            "runda": g.runda,
            "wersja": a["wersja"],
            "zapisal": a.get("zapisal"),
            "wyslane": [] if g.zakonczona else g.wyslane(),
            "pauza": p["pauza"],
            "termin": p["termin"],
            "handel": None if g.zakonczona else hd.znacznik(g.decyzje.get(g.runda, {}), firma),
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
        _moze_zmieniac(request, id_, firma)
        _sprawdz_wersje(request, g, firma)
        if _bez_klubu(request):
            d = kas.ukryj_decyzje(d)
        # limity (silnik/limity.py): zapis z przekroczeniem jest odrzucony
        bledy = naruszenia(g.dane, g.stan().firmy[firma], d, g.runda)
        if bledy:
            raise BladZapytania(" ".join(bledy))
        g.ustaw_decyzje(firma, d)
        druzyny.autor(g, firma, request.user)
    return odpowiedz(_z_druzyna(request, widok(g, firma), id_, g, firma))


@require_http_methods(["GET", "PUT"])
@api
def api_logo(request, id_, firma):
    """Logo firmy: obrazek widzą wszyscy gracze tej gry (mapa, dashboard),
    wgrać je można w pierwszej rundzie."""
    if request.method == "GET":
        if not (jest_mg(request.user) or id_ in gry_ucznia(request.user)):
            raise BladZapytania("To nie jest Twoja gra.", 403)
        from gry.models import Druzyna

        zapis = Druzyna.objects.filter(gra_id=id_, firma=firma).values_list("logo", flat=True)
        obraz = druzyny.logo(zapis.first() or "")
        if not obraz:
            raise BladZapytania("Firma nie ma logo.", 404)
        r = HttpResponse(obraz[1], content_type=obraz[0])
        r["Cache-Control"] = "private, max-age=86400"
        return r
    d = cialo(request)
    with serwisy.zmiana(id_) as g:
        sprawdz_firme(request, id_, g, firma)
        _moze_zmieniac(request, id_, firma)
        if g.zakonczona or g.runda != g.runda_startowa:
            raise BladZapytania("Logo firmy wybiera się w pierwszej rundzie gry.")
        try:
            druzyny.ustaw_logo(id_, firma, str(d.get("logo") or ""))
        except ValidationError as e:
            raise BladZapytania(" ".join(e.messages)) from e
    return odpowiedz(_z_druzyna(request, widok(g, firma), id_, g, firma))


@require_POST
@api
def api_wyslij(request, id_, firma):
    wyslane = bool(cialo(request, wymagane=False).get("wyslane", True))
    przeliczono = False
    with serwisy.zmiana(id_) as g:
        sprawdz_firme(request, id_, g, firma)
        _moze_zmieniac(request, id_, firma)
        g.wyslij(firma, wyslane)
        druzyny.autor(g, firma, request.user, wyslal=wyslane)
        if wyslane and not g.brakujace() and not g.zakonczona:
            g.przelicz()
            przeliczono = True
    v = _z_druzyna(request, widok(g, firma), id_, g, firma)
    v["przeliczono"] = przeliczono
    return odpowiedz(v)


@require_POST
@api
@tylko_mg
def api_przelicz(request, id_):
    with serwisy.zmiana(id_) as g:
        if g.zakonczona:
            raise BladZapytania("Gra jest zakończona.")
        if hg.prowadzenie(id_)["pauza"]:
            raise BladZapytania("Gra jest wstrzymana – wznów ją, żeby zamknąć rundę.")
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
            nowe = d.get("decyzje") or deepcopy(g.szkic(firma))
            _warianty(g, firma)[nazwa] = kas.ukryj_decyzje(nowe) if _bez_klubu(request) else nowe
        else:
            _warianty(g, firma).pop(request.GET.get("nazwa", ""), None)
    return odpowiedz(_dla(request, widok(g, firma)))


@require_GET
@api
def api_dane_wariantu(request, id_, firma):
    g = serwisy.wczytaj(id_)
    sprawdz_firme(request, id_, g, firma)
    zapisane = g.decyzje.get(g.runda, {}).get("_warianty", {}).get(firma, {})
    w = zapisane.get(request.GET.get("nazwa", ""))
    if w is None:
        return blad("Nie ma takiego wariantu.", 404)
    return odpowiedz(kas.ukryj_decyzje(w) if _bez_klubu(request) else w)


@require_POST
@api
def api_podglad(request, id_, firma):
    """Przewidywany wynik bieżącej rundy dla decyzji (bez zapisu, silnik/co_jesli.py). Boty decydują
    jak zwykle, inne drużyny powtarzają decyzje z poprzedniej rundy (ich robocze decyzje są tajne).
    Body: {"warianty": [nazwa wariantu albo "biezace"]} – domyślnie bieżące."""
    g = serwisy.wczytaj(id_)
    sprawdz_firme(request, id_, g, firma)
    if g.zakonczona:
        return blad("Gra jest zakończona.")
    kopia = g.kopia()
    nazwy = cialo(request, wymagane=False).get("warianty") or ["biezace"]
    zapisane = _warianty(kopia, firma)
    nazwy = [n for n in nazwy if n == "biezace" or n in zapisane]
    r = kopia.runda
    warianty = [g.szkic(firma) if n == "biezace" else zapisane[n] for n in nazwy]
    stany = co_jesli.przewiduj(kopia, firma, warianty)
    wyniki = []
    for nazwa, s in zip(nazwy, stany, strict=True):
        w = s.wyniki[r][firma]
        if s.firmy[firma].deklaracja:  # samodzielna księgowość: bez podatków rundy
            w = ukryj(w, podglad=True)
        if _bez_klubu(request):
            w = kas.ukryj_wyniki(w, portfel=jest_mg(request.user))
        wyniki.append(
            {
                "nazwa": "Bieżące decyzje" if nazwa == "biezace" else nazwa,
                "wyniki": w,
                "rynek": s.rynek[r],
            }
        )
    return odpowiedz({"runda": r, "warianty": wyniki})


@require_GET
@api
@tylko_mg
def api_eksport(request, id_):
    g = serwisy.wczytaj(id_)
    plik = g.do_slownika()
    plik["decyzje"] = _bez_klubu_w_decyzjach(plik["decyzje"])
    tresc = json.dumps(plik, ensure_ascii=False, indent=1)
    r = HttpResponse(tresc, content_type="application/json; charset=utf-8")
    r["Content-Disposition"] = content_disposition_header(True, f"{id_}.json")
    return r


@require_GET
@api
@tylko_mg
def api_wyniki_csv(request, id_, co):
    """Eksport wyników do arkusza: `wyniki` – firmy w rundach, `ranking` – ranking końcowy."""
    g = serwisy.wczytaj(id_)
    if co not in ("wyniki", "ranking"):
        raise BladZapytania("Nie ma takiego eksportu.", 404)
    naglowek, wiersze = tabela_wynikow(g, co)
    plik = io.StringIO()
    w = csv.writer(plik, delimiter=";", lineterminator="\r\n")  # Excel z polskimi ustawieniami
    w.writerow(naglowek)
    for wiersz in wiersze:
        w.writerow([f"{x:.2f}".replace(".", ",") if isinstance(x, float) else x for x in wiersz])
    r = HttpResponse("\ufeff" + plik.getvalue(), content_type="text/csv; charset=utf-8")
    r["Content-Disposition"] = content_disposition_header(True, f"{id_}-{co}.csv")
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
