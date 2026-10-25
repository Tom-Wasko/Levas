"""Losowość z ziarnem: ten sam (ziarno gry, runda, firma, zdarzenie) zawsze daje te same liczby.

Każde zdarzenie dostaje własny generator, więc kolejność obliczeń nie zmienia wyników – ważne w grze
wieloosobowej, gdzie każdy komputer przelicza rundę sam.
"""
from __future__ import annotations

import hashlib

import numpy as np


def generator(ziarno: int | str, *klucze) -> np.random.Generator:
    tekst = "|".join(str(k) for k in (ziarno, *klucze))
    return np.random.default_rng(int.from_bytes(hashlib.sha256(tekst.encode("utf-8")).digest()[:8], "little"))
