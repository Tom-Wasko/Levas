"""Gry w bazie: wczytanie do silnika, zapis decyzji, lista gier.

Silnik trzyma decyzje jako {runda: {firma: decyzje, "_przeliczona": bool, "_wyslane": [...],
"_warianty": {...}, "_autorzy": {...}}}. W bazie klucze z podkreśleniem są polami `Runda`,
a decyzje firm – wierszami `Decyzja`. Wczytane gry zostają w pamięci (z policzonymi stanami
rund), dopóki nie zmieni się `Gra.zmieniono`.
"""

from __future__ import annotations

import re
import secrets
import threading
from collections.abc import Iterator
from contextlib import contextmanager

from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from silnik.gra import Gra as GraSilnika

from .models import Decyzja, Gra, Runda

_blokada = threading.RLock()
_pamiec: dict[str, tuple[object, GraSilnika]] = {}

KLUCZE_RUNDY = {"_przeliczona", "_wyslane", "_warianty", "_autorzy"}


def nowy_id(nazwa: str) -> str:
    return re.sub(r"[^\w]+", "-", nazwa.lower()).strip("-")[:30] + "-" + secrets.token_hex(3)


def wczytaj(id_: str) -> GraSilnika:
    """Gra z pamięci albo z bazy. Brak gry: `Gra.DoesNotExist`."""
    zmieniono = Gra.objects.filter(pk=id_).values_list("zmieniono", flat=True).first()
    if zmieniono is None:
        raise Gra.DoesNotExist(id_)
    w_pamieci = _pamiec.get(id_)
    if w_pamieci and w_pamieci[0] == zmieniono:
        return w_pamieci[1]
    obj = Gra.objects.prefetch_related("rundy__decyzje").get(pk=id_)
    decyzje: dict[int, dict] = {}
    for r in obj.rundy.all():
        d = {x.firma: x.dane for x in r.decyzje.all()}
        if r.przeliczona:
            d["_przeliczona"] = True
        if r.wyslane:
            d["_wyslane"] = list(r.wyslane)
        if r.warianty:
            d["_warianty"] = r.warianty
        if r.autorzy:
            d["_autorzy"] = r.autorzy
        decyzje[r.numer] = d
    g = GraSilnika(obj.konfiguracja, decyzje)
    _pamiec[id_] = (obj.zmieniono, g)
    return g


def zapisz(id_: str, g: GraSilnika) -> None:
    with transaction.atomic():
        przeliczone = sum(1 for d in g.decyzje.values() if d.get("_przeliczona"))
        przed = Runda.objects.filter(gra_id=id_, przeliczona=True).count()
        nowa = not Gra.objects.filter(pk=id_).exists()
        defaults = {"nazwa": g.konfiguracja["nazwa"], "konfiguracja": g.konfiguracja}
        if nowa or przeliczone != przed:  # zamknięta albo cofnięta runda – termin liczony od teraz
            defaults["termin_od"] = timezone.now()
        obj, _ = Gra.objects.update_or_create(pk=id_, defaults=defaults)
        obj.rundy.all().delete()
        for numer, d in sorted(g.decyzje.items()):
            nieznane = {k for k in d if k.startswith("_")} - KLUCZE_RUNDY
            if nieznane:
                raise ValueError(f"Nieznane pola rundy {numer}: {', '.join(sorted(nieznane))}")
            r = Runda.objects.create(
                gra=obj,
                numer=numer,
                przeliczona=bool(d.get("_przeliczona")),
                wyslane=list(d.get("_wyslane", [])),
                warianty=d.get("_warianty", {}),
                autorzy=d.get("_autorzy", {}),
            )
            Decyzja.objects.bulk_create(
                Decyzja(runda=r, firma=f, dane=v) for f, v in d.items() if not f.startswith("_")
            )
    _pamiec[id_] = (obj.zmieniono, g)


def utworz(g: GraSilnika) -> str:
    id_ = nowy_id(g.konfiguracja["nazwa"])
    with _blokada:
        zapisz(id_, g)
    return id_


@contextmanager
def zmiana(id_: str) -> Iterator[GraSilnika]:
    """Zmiana gry pod blokadą i zapis po wyjściu. Przy błędzie gra w pamięci jest porzucana."""
    with _blokada:
        g = wczytaj(id_)
        try:
            yield g
        except BaseException:
            _pamiec.pop(id_, None)
            raise
        zapisz(id_, g)


def usun(id_: str) -> None:
    with _blokada:
        _pamiec.pop(id_, None)
        Gra.objects.filter(pk=id_).delete()


def lista() -> list[dict]:
    gry = Gra.objects.annotate(
        ostatnia=Max("rundy__numer", filter=Q(rundy__przeliczona=True))
    ).order_by("-zmieniono")
    return [
        {
            "id": g.pk,
            "nazwa": g.nazwa,
            "runda": (g.ostatnia or 0) + 1,
            "liczba_rund": g.konfiguracja["liczba_rund"],
            "firmy": g.konfiguracja["firmy"],
        }
        for g in gry
    ]
