"""Ustawienia Django dla Levasa. Lokalnie: tryb deweloperski, baza SQLite w `db.sqlite3`."""

import json
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


PLIK_LOKALNY = BASE_DIR / "lokalne.json"  # ustawienia tego komputera (poza gitem)
LOKALNE = json.loads(PLIK_LOKALNY.read_text(encoding="utf-8")) if PLIK_LOKALNY.exists() else {}


def _klucz() -> str:
    """Klucz z LEVAS_SECRET_KEY albo wygenerowany raz i trzymany w `lokalne.json`."""
    if os.environ.get("LEVAS_SECRET_KEY"):
        return os.environ["LEVAS_SECRET_KEY"]
    if not LOKALNE.get("secret_key"):
        LOKALNE["secret_key"] = secrets.token_urlsafe(50)
        PLIK_LOKALNY.write_text(json.dumps(LOKALNE, indent=1), encoding="utf-8")
    return LOKALNE["secret_key"]


SECRET_KEY = _klucz()
DEBUG = os.environ.get("LEVAS_DEBUG", "1") == "1"
# Inne adresy serwera (np. gra w sieci szkoły): LEVAS_HOSTY="levas.szkola.pl,192.168.1.20"
# albo "hosty" w lokalne.json.
_HOSTY = os.environ.get("LEVAS_HOSTY", "").split(",") + LOKALNE.get("hosty", [])
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
ALLOWED_HOSTS += [h.strip() for h in _HOSTY if h.strip()]
# Za serwerem WWW z https (LEVAS_HTTPS=1 albo "https": true): adresy zwrotne logowania z https.
if os.environ.get("LEVAS_HTTPS") == "1" or LOKALNE.get("https"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
    CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS[3:]]
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True

# Logowanie kontem Microsoft (szkolnym), krok po kroku: LOGOWANIE_MICROSOFT.md. Aplikacja
# zarejestrowana w Microsoft Entra ID, adres przekierowania
# http(s)://<serwer>/konta/microsoft/login/callback/. Dane z LEVAS_MS_CLIENT_ID / LEVAS_MS_SECRET /
# LEVAS_MS_TENANT albo z "microsoft" w lokalne.json. Bez identyfikatora klienta – tylko własny login
# i hasło. Dzierżawa (tenant) szkoły: logują się tylko jej konta.
_MS = LOKALNE.get("microsoft", {})
MICROSOFT = {
    "client_id": os.environ.get("LEVAS_MS_CLIENT_ID", _MS.get("client_id", "")),
    "secret": os.environ.get("LEVAS_MS_SECRET", _MS.get("secret", "")),
    "tenant": os.environ.get("LEVAS_MS_TENANT", _MS.get("tenant", "organizations")),
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "konta",  # przed allauth: własne szablony logowania
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.microsoft",
    "gry",
    "api",
    "panel_gracza",
    "panel_mg",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "konta.middleware.LogowanieWymagane",
]

ROOT_URLCONF = "levas.urls"
WSGI_APPLICATION = "levas.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "konta.kontekst.konto",
                "levas.statyczne.kontekst",
            ]
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "pl"
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"

# --- konta (konta/, django-allauth) ---
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_URL = "/konta/login/"
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/konta/login/"
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_ADAPTER = "konta.adaptery.Konta"
SOCIALACCOUNT_ADAPTER = "konta.adaptery.KontaMicrosoft"
SOCIALACCOUNT_PROVIDERS = {
    "microsoft": {
        "TENANT": MICROSOFT["tenant"],
        "APPS": [{"client_id": MICROSOFT["client_id"], "secret": MICROSOFT["secret"]}]
        if MICROSOFT["client_id"]
        else [],  # bez aplikacji przycisk Microsoft się nie pokazuje
    }
}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # gra nie wysyła poczty
# Własne konta zakłada mistrz gry (`manage.py konto`, panel administracyjny); LEVAS_REJESTRACJA=1
# otwiera samodzielną rejestrację.
LEVAS_REJESTRACJA = os.environ.get("LEVAS_REJESTRACJA") == "1"
# Gra na własnym komputerze (`manage.py graj`): automatyczne lokalne konto mistrza gry.
LEVAS_LOKALNIE = os.environ.get("LEVAS_LOKALNIE") == "1"
# Dodatkowe miejsce w mieście dla drużyn (domyślnie włączone); LEVAS_KASYNO=0 je wyłącza.
LEVAS_KASYNO = os.environ.get("LEVAS_KASYNO", "1") == "1"

# Plik gry przy imporcie może mieć kilka MB (decyzje wszystkich rund).
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
