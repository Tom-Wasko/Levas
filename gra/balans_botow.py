"""Balans poziomów botów (F4.4): gra z lokalami, w której wszystkie strategie z dane/boty.yaml
grają na jednym poziomie; wypisuje gotówkę, średni wynik działalności, lokale, pracowników,
przeterminowany towar i sprzedaż/popyt ostatniej rundy.

    python -X utf8 balans_botow.py [rundy] [poziomy po przecinku] [ziarna po przecinku]
    python -X utf8 balans_botow.py 12 latwy,sredni,trudny 7,11,23
"""
import sys
import time

from silnik.dane import dane_domyslne
from silnik.gra import Gra


def _przeterminowane(wyniki: dict) -> float:
    return ((wyniki.get("magazyn") or {}).get("sanepid") or {}).get("przeterminowane") or 0


def rozegraj(rund: int, poziom: str, ziarno: int) -> dict[str, dict]:
    """Gra samych botów (każda strategia raz) na jednym poziomie: {strategia: liczby}."""
    strategie = list(dane_domyslne().boty["strategie"])
    g = Gra.nowa("balans", [(n, n) for n in strategie], rund, ziarno,
                 poziomy={n: poziom for n in strategie})
    for _ in range(rund):
        s = g.przelicz(wymus=True)
    wynik = {}
    for n, f in s.firmy.items():
        wd = [s.wyniki[r][n]["karta"]["wynik_dzialalnosci"] for r in range(2, rund + 1)]
        sp = s.wyniki[rund][n]["sprzedaz"].values()
        wynik[n] = {"gotowka": f.gotowka, "wynik": sum(wd) / len(wd), "lokale": len(f.lokale),
                    "pracownicy": len(f.pracownicy),
                    "przeterminowane": sum(_przeterminowane(s.wyniki[r][n])
                                           for r in range(1, rund + 1)),
                    "sprzedaz": sum(v["sprzedaz"] for v in sp),
                    "popyt": sum(v["popyt"] for v in sp)}
    return wynik


if __name__ == "__main__":
    rund = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    poziomy = sys.argv[2].split(",") if len(sys.argv) > 2 else list(dane_domyslne().boty["poziomy"])
    ziarna = [int(z) for z in sys.argv[3].split(",")] if len(sys.argv) > 3 else [7]
    for poz in poziomy:
        razem = []
        for z in ziarna:
            t = time.time()
            w = rozegraj(rund, poz, z)
            print(f"== {poz}, ziarno {z} ({time.time() - t:.1f} s)")
            for n, x in w.items():
                print(f"  {n:13s} gotówka {x['gotowka']:9.0f}  wynik {x['wynik']:6.3f}"
                      f"  lokale {x['lokale']}  prac. {x['pracownicy']}"
                      f"  przeterm. {x['przeterminowane']:7.0f}"
                      f"  sprzedaż/popyt {x['sprzedaz']:.0f}/{x['popyt']:.0f}")
            razem += [x["gotowka"] for x in w.values()]
        print(f"   średnia gotówka poziomu {poz}: {sum(razem) / len(razem):.0f}")
