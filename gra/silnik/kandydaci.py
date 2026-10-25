"""Rynek pracy: kandydaci na instruktorów, trenerów personalnych i recepcjonistów.

Pula na start = znane osoby z gier (dane/kandydaci.yaml: znani, pensje z rozrzutem jak między grami) + osoby
wygenerowane z rozkładów obserwowanych w grze (kandydaci.yaml: losowanie – pensja, zadowolenie klientów i ryzyko
reklamacji wg gwiazdek, koszt rekrutacji, odprawa). Co rundę dochodzą nowi kandydaci; każda firma widzi całą pulę
bez własnych pracowników (gra A/B/C: te same osoby zatrudnione przez drużyny A i C).
"""
from __future__ import annotations

from .dane import ZAWODY, Dane
from .losowosc import generator


def _osoba(dane: Dane, rng, zawod: str, gwiazdki: int, id_: str, uzyte: set[str]) -> dict:
    rp = dane.rynek_pracy
    los = rp["losowanie"]
    for _ in range(50):
        kobieta = rng.random() < los["udzial_kobiet"]
        imie = rng.choice(rp["imiona_kobiet"] if kobieta else rp["imiona_mezczyzn"])
        nazwisko = rp["nazwiska"][rng.integers(len(rp["nazwiska"]))]["k" if kobieta else "m"]
        pelne = f"{imie} {nazwisko}"
        if pelne not in uzyte:
            break
    uzyte.add(pelne)
    r = los["wg_gwiazdek"][str(gwiazdki)]
    krok = los["krok_pensji"]
    pensja = int(round(rng.uniform(*r["pensja"]) / krok) * krok)
    return {"id": id_, "imie_nazwisko": pelne, "gwiazdki": gwiazdki, "zawod": zawod, "pensja_preferowana": pensja,
            "koszt_rekrutacji": int(rng.choice(los["koszty_rekrutacji"])),
            "koszt_odprawy": round(pensja * rng.choice(los["odprawa_czesc_pensji"])),
            "zadowolenie_klientow": round(rng.uniform(*r["zk"]), 2), "ryzyko_reklamacji": round(rng.uniform(*r["ryzyko"]), 2),
            "wiek": int(rng.integers(*los["wiek"]))}


def _gwiazdki(dane: Dane, rng) -> int:
    p = dane.rynek_pracy["losowanie"]["gwiazdki"]
    return int(rng.choice([int(g) for g in p], p=list(p.values())))


def pula_startowa(dane: Dane, ziarno) -> list[dict]:
    rng = generator(ziarno, "kandydaci", 0)
    rozrzut = dane.z["losowosc"]["kandydaci"]["rozrzut_pensji"]
    krok = dane.rynek_pracy["losowanie"]["krok_pensji"]
    uzyte, pula = set(), []
    for i, k in enumerate(dane.kandydaci):
        o = dict(k)
        o["id"] = f"z{i}"
        o["pensja_preferowana"] = int(round(k["pensja_preferowana"] * (1 + rng.uniform(-rozrzut, rozrzut)) / krok) * krok)
        o["wiek"] = int(rng.integers(*dane.rynek_pracy["losowanie"]["wiek"]))
        uzyte.add(o["imie_nazwisko"])
        pula.append(o)
    for zawod in ZAWODY:
        for j in range(dane.rynek_pracy["losowanie"]["na_start"]):
            pula.append(_osoba(dane, rng, zawod, _gwiazdki(dane, rng), f"g0-{zawod[:3]}-{j}", uzyte))
    return pula


def dodaj_nowych(dane: Dane, pula: list[dict], ziarno, runda: int) -> list[dict]:
    rng = generator(ziarno, "kandydaci", runda)
    uzyte = {o["imie_nazwisko"] for o in pula}
    nowi = [_osoba(dane, rng, zawod, _gwiazdki(dane, rng), f"g{runda}-{zawod[:3]}-{j}", uzyte)
            for zawod in ZAWODY for j in range(dane.rynek_pracy["losowanie"]["co_runde"])]
    return pula + nowi
