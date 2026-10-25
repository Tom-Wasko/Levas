from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Levas – administracja"

urlpatterns = [
    path("konta/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("mg/", include("panel_mg.urls")),
    path("", include("panel_gracza.urls")),
]
