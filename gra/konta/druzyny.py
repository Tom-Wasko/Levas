"""Skład drużyn (1–4 uczniów na firmę), autorzy decyzji i konta zakładane przez mistrza gry."""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from .role import jest_mg

MAKS_CZLONKOW = 4  # [[Zarys aplikacji]]: drużyny 1–4 osób
ZNAKI_HASLA = "abcdefghjkmnpqrstuvwxyz23456789"  # bez l/1, o/0 – hasło przepisuje się z kartki
DLUGOSC_HASLA = 8
MAKS_LOGO_KB = 300  # logo firmy (runda 1) – mały obrazek, trzymany w bazie jako data URL
FORMATY_LOGO = {"image/png": b"\x89PNG", "image/jpeg": b"\xff\xd8\xff"}


def nazwa(user) -> str:
    return user.get_full_name() or user.username


def osoba(user) -> dict:
    return {"login": user.username, "nazwa": nazwa(user)}


def sprawdz_sklad(id_gry: str, firma: str, uzytkownicy) -> None:
    """Najwyżej 4 osoby w drużynie, uczeń w jednej drużynie gry. Błąd: `ValidationError`."""
    from gry.models import Druzyna

    uzytkownicy = list(uzytkownicy)
    if len(uzytkownicy) > MAKS_CZLONKOW:
        raise ValidationError(f"Drużyna może mieć najwyżej {MAKS_CZLONKOW} osoby.")
    inne = (
        Druzyna.objects.filter(gra_id=id_gry, czlonkowie__in=uzytkownicy)
        .exclude(firma=firma)
        .values_list("czlonkowie__username", "firma")
    )
    zajeci = {login: f for login, f in inne if login in {u.username for u in uzytkownicy}}
    if zajeci:
        login, f = sorted(zajeci.items())[0]
        raise ValidationError(f"{login} gra już w drużynie {f}.")


def logo(data_url: str) -> tuple[str, bytes] | None:
    """(typ, bajty) obrazka z data URL; None – brak albo uszkodzony."""
    m = re.fullmatch(r"data:(image/(?:png|jpeg));base64,([A-Za-z0-9+/=\s]+)", data_url or "")
    if not m:
        return None
    try:
        bajty = base64.b64decode(m.group(2), validate=False)
    except (binascii.Error, ValueError):
        return None
    return (m.group(1), bajty) if bajty.startswith(FORMATY_LOGO[m.group(1)]) else None


def ustaw_logo(id_gry: str, firma: str, data_url: str) -> None:
    """Logo firmy (PNG albo JPG, najwyżej MAKS_LOGO_KB); pusty tekst usuwa logo.
    Błąd: `ValidationError`."""
    from gry.models import Druzyna

    if data_url:
        obraz = logo(data_url)
        if not obraz:
            raise ValidationError("Logo musi być obrazkiem PNG albo JPG.")
        if len(obraz[1]) > MAKS_LOGO_KB * 1024:
            raise ValidationError(
                f"Logo jest za duże – najwyżej {MAKS_LOGO_KB} KB. "
                "Zmniejsz obrazek i wgraj go jeszcze raz."
            )
    d, _ = Druzyna.objects.get_or_create(gra_id=id_gry, firma=firma)
    d.logo = data_url or ""
    d.save(update_fields=["logo"])


def loga(id_gry: str) -> dict[str, str]:
    """{firma: wersja logo} – wersja (skrót treści) odświeża obrazek w przeglądarce po zmianie."""
    from gry.models import Druzyna

    zapisane = Druzyna.objects.filter(gra_id=id_gry).exclude(logo="").values_list("firma", "logo")
    return {f: hashlib.sha1(lg.encode()).hexdigest()[:10] for f, lg in zapisane}


