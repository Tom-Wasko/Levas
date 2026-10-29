from django.contrib import admin
from django.urls import include, path, re_path

from . import statyczne

admin.site.site_header = "Levas – administracja"


urlpatterns = [
    re_path(r"^static/(?:v[0-9a-f]+/)?(?P<path>.+)$", statyczne.widok),
    path("konta/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("mg/", include("panel_mg.urls")),
    path("", include("panel_gracza.urls")),
]
