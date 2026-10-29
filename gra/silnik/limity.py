"""Limity, żeby nie dało się wykupić całego rynku (gra z lokalami, notatki „Prawidła świata”, „Ustalenia gry”):

- najwyżej `limit_nowych` nowych pracowników na rundę – zatrudnienia z puli i oferty podkupienia razem
  (`dane/kandydaci.yaml: agencja.limit_nowych`),
- nowy lokal najwyżej co `nowy_lokal_co_rund` rund (`dane/mapa/lokale.yaml: zasady`).

`naruszenia` sprawdza szkic decyzji przy zapisie (API odrzuca zapis z naruszeniem). Przeliczenie rundy i tak
przycina nadmiar (`rynek_pracy.przed_decyzjami`, `lokale.powod_odrzucenia`) – dla botów i starych zapisów gier.
"""
from __future__ import annotations

from .dane import Dane
from .ludzie import rynek_pracy as rp
from .model import Firma
from .nieruchomosci import lokale as lk


def nowi_pracownicy(decyzje: dict, firma: str) -> int:
    """Nowi pracownicy w decyzjach: zatrudnienia i oferty podkupienia pracowników innych firm."""
    podkup = [o for o in (decyzje.get("podkup") or []) if o.get("firma") != firma]
    return len(decyzje.get("zatrudnij") or []) + len(podkup)


def stan_limitow(dane: Dane, firma: Firma, decyzje: dict, runda: int) -> dict:
    """Dla strony: limit i liczba nowych pracowników, runda, od której można wziąć kolejny lokal."""
    return {"pracownicy": {"limit": rp.ustawienia(dane)["limit_nowych"], "nowi": nowi_pracownicy(decyzje, firma.nazwa)},
            "lokal": {"co_rund": dane.mapa["zasady"]["nowy_lokal_co_rund"], "od_rundy": lk.runda_nowego_lokalu(dane, firma)}}


def naruszenia(dane: Dane, firma: Firma, decyzje: dict, runda: int) -> list[str]:
    """Przekroczone limity w decyzjach firmy (pusta lista – w porządku)."""
    wynik = []
    s = stan_limitow(dane, firma, decyzje, runda)
    p = s["pracownicy"]
    if p["nowi"] > p["limit"]:
        wynik.append(f"W jednej rundzie można przyjąć najwyżej {p['limit']} nowych pracowników (zatrudnienia i oferty "
                     f"podkupienia razem) – w decyzjach jest {p['nowi']}.")
    lokal = decyzje.get("lokal") or {}
    if lokal.get("id") and runda < s["lokal"]["od_rundy"]:
        wynik.append(lk.komunikat_odpoczynku(dane, firma, runda))
    return wynik
