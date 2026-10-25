"""Serwer lokalnej gry REVAS Klub Fitness (Flask). Start: start.bat albo
    .venv/Scripts/python -m serwer.app            (z folderu revas_gra)
Gry zapisują się w gra/zapisy/<id>.json.
"""
from __future__ import annotations

import json
import re
import secrets
import threading
import webbrowser
from copy import deepcopy
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file

from silnik.boty import STRATEGIE
from silnik.dane import dane_domyslne
from silnik.gra import Gra
from silnik.runda import przelicz_runde

from .widoki import katalogi, widok

KATALOG = Path(__file__).resolve().parents[1]
ZAPISY = KATALOG / "zapisy"
ZAPISY.mkdir(exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.json.ensure_ascii = False
_blokada = threading.Lock()
_gry: dict[str, Gra] = {}


def _plik(id_: str) -> Path:
    if not re.fullmatch(r"[\w\-]+", id_):
        abort(404)
    return ZAPISY / f"{id_}.json"


def gra(id_: str) -> Gra:
    if id_ not in _gry:
        p = _plik(id_)
        if not p.exists():
            abort(404, "Nie ma takiej gry.")
        _gry[id_] = Gra.wczytaj(p)
    return _gry[id_]


def zapisz(id_: str) -> None:
    _gry[id_].zapisz(_plik(id_))


def blad(tekst: str, kod: int = 400):
    return jsonify({"blad": tekst}), kod


# --- strony ------------------------------------------------------------------------------------
@app.get("/")
def start():
    return render_template("start.html", strategie={k: v["nazwa"] for k, v in STRATEGIE.items()})


@app.get("/gra/<id_>")
def wybor_firmy(id_):
    g = gra(id_)
    ludzie = [f["nazwa"] for f in g.konfiguracja["firmy"] if not f["bot"]]
    if len(ludzie) == 1:
        return redirect(f"/gra/{id_}/{ludzie[0]}")
    return render_template("wybor.html", id=id_, gra=g.konfiguracja, ludzie=ludzie)


@app.get("/gra/<id_>/<firma>")
def strona_gry(id_, firma):
    g = gra(id_)
    if firma not in {f["nazwa"] for f in g.konfiguracja["firmy"]}:
        abort(404)
    return render_template("gra.html", id=id_, firma=firma)


# --- API ---------------------------------------------------------------------------------------
@app.get("/api/katalogi")
def api_katalogi():
    return jsonify(katalogi(dane_domyslne()))


@app.get("/api/gry")
def api_gry():
    wynik = []
    for p in sorted(ZAPISY.glob("*.json"), key=lambda p: -p.stat().st_mtime):
        try:
            k = json.loads(p.read_text(encoding="utf-8"))
            konf, dec = k["konfiguracja"], k.get("decyzje", {})
            runda = 1 + max((int(r) for r, d in dec.items() if d.get("_przeliczona")), default=0)
            wynik.append({"id": p.stem, "nazwa": konf["nazwa"], "runda": runda, "liczba_rund": konf["liczba_rund"],
                          "firmy": konf["firmy"]})
        except (json.JSONDecodeError, KeyError):
            continue
    return jsonify(wynik)


@app.post("/api/gry")
def api_nowa_gra():
    d = request.get_json(force=True)
    wiersze = [f for f in d.get("firmy", []) if f.get("nazwa", "").strip()]
    firmy = [(f["nazwa"].strip(), f.get("bot") or None) for f in wiersze]
    if not firmy or len({n for n, _ in firmy}) != len(firmy):
        return blad("Podaj różne nazwy firm.")
    if not any(b is None for _, b in firmy):
        return blad("Co najmniej jedna firma musi być prowadzona przez gracza.")
    ziarno = d.get("ziarno")
    g = Gra.nowa(d.get("nazwa") or "Gra", firmy, int(d.get("liczba_rund") or 12),
                 int(ziarno) if str(ziarno or "").strip().isdigit() else None,
                 ceny_dostawcow=d.get("ceny_dostawcow", "dane"),
                 kredyt_odnawialny=d.get("kredyt_odnawialny", "jednoczesnie"))
    id_ = re.sub(r"[^\w]+", "-", g.konfiguracja["nazwa"].lower()).strip("-")[:30] + "-" + secrets.token_hex(3)
    with _blokada:
        _gry[id_] = g
        zapisz(id_)
    return jsonify({"id": id_})


@app.delete("/api/gry/<id_>")
def api_usun(id_):
    with _blokada:
        _gry.pop(id_, None)
        p = _plik(id_)
        if p.exists():
            p.unlink()
    return jsonify({"ok": True})


@app.get("/api/gry/<id_>/widok/<firma>")
def api_widok(id_, firma):
    runda = request.args.get("runda", type=int)
    return jsonify(widok(gra(id_), firma, runda))


@app.put("/api/gry/<id_>/decyzje/<firma>")
def api_decyzje(id_, firma):
    g = gra(id_)
    if g.zakonczona:
        return blad("Gra jest zakończona.")
    if firma in g.wyslane():
        return blad("Decyzje są wysłane – najpierw wróć do podejmowania decyzji.")
    with _blokada:
        g.ustaw_decyzje(firma, request.get_json(force=True))
        zapisz(id_)
    return jsonify(widok(g, firma))


@app.post("/api/gry/<id_>/wyslij/<firma>")
def api_wyslij(id_, firma):
    g = gra(id_)
    wyslane = bool((request.get_json(silent=True) or {}).get("wyslane", True))
    przeliczono = False
    with _blokada:
        g.wyslij(firma, wyslane)
        if wyslane and not g.brakujace() and not g.zakonczona:
            g.przelicz()
            przeliczono = True
        zapisz(id_)
    v = widok(g, firma)
    v["przeliczono"] = przeliczono
    return jsonify(v)


@app.post("/api/gry/<id_>/przelicz")
def api_przelicz(id_):
    g = gra(id_)
    if g.zakonczona:
        return blad("Gra jest zakończona.")
    with _blokada:
        g.przelicz(wymus=True)
        zapisz(id_)
    return jsonify({"ok": True, "runda": g.runda})


@app.post("/api/gry/<id_>/cofnij")
def api_cofnij(id_):
    g = gra(id_)
    with _blokada:
        g.cofnij()
        zapisz(id_)
    return jsonify({"ok": True, "runda": g.runda})


def _warianty(g: Gra, firma: str) -> dict:
    return g.decyzje.setdefault(g.runda, {}).setdefault("_warianty", {}).setdefault(firma, {})


@app.put("/api/gry/<id_>/warianty/<firma>")
def api_zapisz_wariant(id_, firma):
    """Zapisuje bieżące robocze decyzje (albo podane) jako nazwany wariant do porównania w Analizie."""
    g = gra(id_)
    d = request.get_json(force=True)
    nazwa = (d.get("nazwa") or "").strip()[:40]
    if not nazwa:
        return blad("Podaj nazwę wariantu.")
    with _blokada:
        _warianty(g, firma)[nazwa] = d.get("decyzje") or deepcopy(g.szkic(firma))
        zapisz(id_)
    return jsonify(widok(g, firma))


@app.delete("/api/gry/<id_>/warianty/<firma>")
def api_usun_wariant(id_, firma):
    g = gra(id_)
    with _blokada:
        _warianty(g, firma).pop(request.args.get("nazwa", ""), None)
        zapisz(id_)
    return jsonify(widok(g, firma))


@app.get("/api/gry/<id_>/warianty-dane/<firma>")
def api_dane_wariantu(id_, firma):
    w = _warianty(gra(id_), firma).get(request.args.get("nazwa", ""))
    return jsonify(w) if w is not None else blad("Nie ma takiego wariantu.", 404)


@app.post("/api/gry/<id_>/podglad/<firma>")
def api_podglad(id_, firma):
    """Przewidywany wynik bieżącej rundy dla decyzji (bez zapisu). Boty decydują jak zwykle, pozostali gracze –
    według swoich roboczych decyzji. Body: {"warianty": [nazwa wariantu albo "biezace"]} – domyślnie bieżące."""
    g = gra(id_)
    if g.zakonczona:
        return blad("Gra jest zakończona.")
    kopia = g.kopia()
    nazwy = (request.get_json(silent=True) or {}).get("warianty") or ["biezace"]
    zapisane = _warianty(kopia, firma)
    warianty = [g.szkic(firma) if n == "biezace" else zapisane[n] for n in nazwy if n == "biezace" or n in zapisane]
    wyniki = []
    stan = kopia.stan(kopia.runda - 1)
    from silnik.boty import decyzje_bota
    r = kopia.runda
    baza = {f["nazwa"]: (decyzje_bota(kopia.dane, stan, f["nazwa"], f["bot"], r, kopia.konfiguracja) if f["bot"]
                         else kopia.szkic(f["nazwa"])) for f in kopia.konfiguracja["firmy"]}
    for nazwa, wariant in zip([n for n in nazwy if n == "biezace" or n in zapisane], warianty):
        dec = deepcopy(baza)
        dec[firma] = wariant
        s = przelicz_runde(kopia.dane, stan, dec, kopia.konfiguracja)
        wyniki.append({"nazwa": "Bieżące decyzje" if nazwa == "biezace" else nazwa,
                       "wyniki": s.wyniki[r][firma], "rynek": s.rynek[r]})
    return jsonify({"runda": r, "warianty": wyniki})


@app.get("/api/gry/<id_>/eksport")
def api_eksport(id_):
    gra(id_)
    return send_file(_plik(id_), as_attachment=True, download_name=f"{id_}.json")


@app.post("/api/gry/import")
def api_import():
    plik = request.files.get("plik")
    if not plik:
        return blad("Brak pliku.")
    try:
        d = json.loads(plik.read().decode("utf-8"))
        g = Gra(d["konfiguracja"], d.get("decyzje"))
    except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
        return blad("To nie jest plik gry.")
    id_ = re.sub(r"[^\w]+", "-", g.konfiguracja["nazwa"].lower()).strip("-")[:30] + "-" + secrets.token_hex(3)
    with _blokada:
        _gry[id_] = g
        zapisz(id_)
    return jsonify({"id": id_})


def uruchom(port: int = 8765, otworz: bool = True):
    if otworz:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}/")).start()
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    uruchom()
