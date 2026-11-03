"""U4: nazwy zakładek w tekstach silnika i danych (komunikaty, lista błędów, wnioski, zdarzenia) istnieją w panelu
gracza – po przebudowie menu (2.11.2026) zostały stare nazwy („Kadry”, „(Inwestycje)” przy stanowiskach)."""

import io
import re
import tokenize
from pathlib import Path

import yaml

GRA = Path(__file__).resolve().parents[2]
ZAKLADKI = GRA / "panel_gracza" / "static" / "zakladki"
SLOWO = r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+"
WIELKA = r"[A-ZĄĆĘŁŃÓŚŹŻ]"
STARE = re.compile(r"\((?:Kadry|Inwestycje|HR|Oferta)\)|zakład\w* (?:Kadry|HR|Oferta)\b")
ZAKLADKA = re.compile(rf"zakład(?:ce|ka|kę|ki) ({WIELKA}{SLOWO}(?: {SLOWO}){{0,3}})")
SCIEZKA = re.compile(rf"((?:{SLOWO} ){{0,3}}{SLOWO}) ▸ ({WIELKA}{SLOWO}(?: {SLOWO}){{0,3}})")


def _tytuly() -> tuple[set[str], set[str]]:
    """Tytuły pozycji menu (najwyższy poziom) i wszystkich zakładek."""
    menu = set(re.findall(r'\{ klucz: "\w+", tytul: "([^"]+)"', (ZAKLADKI / "index.js").read_text(encoding="utf-8")))
    wszystkie = set(menu)
    for plik in ZAKLADKI.glob("*.js"):
        wszystkie |= set(re.findall(r'\btytul: "([^"]+)"', plik.read_text(encoding="utf-8")))
    return menu, wszystkie


def _teksty_py(plik: Path):
    kod = plik.read_text(encoding="utf-8")
    typy = {tokenize.STRING} | {getattr(tokenize, t) for t in ("FSTRING_MIDDLE",) if hasattr(tokenize, t)}
    for t in tokenize.generate_tokens(io.StringIO(kod).readline):
        if t.type in typy:
            yield t.start[0], t.string


def _teksty_yaml(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from _teksty_yaml(v)
    elif isinstance(x, list):
        for v in x:
            yield from _teksty_yaml(v)


def _wszystkie_teksty():
    for katalog in ("silnik", "api"):
        for plik in sorted((GRA / katalog).rglob("*.py")):
            for nr, t in _teksty_py(plik):
                yield f"{plik.relative_to(GRA)}:{nr}", " ".join(t.split())
    menu = "|".join(sorted(map(re.escape, _tytuly()[0]), key=len, reverse=True))
    for plik in sorted((GRA / "panel_gracza" / "static").rglob("*.js")):   # panel: też „Menu → zakładka” (bez strzałek w schematach)
        if "vendor" not in plik.parts:
            for nr, linia in enumerate(plik.read_text(encoding="utf-8").splitlines(), 1):
                if not linia.lstrip().startswith("//"):
                    yield f"{plik.relative_to(GRA)}:{nr}", re.sub(rf"\b({menu}) → ", r"\1 ▸ ", re.sub(r"<[^>]+>", "", linia))
    for plik in sorted((GRA / "dane").rglob("*.yaml")):
        for t in _teksty_yaml(yaml.safe_load(plik.read_text(encoding="utf-8"))):
            yield str(plik.relative_to(GRA)), " ".join(t.split())


def _prefiks_jest(slowa: list[str], tytuly: set[str]) -> bool:
    return any(" ".join(slowa[:n]) in tytuly for n in range(1, len(slowa) + 1))


def test_nazwy_zakladek_w_tekstach_istnieja_w_menu():
    menu, wszystkie = _tytuly()
    assert {"Lokale", "Inwestycje", "Finanse", "Księgowość"} <= menu and {"Sprzęt", "Ludzie", "Biuro rachunkowe"} <= wszystkie
    zle = []
    for gdzie, t in _wszystkie_teksty():
        zle += [f"{gdzie}: {m.group(0)}" for m in STARE.finditer(t)]
        zle += [f"{gdzie}: zakładka {m.group(1)}" for m in ZAKLADKA.finditer(t)
                if not _prefiks_jest(m.group(1).split(), wszystkie)]
        for m in SCIEZKA.finditer(t):
            lewa = m.group(1).split()
            if not any(" ".join(lewa[-n:]) in menu for n in range(1, len(lewa) + 1)) \
                    or not _prefiks_jest(m.group(2).split(), wszystkie):
                zle.append(f"{gdzie}: {m.group(0)}")
    assert not zle, "Nieistniejące zakładki:\n" + "\n".join(zle)
