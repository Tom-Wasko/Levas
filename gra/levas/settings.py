"""Ustawienia Django dla Levasa. Lokalnie: tryb deweloperski, baza SQLite w `db.sqlite3`."""

import json
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _klucz() -> str:
    """Klucz z LEVAS_SECRET_KEY albo wygenerowany raz i trzymany w `lokalne.json` (poza gitem)."""
    if os.environ.get("LEVAS_SECRET_KEY"):
        return os.environ["LEVAS_SECRET_KEY"]
    plik = BASE_DIR / "lokalne.json"
    dane = json.loads(plik.read_text(encoding="utf-8")) if plik.exists() else {}
    if not dane.get("secret_key"):
        dane["secret_key"] = secrets.token_urlsafe(50)
        plik.write_text(json.dumps(dane, indent=1), encoding="utf-8")
    return dane["secret_key"]


SECRET_KEY = _klucz()
DEBUG = os.environ.get("LEVAS_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "gry",
    "api",
    "panel_gracza",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "levas.urls"
WSGI_APPLICATION = "levas.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
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

# Plik gry przy imporcie może mieć kilka MB (decyzje wszystkich rund).
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
