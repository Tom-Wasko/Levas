"""Odcisk (skrót) stanów gier botów po każdej rundzie – kontrola, że przyspieszenie silnika albo
przeniesienie kodu bez zmiany zasad nie zmienia wyników (plan optymalizacji, B2). Kilka gier:
poziomy, opcje gry, drużyna ludzi bez decyzji i mały kapitał; skrót stanu, decyzji botów
i wniosków w każdej rundzie.

    python -X utf8 -m balans.odcisk zapisz plik.json     # przed zmianą
    python -X utf8 -m balans.odcisk porownaj plik.json   # po zmianie – rundy, które się różnią
"""
import hashlib
import json
import sys

from silnik.dane import dane_domyslne
from silnik.gra import Gra
from silnik.model import do_slownika
from silnik.wyniki.wnioski import wnioski

# (nazwa, rundy, ziarno, poziom botów, opcje gry)
GRY = [("sredni7", 18, 7, "sredni", {}), ("trudny11", 18, 11, "trudny", {}),
       ("latwy23", 12, 23, "latwy", {}),
       ("opcje5", 14, 5, "sredni", {"ceny_dostawcow": "losowe",
                                    "kredyt_odnawialny": "jednoczesnie", "auto_zamowienia": True}),
       ("kapital3", 10, 3, "trudny", {"kapital_startowy": 15000})]


def _skrot(x) -> str:
    tekst = json.dumps(x, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(tekst.encode()).hexdigest()[:16]


def odcisk() -> dict[str, list[str]]:
    """{"gra/runda": [skrót stanu, decyzji, wniosków]}; sprawdza też, że historia się nie zmienia"""
    strategie = list(dane_domyslne().boty["strategie"])
    wynik = {}
    for nazwa, rund, ziarno, poziom, opcje in GRY:
        g = Gra.nowa("odcisk", [(n, n) for n in strategie] + [("Ludzie", None)], rund, ziarno,
                     poziomy={n: poziom for n in strategie}, **opcje)
        for r in range(1, rund + 1):
            if r == 1:
                g.ustaw_decyzje("Ludzie", {"lokal": {"id": "centrum_3", "forma": "najem"}})
            s = g.przelicz(wymus=True)
            wn = {f: wnioski(g.dane, s.wyniki[r].get(f)) for f in s.firmy}
            wynik[f"{nazwa}/{r}"] = [_skrot(do_slownika(s)), _skrot(g.decyzje[r]), _skrot(wn)]
        # stany wcześniejszych rund nie mogą się zmienić po kolejnych (historia tylko do odczytu)
        for r in range(1, rund + 1):
            if _skrot(do_slownika(g.stan(r))) != wynik[f"{nazwa}/{r}"][0]:
                raise AssertionError(f"historia zmieniona: {nazwa}, runda {r}")
    return wynik


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("zapisz", "porownaj"):
        print(__doc__)
        return 2
    teraz = odcisk()
    if argv[0] == "zapisz":
        with open(argv[1], "w", encoding="utf-8") as p:
            json.dump(teraz, p, indent=0)
        print(f"zapisano {len(teraz)} rund")
        return 0
    with open(argv[1], encoding="utf-8") as p:
        wzor = json.load(p)
    rozne = [k for k in wzor if teraz.get(k) != wzor[k]]
    zgodny = not rozne and len(teraz) == len(wzor)
    print("odcisk identyczny" if zgodny else f"różne rundy: {', '.join(rozne)}")
    return 0 if zgodny else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
