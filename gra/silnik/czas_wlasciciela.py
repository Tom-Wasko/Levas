"""Czas właściciela (gra z lokalami, F3a.7).

Właściciel ma na rundę pulę godzin na sprawy poza lokalem (`operacje.czas_wlasciciela` w zalozenia.yaml): odbiór
osobisty w dyskontach, a w kolejnych etapach ogłoszenia na pracuj.pl i parki. Decyzje zużywają godziny po kolei;
decyzja, na którą nie starcza godzin, jest odrzucona (czerwony błąd na liście błędów).
"""

from __future__ import annotations

from .dane import Dane


def godziny(x: float) -> str:
    return f"{x:g}".replace(".", ",")


class Czas:
    def __init__(self, pula: float):
        self.pula = float(pula)
        self.pozycje: list[dict] = []

    @property
    def wykorzystane(self) -> float:
        return round(sum(p["godziny"] for p in self.pozycje if p["przyjete"]), 2)

    @property
    def wolne(self) -> float:
        return round(self.pula - self.wykorzystane, 2)

    def wez(self, ile: float, opis: str, zakladka: str) -> bool:
        """Rezerwuje `ile` godzin; False (i pozycja odrzucona) – brak wolnych godzin."""
        ok = ile <= self.wolne + 1e-9
        self.pozycje.append({"opis": opis, "godziny": ile, "zakladka": zakladka, "przyjete": ok})
        return ok

    def podsumowanie(self) -> dict:
        return {"pula": self.pula, "wykorzystane": self.wykorzystane, "wolne": self.wolne, "pozycje": list(self.pozycje)}


def nowy(dane: Dane) -> Czas:
    return Czas(dane.z["operacje"]["czas_wlasciciela"])