def sklad(id_gry: str) -> dict[str, list[dict]]:
    """{firma: [{login, nazwa}]} – tylko firmy z dopisanymi uczniami."""
    from gry.models import Druzyna

    wynik: dict[str, list[dict]] = {}
    for d in Druzyna.objects.filter(gra_id=id_gry).prefetch_related("czlonkowie"):
        osoby = sorted((osoba(u) for u in d.czlonkowie.all()), key=lambda o: o["nazwa"].lower())
        if osoby:
            wynik[d.firma] = osoby
    return wynik


def dodaj(id_gry: str, firma: str, login: str) -> None:
    from gry.models import Druzyna

    user = get_user_model().objects.filter(username=login.strip()).first()
    if user is None:
        raise ValidationError(f"Nie ma konta {login.strip()}.")
    druzyna, _ = Druzyna.objects.get_or_create(gra_id=id_gry, firma=firma)
    if druzyna.czlonkowie.filter(pk=user.pk).exists():
        return
    sprawdz_sklad(id_gry, firma, [*druzyna.czlonkowie.all(), user])
    druzyna.czlonkowie.add(user)


def usun(id_gry: str, firma: str, login: str) -> None:
    from gry.models import Druzyna

    druzyna = Druzyna.objects.filter(gra_id=id_gry, firma=firma).first()
    if druzyna:
        druzyna.czlonkowie.remove(*druzyna.czlonkowie.filter(username=login))


def uczniowie() -> list[dict]:
    """Konta bez roli mistrza gry – podpowiedzi przy dopisywaniu do drużyny."""
    konta = get_user_model().objects.filter(is_active=True).order_by("username")
    return [osoba(u) for u in konta.prefetch_related("groups") if not jest_mg(u)]


def nowe_haslo() -> str:
    return "".join(secrets.choice(ZNAKI_HASLA) for _ in range(DLUGOSC_HASLA))


def nowe_konto(login: str, imie: str = "") -> tuple[object, str]:
    """Konto ucznia z losowym hasłem (mistrz gry przekazuje je uczniowi). Zwraca (konto, hasło)."""
    login = login.strip()
    if not login:
        raise ValidationError("Podaj login.")
    UnicodeUsernameValidator()(login)
    Konto = get_user_model()
    if Konto.objects.filter(username__iexact=login).exists():
        raise ValidationError(f"Login {login} jest już zajęty.")
    haslo = nowe_haslo()
    user = Konto(username=login)
    user.first_name, _, user.last_name = imie.strip().partition(" ")
    user.set_password(haslo)
    user.save()
    return user, haslo


def autor(g, firma: str, user, wyslal: bool | None = None) -> None:
    """Zapisuje w rundzie, kto z drużyny ostatnio zapisał (albo wysłał) decyzje; podbija wersję."""
    a = g.decyzje.setdefault(g.runda, {}).setdefault("_autorzy", {}).setdefault(firma, {})
    ktos = {"login": user.username, "nazwa": nazwa(user), "kiedy": timezone.now().isoformat()}
    if wyslal is None:
        a["zapisal"] = ktos
    elif wyslal:
        a["wyslal"] = ktos
    else:
        a.pop("wyslal", None)
    a["wersja"] = a.get("wersja", 0) + 1


def autorzy(g, firma: str) -> dict:
    """Kto zapisał / wysłał decyzje firmy w bieżącej rundzie: {zapisal, wyslal, wersja}."""
    a = dict(g.decyzje.get(g.runda, {}).get("_autorzy", {}).get(firma, {}))
    if firma not in g.wyslane():
        a.pop("wyslal", None)
    a.setdefault("wersja", 0)
    return a


POLSKIE = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def wolny_login(imie: str) -> str:
    """„Ala Nowak” → ala.nowak (ala.nowak2, gdy zajęty)."""
    baza = ".".join(re.findall(r"[a-z0-9]+", imie.translate(POLSKIE).lower()))[:30] or "uczen"
    Konto = get_user_model()
    login, n = baza, 1
    while Konto.objects.filter(username__iexact=login).exists():
        n += 1
        login = f"{baza}{n}"
    return login
