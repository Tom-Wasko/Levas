"""B10: mnożnik wyposażenia – liniowy bez `wyposazenie_nasycenie`, z nim malejące korzyści z kolejnych sztuk."""
import copy
import math

from silnik.dane import dane_domyslne
from silnik.kuchnia.jakosc import mnoznik_wyposazenia


def _z_nasyceniem(s):
    dane = copy.copy(dane_domyslne())
    dane.z = {**dane.z, "popyt": {**dane.z["popyt"], "wyposazenie_nasycenie": s}}
    return dane


def test_bez_nasycenia_liniowo():
    dane = dane_domyslne()
    k = dane.z["popyt"]["wyposazenie_na_procent_klientow"]
    poz = dane.pozycje("wyposazenie")
    wsz = list(poz)
    assert math.isclose(mnoznik_wyposazenia(dane, wsz), 1 + k * sum(p["procent"] for p in poz.values()) / 100)
    assert mnoznik_wyposazenia(dane, []) == 1.0


def test_nasycenie_kolejne_sztuki_daja_mniej():
    dane = _z_nasyceniem(3.0)
    k = dane.z["popyt"]["wyposazenie_na_procent_klientow"]
    poz = sorted(dane.pozycje("wyposazenie").values(), key=lambda p: -p["procent"])
    nazwy = [p["nazwa"] for p in poz]
    m = [mnoznik_wyposazenia(dane, nazwy[:i]) for i in range(len(nazwy) + 1)]
    x = sum(p["procent"] for p in poz) / 100
    assert math.isclose(m[-1], 1 + k * 3.0 * (1 - math.exp(-x / 3.0)))
    assert m[-1] < 1 + k * x                                     # komplet słabiej niż liniowo
    assert m[1] - 1 > 0.85 * k * poz[0]["procent"] / 100          # pierwsza sztuka prawie jak liniowo
    prz = [(b - a) / (p["procent"] / 100) for a, b, p in zip(m, m[1:], poz)]
    assert all(b < a for a, b in zip(prz, prz[1:]))               # każdy kolejny procent klientów daje mniej
