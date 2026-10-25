from django.urls import include, path

urlpatterns = [
    path("api/", include("api.urls")),
    path("mg/", include("panel_mg.urls")),
    path("", include("panel_gracza.urls")),
]
