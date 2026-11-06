"""Cele trudności B5 z pomiaru poziomów „jak człowiek”: python trud.py katalog [katalog2 ...]"""
import collections
import csv
import statistics as s
import sys

for kat in sys.argv[1:]:
    g = {}
    for x in csv.DictReader(open(f"{kat}/gry.csv", encoding="utf8")):
        if x["wariant"] == "baza":
            g[(x["strategia"], int(x["ziarno"]), x["poziom"])] = x
    trojki = sorted({(a, z) for a, z, _ in g})
    sl, sr, do = "czlowiek_slaby", "czlowiek_sredni", "czlowiek_dobry"
    trojki = [t for t in trojki if all((*t, p) in g for p in (sl, sr, do))]
    pp = collections.Counter()
    for t in trojki:
        v = g[(*t, sr)]["pierwszy_plus"]
        pp["4-6" if v and 4 <= float(v) <= 6 else f"{v}"] += 1
    al = sum(float(g[(*t, sl)]["alarmy"]) > 0 for t in trojki)
    dob = sum(float(g[(*t, do)]["karta"]) > float(g[(*t, sr)]["karta"]) for t in trojki)
    sla = sum(float(g[(*t, sl)]["karta"]) < float(g[(*t, sr)]["karta"]) for t in trojki)
    karty = {p: s.mean(float(g[(*t, p)]["karta"]) for t in trojki) for p in (sl, sr, do)}
    maj = s.mean(float(g[(*t, sr)]["majatek"]) for t in trojki)
    wg = collections.Counter(t[0] for t in trojki
                             if float(g[(*t, do)]["karta"]) > float(g[(*t, sr)]["karta"]))
    print(f"{kat}: {len(trojki)} trójek")
    print(f"  pierwszy plus średniej: {dict(pp)}")
    print(f"  alarmy słabej: {al}; dobra > średnia: {dob}; słaba < średnia: {sla}")
    print("  karta słaba/średnia/dobra: " + " / ".join(f"{v:.2f}" for v in karty.values())
          + f"; majątek średniej {maj / 1000:.0f} tys.")
    print(f"  dobra > średnia wg strategii: {dict(wg)}")
