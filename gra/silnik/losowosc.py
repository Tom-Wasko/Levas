"""Jedyne źródło losowości w grze: nazwane strumienie `numpy.random.Generator(PCG64)`.

Strumień wyznaczają (ziarno gry, runda, cel, klucze), np. `strumien(ziarno, 3, "popyt", firma, danie)`.
Ziarno strumienia to pełny skrót SHA-256 tych wartości (przez `SeedSequence`), więc:
- ten sam strumień zawsze daje te same liczby, na każdym komputerze – ważne w grze wieloosobowej, gdzie
  każdy przelicza rundę sam;
- kolejność obliczeń nie zmienia wyników – każde zdarzenie ma własny strumień;
- dodanie nowego losowania nie przesuwa liczb w innych strumieniach.

Cele są wymienione w `CELE` – literówka w nazwie celu to błąd, a nie cicho inny strumień.
Poza tym modułem silnik nie używa `numpy.random` ani `random` (pilnuje tego test).
"""
from __future__ import annotations

import hashlib
import json

import numpy as np

CELE = frozenset({
    "bot",         # decyzje bota: runda, nazwa firmy
    "biuro",       # błąd biura rachunkowego w deklaracji: runda, firma
    "dostawcy",    # ceny dostawców w trybie losowym: runda = miesiąc (0 = styczeń)
    "gazetki",     # promocje w gazetkach dyskontów: runda, dostawca
    "harpagon",    # wizyty Harpagona u dłużnika: runda, firma
    "kandydaci",   # rynek pracy: runda 0 = pula startowa
    "kolejnosc",   # kolejność firm w rundzie
    "parki",       # kolejność historii w parkach: runda = numer cyklu wszystkich historii
    "lokal",       # wybór lokalu przez bota: runda, nazwa firmy
    "popyt",       # szum popytu: runda, firma, usługa
    "reklamacje",  # reklamacje: runda, firma, usługa
    "rynek_pracy", # remisy w licytacjach i ofertach podkupienia: runda, rodzaj, id osoby
    "sanepid",     # kontrola sanepidu w lokalu (silnik/magazyn.py): runda, firma
    "reklama",     # tekst raportu agencji reklamowej (silnik/reklama.py): runda, firma, agencja, kanał
    "zdarzenia",   # ciąg dalszy historii z parku: runda, firma, historia
})


def strumien(ziarno: int | str, runda: int, cel: str, *klucze: int | str) -> np.random.Generator:
    if cel not in CELE:
        raise ValueError(f"nieznany cel losowania {cel!r} – dopisz go do CELE w silnik/losowosc.py")
    tekst = json.dumps([ziarno, runda, cel, *klucze], ensure_ascii=False)
    skrot = hashlib.sha256(tekst.encode("utf-8")).digest()
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(int.from_bytes(skrot, "little"))))
