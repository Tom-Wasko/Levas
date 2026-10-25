from django.urls import path

from . import widoki as w

urlpatterns = [
    path("katalogi", w.api_katalogi),
    path("gry", w.api_gry),
    path("gry/import", w.api_import),
    path("konta", w.api_konta),
    path("konta/<str:login>/haslo", w.api_nowe_haslo),
    path("gry/<str:id_>", w.api_usun),
    path("gry/<str:id_>/mg", w.api_mg),
    path("gry/<str:id_>/druzyny", w.api_druzyny),
    path("gry/<str:id_>/druzyny/<str:firma>", w.api_druzyna),
    path("gry/<str:id_>/widok/<str:firma>", w.api_widok),
    path("gry/<str:id_>/decyzje/<str:firma>", w.api_decyzje),
    path("gry/<str:id_>/stan/<str:firma>", w.api_stan),
    path("gry/<str:id_>/wyslij/<str:firma>", w.api_wyslij),
    path("gry/<str:id_>/przelicz", w.api_przelicz),
    path("gry/<str:id_>/cofnij", w.api_cofnij),
    path("gry/<str:id_>/warianty/<str:firma>", w.api_warianty),
    path("gry/<str:id_>/warianty-dane/<str:firma>", w.api_dane_wariantu),
    path("gry/<str:id_>/podglad/<str:firma>", w.api_podglad),
    path("gry/<str:id_>/eksport", w.api_eksport),
]
