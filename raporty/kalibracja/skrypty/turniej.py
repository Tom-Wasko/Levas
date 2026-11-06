"""B14: turniej strategii – wszystkie firmy na tym samym poziomie; kto wygrywa (karta) w jakim kontekście.
python turniej.py katalog procesy ziarno_od ziarno_do poziom:firm:rund [poziom:firm:rund ...]
Wynik: katalog/turniej.csv (kontekst, ziarno, firma, strategia, strefy, karta, majatek, miejsce)."""
import csv
import random
import sys
from multiprocessing import Pool
from pathlib import Path

from silnik.dane import dane_domyslne
from silnik.gra import Gra
from silnik.wyniki.majatek import z_portfelem

KAT = Path(sys.argv[1])


def gra(z):
    kontekst, ziarno = z
    plik = KAT / "gry" / f"{kontekst.replace(':', '_')}_{ziarno}.csv"
    if plik.exists():
        return
    poziom, firm, rund = kontekst.split(":")
    firm, rund = int(firm), int(rund)
    rng = random.Random(ziarno * 1000 + firm * 31 + rund)
    st = list(dane_domyslne().boty["strategie"])
    lista = st[:firm] if firm <= len(st) else st + [rng.choice(st) for _ in range(firm - len(st))]
    if firm < len(st):
        lista = rng.sample(st, firm)
    rng.shuffle(lista)
    fs = [(f"F{i}_{s}", s) for i, s in enumerate(lista)]
    g = Gra.nowa("b14", fs, rund, ziarno, poziomy={n: poziom for n, _ in fs})
    for _ in range(rund):
        s = g.przelicz(wymus=True)
    karty = {n: sum(s.wyniki[r][n]["karta"]["wynik_dzialalnosci"] for r in range(2, rund + 1)) / (rund - 1)
             for n in s.firmy}
    d = dane_domyslne()
    kol = sorted(karty, key=karty.get, reverse=True)
    wiersze = [{"kontekst": kontekst, "ziarno": ziarno, "firma": n, "strategia": n.split("_", 1)[1],
                "strefy": ";".join(d.lokale[x.id]["strefa"] for x in s.firmy[n].lokale),
                "lokale": len(s.firmy[n].lokale), "karta": round(karty[n], 4),
                "majatek": z_portfelem(s.wyniki[rund][n]), "miejsce": kol.index(n) + 1} for n in s.firmy]
    with open(plik, "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, list(wiersze[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(wiersze)


if __name__ == "__main__":
    (KAT / "gry").mkdir(parents=True, exist_ok=True)
    zad = [(k, z) for k in sys.argv[5:] for z in range(int(sys.argv[3]), int(sys.argv[4]))]
    with Pool(int(sys.argv[2])) as p:
        for i, _ in enumerate(p.imap_unordered(gra, zad)):
            print(i + 1, "/", len(zad), flush=True)
