from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from konta.druzyny import sprawdz_sklad

from .models import Druzyna, Gra


class DruzynaForm(forms.ModelForm):
    """Zasady jak w panelu mistrza gry: firma gracza z gry, 1–4 osoby, uczeń w jednej drużynie."""

    class Meta:
        model = Druzyna
        fields = ["gra", "firma", "czlonkowie"]

    def clean(self):
        dane = super().clean()
        gra = dane.get("gra") or getattr(self.instance, "gra", None)
        firma = dane.get("firma")
        if gra is None or not firma:
            return dane
        if firma not in {f["nazwa"] for f in gra.konfiguracja["firmy"] if not f["bot"]}:
            raise ValidationError(f"W grze {gra.nazwa} nie ma firmy gracza {firma}.")
        sprawdz_sklad(gra.pk, firma, dane.get("czlonkowie") or [])
        return dane


class DruzynaWGrze(admin.TabularInline):
    model = Druzyna
    form = DruzynaForm
    extra = 0
    filter_horizontal = ["czlonkowie"]


@admin.register(Gra)
class GraAdmin(admin.ModelAdmin):
    list_display = ["nazwa", "id", "zmieniono"]
    fields = ["nazwa"]
    readonly_fields = ["nazwa"]  # nazwa jest też w konfiguracji gry
    inlines = [DruzynaWGrze]

    def has_add_permission(self, request):
        return False  # gry zakłada się w panelu mistrza gry


@admin.register(Druzyna)
class DruzynaAdmin(admin.ModelAdmin):
    form = DruzynaForm
    list_display = ["firma", "gra"]
    list_filter = ["gra"]
    filter_horizontal = ["czlonkowie"]
