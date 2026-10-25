"""Zapis gry (event sourcing): konfiguracja + decyzje firm w rundach. Stan liczy silnik od nowa."""

from django.conf import settings
from django.db import models


class Gra(models.Model):
    id = models.CharField(primary_key=True, max_length=40)
    nazwa = models.CharField(max_length=100)
    konfiguracja = models.JSONField()
    utworzono = models.DateTimeField(auto_now_add=True)
    zmieniono = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "gry"

    def __str__(self) -> str:
        return self.nazwa


class Runda(models.Model):
    gra = models.ForeignKey(Gra, on_delete=models.CASCADE, related_name="rundy")
    numer = models.PositiveIntegerField()
    przeliczona = models.BooleanField(default=False)
    wyslane = models.JSONField(default=list)  # firmy, które wysłały decyzje
    warianty = models.JSONField(default=dict)  # {firma: {nazwa wariantu: decyzje}} do Analizy

    class Meta:
        verbose_name_plural = "rundy"
        constraints = [models.UniqueConstraint(fields=["gra", "numer"], name="runda_unikalna")]
        ordering = ["numer"]

    def __str__(self) -> str:
        return f"{self.gra_id} r{self.numer}"


class Decyzja(models.Model):
    runda = models.ForeignKey(Runda, on_delete=models.CASCADE, related_name="decyzje")
    firma = models.CharField(max_length=100)
    dane = models.JSONField(default=dict)

    class Meta:
        verbose_name_plural = "decyzje"
        constraints = [models.UniqueConstraint(fields=["runda", "firma"], name="decyzja_unikalna")]

    def __str__(self) -> str:
        return f"{self.runda} {self.firma}"


class Druzyna(models.Model):
    """Uczniowie prowadzący firmę w grze. Uczeń widzi tylko gry i firmy swoich drużyn."""

    gra = models.ForeignKey(Gra, on_delete=models.CASCADE, related_name="druzyny")
    firma = models.CharField(max_length=100)
    czlonkowie = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="druzyny", blank=True, verbose_name="uczniowie"
    )

    class Meta:
        verbose_name = "drużyna"
        verbose_name_plural = "drużyny"
        constraints = [models.UniqueConstraint(fields=["gra", "firma"], name="druzyna_unikalna")]

    def __str__(self) -> str:
        return f"{self.firma} ({self.gra_id})"
