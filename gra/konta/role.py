"""Role: mistrz gry (grupa `mistrz_gry` albo superużytkownik) i uczeń (każde inne konto).

Uczeń widzi tylko gry i firmy swoich drużyn (`gry.Druzyna.czlonkowie`), mistrz gry – wszystko.
"""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission

MISTRZ_GRY = "mistrz_gry"
# panel administracyjny: konta uczniów, drużyny, podgląd gier
UPRAWNIENIA_MG = {
    "auth": ["add_user", "change_user", "view_user"],
    "gry": ["add_druzyna", "change_druzyna", "delete_druzyna", "view_druzyna"]
    + ["view_gra", "change_gra"],  # zmiana gry = dopisywanie drużyn na jej stronie
}


def jest_mg(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if not hasattr(user, "_jest_mg"):
        user._jest_mg = user.groups.filter(name=MISTRZ_GRY).exists()
    return user._jest_mg


def nadaj_mg(user, mg: bool = True) -> None:
    grupa, nowa = Group.objects.get_or_create(name=MISTRZ_GRY)
    if nowa or not grupa.permissions.exists():
        for aplikacja, kody in UPRAWNIENIA_MG.items():
            grupa.permissions.add(
                *Permission.objects.filter(content_type__app_label=aplikacja, codename__in=kody)
            )
    (user.groups.add if mg else user.groups.remove)(grupa)
    user.is_staff = mg or user.is_superuser  # panel administracyjny Django dla mistrza gry
    user.save(update_fields=["is_staff"])
    user.__dict__.pop("_jest_mg", None)


def firmy_ucznia(user, id_gry: str) -> set[str]:
    from gry.models import Druzyna

    if not user.is_authenticated:
        return set()
    return set(
        Druzyna.objects.filter(gra_id=id_gry, czlonkowie=user).values_list("firma", flat=True)
    )


def gry_ucznia(user) -> set[str]:
    from gry.models import Druzyna

    return set(Druzyna.objects.filter(czlonkowie=user).values_list("gra_id", flat=True))


def moze_firme(user, id_gry: str, firma: str) -> bool:
    return jest_mg(user) or firma in firmy_ucznia(user, id_gry)


def moze_gre(user, id_gry: str) -> bool:
    return jest_mg(user) or bool(firmy_ucznia(user, id_gry))
