"""Rejestracja: własne konta zakłada mistrz gry, konto Microsoft (szkolne) zakłada się samo."""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class Konta(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return settings.LEVAS_REJESTRACJA


class KontaMicrosoft(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True  # dostęp ogranicza dzierżawa (tenant) szkoły w ustawieniach aplikacji Microsoft
