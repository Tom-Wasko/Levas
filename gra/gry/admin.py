from django.contrib import admin

from .models import Druzyna, Gra


class DruzynaWGrze(admin.TabularInline):
    model = Druzyna
    extra = 0
    filter_horizontal = ["czlonkowie"]


@admin.register(Gra)
class GraAdmin(admin.ModelAdmin):
    list_display = ["nazwa", "id", "zmieniono"]
    fields = ["nazwa"]
    readonly_fields = ["nazwa"]  # nazwa jest też w konfiguracji gry
    inlines = [DruzynaWGrze]


@admin.register(Druzyna)
class DruzynaAdmin(admin.ModelAdmin):
    list_display = ["firma", "gra"]
    list_filter = ["gra"]
    filter_horizontal = ["czlonkowie"]
