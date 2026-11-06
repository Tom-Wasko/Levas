"""Pary poziomów z pomiaru baza: python poz.py katalog poziom1,poziom2,... – kolejne pary: niższy < wyższy."""
import collections
import csv
import statistics as s
import sys

kat, poz = sys.argv[1], sys.argv[2].split(",")
g = {(x["strategia"], int(x["ziarno"]), x["poziom"]): x
     for x in csv.DictReader(open(f"{kat}/gry.csv", encoding="utf8")) if x["wariant"] == "baza"}
strat = sorted({a for a, _, _ in g})
ziarna = sorted({z for _, z, _ in g})
f = lambda st, z, p, k="karta": float(g[(st, z, p)][k])   # noqa: E731
print("karta śr.:", ", ".join(f"{p} {s.mean(f(a, z, p) for a in strat for z in ziarna if (a, z, p) in g):.2f}" for p in poz))
print("alarmy:", ", ".join(f"{p} {sum(f(a, z, p, 'alarmy') > 0 for a in strat for z in ziarna if (a, z, p) in g)}" for p in poz))
print("miejsce śr.:", ", ".join(f"{p} {s.mean(f(a, z, p, 'miejsce') for a in strat for z in ziarna if (a, z, p) in g):.1f}" for p in poz))
for lo, hi in zip(poz, poz[1:]):
    wg = collections.Counter()
    n = collections.Counter()
    for a in strat:
        for z in ziarna:
            if (a, z, lo) in g and (a, z, hi) in g:
                n[a] += 1
                wg[a] += f(a, z, hi) > f(a, z, lo)
    print(f"{hi} > {lo}: {sum(wg.values())}/{sum(n.values())}  " + ", ".join(f"{a} {wg[a]}/{n[a]}" for a in strat))
print("karta wg strategii:")
for a in strat:
    print(f"  {a:13s}", "  ".join(f"{p} {s.mean(f(a, z, p) for z in ziarna if (a, z, p) in g):+.2f}" for p in poz))
