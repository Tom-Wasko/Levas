"""Pomocniki wspólne dla testów: kopia danych do zmiany, gra z lokalami, runda z decyzjami, oferty i kandydaci.

Katalog `testy/` jest na ścieżce importu (pyproject.toml), więc testy z podfolderów piszą `from pomocnicze import …`.
"""
import shutil
from pathlib import Path

import yaml

from silnik import Gra
from silnik.dane import KATALOG_DANYCH, dane_domyslne
from silnik.ksiegowosc.finanse import vat_z_brutto


def _kopia(tmp_path: Path) -> Path:
    kat = tmp_path / "dane"
    shutil.copytree(KATALOG_DANYCH, kat)
    return kat


def _zmien(kat: Path, plik: str, zmiana) -> None:
    p = kat / plik
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    zmiana(d)
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _gra(*firmy, rund=8, **opcje):
    opcje.setdefault("kapital_startowy", 100000)   # testy kupna lokali i działek – kapitał większy niż domyślny
    return Gra.nowa("lokale", [(n, b) for n, b in firmy] or [("A", None), ("B", None)], rund, 1, **opcje)


def _runda(g, **decyzje):
    for firma, d in decyzje.items():
        g.ustaw_decyzje(firma, d)
    return g.przelicz(wymus=True)


def _lokal(id_, forma="najem"):
    return {"lokal": {"id": id_, "forma": forma}}


def _netto(brutto, stawka=0.23):
    """Kwota w KPiR gry z lokalami: ceny są brutto, VAT idzie do rejestru (F3a.11)."""
    return round(brutto - vat_z_brutto(brutto, stawka), 2)


def _rachunek(s, r, firma, poczatek):
    return [p["kwota"] for p in s.wyniki[r][firma]["rachunek"] if p["opis"].startswith(poczatek)]


KEBAB = "kebab_w_bulce"


def _oferta(strefa, cena_proc=1.0, jakosc=(2, 2, 2), **inne):
    d = dane_domyslne()
    cena = d.uslugi[KEBAB]["cena_preferowana"] * d.mapa["popyt"]["strefy"][strefa]["cena"] * cena_proc
    return {"strefa": strefa, "cena": cena, "jakosc": jakosc, **inne}


def _kandydat(s, gwiazdki, pomin=()):
    return next(k for k in s.kandydaci if k["gwiazdki"] == gwiazdki and k["zawod"] == "Kucharz" and k["id"] not in pomin)


def _z(k, nr, **kw):
    return {"kandydat": k["id"], "typ": "kuchnia", "nr": nr, **kw}
