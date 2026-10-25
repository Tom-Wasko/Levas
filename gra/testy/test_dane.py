"""Dane gry w `dane/*.yaml`: schematy, odwołania między plikami, `python -m silnik.dane sprawdz`
i brak liczb gry w kodzie silnika."""

import ast
import shutil
from pathlib import Path

import pytest
import yaml

from silnik import dane as modul_danych
from silnik.dane import KATALOG_DANYCH, KATALOG_REVAS, Dane, sprawdz

SILNIK = Path(modul_danych.__file__).parent

# Liczby, które mogą być w kodzie silnika, bo opisują budowę modelu, a nie grę: indeksy i kroki, jakość
# 1–3, procent, 12 miesięcy w roku, grosze, dokładność zaokrągleń i porównań, limity pętli numerycznych.
DOZWOLONE_LICZBY = {0, 1, 2, 3, 4, 9, 10, 12, 50, 60, 100, 0.005, 0.01, 1e-9, 1e-7, 1e-6, 1e6,
                    6, 7, 52}  # kalendarz: dni tygodnia, tygodnie w roku


def _kopia(tmp_path: Path) -> Path:
    kat = tmp_path / "dane"
    shutil.copytree(KATALOG_DANYCH, kat)
    return kat


def _zmien(kat: Path, plik: str, zmiana) -> None:
    p = kat / plik
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    zmiana(d)
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_dane_gry_sa_poprawne():
    assert sprawdz() == []
    assert sprawdz(KATALOG_REVAS) == []   # wzorzec REVAS (fitness) do testów mechaniki


def test_kazdy_plik_ma_opis_i_zrodlo():
    d = Dane()
    assert set(d.pliki) >= {"uslugi.yaml", "katalog.yaml", "zalozenia.yaml", "boty.yaml"}
    for nazwa, tresc in d.pliki.items():
        assert tresc.get("opis"), nazwa
        # katalog i założenia mają źródło przy każdej sekcji / parametrze
        if nazwa not in ("katalog.yaml", "zalozenia.yaml"):
            assert tresc.get("zrodlo"), nazwa
    for sekcja, v in d.katalog_ofert.items():
        if isinstance(v, dict):
            assert v.get("zrodlo"), sekcja


@pytest.mark.parametrize(
    ("plik", "zmiana", "oczekiwany"),
    [
        ("uslugi.yaml", lambda d: d.pop("zrodlo"), "uslugi.yaml: zrodlo"),
        ("sprzet.yaml", lambda d: d["sprzet"]["Rożen"].update(kolor="czerwony"), "kolor"),
        ("uslugi.yaml", lambda d: d["uslugi"]["falafel"]["sprzet"].append("Kasa fiskalna"), "Kasa fiskalna"),
        ("uslugi.yaml", lambda d: d["uslugi"]["falafel"]["zasoby"].update({"Lawasz": 1}), "Lawasz"),
        ("katalog.yaml", lambda d: d["banki"].pop("zrodlo"), "katalog.yaml: banki.zrodlo"),
        ("kandydaci.yaml", lambda d: d["losowanie"]["gwiazdki"].update({"3": 0.5}), "sumować"),
        (
            "boty.yaml",
            lambda d: d["strategie"]["tani"]["reklama"].update({"Gazeta X": 1}),
            "Gazeta X",
        ),
        (
            "zalozenia.yaml",
            lambda d: d["finanse"]["podatek_cit"].update(pewnosc="chyba"),
            "finanse.podatek_cit",
        ),
        ("zalozenia.yaml", lambda d: d["finanse"]["podatek_cit"].pop("zrodlo"), "podatek_cit"),
    ],
)
def test_sprawdz_wykrywa_bledy(tmp_path, plik, zmiana, oczekiwany):
    kat = _kopia(tmp_path)
    _zmien(kat, plik, zmiana)
    bledy = sprawdz(kat)
    assert any(oczekiwany in b for b in bledy), bledy


def test_brak_pliku_i_komenda(tmp_path, capsys):
    assert modul_danych.main(["sprawdz"]) == 0
    assert "Dane w porządku" in capsys.readouterr().out
    kat = _kopia(tmp_path)
    (kat / "boty.yaml").unlink()
    assert sprawdz(kat) == ["brak pliku dane/boty.yaml"]
    assert modul_danych.main(["sprawdz", str(kat)]) == 1
    assert modul_danych.main([]) == 2


def test_wersja_zalezy_od_danych(tmp_path):
    kat = _kopia(tmp_path)
    przed = Dane(kat).wersja
    assert przed == Dane().wersja
    _zmien(kat, "boty.yaml", lambda d: d["ustawienia"].update(bufor_gotowki=1))
    assert Dane(kat).wersja != przed


def test_w_kodzie_silnika_nie_ma_liczb_gry():
    """Parametry gry są w `dane/*.yaml` – w kodzie silnika zostają tylko liczby budowy modelu."""
    obce = []
    for plik in sorted(SILNIK.glob("*.py")):
        for wezel in ast.walk(ast.parse(plik.read_text(encoding="utf-8"))):
            if isinstance(wezel, ast.Constant) and type(wezel.value) in (int, float):
                if wezel.value not in DOZWOLONE_LICZBY:
                    obce.append(f"{plik.name}:{wezel.lineno}: {wezel.value}")
    assert obce == []
