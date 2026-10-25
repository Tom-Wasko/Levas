from django.urls import path

from . import widoki as w

urlpatterns = [
    path("", w.lista),
    path("gra/<str:id_>", w.gra),
]
