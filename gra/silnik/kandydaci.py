"""Rynek pracy: kandydaci na instruktorów, trenerów personalnych i recepcjonistów.

Pula na start = znane osoby z gier (dane/kandydaci.json, pensje z rozrzutem jak między grami) + osoby wygenerowane
z rozkładów obserwowanych w grze. Co rundę dochodzą nowi kandydaci; każda firma widzi całą pulę
bez własnych pracowników (gra A/B/C: te same osoby zatrudnione przez drużyny A i C). Parametry wg gwiazdek (listy kandydatów i profile pracowników):
  1★: pensja 4785–4950, zadowolenie klientów 70–82%, ryzyko reklamacji 8–15%
  2★: pensja 5005–5170, 80–89%, 5–10%
  3★: pensja 5280–5500, 95–100%, 1–3%
  koszt rekrutacji 200–700, odprawa = 30/35/40/50/60% pensji preferowanej.
"""
from __future__ import annotations

from .dane import INSTRUKTOR, RECEPCJONISTA, TRENER, Dane
from .losowosc import generator

IMIONA_K = ["Anna", "Katarzyna", "Magdalena", "Agnieszka", "Joanna", "Monika", "Ewa", "Natalia", "Karolina", "Aleksandra",
            "Paulina", "Marta", "Zofia", "Weronika", "Julia", "Beata", "Iwona", "Justyna", "Sylwia", "Dorota"]
IMIONA_M = ["Piotr", "Krzysztof", "Tomasz", "Paweł", "Marcin", "Michał", "Jakub", "Adam", "Łukasz", "Mateusz",
            "Kamil", "Bartosz", "Rafał", "Grzegorz", "Wojciech", "Marek", "Dariusz", "Szymon", "Filip", "Damian"]
NAZWISKA = [("Kowalski", "Kowalska"), ("Wiśniewski", "Wiśniewska"), ("Wójcik", "Wójcik"), ("Kamiński", "Kamińska"),
            ("Lewandowski", "Lewandowska"), ("Zieliński", "Zielińska"), ("Szymański", "Szymańska"), ("Woźniak", "Woźniak"),
            ("Dąbrowski", "Dąbrowska"), ("Kozłowski", "Kozłowska"), ("Jankowski", "Jankowska"), ("Mazur", "Mazur"),
            ("Kwiatkowski", "Kwiatkowska"), ("Krawczyk", "Krawczyk"), ("Piotrowski", "Piotrowska"), ("Grabowski", "Grabowska"),
            ("Nowakowski", "Nowakowska"), ("Pawłowski", "Pawłowska"), ("Michalski", "Michalska"), ("Król", "Król"),
            ("Wieczorek", "Wieczorek"), ("Jabłoński", "Jabłońska"), ("Wróbel", "Wróbel"), ("Majewski", "Majewska")]
ROZKLAD = {1: {"pensja": (4785, 4950), "zk": (0.70, 0.82), "ryzyko": (0.08, 0.15)},
           2: {"pensja": (5005, 5170), "zk": (0.80, 0.89), "ryzyko": (0.05, 0.10)},
           3: {"pensja": (5280, 5500), "zk": (0.95, 1.00), "ryzyko": (0.01, 0.03)}}
ZAWODY = (INSTRUKTOR, TRENER, RECEPCJONISTA)
NA_START = 12         # wygenerowanych kandydatów każdego zawodu na początku gry
CO_RUNDE = 6          # nowych kandydatów każdego zawodu w każdej rundzie (ATH zatrudnił 18 osób w 5 miesięcy)
WIEK = (22, 50)


def _osoba(rng, zawod: str, gwiazdki: int, id_: str, uzyte: set[str]) -> dict:
    for _ in range(50):
        kobieta = rng.random() < 0.55
        imie = rng.choice(IMIONA_K if kobieta else IMIONA_M)
        nazwisko = NAZWISKA[rng.integers(len(NAZWISKA))][1 if kobieta else 0]
        pelne = f"{imie} {nazwisko}"
        if pelne not in uzyte:
            break
    uzyte.add(pelne)
    r = ROZKLAD[gwiazdki]
    pensja = int(round(rng.uniform(*r["pensja"]) / 5) * 5)
    return {"id": id_, "imie_nazwisko": pelne, "gwiazdki": gwiazdki, "zawod": zawod, "pensja_preferowana": pensja,
            "koszt_rekrutacji": int(rng.choice([200, 250, 300, 350, 400, 500, 600, 700])),
            "koszt_odprawy": round(pensja * rng.choice([0.30, 0.35, 0.40, 0.50, 0.60])),
            "zadowolenie_klientow": round(rng.uniform(*r["zk"]), 2), "ryzyko_reklamacji": round(rng.uniform(*r["ryzyko"]), 2),
            "wiek": int(rng.integers(*WIEK))}


def _gwiazdki(rng) -> int:
    return int(rng.choice([1, 2, 3], p=[0.45, 0.40, 0.15]))


def pula_startowa(dane: Dane, ziarno) -> list[dict]:
    rng = generator(ziarno, "kandydaci", 0)
    rozrzut = dane.z["losowosc"]["kandydaci"]["rozrzut_pensji"]
    uzyte, pula = set(), []
    for i, k in enumerate(dane.kandydaci):
        o = dict(k)
        o["id"] = f"z{i}"
        o["pensja_preferowana"] = int(round(k["pensja_preferowana"] * (1 + rng.uniform(-rozrzut, rozrzut)) / 5) * 5)
        o["wiek"] = int(rng.integers(*WIEK))
        uzyte.add(o["imie_nazwisko"])
        pula.append(o)
    for zawod in ZAWODY:
        for j in range(NA_START):
            pula.append(_osoba(rng, zawod, _gwiazdki(rng), f"g0-{zawod[:3]}-{j}", uzyte))
    return pula


def dodaj_nowych(pula: list[dict], ziarno, runda: int) -> list[dict]:
    rng = generator(ziarno, "kandydaci", runda)
    uzyte = {o["imie_nazwisko"] for o in pula}
    nowi = [_osoba(rng, zawod, _gwiazdki(rng), f"g{runda}-{zawod[:3]}-{j}", uzyte)
            for zawod in ZAWODY for j in range(CO_RUNDE)]
    return pula + nowi
