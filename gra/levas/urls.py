from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.urls import include, path, re_path
from django.utils.cache import patch_cache_control

admin.site.site_header = "Levas – administracja"


def statyczne(request, path):
    """Pliki statyczne z `no-cache`: przeglądarka sprawdza przy każdym wczytaniu, czy plik się
    zmienił (odpowiedź 304, gdy nie), więc po zmianie zakładek gracze widzą nowe moduły bez Ctrl+F5.
    `graj` i `hostuj` uruchamiają serwer bez wbudowanej obsługi /static/, żeby szła tędy."""
    odp = serve(request, path, insecure=True)
    patch_cache_control(odp, no_cache=True)
    return odp


urlpatterns = [
    re_path(r"^static/(?P<path>.+)$", statyczne),
    path("konta/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("mg/", include("panel_mg.urls")),
    path("", include("panel_gracza.urls")),
]
