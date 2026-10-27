"""Instrukcja dla graczy: INSTRUKCJA.md → HTML strony „Jak grać” (i PDF, komenda `instrukcja_pdf`).

Mały konwerter tylko dla składni używanej w instrukcji: nagłówki #/##/###, akapity, listy (- i 1.),
tabele |…|, cytaty > (ramki z radami), linia ---, **pogrubienie**, *kursywa*, `kod` i [link](adres).
"""

from __future__ import annotations

import html
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings

PLIK = Path(settings.BASE_DIR) / "INSTRUKCJA.md"
LISTA = r"(- |\d+\. )"
NOWY_BLOK = r"(#{1,3} |>|\||- |\d+\. |---)"


def _kotwica(tekst: str) -> str:
    return re.sub(r"[^\w]+", "-", tekst.lower()).strip("-")


def _w_linii(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t)
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)


def _bloki(linie: list[str], spis: list[dict]) -> str:
    wynik, i = [], 0
    while i < len(linie):
        w = linie[i]
        if not w.strip():
            i += 1
        elif m := re.match(r"(#{1,3}) (.+)", w):
            poziom, tekst = len(m[1]), m[2].strip()
            k = _kotwica(tekst)
            if poziom == 2:
                spis.append({"kotwica": k, "tytul": tekst})
            wynik.append(f'<h{poziom} id="{k}">{_w_linii(tekst)}</h{poziom}>')
            i += 1
        elif w.strip() == "---":
            wynik.append("<hr>")
            i += 1
        elif w.startswith(">"):
            cytat = []
            while i < len(linie) and linie[i].startswith(">"):
                cytat.append(linie[i][1:].removeprefix(" "))
                i += 1
            klasa = "uwaga" if cytat[0].startswith("**Uwaga") else "rada"
            wynik.append(f'<div class="ramka {klasa}">{_bloki(cytat, [])}</div>')
        elif w.startswith("|"):
            wiersze = []
            while i < len(linie) and linie[i].startswith("|"):
                wiersze.append([k.strip() for k in linie[i].strip().strip("|").split("|")])
                i += 1
            glowa = "".join(f"<th>{_w_linii(k)}</th>" for k in wiersze[0])
            cialo = "".join("<tr>" + "".join(f"<td>{_w_linii(k)}</td>" for k in r) + "</tr>"
                            for r in wiersze[2:])
            wynik.append(f'<div class="tabela"><table><thead><tr>{glowa}</tr></thead>'
                         f'<tbody>{cialo}</tbody></table></div>')
        elif re.match(r"(- |\d+\. )", w):
            znacznik = "ol" if w[0].isdigit() else "ul"
            punkty = []
            while i < len(linie) and (re.match(LISTA, linie[i]) or linie[i].startswith("  ")):
                if linie[i].startswith("  ") and punkty:
                    punkty[-1].append(linie[i].strip())
                else:
                    punkty.append([re.sub(r"^(- |\d+\. )", "", linie[i])])
                i += 1
            wynik.append(f"<{znacznik}>" + "".join(_punkt(p) for p in punkty) + f"</{znacznik}>")
        else:
            akapit = []
            while i < len(linie) and linie[i].strip() and not re.match(NOWY_BLOK, linie[i]):
                akapit.append(linie[i].strip())
                i += 1
            wynik.append(f"<p>{_w_linii(' '.join(akapit))}</p>")
    return "\n".join(wynik)


def _punkt(linie: list[str]) -> str:
    """Punkt listy: tekst i zagnieżdżona lista „  - …” (jeden poziom)."""
    tekst = [x for x in linie if not x.startswith("- ")]
    pod = [x[2:] for x in linie if x.startswith("- ")]
    podlista = "".join(f"<li>{_w_linii(x)}</li>" for x in pod)
    podlista = f"<ul>{podlista}</ul>" if pod else ""
    return f"<li>{_w_linii(' '.join(tekst))}{podlista}</li>"


def na_html(tekst: str) -> dict:
    """{"tytul", "tresc" (HTML bez tytułu), "spis" ([{kotwica, tytul}] rozdziałów ##)}."""
    linie = tekst.replace("\r\n", "\n").split("\n")
    ma_tytul = linie[0].startswith("# ")
    tytul = linie[0].removeprefix("# ").strip() if ma_tytul else "Instrukcja"
    spis: list[dict] = []
    tresc = _bloki(linie[1:] if ma_tytul else linie, spis)
    return {"tytul": tytul, "tresc": tresc, "spis": spis}


@lru_cache(maxsize=4)
def _wczytaj(zmiana: float) -> dict:
    return na_html(PLIK.read_text(encoding="utf-8"))


def instrukcja() -> dict:
    return _wczytaj(PLIK.stat().st_mtime)   # nowa wersja pliku – nowy HTML bez restartu serwera
