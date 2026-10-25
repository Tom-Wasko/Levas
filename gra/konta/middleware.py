"""Logowanie wymagane na każdej stronie poza logowaniem i statykami.

Gra na własnym komputerze (`manage.py graj`, start.bat) loguje się sama na lokalne konto mistrza
gry – tylko gdy zapytanie przychodzi z tego komputera.
"""

from __future__ import annotations

from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from django.shortcuts import redirect

from .role import nadaj_mg

WOLNE = ("/konta/", "/static/", "/favicon.ico")
LOKALNE_ADRESY = {"127.0.0.1", "::1"}
LOKALNY_LOGIN = "lokalny"


def lokalne_konto():
    user, nowe = get_user_model().objects.get_or_create(
        username=LOKALNY_LOGIN, defaults={"first_name": "Gra lokalna"}
    )
    if nowe:
        user.set_unusable_password()
        user.save()
        nadaj_mg(user)
    return user


class LogowanieWymagane:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.path.startswith(WOLNE):
            if settings.LEVAS_LOKALNIE and request.META.get("REMOTE_ADDR") in LOKALNE_ADRESY:
                login(request, lokalne_konto(), backend="django.contrib.auth.backends.ModelBackend")
            elif request.path.startswith("/api/"):
                return JsonResponse({"blad": "Zaloguj się."}, status=401)
            else:
                return redirect(f"{settings.LOGIN_URL}?next={quote(request.get_full_path())}")
        return self.get_response(request)
