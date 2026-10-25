"""Silnik gry (bez interfejsu). Wejście: silnik.gra.Gra; dane: `python -m silnik.dane sprawdz`."""


def __getattr__(nazwa: str):
    # leniwy import, żeby `python -m silnik.dane` nie wczytywał modułu dwa razy
    if nazwa == "Gra":
        from .gra import Gra

        return Gra
    raise AttributeError(nazwa)
