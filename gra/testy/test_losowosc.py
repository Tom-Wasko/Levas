"""Nazwane strumienie losowości (PCG64): powtarzalność, niezależność i jedno źródło losowości."""

import ast
from pathlib import Path

import pytest

from silnik import Gra
from silnik.losowosc import CELE, strumien

SILNIK = Path(strumien.__code__.co_filename).parent


def test_wartosci_wzorcowe():
    """Te same liczby co przy pisaniu testu – złapie zmianę algorytmów numpy lub wyprowadzania ziarna."""
    g = strumien(12345, 1, "popyt", "Firma A", "joga")
    assert g.random(3).tolist() == pytest.approx(
        [0.07309083083645984, 0.8353699855657901, 0.38613564018605095], abs=1e-15
    )
    assert g.normal(0, 1, 2).tolist() == pytest.approx(
        [0.3894555552258837, 0.33286238539544516], abs=1e-15
    )
    assert int(g.binomial(20, 0.3)) == 7
    assert g.permutation(["A", "B", "C", "D"]).tolist() == ["B", "C", "D", "A"]
    assert int(g.integers(0, 1000)) == 221
    assert strumien("abc", 0, "kandydaci").random() == pytest.approx(0.6957282352347165, abs=1e-15)


def test_ten_sam_strumien_te_same_liczby_niezaleznie_od_kolejnosci():
    a = strumien(7, 2, "reklamacje", "F1", "joga").random(5).tolist()
    for cel in sorted(CELE):  # inne losowania pomiędzy nie zmieniają wyniku
        strumien(7, 2, cel, "F1").random(100)
    assert strumien(7, 2, "reklamacje", "F1", "joga").random(5).tolist() == a


@pytest.mark.parametrize(
    "inny",
    [
        (8, 2, "reklamacje", "F1", "joga"),
        (7, 3, "reklamacje", "F1", "joga"),
        (7, 2, "popyt", "F1", "joga"),
        (7, 2, "reklamacje", "F2", "joga"),
        (7, 2, "reklamacje", "F1|joga"),  # klucze nie sklejają się w jeden
        ("7", 2, "reklamacje", "F1", "joga"),
    ],
)
def test_rozne_strumienie_rozne_liczby(inny):
    assert (
        strumien(*inny).random(3).tolist()
        != strumien(7, 2, "reklamacje", "F1", "joga").random(3).tolist()
    )


def test_nieznany_cel():
    with pytest.raises(ValueError, match="CELE"):
        strumien(1, 1, "popytt")


def test_gra_powtarzalna_i_zalezna_od_ziarna():
    def gra(ziarno):
        g = Gra.nowa("Test", [("A", "tani"), ("B", "premium"), ("C", "nasladowca")], 3, ziarno)
        for _ in range(3):
            g.przelicz()
        return g.stan().model_dump_json()

    assert gra(5) == gra(5)
    assert gra(5) != gra(6)


def test_losowosc_tylko_z_modulu_losowosc():
    obce = []
    for plik in sorted(SILNIK.glob("*.py")):
        if plik.name == "losowosc.py":
            continue
        for w in ast.walk(ast.parse(plik.read_text(encoding="utf-8"))):
            if isinstance(w, ast.Import | ast.ImportFrom):
                nazwy = [a.name for a in w.names] + [getattr(w, "module", None) or ""]
                if any(n == "random" or n.startswith("numpy.random") for n in nazwy):
                    obce.append(f"{plik.name}:{w.lineno}")
            elif (
                isinstance(w, ast.Attribute)
                and w.attr == "random"
                and isinstance(w.value, ast.Name)
                and w.value.id in ("np", "numpy")
            ):
                obce.append(f"{plik.name}:{w.lineno}")
    assert obce == []
